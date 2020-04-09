# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint
from .views import ClientView


basic_blp = Blueprint(name='client', import_name=__name__, url_prefix='/')
basic_blp.add_url_rule('client/', view_func=ClientView.as_view(name="client"))
