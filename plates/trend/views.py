# _*_ coding:utf-8 _*_
# Author: zizle
import os
import json
import datetime
import pandas as pd
from hashlib import md5
from flask import request, jsonify, render_template, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from db import MySQLConnection
from plates.user import enums
from settings import BASE_DIR
from utils.file_handler import hash_filename


class TrendGroupView(MethodView):
    def get(self):
        try:
            variety_id = int(request.args.get('variety'))
        except Exception as e:
            return jsonify({"message": "参数错误"}), 400
        select_statement = "SELECT `id`,`name` " \
                           "FROM `info_variety_trendgroup` " \
                           "WHERE `variety_id`=%d " \
                           "ORDER BY `sort` ASC;" % variety_id
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement)
        result = cursor.fetchall()
        return jsonify({"message": "查询成功", "groups": result})

    def post(self):
        body_json = request.json
        try:
            variety_id = int(body_json.get('variety_id'))
            group_name = body_json.get('name')
            if not group_name:
                raise ValueError('group ERROR')
            utoken = body_json.get('utoken')
        except Exception as e:
            return jsonify({"message": "参数错误"}), 400
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"message": "登录已过期或不能操作"})
        user_id = user_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询用户权限
        auth_statement = "SELECT `id` FROM `link_user_variety` " \
                         "WHERE `user_id`=%d AND `variety_id`=%d;" % (user_id, variety_id)
        cursor.execute(auth_statement)
        if not cursor.fetchone():
            db_connection.close()
            return jsonify({"message": "没有权限,不能这样操作"}), 400
        save_statement = "INSERT INTO `info_variety_trendgroup` " \
                         "(`name`,`variety_id`,`author_id`) " \
                         "VALUES (%s,%s,%s);"
        cursor.execute(save_statement, (group_name, variety_id, user_id))
        new_id = db_connection.insert_id()
        update_sort_statement = "UPDATE `info_variety_trendgroup` SET `sort`=%d WHERE `id`=%d;" % (new_id, new_id)
        cursor.execute(update_sort_statement)
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "添加组成功!"}), 201


