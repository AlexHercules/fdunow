"""
后台管理模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime
import json

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')

@admin_bp.route('/')
@login_required
def index():
    """后台管理首页"""
    # 检查用户是否为管理员
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取平台统计数据
    stats = {
        'user_count': 1200,  # 示例数据，实际应从数据库查询
        'project_count': 100,
        'team_count': 50,
        'donation_count': 500,
        'total_donation': 50000
    }
    
    return render_template('admin/index.html', stats=stats)

@admin_bp.route('/users')
@login_required
def users():
    """用户管理页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取用户列表
    # 示例数据，实际应从数据库查询
    users = [
        {'id': 1, 'username': '张三', 'email': 'zhangsan@example.com', 'status': '正常'},
        {'id': 2, 'username': '李四', 'email': 'lisi@example.com', 'status': '正常'},
        {'id': 3, 'username': '王五', 'email': 'wangwu@example.com', 'status': '禁用'}
    ]
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/projects')
@login_required
def projects():
    """项目管理页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取项目列表
    # 示例数据，实际应从数据库查询
    projects = [
        {'id': 1, 'title': '智能校园导航系统', 'status': '筹款中', 'current_amount': 15000, 'target_amount': 20000},
        {'id': 2, 'title': '校园二手交易平台', 'status': '筹款中', 'current_amount': 8000, 'target_amount': 20000},
        {'id': 3, 'title': '复旦历史文化展览', 'status': '筹款中', 'current_amount': 18000, 'target_amount': 20000}
    ]
    
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/teams')
@login_required
def teams():
    """团队管理页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取团队列表
    # 示例数据，实际应从数据库查询
    teams = [
        {'id': 1, 'name': '创新团队A', 'leader': '张三', 'members': 5, 'status': '招募中'},
        {'id': 2, 'name': '创新团队B', 'leader': '李四', 'members': 3, 'status': '已组建'},
        {'id': 3, 'name': '创新团队C', 'leader': '王五', 'members': 6, 'status': '招募中'}
    ]
    
    return render_template('admin/teams.html', teams=teams)

@admin_bp.route('/payments')
@login_required
def payments():
    """支付管理页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取支付记录
    # 示例数据，实际应从数据库查询
    payments = [
        {'id': 1, 'user': '张三', 'project': '智能校园导航系统', 'amount': 100, 'status': '已支付', 'date': '2025-01-01'},
        {'id': 2, 'user': '李四', 'project': '校园二手交易平台', 'amount': 200, 'status': '已支付', 'date': '2025-01-02'},
        {'id': 3, 'user': '王五', 'project': '复旦历史文化展览', 'amount': 300, 'status': '已支付', 'date': '2025-01-03'}
    ]
    
    return render_template('admin/payments.html', payments=payments)

@admin_bp.route('/statistics')
@login_required
def statistics():
    """数据统计页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取统计数据
    # 示例数据，实际应从数据库查询
    monthly_donations = [
        {'month': '1月', 'amount': 5000},
        {'month': '2月', 'amount': 8000},
        {'month': '3月', 'amount': 12000},
        {'month': '4月', 'amount': 10000},
        {'month': '5月', 'amount': 15000}
    ]
    
    project_categories = [
        {'category': '科技创新', 'count': 25},
        {'category': '公益活动', 'count': 20},
        {'category': '学术研究', 'count': 15},
        {'category': '文化艺术', 'count': 25},
        {'category': '其他', 'count': 15}
    ]
    
    return render_template('admin/statistics.html', 
                          monthly_donations=monthly_donations,
                          project_categories=project_categories)

@admin_bp.route('/content-audit')
@login_required
def content_audit():
    """内容审核页面"""
    if not current_user.is_admin:
        flash('您没有权限访问管理后台', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取待审核内容
    # 示例数据，实际应从数据库查询
    pending_projects = [
        {'id': 1, 'title': '创意项目A', 'creator': '张三', 'date': '2025-01-01'},
        {'id': 2, 'title': '创意项目B', 'creator': '李四', 'date': '2025-01-02'}
    ]
    
    pending_comments = [
        {'id': 1, 'content': '这个项目很有创意', 'user': '张三', 'date': '2025-01-01'},
        {'id': 2, 'content': '支持这个项目', 'user': '李四', 'date': '2025-01-02'}
    ]
    
    return render_template('admin/content_audit.html', 
                          pending_projects=pending_projects,
                          pending_comments=pending_comments)

@admin_bp.route('/api/stats')
@login_required
def api_stats():
    """获取统计数据的API接口"""
    if not current_user.is_admin:
        return jsonify({'error': '没有权限访问'}), 403
    
    # 模拟返回一些统计数据
    return jsonify({
        'users': {
            'total': 1200,
            'active': 800,
            'new_this_month': 120
        },
        'projects': {
            'total': 100,
            'active': 60,
            'completed': 40
        },
        'donations': {
            'total_amount': 50000,
            'average_amount': 100,
            'success_rate': 0.85
        }
    }) 