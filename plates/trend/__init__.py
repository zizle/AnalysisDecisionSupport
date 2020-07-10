# _*_ coding:utf-8 _*_
# Author: zizle

from flask import Blueprint
from .views import TrendGroupView, UserTrendTableView, TrendTableView, UserTrendChartView, TrendChartOptionsView
from .trend_home import TrendHomeChartsView
from .source import UserDataSourceConfigView
from .variety import VarietyTrendTableView
from .chart import TrendTableChartView, TrendChartRetrieveView

trend_blp = Blueprint(name='trend', import_name=__name__, url_prefix='/')

trend_blp.add_url_rule('trend/group/', view_func=TrendGroupView.as_view(name='trendgroup'))
trend_blp.add_url_rule('user/data_configs/', view_func=UserDataSourceConfigView.as_view(name='uconfigs'))  # 用户数据源配置
trend_blp.add_url_rule('user/<int:uid>/trend/table/', view_func=UserTrendTableView.as_view(name='utdtable'))  # 用户数据表
trend_blp.add_url_rule('variety/<int:vid>/trend/table/', view_func=VarietyTrendTableView.as_view(name='vtdtable'))  # 品种数据表

trend_blp.add_url_rule('user/<int:uid>/trend/chart/', view_func=UserTrendChartView.as_view(name='utdchart'))  # 旧版保存图形配置接口
trend_blp.add_url_rule('trend/table-chart/', view_func=TrendTableChartView.as_view(name='tchart'))  # 新版保存图形配置接口
trend_blp.add_url_rule('trend/table-chart/<int:cid>/', view_func=TrendChartRetrieveView.as_view(name='tchartretrieve'))  # 具体图形配置的接口

trend_blp.add_url_rule('trend/table/<int:tid>/', view_func=TrendTableView.as_view(name='trendtable'))

trend_blp.add_url_rule('trend/charts/', view_func=TrendHomeChartsView.as_view('thcview'))  # 基本分析首页展示图形
# trend_blp.add_url_rule('trend/chart/<int:cid>/', view_func=TrendChartOptionsView.as_view(name='chartoption'))
