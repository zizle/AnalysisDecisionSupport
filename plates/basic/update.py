# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-21
# ------------------------
import os
import hashlib
from configparser import ConfigParser
from flask import request, send_file, jsonify, current_app
from flask.views import MethodView
from settings import CLIENT_UPDATE_PATH


class UpdatingClientView(MethodView):
    update_list = dict()

    def get(self):
        identify = request.args.get('identify', 0)
        client_v = request.args.get('version')
        user_agent = request.headers['User-Agent']
        system_bit = int(request.args.get('sbit', '32'))  # 默认32位的系统
        # print(user_agent, identify, client_v)
        if identify == '1' and user_agent == 'RuiDa_ADSClient':
            # print('更新管理端')
            # 判断客户端的系统位数
            if system_bit == 64:
                conf_path = os.path.join(CLIENT_UPDATE_PATH, 'INSIDE/X64/cinfo.ini')
                ready_path = os.path.join(CLIENT_UPDATE_PATH, 'INSIDE/X64/')
            else:
                conf_path = os.path.join(CLIENT_UPDATE_PATH, 'INSIDE/X32/cinfo.ini')
                ready_path = os.path.join(CLIENT_UPDATE_PATH, 'INSIDE/X32/')
        else:
            # print('更新用户端')
            if system_bit == 64:
                conf_path = os.path.join(CLIENT_UPDATE_PATH, 'OUTSIDE/X64/cinfo.ini')
                ready_path = os.path.join(CLIENT_UPDATE_PATH, 'OUTSIDE/X64/')
            else:
                conf_path = os.path.join(CLIENT_UPDATE_PATH, 'OUTSIDE/X32/cinfo.ini')
                ready_path = os.path.join(CLIENT_UPDATE_PATH, 'OUTSIDE/X32/')
        # 获取服务端版本
        current_app.logger.error("获取更新文件夹:{}".format(ready_path))
        conf = ConfigParser()
        conf.read(conf_path)
        server_version = str(conf.get('VERSION', 'VERSION'))
        # print(server_version)
        data = {
            'version': client_v,
            'update': False,
            'file_list': {}
        }
        if client_v != server_version:
            data['version'] = server_version
            data['update'] = True
            self.find_files(ready_path, ready_path)
            data['file_list'] = self.update_list
        return jsonify({'message': '检测成功!', 'data': data})

    # 计算文件MD5
    def getfile_md5(self, filename):
        if not os.path.isfile(filename):
            return
        myHash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8192)
            if not b:
                break
            myHash.update(b)
        f.close()
        return myHash.hexdigest()

    # 查找文件清单
    def find_files(self, path, replace_str):
        fsinfo = os.listdir(path)
        for fn in fsinfo:
            temp_path = os.path.join(path, fn)
            if not os.path.isdir(temp_path):
                # print('文件路径: {}'.format(temp_path))
                file_md5 = self.getfile_md5(temp_path)
                # print(fn)
                fn = temp_path.replace(replace_str, '')
                fn = '/'.join(fn.split('\\'))
                self.update_list[fn] = file_md5
            else:
                self.find_files(temp_path, replace_str)


class DownloadingClientView(MethodView):
    def get(self):
        user_agent = request.headers['User-Agent']
        identify = request.json.get('identify', 0)
        file_path = request.json.get('filename', '')
        system_bit = int(request.json.get('sbit', '32'))  # 默认32位的系统
        current_app.logger.error(file_path)
        if identify == '1' and user_agent == 'RuiDa_ADSClient':
            if system_bit == 64:
                file_path = os.path.join(CLIENT_UPDATE_PATH + 'INSIDE/X64/', file_path)
            else:
                file_path = os.path.join(CLIENT_UPDATE_PATH + 'INSIDE/X32/', file_path)
        else:
            if system_bit == 64:
                file_path = os.path.join(CLIENT_UPDATE_PATH + 'OUTSIDE/X64/', file_path)
            else:
                file_path = os.path.join(CLIENT_UPDATE_PATH + 'OUTSIDE/X32/', file_path)
        if not os.path.exists(file_path):
            # print('文件不存在。。。。。', file_path)
            current_app.logger.error('客户端更新文件不存在:{}'.format(file_path))
            return jsonify({'message': '文件不存在'}), 400
        else:
            return send_file(file_path)


# 更新交割独立客户端
class UpdatingDeliveryView(MethodView):
    update_list = dict()

    def get(self):
        client_v = request.args.get('version')
        conf_path = os.path.join(CLIENT_UPDATE_PATH, 'DELIVERY/cinfo.ini')
        ready_path = os.path.join(CLIENT_UPDATE_PATH, 'DELIVERY/')

        # 获取服务端版本
        conf = ConfigParser()
        conf.read(conf_path)
        server_version = str(conf.get('VERSION', 'VERSION'))
        # print(server_version)
        data = {
            'version': client_v,
            'update': False,
            'file_list': {}
        }
        if client_v != server_version:
            data['version'] = server_version
            data['update'] = True
            self.find_files(ready_path, ready_path)
            data['file_list'] = self.update_list
        return jsonify({'message': '检测成功!', 'data': data})

    # 计算文件MD5
    def getfile_md5(self, filename):
        if not os.path.isfile(filename):
            return
        myHash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8192)
            if not b:
                break
            myHash.update(b)
        f.close()
        return myHash.hexdigest()

    # 查找文件清单
    def find_files(self, path, replace_str):
        fsinfo = os.listdir(path)
        for fn in fsinfo:
            temp_path = os.path.join(path, fn)
            if not os.path.isdir(temp_path):
                # print('文件路径: {}'.format(temp_path))
                file_md5 = self.getfile_md5(temp_path)
                # print(fn)
                fn = temp_path.replace(replace_str, '')
                fn = '/'.join(fn.split('\\'))
                self.update_list[fn] = file_md5
            else:
                self.find_files(temp_path, replace_str)


# 下载交割客户端
class DownloadingDeliveryView(MethodView):
    def get(self):
        file_path = request.json.get('filename', '')
        # print(file_path)
        file_path = os.path.join(CLIENT_UPDATE_PATH + 'DELIVERY/', file_path)
        if not os.path.exists(file_path):
            # print('文件不存在。。。。。', file_path)
            current_app.logger('客户端更新文件不存在:{}'.format(file_path))
            return jsonify({'message': '文件不存在'}), 400
        else:
            return send_file(file_path)
