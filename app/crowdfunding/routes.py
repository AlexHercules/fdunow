"""
众筹模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, CrowdfundingProject, CrowdfundingDonation
from app.extensions import db
from datetime import datetime

crowdfunding_bp = Blueprint('crowdfunding', __name__, template_folder='templates/crowdfunding')

@crowdfunding_bp.route('/')
def index():
    """众筹项目列表页面"""
    # 这里应该从数据库获取项目列表
    # 由于模型可能还未完全实现，先使用静态数据
    projects = [
        {
            'id': 1,
            'title': '智能校园导航系统',
            'image': 'project1.jpg',
            'target_amount': 10000,
            'current_amount': 6500,
            'end_date': '2023-12-31',
            'description': '基于AR技术的校园导航解决方案，帮助新生和访客快速找到目的地'
        },
        {
            'id': 2,
            'title': '校园二手交易平台',
            'image': 'project2.jpg',
            'target_amount': 5000,
            'current_amount': 3200,
            'end_date': '2023-12-15',
            'description': '为大学生提供安全、便捷的二手物品交易服务，促进资源循环利用'
        },
        {
            'id': 3,
            'title': '大学生心理健康助手',
            'image': 'project3.jpg',
            'target_amount': 8000,
            'current_amount': 2000,
            'end_date': '2024-01-15',
            'description': '结合AI技术的心理健康评估与辅导系统，为大学生提供心理支持'
        },
    ]
    
    return render_template('crowdfunding/index.html', projects=projects)

@crowdfunding_bp.route('/<int:project_id>')
def project_detail(project_id):
    """众筹项目详情页面"""
    # 这里将来需要从数据库获取项目详情
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

@crowdfunding_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    """创建众筹项目页面"""
    # 需要用户登录才能创建项目
    # 这里将来需要实现表单验证和数据库操作
    # 目前返回一个错误页面
    return render_template('errors/404.html'), 404

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