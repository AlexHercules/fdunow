"""
校园众创平台应用主模块
此文件原为app.py，为避免与app包冲突，重命名为application.py
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pathlib import Path
from flask_cors import CORS

# 加载环境变量
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_restx import Api
from flask_mail import Mail  # 导入Mail
from werkzeug.security import check_password_hash, generate_password_hash
from config import config
from app.extensions import db, migrate, login_manager, moment

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
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)  # 初始化mail
    moment.init_app(app)
    
    # 允许跨域请求
    CORS(app)
    
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
        # 主蓝图
        from app.main import main as main_blueprint
        app.register_blueprint(main_blueprint)
        
        # 认证蓝图
        from app.auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        
        # 用户蓝图
        try:
            from app.user import user as user_blueprint
            app.register_blueprint(user_blueprint, url_prefix='/user')
        except ImportError:
            app.logger.warning('无法导入用户模块，跳过注册用户蓝图')
        
        # 个人中心蓝图
        try:
            from app.profile import profile as profile_blueprint
            app.register_blueprint(profile_blueprint, url_prefix='/profile')
        except ImportError:
            app.logger.warning('无法导入个人中心模块，跳过注册个人中心蓝图')
        
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
        
        # 注册社交蓝图
        try:
            from app.social import social
            has_social = True
        except ImportError:
            has_social = False
            app.logger.warning("Social module not found")
        
        # 注册支付蓝图
        try:
            from app.payment import payment
            has_payment = True
        except ImportError:
            has_payment = False
            app.logger.warning("Payment module not found")
        
        if has_crowdfunding:
            app.register_blueprint(crowdfunding, url_prefix='/crowdfunding')
        if has_team:
            app.register_blueprint(team, url_prefix='/team')
        if has_social:
            app.register_blueprint(social, url_prefix='/social')
        if has_payment:
            app.register_blueprint(payment, url_prefix='/payment')
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
    
    # 注册自定义模板过滤器
    def register_template_filters(app):
        # 添加自定义过滤器的地方
        pass
    
    register_template_filters(app)
    
    return app

def configure_logging(app):
    """配置应用日志"""
    # 设置日志级别
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    app.logger.setLevel(numeric_level)
    
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs', exist_ok=True)
    
    # 创建日志处理器
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5)
    file_handler.setLevel(numeric_level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加到应用日志
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
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