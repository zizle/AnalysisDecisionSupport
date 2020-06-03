# _*_ coding:utf-8 _*_
# Author: zizle
import os
import logging

SECRET_KEY = "cj3gnb1k2xzfq*odw5y-vts^+cv+p8suw+(_5#va%f70=tvt5mp"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASES = {
    'mysql': {
        'HOST': 'localhost',
        'PORT': 3306,
        'USER': 'decisionmaker',
        'PASSWORD': 'ruidaads0603',
        'NAME': 'analysisdsupport'
    },
    'mysql_deve': {
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

CLIENT_UPDATE_PATH = 'F:/DecisionClients/'
