# _*_ coding:utf-8 _*_
# __Author__： zizle
from db import MySQLConnection


def get_client(machine_code):
    if not machine_code:
        return None
    db_connection = MySQLConnection()
    select_statement = "SELECT `id`,`name`,`machine_code`,`join_time`,`update_time`, `is_manager` " \
                       "FROM `info_client` WHERE `machine_code`=%s AND `is_active`=1;"
    cursor = db_connection.get_cursor()
    cursor.execute(select_statement, machine_code)
    client = cursor.fetchone()
    db_connection.close()
    return client
