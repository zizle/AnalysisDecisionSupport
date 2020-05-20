# _*_ coding:utf-8 _*_
# __Author__： zizle
# _*_ coding:utf-8 _*_
# Author: zizle
# Flask要求app得是一个包
import os
from flask import Flask, request
from flask_cors import CORS
from utils.log_handler import config_logger_handler
from plates.basic import basic_blp
from plates.user import user_blp
from plates.homepage import homepage_blp
from plates.pserver import pserver_blp
from plates.trend import trend_blp
from settings import BASE_DIR

static_folder = os.path.join(BASE_DIR, 'fileStorage')
templates_folder = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, static_url_path='/ads', static_folder=static_folder, template_folder=templates_folder)

CORS(app, supports_credemtials=True)  # 支持跨域
app.config['JSON_AS_ASCII'] = False  # json返回数据支持中文

app.logger.addHandler(config_logger_handler())  # 配置日志


app.register_blueprint(basic_blp)
app.register_blueprint(user_blp)
app.register_blueprint(homepage_blp)
app.register_blueprint(pserver_blp)
app.register_blueprint(trend_blp)


# 主页
@app.route('/')
def index():
    return "OK"
    # return redirect("/static/index.html")  # 重定向


# # 拦截所有请求
# @app.before_request
# def before_request():
#     print(request.headers)
#     print('拦截了请求')


# # favicon
# @app.route('/favicon.ico')
# def favicon():
#     return send_from_directory(app.root_path,
#                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

