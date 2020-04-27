# _*_ coding:utf-8 _*_
# Author: zizle

from flask import Blueprint
from .views import TrendGroupView,TrendTableView

trend_blp = Blueprint(name='trend', import_name=__name__, url_prefix='/')

trend_blp.add_url_rule('trend/group/', view_func=TrendGroupView.as_view(name='trendgroup'))
trend_blp.add_url_rule('trend/table/', view_func=TrendTableView.as_view(name='trendtable'))

