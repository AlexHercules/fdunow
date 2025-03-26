"""
团队模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Team, TeamType, TeamMember, TeamRequirement
from app.extensions import db
from datetime import datetime

team_bp = Blueprint('team', __name__, template_folder='templates/team')

@team_bp.route('/')
def index():
    """团队列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['TEAMS_PER_PAGE']
    teams = Team.query.filter_by(is_active=True).order_by(Team.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template('team/index.html', 
                          title='创业团队', 
                          teams=teams)

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
    team = Team.query.get_or_404(team_id)
    members = TeamMember.query.filter_by(team_id=team_id).all()
    requirements = TeamRequirement.query.filter_by(team_id=team_id, is_active=True).all()
    return render_template('team/team_detail.html',
                          title=team.name,
                          team=team,
                          members=members,
                          requirements=requirements)

@team_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """创建团队页面"""
    # 这里需要添加表单处理逻辑
    return render_template('team/create_team.html', title='创建团队')

@team_bp.route('/join/<int:team_id>', methods=['GET', 'POST'])
@login_required
def join_team(team_id):
    """申请加入团队"""
    team = Team.query.get_or_404(team_id)
    # 检查用户是否已经是团队成员
    if TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first():
        flash('您已经是团队成员', 'info')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 这里需要添加申请表单处理逻辑
    return render_template('team/join_team.html', 
                          title=f'加入团队 - {team.name}', 
                          team=team)

@team_bp.route('/search')
def search_teams():
    """搜索团队"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['TEAMS_PER_PAGE']
    
    if not query:
        return redirect(url_for('team.index'))
    
    teams = Team.query.filter(
        Team.name.contains(query) | 
        Team.description.contains(query)
    ).filter_by(is_active=True).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('team/search_results.html',
                          title=f'搜索结果: {query}',
                          query=query,
                          teams=teams)

@team_bp.route('/my_teams')
@login_required
def my_teams():
    """我的团队页面"""
    # 获取我创建的团队
    owned_teams = Team.query.filter_by(founder_id=current_user.id).all()
    
    # 获取我参与的团队
    team_members = TeamMember.query.filter_by(user_id=current_user.id).all()
    joined_team_ids = [tm.team_id for tm in team_members]
    joined_teams = Team.query.filter(Team.id.in_(joined_team_ids)).all()
    
    return render_template('team/my_teams.html',
                          title='我的团队',
                          owned_teams=owned_teams,
                          joined_teams=joined_teams) 