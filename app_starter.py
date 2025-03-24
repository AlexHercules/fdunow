"""
校园众创平台 - 简化启动文件
用于解决编码问题并启动应用
"""
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# 创建基本应用
app = Flask(__name__,
            template_folder='app/templates',
            static_folder='app/static')

# 配置
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app-test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads')

# 初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

# 简单的用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

# 用户加载器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库和目录
with app.app_context():
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # 创建数据库表
    db.create_all()

# 路由
@app.route('/')
def index():
    return render_template('main/index.html')

@app.route('/about')
def about():
    return render_template('main/about.html')

@app.route('/crowdfunding')
def crowdfunding():
    return render_template('crowdfunding/index.html')

@app.route('/team')
def team():
    return render_template('team/index.html')

@app.route('/payment')
def payment():
    return render_template('payment/index.html')

# 启动应用
if __name__ == '__main__':
    app.run(debug=True) 