class UserTrendTableView(MethodView):
    """
    用户自己的数据表
    get-获取所有自己已上传的数据表,(暂时前端未做使用)
    post-更新或新增一个数据表
    """
    def get(self, uid):
        group = request.args.get('group')
        variety = request.args.get('variety')
        try:
            group_id = int(group)
            variety_id = int(variety)
        except Exception:
            return jsonify({"message": "参数错误"}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if group_id == 0:  # 获取全部
            query_statement = "SELECT * " \
                              "FROM `info_trend_table` " \
                              "WHERE `author_id`=%d AND `variety_id`=%d AND `is_active`=1 " \
                              "ORDER BY `suffix_index`, `update_time` DESC;" % (uid, variety_id)

        else:
            query_statement = "SELECT * " \
                              "FROM `info_trend_table` " \
                              "WHERE `author_id`=%d AND `variety_id`=%d AND `is_active`=1 AND `group_id`=%d " \
                              "ORDER BY `suffix_index`, `update_time` DESC;" % (uid, variety_id, group_id)

        cursor.execute(query_statement)
        db_connection.close()
        query_result = cursor.fetchall()
        for record_item in query_result:
            record_item['create_time'] = record_item['create_time'].strftime('%Y-%m-%d')
            record_item['update_time'] = record_item['update_time'].strftime('%Y-%m-%d')
        return jsonify({"message": "查询成功!", "tables": query_result})

    def post(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.RESEARCH:
            return jsonify({"message": "登录已过期或无法这样操作"}), 400
        variety_id = body_json.get('variety_id')
        group_id = body_json.get('group_id')
        title = body_json.get('title', None)
        origin = body_json.get('origin', '')
        table_values = body_json.get('table_values')
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if not title:
            raise ValueError("NOT FOUND TITLE")
        user_id = int(user_info['id'])
        variety_id = int(variety_id)
        # 查询用户品种权限
        auth_statement = "SELECT linkuv.id,varietytb.name_en " \
                         "FROM `link_user_variety` AS linkuv INNER JOIN `info_variety` AS varietytb " \
                         "ON (linkuv.user_id=%d AND linkuv.variety_id=%d) AND varietytb.id=%d;" % (
                         user_id, variety_id, variety_id)
        cursor.execute(auth_statement)
        has_auth_variety = cursor.fetchone()
        if not has_auth_variety:
            raise ValueError("没有权限,不能这样操作")
        # 通过title的md5查询是否存在，进而判断是更新表还是新建表
        title_md5 = md5(title.encode('utf8')).hexdigest()
        table_exists = "SELECT `sql_table` " \
                       "FROM `info_trend_table` " \
                       "WHERE `variety_id`=%s AND `group_id`=%s AND `title_md5`=%s;"
        cursor.execute(table_exists, (variety_id, group_id, title_md5))
        exists_ret = cursor.fetchone()
        if exists_ret:  # 数据表存在，进行更新
            sql_table = exists_ret['sql_table']
            # print('数据表存在，进行更新', sql_table)
            # 查出已存在的最大数据时间
            select_max_date = "SELECT MAX(`column_0`) AS `max_date` " \
                              "FROM %s " \
                              "WHERE id>2;" % sql_table
            cursor.execute(select_max_date)
            max_date = cursor.fetchone()['max_date']
            # print(sql_table,max_date)
            db_connection.close()
            return self.update_exist_table(
                user_id=user_id,
                max_date=max_date,
                sql_table=sql_table,
                table_values=table_values
            )
        else:  # 新建一个表
            # print('新建一个表')
            # 查询表内最大的suffix_index
            select_max_sql_index = "SELECT MAX(`suffix_index`) AS  `max_index` " \
                                   "FROM `info_trend_table` " \
                                   "WHERE `variety_id`=%d;" % variety_id
            cursor.execute(select_max_sql_index)
            db_connection.close()  # 关闭，新建表时重新开启连接
            suffix_index_ret = cursor.fetchone()['max_index']
            suffix_index = 1 if not suffix_index_ret else suffix_index_ret + 1
            variety_name_en = has_auth_variety['name_en']
            sql_table_name = "{}_table_{}".format(variety_name_en, suffix_index)
            return self.create_new_table(
                user_id=user_id,
                variety_id=variety_id,
                group_id=group_id,
                title=title,
                title_md5=title_md5,
                suffix_index=suffix_index,
                sql_table_name=sql_table_name,
                table_values=table_values,
                origin=origin
            )

    def create_new_table(self, user_id, variety_id, group_id, title, title_md5, suffix_index, sql_table_name, table_values, origin):
        """
        新建一张数据表
        :param user_id: 创建表的用户ID
        :param variety_id: 表相关的品种ID
        :param group_id: 表所属数据组的ID
        :param title: 表的名称
        :param title_md5: 表名称的MD5
        :param suffix_index: 表的后缀索引
        :param sql_table_name: 实际数据表的sql名
        :param table_values: 实际数据
        :param origin: 备注，数据来源
        :return:
        """
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        table_headers = table_values.pop(0)  # 取出第一行为表头
        free_row = table_values.pop(0)  # 再取出第一行为自由行(即上传表中的第三行数据)
        # 取得table_values[0]列中的最大值和最小值
        table_values_df = pd.DataFrame(table_values)
        if table_values_df.empty:
            current_app.logger.error("user_id={}保存表:{}为空。".format(user_id, title))
            return jsonify({"message": "待保存数据为空"}), 400
        table_values_df[0] = pd.to_datetime(table_values_df[0], format='%Y-%m-%d')  # 转为时间格式
        table_values_df.drop_duplicates(subset=[0],keep='last', inplace=True)  # 去除日期完全一致的数据行
        max_date = (table_values_df[0].max()).strftime('%Y-%m-%d')
        min_date = (table_values_df[0].min()).strftime('%Y-%m-%d')
        # 再转为字符串时间
        table_values_df[0] = table_values_df[0].apply(lambda x: x.strftime('%Y-%m-%d'))
        # print('数据中最小时间:', min_date)
        # print('数据中最大时间:', max_date)
        # 插入自由行到数据中
        table_values_df.loc[-1] = free_row
        table_values_df.index = table_values_df.index + 1
        table_values_df.sort_index(inplace=True)
        # 插入表头到数据中
        table_values_df.loc[-1] = table_headers
        table_values_df.index = table_values_df.index + 1
        table_values_df.sort_index(inplace=True)
        table_values_df.columns = table_headers

        table_values = table_values_df.values.tolist()  # 转为列表
        # 根据表头生成sql需要的语句片段
        sqls_segment = self.generate_sql_segment(table_headers)
        create_col = sqls_segment['create']
        add_col = sqls_segment['add']
        values_col = sqls_segment['values']
        db_connection.begin()  # 开启事务
        try:
            # 增加数据表的信息表
            insert_statement = "INSERT INTO `info_trend_table` (`title`,`title_md5`,`suffix_index`,`sql_table`,`group_id`," \
                               "`variety_id`,`author_id`,`updater_id`,`origin`,`min_date`,`max_date`,`new_count`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            cursor.execute(insert_statement,
                           (title, title_md5, suffix_index, sql_table_name, group_id,
                            variety_id, user_id, user_id, origin,min_date, max_date, table_values_df.shape[0])
                           )
            # 创建实际数据表
            create_table_statement = "CREATE TABLE IF NOT EXISTS %s (" \
                                     "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT," \
                                     "`create_time` DATETIME NOT NULL DEFAULT NOW()," \
                                     "`update_time` DATETIME NOT NULL DEFAULT NOW()," \
                                     "%s);" % (sql_table_name, create_col)
            cursor.execute(create_table_statement)

            # 在新建表中加入数据
            insert_data_statement = "INSERT INTO %s (%s) " \
                                    "VALUES (%s);" % (sql_table_name, add_col, values_col)
            cursor.executemany(insert_data_statement, table_values)
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": str(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "添加数据表成功!"}), 201

    def update_exist_table(self,user_id, max_date, sql_table, table_values):
        """更新一张已存在的数据表(新增数据)"""
        max_date = pd.to_datetime(max_date, format='%Y-%m-%d')
        table_headers = table_values.pop(0)
        free_row = table_values.pop(0)  # 去除自由数据行
        table_values_df = pd.DataFrame(table_values)
        table_values_df[0] = pd.to_datetime(table_values_df[0], format='%Y-%m-%d')
        new_max_date = (table_values_df[0].max()).strftime('%Y-%m-%d')  # 数据的最大时间
        # min_date = (table_values_df[0].min()).strftime('%Y-%m-%d')
        table_values_df.drop_duplicates(subset=[0], keep='last', inplace=True)  # 去重
        table_values_df = table_values_df[table_values_df[0] > max_date]  # 取日期大于max_date的
        table_values_df[0] = table_values_df[0].apply(lambda x: x.strftime('%Y-%m-%d'))  # 日期再转为字符串
        if table_values_df.empty:
            # print(sql_table, "空增加")
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            today = datetime.datetime.today()
            update_info_statement = "UPDATE `info_trend_table` SET " \
                                    "`update_time`=%s,`updater_id`=%s,`new_count`=%s " \
                                    "WHERE `sql_table`=%s;"
            cursor.execute(update_info_statement, (today, user_id, 0, sql_table))
            db_connection.commit()
            db_connection.close()
            return jsonify({'message': "更新成功!"})
        else:
            # print(sql_table, '有数据')
            # 根据表头生成sql需要的语句片段
            sqls_segment = self.generate_sql_segment(table_headers)
            add_col = sqls_segment['add']
            values_col = sqls_segment['values']
            db_connection = MySQLConnection()
            cursor = db_connection.get_cursor()
            try:
                table_values = table_values_df.values.tolist()
                insert_data_statement = "INSERT INTO %s (%s) " \
                                        "VALUES (%s);" % (sql_table, add_col, values_col)
                cursor.executemany(insert_data_statement, table_values)
                # 更新数据信息
                today = datetime.datetime.today()
                update_info_statement = "UPDATE `info_trend_table` SET " \
                                        "`update_time`=%s,`updater_id`=%s,`max_date`=%s,`new_count`=%s " \
                                        "WHERE `sql_table`=%s;"
                cursor.execute(update_info_statement, (today, user_id, new_max_date, table_values_df.shape[0], sql_table))
                db_connection.commit()
            except Exception as e:
                db_connection.rollback()
                db_connection.close()
                return jsonify({"message":"更新数据失败:{}".format(e)}), 400
            else:
                db_connection.close()
                return jsonify({"message": "更新数据成功"})

    @staticmethod
    def generate_sql_segment(table_headers) -> dict:
        """
        根据表头列表生成sql语句片段
        :param table_headers:
        """
        create_col_str = ""
        add_col_str = ""
        values_str = ""
        for index in range(len(table_headers)):
            if index == len(table_headers) - 1:
                create_col_str += "`column_{}` VARCHAR(256) DEFAULT ''".format(index)
                add_col_str += "`column_{}`".format(index)
                values_str += "%s"
            else:
                create_col_str += "`column_{}` VARCHAR(256) DEFAULT '',".format(index)
                add_col_str += "`column_{}`,".format(index)
                values_str += "%s,"

        return {
            'create': create_col_str,
            'add': add_col_str,
            'values': values_str
        }


class TrendTableView(MethodView):
    """具体数据表的数据视图"""
    def get(self, tid):
        table_info_statement = "SELECT `sql_table` " \
                               "FROM `info_trend_table` " \
                               "WHERE id=%d AND `is_active`=1;" % tid
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(table_info_statement)
        fetch_ret = cursor.fetchone()
        sql_table = fetch_ret['sql_table']
        if not sql_table:
            db_connection.close()
            return jsonify({"message": "数据表已被删除."})
        query_statement = "SELECT * FROM %s;" % sql_table
        cursor.execute(query_statement)
        query_result = cursor.fetchall()
        db_connection.close()
        return jsonify({'message': '查询成功', 'records': query_result})

    def post(self, tid):
        """给一张表新增数据"""
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['id']
        new_contents = body_json.get('new_contents')
        if len(new_contents) <= 0:
            return jsonify({"message": '没有发现任何新数据..'}), 400
        new_headers = body_json.get('new_header')
        select_table_info = "SELECT `sql_table` " \
                            "FROM `info_trend_table` " \
                            "WHERE `is_active`=1 AND `id`=%d;" % tid
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_table_info)
        table_info = cursor.fetchone()
        table_sql_name = table_info['sql_table']
        if not table_sql_name:
            db_connection.close()
            return jsonify({"message": "数据表不存在"}), 400
        col_str = ""
        content_str = ""
        for col_index in range(len(new_headers)):
            if col_index == len(new_headers) - 1:
                col_str += "`column_{}`".format(col_index)
                content_str += "%s"
            else:
                col_str += "`column_{}`,".format(col_index)
                content_str += "%s,"
        insert_statement = "INSERT INTO `%s` (%s) " \
                           "VALUES (%s);" % (table_sql_name, col_str, content_str)
        today = datetime.datetime.today()
        try:
            cursor.executemany(insert_statement, new_contents)
            update_info_statement = "UPDATE `info_trend_table` " \
                                    "SET `update_time`=%s, `updater_id`=%s " \
                                    "WHERE `id`=%s;"
            cursor.execute(update_info_statement, (today, user_id, tid))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({'message': "失败{}".format(e)})
        else:
            db_connection.close()
            return jsonify({"message": '添加成功'}), 201

    def put(self, tid):
        """修改id=tid的表内的指定一行数据"""
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['id']
        record_id = body_json.get('record_id')
        record_content = body_json.get('record_content')
        # 第一列的数据类型检测
        try:
            record_content[0] = datetime.datetime.strptime(record_content[0], '%Y-%m-%d').strftime('%Y-%m-%d')
        except Exception as e:
            return jsonify({"message":"第一列时间数据格式错误!\n{}".format(e)}), 400
        select_table_info = "SELECT `sql_table` " \
                            "FROM `info_trend_table` " \
                            "WHERE `is_active`=1 AND `id`=%d;" % tid
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_table_info)
        table_info = cursor.fetchone()
        table_sql_name = table_info['sql_table']
        if not table_sql_name:
            db_connection.close()
            return jsonify({"message": "数据表不存在"}), 400
        # 修改数据
        col_str = ""
        for col_index in range(len(record_content)):
            if col_index == len(record_content) - 1:
                col_str += "`column_{}`=%s".format(col_index)
            else:
                col_str += "`column_{}`=%s,".format(col_index)
        update_statement = "UPDATE `%s` " \
                           "SET %s " \
                           "WHERE `id`=%s;" % (table_sql_name, col_str, record_id)
        # print("修改的sql:\n", update_statement)
        try:
            today = datetime.datetime.today()
            cursor.execute(update_statement, record_content)
            update_table_info = "UPDATE `info_trend_table` " \
                                "SET `updater_id`=%s,`update_time`=%s " \
                                "WHERE `id`=%s;"
            cursor.execute(update_table_info, (user_id, today, tid))
            db_connection.commit()
        except Exception as e:
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "修改失败{}".format(e)}), 400
        else:
            db_connection.close()
            return jsonify({"message": "修改记录成功!"}), 200

    def delete(self, tid):
        """删除数据表"""
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message":"登录已过期.."}), 400
        user_id = user_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 先找到原数据表
        if user_info["role_num"] <= 2:
            select_statement = "SELECT `id`,`sql_table` FROM `info_trend_table` WHERE `id`=%s;"
            cursor.execute(select_statement, (tid,))
        else:
            select_statement = "SELECT `id`,`sql_table` FROM `info_trend_table` WHERE `id`=%s AND `author_id`=%s;"
            cursor.execute(select_statement, (tid, user_id))
        fetch_one = cursor.fetchone()
        if not fetch_one:
            db_connection.close()
            return jsonify({"message": "删除他人数据就是谋财害命..."}), 400
        else:
            db_connection.begin()
            try:
                sql_table = fetch_one['sql_table']
                table_id = fetch_one['id']
                # 删除根据此表数据画的图
                delete_relate_chart = "DELETE FROM `info_trend_chart` " \
                                      "WHERE `table_id`=%s;"
                cursor.execute(delete_relate_chart, table_id)
                # 删除表
                drop_statement = "DROP TABLE %s;" % sql_table
                # 删除表记录
                delete_statement = "DELETE FROM `info_trend_table` " \
                                   "WHERE `id`=%s AND `author_id`=%s;"
                cursor.execute(delete_statement, (tid, user_id))
                cursor.execute(drop_statement)
                db_connection.commit()
            except Exception:
                db_connection.rollback()
                db_connection.close()
                return jsonify({"message":"删除出错了..."}), 400
            else:
                db_connection.close()
                return jsonify({"message": "这张表已烟消云散..."})


