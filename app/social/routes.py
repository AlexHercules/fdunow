from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required

# 创建社交模块蓝图
social = Blueprint('social', __name__)

@social.route('/')
def index():
    """社交首页"""
    flash('社交功能正在开发中，敬请期待！', 'info')
    return render_template('social/index.html') 