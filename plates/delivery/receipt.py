# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-06-10
# ------------------------
from flask import request, jsonify, current_app
from flask.views import MethodView
from db import MySQLConnection


class ReceiptsView(MethodView):
    def post(self):
        body_json = request.json
        receipts = body_json.get('receipts', [])
        # 将数据保存到数据库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        try:
            save_statement = "INSERT INTO `info_warehouse_receipt` " \
                             "(`warehouse_code`,`warehouse_name`,`variety`,`variety_en`,`date`,`receipt`,`increase`) " \
                             "VALUES (%s,%s,%s,%s,%s,%s,%s);"
            cursor.executemany(save_statement, receipts)
            db_connection.commit()
        except Exception as e:
            db_connection.close()
            current_app.logger.error("保存数据到生产库发生了错误!{}".format(e))
            return jsonify({'message': '上传仓单失败!'}), 400
        else:
            db_connection.close()
            return jsonify({'message': '上传仓单成功!'}), 201
