"""
团队模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Team, TeamType
from app.extensions import db
from datetime import datetime

team_bp = Blueprint('team', __name__, template_folder='templates/team')

@team_bp.route('/')
def index():
    """团队组建页面"""
    return render_template('team/index.html')

@team_bp.route('/post', methods=['GET', 'POST'])
def post_requirement():
    """发布团队需求页面"""
    # 需要用户登录才能发布需求
    # 这里将来需要实现表单验证和数据库操作
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@team_bp.route('/apply/<int:team_id>', methods=['POST'])
def apply_team(team_id):
    """申请加入团队"""
    # 需要用户登录才能申请加入
    # 这里将来需要实现团队申请逻辑
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@team_bp.route('/my_applications')
def my_applications():
    """我的申请记录页面"""
    # 需要用户登录才能查看申请记录
    # 这里将来需要从数据库获取记录
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@team_bp.route('/team/<int:team_id>')
def team_detail(team_id):
    """团队详情页面"""
    # 这里将来需要从数据库获取团队详情
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@team_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """创建团队页面"""
    # 这里将来需要实现表单验证和数据库操作
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@team_bp.route('/join/<int:team_id>', methods=['POST'])
@login_required
def join_team(team_id):
    """加入团队"""
    # 这里将来需要实现团队加入逻辑
    # 目前返回一个简单的成功消息
    return {"success": True, 
            "message": "已申请加入团队，等待团队创建者审核",
            "redirect": url_for('team.team_detail', team_id=team_id)} 