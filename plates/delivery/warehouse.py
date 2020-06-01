# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
from flask import request, jsonify
from flask.views import MethodView
from db import MySQLConnection
from utils.char_reverse import strQ2B


"""仓库编号信息管理"""


class HouseNumberView(MethodView):
    def get(self):
        # 获取所有
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute("SELECT `id`,`name`,`fixed_code` FROM `info_warehouse_fixed_code` ORDER BY `id`;")
        return jsonify({'message': '查询成功!', 'warehouses': cursor.fetchall()})

    def post(self):

        # 批量
        # body_json = request.json
        # houses = body_json.get('houses', None)
        # db_connection = MySQLConnection()
        # cursor = db_connection.get_cursor()
        #
        # insert_statement = "INSERT INTO `info_warehouse_fixed_code`(" \
        #                    "`name`,`fixed_code`) " \
        #                    "VALUES (%s,%s);"
        # cursor.executemany(insert_statement, houses)
        # db_connection.commit()
        # db_connection.close()

        # 增加一个
        body_json = request.json
        name = body_json.get('name', None)
        # 将简称字符转为半角
        name = strQ2B(name)
        if not name:
            return jsonify({'message': '简称不能为空!'}), 400
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        exist_query = "SELECT `name` FROM `info_warehouse_fixed_code` WHERE `name`=%s;"
        cursor.execute(exist_query, name)
        exist_ = cursor.fetchone()
        if exist_:
            db_connection.close()
            return jsonify({'message': '该仓库已存在..'}), 400
        else:
            # 生成fixed_code
            maxid_select = "SELECT MAX(`id`) AS `maxid` FROM `info_warehouse_fixed_code`;"
            cursor.execute(maxid_select)
            max_id = cursor.fetchone()['maxid']
            fixed_code = '%04d' % (max_id + 1)
            insert_statement = "INSERT INTO `info_warehouse_fixed_code` (`name`,`fixed_code`) " \
                               "VALUES (%s, %s);"
            cursor.execute(insert_statement, (name, fixed_code))
            db_connection.commit()
            db_connection.close()

        return jsonify({'message': '保存成功!', 'fixed_code': fixed_code}), 201


"""仓库信息管理"""


class WarehouseView(MethodView):
    # 获取所有的仓库
    def get(self):
        select_statement = "SELECT * FROM `info_warehouse` ORDER BY `id`;"
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        cursor.execute(select_statement)
        records = list()
        for item in cursor.fetchall():
            item['create_time'] = item['create_time'].strftime('%Y-%m-%d')
            records.append(item)

        return jsonify({'message':'查询成功!', 'warehouses': records})

    def post(self):
        # 批量增加仓库
        # body_json = request.json
        # warehouses = body_json.get('warehouses', None)
        # db_connection = MySQLConnection()
        # cursor = db_connection.get_cursor()
        # # 查询所有的简称对应的仓库编号
        # cursor.execute("SELECT `name`,`fixed_code` FROM `info_warehouse_fixed_code`;")
        # all_fixed_codes = cursor.fetchall()
        # all_fixed_codes_dict = dict()
        #
        # for item in all_fixed_codes:
        #     if item['name'] not in all_fixed_codes_dict.keys():
        #         all_fixed_codes_dict[item['name']] = item['fixed_code']
        #     else:
        #         print('该仓库简称已存在')
        # for new_warehouse in warehouses:
        #     new_fixed_code = all_fixed_codes_dict.get(new_warehouse['short_name'], None)
        #     if not new_fixed_code:
        #         print("发现新仓库:{}!".format(new_warehouse['short_name']))
        #         db_connection.close()
        #         return jsonify({'message':'有新仓库{}'.format(new_warehouse['short_name'])}), 400
        #     else:
        #         new_warehouse['fixed_code'] = new_fixed_code
        # save_list = list()
        # for house_item in warehouses:
        #     item_list = list()
        #     item_list.append(house_item['fixed_code'])
        #     item_list.append(house_item['area'])
        #     item_list.append(house_item['name'])
        #     item_list.append(house_item['short_name'])
        #     item_list.append(house_item['addr'])
        #     item_list.append(house_item['arrived'])
        #     item_list.append(house_item['longitude'])
        #     item_list.append(house_item['latitude'])
        #     save_list.append(item_list)
        #
        # print(save_list)
        # insert_statement = "INSERT INTO `info_warehouse` " \
        #                    "(`fixed_code`,`area`,`name`,`short_name`,`addr`,`arrived`,`longitude`,`latitude`) " \
        #                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
        # cursor.executemany(insert_statement, save_list)
        # db_connection.commit()
        # db_connection.close()

        # 新增单个仓库
        body_json = request.json
        fixed_code = body_json.get('fixed_code', None)
        area = body_json.get('area', None)
        name = body_json.get('name', None)
        short_name = body_json.get('short_name', None)
        addr = body_json.get('addr', None)
        arrived = body_json.get('arrived', '')
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
                           "(`fixed_code`,`area`,`name`, `short_name`,`addr`,`arrived`,`longitude`,`latitude`) " \
                           "VALUES (%s,%s,%s,%s,%s,%s,%s);"
        cursor.execute(insert_statement, (fixed_code, area, name, short_name, addr, arrived, longitude, latitude))

        db_connection.commit()
        db_connection.close()
        return jsonify({'message': '新增成功!'}), 201


