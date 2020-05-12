# _*_ coding:utf-8 _*_
# Author: zizle

from flask import Blueprint
from .views import TrendGroupView, UserTrendTableView, TrendTableView, UserTrendChartView, TrendChartOptionsView

trend_blp = Blueprint(name='trend', import_name=__name__, url_prefix='/')

trend_blp.add_url_rule('trend/group/', view_func=TrendGroupView.as_view(name='trendgroup'))
trend_blp.add_url_rule('user/<int:uid>/trend/table/', view_func=UserTrendTableView.as_view(name='utdtable'))

trend_blp.add_url_rule('user/<int:uid>/trend/chart/', view_func=UserTrendChartView.as_view(name='utdchart'))
trend_blp.add_url_rule('trend/table/<int:tid>/', view_func=TrendTableView.as_view(name='trendtable'))

trend_blp.add_url_rule('trend/chart/<int:cid>/', view_func=TrendChartOptionsView.as_view(name='chartoption'))
