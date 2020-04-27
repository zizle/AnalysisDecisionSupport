# _*_ coding:utf-8 _*_
# Author: zizle
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 品种数据组
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_variety_trendgroup`("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`name` VARCHAR(16) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`sort` INT(11) DEFAULT 0,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `vtgroup`(`variety_id`,`name`)"
                   ");")

    # 品种数据表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_trend_table` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`update_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`sql_index` INT(11) NOT NULL,"
                   "`sql_table` VARCHAR(32) NOT NULL,"
                   "`group_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`updater_id` INT(11) NOT NULL,"
                   "`origin` VARCHAR(512) DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")


    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()