class WarehouseVarietyView(MethodView):
    def get(self, wcode):
        print(wcode)
        # 获取当前仓库的信息和涉及的交割品种
        db_connection = MySQLConnection()
        cursor = db_connection.get_cursor()
        house_select = "SELECT `id`, `fixed_code`,`name`, `short_name` FROM `info_warehouse` WHERE `fixed_code`=%s;" % wcode
        cursor.execute(house_select)
        house = cursor.fetchone()
        if not house:
            db_connection.close()
            return jsonify({'message':'该仓库不存在!'}), 400
        # 连接查询
        select_statement = "SELECT * " \
                           "FROM `info_variety` AS varietytb " \
                           "LEFT JOIN `info_warehouse_variety` AS whvarity " \
                           "ON varietytb.name_en=whvarity.variety_en AND whvarity.warehouse_code=%s " \
                           "ORDER BY varietytb.id;"
        cursor.execute(select_statement,wcode)
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

    def post(self, wcode):
        # 批量增加仓库的可交割品种
        # body_json = request.json
        # variety_message = body_json.get('variety_record', '')
        # # 查询所有的简称对应的仓库编号
        # db_connection = MySQLConnection()
        # cursor = db_connection.get_cursor()
        # cursor.execute("SELECT `name`,`fixed_code` FROM `info_warehouse_fixed_code`;")
        # all_fixed_codes = cursor.fetchall()
        # all_fixed_codes_dict = dict()
        #
        # for item in all_fixed_codes:
        #     if item['name'] not in all_fixed_codes_dict.keys():
        #         all_fixed_codes_dict[item['name']] = item['fixed_code']
        #     else:
        #         print('该仓库简称已存在')
        # # 通过简称找到仓库
        # for variety_item in variety_message:
        #     house_fixed_code = all_fixed_codes_dict.get(variety_item['short_name'],None)
        #     if not house_fixed_code:
        #         print('发现新仓库:{}'.format(variety_item['short_name']))
        #     else:
        #         variety_item['warehouse_code'] = house_fixed_code
        #
        # # 整理数据
        # save_list = list()
        # for new_item in variety_message:
        #     new_list = list()
        #     new_list.append(new_item['warehouse_code'])
        #     new_list.append(new_item['name'])
        #     new_list.append(new_item['name_en'])
        #     new_list.append(new_item['linkman'])
        #     new_list.append(new_item['links'])
        #     new_list.append(new_item['premium'])
        #     save_list.append(new_list)
        #
        # print(save_list)
        # save_statement = "INSERT INTO `info_warehouse_variety` " \
        #                  "(`warehouse_code`,`variety`,`variety_en`,`linkman`,`links`,`premium`) " \
        #                  "VALUES (%s,%s,%s,%s,%s,%s);"
        #
        # cursor.executemany(save_statement, save_list)
        # db_connection.commit()
        # db_connection.close()

        # 新增或修改仓库的可交割品种
        body_json = request.json
        variety_en = body_json.get('variety_en', None)
        variety_text = body_json.get('variety_text', None)
        if not all([wcode, variety_en, variety_text]):
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
            insert_statement = "INSERT INTO `info_warehouse_variety` " \
                               "(`warehouse_code`,`variety`,`variety_en`,`linkman`,`links`,`premium`) " \
                               "VALUES (%s,%s,%s,%s,%s,%s);"
            cursor.execute(insert_statement, (wcode, variety_text, variety_en, linkman, links, premium))
        else:
            # 去除可交割品种
            delete_statement = "DELETE FROM `info_warehouse_variety` " \
                              "WHERE `warehouse_code`=%s AND `variety_en`=%s;"
            cursor.execute(delete_statement, (wcode, variety_en))
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
                              "FROM `info_warehouse_variety` AS lwvtb " \
                              "INNER JOIN `info_warehouse` AS infowhtb " \
                              "ON lwvtb.warehouse_code=infowhtb.fixed_code " \
                              "WHERE infowhtb.id=%s AND lwvtb.variety_en=%s;"
            cursor.execute(query_statement,(hid, variety_en))
        else:
            query_statement = "SELECT infowhtb.id,infowhtb.fixed_code,infowhtb.name,infowhtb.short_name," \
                              "lwvtb.variety,lwvtb.variety_en,lwvtb.linkman,lwvtb.links,lwvtb.premium " \
                              "FROM `info_warehouse_variety` AS lwvtb " \
                              "INNER JOIN `info_warehouse` AS infowhtb " \
                              "ON lwvtb.warehouse_code=infowhtb.fixed_code " \
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

