# _*_ coding:utf-8 _*_
# Author: zizle

""" 数据库交互 """

import sys
import redis
import pickle
from pymysql import connect, converters, FIELD_TYPE
from pymysql.cursors import DictCursor
import settings

converions = converters.conversions
#全局配置了
converions[FIELD_TYPE.BIT] = lambda x: 1 if int.from_bytes(x, byteorder=sys.byteorder, signed=False) else 0 # 转换BIT类型为0或1


class MySQLConnection(object):
    def __init__(self):
        db_params = settings.DATABASES.get('mysql')
        self._db = connect(
            host=db_params['HOST'],
            user=db_params['USER'],
            password=db_params['PASSWORD'],
            database=db_params['NAME'],
            port=db_params['PORT'],
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


class RedisConnection(object):
    def __init__(self):
        redis_params = settings.DATABASES.get('redis')
        self._connection = redis.StrictRedis(
            host=redis_params['HOST'],
            port=redis_params['PORT'],
            db=redis_params['DBINDEX'],
            password=redis_params['PASSWORD']
        )

    def set_value(self, key, value, ex=None):
        self._connection.set(key, pickle.dumps(value), ex)
        self._connection.close()

    def get_value(self, key):
        value = self._connection.get(key)
        if value is not None:
            value = pickle.loads(value)
        self._connection.close()
        return value
