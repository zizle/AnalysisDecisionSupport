# _*_ coding:utf-8 _*_
# Author: zizle

from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from plates.user import enums


class UsersView(MethodView):
    def get(self):
        utoken = request.args.get('utoken')
        role_num = request.args.get('role_num', 0)
        try:
            role_num = int(role_num)
        except Exception as e:
            return jsonify({"message":"参数错误"}), 400
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.OPERATOR:
            return jsonify({"message":"不能访问或登录已过期。"}), 400
        if role_num == 0:
            query_statement = "SELECT `id`,`username`,`avatar`,`phone`,`email`,`role_num`,`note`, " \
                              "DATE_FORMAT(`join_time`,'%Y-%m-%d') AS `join_time`,DATE_FORMAT(`update_time`,'%Y-%m-%d') AS `update_time`" \
                              "FROM `info_user`;"
        else:
            query_statement = "SELECT `id`,`username`,`avatar`,`phone`,`email`,`role_num`,`note`," \
                              "DATE_FORMAT(`join_time`,'%%Y-%%m-%%d') AS `join_time`," \
                              "DATE_FORMAT(`update_time`,'%%Y-%%m-%%d') AS `update_time` " \
                              "FROM `info_user` WHERE `role_num`=%d;" % role_num
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement)
        response_users = list()
        for user_item in cursor.fetchall():
            user_item['role_text'] = enums.user_roles.get(user_item['role_num'], '未知')
            response_users.append(user_item)
        return jsonify({"message":"获取信息成功!", "users": response_users})


class RetrieveUserView(MethodView):
    def patch(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.OPERATOR:
            return jsonify({"message":"不能这样操作或登录过期"}), 400
        to_role_num = body_json.get('role_to', enums.NORMAL)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`role_num` FROM `info_user` WHERE `id`=%d;" %uid
        cursor.execute(select_statement)
        user_role = cursor.fetchone()
        if not user_role:
            db_connection.close()
            return jsonify({"message":'修改的用户不存在。'}), 400
        if user_role['role_num'] <= enums.OPERATOR:
            db_connection.close()
            return jsonify({"message":"不能对当前人员进行这项设置!"}), 400
        update_statement = "UPDATE `info_user` SET `role_num`=%d WHERE `id`=%d;" %(to_role_num,uid)
        cursor.execute(update_statement)
        db_connection.commit()
        db_connection.close()

        return jsonify({"message":"修改成功!", "role_text": enums.user_roles.get(to_role_num, "")})
