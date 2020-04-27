# _*_ coding:utf-8 _*_
# Author: zizle
import os
from flask import request, jsonify, current_app
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from plates.user import enums
from settings import BASE_DIR


class VarietyIntroductionView(MethodView):
    def post(self):
        body_form = request.form
        utoken = body_form.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.OPERATOR:
            return jsonify({"message": "登录已过期或不能进行操作。"}), 400
        variety_file = request.files.get('variety_file')
        if not variety_file:
            return jsonify({"message": "参数错误!"}), 400
        try:
            file_folder = os.path.join(BASE_DIR, "fileStorage/pserver/varietyintro/")
            if not os.path.exists(file_folder):
                os.makedirs(file_folder)
            file_path = os.path.join(file_folder, '品种介绍.pdf')
            variety_file.save(file_path)
        except Exception as e:
            current_app.logger.error("上传-修改人才培养内容错误:{}".format(e))
            return jsonify({'message': "上传错误:{}".format(e)}), 400
        else:
            return jsonify({"message": "上传成功!"}), 201