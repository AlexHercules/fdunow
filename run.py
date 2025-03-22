"""
校园众创平台启动脚本
此文件用于启动Flask应用
"""

import os
from application import app

if __name__ == '__main__':
    app.run(debug=True) 