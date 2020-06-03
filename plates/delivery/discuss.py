# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-02
# ------------------------
from flask import request, jsonify
from flask.views import MethodView
from utils.psd_handler import verify_json_web_token
from db import MySQLConnection


def get_sub_reply(cursor, parent_id):
    query_statement = "SELECT infodis.id,infodis.content,infodis.create_time," \
                      "usertb.username,usertb.phone,usertb.avatar " \
                      "FROM `info_discussion` AS infodis " \
                      "INNER JOIN `info_user` AS usertb " \
                      "ON infodis.author_id=usertb.id " \
                      "WHERE infodis.parent_id=%s " \
                      "ORDER BY infodis.create_time DESC;"
    cursor.execute(query_statement, parent_id)
    sub_reply = cursor.fetchall()
    replies = list()
    for reply_item in sub_reply:
        reply_dict = dict()
        reply_dict['id'] = reply_item['id']
        if reply_item['username']:
            username = reply_item['username']
        else:
            phone = reply_item['phone']
            username = phone[:4] + '****' + phone[8:]
        reply_dict['username'] = username
        reply_dict['avatar'] = reply_item['avatar']
        reply_dict['text'] = reply_item['content']
        reply_dict['create_time'] = reply_item['create_time'].strftime('%Y-%m-%d')
        replies.append(reply_dict)
    return replies


class DiscussionView(MethodView):
    def get(self):
        c_page = request.args.get('page', 1)
        c_page_size = request.args.get('page_size', 20)
        try:
            c_page = int(c_page) - 1  # 减1处理才能查到第一页
        except Exception:
            c_page = 0
        # 查询当前页码下的数据
        limit_start = c_page * c_page_size
        query_statement = "SELECT infodis.id,infodis.content,infodis.create_time," \
                          "usertb.username,usertb.phone,usertb.avatar " \
                          "FROM `info_discussion` AS infodis " \
                          "INNER JOIN `info_user` AS usertb " \
                          "ON infodis.author_id=usertb.id " \
                          "WHERE infodis.parent_id is NULL " \
                          "ORDER BY infodis.create_time DESC " \
                          "LIMIT %s,%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement,(limit_start, c_page_size))
        records_result = cursor.fetchall()
        # 查询总条数
        count_statement = "SELECT COUNT(infodis.id) AS total " \
                          "FROM `info_discussion` AS infodis " \
                          "INNER JOIN `info_user` AS usertb " \
                          "ON infodis.author_id=usertb.id " \
                          "WHERE infodis.parent_id is NULL;" \

        cursor.execute(count_statement)
        # 计算总页数
        total_count = cursor.fetchone()['total']
        total_page = int((total_count + c_page_size - 1) / c_page_size)
        response_data = list()
        for dis_item in records_result:
            dis_dict = dict()
            dis_dict['id'] = dis_item['id']
            if dis_item['username']:
                username = dis_item['username']
            else:
                phone = dis_item['phone']
                username = phone[:4] + '****' + phone[8:]
            dis_dict['username'] = username
            dis_dict['avatar'] = dis_item['avatar']
            dis_dict['create_time'] = dis_item['create_time'].strftime('%Y-%m-%d')
            dis_dict['text'] = dis_item['content']
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
        db_connection.close()
        return jsonify({'message': '查询成功!', 'discussions': response_data, 'total_page': total_page})

    def post(self):
        body_json = request.json
        utoken = body_json.get('utoken', None)
        user_info = verify_json_web_token(utoken)
        content = body_json.get('content', '')
        parent_id = body_json.get('parent_id', None)
        if not all([user_info, content]):
            return jsonify({'message': '登录已过期或未填写内容'}), 400
        # print(user_info)
        # print(content, parent_id)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        insert_statement = "INSERT INTO `info_discussion` " \
                           "(`author_id`,`content`,`parent_id`) " \
                           "VALUES (%s,%s,%s);"
        cursor.execute(insert_statement, (user_info['id'], content, parent_id))
        replies = []
        if parent_id:
            replies = get_sub_reply(cursor, parent_id)
        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '提交成功', 'replies': replies}), 201


class LatestDiscussionView(MethodView):
    def get(self):
        query_statement = "SELECT infodis.id,infodis.content,infodis.create_time," \
                          "usertb.username,usertb.phone,usertb.avatar " \
                          "FROM `info_discussion` AS infodis " \
                          "INNER JOIN `info_user` AS usertb " \
                          "ON infodis.author_id=usertb.id " \
                          "WHERE infodis.parent_id is NULL " \
                          "ORDER BY infodis.create_time DESC " \
                          "LIMIT 8;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement)
        query_all = cursor.fetchall()
        response_data = list()
        for dis_item in query_all:
            dis_dict = dict()
            dis_dict['id'] = dis_item['id']
            if dis_item['username']:
                username = dis_item['username']
            else:
                phone = dis_item['phone']
                username = phone[:4] + '****' + phone[8:]
            dis_dict['username'] = username
            dis_dict['avatar'] = dis_item['avatar']
            dis_dict['create_time'] = dis_item['create_time'].strftime('%Y-%m-%d')
            dis_dict['text'] = dis_item['content']
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
        db_connection.close()
        return jsonify({'message': '查询成功!', 'discussions': response_data})
