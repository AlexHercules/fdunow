import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_restx import Api
from models import db, User
from config import config

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
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化数据库迁移
    migrate = Migrate(app, db)
    
    # 初始化登录管理器
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 初始化API文档
    api = Api(
        app, 
        version='1.0', 
        title='校园众创平台 API',
        description='众筹、组队和社交模块接口文档',
        doc='/api/docs',
        prefix='/api'
    )
    
    # 首页路由
    @app.route('/')
    def index():
        return render_template('index.html', title='校园众创平台')
    
    # 注册蓝图和API命名空间
    register_blueprints(app, api)
    
    # 配置错误处理
    configure_error_handlers(app)
    
    # 配置日志（非调试模式）
    if not app.debug and not app.testing:
        configure_logging(app)
    
    # 创建数据库表
    @app.before_first_request
    def create_tables():
        db.create_all()
    
    return app

def register_blueprints(app, api):
    """注册所有蓝图和API命名空间"""
    # 导入蓝图
    from crowdfunding import crowdfunding_bp
    from team import team_bp
    from social import social_bp
    from payment import payment_bp
    
    # 注册网页路由蓝图
    app.register_blueprint(crowdfunding_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(payment_bp)
    
    # 导入并注册API命名空间
    try:
        # 导入API命名空间
        from crowdfunding import ns as crowdfunding_ns
        from team import ns as team_ns
        from social import ns as social_ns
        from payment import ns as payment_ns
        
        # 注册到API
        api.add_namespace(crowdfunding_ns, path='/crowdfunding')
        api.add_namespace(team_ns, path='/team')
        api.add_namespace(social_ns, path='/social')
        api.add_namespace(payment_ns, path='/payment')
    except ImportError as e:
        app.logger.warning(f"API命名空间导入异常: {e}")

def configure_error_handlers(app):
    """配置错误处理器"""
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f'404错误: {request.path}')
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'500错误: {str(e)}')
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        app.logger.warning(f'403错误: {request.path}')
        return render_template('403.html'), 403
    
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f'400错误: {str(e)}')
        return render_template('400.html'), 400

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

# 创建应用实例（使用环境变量或默认为开发环境）
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# 如果作为主程序运行
if __name__ == '__main__':
    app.run() 