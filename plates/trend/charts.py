# _*_ coding:utf-8 _*_
# __Author__： zizle
import os
import pandas as pd
from flask import request, jsonify, current_app
from flask.views import MethodView
from pyecharts.components import Table
from db import MySQLConnection
from settings import BASE_DIR


class DrawChartView(MethodView):
    def post(self, tid):
        body_json = request.json
        print(body_json)
        title = body_json.get('title')
        x_bottoms = body_json.get('x_bottoms')
        y_left = body_json.get('y_left')
        y_right = body_json.get('y_right')
        select_table_info = "SELECT `sql_table`,`headers` " \
                            "FROM `info_trend_table` " \
                            "WHERE `id`=%d;" % tid
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_table_info)
        ret = cursor.fetchone()
        sql_table = ret['sql_table']
        table_headers = ret['headers']
        if not all([sql_table, table_headers]):
            db_connection.close()
            return jsonify({"message":"表数据不存在"}), 400
        query_statement = "SELECT * FROM %s;" % sql_table
        cursor.execute(query_statement)
        table_data = cursor.fetchall()
        tbdf = pd.DataFrame(table_data)
        print(tbdf)


        return jsonify({'message': '绘图成功', 'file_url': ''})

    def post1(self, tid):
        import pyecharts.options as opts
        from pyecharts.charts import Line, Page
        from pyecharts.components import Table

        week_name_list = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        high_temperature = [11, 11, 15, 13, 12, 13, 10]
        low_temperature = [1, -2, 2, 5, 3, 2, 0]
        file_folder = os.path.join(BASE_DIR, 'fileStorage/charts/cache/')
        file_path = os.path.join(file_folder, 'temperature_change_line_chart.html')
        file_url = 'charts/cache/temperature_change_line_chart.html'

        c = (
            Line(init_opts=opts.InitOpts(width="800px", height="600px"))
                .add_xaxis(xaxis_data=week_name_list)
                .add_yaxis(
                series_name="最高气温",
                y_axis=high_temperature,
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最大值"),
                        opts.MarkPointItem(type_="min", name="最小值"),
                    ]
                ),
                markline_opts=opts.MarkLineOpts(
                    data=[opts.MarkLineItem(type_="average", name="平均值")]
                ),
            )
                .add_yaxis(
                series_name="最低气温",
                y_axis=low_temperature,
                markpoint_opts=opts.MarkPointOpts(
                    data=[opts.MarkPointItem(value=-2, name="周最低", x=1, y=-1.5)]
                ),
                markline_opts=opts.MarkLineOpts(
                    data=[
                        opts.MarkLineItem(type_="average", name="平均值"),
                        opts.MarkLineItem(symbol="none", x="90%", y="max"),
                        opts.MarkLineItem(symbol="circle", type_="max", name="最高点"),
                    ]
                ),
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title="未来一周气温变化", subtitle="纯属虚构"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                toolbox_opts=opts.ToolboxOpts(is_show=True),
                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
            )

        )
        table = Table()

        headers = ["City name", "Area", "Population", "Annual Rainfall"]
        rows = [
            ["Brisbane", 5905, 1857594, 1146.4],
            ["Adelaide", 1295, 1158259, 600.5],
            ["Darwin", 112, 120900, 1714.7],
            ["Hobart", 1357, 205556, 619.5],
            ["Sydney", 2058, 4336374, 1214.8],
            ["Melbourne", 1566, 3806092, 646.9],
            ["Perth", 5386, 1554769, 869.4],
        ]
        table.add(headers, rows).set_global_opts(
            title_opts=opts.ComponentTitleOpts(title="Table")
        )

        page = Page(layout=Page.SimplePageLayout)
        page.add(
            c,
            table,
        )
        page.render(file_path)
        return jsonify({'message': '绘制成功', 'file_url': file_url})

    def a(self):
        import pyecharts.options as opts
        from pyecharts.charts import Line
        x_data = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        y_data = [820, 932, 901, 934, 1290, 1330, 1320]
        (
            Line()
                .set_global_opts(
                tooltip_opts=opts.TooltipOpts(is_show=False),
                xaxis_opts=opts.AxisOpts(type_="category"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    axistick_opts=opts.AxisTickOpts(is_show=True),
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                ),
            )
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                series_name="",
                y_axis=y_data,
                symbol="emptyCircle",
                is_symbol_show=True,
                label_opts=opts.LabelOpts(is_show=False),
            )
                .render("basic_line_chart.html")
        )

