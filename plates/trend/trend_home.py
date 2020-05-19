# _*_ coding:utf-8 _*_
# Author: zizle
# Created: 2020-05-12
# ---------------------------

""" 基本分析首页 """

from flask import request, jsonify, render_template
from flask.views import MethodView
from db import MySQLConnection


class TrendHomeChartsView(MethodView):
    def get(self):
        """ 获取所有首页要显示的数据图信息 """
        variety_id = request.args.get('variety')
        try:
            variety_id = int(variety_id)
        except Exception:
            return jsonify({"message":'参数错误'}), 400

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        is_render = request.args.get('is_render', False)
        if variety_id == 0:
            query_statement = "SELECT * FROM `info_trend_chart` " \
                              "WHERE `is_trend_show`=1;"
            cursor.execute(query_statement)
        else:
            query_statement = "SELECT * FROM `info_trend_chart` " \
                              "WHERE `is_variety_show`=1 AND `variety_id`=%s;"
            cursor.execute(query_statement, variety_id)
        query_all = cursor.fetchall()
        records = list()
        for item in query_all:
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d')
            item['update_time'] = item['update_time'].strftime('%Y-%m-%d')
            records.append(item)
        if is_render:
            return render_template('trend/charts_render.html', user_charts=records)
        else:
            return jsonify({'message': '查询成功', 'charts_info': records})