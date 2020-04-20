# _*_ coding:utf-8 _*_
# Author: zizle

""" 公告 """

import os
import datetime
from flask import jsonify, request, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from settings import BASE_DIR


class BulletinView(MethodView):

    def get(self):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
        except Exception:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url` " \
                          "FROM `info_bulletin` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_bulletin` WHERE `is_active`=1;")
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        response_data = dict()
        response_data['bulletins'] = query_result
        response_data['total_page'] = total_page
        response_data['page_size'] = page_size
        response_data['current_page'] = current_page
        return jsonify({
            "message": "查询成功!",
            "bulletins": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size
        })

    def post(self):
        body_json = request.form
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if user_info['role_num'] > 3:
            return jsonify({"message": "登录已过期或不能进行这个操作."}), 400
        bulletin_title = body_json.get('bulletin_title')
        bulletin_file = request.files.get('bulletin_file', None)
        if not all([bulletin_title, bulletin_file]):
            return jsonify({"message":"参数错误!NOT FOUND NAME OR FILE."}), 400
        # hash文件名
        bulletin_filename = bulletin_file.filename
        file_hash_name = hash_filename(bulletin_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        bulletin_folder = os.path.join(BASE_DIR, "fileStorage/homepage/bulletin/{}/{}/".format(year, month))
        if not os.path.exists(bulletin_folder):
            os.makedirs(bulletin_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(bulletin_folder, prefix_filename + file_hash_name)
        file_save_url = "homepage/bulletin/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        bulletin_file.save(file_path)
        # 保存到数据库
        save_bulletin_statement = "INSERT INTO `info_bulletin` (`create_time`,`title`,`file_url`) " \
                                  "VALUES (%s, %s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:

            cursor.execute(save_bulletin_statement, (today, bulletin_title, file_save_url))
            db_connection.commit()
        except Exception as e:
            current_app.logger.error("保存公告错误:{}".format(e)), 400
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "上传公告失败!"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "上传公告成功!"}), 201
