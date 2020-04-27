# _*_ coding:utf-8 _*_
# Author: zizle
import os
import hashlib
import datetime
from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from plates.user import enums
from settings import BASE_DIR


class ShortMessageView(MethodView):
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
        query_statement = "SELECT `id`, `custom_time`,`content` " \
                          "FROM `info_shortmessage` " \
                          "ORDER BY `custom_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_shortmessage`;")
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        records = list()
        for sms_item in query_result:
            sms_item['date'] = sms_item['custom_time'].strftime('%Y-%m-%d')
            sms_item['time'] = sms_item['custom_time'].strftime('%H:%M:%S')
            records.append(sms_item)
        return jsonify({
            "message": "查询成功!",
            "records": records,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"message":"登录过期或不能执行操作."}), 400
        today = datetime.datetime.today()
        custom_time = body_json.get('custom_time', today)
        content = body_json.get('content')
        if not content:
            return jsonify({"message":"请输入内容"}), 400
        db_connection = MySQLConnection()
        try:
            custom_time = datetime.datetime.strptime(custom_time, "%Y-%m-%d %H:%M:%S")
            author_id = int(user_info['id'])
            save_statement = "INSERT INTO `info_shortmessage` (`create_time`,`custom_time`,`content`,`author_id`) " \
                             "VALUES (%s,%s,%s,%s);"
            cursor = db_connection.get_cursor()
            cursor.execute(save_statement,(today, custom_time,content,author_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("添加短信通错误:{}".format(e)), 400
            return jsonify({'message':'添加错误:{}'.format(e)})
        else:
            db_connection.close()
            return jsonify({"message":"添加成功!"}), 201


class UserShortMessageView(MethodView):
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
        query_statement = "SELECT `id`, `custom_time`,`content` " \
                          "FROM `info_shortmessage` " \
                          "WHERE `author_id`=%d ORDER BY `custom_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_shortmessage` WHERE `author_id`=%d;" % uid)
        total_count = cursor.fetchone()['total']
        db_connection.close()
        total_page = int((total_count + page_size - 1) / page_size)
        for sms_item in query_result:
            sms_item['custom_time'] = sms_item['custom_time'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            "message": "查询成功!",
            "records": query_result,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class MarketAnalysisView(MethodView):
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
                          "FROM `info_marketanalysis` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_marketanalysis` WHERE `is_active`=1;"

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
        market_analysis_file = request.files.get('market_file')
        if not all([title, market_analysis_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        market_filename = market_analysis_file.filename
        file_hash_name = hash_filename(market_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/marketas/{}/{}/".format(year, month))
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(file_folder, prefix_filename + file_hash_name)
        file_save_url = "pserver/marketas/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        market_analysis_file.save(file_path)

        save_statement = "INSERT INTO `info_marketanalysis` (`title`,`file_url`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            cursor.execute(save_statement, (title, file_save_url, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("添加市场分析错误:{}".format(e))
            return jsonify({'message': "添加市场分析错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201


class UserMarketAnalysisView(MethodView):
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
                          "FROM `info_marketanalysis` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_marketanalysis` WHERE `author_id`=%d;" % uid)
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


class UserRetrieveMarketAnalysisView(MethodView):
    def delete(self, uid, mid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_marketanalysis` WHERE `id`=%d;" % mid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_marketanalysis` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (mid, uid)
            cursor.execute(delete_statement)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
            return jsonify({"message": "删除成功!"})


class TopicSearchView(MethodView):
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
                          "FROM `info_topicsearch` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_topicsearch` WHERE `is_active`=1;"

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
        topic_search_file = request.files.get('topic_file')
        if not all([title, topic_search_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        topic_filename = topic_search_file.filename
        file_hash_name = hash_filename(topic_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/topicsh/{}/{}/".format(year, month))
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(file_folder, prefix_filename + file_hash_name)
        file_save_url = "pserver/topicsh/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        topic_search_file.save(file_path)

        save_statement = "INSERT INTO `info_topicsearch` (`title`,`file_url`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            cursor.execute(save_statement, (title, file_save_url, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("添加专题研究错误:{}".format(e))
            return jsonify({'message': "添加错误:{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201


class UserTopicSearchView(MethodView):
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
                          "FROM `info_topicsearch` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_topicsearch` WHERE `author_id`=%d;" % uid)
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


class UserRetrieveTopicSearchView(MethodView):
    def delete(self, uid, tid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_topicsearch` WHERE `id`=%d;" % tid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_topicsearch` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (tid, uid)
            cursor.execute(delete_statement)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
            return jsonify({"message": "删除成功!"})


class SearchReportView(MethodView):
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
                          "FROM `info_searchreport` " \
                          "WHERE `is_active`=1 ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (id_start, page_size)
        query_total_statement = "SELECT COUNT(`id`) AS `total` FROM `info_searchreport` WHERE `is_active`=1;"

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
        print(query_result)
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
        serarch_report_file = request.files.get('sreport_file')
        if not all([title, serarch_report_file]):
            return jsonify({"message": "参数错误!"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        market_filename = serarch_report_file.filename
        file_hash_name = hash_filename(market_filename)
        today = datetime.datetime.today()
        year = today.year
        month = "%.2d" % today.month
        day = "%.2d" % today.day
        file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/searchrp/{}/{}/".format(year, month))
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        prefix_filename = "{}_".format(day)
        file_path = os.path.join(file_folder, prefix_filename + file_hash_name)
        file_save_url = "pserver/searchrp/{}/{}/".format(year, month) + prefix_filename + file_hash_name
        serarch_report_file.save(file_path)

        save_statement = "INSERT INTO `info_searchreport` (`title`,`file_url`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        try:
            user_id = int(user_info['id'])
            cursor.execute(save_statement, (title, file_save_url, user_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            os.remove(file_path)
            db_connection.close()
            current_app.logger.error("添加调研报告错误:{}".format(e))
            return jsonify({'message': "添加报告错误"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201


class UserSearchReportView(MethodView):
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
                          "FROM `info_searchreport` " \
                          "WHERE `author_id`=%d ORDER BY `create_time` DESC " \
                          "LIMIT %d,%d;" % (uid, id_start, page_size)
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT COUNT(`id`) AS `total` FROM `info_searchreport` WHERE `author_id`=%d;" % uid)
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


class UserRetrieveSearchReportView(MethodView):
    def delete(self, uid, sid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            select_statement = "SELECT `file_url` FROM `info_searchreport` WHERE `id`=%d;" % sid
            cursor.execute(select_statement)
            file_url = cursor.fetchone()['file_url']
            delete_statement = "DELETE FROM `info_searchreport` " \
                               "WHERE `id`=%d AND `author_id`=%d;" % (sid, uid)
            cursor.execute(delete_statement)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            # 删除文件
            if file_url:
                file_addr = os.path.join(BASE_DIR, "fileStorage/" + file_url)
                if os.path.isfile(file_addr):
                    os.remove(file_addr)
            return jsonify({"message": "删除成功!"})




