# _*_ coding:utf-8 _*_
# Author: zizle
import jwt
from hashlib import md5
from settings import SECRET_KEY

# hash密码
def hash_user_password(password):
    hasher = md5()
    hasher.update(password.encode('utf-8'))
    hasher.update(SECRET_KEY.encode('utf-8'))
    # print('输入密码hash后：', hasher.hexdigest())
    return hasher.hexdigest()


# 检查密码
def check_user_password(password, real_password):
    # print("用户输入密码：", password)
    # print('数据库密码：', real_password)
    if hash_user_password(password) == real_password:
        return True
    else:
        return False


def verify_json_web_token(token):
    if not token:
        return None
    try:
        data = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=['HS256']
        )
    except Exception as e:
        # print(e)
        return None
    else:
        return data
