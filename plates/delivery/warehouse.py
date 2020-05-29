# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection


"""仓库信息管理"""


class WarehouseView(MethodView):
    # 获取所有的仓库
    def get(self):
        select_statement = "SELECT * FROM `info_delivery_warehouse`;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement)
        records = list()
        for item in cursor.fetchall():
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d')
            records.append(item)

        return jsonify({'message':'查询成功!', 'warehouses': records})

    def post(self):
        body_json = request.json
        fixed_code = body_json.get('fixed_code', None)
        area = body_json.get('area', None)
        name = body_json.get('name', None)
        short_name = body_json.get('short_name', None)
        addr = body_json.get('addr', None)
        longitude = body_json.get('longitude', None)
        latitude = body_json.get('latitude', None)
        if not all([fixed_code, area, name, short_name, addr, longitude, latitude]):
            return jsonify({'message': '参数错误!'}), 400

        try:
            if len(fixed_code) != 4:
                raise ValueError('编号格式有误')
            int(fixed_code)
            longitude = float(longitude)
            latitude = float(latitude)
        except Exception:
            return jsonify({'message': '参数错误!'}), 400
        # 保存数据到数据库
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        # 查询编码是否存在
        fixed_code_statement = "SELECT `fixed_code` FROM `info_delivery_warehouse` where `fixed_code`=%s;"
        cursor.execute(fixed_code_statement, fixed_code)
        fixed_code_exist = cursor.fetchone()
        if fixed_code_exist:
            db_connection.close()
            return jsonify({'message': '仓库已存在!'}), 400

        insert_statement = "INSERT INTO `info_delivery_warehouse` " \
                           "(`fixed_code`,`area`,`name`, `short_name`,`addr`,`longitude`,`latitude`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s);"
        cursor.execute(insert_statement, (fixed_code, area, name, short_name, addr, longitude, latitude))

        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '新增成功!'}), 201


class WarehouseVarietyView(MethodView):
    def get(self, hid):
        # 获取当前仓库的信息和涉及的交割品种
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        house_select = "SELECT `id`, `fixed_code`,`name`, `short_name` FROM `info_delivery_warehouse` WHERE `id`=%d;" % hid
        cursor.execute(house_select)
        house = cursor.fetchone()
        if not house:
            db_connection.close()
            return jsonify({'message':'该仓库不存在!'}), 400
        # 连接查询
        select_statement = "SELECT * " \
                           "FROM `info_variety` AS varietytb " \
                           "LEFT JOIN `link_warehouse_variety` AS whvarity " \
                           "ON varietytb.name_en=whvarity.variety_en AND whvarity.warehouse_id=%d;" %hid

        cursor.execute(select_statement)
        result = cursor.fetchall()
        response_result = list()
        for item in result:
            if item['parent_id'] is None:
                continue
            new_item = dict()
            new_item['id'] = item['id']
            new_item['name'] = item['name']
            new_item['name_en'] = item['name_en']
            new_item['is_delivery'] = 0
            if item['whvarity.id'] is not None:
                new_item['is_delivery'] = 1
            response_result.append(new_item)
        return jsonify({
            'message': '查询成功',
            'fixed_code':house['fixed_code'],
            'name': house['name'],
            'short_name': house['short_name'],
            'result': response_result
        })

    def post(self, hid):
        # 新增或修改仓库的可交割品种
        body_json = request.json
        house_id = body_json.get('house_id', None)
        variety_en = body_json.get('variety_en', None)
        variety_text = body_json.get('variety_text', None)
        if not all([house_id, variety_en, variety_text]):
            return jsonify({'message':'参数错误'}), 400

        is_delivery = body_json.get('is_delivery', 0)
        delivery_msg = body_json.get('delivery_msg', None)
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        if is_delivery:
            linkman = delivery_msg.get('linkman','')
            links = delivery_msg.get('links', '')
            premium = delivery_msg.get('premium', '')
            # 新增
            insert_statement = "INSERT INTO `link_warehouse_variety` " \
                               "(`warehouse_id`,`variety`,`variety_en`,`linkman`,`links`,`premium`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s);"
            cursor.execute(insert_statement, (house_id, variety_text, variety_en, linkman, links, premium))
        else:
            # 去除可交割品种
            delete_statement = "DELETE FROM `link_warehouse_variety` " \
                              "WHERE `warehouse_id`=%s AND `variety_en`=%s;"
            cursor.execute(delete_statement, (house_id, variety_en))
        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '操作成功!'})


class WarehouseReceiptsView(MethodView):
    def get(self, hid):
        variety_en = request.args.get('v_en', None)
        if variety_en:
            try:
                variety_en = variety_en.upper()
            except Exception:
                return jsonify({'message':'参数错误!', 'warehouses_receipts':{}})
        print('品种:', variety_en)
        # 获取指定仓库下的仓单详情和交割的品种
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()

        if variety_en:
            query_statement = "SELECT infowhtb.id,infowhtb.fixed_code,infowhtb.name,infowhtb.short_name," \
                              "lwvtb.variety,lwvtb.variety_en,lwvtb.linkman,lwvtb.links,lwvtb.premium " \
                              "FROM `link_warehouse_variety` AS lwvtb " \
                              "INNER JOIN `info_delivery_warehouse` AS infowhtb " \
                              "ON lwvtb.warehouse_id=infowhtb.id " \
                              "WHERE infowhtb.id=%s AND lwvtb.variety_en=%s;"
            cursor.execute(query_statement,(hid, variety_en))
        else:
            query_statement = "SELECT infowhtb.id,infowhtb.fixed_code,infowhtb.name,infowhtb.short_name," \
                              "lwvtb.variety,lwvtb.variety_en,lwvtb.linkman,lwvtb.links,lwvtb.premium " \
                              "FROM `link_warehouse_variety` AS lwvtb " \
                              "INNER JOIN `info_delivery_warehouse` AS infowhtb " \
                              "ON lwvtb.warehouse_id=infowhtb.id " \
                              "WHERE infowhtb.id=%s;"
            cursor.execute(query_statement, hid)

        query_result = cursor.fetchall()
        if len(query_result) <= 0:
            db_connection.close()
            return jsonify({'message':'获取仓单成功','warehouses_receipts': {}})
        # 整理出品种列表以及品种的仓单
        response_data = dict()
        variety_receipts = list()
        # 查询仓单sql
        receipt_statement = "SELECT * " \
                            "FROM `info_warehouse_receipt` " \
                            "WHERE `variety_en`=%s AND `warehouse_code`=%s " \
                            "ORDER BY `id` DESC " \
                            "LIMIT 10;"
        variety_first = query_result[0]
        response_data['warehouse'] = variety_first['name']
        response_data['varieties'] = variety_receipts
        for variety_item in query_result:
            variety_dict = dict()
            variety_dict['name'] = variety_item['variety']
            variety_dict['name_en'] = variety_item['variety_en']
            variety_dict['linkman'] = variety_item['linkman']
            variety_dict['links'] = variety_item['links']
            variety_dict['premium'] = variety_item['premium']
            cursor.execute(receipt_statement, (variety_item['variety_en'], variety_item['fixed_code']))
            variety_dict['receipts'] = cursor.fetchall()
            variety_receipts.append(variety_dict)
        # print(response_data)
        db_connection.close()
        return jsonify({'message':'获取仓单成功','warehouses_receipts': response_data})

