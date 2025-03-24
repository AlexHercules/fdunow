"""
应用扩展初始化模块
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_moment import Moment
from flask_socketio import SocketIO
from flask_ckeditor import CKEditor

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
moment = Moment()
socketio = SocketIO()
ckeditor = CKEditor()

def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    socketio.init_app(app)
    ckeditor.init_app(app)
    
    # 配置 login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'
    login_manager.login_message_category = 'info'
    
    # 加载用户回调
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
