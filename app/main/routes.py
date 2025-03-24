from flask import render_template, Blueprint, current_app
from app.extensions import db

main_bp = Blueprint('main', __name__, template_folder='templates/main')

@main_bp.route('/')
def index():
    """首页路由"""
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    """关于我们页面路由"""
    return render_template('main/about.html') 