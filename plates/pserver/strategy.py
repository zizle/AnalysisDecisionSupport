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
from settings import BASE_DIR


class InvestmentPlan(MethodView):
    def get(self):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
        except Exception as e:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url` " \
                          "FROM `info_investmentplan` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_investmentplan` WHERE `is_active`=1;"

        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute(query_total_statement)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        # 处理分类
        # response_reports = list()
        # for report_item in query_result:
        #     response_reports.append(report_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "records": query_result,
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
        investment_file = request.files.get('invest_file')
        if not all([title, investment_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        invest_filename = investment_file.filename
        file_hash_name = hash_filename(invest_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/investmentplan/{}/{}/".format(year, month))
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(file_folder, prefix_filename + file_hash_name)
        file_save_url = "pserver/investmentplan/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        investment_file.save(file_path)

        save_statement = "INSERT INTO `info_investmentplan` (`title`,`file_url`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            cursor.execute(save_statement, (title, file_save_url, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("添加投资方案错误:{}".format(e))
            return jsonify({'message': "添加方案错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201


class UserInvestmentPlan(MethodView):
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
        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url`, `is_active` " \
                          "FROM `info_investmentplan` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_investmentplan` WHERE `author_id`=%d;" % uid)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "records": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveInvestmentPlan(MethodView):
    def delete(self, uid, iid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "登录过期,参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_investmentplan` WHERE `id`=%d;" % iid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_investmentplan` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (iid, uid)
            cursor.execute(delete_statement)
            db_connection.commit()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "删除成功!"})


class HedgePlanView(MethodView):
    def get(self):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
        except Exception as e:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url` " \
                          "FROM `info_hedgeplan` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_hedgeplan` WHERE `is_active`=1;"

        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute(query_total_statement)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        # 处理分类
        # response_reports = list()
        # for report_item in query_result:
        #     response_reports.append(report_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "records": query_result,
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
        hedge_file = request.files.get('hedge_file')
        if not all([title, hedge_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        hedge_filename = hedge_file.filename
        file_hash_name = hash_filename(hedge_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/hedgeplan/{}/{}/".format(year, month))
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(file_folder, prefix_filename + file_hash_name)
        file_save_url = "pserver/hedgeplan/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        hedge_file.save(file_path)

        save_statement = "INSERT INTO `info_hedgeplan` (`title`,`file_url`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            cursor.execute(save_statement, (title, file_save_url, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("添加套保方案错误:{}".format(e))
            return jsonify({'message': "添加方案错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201


class UserHedgePlanView(MethodView):
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
        query_statement = "SELECT `id`, DATE_FORMAT(`create_time`, '%%Y-%%m-%%d') AS `create_time`,`title`,`file_url`, `is_active` " \
                          "FROM `info_hedgeplan` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_hedgeplan` WHERE `author_id`=%d;" % uid)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "records": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveHedgePlanView(MethodView):
    def delete(self, uid, hid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "登录过期,参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_hedgeplan` WHERE `id`=%d;" % hid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_hedgeplan` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (hid, uid)
            cursor.execute(delete_statement)
            db_connection.commit()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "删除成功!"})


