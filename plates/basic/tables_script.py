# _*_ coding:utf-8 _*_
# __Author__： zizle
from db import MySQLConnection


def create_tables():
    db_connection = MySQLConnection()
    cursor = db_connection.get_cursor()
    # 客户端信息表
    cursor.execute("CREATE TABLE IF NOT EXISTS `client_info` ("
                   "`id` INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                   "`name` VARCHAR(128) NOT NULL DEFAULT '',"
                   "`machine_code` VARCHAR(32) NOT NULL UNIQUE,"
                   "`join_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                   "`update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                   "`is_manager` BIT NOT NULL DEFAULT 0,"
                   "`is_active` BIT NOT NULL DEFAULT 1"
                   ");")

    db_connection.commit()
    db_connection.close()


if __name__ == '__main__':
    create_tables()
