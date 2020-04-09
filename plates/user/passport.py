# _*_ coding:utf-8 _*_
# __Author__： zizle
import re
import jwt
import time
import datetime
from flask import request,jsonify,current_app
from flask.views import MethodView
from utils.client import get_client
from utils.psd_handler import hash_user_password
from db import MySQLConnection, RedisConnection
from settings import JSON_WEB_TOKEN_EXPIRE, SECRET_KEY
from .enums import USER_ROLES


class RegisterView(MethodView):
    def post(self):
        json_body = request.json
        imgcid = json_body.get('image_code_id', '')
        machine_code = json_body.get('machine_code', None)
        client = get_client(machine_code)
        print(machine_code, client)
        if not client:
            return jsonify({'message': 'INVALID CLIENT,无法注册!'})
        role_num = 5
        if client['is_manager'] == 1:
            role_num = 4
        username = json_body.get('username',None)
        password = json_body.get('password',None)
        phone = json_body.get('phone',None)
        email = json_body.get('email', '')
        image_code = json_body.get('imgcode', None)
        if not all([username, password, phone, image_code]):
            return jsonify({'message': '请提交完整数据.'})
        if not re.match(r'^[1][3-9][0-9]{9}$', phone):  # 手机号验证
            return jsonify({"message": "手机号有误!"})
        redis_connection = RedisConnection()
        real_imgcode = redis_connection.get_value('imgcid_%s' % imgcid)  # 取出验证码

        if not real_imgcode or image_code.lower() != real_imgcode.lower():
            return jsonify({"message": "验证码错误!"})
        password = hash_user_password(password)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:

            save_statement = "INSERT INTO `user_info`(`username`,`password`,`phone`,`email`,`role_num`)" \
                             "VALUES (%s,%s,%s,%s,%s);"
            cursor.execute(save_statement,(username,password,phone,email, role_num))
            # 写入第三方表(记录用户可登录的客户端表)
            new_user_id = db_connection.insert_id()
            client_id = int(client['id'])
            expire_time = datetime.datetime.strptime("3000-01-01", "%Y-%m-%d")

            uc_save_statement = "INSERT INTO `user_client`(`user_id`,`client_id`,`expire_time`)" \
                                "VALUES (%s,%s,%s);"
            cursor.execute(uc_save_statement,(new_user_id, client_id, expire_time))
            db_connection.commit()
        except Exception as e:
            current_app.logger.error("用户注册错误:{}".format(e))
            db_connection.rollback()  # 事务回滚
            db_connection.close()
            return jsonify({"message": "注册失败%s" % str(e)}), 400
        else:
            return jsonify({"message": "注册成功"})

    # @staticmethod
    # def generate_json_web_token(uid, username, role, phone, note=''):
    #     issued_at = time.time()
    #     expiration = issued_at + JSON_WEB_TOKEN_EXPIRE  # 有效期
    #     token_dict = {
    #         'iat': issued_at,
    #         'exp': expiration,
    #         'uid': uid,
    #         'username': username,
    #         'role': role,
    #         'phone': phone,
    #         'note':note
    #     }
    #
    #     headers = {
    #         'alg': 'HS256',
    #     }
    #     jwt_token = jwt.encode(
    #         payload=token_dict,
    #         key=SECRET_KEY,
    #         algorithm='HS256',
    #         headers=headers
    #     ).decode('utf-8')
    #     return jwt_token
