# _*_ coding:utf-8 _*_
# Author: zizle
import os
from flask import request,send_from_directory,jsonify
from flask.views import MethodView
from settings import BASE_DIR

class ModelFilesView(MethodView):
    def get(self):
        file_name=request.args.get('filename', None)
        print(file_name)
        if not file_name:
            return jsonify({'message':"参数错误"}), 400
        file_folder = os.path.join(BASE_DIR, 'fileStorage/models/')
        return send_from_directory(directory=file_folder, filename=file_name)