# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint
from .verify_code import ImageCodeView
from .passport import RegisterView, LoginView
from .views import UsersView, RetrieveUserView
from .variety import UserVarietyView

user_blp = Blueprint(name='user', import_name=__name__, url_prefix='/')
user_blp.add_url_rule('image_code/', view_func=ImageCodeView.as_view(name="imgcode"))
user_blp.add_url_rule('register/', view_func=RegisterView.as_view(name="register"))
user_blp.add_url_rule('login/', view_func=LoginView.as_view(name="login"))
user_blp.add_url_rule('users/', view_func=UsersView.as_view(name='users'))
user_blp.add_url_rule('user/<int:uid>/', view_func=RetrieveUserView.as_view(name="rtvuser"))
user_blp.add_url_rule('user/<int:uid>/variety/', view_func=UserVarietyView.as_view(name='uservariety'))