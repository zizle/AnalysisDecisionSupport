# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-25
# ------------------------
from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token


class OnlyMeVarietyTrendTableView(MethodView):
    """ 我上传的数据表接口 """
    def get(self, vid):
        group = request.args.get('group', 0)
        utoken = request.args.get('token', None)
        try:
            if not utoken:
                raise ValueError("token not found.")
            user_info = verify_json_web_token(utoken)
            if not user_info:
                raise ValueError("must be logged.")
            group_id = int(group)
            user_id = int(user_info["id"])
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

        if group_id == 0:
            query_statement = "SELECT id,create_time,update_time,variety_id,suffix_index,title," \
                              "author_id,updater_id,new_count,is_active " \
                              "FROM `info_trend_table`" \
                              "WHERE author_id=%s AND variety_id=%s " \
                              "ORDER BY suffix_index,update_time DESC;"
            cursor.execute(query_statement, (user_id, vid))
        else:
            query_statement = "SELECT id,create_time,update_time,variety_id,suffix_index,title," \
                              "author_id,updater_id,new_count,is_active " \
                              "FROM `info_trend_table`" \
                              "WHERE author_id=%s AND variety_id=%s AND  group_id=%s " \
                              "ORDER BY suffix_index,update_time DESC;"
            cursor.execute(query_statement, (user_id, vid, group_id))
        query_result = cursor.fetchall()

        for record_item in query_result:
            record_item['author'] = user_infos_all[record_item['author_id']]
            record_item['updater'] = user_infos_all[record_item['updater_id']]
            record_item['create_time'] = record_item['create_time'].strftime('%Y-%m-%d')
            record_item['update_time'] = record_item['update_time'].strftime('%Y-%m-%d')
        db_connection.close()
        return jsonify({"message": "获取品种表信息成功!", "tables": query_result})


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
            # query_statement = "SELECT * " \
            #                   "FROM `info_trend_table` " \
            #                   "WHERE `variety_id`=%d AND `is_active`=1 ORDER BY `variety_id`,`suffix_index`;" % vid

            query_statement = "SELECT ttable.*,(SELECT COUNT(tchart.id) FROM `info_trend_echart` AS tchart WHERE ttable.id=tchart.table_id ) AS `charts_count` " \
                              "FROM `info_trend_table` AS ttable " \
                              "WHERE ttable.variety_id=%d ORDER BY ttable.is_active DESC,ttable.suffix_index,ttable.update_time DESC;" % vid

        else:
            query_statement = "SELECT ttable.*,(SELECT COUNT(tchart.id) FROM `info_trend_echart` AS tchart WHERE ttable.id=tchart.table_id ) AS `charts_count` " \
                              "FROM `info_trend_table` AS ttable " \
                              "WHERE ttable.variety_id=%d AND ttable.group_id=%d ORDER BY ttable.is_active DESC,ttable.suffix_index,ttable.update_time DESC;" % (vid, group_id)

            # query_statement = "SELECT * " \
            #                   "FROM `info_trend_table` " \
            #                   "WHERE `variety_id`=%d AND `is_active`=1 AND `group_id`=%d ORDER BY `variety_id`,`suffix_index`;" % (vid, group_id)

        cursor.execute(query_statement)
        db_connection.close()
        query_result = cursor.fetchall()

        for record_item in query_result:
            record_item['author'] = user_infos_all[record_item['author_id']]
            record_item['updater'] = user_infos_all[record_item['updater_id']]
            record_item['create_time'] = record_item['create_time'].strftime('%Y-%m-%d')
            record_item['update_time'] = record_item['update_time'].strftime('%Y-%m-%d')
        return jsonify({"message": "获取品种表信息成功!", "tables": query_result})

    # 修改表的排序
    def put(self, vid):
        body_json = request.json
        current_id = body_json.get('current_id', None)
        current_suffix = body_json.get('current_suffix', None)
        target_id = body_json.get('target_id', None)
        target_suffix = body_json.get('target_suffix', None)

        if not all([current_id, current_suffix, target_id, target_suffix]):
            return jsonify({"message": "缺少参数.."}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            update_statement = "UPDATE `info_trend_table` SET `suffix_index`=%s WHERE `id`=%s;"
            cursor.execute(update_statement, (current_suffix, target_id))
            cursor.execute(update_statement, (target_suffix, current_id))
        except Exception as e:
            db_connection.rollback()
            current_app.logger.error("修改数据表顺序错误{}".format(e))
            db_connection.close()
            return jsonify({"message": "修改失败"}), 400
        else:
            db_connection.commit()
            resp_data = {
                "current_id": current_id,
                "current_suffix": target_suffix,
                "target_id": target_id,
                "target_suffix": current_suffix
            }
            return jsonify({"message": "修改成功", "indexes": resp_data})
