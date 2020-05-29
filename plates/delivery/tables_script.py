# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-05-26
# ------------------------
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 仓库信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_delivery_warehouse` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "fixed_code VARCHAR(8) NOT NULL DEFAULT '',"
                   "`area` VARCHAR(4) NOT NULL,"
                   "`name` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`short_name` VARCHAR(16) NOT NULL,"
                   "`addr` VARCHAR(1024) NOT NULL DEFAULT '',"
                   "`create_time` DATETIME DEFAULT NOW(),"
                   "`update_time` DATETIME DEFAULT NOW(),"
                   "`longitude` FLOAT(10,4) NOT NULL,"
                   "`latitude` FLOAT(10,4) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 仓库交割的品种表
    cursor.execute("CREATE TABLE IF NOT EXISTS `link_warehouse_variety` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "warehouse_id INT(11) NOT NULL,"
                   "`variety` VARCHAR(8) NOT NULL DEFAULT '',"
                   "`variety_en` VARCHAR(4) NOT NULL DEFAULT '',"
                   "`linkman` VARCHAR(32) DEFAULT '' DEFAULT '',"
                   "`links` VARCHAR(512) NOT NULL DEFAULT '',"
                   "`premium` VARCHAR(64) NOT NULL DEFAULT '',"
                   "`create_time` DATETIME DEFAULT NOW(),"
                   "`update_time` DATETIME DEFAULT NOW(),"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `warevariety`(`warehouse_id`,`variety_en`)"
                   ");")

    # 仓单表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_warehouse_receipt` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`warehouse_code` VARCHAR(8) NOT NULL,"
                   "`variety` VARCHAR(8) NOT NULL DEFAULT '',"
                   "`variety_en` VARCHAR(4) NOT NULL DEFAULT '',"
                   "`date` VARCHAR(8) NOT NULL,"
                   "`receipt` INT(11) DEFAULT 0,"
                   "`increase` INT(11) DEFAULT 0,"
                   "`create_time` DATETIME DEFAULT NOW()"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()

