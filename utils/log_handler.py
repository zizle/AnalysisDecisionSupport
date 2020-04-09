# _*_ coding:utf-8 _*_
# Author: zizle
import os
import time
import logging
from settings import BASE_DIR, LOGGER_LEVEL

def make_dir(dir_path):
    path = dir_path.strip()
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def config_logger_handler():
    # 日志配置
    log_folder = os.path.join(BASE_DIR, "logs/")
    make_dir(log_folder)
    log_file_name = time.strftime('%Y-%m-%d', time.localtime(time.time())) + '.log'
    log_file_path = log_folder + os.sep + log_file_name

    handler = logging.FileHandler(log_file_path, encoding='UTF-8')
    handler.setLevel(LOGGER_LEVEL)
    logger_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s[line:%(lineno)d]"
    )
    handler.setFormatter(logger_format)
    return handler
