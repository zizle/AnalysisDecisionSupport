# _*_ coding:utf-8 _*_
# Author: zizle

from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 用户信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `user_info` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`username` VARCHAR(255) NOT NULL UNIQUE,"
                   "`avatar` VARCHAR(256) NOT NULL DEFAULT '',"
                   "`join_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                   "`password` VARCHAR(32) NOT NULL,"
                   "`phone` VARCHAR(11) NOT NULL UNIQUE,"
                   "`email` VARCHAR(64) NOT NULL DEFAULT '',"
                   "`role_num` INT(11) NOT NULL DEFAULT 5,"
                   "`note` VARCHAR(8) NOT NULL DEFAULT '',"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")
    # 用户-客户端表
    cursor.execute("CREATE TABLE IF NOT EXISTS `user_client` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`user_id` INT(11) NOT NULL,"
                   "`client_id` INT(11) NOT NULL,"
                   "`expire_time` DATETIME NOT NULL"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()