class UserTrendChartView(MethodView):  # 现已关闭本接口
    def get(self): # 临时接口：同步旧版已保存的图形
        """获取当前用户的所有设置的数据图"""
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        variety_id = request.args.get('variety')
        is_render = request.args.get('is_render', False)
        try:
            variety_id = int(variety_id)
        except Exception:
            return jsonify({"message":'参数错误'}), 400
        if variety_id == 0:
            # query_statement = "SELECT * FROM `info_trend_chart` " \
            #                   "WHERE `author_id`=%s;"
            query_statement = "SELECT * FROM `info_trend_chart`;"
            cursor.execute(query_statement)
        query_ret = cursor.fetchall()
        records = list()
        for item in query_ret:
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            item['update_time'] = item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            records.append(item)
        if is_render:
            return render_template('trend/charts_render.html', user_charts=records)
        else:
            return jsonify({'message': '查询成功', 'charts_info': records})

    # 临时接口：同步旧版已保存的图形
    def post(self):
        body_json = request.json
        create_time = datetime.datetime.strptime(body_json.get('create_time'), '%Y-%m-%d %H:%M:%S')
        update_time = datetime.datetime.strptime(body_json.get('update_time'), '%Y-%m-%d %H:%M:%S')
        author_id = body_json.get('author_id')
        title = body_json.get('title')
        table_id = body_json.get('table_id')
        variety_id = body_json.get('variety_id')
        decipherment = body_json.get('decipherment')
        is_trend_show = body_json.get('is_trend_show')
        is_variety_show = body_json.get('is_variety_show')
        chart_options = body_json.get('chart_options')

        configs_filename = hash_filename(str(author_id) + '.json')

        local_folder = 'fileStorage/chartconfigs/{}/{}/{}/'.format(author_id, create_time.strftime("%Y"), create_time.strftime("%m"))
        save_folder = os.path.join(BASE_DIR, local_folder)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        save_path = os.path.join(save_folder, configs_filename)
        config_sql_path = local_folder + configs_filename  # 保存到sql的地址
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(chart_options, f, indent=4)
        # print(config_sql_path, len(config_sql_path))
        # 保存到sql中
        insert_statement = "INSERT INTO `info_trend_echart` " \
                           "(`create_time`,`update_time`,`author_id`,`title`,`table_id`,`variety_id`,`options_file`,`decipherment`,`is_trend_show`,`is_variety_show`)" \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 保存表信息
        try:
            cursor.execute(insert_statement, (create_time,update_time,author_id, title, table_id, variety_id, config_sql_path, decipherment, is_trend_show,is_variety_show))
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("用户={}保存图形配置错误:{}".format(author_id, e))
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({"message": "保存失败了!"}), 400
        else:
            db_connection.close()
            return jsonify({"message":"保存成功."}), 201


    # def post(self, uid):
    #     body_json = request.json
    #     title = body_json.get('title', None)
    #     table_id = body_json.get('table_id', None)
    #     bottom_axis = body_json.get('bottom_axis', None)
    #     left_axis = body_json.get('left_axis', None)
    #     if not all([title, table_id, bottom_axis, left_axis]):
    #         return jsonify({'message': '参数不足'}), 400
    #     is_watermark = body_json.get('is_watermark', False)
    #     watermark = body_json.get('watermark', '')
    #     decipherment = body_json.get('decipherment', '')
    #     right_axis = body_json.get('right_axis', '{}')
    #     # 通过table_id获取group_id 和variety_id
    #     db_connection = MySQLConnection()
    #     cursor = db_connection.get_cursor()
    #     table_info_statement = "SELECT `sql_table`,`group_id`,`variety_id` " \
    #                            "FROM info_trend_table " \
    #                            "WHERE `id`=%s;"
    #     cursor.execute(table_info_statement, table_id)
    #     fetch_table_one = cursor.fetchone()
    #     sql_table = fetch_table_one['sql_table']
    #     variety_id = fetch_table_one['variety_id']
    #     group_id = fetch_table_one['group_id']
    #     # save_chart
    #     save_chart_statement = "INSERT INTO `info_trend_chart` (" \
    #                            "`title`, `table_id`,`sql_table`,`is_watermark`,`watermark`,`variety_id`, `group_id`," \
    #                            "`bottom_axis`,`left_axis`,`right_axis`,`author_id`,`updater_id`,`decipherment`) " \
    #                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    #     cursor.execute(save_chart_statement, (title, table_id, sql_table, is_watermark, watermark, variety_id, group_id,
    #                                           bottom_axis, left_axis, right_axis, uid, uid, decipherment)
    #                    )
    #     db_connection.commit()
    #     db_connection.close()
    #     return jsonify({"message":'保存配置成功'}), 201
