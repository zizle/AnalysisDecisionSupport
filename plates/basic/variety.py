# _*_ coding:utf-8 _*_
# Author: zizle
from operator import itemgetter
from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from .enums import ZH_EXGS


class VarietyView(MethodView):
    def get(self):
        way = request.args.get('way')
        if not way or way not in ["group", "exchange"]:
            return jsonify({"message":"参数错误!", "variety":[]}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if way == "group":
            select_statement = "SELECT `id`,`name` " \
                               "FROM `info_variety` " \
                               "WHERE `parent_id` IS NULL ORDER BY `sort`;"
            cursor.execute(select_statement)
            variety_groups = cursor.fetchall()
            for group_item in variety_groups:
                query_subs_statement = "SELECT `id`,`name`,`name_en`, `parent_id`,`exchange` " \
                                       "FROM `info_variety` " \
                                       "WHERE `parent_id`=%s ORDER BY `sort`;"
                cursor.execute(query_subs_statement, group_item['id'])
                group_item['subs'] = cursor.fetchall()
            response_data = variety_groups
        else:
            select_statement = "SELECT `id`,`name`,`name_en`, `parent_id`,`exchange`,`sort` " \
                               "FROM `info_variety` " \
                               "WHERE `parent_id` IS NOT NULL AND `is_active`=1;"
            cursor.execute(select_statement)
            query_result = cursor.fetchall()
            response_data = self.key_sort_group(query_result)
        return jsonify({"message":"获取信息成功!", "variety": response_data})

    @staticmethod
    def key_sort_group(sort_list):
        """对列表中dict数据指定key排序，分组"""
        result = dict()
        sort_list.sort(key=itemgetter('sort'))  # sort排序；无返回值
        for item in sort_list:
            if ZH_EXGS.get(item['exchange']) not in result:
                result[ZH_EXGS.get(item['exchange'])] = list()
            result[ZH_EXGS.get(item['exchange'])].append(item)
        return result

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录已过期!"}), 400
        if user_info['role_num'] > 2:
            return jsonify({"message": "没有权限进行这个操作!"}), 400
        variety_name = body_json.get('variety_name', None)
        variety_name_en = body_json.get('variety_name_en', None)
        exchange_num = body_json.get('exchange_num', 0)
        parent_id = body_json.get('parent_num', 0)
        if not variety_name:
            return jsonify("参数错误! NOT FOUND NAME."), 400
        # 保存
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            if not parent_id:
                insert_statement = "INSERT INTO `info_variety` (`name`) VALUES (%s);"
                cursor.execute(insert_statement, variety_name)
            else:
                parent_id = int(parent_id)
                exchange_num = int(exchange_num)
                variety_name_en = variety_name_en.upper()
                insert_statement = "INSERT INTO `info_variety` (`name`,`name_en`,`parent_id`,`exchange`) VALUES (%s,%s,%s,%s);"
                cursor.execute(insert_statement, (variety_name, variety_name_en, parent_id, exchange_num))
            new_vid = db_connection.insert_id()
            cursor.execute("UPDATE `info_variety` SET `sort`=%d WHERE `id`=%d;" % (new_vid, new_vid))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            current_app.logger.error("增加品种错误:{}".format(e))
            return jsonify({"message":"增加品种错误."}), 400
        else:
            db_connection.close()
            return jsonify({"message":"增加品种成功!"}), 201

