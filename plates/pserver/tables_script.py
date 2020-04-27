# _*_ coding:utf-8 _*_
# Author: zizle
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 短讯通记录表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_shortmessage`("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`custom_time` DATETIME NOT NULL,"
                   "`content` VARCHAR(2048) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 市场分析
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_marketanalysis` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")
    # 专题研究
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_topicsearch` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")
    # 调研报告
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_searchreport` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 交易策略
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_tradepolicy`("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`custom_time` DATETIME NOT NULL,"
                   "`content` VARCHAR(2048) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 投资方案
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_investmentplan` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 套保方案
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_hedgeplan` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()