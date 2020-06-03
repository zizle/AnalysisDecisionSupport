# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-25
# ------------------------
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection


class VarietyTrendTableView(MethodView):
    def get(self, vid):
        group = request.args.get('group', 0)
        try:
            group_id = int(group)
        except Exception:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询用户信息
        user_select = "SELECT `id`,`username`,`phone`,`note` " \
                      "FROM `info_user`;"
        cursor.execute(user_select)
        user_infos_all = cursor.fetchall()
        user_infos_all = {user_item['id']: user_item['username'] for user_item in user_infos_all}
        if group_id == 0:  # 获取全部
            query_statement = "SELECT * " \
                              "FROM `info_trend_table` " \
                              "WHERE `variety_id`=%d AND `is_active`=1;" % vid

        else:
            query_statement = "SELECT * " \
                              "FROM `info_trend_table` " \
                              "WHERE `variety_id`=%d AND `is_active`=1 AND `group_id`=%d;" % (vid, group_id)

        cursor.execute(query_statement)
        db_connection.close()
        query_result = cursor.fetchall()
        for record_item in query_result:
            record_item['author'] = user_infos_all[record_item['author_id']]
            record_item['updater'] = user_infos_all[record_item['updater_id']]
            record_item['create_time'] = record_item['create_time'].strftime('%Y-%m-%d')
            record_item['update_time'] = record_item['update_time'].strftime('%Y-%m-%d')
        return jsonify({"message": "获取品种表信息成功!", "tables": query_result})

