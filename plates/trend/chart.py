# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-08
# ------------------------
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from flask import request, jsonify, render_template, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
from utils.charts import chart_options_handler, season_chart_options_handler
from settings import BASE_DIR

"""关于图形的接口"""


class TrendTableChartView(MethodView):
    # 获取用户保存的图形信息接口
    def get(self):
        args_json = request.args
        user_info = verify_json_web_token(args_json.get('utoken', None))
        variety_id = int(args_json.get('vid', 0))
        is_json = args_json.get('is_json', False)
        if not user_info:
            return jsonify({"message": "query param `utoken` was required", "charts": []}), 400
        user_id = user_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if not variety_id:
            select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show`,`suffix_index` " \
                               "FROM `info_trend_echart` WHERE `author_id`=%s " \
                               "ORDER by `suffix_index`,`update_time` DESC;"
            cursor.execute(select_statement, (user_id, ))
        else:
            select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show`,`suffix_index` " \
                               "FROM `info_trend_echart` " \
                               "WHERE `author_id`=%s AND `variety_id`=%s " \
                               "ORDER by `suffix_index`,`update_time` DESC;"
            cursor.execute(select_statement, (user_id, variety_id))
        user_charts = cursor.fetchall()
        db_connection.close()
        if is_json:  # 返回json数据
            for chart_item in user_charts:
                chart_item['create_time'] = chart_item['create_time'].strftime("%Y-%m-%d")
                chart_item['update_time'] = chart_item['update_time'].strftime("%Y-%m-%d")
            return jsonify({"message": 'get current variety charts of user successfully!', "charts": user_charts})
        else:  # 直接渲染数据
            return render_template('trend/charts_render.html', user_charts=user_charts)

    # 用户新建保存图形配置信息json
    def post(self):
        body_json = request.json
        user_info = verify_json_web_token(body_json.get('utoken', None))
        if not user_info:
            return jsonify({"message": "登录过期了,重新登录后再保存..."}), 400
        user_id = user_info['id']
        chart_options = body_json.get('chart_options', None)
        title = body_json.get('title', None)  # 图表标题
        variety_id = body_json.get('variety_id', None)
        table_id = body_json.get('table_id', None)
        decipherment = body_json.get('decipherment', '')
        if not all([chart_options, title, variety_id, table_id]):
            return jsonify({"message": "参数错误...请填写图形标题名称"}), 400
        # configs file path
        configs_filename = hash_filename(str(user_id) + '.json')
        now = datetime.now()
        local_folder = 'fileStorage/chartconfigs/{}/{}/{}/'.format(user_id, now.strftime("%Y"), now.strftime("%m"))
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
                           "(`author_id`,`title`,`table_id`,`variety_id`,`options_file`,`decipherment`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 保存表信息
        try:
            cursor.execute(insert_statement, (user_id, title, table_id,variety_id, config_sql_path,decipherment))
            new_id = db_connection.insert_id()
            cursor.execute("UPDATE `info_trend_echart` SET `suffix_index`=%d WHERE `id`=%d;" % (new_id, new_id))
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("用户={}保存图形配置错误:{}".format(user_id, e))
            if os.path.exists(save_path):
                os.remove(save_path)
            return jsonify({"message": "保存失败了!"}), 400
        else:
            db_connection.close()
            return jsonify({"message": "保存成功!"}), 201

    # 修改图形排序
    def put(self):
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
            update_statement = "UPDATE `info_trend_echart` SET `suffix_index`=%s WHERE `id`=%s;"
            cursor.execute(update_statement, (current_suffix, target_id))
            cursor.execute(update_statement, (target_suffix, current_id))
        except Exception as e:
            db_connection.rollback()
            current_app.logger.error("修改图形顺序错误{}".format(e))
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


