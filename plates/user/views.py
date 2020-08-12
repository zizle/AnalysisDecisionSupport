# _*_ coding:utf-8 _*_
# Author: zizle
import os
from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection
from utils.psd_handler import verify_json_web_token, hash_user_password
from utils.file_handler import hash_filename
from plates.user import enums
from settings import BASE_DIR


class UsersView(MethodView):
    def get(self):
        utoken = request.args.get('utoken')
        role_num = request.args.get('role_num', 0)
        try:
            role_num = int(role_num)
        except Exception as e:
            return jsonify({"message": "参数错误"}), 400
        user_info = verify_json_web_token(utoken)
        if not user_info or user_info['role_num'] > enums.OPERATOR:
            return jsonify({"message": "不能访问或登录已过期。"}), 400
        if role_num == 0:
            query_statement = "SELECT `id`,`username`,`avatar`,`phone`,`email`,`role_num`,`note`,`is_active`, " \
                              "DATE_FORMAT(`join_time`,'%Y-%m-%d') AS `join_time`, " \
                              "DATE_FORMAT(`update_time`,'%Y-%m-%d') AS `update_time` " \
                              "FROM `info_user` WHERE `id`>1;"
        else:
            query_statement = "SELECT `id`,`username`,`avatar`,`phone`,`email`,`role_num`,`note`,`is_active`," \
                              "DATE_FORMAT(`join_time`,'%%Y-%%m-%%d') AS `join_time`," \
                              "DATE_FORMAT(`update_time`,'%%Y-%%m-%%d') AS `update_time` " \
                              "FROM `info_user` WHERE `role_num`=%d;" % role_num
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement)
        response_users = list()
        for user_item in cursor.fetchall():
            user_item['role_text'] = enums.user_roles.get(user_item['role_num'], '未知')
            response_users.append(user_item)
        return jsonify({"message": "获取信息成功!", "users": response_users})


class RetrieveUserView(MethodView):
    def post(self, uid):
        # 管理员重置用户密码
        body_json = request.json
        utoken = body_json.get('utoken',None)
        operate_user = verify_json_web_token(utoken)  # 操作者
        if not operate_user or operate_user['role_num'] > 2:
            return jsonify({'message': '没有权限进行这个操作!'}), 400
        # 重置密码
        new_password = hash_user_password('123456')
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        new_statement = "UPDATE `info_user` SET `password`=%s WHERE `id`=%s;"

        cursor.execute(new_statement, (new_password, uid))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message':'重置成功!'})

    def patch(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)

        if not user_info or user_info['role_num'] > enums.OPERATOR:
            return jsonify({"message": "不能这样操作或登录过期"}), 400

        is_active = 1 if body_json.get('is_active', False) else 0
        is_sync_tables = 1 if body_json.get('sync_tables', False) else 0

        to_role_num = body_json.get('role_num', enums.NORMAL)
        note = body_json.get('note', '')

        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`role_num` FROM `info_user` WHERE `id`=%d;" %uid
        cursor.execute(select_statement)
        user_role = cursor.fetchone()
        if not user_role:
            db_connection.close()
            return jsonify({"message": '修改的用户不存在。'}), 400
        if to_role_num < enums.OPERATOR:
            db_connection.close()
            return jsonify({'message': '不能修改为这个角色!'}), 400
        if user_role['role_num'] < enums.OPERATOR:
            db_connection.close()
            return jsonify({"message": "不能对当前人员进行这项设置!"}), 400
        if user_info['role_num'] > enums.SUPERUSER and to_role_num < enums.COLLECTOR:
            db_connection.close()
            return jsonify({'message': '您不能设置运营管理员角色!'}), 400

        update_statement = "UPDATE `info_user` SET `role_num`=%s,`note`=%s, `is_active`=%s WHERE `id`=%s;"
        db_connection.begin()
        try:
            cursor.execute(update_statement, (to_role_num, note, is_active, uid))
            # 如果同步数据表，修改数据表的状态
            if is_sync_tables:
                cursor.execute(
                    "UPDATE `info_trend_table` SET `is_active`=%s WHERE `author_id`=%s;",
                    (is_active, uid)
                )
            db_connection.commit()
        except Exception as e:
            current_app.logger.error("修改人员状态和同步数据表状态错误:{}".format(e))
            db_connection.rollback()
            db_connection.close()
            return jsonify({"message": "修改失败!"})
        else:
            db_connection.close()
            return jsonify({"message": "修改成功!", "role_text": enums.user_roles.get(to_role_num, ""), 'note':note})


class UserInfoView(MethodView):
    def get(self, uid):
        utoken = request.args.get('utoken')
        user_info = verify_json_web_token(utoken)
        user_id = user_info['id']
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        select_statement = "SELECT `id`,`phone`,`username`,`email`, `avatar` FROM `info_user` WHERE `id`=%s;"
        cursor.execute(select_statement, user_id)
        user_data = cursor.fetchone()
        db_connection.close()

        return jsonify({"message": "获取信息成功", "data": user_data})

    def patch(self, uid):
        body_json = request.json
        utoken = body_json.get('utoken')
        user_info = verify_json_web_token(utoken)
        if not user_info:
            return jsonify({'message':'登录已过期，重新登录再进行修改'}), 400
        user_id = int(user_info['id'])
        modify_dict = dict()
        for can_modify_key in ['username', 'password', 'phone', 'email']:
            if can_modify_key in body_json:
                if can_modify_key == 'password':
                    modify_dict['password'] = hash_user_password(body_json['password'])
                else:
                    modify_dict[can_modify_key] = body_json[can_modify_key]
        update_str = ""
        for modify_key in modify_dict:
            update_str += "`{}`='{}',".format(modify_key, modify_dict[modify_key])
        update_str = update_str[:-1]
        update_statement = "UPDATE `info_user` SET %s WHERE `id`=%d;" % (update_str, user_id)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(update_statement)
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "修改成功!"})


class UserAvatarView(MethodView):
    def post(self, uid):  # 修改头像
        avatar_file = request.files.get('image', None)
        if not avatar_file:
            return jsonify({'message':'修改成功!'})
        avatar_folder = os.path.join(BASE_DIR, "fileStorage/avatars/{}/".format(uid))
        if not os.path.exists(avatar_folder):
            os.makedirs(avatar_folder)
        avatar_file_name = avatar_file.filename
        avatar_hash_name = hash_filename(avatar_file_name)
        file_path = os.path.join(avatar_folder, avatar_hash_name)
        file_save_url = "avatars/{}/{}".format(uid, avatar_hash_name)
        avatar_file.save(file_path)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 找出旧头像文件删除
        select_old_avatar = "SELECT `avatar` FROM `info_user` WHERE `id`=%s;"
        cursor.execute(select_old_avatar, uid)
        fetch_avatar = cursor.fetchone()
        if fetch_avatar:
            old_url = fetch_avatar['avatar']
            old_path = os.path.join(BASE_DIR, 'fileStorage/{}'.format(old_url))
            if os.path.exists(old_path):
                os.remove(old_path)
        save_statement = "UPDATE `info_user` SET `avatar`=%s WHERE `id`=%s;"
        cursor.execute(save_statement, (file_save_url, uid))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message':'修改成功!', 'avatar_url': file_save_url})


