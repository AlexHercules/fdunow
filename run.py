"""
应用启动脚本
"""

import os
from dotenv import load_dotenv
from app import create_app, db
from app.models.user import User, Role
from app.models.project import ProjectCategory
from flask_migrate import upgrade

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """为 Flask shell 添加上下文"""
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
    admin_email = os.getenv('ADMIN_EMAIL') or 'admin@fdunow.com'
    admin_username = os.getenv('ADMIN_USERNAME') or 'admin'
    admin_password = os.getenv('ADMIN_PASSWORD') or 'Admin123!'
    User.create_admin_user(admin_email, admin_username, admin_password)

if __name__ == '__main__':
    app.run(debug=True)
