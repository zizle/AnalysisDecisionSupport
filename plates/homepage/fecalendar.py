# _*_ coding:utf-8 _*_
# Author: zizle

""" financial economic calendar """
import xlrd
import datetime
from flask import request,jsonify,current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from plates.user import enums


class FeCalendarView(MethodView):
    def get(self):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
            date = params.get('date', None)
            if date:
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if date:
            query_statement = "SELECT `id`, `date`,`time`,`country`,`event`,`expected` " \
                              "FROM `info_finance` " \
                              "WHERE `date`=%s " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_finance` WHERE `date`=%s;"
            cursor.execute(query_statement, (date, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement, date)
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT `id`, `date`,`time`,`country`,`event`,`expected` " \
                              "FROM `info_finance` " \
                              "ORDER BY `date` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_finance`;"
            cursor.execute(query_statement, (id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement)
            total_count = cursor.fetchone()['total']
        response_fecs = list()
        for fc_item in query_result:
            fc_item['date'] = fc_item['date'].strftime("%Y-%m-%d")
            duration = fc_item['time'].total_seconds()
            fc_item['time'] = '%02d:%02d' % (duration // 3600, duration % 3600 // 60)
            response_fecs.append(fc_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "fecalendar": response_fecs,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })

    def post(self):
        fc_file = request.files.get('fecalendar_file')
        if fc_file:
            return self.save_file_data(fc_file)
        else:
            return self.save_json_data()

    def save_file_data(self, fc_file):
        utoken = request.form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录已过期"}), 400
        file_contents = xlrd.open_workbook(file_contents=fc_file.read())
        table_data = file_contents.sheets()[0]
        if not file_contents.sheet_loaded(0):
            return jsonify({"message": "数据导入失败."}), 400
        table_headers = table_data.row_values(0)
        if table_headers != [
            "日期", "时间", "地区", "事件", "预期值"
        ]:
            return jsonify({"message": "文件格式有误,请检查后再上传."}), 400
        ready_to_save = list()
        start_data_in = False
        message = "表格数据类型有误，请检查后上传."
        today = datetime.datetime.today()
        user_id = int(user_info['id'])
        try:
            for row in range(table_data.nrows):
                row_content = table_data.row_values(row)
                if row_content[0] == "start":
                    start_data_in = True
                    continue
                if row_content[0] == 'end':
                    start_data_in = False
                    continue
                if start_data_in:
                    record_row = list()
                    # "日期", "时间", "地区", "事件", "预期值"
                    record_row.append(today)
                    record_row.append(xlrd.xldate_as_datetime(row_content[0], 0))
                    time = xlrd.xldate_as_datetime(row_content[1], 0)
                    record_row.append(time.strftime('%H:%M:%S'))
                    record_row.append(row_content[2])
                    record_row.append(row_content[3])
                    record_row.append(row_content[4])
                    record_row.append(user_id)
                    ready_to_save.append(record_row)
        except Exception as e:
            current_app.logger.error("批量上传财经日历数据错误:{}".format(e))
            return jsonify({"message": message}), 400
        insert_statement = "INSERT INTO `info_finance` " \
                           "(`create_time`,`date`,`time`,`country`,`event`,`expected`,`author_id`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.executemany(insert_statement, ready_to_save)
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "上传成功"}), 201

    def save_json_data(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.COLLECTOR:
            return jsonify({"message": "登录已过期或不能操作."}), 400
        today = datetime.datetime.today()
        date = body_json.get('date')
        time = body_json.get('time')
        country = body_json.get('country', '')
        event = body_json.get('event', '')
        expected = body_json.get('expected', '')
        if not all([date, time, event]):
            return jsonify({"message": "参数错误."}), 400
        save_statement = "INSERT INTO `info_finance` " \
                         "(`create_time`,`date`, `time`,`country`,`event`,`expected`,`author_id`) " \
                         "VALUES (%s,%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
            time = datetime.datetime.strptime(time, "%H:%M:%S")
            user_id = user_info['id']
            cursor = db_connection.get_cursor()
            cursor.execute(save_statement,
                           (today, date, time, country, event, expected, user_id)
                           )
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("写入财经日历错误:{}".format(e))
            return jsonify({"message": "错误:{}".format(e)})
        else:
            return jsonify({"message": "添加成功!"}), 201


class UserFeCalendarView(MethodView):
    def get(self, uid):
        params = request.args
        try:
            current_page = int(params.get('page', 1)) - 1
            page_size = int(params.get('page_size', 50))
            date = params.get('date', None)
            if date:
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            return jsonify({"message": "参数错误。"}), 400
        id_start = current_page * page_size
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if date:
            query_statement = "SELECT `id`,`date`,`time`,`country`,`event`,`expected` " \
                              "FROM `info_finance` " \
                              "WHERE `author_id`=%s AND `date`=%s " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_finance` WHERE `author_id`=%s AND `date`=%s;"
            cursor.execute(query_statement,(uid, date, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement, (uid,date))
            total_count = cursor.fetchone()['total']

        else:

            query_statement = "SELECT `id`,`date`,`time`,`country`,`event`,`expected` " \
                              "FROM `info_finance` " \
                              "WHERE `author_id`=%s ORDER BY `date` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_finance` WHERE `author_id`=%s;"
            cursor.execute(query_statement,(uid, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement,uid)
            total_count = cursor.fetchone()['total']
        db_connection.close()
        response_fecs = list()
        for fc_item in query_result:
            fc_item['date'] = fc_item['date'].strftime("%Y-%m-%d")
            duration = fc_item['time'].total_seconds()
            fc_item['time'] = '%02d:%02d' %(duration // 3600, duration % 3600 // 60)
            response_fecs.append(fc_item)

        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "fecalendar": response_fecs,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveFeCalendarView(MethodView):
    def delete(self,uid, fid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            delete_statement = "DELETE FROM `info_finance` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(),`create_time`) < 3;" % (fid, uid)
            lines_changed = cursor.execute(delete_statement)
            if lines_changed <= 0:
                raise ValueError("不能删除较早期的记录了.")
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "删除失败{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "删除成功!"})
