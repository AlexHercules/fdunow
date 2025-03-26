from flask import render_template, current_app
from app.main import main_bp

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """主页视图"""
    return render_template('main/index.html', title='首页')

@main_bp.route('/about')
def about():
    """关于我们页面"""
    return render_template('main/about.html', title='关于我们') 