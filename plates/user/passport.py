# _*_ coding:utf-8 _*_
# __Author__： zizle
import re
import jwt
import time
import datetime
from flask import request,jsonify,current_app
from flask.views import MethodView
from utils.client import get_client
from utils.psd_handler import hash_user_password, verify_json_web_token, check_user_password
from db import MySQLConnection, RedisConnection
from settings import JSON_WEB_TOKEN_EXPIRE, SECRET_KEY


class RegisterView(MethodView):
    def post(self):
        json_body = request.json
        imgcid = json_body.get('image_code_id', '')
        machine_code = json_body.get('machine_code', None)
        client = get_client(machine_code)
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

            save_statement = "INSERT INTO `info_user`(`username`,`password`,`phone`,`email`,`role_num`)" \
                             "VALUES (%s,%s,%s,%s,%s);"
            cursor.execute(save_statement,(username,password,phone,email, role_num))
            # 写入第三方表(记录用户可登录的客户端表)
            new_user_id = db_connection.insert_id()
            client_id = int(client['id'])
            expire_time = datetime.datetime.strptime("3000-01-01", "%Y-%m-%d")

            uc_save_statement = "INSERT INTO `link_user_client`(`user_id`,`client_id`,`expire_time`)" \
                                "VALUES (%s,%s,%s);"
            cursor.execute(uc_save_statement,(new_user_id, client_id, expire_time))
            db_connection.commit()
        except Exception as e:
            current_app.logger.error("用户注册错误:{}".format(e))
            db_connection.rollback()  # 事务回滚
            db_connection.close()
            return jsonify({"message": "注册失败%s" % str(e)}), 400
        else:
            return jsonify({"message": "注册成功"}), 201


class LoginView(MethodView):
    def get(self):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            message = '登录已过期'
        else:
            user_info['utoken'] = utoken
            message = "登录成功!"
        return jsonify({"message": message,"user_data": user_info})

    def post(self):
        body_json = request.json
        machine_code = body_json.get("machine_code", None)
        client = get_client(machine_code)
        if not client:
            return jsonify({"message":"参数错误,登录失败。"}), 400
        username = body_json.get("username", '')
        phone = body_json.get("phone", '')
        password = body_json.get("password", '')
        # 查询数据库
        select_statement = "SElECT `id`,`username`,`phone`,`avatar`,`email`,`role_num`,`note`,`password` " \
                           "FROM `info_user` " \
                           "WHERE (`username`=%s OR `phone`=%s) AND `is_active`=1;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement,(username, phone))
        user_info = cursor.fetchone()
        if not user_info:
            db_connection.close()
            return jsonify({"message": "用户名或密码错误!"}), 400
        if not check_user_password(password, user_info['password']):
            return jsonify({"message": "用户名或密码错误!"}), 400
        now = datetime.datetime.now()
        if user_info['role_num'] > 2:
            # 查询是否能在此客户端登录
            can_login_statement = "SELECT `user_id`,`client_id` " \
                                  "FROM `link_user_client` " \
                                  "WHERE `user_id`=%s AND `client_id`=%s AND `expire_time`>%s;"
            cursor.execute(can_login_statement, (user_info['id'], client['id'], now))
            can_login = cursor.fetchone()
            if not can_login:
                db_connection.close()
                return jsonify({"message": "无法在此客户端登录,联系管理员开通."}), 400
        update_statement = "UPDATE `info_user` SET `update_time`=%s WHERE `id`=%s;"
        cursor.execute(update_statement, (now, user_info['id']))  # 更新登录时间
        db_connection.commit()
        db_connection.close()
        # 生成token
        utoken = self.generate_json_web_token(
            uid=user_info['id'],
            username=user_info['username'],
            avatar=user_info['avatar'],
            role_num=user_info['role_num'],
            phone=user_info['phone']
        )
        user_data = {
            "id": user_info['id'],
            "role_num": user_info['role_num'],
            "username": user_info['username'],
            "phone": phone[0:3] + '****' + phone[7:11],
            "avatar": user_info['avatar'],
            "utoken": utoken
        }
        return jsonify({"message":"登录成功!","user_data": user_data})

    @staticmethod
    def generate_json_web_token(uid, username,avatar, role_num, phone, note=''):
        issued_at = time.time()
        expiration = issued_at + JSON_WEB_TOKEN_EXPIRE  # 有效期
        token_dict = {
            'iat': issued_at,
            'exp': expiration,
            'id': uid,
            'username': username,
            'avatar':avatar,
            'role_num': role_num,
            'phone': phone,
            'note':note
        }

        headers = {
            'alg': 'HS256',
        }
        jwt_token = jwt.encode(
            payload=token_dict,
            key=SECRET_KEY,
            algorithm='HS256',
            headers=headers
        ).decode('utf-8')
        return jwt_token


