"""
众筹模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, CrowdfundingProject, CrowdfundingDonation
from app.extensions import db
from datetime import datetime
from app.crowdfunding import crowdfunding_bp
from app.models.project import Project, ProjectCategory, ProjectUpdate, ProjectComment
from app.models.payment import ProjectReward, Payment

crowdfunding_bp = Blueprint('crowdfunding', __name__, template_folder='templates/crowdfunding')

@crowdfunding_bp.route('/')
def index():
    """众筹项目列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PROJECTS_PER_PAGE']
    projects = Project.query.filter_by(is_active=True).order_by(Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    categories = ProjectCategory.query.all()
    return render_template('crowdfunding/index.html', 
                          title='众筹项目', 
                          projects=projects,
                          categories=categories)

@crowdfunding_bp.route('/project/<int:project_id>')
def project_detail(project_id):
    """众筹项目详情页面"""
    project = Project.query.get_or_404(project_id)
    updates = ProjectUpdate.query.filter_by(project_id=project_id).order_by(ProjectUpdate.created_at.desc()).all()
    comments = ProjectComment.query.filter_by(project_id=project_id).order_by(ProjectComment.created_at.desc()).all()
    rewards = ProjectReward.query.filter_by(project_id=project_id).all()
    return render_template('crowdfunding/project_detail.html',
                          title=project.title,
                          project=project,
                          updates=updates,
                          comments=comments,
                          rewards=rewards)

@crowdfunding_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """创建众筹项目页面"""
    # 这里需要添加表单处理逻辑
    return render_template('crowdfunding/create_project.html', title='创建众筹项目')

@crowdfunding_bp.route('/category/<int:category_id>')
def category_projects(category_id):
    """按分类查看众筹项目"""
    category = ProjectCategory.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PROJECTS_PER_PAGE']
    projects = Project.query.filter_by(category_id=category_id, is_active=True).paginate(
        page=page, per_page=per_page, error_out=False)
    categories = ProjectCategory.query.all()
    return render_template('crowdfunding/index.html', 
                          title=f'{category.name} - 众筹项目',
                          category=category,
                          projects=projects,
                          categories=categories)

@crowdfunding_bp.route('/search')
def search_projects():
    """搜索众筹项目"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PROJECTS_PER_PAGE']
    
    if not query:
        return redirect(url_for('crowdfunding.index'))
    
    projects = Project.query.filter(
        Project.title.contains(query) | 
        Project.description.contains(query)
    ).filter_by(is_active=True).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('crowdfunding/search_results.html',
                          title=f'搜索结果: {query}',
                          query=query,
                          projects=projects)

@crowdfunding_bp.route('/donate/<int:project_id>', methods=['POST'])
@login_required
def donate(project_id):
    """为项目捐款"""
    # 这里应该处理捐款逻辑
    amount = request.form.get('amount', type=float)
    if not amount or amount <= 0:
        return jsonify({'success': False, 'message': '请输入有效的金额'})
    
    # 模拟捐款成功
    return jsonify({
        'success': True, 
        'message': f'成功为项目ID:{project_id}捐款{amount}元',
        'redirect': url_for('crowdfunding.project_detail', project_id=project_id)
    }) 