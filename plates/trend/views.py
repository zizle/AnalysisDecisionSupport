# _*_ coding:utf-8 _*_
# Author: zizle
from flask import request, jsonify, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from db import MySQLConnection
from plates.user import enums

class TrendGroupView(MethodView):
    def get(self):
        try:
            variety_id = int(request.args.get('variety'))
        except Exception as e:
            return jsonify({"message":"参数错误"}), 400
        select_statement = "SELECT `id`,`name` " \
                           "FROM `info_variety_trendgroup` " \
                           "WHERE `variety_id`=%d " \
                           "ORDER BY `sort` ASC;" % variety_id
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement)
        result = cursor.fetchall()
        return jsonify({"message":"查询成功", "groups": result})


    def post(self):
        body_json = request.json
        try:
            variety_id = int(body_json.get('variety_id'))
            group_name = body_json.get('name')
            if not group_name:
                raise ValueError('group ERROR')
            utoken = body_json.get('utoken')
        except Exception as e:
            return jsonify({"message":"参数错误"}), 400
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"登录已过期或不能操作"})
        user_id = user_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询用户权限
        auth_statement = "SELECT `id` FROM `link_user_variety` " \
                         "WHERE `user_id`=%d AND `variety_id`=%d;"%(user_id,variety_id)
        cursor.execute(auth_statement)
        if not cursor.fetchone():
            db_connection.close()
            return jsonify({"message":"没有权限,不能这样操作"}), 400
        save_statement = "INSERT INTO `info_variety_trendgroup` " \
                         "(`name`,`variety_id`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        cursor.execute(save_statement, (group_name, variety_id, user_id))
        new_id = db_connection.insert_id()
        update_sort_statement = "UPDATE `info_variety_trendgroup` SET `sort`=%d WHERE `id`=%d;" %(new_id, new_id)
        cursor.execute(update_sort_statement)
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":"添加组成功!"}), 201


class TrendTableView(MethodView):
    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"message":"登录已过期或无法这样操作"}), 400
        variety_id = body_json.get('variety_id')
        group_id = body_json.get('group_id')
        title = body_json.get('title', None)
        origin = body_json.get('origin', None)
        table_values = body_json.get('table_values')
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            if not all([title, origin]):
                raise ValueError("NOT FOUND TITLE, ORIGIN")
            user_id = int(user_info['id'])
            variety_id = int(variety_id)
            # 查询用户品种权限
            auth_statement = "SELECT linkuv.id,varietytb.name_en " \
                             "FROM `link_user_variety` AS linkuv INNER JOIN `info_variety` AS varietytb " \
                             "ON (linkuv.user_id=%d AND linkuv.variety_id=%d) AND varietytb.id=%d;" % (user_id, variety_id, variety_id)
            cursor.execute(auth_statement)
            has_auth_variety = cursor.fetchone()
            if not has_auth_variety:
                raise ValueError("没有权限,不能这样操作")
            # 查询表内最大的sql_index
            select_max_sql_index = "SELECT MAX(`sql_index`) AS  `max_index` " \
                                   "FROM `info_trend_table` WHERE `variety_id`=%d;" % variety_id
            cursor.execute(select_max_sql_index)
            max_index_ret = cursor.fetchone()['max_index']
            max_index = 1 if not max_index_ret else max_index_ret + 1
            variety_name_en = has_auth_variety['name_en']
            sql_table_name = "`{}_table_{}`".format(variety_name_en, max_index)
            # 增加数据信息表
            insert_statement = "INSERT INTO `info_trend_table` (`title`,`sql_index`,`sql_table`,`group_id`," \
                               "`variety_id`,`author_id`,`updater_id`,`origin`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
            # print("增加信息表:\n", insert_statement)
            cursor.execute(insert_statement, (title, max_index, sql_table_name, group_id, variety_id, user_id, user_id, origin))

            # 根据表头数量创建列数量
            table_headers = table_values['headers']
            table_contents = table_values['contents']
            create_col_str = ""
            add_col_str = ""
            values_str = ""
            for index in range(len(table_headers)):
                if index == len(table_headers) - 1:
                    create_col_str += "`column_{}` VARCHAR(128) DEFAULT ''".format(index)
                    add_col_str += "`column_{}`".format(index)
                    values_str += "%s"
                else:
                    create_col_str += "`column_{}` VARCHAR(128) DEFAULT '',".format(index)
                    add_col_str += "`column_{}`,".format(index)
                    values_str += "%s,"
            # 创建数据表
            create_table_statement = "CREATE TABLE IF NOT EXISTS %s (" \
                                     "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT," \
                                     "`create_time` DATETIME NOT NULL DEFAULT NOW()," \
                                     "`update_time` DATETIME NOT NULL DEFAULT NOW()," \
                                     "%s" \
                                     ");" % (sql_table_name, create_col_str)
            # print("创建数据库表:\n", create_table_statement)
            cursor.execute(create_table_statement)

            # 增加数据
            insert_data_statement = "INSERT INTO %s (%s) " \
                                    "VALUES (%s);" % (sql_table_name, add_col_str, values_str)
            # print("添加实际数据:\n", insert_data_statement)
            cursor.executemany(insert_data_statement, table_contents)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message":str(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message":"添加数据表成功!"}), 201


