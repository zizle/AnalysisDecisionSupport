# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------

""" 交割服务模块 """

from flask import Blueprint
from .warehouse import WarehouseView, WarehouseVarietyView, WarehouseReceiptsView
from .variety import VarietyWarehouseView, ProvinceWarehouseView

delivery_blp = Blueprint(name='delivery', import_name=__name__, url_prefix='/')
delivery_blp.add_url_rule('warehouse/', view_func=WarehouseView.as_view(name='warehouse'))
delivery_blp.add_url_rule('warehouse/<int:hid>/variety/', view_func=WarehouseVarietyView.as_view(name='whvariety'))  # 当前仓库的可交割品种信息
delivery_blp.add_url_rule('variety/warehouse/', view_func=VarietyWarehouseView.as_view(name='varietywh'))  # 当前品种的所有仓库
delivery_blp.add_url_rule('province/warehouse/', view_func=ProvinceWarehouseView.as_view(name='provincewh'))  # 当前品种的所有仓库
delivery_blp.add_url_rule('warehouse/<int:hid>/receipts/', view_func=WarehouseReceiptsView.as_view(name='receipts'))  # 当前品种的所有仓库

