# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
import re
from flask import request, jsonify, render_template
from flask.views import MethodView
from pyecharts.charts import Line
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
                           "FROM `link_warehouse_variety` AS lwhvtb " \
                           "INNER JOIN `info_delivery_warehouse` AS infowhtb " \
                           "ON lwhvtb.warehouse_id=infowhtb.id AND lwhvtb.variety_en=%s;"
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
                          "FROM `info_delivery_warehouse` AS infotb " \
                          "LEFT JOIN `link_warehouse_variety` AS lwhtb " \
                          "ON infotb.id=lwhtb.warehouse_id " \
                          "WHERE infotb.area=%s " \
                          "GROUP BY infotb.id;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(query_statement, province)
        query_result = cursor.fetchall()
        db_connection.close()
        return jsonify({'message': '获取数据成功!', 'warehouses': query_result})