class TrendChartRetrieveView(MethodView):
    # 获取某个图形的配置进行展示图形
    def get(self, cid):
        chart_id = cid
        is_render = request.args.get("is_render", False)
        if not chart_id:
            return jsonify({"message": "query params `chart` is required!", "options": {}}), 400
        # 1根据id查询信息
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_echart = "SELECT infotchart.id,infotchart.title,infotchart.options_file,infotchart.decipherment," \
                        "infottable.sql_table " \
                        "FROM `info_trend_echart` AS infotchart " \
                        "INNER JOIN `info_trend_table` AS infottable " \
                        "ON infotchart.table_id=infottable.id " \
                        "WHERE infotchart.id=%s;"
        cursor.execute(select_echart, (chart_id,))
        # 2根据查询的文件位置读取配置文件
        chart_info = cursor.fetchone()
        if not chart_info:
            return jsonify({"message": "The chart options not found!", "options": {}}), 400
        if is_render:
            return render_template('trend/charts_render.html', user_charts=[chart_info])

        options_file_path = os.path.join(BASE_DIR, chart_info['options_file'])
        with open(options_file_path, 'r', encoding='utf-8') as f:
            options_content = json.load(f)
        # 根据table_sql和options_content处理图表配置问题
        chart_options = self.get_chart_options(cursor, chart_info['sql_table'], options_content)
        # 3根据配置文件配置图形参数返回前端
        db_connection.close()
        return jsonify({"message": "get chart options successfully!", "options": chart_options})

    @staticmethod
    def get_chart_options(cursor, sql_table, options_content):
        # get table source data
        cursor.execute("SELECT * FROM %s;" % sql_table)
        table_source_data = cursor.fetchall()
        table_headers_dict = table_source_data.pop(0)  # 头
        table_source_data.pop(0)  # third free row
        # print(table_headers_dict)
        source_df = pd.DataFrame(table_source_data)
        # 读取配置内的横轴格式,对source_df进行数据column_0数据排序
        x_axis = options_content['x_axis'][0]
        if x_axis['col_index'] == "column_0":  # 当横轴是时间轴的处理
            date_format = x_axis['date_format']
            source_df['column_0'] = pd.to_datetime(source_df['column_0'], format='%Y-%m-%d')
            source_df['column_0'] = source_df['column_0'].apply(lambda x: x.strftime(date_format))
            source_df = source_df.sort_values(by="column_0")  # 排序
            source_df.reset_index(drop=True, inplace=True)  # 重置数据索引
            x_axis_start = x_axis['start']
            x_axis_end = x_axis['end']
            last_weeks = x_axis.get('last_weeks', '')
            if x_axis_start:  # 切片取数
                start_year = datetime.strptime(x_axis_start, '%Y').strftime(date_format)
                source_df = source_df[start_year <= source_df['column_0']]
            if x_axis_end:  # 切片取数
                end_year = datetime.strptime(x_axis_end, '%Y').strftime(date_format)
                source_df = source_df[source_df['column_0'] <= end_year]
            if last_weeks:  # 最近几周的数据
                start_date = datetime.today() + timedelta(weeks=-int(last_weeks))
                start_date = start_date.strftime(date_format)
                source_df = source_df[start_date <= source_df['column_0']]
        else:  # 横轴非时间轴
            source_df = source_df.sort_values(by=x_axis['col_index'])  # 排序
            source_df.reset_index(drop=True, inplace=True)  # 重置数据索引
            x_axis_start = x_axis['start']
            x_axis_end = x_axis['end']
            if x_axis_start:
                source_df = source_df[int(x_axis_start):source_df.shape[0]]
            if x_axis_end:
                source_df = source_df[:int(x_axis_end)]
        # 处理完后的数据source_df进行绘图配置
        if options_content['typec'] == 'single':
            options = chart_options_handler(source_df, table_headers_dict, options_content)
        elif options_content['typec'] == 'single_season':
            options = season_chart_options_handler(source_df, options_content)
        else:
            options = {}
        return options

    # 修改图形的配置信息
    def post(self, cid):
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({"message": "登录已过期,重新登录后操作"}),400

        start_year = body_json.get('start', '')
        end_year = body_json.get('end', '')
        last_weeks = body_json.get('last_weeks', '')
        try:
            if start_year:
                if int(start_year) <= 0 or len(start_year) != 4:
                    raise ValueError('输入错误')
            if end_year:
                if int(end_year) <=0 or len(end_year) != 4:
                    raise ValueError('输入错误')
        except Exception as e:
            return jsonify({"message": "错误的输入值"}), 400

        # 连接数据库查找配置json
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_statement = "SELECT `id`,`options_file` " \
                          "FROM `info_trend_echart` WHERE `id`=%s AND `author_id`=%s;"
        cursor.execute(query_statement, (cid, user_info['id']))
        result = cursor.fetchone()
        db_connection.close()
        if not result:
            return jsonify({"message": "图形不存在了"}), 400
        opts_file_path = result['options_file']
        opts_file_path = os.path.join(BASE_DIR, opts_file_path)
        with open(opts_file_path, 'r') as file:
            option_content = json.load(file)
        option_content['x_axis'][0]["start"] = str(start_year)
        option_content['x_axis'][0]["end"] = str(end_year)
        option_content['x_axis'][0]["last_weeks"] = str(last_weeks)
        with open(opts_file_path, 'w', encoding='utf-8') as f:
            json.dump(option_content, f, indent=4)
        return jsonify({"message": "修改成功!"})

    # 修改图形的信息（首页显示,品种页显示,解说修改）
    def patch(self, cid):
        body_json = request.json
        user_info = verify_json_web_token(body_json.get('utoken', None))
        if not user_info or int(user_info['role_num']) > 4:
            return jsonify({"message": "登录过期或不能进行这样的操作。"}), 400
        decipherment = body_json.get('decipherment', '')  # 解说
        is_trend_show = body_json.get('is_trend_show', None)  # 首页展示
        is_variety_show = body_json.get('is_variety_show', None)  # 品种页展示

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        update_statement = "UPDATE `info_trend_echart` " \
                           "SET `decipherment`=%s,`is_trend_show`=%s,`is_variety_show`=%s,`update_time`=%s " \
                           "WHERE `id`=%s AND `author_id`=%s;"
        is_trend_show = 1 if is_trend_show else 0
        is_variety_show = 1 if is_variety_show else 0
        now = datetime.now()
        cursor.execute(update_statement, (decipherment, is_trend_show, is_variety_show, now, cid, user_info['id']))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '修改成功!'})

    def delete(self, cid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or int(user_info['role_num']) > 4:
            return jsonify({"message": "登录过期或不能进行这样的操作。"}), 400
        # 查询配置文件
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_option_file = "SELECT `id`,`options_file` FROM `info_trend_echart` WHERE `id`=%s AND `author_id`=%s;"
        cursor.execute(select_option_file, (cid, user_info['id']))
        fetch_one = cursor.fetchone()
        if not fetch_one:
            db_connection.close()
            return jsonify({'message':'系统中没有此图形信息。'}), 400
        options_file_path = fetch_one['options_file']
        options_file_path = os.path.join(BASE_DIR, options_file_path)
        try:
            delete_statement = "DELETE FROM `info_trend_echart` WHERE `id`=%s AND `author_id`=%s;"
            cursor.execute(delete_statement, (cid, user_info['id']))
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("id={}用户删除图形失败:{}".format(user_info['id'], e))
            return jsonify({'message': '删除失败!'}), 400
        else:
            db_connection.close()
            if os.path.exists(options_file_path):
                os.remove(options_file_path)
            return jsonify({'message': '删除成功!'})


class TableChartsView(MethodView):

    # 获取根据某个table的画出的所有数据表
    def get(self, tid):
        is_json = request.args.get('is_json', False)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show` " \
                           "FROM `info_trend_echart` WHERE `table_id`=%d ORDER by `create_time` DESC;" % tid
        cursor.execute(select_statement)
        user_charts = cursor.fetchall()
        db_connection.close()
        if is_json:  # 返回json数据
            for chart_item in user_charts:
                chart_item['create_time'] = chart_item['create_time'].strftime("%Y-%m-%d")
                chart_item['update_time'] = chart_item['update_time'].strftime("%Y-%m-%d")
            return jsonify({"message": 'get charts of current table successfully!', "charts": user_charts})
        else:  # 直接渲染数据
            has_chart = 0
            if len(user_charts) > 0:
                has_chart = 1
            return render_template('trend/charts_render.html', user_charts=user_charts, has_chart=has_chart)


class VarietyPageCharts(MethodView):
    # 品种页显示的图形
    def get(self, vid):
        is_json = request.args.get('is_json', False)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show` " \
                           "FROM `info_trend_echart` WHERE `variety_id`=%d AND `is_variety_show`=1 ORDER by `create_time` DESC;" % vid
        cursor.execute(select_statement)
        user_charts = cursor.fetchall()
        db_connection.close()
        if is_json:  # 返回json数据
            for chart_item in user_charts:
                chart_item['create_time'] = chart_item['create_time'].strftime("%Y-%m-%d")
                chart_item['update_time'] = chart_item['update_time'].strftime("%Y-%m-%d")
            return jsonify({"message": 'get charts of current table successfully!', "charts": user_charts})
        else:  # 直接渲染数据
            has_chart = 0
            if len(user_charts) > 0:
                has_chart = 1
            return render_template('trend/charts_render.html', user_charts=user_charts, has_chart=has_chart)


class TrendPageCharts(MethodView):
    # 首页展示图形
    def get(self):
        is_json = request.args.get('is_json', False)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show` " \
                           "FROM `info_trend_echart` WHERE `is_trend_show`=1 ORDER by `create_time` DESC;"
        cursor.execute(select_statement)
        user_charts = cursor.fetchall()
        db_connection.close()
        if is_json:  # 返回json数据
            for chart_item in user_charts:
                chart_item['create_time'] = chart_item['create_time'].strftime("%Y-%m-%d")
                chart_item['update_time'] = chart_item['update_time'].strftime("%Y-%m-%d")
            return jsonify({"message": 'get charts of current table successfully!', "charts": user_charts})
        else:  # 直接渲染数据
            has_chart = 0
            if len(user_charts) > 0:
                has_chart = 1
            return render_template('trend/charts_render.html', user_charts=user_charts, has_chart=has_chart)
