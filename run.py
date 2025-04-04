﻿# -*- coding: utf-8 -*-
"""应用启动脚本"""

import os
from dotenv import load_dotenv
from app import create_app, db
from app.models.user import User, Role
from app.models.project import ProjectCategory
from flask_migrate import upgrade

# 加载环境变量
try:
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    print("环境变量加载成功")
except Exception as e:
    print(f"环境变量加载失败: {e}")
    # 设置默认环境变量
    os.environ.setdefault('FLASK_CONFIG', 'development')
    os.environ.setdefault('SECRET_KEY', 'dev-key')

# 创建应用实例
print("开始创建应用实例...")
try:
    app = create_app(os.getenv("FLASK_CONFIG") or "development")
    print("应用实例创建成功!")
except Exception as e:
    import traceback
    print(f"应用创建失败: {e}")
    traceback.print_exc()
    import sys
    sys.exit(1)

@app.shell_context_processor
def make_shell_context():
    """为Flask shell添加数据库和模型上下文"""
    return dict(db=db, User=User, Role=Role, ProjectCategory=ProjectCategory)

@app.cli.command()
def deploy():
    """部署命令"""
    # 迁移数据库到最新版本
    upgrade()
    
    # 创建角色
    Role.insert_roles()
    
    # 创建默认项目类别
    ProjectCategory.insert_categories()
    
    # 创建管理员用户（如果不存在）
    admin_email = os.getenv("ADMIN_EMAIL") or "admin@fdunow.com"
    admin_username = os.getenv("ADMIN_USERNAME") or "admin"
    admin_password = os.getenv("ADMIN_PASSWORD") or "Admin123!"
    User.create_admin_user(admin_email, admin_username, admin_password)

if __name__ == "__main__":
    try:
        print("启动应用服务器...")
        app.run(debug=True)
    except Exception as e:
        import traceback
        print(f"应用启动失败: {e}")
        traceback.print_exc()
