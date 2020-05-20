# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-20
# ------------------------
import datetime
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection
from utils.client import get_client
from utils.psd_handler import verify_json_web_token


class UserDataSourceConfigView(MethodView):
    def get(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({'message': '请登录后再操作..'}), 400
        user_id = user_info['id']
        variety_id = body_json.get('variety_id', None)
        machine_code = body_json.get('machine_code')
        client_info = get_client(machine_code)
        if not all([user_id, variety_id, client_info]):
            return jsonify({'message': '参数错误'}), 400
        client_id = client_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT * FROM `info_tablesource_configs` " \
                           "WHERE `variety_id`=%s AND `client_id`=%s AND `user_id`=%s;"
        cursor.execute(select_statement, (variety_id, client_id, user_id))
        records = cursor.fetchall()
        configs = list()
        for item in records:
            new = dict()
            new['id'] = item['id']
            new['update_time'] = item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            new['variety_name'] = item['variety_name']
            new['variety_id'] = item['variety_id']
            new['group_name'] = item['group_name']
            new['group_id'] = item['group_id']
            new['file_folder'] = item['file_folder']
            configs.append(new)
        return jsonify({'message': '查询成功', 'configs': configs})

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({'message': '请登录后再操作..'}), 400
        user_id = user_info['id']
        variety_name = body_json.get('variety_name', '')
        variety_id = body_json.get('variety_id', None)
        group_name = body_json.get('group_name', '')
        group_id = body_json.get('group_id', None)
        machine_code = body_json.get('machine_code')
        file_folder = body_json.get('file_folder', None)
        client_info = get_client(machine_code)
        if not all([user_id, variety_id, group_id, client_info, file_folder]):
            return jsonify({'message': '参数错误'}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        now = datetime.datetime.now()
        client_id = client_info['id']
        # 查找当前配置是否存在
        exist_statement = "SELECT `id` FROM `info_tablesource_configs` " \
                          "WHERE `client_id`=%s AND `variety_id`=%s AND `group_id`=%s AND `user_id`=%s;"
        cursor.execute(exist_statement, (client_id, variety_id, group_id, user_id))
        record_exist = cursor.fetchone()
        if record_exist:  # 更新
            exist_id = record_exist['id']
            update_statement = "UPDATE `info_tablesource_configs` SET " \
                               "`update_time`=%s,`variety_name`=%s, `variety_id`=%s,`group_name`=%s,`group_id`=%s, `client_id`=%s,`user_id`=%s,`file_folder`=%s " \
                               "WHERE `id`=%s;"
            cursor.execute(update_statement, (now, variety_name, variety_id, group_name, group_id, client_id, user_id, file_folder, exist_id))
        else:
            insert_statement = "INSERT INTO `info_tablesource_configs` " \
                               "(`update_time`,`variety_name`, `variety_id`,`group_name`,`group_id`, `client_id`,`user_id`,`file_folder`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s);" \

            cursor.execute(insert_statement, (now, variety_name, variety_id, group_name, group_id, client_id, user_id, file_folder))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message':'配置成功!'})

    def patch(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({'message': '请登录后再操作..'}), 400
        user_id = user_info['id']
        variety_id = body_json.get('variety_id', None)
        group_id = body_json.get('group_id', None)
        machine_code = body_json.get('machine_code')
        client_info = get_client(machine_code)
        if not all([user_id, variety_id, client_info, group_id]):
            return jsonify({'message': '参数错误'}), 400
        client_id = client_info['id']
        now = datetime.datetime.now()
        update_statement = "UPDATE `info_tablesource_configs` " \
                           "SET `update_time`=%s " \
                           "WHERE `client_id`=%s AND `user_id`=%s AND `variety_id`=%s AND `group_id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(update_statement, (now, client_id, user_id, variety_id, group_id))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message':'修改成功'})

