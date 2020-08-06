# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
import re
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection


class VarietyWarehouseView(MethodView):
    def get(self):
        variety_en = request.args.get('v_en', '')
        try:
            variety_en = variety_en.upper()
            if not re.match(r'[A-Z]+', variety_en):
                raise ValueError('Error')
        except Exception:
            return jsonify({'message': '参数错误', 'warehouses': []}), 400
        # 查询品种下的仓库信息
        select_statement = "SELECT infowhtb.id,infowhtb.area,infowhtb.name,infowhtb.addr,infowhtb.longitude,infowhtb.latitude," \
                           "lwhvtb.variety,lwhvtb.variety_en,lwhvtb.linkman,lwhvtb.links,lwhvtb.premium " \
                           "FROM `info_warehouse_variety` AS lwhvtb " \
                           "INNER JOIN `info_warehouse` AS infowhtb " \
                           "ON lwhvtb.warehouse_code=infowhtb.fixed_code AND lwhvtb.variety_en=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement, variety_en)
        query_result = cursor.fetchall()
        db_connection.close()
        return jsonify({'message': '获取数据成功!', 'warehouses': query_result})


class ProvinceWarehouseView(MethodView):
    def get(self):
        # 获取指定地区下的仓库
        province = request.args.get('province', '')
        query_statement = "SELECT infotb.id,infotb.area,infotb.name,infotb.addr,infotb.longitude,infotb.latitude," \
                          "lwhtb.linkman,lwhtb.links,lwhtb.premium, " \
                          "GROUP_CONCAT(lwhtb.variety) AS delivery_varieties " \
                          "FROM `info_warehouse` AS infotb " \
                          "LEFT JOIN `info_warehouse_variety` AS lwhtb " \
                          "ON infotb.fixed_code=lwhtb.warehouse_code " \
                          "WHERE infotb.area=%s " \
                          "GROUP BY infotb.id;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, province)
        query_result = cursor.fetchall()
        db_connection.close()
        return jsonify({'message': '获取数据成功!', 'warehouses': query_result})


class DeliveryVarietyMessage(MethodView):
    def get(self):
        """ 返回所有品种的交割信息 """
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        query_sql = "SELECT id,variety,variety_en,last_trade,receipt_expire,delivery_unit,limit_holding " \
                    "FROM info_variety_delivery;"
        cursor.execute(query_sql)
        all_items = cursor.fetchall()
        db_connection.close()
        return jsonify({"message": "查询成功!", "variety_data": all_items})

    def post(self):
        # 批量新增品种信息
        body_json = request.json
        # print(body_json)
        # # utoken = body_json.get('utoken')
        # # user_info = verify_json_web_token(utoken)
        # # print(user_info)
        # # if not user_info or user_info['role_num'] > 2:
        # #     return
        # variety_msg = body_json.get('variety_record')
        # save_list = list()
        # for item in variety_msg:
        #     item_list = list()
        #     item_list.append(item['variety'])
        #     item_list.append(item['variety_en'])
        #     item_list.append(item['last_trade'])
        #     item_list.append(item['receipt_expire'])
        #     item_list.append(item['delivery_unit'])
        #     item_list.append(item['limit_holding'])
        #     save_list.append(item_list)
        # db_connection = MySQLConnection()
        # cursor = db_connection.get_cursor()
        # insert_statement = "INSERT INTO `info_variety_delivery` " \
        #                    "(`variety`,`variety_en`,`last_trade`,`receipt_expire`,`delivery_unit`,`limit_holding`) " \
        #                    "VALUES (%s,%s,%s,%s,%s,%s);"
        # cursor.executemany(insert_statement, save_list)
        # db_connection.commit()
        # db_connection.close()
        return jsonify({'message': '保存成功!'})

    def put(self):
        """ 修改品种的信息 """
        body_json = request.json
        vid = body_json.get("vid", None)
        last_trade = body_json.get("last_trade", None)
        receipt_expire = body_json.get("receipt_expire", None)
        delivery_unit = body_json.get("delivery_unit", None)
        limit_holding = body_json.get("limit_holding", None)
        update_sql = "UPDATE `info_variety_delivery` " \
                     "SET `last_trade`=%s,`receipt_expire`=%s,`delivery_unit`=%s,`limit_holding`=%s " \
                     "WHERE `id`=%s;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(update_sql, (last_trade, receipt_expire, delivery_unit, limit_holding, vid))
        db_connection.commit()
        db_connection.close()
        return jsonify({"message": "修改成功!"})
