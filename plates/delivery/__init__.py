# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------

""" 交割服务模块 """

from flask import Blueprint
from .warehouse import HouseNumberView, WarehouseView, WarehouseVarietyView, WarehouseReceiptsView
from .variety import VarietyWarehouseView, ProvinceWarehouseView, DeliveryVarietyMessage
from .discuss import DiscussionView, LatestDiscussionView
from .receipt import ReceiptsView

delivery_blp = Blueprint(name='delivery', import_name=__name__, url_prefix='/')
delivery_blp.add_url_rule('house_number/', view_func=HouseNumberView.as_view(name='hnum'))  # 仓库基础编号
delivery_blp.add_url_rule('warehouse/', view_func=WarehouseView.as_view(name='warehouse'))
delivery_blp.add_url_rule('warehouse/<reg("[0-9]{4}"):wcode>/variety/', view_func=WarehouseVarietyView.as_view(name='whvariety'))  # 当前仓库的可交割品种信息
delivery_blp.add_url_rule('variety/warehouse/', view_func=VarietyWarehouseView.as_view(name='varietywh'))  # 当前品种的所有仓库
delivery_blp.add_url_rule('province/warehouse/', view_func=ProvinceWarehouseView.as_view(name='provincewh'))  # 当前品种的所有仓库
delivery_blp.add_url_rule('warehouse/<int:hid>/receipts/', view_func=WarehouseReceiptsView.as_view(name='receipts'))  # 当前品种的所有仓单
delivery_blp.add_url_rule('receipts/', view_func=ReceiptsView.as_view(name='receiptsview'))  # 所有仓单数据(给前端爬虫上传的接口(服务器无法访问郑商所))
delivery_blp.add_url_rule('delivery/variety-message/', view_func=DeliveryVarietyMessage.as_view(name='dvmessage'))  # 交割品种信息管理接口
delivery_blp.add_url_rule('discussion/', view_func=DiscussionView.as_view(name='dis'))  # 交流与讨论
delivery_blp.add_url_rule('discussion/latest/', view_func=LatestDiscussionView.as_view(name='latestdis'))  # 最新交流与讨论

