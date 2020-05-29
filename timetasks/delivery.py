# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-29
# ------------------------
import sys
from logging import Logger
from pymysql import connect, FIELD_TYPE, converters
from pymysql.cursors import DictCursor
from db import MySQLConnection
from utils.date_handler import get_date_iteration
from utils.log_handler import config_logger_handler
from libs.warehouse_lib import warehouses_code

"""从数据库中将交割仓库的仓单数据读取到本项目数据库中"""

logger = Logger(name='warehouse')
logger.addHandler(config_logger_handler())


TARGET_DATABASE = 'exld_develop'
NAME = 'root'
PASSWORD = 'mysql'
PORT = 3306

converions = converters.conversions
#全局配置了
converions[FIELD_TYPE.BIT] = lambda x: 1 if int.from_bytes(x, byteorder=sys.byteorder, signed=False) else 0 # 转换BIT类型为0或1


class TargetSQLConnection(object):
    def __init__(self):
        self._db = connect(
            host='localhost',
            user=NAME,
            password=PASSWORD,
            database=TARGET_DATABASE,
            port=PORT,
            charset='utf8',
            conv=converions,
        )
        self.cursor = self._db.cursor(DictCursor)  # 传入字典形式的cursor返回的是字典

    # 获取游标
    def get_cursor(self):
        return self.cursor

    # 关闭游标,断开连接
    def close(self):
        self.cursor.close()
        self._db.close()

    # 开启事务
    def begin(self):
        self._db.begin()

    # 事务回滚
    def rollback(self):
        self._db.rollback()

    # 提交事务
    def commit(self):
        self._db.commit()

    # 插入返回id
    def insert_id(self):
        return self._db.insert_id()


def migrate_warehouse_receipts():
    # 迁移仓单数据库数据
    query_statement = "SELECT * " \
                     "FROM `czce_warehouse` " \
                     "WHERE `date`=%s;"
    target_connection = TargetSQLConnection()
    cursor = target_connection.get_cursor()

    save_connection = MySQLConnection()
    save_cursor = save_connection.get_cursor()

    date_iterator = get_date_iteration('20200101', '20200430')

    for date in date_iterator:
        cursor.execute(query_statement, date)
        result = cursor.fetchall()
        save_list = list()
        error = ''
        for receipt_item in result:
            item_values = list()
            fixed_code = warehouses_code.get(receipt_item['warehouse'], None)
            if not fixed_code:
                new_error_text = "{} 的 {} 仓库没编码...".format(date, receipt_item['warehouse'])
                if new_error_text != error:
                    logger.error(new_error_text)
                    error = new_error_text
                continue
            item_values.append(fixed_code)
            item_values.append(receipt_item['variety'])
            item_values.append(receipt_item['variety_en'])
            item_values.append(receipt_item['date'])
            item_values.append(receipt_item['receipt'])
            item_values.append(receipt_item['increase'])
            save_list.append(item_values)
        save_date_receipts(save_cursor, save_list)
        save_connection.commit()

    target_connection.close()
    save_connection.close()


def save_date_receipts(cursor, save_list):
    # 保存一天的仓单
    save_statement = "INSERT INTO `info_warehouse_receipt` " \
                     "(`warehouse_code`,`variety`,`variety_en`,`date`,`receipt`,`increase`) " \
                     "VALUES (%s,%s,%s,%s,%s,%s);"
    cursor.executemany(save_statement, save_list)


if __name__ == '__main__':
    migrate_warehouse_receipts()
