# _*_ coding:utf-8 _*_
# __Author__： zizle
import datetime
from flask import request, jsonify
from db import MySQLConnection
from flask.views import MethodView
from utils.client import get_client
from utils.psd_handler import verify_json_web_token


class ClientView(MethodView):
    def post(self):
        body_json = request.json
        machine_code = body_json.get('machine_code', '')
        is_manager = body_json.get('is_manager', 0)
        if not machine_code:
            return jsonify("NOT FOUND machine_code!"), 400
        query_statement = "SELECT `id` FROM `info_client` WHERE `machine_code`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, machine_code)
        client = cursor.fetchone()
        if not client:
            # 创建客户端
            insert_statement = "INSERT INTO `info_client` (`machine_code`, `is_manager`) VALUES (%s, %s);"
            cursor.execute(insert_statement, (machine_code, is_manager))
        else:
            # 更新打开时间
            now = datetime.datetime.now()
            update_statement = "UPDATE `info_client` SET `update_time`=%s WHERE `id`=%s;"
            cursor.execute(update_statement, (now, client['id']))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":"检测或注册客户端成功!",'machine_code': machine_code})


class ModuleView(MethodView):
    def get(self):
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message":"参数错误!"}), 400
        module_level = user_info["role_num"]
        query_pmodule_statement = "SELECT `id`,`name` FROM `info_module` " \
                                  "WHERE `parent_id` IS NULL AND `level`>=%s AND `is_active`=1;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_pmodule_statement, module_level)
        parent_modules = cursor.fetchall()
        response_data = list()
        for p_module_item in parent_modules:
            sub_query_statement = "SELECT `id`,`name`,`parent_id`,`level` FROM `info_module` " \
                                  "WHERE `parent_id`=%s AND `level` >=%s AND `is_active`=1;"
            cursor.execute(sub_query_statement, (p_module_item['id'], module_level))
            p_module_item['subs'] = cursor.fetchall()
            response_data.append(p_module_item)
        return jsonify({"message":"查询成功!", "modules": response_data})

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken',None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message":"登录已过期!"}), 400
        if user_info['role_num'] > 2:
            return jsonify({"message": "没有权限进行这个操作!"}), 400
        module_name = body_json.get('module_name', None)
        parent_id = body_json.get('parent_id', None)
        if not module_name:
            return jsonify({"message": "参数错误! NOT FOUND NAME."}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            if not parent_id:
                insert_statement = "INSERT INTO `info_module` (`name`) VALUES (%s);"
                cursor.execute(insert_statement, module_name)
            else:
                parent_id = int(parent_id)
                insert_statement = "INSERT INTO `info_module`(`name`,`parent_id`) VALUES (%s,%s);"
                cursor.execute(insert_statement,(module_name, parent_id))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "添加失败{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加成功!"}), 201
