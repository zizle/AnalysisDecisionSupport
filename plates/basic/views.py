# _*_ coding:utf-8 _*_
# __Author__： zizle
import datetime
from flask import request, jsonify
from db import MySQLConnection
from flask.views import MethodView


class ClientView(MethodView):
    def post(self):
        body_json = request.json
        machine_code = body_json.get('machine_code', '')
        is_manager = body_json.get('is_manager', 0)
        if not machine_code:
            return jsonify("NOT FOUND machine_code!"), 400
        query_statement = "SELECT `id` FROM `client_info` WHERE `machine_code`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, machine_code)
        client = cursor.fetchone()
        if not client:
            # 创建客户端
            insert_statement = "INSERT INTO `client_info` (`machine_code`, `is_manager`) VALUES (%s, %s);"
            cursor.execute(insert_statement, (machine_code, is_manager))
        else:
            # 更新登录时间
            now = datetime.datetime.now()
            update_statement = "UPDATE `client_info` SET `update_time`=%s;"
            cursor.execute(update_statement, now)
        db_connection.commit()
        db_connection.close()
        return jsonify({'machine_code': machine_code})

