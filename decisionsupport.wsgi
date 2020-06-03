import os
import sys

# 虚拟环境包位置
virtual_dir = 'E:/Virtualenv/decisionSupport/Lib/site-packages'
sys.path.insert(0, virtual_dir)
# 项目文件位置
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import app as application
