# _*_ coding:utf-8 _*_
# Author: zizle
import os
import datetime
from flask import request, jsonify,current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from plates.user import enums
from .enums import notice_categories
from settings import BASE_DIR


class ExNoticeView(MethodView):
    def get(self):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
            category = int(params.get('category', -1))  # -1是全部,0是其他
        except Exception as e:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`,DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url`,`category` " \
                          "FROM `info_exnotice` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" %(id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` " \
                                "FROM `info_exnotice` WHERE `is_active`=1;"

        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        cursor.execute(query_total_statement)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        response_exnotices = list()
        if category == -1:
            for notice_item in query_result:
                notice_item['category'] = notice_categories.get(notice_item['category'], '')
                response_exnotices.append(notice_item)
        else:
            for notice_item in query_result:
                if notice_item['category'] != category:
                    continue
                notice_item['category'] = notice_categories.get(notice_item['category'], '')
                response_exnotices.append(notice_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "exnotices": response_exnotices,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })

    def post(self):
        body_form = request.form
        utoken = body_form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.COLLECTOR:
            return jsonify({"message": "登录已过期或不能进行操作。"}), 400
        title = body_form.get('title', None)
        notice_file = request.files.get('notice_file')
        category = body_form.get('category', 0)
        if not all([title, notice_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        notice_filename = notice_file.filename
        file_hash_name = hash_filename(notice_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        exnotice_folder = os.path.join(BASE_DIR, "fileStorage/homepage/exnotice/{}/{}/".format(year, month))
        if not os.path.exists(exnotice_folder):
            os.makedirs(exnotice_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(exnotice_folder, prefix_filename + file_hash_name)
        file_save_url = "homepage/exnotice/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        notice_file.save(file_path)

        save_statement = "INSERT INTO `info_exnotice` (`create_time`,`title`,`file_url`,`category`,`author_id`) " \
                         "VALUES (%s,%s,%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            category = int(category)
            if category < 0 or category > 3:
                raise ValueError('分类错误!')
            cursor.execute(save_statement, (today, title, file_save_url, category, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("上传交易通知错误:{}".format(e))
            return jsonify({'message': "上传交易通知错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "上传交易通知成功!"}), 201


class UserExNoticeView(MethodView):
    def get(self, uid):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
        except Exception:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url`,`category`, `is_active` " \
                          "FROM `info_exnotice` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_exnotice` WHERE `author_id`=%d;" % uid)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "exnotices": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveExNoticeView(MethodView):
    def delete(self, uid, nid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_exnotice` WHERE `id`=%d;" % nid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_exnotice` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(),`create_time`) < 3;" % (nid, uid)
            lines_changed = cursor.execute(delete_statement)
            if lines_changed <= 0:
                raise ValueError("不能删除较早期的通知了.")
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message":"删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
            return jsonify({"message": "删除成功!"})
