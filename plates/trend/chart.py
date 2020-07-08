# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-08
# ------------------------
from flask import request, jsonify
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token

"""关于图形的接口"""


class TrendTableChartView(MethodView):
    def post(self):
        # 保存图形配置信息json文件
        body_json = request.json
        user_info = verify_json_web_token(body_json.get('utoken', None))
        if not user_info:
            return jsonify({"message":"登录过期了,重新登录后再保存..."}), 400
        user_id = user_info['id']

        return jsonify({"message": "保存成功!"}), 201

