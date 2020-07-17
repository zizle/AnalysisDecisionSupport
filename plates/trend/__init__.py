# _*_ coding:utf-8 _*_
# Author: zizle

from flask import Blueprint
from .views import TrendGroupView, UserTrendTableView, TrendTableView, UserTrendChartView
from .source import UserDataSourceConfigView
from .variety import VarietyTrendTableView
from .chart import TrendTableChartView, TrendChartRetrieveView, TableChartsView, VarietyPageCharts, TrendPageCharts

trend_blp = Blueprint(name='trend', import_name=__name__, url_prefix='/')

trend_blp.add_url_rule('trend/group/', view_func=TrendGroupView.as_view(name='trendgroup'))  # 数据组的设置
trend_blp.add_url_rule('user/data_configs/', view_func=UserDataSourceConfigView.as_view(name='uconfigs'))  # 用户数据源配置
trend_blp.add_url_rule('user/<int:uid>/trend/table/', view_func=UserTrendTableView.as_view(name='utdtable'))  # 用户数据表(所有,上传)
trend_blp.add_url_rule('variety/<int:vid>/trend/table/', view_func=VarietyTrendTableView.as_view(name='vtdtable'))  # 品种的数据表

# trend_blp.add_url_rule('user/1/trend/chart/', view_func=UserTrendChartView.as_view(name='utdchart'))  # 旧版保存图形配置接口(临时接口用于同步旧版数据)
trend_blp.add_url_rule('trend/table-chart/', view_func=TrendTableChartView.as_view(name='tchart'))  # 新版保存图形配置接口（GET-用户保存的所有图形）
trend_blp.add_url_rule('trend/table-chart/<int:cid>/', view_func=TrendChartRetrieveView.as_view(name='tchartretrieve'))  # 获取图形配置options的接口

trend_blp.add_url_rule('trend/table/<int:tid>/', view_func=TrendTableView.as_view(name='trendtable'))  # 获取某个table的源数据
trend_blp.add_url_rule('trend/table/<int:tid>/charts/', view_func=TableChartsView.as_view(name='tablecharts'))  # 获取某个table下的所有图形

trend_blp.add_url_rule('trend/variety-charts/<int:vid>/', view_func=VarietyPageCharts.as_view(name='varietycharts'))  # 在品种页显示的图形接口
trend_blp.add_url_rule('trend/charts/', view_func=TrendPageCharts.as_view('thcview'))  # 基本分析首页展示图形
