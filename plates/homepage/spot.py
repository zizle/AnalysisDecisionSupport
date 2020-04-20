# _*_ coding:utf-8 _*_
# Author: zizle
import xlrd
import datetime
from flask import jsonify, request, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from plates.user import enums


class SpotView(MethodView):
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
            query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`name`,`area`," \
                              "`level`, `price`,`increase`,`note`,`is_active` " \
                              "FROM `info_spot` " \
                              "WHERE `custom_time`=%s ORDER BY `custom_time` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_spot` WHERE `custom_time`=%s;"
            cursor.execute(query_statement,(date, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement, date)
            total_count = cursor.fetchone()['total']
        else:
            query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`name`,`area`," \
                              "`level`, `price`,`increase`,`note`,`is_active` " \
                              "FROM `info_spot` " \
                              "ORDER BY `custom_time` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_spot`;"
            cursor.execute(query_statement, (id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement)
            total_count = cursor.fetchone()['total']
        response_spots = list()
        for spot_item in query_result:
            spot_item['price'] = '%.0f' % spot_item['price']
            spot_item['increase'] = '%.0f' % spot_item['increase']
            response_spots.append(spot_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "spots": response_spots,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })

    def post(self):
        spot_file = request.files.get('spot_file')
        if spot_file:
            return self.save_file_data(spot_file)
        else:
            return self.save_json_data()

    def save_file_data(self, spot_file):
        utoken = request.form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录已过期"}), 400
        file_contents = xlrd.open_workbook(file_contents=spot_file.read())
        table_data = file_contents.sheets()[0]
        if not file_contents.sheet_loaded(0):
            return jsonify({"message":"数据导入失败."}), 400
        table_headers = table_data.row_values(0)
        if table_headers != [
            "日期", "名称","地区","等级","价格","增减","备注"
        ]:
            return jsonify({"message":"文件格式有误,请检查后再上传."}), 400
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
                    #"日期", "名称","地区","等级","价格","增减","备注"
                    record_row.append(today)
                    record_row.append(xlrd.xldate_as_datetime(row_content[0],0))
                    record_row.append(row_content[1])
                    record_row.append(row_content[2])
                    record_row.append(row_content[3])
                    record_row.append(float(row_content[4]))
                    record_row.append(float(row_content[5]))
                    record_row.append(row_content[6])
                    record_row.append(user_id)

                    ready_to_save.append(record_row)
        except Exception as e:
            current_app.logger.error("批量上传现货报表数据错误:{}".format(e))
            return jsonify({"message": message}), 400
        insert_statement = "INSERT INTO `info_spot` " \
                           "(`create_time`,`custom_time`,`name`,`area`,`level`,`price`,`increase`,`note`,`author_id`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.executemany(insert_statement, ready_to_save)
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":"上传成功"}), 201

    def save_json_data(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.COLLECTOR:
            return jsonify({"message":"登录已过期或不能操作."}), 400
        today = datetime.datetime.today()
        custom_time = body_json.get('custom_time')
        name = body_json.get('name','')
        area = body_json.get('area','')
        level = body_json.get('level', '')
        price = body_json.get('price', 0)
        increase = body_json.get('increase', 0)
        note = body_json.get('note', '')
        if not all([custom_time,name,price,increase]):
            return jsonify({"message":"参数错误."}), 400
        save_statement = "INSERT INTO `info_spot` " \
                         "(`create_time`, `custom_time`,`name`,`area`,`level`,`price`,`increase`,`author_id`,`note`) " \
                         "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        try:
            custom_time = datetime.datetime.strptime(custom_time, "%Y-%m-%d")
            price = float(price)
            increase = float(increase)
            user_id = user_info['id']
            cursor = db_connection.get_cursor()
            cursor.execute(save_statement,
                           (today, custom_time,name,area,level,price,increase,user_id,note)
                           )
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("写入现货报表错误:{}".format(e))
            return jsonify({"message":"错误:{}".format(e)})
        else:
            return jsonify({"message":"添加成功!"}), 201


class UserSpotView(MethodView):
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
            query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`name`,`area`," \
                              "`level`, `price`,`increase`,`note`,`is_active` " \
                              "FROM `info_spot` " \
                              "WHERE `author_id`=%s AND `custom_time`=%s ORDER BY `custom_time` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_spot` WHERE `author_id`=%s AND `custom_time`=%s;"
            cursor.execute(query_statement,(uid, date, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement, (uid,date))
            total_count = cursor.fetchone()['total']

        else:

            query_statement = "SELECT `id`, DATE_FORMAT(`custom_time`, '%%Y-%%m-%%d') AS `custom_time`,`name`,`area`," \
                              "`level`, `price`,`increase`,`note`,`is_active` " \
                              "FROM `info_spot` " \
                              "WHERE `author_id`=%s ORDER BY `custom_time` DESC " \
                              "LIMIT %s,%s;"
            total_count_statement = "SELECT COUNT(`id`) AS `total` FROM `info_spot` WHERE `author_id`=%s;"
            cursor.execute(query_statement,(uid, id_start, page_size))
            query_result = cursor.fetchall()
            # 查询总数量
            cursor.execute(total_count_statement,uid)
            total_count = cursor.fetchone()['total']
        db_connection.close()
        response_spots = list()
        for spot_item in query_result:
            spot_item['price'] = '%.0f' % spot_item['price']
            spot_item['increase'] = '%.0f' % spot_item['increase']
            response_spots.append(spot_item)
        total_page = int((total_count + page_size - 1) / page_size)
        return jsonify({
            "message": "查询成功!",
            "spots": response_spots,
            "current_page": current_page,
            "total_page": total_page,
            "page_size": page_size,
            "total_count": total_count
        })


class UserRetrieveSpotView(MethodView):
    def delete(self,uid, sid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['id'] != uid:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        try:
            cursor = db_connection.get_cursor()
            delete_statement = "DELETE FROM `info_spot` " \
                               "WHERE `id`=%d AND `author_id`=%d AND DATEDIFF(NOW(),`create_time`) < 3;" % (sid, uid)
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

