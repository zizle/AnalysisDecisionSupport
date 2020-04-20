# _*_ coding:utf-8 _*_
# Author: zizle
import datetime
from flask import request, jsonify
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from db import MySQLConnection
from plates.user import enums


class AuthUserModuleView(MethodView):
    def get(self, mid):
        if mid < 1:
            return jsonify({"message":"验证完毕!", "auth":1})
        utoken = request.json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "验证完毕!", "auth": 0})
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询模块等级
        level_statement = "SELECT `id`,`level` FROM `info_module` WHERE `id`=%s;"
        cursor.execute(level_statement, mid)
        module_info = cursor.fetchone()
        if not module_info:
            db_connection.close()
            return jsonify({"message": "验证完毕!", "auth": 0})
        if user_info['role_num'] <= enums.RESEARCH and user_info['role_num'] <= mid:
            db_connection.close()
            return jsonify({"message": "验证完毕!", "auth": 1})
        now = datetime.datetime.now()
        select_statement = "SELECT `id`,`user_id`,`module_id` " \
                           "FROM `link_user_module` " \
                           "WHERE `user_id`=%s AND `module_id`=%s AND `expire_time`>%s;"
        cursor.execute(select_statement, (user_info['id'], mid, now))
        auth = 1 if cursor.fetchone() else 0
        db_connection.close()
        return jsonify({"message": "验证完毕!", "auth": auth})
