"""
校园众创平台应用主模块
此文件原为app.py，为避免与app包冲突，重命名为application.py
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_restx import Api
from flask_mail import Mail  # 导入Mail
from werkzeug.security import check_password_hash, generate_password_hash
from config import config

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问此页面'
mail = Mail()  # 初始化Mail

# 创建应用工厂函数
def create_app(config_name='default'):
    """应用工厂函数，根据配置名创建Flask应用实例"""
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 注册扩展
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # 初始化mail
    
    # 导入模型以确保SQLAlchemy能够识别它们
    from models import User, VerificationCode
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 注册蓝图
    try:
        # 直接导入auth蓝图
        from app.auth import auth
        app.register_blueprint(auth, url_prefix='/auth')
        
        # 注册邮件蓝图
        from app.mail import mail_bp
        app.register_blueprint(mail_bp, url_prefix='/mail')
        
        # 注册众筹蓝图
        try:
            from app.crowdfunding import crowdfunding
            has_crowdfunding = True
        except ImportError:
            has_crowdfunding = False
            app.logger.warning("Crowdfunding module not found")
        
        # 注册团队蓝图
        try:
            from app.team import team
            has_team = True
        except ImportError:
            has_team = False
            app.logger.warning("Team module not found")
        
        if has_crowdfunding:
            app.register_blueprint(crowdfunding, url_prefix='/crowdfunding')
        if has_team:
            app.register_blueprint(team, url_prefix='/team')
    except ImportError as e:
        app.logger.warning(f"蓝图导入失败: {e}")
    
    # 首页路由
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/favicon.ico')
    def favicon():
        return redirect(url_for('static', filename='favicon.ico'))
    
    # 项目详情页面路由
    @app.route('/project/campus-nav')
    def campus_nav():
        return render_template('project/campus-nav.html')
    
    @app.route('/project/second-hand')
    def second_hand():
        return render_template('project/second-hand.html')
    
    # 配置错误处理器
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # 配置日志（非调试模式）
    if not app.debug and not app.testing:
        configure_logging(app)
    
    return app

def configure_logging(app):
    """配置应用日志"""
    # 设置日志级别
    app.logger.setLevel(logging.INFO)
    
    # 创建日志处理器
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # 添加到应用日志
    app.logger.addHandler(file_handler)
    app.logger.info('校园众创平台 启动')

# 创建API实例
api = Api(
    version='1.0',
    title='校园众创平台 API',
    description='众筹、组队和社交模块API文档',
    doc='/api/docs',
    prefix='/api'
)

# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))
api.init_app(app)

# 如果作为主程序运行
if __name__ == '__main__':
    app.run(debug=True) 