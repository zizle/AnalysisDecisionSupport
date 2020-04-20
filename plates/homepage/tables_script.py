# _*_ coding:utf-8 _*_
# __Author__： zizle
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 新闻公告信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_bulletin` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"  
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 广告信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_advertisement` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`image_url` VARCHAR(256) DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 报告信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_report` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`custom_time` DATETIME NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`category` INT(11) DEFAULT 0,"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 报告与品种的关联表
    cursor.execute("CREATE TABLE IF NOT EXISTS `link_report_variety` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`report_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "UNIQUE KEY `reportvariety`(`variety_id`,`report_id`)"
                   ");")

    # 交易通知信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_exnotice` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`file_url` VARCHAR(256) DEFAULT '',"
                   "`category` INT(11) DEFAULT 0,"
                   "`author_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 现货报表信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_spot` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`custom_time` DATETIME NOT NULL,"
                   "`name` VARCHAR(64) NOT NULL,"
                   "`area` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`level` VARCHAR(16) NOT NULL DEFAULT '',"
                   "`price` DECIMAL (11, 4) NOT NULL DEFAULT 0,"
                   "`increase` DECIMAL (11, 4) NOT NULL DEFAULT 0,"
                   "`note` VARCHAR (256) DEFAULT '',"
                   "`author_id` INT(11) NOT NULL ,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 财经日历信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_finance` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL,"
                   "`date` DATE NOT NULL,"
                   "`time` TIME NOT NULL DEFAULT '00:00:00',"
                   "`country` VARCHAR(128) NOT NULL,"
                   "`event` VARCHAR (1024) NOT NULL DEFAULT '',"
                   "`expected` VARCHAR(32) NOT NULL DEFAULT '',"
                   "`author_id` INT(11) NOT NULL ,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()
