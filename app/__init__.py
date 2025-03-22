from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import config

# 创建扩展实例，这些在application.py中已经创建，这里仅作声明
db = None  # 在application.py中已定义
login_manager = None  # 在application.py中已定义
mail = None  # 在application.py中已定义

# 注释掉应用工厂函数，使用application.py中的工厂函数
"""
def create_app(config_name='default'):
    # 应用工厂函数，根据配置名创建Flask应用实例
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # 注册蓝图
    from .auth import auth
    app.register_blueprint(auth, url_prefix='/auth')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    return app
""" 