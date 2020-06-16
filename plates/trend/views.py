# _*_ coding:utf-8 _*_
# Author: zizle
import os
import ast
import datetime
import pandas as pd
from hashlib import md5
import pyecharts.options as opts
from pyecharts.charts import Line, Bar
from flask import request, jsonify, render_template
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from db import MySQLConnection
from plates.user import enums
from settings import BASE_DIR


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
                              "WHERE `author_id`=%d AND `variety_id`=%d AND `is_active`=1;" % (uid, variety_id)

        else:
            query_statement = "SELECT * " \
                              "FROM `info_trend_table` " \
                              "WHERE `author_id`=%d AND `variety_id`=%d AND `is_active`=1 AND `group_id`=%d;" % (uid, variety_id, group_id)

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
                              "WHERE id>1;" % sql_table
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
        # 取得table_values[0]列中的最大值和最小值
        table_values_df = pd.DataFrame(table_values)
        table_values_df[0] = pd.to_datetime(table_values_df[0], format='%Y-%m-%d')  # 转为时间格式
        table_values_df.drop_duplicates(subset=[0],keep='last', inplace=True)  # 去除日期完全一致的数据行
        max_date = (table_values_df[0].max()).strftime('%Y-%m-%d')
        min_date = (table_values_df[0].min()).strftime('%Y-%m-%d')
        # 再转为字符串时间
        table_values_df[0] = table_values_df[0].apply(lambda x: x.strftime('%Y-%m-%d'))
        # print('数据中最小时间:', min_date)
        # print('数据中最大时间:', max_date)
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
                               "`variety_id`,`author_id`,`updater_id`,`origin`,`min_date`,`max_date`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            cursor.execute(insert_statement,
                           (title, title_md5, suffix_index, sql_table_name, group_id,
                            variety_id, user_id, user_id, origin,min_date, max_date)
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

        table_values_df = pd.DataFrame(table_values)
        table_values_df[0] = pd.to_datetime(table_values_df[0], format='%Y-%m-%d')
        new_max_date = (table_values_df[0].max()).strftime('%Y-%m-%d')  # 数据的最大时间
        # min_date = (table_values_df[0].min()).strftime('%Y-%m-%d')
        table_values_df.drop_duplicates(subset=[0], keep='last', inplace=True)  # 去重
        table_values_df = table_values_df[table_values_df[0] > max_date]  # 取日期大于max_date的
        table_values_df[0] = table_values_df[0].apply(lambda x: x.strftime('%Y-%m-%d'))  # 日期再转为字符串
        if table_values_df.empty:
            # print(sql_table, "空增加")
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
                                        "`update_time`=%s,`updater_id`=%s,`max_date`=%s " \
                                        "WHERE `sql_table`=%s;"
                cursor.execute(update_info_statement, (today, user_id, new_max_date, sql_table))
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


class UserTrendChartView(MethodView):
    def get(self, uid):
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
            query_statement = "SELECT * FROM `info_trend_chart` " \
                              "WHERE `author_id`=%s;"
            cursor.execute(query_statement, uid)
        else:
            query_statement = "SELECT * FROM `info_trend_chart` " \
                              "WHERE `author_id`=%s  AND `variety_id`=%s;"
            cursor.execute(query_statement, (uid, variety_id))
        query_ret = cursor.fetchall()
        records = list()
        for item in query_ret:
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d')
            item['update_time'] = item['update_time'].strftime('%Y-%m-%d')
            records.append(item)
        if is_render:
            return render_template('trend/charts_render.html', user_charts=records)
        else:
            return jsonify({'message': '查询成功', 'charts_info': records})

    def post(self, uid):
        body_json = request.json
        title = body_json.get('title', None)
        table_id = body_json.get('table_id', None)
        bottom_axis = body_json.get('bottom_axis', None)
        left_axis = body_json.get('left_axis', None)
        if not all([title, table_id, bottom_axis, left_axis]):
            return jsonify({'message': '参数不足'}), 400
        is_watermark = body_json.get('is_watermark', False)
        watermark = body_json.get('watermark', '')
        decipherment = body_json.get('decipherment', '')
        right_axis = body_json.get('right_axis', '{}')
        # 通过table_id获取group_id 和variety_id
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        table_info_statement = "SELECT `sql_table`,`group_id`,`variety_id` " \
                               "FROM info_trend_table " \
                               "WHERE `id`=%s;"
        cursor.execute(table_info_statement, table_id)
        fetch_table_one = cursor.fetchone()
        sql_table = fetch_table_one['sql_table']
        variety_id = fetch_table_one['variety_id']
        group_id = fetch_table_one['group_id']
        # save_chart
        save_chart_statement = "INSERT INTO `info_trend_chart` (" \
                               "`title`, `table_id`,`sql_table`,`is_watermark`,`watermark`,`variety_id`, `group_id`," \
                               "`bottom_axis`,`left_axis`,`right_axis`,`author_id`,`updater_id`,`decipherment`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        cursor.execute(save_chart_statement, (title, table_id, sql_table, is_watermark, watermark, variety_id, group_id,
                                              bottom_axis, left_axis, right_axis, uid, uid, decipherment)
                       )
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":'保存配置成功'}), 201


