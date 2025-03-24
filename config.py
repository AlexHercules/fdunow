"""
应用配置文件
"""

import os
from datetime import timedelta

# 获取当前目录的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'another-hard-to-guess-string'
    
    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 上传文件配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    PROJECT_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'projects')
    USER_AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    TEAM_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'teams')
    PAYMENT_EVIDENCE_FOLDER = os.path.join(UPLOAD_FOLDER, 'payments')
    
    # 分页配置
    PROJECTS_PER_PAGE = 9
    TEAMS_PER_PAGE = 9
    COMMENTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    
    # 应用名称
    APP_NAME = '校园众创平台 - 复旦大学学生创新创业中心'
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app-dev.sqlite')
    
    # 邮件发送方式
    MAIL_SUPPRESS_SEND = True  # 开发环境不实际发送邮件

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app-test.sqlite')
    
    # 邮件发送方式
    MAIL_SUPPRESS_SEND = True
    
    # 测试环境关闭CSRF保护
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.sqlite')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    'default': DevelopmentConfig
} 