# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-08
# ------------------------
import os
import json
import math
import pandas as pd
from datetime import datetime
from flask import request, jsonify, render_template, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token
from utils.file_handler import hash_filename
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
            select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show` " \
                               "FROM `info_trend_echart` WHERE `author_id`=%s;"
            cursor.execute(select_statement, (user_id, ))
        else:
            select_statement = "SELECT `id`,`create_time`,`update_time`,`title`,`decipherment`,`is_trend_show`,`is_variety_show` " \
                               "FROM `info_trend_echart` " \
                               "WHERE `author_id`=%s AND `variety_id`=%s;"
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
            print(chart_options, title, variety_id)
            return jsonify({"message": "参数错误..."}), 400
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
        insert_statement = "INSERT `info_trend_echart` " \
                           "(`author_id`,`title`,`table_id`,`variety_id`,`options_file`,`decipherment`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s);"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 保存表信息
        cursor.execute(insert_statement, (user_id, title, table_id,variety_id, config_sql_path,decipherment))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "保存成功!"}), 201


class TrendChartRetrieveView(MethodView):
    # 获取某个图形的配置进行展示图形
    def get(self, cid):
        chart_id = cid
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
            if x_axis_start:  # 切片取数
                start_year = datetime.strptime(x_axis_start, '%Y').strftime(date_format)
                source_df = source_df[start_year <= source_df['column_0']]
            if x_axis_end:  # 切片取数
                end_year = datetime.strptime(x_axis_end, '%Y').strftime(date_format)
                source_df = source_df[source_df['column_0'] <= end_year]
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
        # 1 x轴数据
        option_of_xaxis = {
            "type": "category",
            "data": source_df[x_axis["col_index"]].values.tolist(),
            'axisLabel': {
                'rotate': -26,
                'fontSize': 11
            },
        }
        # 2 Y轴数据
        y_axis = list()
        series = list()
        legend_data = list()
        if len(options_content['y_left']) > 0:
            y_axis.append({'type': 'value', 'name': options_content['axis_tags']['left']})
        if len(options_content['y_right']) > 0:
            y_axis.append({'type': 'value', 'name':options_content['axis_tags']['right']})
        for y_left_opts_item in options_content['y_left']:  # 左轴数据
            left_series = dict()
            if y_left_opts_item['no_zero']:  # 本数据去0
                cache_df = source_df[source_df[y_left_opts_item['col_index']] != '0']
            else:
                cache_df = source_df
            left_series['type'] = y_left_opts_item['chart_type']
            left_series['name'] = table_headers_dict[y_left_opts_item['col_index']]
            left_series['yAxisIndex'] = 0
            a = cache_df[x_axis['col_index']].values.tolist()  # 横轴数据
            b = cache_df[y_left_opts_item['col_index']].values.tolist()  # 数值
            left_series['data'] = [*zip(a, b)]
            series.append(left_series)
            legend_data.append(table_headers_dict[y_left_opts_item['col_index']])
        for y_right_opts_item in options_content['y_right']:  # 右轴数据
            right_series = dict()
            if y_right_opts_item['no_zero']:  # 本数据去0
                cache_df = source_df[source_df[y_right_opts_item['col_index']] != '0']
            else:
                cache_df = source_df
            right_series['type'] = y_right_opts_item['chart_type']
            right_series['name'] = table_headers_dict[y_right_opts_item['col_index']]
            right_series['yAxisIndex'] = 1
            a = cache_df[x_axis['col_index']].values.tolist()  # 横轴数据
            b = cache_df[y_right_opts_item['col_index']].values.tolist()  # 数值
            right_series['data'] = [*zip(a, b)]
            series.append(right_series)
            legend_data.append(table_headers_dict[y_right_opts_item['col_index']])
        title_size = options_content['title']['textStyle']['fontSize']
        options = {
            "title": options_content["title"],
            'legend': {'data': legend_data, 'bottom': 0},
            'tooltip': {'axisPointer': {'type': 'cross'}},
            'grid': {
                'top': title_size + 15,
                'left': 15,
                'right': 15,
                'bottom': 20 * (len(legend_data) / 3 + 1) + 16,
                'show': False,
                'containLabel': True,
            },
            'xAxis': option_of_xaxis,
            'yAxis': y_axis,
            'series': series,
        }
        if options_content['watermark']:
            options['graphic'] = {
                'type': 'group',
                'rotation': math.pi / 4,
                'bounding': 'raw',
                'right': 110,
                'bottom': 110,
                'z': 100,
                'children': [
                    {
                        'type': 'rect',
                        'left': 'center',
                        'top': 'center',
                        'z': 100,
                        'shape': {
                            'width': 400,
                            'height': 50
                        },
                        'style': {
                            'fill': 'rgba(0,0,0,0.3)'
                        }
                    },
                    {
                        'type': 'text',
                        'left': 'center',
                        'top': 'center',
                        'z': 100,
                        'style': {
                            'fill': '#fff',
                            'text': options_content["watermark_text"],
                            'font': 'bold 26px Microsoft YaHei'
                        }
                    }
                ]
            }

        return options

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
