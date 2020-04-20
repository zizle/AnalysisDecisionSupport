# _*_ coding:utf-8 _*_
# Author: zizle
import os
import datetime
from flask import request, jsonify, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from db import MySQLConnection
from plates.user import enums
from .enums import report_categories
from settings import BASE_DIR


class ReportView(MethodView):
    def get(self):
        # 接口说明:品种variety<=0是全部;类型category=-1是全部,0是其他
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
            variety_id = int(params.get('variety', 0))
            category = int(params.get('category', -1))
        except Exception as e:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if variety_id <= 0:
            query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`title`,`file_url`,`category` " \
                              "FROM `info_report` " \
                              "WHERE `is_active`=1 ORDER BY `custom_time` DESC " \
                              "LIMIT %d,%d;" % (id_start, page_size)
            query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_report` WHERE `is_active`=1;"
        else:
            query_statement = "SELECT reporttb.id,DATE_FORMAT(reporttb.custom_time, '%%Y-%%m-%%d') AS `custom_time`,`title`,`file_url`,`category` " \
                              "FROM `info_report` AS `reporttb` INNER JOIN `link_report_variety` AS `linkvtb` " \
                              "ON reporttb.id=linkvtb.report_id AND linkvtb.variety_id=%d " \
                              "ORDER BY `custom_time` DESC " \
                              "LIMIT %d,%d;" % (variety_id, id_start,page_size)
            query_total_statement = "SELECT COUNT(reporttb.id) AS `total` FROM `info_report` AS `reporttb` " \
                                    "INNER JOIN `link_report_variety` AS `linkvtb` " \
                                    "ON reporttb.id=linkvtb.report_id AND linkvtb.variety_id=%d;" % variety_id

        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute(query_total_statement)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        # 处理分类
        response_reports = list()
        if category != -1:
            for report_item in query_result:
                if report_item['category'] != category:
                    continue
                report_item['category'] = report_categories.get(report_item['category'], '')
                response_reports.append(report_item)
        else:
            for report_item in query_result:
                report_item['category'] = report_categories.get(report_item['category'], '')
                response_reports.append(report_item)

        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "reports": response_reports,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })

    def post(self):
        body_form = request.form
        utoken = body_form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"message": "登录已过期或不能进行操作。"}), 400
        title = body_form.get('title', None)
        report_file = request.files.get('report_file')
        link_varieties = body_form.get('link_varieties')
        custom_time = body_form.get('custom_time')
        category = body_form.get('category', 0)
        if not all([title, report_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        user_has_access_variety = True
        if link_varieties:
            link_varieties = list(map(int, link_varieties.split(',')))  # 转为列表并转为整形
            query_user_variety = "SELECT `id` FROM `link_user_variety` " \
                                 "WHERE `variety_id`=%s;"
            for variety_id in link_varieties:
                cursor.execute(query_user_variety, variety_id)
                if not cursor.fetchone():
                    user_has_access_variety = False
                    break
        if not user_has_access_variety:
            db_connection.close()
            return jsonify({"message":"没有当前品种的权限!"}), 400

        report_filename = report_file.filename
        file_hash_name = hash_filename(report_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        report_folder = os.path.join(BASE_DIR, "fileStorage/homepage/report/{}/{}/".format(year, month))
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(report_folder, prefix_filename + file_hash_name)
        file_save_url = "homepage/report/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        report_file.save(file_path)

        save_statement = "INSERT INTO `info_report` (`create_time`,`custom_time`,`title`,`file_url`,`category`,`author_id`) " \
                         "VALUES (%s,%s,%s,%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            custom_time = datetime.datetime.strptime(custom_time, '%Y-%m-%d') if custom_time else today
            category = int(category)
            if category < 0 or category > 5:
                raise ValueError('分类错误!')
            cursor.execute(save_statement, (today, custom_time, title, file_save_url, category, user_id))
            if link_varieties:
                new_report_id = db_connection.insert_id()

                link_statement = "INSERT INTO `link_report_variety` (`report_id`,`variety_id`) " \
                                 "VALUES (%s,%s);"
                many_values = [(new_report_id, variety_id) for variety_id in link_varieties]
                cursor.executemany(link_statement, many_values)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("上传报告错误:{}".format(e))
            return jsonify({'message': "上传报告错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "上传报告成功!"}), 201


class UserReportView(MethodView):
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
        query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`title`,`file_url`,`category`, `is_active` " \
                          "FROM `info_report` " \
                          "WHERE `author_id`=%d ORDER BY `custom_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_report` WHERE `author_id`=%d;" % uid)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "reports": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveReportView(MethodView):
    def delete(self, uid, rid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_report` WHERE `id`=%d;" % rid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_report` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(),`create_time`) < 3;" % (rid, uid)
            lines_changed = cursor.execute(delete_statement)  # 删除报告本身
            if lines_changed <= 0:
                raise ValueError("不能删除较早期的报告了.")
            delete_links = "DELETE FROM `link_report_variety` " \
                           "WHERE `report_id`=%d;" % rid
            cursor.execute(delete_links)
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
