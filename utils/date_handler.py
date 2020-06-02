# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-29
# ------------------------

import datetime


def generate_date_range(start, end):
    """ 时间生成器,含端点"""
    start_date = datetime.datetime.strptime(start, '%Y%m%d') + datetime.timedelta(days=-1)
    end_date = datetime.datetime.strptime(end, '%Y%m%d')
    while start_date < end_date:
        start_date += datetime.timedelta(days=1)
        if start_date.weekday() >= 5:  # 去除周末
            continue
        yield start_date.strftime("%Y%m%d")


def get_date_iteration(start_date=None, end_date=None):
    """获取时间段,可选择传入的时间，
    智能与当前时间为界点，生成开始至当前或当前至结束的时间区间
    """
    if not start_date and not end_date:
        start_date = end_date = datetime.datetime.today().strftime("%Y%m%d")
    if not start_date and end_date:
        start_date = datetime.datetime.today().strftime("%Y%m%d")
    if start_date and not end_date:
        end_date = datetime.datetime.today().strftime("%Y%m%d")
    return generate_date_range(start_date, end_date)
