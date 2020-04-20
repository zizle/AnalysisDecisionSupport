# _*_ coding:utf-8 _*_
# Author: zizle
import os
import logging

SECRET_KEY = "cj3gmb1k2xzfq*odq5y-vts^+cv+p7suw+(_5#va%f70=tt5mp"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASES = {
    'mysql2': {
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'ads_worker',
        'PASSWORD': 'rdyjxxxxads',
        'NAME': 'analysis_decision'
    },
    'mysql': {
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': 'mysql',
        'NAME': 'analysis_decision'
    },
    'sqlite': {
        'NAME': 'test.db'
    },
    'redis': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DBINDEX': 0,
        'PASSWORD': ''
    }
}
# DEBUG,INFO,WARNING,ERROR,CRITICAL

LOGGER_LEVEL = logging.DEBUG
# jwt的有效时间
JSON_WEB_TOKEN_EXPIRE = 1728000
