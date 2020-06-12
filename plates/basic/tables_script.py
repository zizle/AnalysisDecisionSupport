# _*_ coding:utf-8 _*_
# __Author__： zizle
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 客户端信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_client` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`machine_code` VARCHAR(32) NOT NULL UNIQUE,"
                   "`join_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                   "`is_manager` BIT NOT NULL DEFAULT 0,"
                   "`origin` VARCHAR(10) NOT NULL DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 系统功能模块表
    # level字段对应用户的角色枚举值
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(128) NOT NULL UNIQUE,"
                   "`parent_id` INT(11) DEFAULT NULL,"
                   "`level` INT(11) DEFAULT 5,"
                   "`sort` INT(11) DEFAULT 0,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    # 用户-模块表(记录可进入的，level表示的是那些用户可见与否)
    cursor.execute("CREATE TABLE IF NOT EXISTS `link_user_module` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INT(11) NOT NULL,"
                   "`module_id` INT(11) NOT NULL,"
                   "`expire_time` DATETIME NOT NULL,"
                   "UNIQUE KEY `usermodule`(`user_id`,`module_id`)"
                   ");")
    # 添加系统管理模块
    cursor.execute("INSERT INTO `info_module` (`name`,`level`) VALUES ('系统管理', 4);")
    new_mid = db_connection.insert_id()
    # 更新sort
    cursor.execute("UPDATE `info_module` SET `sort`=%d WHERE `id`=%d" % (new_mid,new_mid))
    cursor.execute("INSERT INTO `info_module` (`name`,`parent_id`,`level`) VALUES ('运营管理', %d, 2);" % new_mid)
    new_mid = db_connection.insert_id()
    cursor.execute("UPDATE `info_module` SET `sort`=%d WHERE `id`=%d" % (new_mid, new_mid))
    cursor.execute("INSERT INTO `info_module` (`name`,`parent_id`,`level`) VALUES ('角色管理', %d, 1);" % new_mid)
    new_mid = db_connection.insert_id()
    cursor.execute("UPDATE `info_module` SET `sort`=%d WHERE `id`=%d" % (new_mid, new_mid))

    # 品种信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_variety` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(128) NOT NULL,"
                   "`name_en` VARCHAR(16) NOT NULL DEFAULT '',"
                   "`parent_id` INT(11) DEFAULT NULL,"
                   "`exchange` TINYINT(3) NOT NULL DEFAULT 0,"
                   "`sort` INT(11) DEFAULT 0,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `varietyname`(`name`,`name_en`)"
                   ");")
    # 增加品种4个分组
    cursor.execute("INSERT INTO `info_variety` (`name`) VALUES ('金融股指');")
    new_vid = db_connection.insert_id()
    cursor.execute("UPDATE `info_variety` SET `sort`=%d WHERE `id`=%d" %(new_vid, new_vid))
    cursor.execute("INSERT INTO `info_variety` (`name`) VALUES ('农业产品');")
    new_vid = db_connection.insert_id()
    cursor.execute("UPDATE `info_variety` SET `sort`=%d WHERE `id`=%d" % (new_vid, new_vid))
    cursor.execute("INSERT INTO `info_variety` (`name`) VALUES ('化工材料');")
    new_vid = db_connection.insert_id()
    cursor.execute("UPDATE `info_variety` SET `sort`=%d WHERE `id`=%d" % (new_vid, new_vid))
    cursor.execute("INSERT INTO `info_variety` (`name`) VALUES ('黑色金属');")
    new_vid = db_connection.insert_id()
    cursor.execute("UPDATE `info_variety` SET `sort`=%d WHERE `id`=%d" % (new_vid, new_vid))
    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()