class UserAuthClientsView(MethodView):
    # 获取所有指定类型客户端信息和用户是否可登录
    def get(self, uid):
        t_client = request.args.get('t', 0)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询用户的角色
        role_statement = "SELECT `role_num` FROM `info_user` WHERE `id`=%s;"
        cursor.execute(role_statement, uid)
        user_role_num = cursor.fetchone()['role_num']
        select_statement = "SELECT client.id, client.name, client.machine_code, client.is_manager, linkuser.user_id, linkuser.client_id, linkuser.expire_time " \
                           "FROM `info_client` AS client LEFT JOIN `link_user_client` AS linkuser " \
                           "ON client.id=linkuser.client_id AND linkuser.user_id=%s AND linkuser.expire_time>NOW() " \
                           "WHERE client.is_manager=%s;"

        cursor.execute(select_statement, (uid, t_client))
        client_information = cursor.fetchall()
        result = list()
        for item in client_information:
            new_item = dict()
            new_item['id'] = item['id']
            new_item['name'] = item['name']
            new_item['machine_code'] = item['machine_code']
            new_item['is_manager'] = '管理端' if item['is_manager'] else '普通端'
            if user_role_num <= 2:
                new_item['accessed'] = 1
                new_item['expire_time'] = '3000-01-01'
            else:
                new_item['accessed'] = 1 if item['user_id'] else 0
                new_item['expire_time'] = item['expire_time'].strftime('%Y-%m-%d') if item['expire_time'] else ''
            result.append(new_item)
        db_connection.close()
        return jsonify({'message': '查询成功!', 'information': result})

    # 修改可在某客户端的登录状态
    def post(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        operate_info = verify_json_web_token(utoken)
        if not operate_info or operate_info['role_num'] > 2:
            return jsonify({'message': '登录过期或不能进行这个操作.'}), 400
        user_id = body_json.get('user_id', None)
        client_id = body_json.get('client_id', None)
        is_accessed = body_json.get('accessed', 0)
        if not all([user_id, client_id]):
            return jsonify({'message': '参数错误!'}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询用户的角色
        role_statement = "SELECT `role_num` FROM `info_user` WHERE `id`=%s;"
        cursor.execute(role_statement, user_id)
        user_role = cursor.fetchone()['role_num']
        if user_role <= 2:  # 运营以上的人员
            db_connection.close()
            return jsonify({'message': '不能对运营管理员这样修改.'}), 400
        exist_statement = "SELECT `id`, `client_id`, `user_id` " \
                          "FROM `link_user_client` " \
                          "WHERE `client_id`=%s AND `user_id`=%s;"
        cursor.execute(exist_statement, (client_id, user_id))
        if is_accessed:
            expire_time = datetime.datetime.strptime('3000-01-01', '%Y-%m-%d')
        else:
            expire_time = datetime.datetime.today()
        if not cursor.fetchone():
            insert_statement = "INSERT INTO `link_user_client` " \
                               "(`client_id`, `user_id`, `expire_time`) " \
                               "VALUES (%s, %s, %s);"
            cursor.execute(insert_statement, (client_id, user_id, expire_time))
        else:
            update_statement = "UPDATE `link_user_client` " \
                               "SET `expire_time`=%s " \
                               "WHERE `client_id`=%s AND `user_id`=%s;"
            cursor.execute(update_statement, (expire_time, client_id, user_id))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '修改成功', 'expire_time': expire_time.strftime('%Y-%m-%d')})
