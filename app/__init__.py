import os
from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, csrf, mail, moment, socketio, init_extensions

def create_app(config_class=None):
    """
    应用工厂函数
    
    Args:
        config_class: 配置类
        
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 配置应用
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_pyfile('../config.py')
    
    # 初始化扩展
    init_extensions(app)
    
    # 创建上传目录
    init_upload_folders(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    return app

def init_upload_folders(app):
    """创建上传文件所需的目录"""
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

def register_blueprints(app):
    """注册所有蓝图"""
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.crowdfunding.routes import crowdfunding_bp
    from app.team.routes import team_bp
    from app.payment.routes import payment_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(crowdfunding_bp, url_prefix='/crowdfunding')
    app.register_blueprint(team_bp, url_prefix='/team')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 注册错误处理器
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # 创建目录
    with app.app_context():
        create_directories()

def create_directories():
    """创建必要的目录"""
    from config import basedir
    
    # 上传文件目录
    upload_dir = os.path.join(basedir, 'app', 'static', 'uploads')
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