# _*_ coding:utf-8 _*_
# Author: zizle
from flask import request,jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token


class UserVarietyView(MethodView):
    def get(self,uid):
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询当前用户信息
        query_user = "SELECT `id`,`username`,`phone`,`role_num` " \
                     "FROM `info_user` WHERE `id`=%d;" % uid
        cursor.execute(query_user)
        user_info = cursor.fetchone()
        if user_info['role_num'] <= 2:
            query_statement = "SELECT `id` AS `variety_id`,`name`,`is_active` " \
                              "FROM `info_variety` WHERE `is_active`=1 AND `parent_id` IS NOT NULL;"
        else:
            query_statement = "SELECT linkuv.id,linkuv.user_id,linkuv.variety_id,linkuv.is_active,infov.name " \
                              "FROM `link_user_variety` AS linkuv INNER JOIN `info_variety` AS infov " \
                              "ON linkuv.user_id=%d AND linkuv.variety_id=infov.id;" % uid

        cursor.execute(query_statement)
        query_result = cursor.fetchall()

        db_connection.close()
        # print(query_result)
        return jsonify({"message": "查询成功!", "variety": query_result, "user_info": user_info})

    def post(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        operate_user = verify_json_web_token(utoken)
        if not operate_user:
            return jsonify({"message": "登录已过期."}), 400
        if operate_user['role_num'] > 2:
            return jsonify({"message": "您无法进行这个操作"}), 400
        is_active = body_json.get('is_active', 0)
        variety_id = body_json.get('variety_id', 0)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        operate_statement = "REPLACE INTO `link_user_variety` (`user_id`,`variety_id`, `is_active`) " \
                            "VALUES (%s,%s,%s);"
        cursor.execute(operate_statement,(uid, variety_id, is_active))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":"操作成功"})
