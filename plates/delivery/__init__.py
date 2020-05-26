# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------

""" 交割服务模块 """

from flask import Blueprint
from .warehouse import WarehouseView, WarehouseVarietyView

delivery_blp = Blueprint(name='delivery', import_name=__name__, url_prefix='/')
delivery_blp.add_url_rule('warehouse/', view_func=WarehouseView.as_view(name='warehouse'))
delivery_blp.add_url_rule('warehouse/<int:hid>/variety/', view_func=WarehouseVarietyView.as_view(name='whvariety'))
