import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from models import db, User

# 创建Flask应用实例
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)
migrate = Migrate(app, db)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 首页路由
@app.route('/')
def index():
    return render_template('index.html', title='校园众创平台')

# 导入并注册蓝图
def register_blueprints(app):
    from crowdfunding import crowdfunding_bp
    from team import team_bp
    from social import social_bp
    from payment import payment_bp
    
    app.register_blueprint(crowdfunding_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(payment_bp)

# 创建数据库表
@app.before_first_request
def create_tables():
    db.create_all()

# 注册错误处理器
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# 注册所有蓝图
register_blueprints(app)

# 如果作为主程序运行
if __name__ == '__main__':
    app.run(debug=True) 