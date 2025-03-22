from flask import Blueprint, render_template, request, current_app, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User
from sqlalchemy import or_

# 创建用户蓝图
user = Blueprint('user', __name__)

@user.route('/list')
@login_required
def list():
    """用户列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('USERS_PER_PAGE', 12)
    
    # 处理搜索条件
    query = request.args.get('query', '')
    major = request.args.get('major', '')
    skill = request.args.get('skill', '')
    
    # 构建查询
    user_query = User.query
    
    # 应用搜索过滤
    if query:
        user_query = user_query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.name.ilike(f'%{query}%'),
                User.bio.ilike(f'%{query}%')
            )
        )
    
    # 专业过滤
    if major:
        user_query = user_query.filter(User.major.ilike(f'%{major}%'))
    
    # 技能过滤（字符串匹配，可能需要根据实际存储方式调整）
    if skill:
        user_query = user_query.filter(User.skills.ilike(f'%{skill}%'))
    
    # 分页
    pagination = user_query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    # 获取所有可用的专业和技能列表（用于过滤选项）
    # 注意：在实际应用中，这可能需要优化或缓存，特别是用户数量大时
    distinct_majors = db.session.query(User.major).distinct().filter(User.major != None, User.major != '').all()
    majors = [m[0] for m in distinct_majors]
    
    # 从所有用户的技能字段中提取不同的技能（假设技能是以逗号分隔的）
    # 这种实现方式取决于数据库中技能的实际存储方式
    all_users_with_skills = User.query.filter(User.skills != None, User.skills != '').all()
    all_skills = set()
    for u in all_users_with_skills:
        if u.skills:
            skills = [s.strip() for s in u.skills.split(',')]
            all_skills.update(skills)
    
    # 将技能列表转换为已排序的列表
    skills = sorted(list(all_skills))
    
    return render_template(
        'user/list.html',
        users=users,
        pagination=pagination,
        current_user=current_user,
        majors=majors,
        skills=skills,
        query=query,
        major=major,
        skill=skill
    )

@user.route('/detail/<int:user_id>')
@login_required
def detail(user_id):
    """用户详情页面"""
    # 获取用户及其关联数据
    user_obj = User.query.get_or_404(user_id)
    
    # 获取用户创建的项目
    created_projects = user_obj.created_projects.all()
    
    # 获取用户支持的项目
    supported_projects = user_obj.supported_projects.all()
    
    # 获取用户的团队
    teams = user_obj.teams.all()
    
    # 获取用户的好友（如果当前用户有权查看）
    friends = []
    if user_id == current_user.id or current_user.is_friend(user_obj):
        friends = user_obj.friends.all()
    
    return render_template(
        'user/detail.html',
        user=user_obj,
        created_projects=created_projects,
        supported_projects=supported_projects,
        teams=teams,
        friends=friends
    )

@user.route('/search')
@login_required
def search():
    """用户搜索API"""
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        return render_template('user/search_results.html', users=[])
    
    # 基于用户名、姓名、技能等搜索用户
    users = User.query.filter(
        or_(
            User.username.ilike(f'%{query}%'),
            User.name.ilike(f'%{query}%'),
            User.bio.ilike(f'%{query}%'),
            User.skills.ilike(f'%{query}%'),
            User.major.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return render_template('user/search_results.html', users=users)