import os
import sys
from flask_mail import Mail  # 提前导入Flask-Mail

# 将当前目录添加到路径中，以确保可以导入当前目录下的模块
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 显式导入application.py，而不是app.py或app包
import application

app = application.app

if __name__ == '__main__':
    app.run(debug=True) 