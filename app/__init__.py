import os
from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, csrf, mail, moment, socketio, ckeditor, init_extensions

def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称
        
    Returns:
        Flask应用实例
    """
    print(f"初始化应用，配置: {config_name}")
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    print(f"使用配置: {config_name}")
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    print("初始化扩展...")
    init_extensions(app)
    
    # 创建上传目录
    print("创建上传目录...")
    init_upload_folders(app)
    
    # 注册蓝图
    print("注册蓝图...")
    register_blueprints(app)
    
    # 注册错误处理
    print("注册错误处理...")
    register_errors(app)
    
    # 注册Shell上下文
    register_shell_context(app)
    
    # 注册拦截器
    register_hooks(app)
    
    # 创建目录
    with app.app_context():
        create_directories()
    
    print("应用初始化完成")
    return app

def init_upload_folders(app):
    """创建上传文件所需的目录"""
    try:
        upload_folders = [
            app.config.get('UPLOAD_FOLDER', 'uploads'),
            app.config.get('PROJECT_IMAGE_FOLDER', 'uploads/projects'),
            app.config.get('USER_AVATAR_FOLDER', 'uploads/avatars'),
            app.config.get('TEAM_IMAGE_FOLDER', 'uploads/teams'),
            app.config.get('PAYMENT_EVIDENCE_FOLDER', 'uploads/payments')
        ]
        
        for folder in upload_folders:
            # 确保路径是绝对路径
            if not os.path.isabs(folder):
                folder = os.path.join(app.root_path, folder)
            
            # 创建目录（如果不存在）
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"创建目录: {folder}")
    except Exception as e:
        print(f"创建上传目录失败: {e}")

def register_blueprints(app):
    """注册所有蓝图"""
    try:
        # 主页蓝图
        from app.main import main_bp
        app.register_blueprint(main_bp)
        
        # 认证蓝图
        from app.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # 后台管理蓝图
        try:
            from app.admin import admin_bp, init_admin
            app.register_blueprint(admin_bp, url_prefix='/admin')
        except ImportError as e:
            print(f"管理模块导入失败，已跳过: {e}")
        
        # 尝试加载其他蓝图，如果导入失败则跳过
        try:
            from app.crowdfunding import init_crowdfunding
            app.register_blueprint(init_crowdfunding(), url_prefix='/crowdfunding')
        except ImportError as e:
            print(f"众筹模块导入失败，已跳过: {e}")
            
        try:
            from app.team import init_team
            app.register_blueprint(init_team(), url_prefix='/team')
        except ImportError as e:
            print(f"团队模块导入失败，已跳过: {e}")
            
        try:
            from app.payment import init_payment
            app.register_blueprint(init_payment(), url_prefix='/payment')
        except ImportError as e:
            print(f"支付模块导入失败，已跳过: {e}")
        
        print("所有蓝图注册成功")
    except Exception as e:
        print(f"注册蓝图失败: {e}")
        import traceback
        traceback.print_exc()

def register_errors(app):
    """注册错误处理器"""
    try:
        from app.errors import register_error_handlers
        register_error_handlers(app)
        print("错误处理器注册成功")
    except Exception as e:
        print(f"注册错误处理器失败: {e}")
        
        # 如果errors模块不可用，使用简单的错误处理
        @app.errorhandler(404)
        def page_not_found(e):
            return "页面未找到", 404
        
        @app.errorhandler(500)
        def internal_server_error(e):
            return "服务器内部错误", 500

def register_shell_context(app):
    """注册shell上下文"""
    @app.shell_context_processor
    def make_shell_context():
        try:
            from app.models.user import User, Role
            from app.models.project import Project, ProjectCategory
            return dict(db=db, User=User, Role=Role, Project=Project, ProjectCategory=ProjectCategory)
        except Exception as e:
            print(f"加载shell上下文失败: {e}")
            return dict(db=db)

def register_hooks(app):
    """注册拦截器"""
    @app.before_request
    def before_request():
        pass

def create_directories():
    """创建必要的目录"""
    try:
        import os
        
        # 上传文件目录
        upload_dir = os.path.join('app', 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 项目图片目录
        project_img_dir = os.path.join(upload_dir, 'projects')
        if not os.path.exists(project_img_dir):
            os.makedirs(project_img_dir)
        
        # 用户头像目录
        avatar_dir = os.path.join(upload_dir, 'avatars')
        if not os.path.exists(avatar_dir):
            os.makedirs(avatar_dir)
        
        # 支付证据目录
        payment_dir = os.path.join(upload_dir, 'payment')
        if not os.path.exists(payment_dir):
            os.makedirs(payment_dir)
    except Exception as e:
        print(f"创建目录失败: {e}")
