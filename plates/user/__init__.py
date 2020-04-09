# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint
from .verify_code import ImageCodeView
from .passport import RegisterView

user_blp = Blueprint(name='user', import_name=__name__, url_prefix='/')

user_blp.add_url_rule('image_code/', view_func=ImageCodeView.as_view(name="imgcode"))
user_blp.add_url_rule('register/', view_func=RegisterView.as_view(name="register"))