class TrendChartOptionsView(MethodView):
    def get(self, cid):
        # 根据id获取图表配置参数
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT * FROM `info_trend_chart` WHERE `id`=%s;"
        cursor.execute(select_statement, cid)
        fetch_one = cursor.fetchone()
        # 处理图表配置参数
        if not fetch_one:
            c = Line()
        else:
            # 查询图表用的具体数据
            sql_table = fetch_one['sql_table']
            query_statement = "SELECT * FROM %s;" % sql_table
            cursor.execute(query_statement)
            query_ret = cursor.fetchall()
            data_headers = query_ret.pop(0)
            data_frame = pd.DataFrame(query_ret)
            db_connection.close()
            c = self.draw_chart(fetch_one, data_headers, data_frame)
        return c.dump_options_with_quotes()

    @staticmethod
    def draw_chart(params, headers, source_df):
        # print('headers', headers)
        # print(source_df)
        title = params['title']
        bottom_axis = ast.literal_eval(params['bottom_axis'])
        left_axis = ast.literal_eval(params['left_axis'])
        right_axis = ast.literal_eval(params['right_axis'])
        is_watermark = params['is_watermark']
        watermark = params['watermark']
        # print('标题:', title)
        # print('横轴:', bottom_axis, type(bottom_axis))
        # print('左轴:', left_axis, type(left_axis))
        # print('右轴:', right_axis, type(right_axis))
        # print('水印:', is_watermark, type(is_watermark))
        # 根据参数作图
        bottom = [key for key in bottom_axis.keys()][0]
        if bottom == 'column_0':
            date_format = bottom_axis['column_0']
            source_df[bottom] = pd.to_datetime(source_df[bottom], format='%Y-%m-%d')
            source_df[bottom] = source_df[bottom].apply(lambda x: x.strftime(date_format))
        # 对x轴进行排序
        sort_df = source_df.sort_values(by=bottom)
        # print(sort_df)

        try:
            # 进行画图
            x_axis_data = sort_df[bottom].values.tolist()
            # 由于pyecharts改变了overlap方法,读取左轴第一个数据类型进行绘制
            left_axis_copy = {key: val for key, val in left_axis.items()}
            # print("复制后的左轴参数:", left_axis_copy)
            first_key = list(left_axis_copy.keys())[0]
            first_datacol, first_type = first_key, left_axis_copy[first_key]
            del left_axis_copy[first_key]
            # init_opts = opts.InitOpts(
            #     width=str(self.chart_widget.width() - 20) + 'px',
            #     height=str(self.chart_widget.height() - 25) + 'px'
            # )
            if first_type == 'line':
                chart = Line()
                chart.add_xaxis(xaxis_data=x_axis_data)
                chart.add_yaxis(
                    series_name=headers[first_key],
                    y_axis=sort_df[first_key].values.tolist(),
                    label_opts=opts.LabelOpts(is_show=False),
                    # symbol='circle',
                    z_level=9,
                    is_smooth=True
                )
            elif first_type == 'bar':
                chart = Bar()
                chart.add_xaxis(xaxis_data=x_axis_data)
                chart.add_yaxis(
                    series_name=headers[first_key],
                    yaxis_data=sort_df[first_key].values.tolist(),
                    label_opts=opts.LabelOpts(is_show=False),
                )
            else:
                return
            # 1 绘制其他左轴数据
            # 根据参数画图
            for col_name, chart_type in left_axis_copy.items():
                if chart_type == 'line':
                    extra_c = (
                        Line()
                            .add_xaxis(xaxis_data=x_axis_data)
                            .add_yaxis(
                            series_name=headers[col_name],
                            y_axis=sort_df[col_name].values.tolist(),
                            label_opts=opts.LabelOpts(is_show=False),
                            z_level=9,
                            is_smooth=True
                        )
                    )
                elif chart_type == 'bar':
                    extra_c = (
                        Bar()
                            .add_xaxis(xaxis_data=x_axis_data)
                            .add_yaxis(
                            series_name=headers[col_name],
                            yaxis_data=sort_df[col_name].values.tolist(),
                            label_opts=opts.LabelOpts(is_show=False),
                        )
                    )
                else:
                    continue
                chart.overlap(extra_c)
            # 绘制其他右轴数据
            if right_axis:
                chart.extend_axis(
                    yaxis=opts.AxisOpts()
                )
            for col_name, chart_type in right_axis.items():
                if chart_type == 'line':
                    extra_c = (
                        Line()
                            .add_xaxis(xaxis_data=x_axis_data)
                            .add_yaxis(
                            series_name=headers[col_name],
                            y_axis=sort_df[col_name].values.tolist(),
                            label_opts=opts.LabelOpts(is_show=False),
                            z_level=9,
                            is_smooth=True,
                            yaxis_index=1
                        )
                    )
                elif chart_type == 'bar':
                    extra_c = (
                        Bar()
                            .add_xaxis(xaxis_data=x_axis_data)
                            .add_yaxis(
                            series_name=headers[col_name],
                            yaxis_data=sort_df[col_name].values.tolist(),
                            label_opts=opts.LabelOpts(is_show=False),
                            yaxis_index=1
                        )
                    )
                else:
                    continue
                chart.overlap(extra_c)
            image_path = os.path.join(BASE_DIR, '/ads/static/logo.png')
            if is_watermark:
                water_graphic_opts = opts.GraphicGroup(
                    graphic_item=opts.GraphicItem(
                        width=200,
                        left=100,
                        # left=self.chart_widget.width() / 2 - 150,
                        top='center',
                        bounding='raw',
                        z=-1,
                    ),
                    children=[
                        opts.GraphicImage(
                            graphic_item=opts.GraphicItem(
                                left=0,
                                top='center',
                            ),
                            graphic_imagestyle_opts=opts.GraphicImageStyleOpts(
                                image=image_path,
                                width=40,
                                height=40,
                                opacity=0.3
                            ),
                        ),
                        opts.GraphicText(
                            graphic_item=opts.GraphicItem(
                                left=42, top="center", z=-1
                            ),
                            graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                # 要显示的文本
                                text=watermark,
                                font="bold 35px Microsoft YaHei",
                                graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                                    fill="rgba(200,200,200,0.5)"
                                ),
                            )
                        )
                    ]
                )
            else:
                water_graphic_opts = None

            chart.set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    pos_left='center',
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type='cross'),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    axislabel_opts=opts.LabelOpts(rotate=-25, font_size=11,margin=6),
                    axistick_opts=opts.AxisTickOpts(is_align_with_label=True, length=3)
                 ),
                yaxis_opts=opts.AxisOpts(type_="value"),
                legend_opts=opts.LegendOpts(
                    type_='scroll',
                    pos_bottom='0%',
                    item_gap=25,
                    item_width=30,
                ),
                toolbox_opts=opts.ToolboxOpts(
                    is_show=True,
                    feature=opts.ToolBoxFeatureOpts(
                        save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(is_show=False),
                        data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=True),
                        magic_type=opts.ToolBoxFeatureMagicTypeOpts(type_=['line','bar']),
                        brush=opts.ToolBoxFeatureBrushOpts(type_='clear'),
                    )
                ),
                graphic_opts=water_graphic_opts,
            )

        except Exception:
            chart = Line()
        # grid = Grid()
        # grid.add(chart, grid_opts=opts.GridOpts(pos_bottom="25%", is_contain_label=True))
        return chart

    def patch(self, cid):

        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or int(user_info['id']) > enums.RESEARCH:
            return jsonify({"message": "登录过期或不能进行这样的操作。"}), 400

        decipherment = request.json.get('decipherment', None)  # 解说
        is_trend_show = request.json.get('is_trend_show', None)  # 首页展示
        is_variety_show = request.json.get('is_variety_show', None)  # 品种页展示
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if decipherment is not None:
            update_statement = "UPDATE `info_trend_chart` SET `decipherment`=%s WHERE `id`=%s AND `author_id`=%s;"
            cursor.execute(update_statement,(decipherment, cid, int(user_info['id'])))
        if is_trend_show is not None:
            is_trend_show = 1 if is_trend_show else 0
            update_statement = "UPDATE `info_trend_chart` SET `is_trend_show`=%s WHERE `id`=%s AND `author_id`=%s;"
            cursor.execute(update_statement, (is_trend_show, cid, int(user_info['id'])))
        if is_variety_show is not None:
            is_variety_show = 1 if is_variety_show else 0
            update_statement = "UPDATE `info_trend_chart` SET `is_variety_show`=%s WHERE `id`=%s AND `author_id`=%s;"
            cursor.execute(update_statement, (is_variety_show, cid, int(user_info['id'])))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message":"修改成功"})

    def delete(self, cid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        print(user_info)
        if not user_info or int(user_info['id']) > enums.RESEARCH:
            return jsonify({"message":"登录过期或不能进行这样的操作。"}), 400
        delete_statement = "DELETE FROM `info_trend_chart` WHERE `id`=%s AND `author_id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(delete_statement, (cid, int(user_info['id'])))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message':'删除成功!'})
