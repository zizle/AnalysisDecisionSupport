# _*_ coding:utf-8 _*_
# Author: zizle

""" advertisement """

import os
import datetime
from flask import request, jsonify, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from db import MySQLConnection
from settings import BASE_DIR


class AdView(MethodView):
    def get(self):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`,'%Y-%m-%d') AS `create_time`,`title`, `file_url`,`image_url` " \
                          "FROM `info_advertisement` " \
                          "WHERE `is_active`=1;"
        cursor.execute(query_statement)
        adments = cursor.fetchall()
        return jsonify({"message":"获取广告信息成功!", "adments": adments})

    def post(self):
        body_form = request.form
        utoken = body_form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if user_info['role_num'] > 2:
            return jsonify({"message": "登录已过期或不能进行这个操作."}), 400
        ad_title = body_form.get('ad_title')
        ad_file = request.files.get('ad_file', None)
        ad_image = request.files.get('ad_image', None)
        if not all([ad_title, ad_file, ad_image]):
            return jsonify({"message": "参数不足!"}), 400
        # hash文件名
        ad_filename = ad_file.filename
        ad_imagename = ad_image.filename
        adfile_hash_name = hash_filename(ad_filename)
        adimage_hash_name = adfile_hash_name.rsplit('.', 1)[0] + '.' + ad_imagename.rsplit('.', 1)[1]
        ad_folder = os.path.join(BASE_DIR, "fileStorage/homepage/ad/")
        if not os.path.exists(ad_folder):
            os.makedirs(ad_folder)
        adfile_path = os.path.join(ad_folder + adfile_hash_name)
        adimage_path = os.path.join(ad_folder + adimage_hash_name)
        adfile_save_url = "homepage/ad/" + adfile_hash_name
        adimage_save_url = "homepage/ad/" + adimage_hash_name
        ad_file.save(adfile_path)
        ad_image.save(adimage_path)
        today = datetime.datetime.today()
        # 保存到数据库
        save_ad_statement = "INSERT INTO `info_advertisement` (`create_time`,`title`,`file_url`,`image_url`) " \
                            "VALUES (%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            cursor.execute(save_ad_statement, (today, ad_title, adfile_save_url, adimage_save_url))
            db_connection.commit()
        except Exception as e:
            current_app.logger.error("保存广告错误:{}".format(e)), 400
            db_connection.rollback()
            db_connection.close()
            os.remove(adfile_path)
            os.remove(adimage_path)
            return jsonify({"message": "新建广告失败!"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "新建广告成功!"}), 201
