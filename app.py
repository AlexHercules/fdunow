import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_restx import Api
from models import db, User
from config import config
from werkzeug.security import check_password_hash, generate_password_hash

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
    
    # 登录路由
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """用户登录页面"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = 'remember' in request.form
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
        
        return render_template('login.html')
    
    # 注册路由
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """用户注册页面"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # 验证表单
            if not all([username, email, password, confirm_password]):
                flash('请填写所有必填字段')
                return render_template('register.html')
                
            if password != confirm_password:
                flash('两次输入的密码不一致')
                return render_template('register.html')
                
            # 检查用户名和邮箱是否已存在
            if User.query.filter_by(username=username).first():
                flash('用户名已存在')
                return render_template('register.html')
                
            if User.query.filter_by(email=email).first():
                flash('邮箱已被注册')
                return render_template('register.html')
            
            # 创建新用户
            user = User(username=username, email=email)
            user.password_hash = generate_password_hash(password)
            db.session.add(user)
            db.session.commit()
            
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    # 退出登录路由
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    # 仪表盘路由
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """登录后的功能导航页面"""
        return render_template('dashboard.html')
    
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