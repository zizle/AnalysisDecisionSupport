# _*_ coding:utf-8 _*_
# Author: zizle

from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 用户信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `info_user` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`username` VARCHAR(255) NOT NULL,"
                   "`avatar` VARCHAR(256) NOT NULL DEFAULT '',"
                   "`join_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                   "`password` VARCHAR(32) NOT NULL,"
                   "`phone` VARCHAR(11) NOT NULL UNIQUE,"
                   "`email` VARCHAR(64) NOT NULL DEFAULT '',"
                   "`role_num` TINYINT(3) NOT NULL DEFAULT 5,"
                   "`note` VARCHAR(8) NOT NULL DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")
    # 用户-客户端表
    cursor.execute("CREATE TABLE IF NOT EXISTS `link_user_client` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INT(11) NOT NULL,"
                   "`client_id` INT(11) NOT NULL,"
                   "`expire_time` DATETIME NOT NULL,"
                   "UNIQUE KEY `userclient`(`user_id`,`client_id`)"
                   ");")

    # 用户-品种表
    cursor.execute("CREATE TABLE IF NOT EXISTS `link_user_variety` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INT(11) NOT NULL,"
                   "`variety_id` INT(11) NOT NULL,"
                   "`is_active` BIT NOT NULL DEFAULT 1,"
                   "UNIQUE KEY `uservariety`(`user_id`,`variety_id`)"
                   ");")

    # 增加一个超级管理员
    cursor.execute("INSERT INTO `info_user` (`username`,`phone`,`role_num`, `password`) "
                   "VALUES ('超级管理员','18866668787',1,'7f4675985509569cd50a96d129a196ff');")
    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()
