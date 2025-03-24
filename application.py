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
from flask_socketio import SocketIO

# 加载环境变量
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_restx import Api
from flask_mail import Mail
from werkzeug.security import check_password_hash, generate_password_hash
from config import config
from app.extensions import db, migrate, login_manager, mail, moment, socketio

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
    mail.init_app(app)
    moment.init_app(app)
    socketio.init_app(app)
    
    # 允许跨域请求
    CORS(app)
    
    # 导入模型以确保SQLAlchemy能够识别它们
    from app.models import User, VerificationCode
    
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
        
        # 实时消息蓝图
        try:
            from app.realtime import realtime as realtime_blueprint
            app.register_blueprint(realtime_blueprint, url_prefix='/realtime')
        except ImportError:
            app.logger.warning('无法导入实时消息模块，跳过注册实时消息蓝图')
        
        # 注册邮件蓝图
        try:
            from app.mail import mail_bp
            app.register_blueprint(mail_bp, url_prefix='/mail')
        except ImportError:
            app.logger.warning('无法导入邮件模块，跳过注册邮件蓝图')
        
        # 注册众筹蓝图
        try:
            from app.crowdfunding import crowdfunding
            app.register_blueprint(crowdfunding, url_prefix='/crowdfunding')
        except ImportError:
            app.logger.warning("众筹模块未找到")
        
        # 注册团队蓝图
        try:
            from app.team import team
            app.register_blueprint(team, url_prefix='/team')
        except ImportError:
            app.logger.warning("团队模块未找到")
        
        # 注册社交蓝图
        try:
            from app.social import social
            app.register_blueprint(social, url_prefix='/social')
        except ImportError:
            app.logger.warning("社交模块未找到")
        
        # 注册支付蓝图
        try:
            from app.payment import payment_bp
            app.register_blueprint(payment_bp, url_prefix='/payment')
        except ImportError:
            app.logger.warning("支付模块未找到")
            
        # 注册管理蓝图
        try:
            from app.admin import admin
            app.register_blueprint(admin, url_prefix='/admin')
        except ImportError:
            app.logger.warning("管理模块未找到")
            
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
    
    # 注册错误处理
    try:
        from app.errors import register_error_handlers
        register_error_handlers(app)
    except ImportError:
        app.logger.warning("错误处理模块未找到")
    
    # 配置日志（非调试模式）
    if not app.debug and not app.testing:
        configure_logging(app)
    
    # 注册自定义模板过滤器
    def register_template_filters(app):
        """注册自定义模板过滤器"""
        from app.utils import safe_html
        
        @app.template_filter('safe_html')
        def safe_html_filter(text):
            return safe_html(text)
        
        @app.template_filter('format_datetime')
        def format_datetime(value, format='%Y-%m-%d %H:%M'):
            """格式化日期时间"""
            if value is None:
                return ""
            return value.strftime(format)
        
        @app.template_filter('format_currency')
        def format_currency(value):
            """格式化货币"""
            if value is None:
                return "0.00"
            return "{:,.2f}".format(float(value))
    
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
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000) 