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

    # 更新的数据源配置信息表(哪个用户哪台电脑哪个品种哪个组别的数据配置记录表)
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_tablesource_configs`("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`update_time` DATETIME DEFAULT NOW(),"
                   "`variety_name` VARCHAR(32) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`group_name` VARCHAR(64) NOT NULL,"
                   "`group_id` INT(11) NOT NULL,"
                   "`client_id` INT(11) NOT NULL,"
                   "`user_id` INT(11) NOT NULL,"
                   "`file_folder` VARCHAR (1024) NOT NULL"
                   ");")

    # 品种数据表信息
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_trend_table` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`update_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL,"
                   "`title_md5` VARCHAR(32) NOT NULL,"
                   "`suffix_index` INT(11) NOT NULL,"
                   "`sql_table` VARCHAR(32) NOT NULL UNIQUE,"
                   "`group_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`updater_id` INT(11) NOT NULL,"
                   "`origin` VARCHAR(256) DEFAULT '',"
                   "`min_date` VARCHAR(10) DEFAULT '',"
                   "`max_date` VARCHAR(10) DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 配置好的数据图表信息
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_trend_chart` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`update_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`title` VARCHAR(128) NOT NULL,"
                   "`table_id` INT(11) NOT NULL,"
                   "`sql_table` VARCHAR(32) NOT NULL,"
                   "`is_watermark` BIT NOT NULL DEFAULT 0,"
                   "`watermark` VARCHAR(64) DEFAULT '',"
                   "`bottom_axis` VARCHAR(64) NOT NULL,"
                   "`left_axis` VARCHAR(512) NOT NULL,"
                   "`right_axis` VARCHAR(512) NOT NULL,"
                   "`group_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`author_id` INT(11) NOT NULL,"
                   "`updater_id` INT(11) NOT NULL,"
                   "`decipherment` TEXT,"
                   "`is_trend_show` BIT NOT NULL DEFAULT 0,"
                   "`is_variety_show` BIT NOT NULL DEFAULT 0,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 数据图表信息
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_trend_echart` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`create_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`update_time` DATETIME NOT NULL DEFAULT NOW(),"
                   "`author_id` INT(11) NOT NULL,"
                   "`title` VARCHAR(128) NOT NULL,"
                   "`table_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`options_file` VARCHAR(256) DEFAULT NULL,"
                   "`decipherment` TEXT,"
                   "`is_trend_show` BIT NOT NULL DEFAULT 0,"
                   "`is_variety_show` BIT NOT NULL DEFAULT 0"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()