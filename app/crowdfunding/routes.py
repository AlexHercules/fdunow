"""
众筹模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import User, CrowdfundingProject, CrowdfundingDonation
from application import db
from datetime import datetime

crowdfunding = Blueprint('crowdfunding', __name__)

@crowdfunding.route('/')
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

@crowdfunding.route('/project/<int:project_id>')
def project_detail(project_id):
    """众筹项目详情页面"""
    # 模拟项目数据
    projects = {
        1: {
            'id': 1,
            'title': '智能校园导航系统',
            'image': 'project1.jpg',
            'target_amount': 10000,
            'current_amount': 6500,
            'end_date': '2023-12-31',
            'description': '基于AR技术的校园导航解决方案，帮助新生和访客快速找到目的地',
            'content': """
                <h4>项目介绍</h4>
                <p>智能校园导航系统是一款基于AR(增强现实)技术的校园导航应用，旨在解决新生和访客在校园内寻找目的地的困难。</p>
                
                <h4>项目特点</h4>
                <ul>
                    <li>实时AR导航，直观显示路线</li>
                    <li>智能语音引导，提供详细指示</li>
                    <li>校园热点标记，了解周边设施</li>
                    <li>室内外无缝导航，覆盖整个校园</li>
                </ul>
                
                <h4>资金用途</h4>
                <p>筹集的资金将用于技术开发、服务器租用、应用测试以及市场推广。我们计划在完成开发后，首先在复旦大学内部试运行，然后推广到其他高校。</p>
            """
        },
        2: {
            'id': 2,
            'title': '校园二手交易平台',
            'image': 'project2.jpg',
            'target_amount': 5000,
            'current_amount': 3200,
            'end_date': '2023-12-15',
            'description': '为大学生提供安全、便捷的二手物品交易服务，促进资源循环利用',
            'content': """
                <h4>项目介绍</h4>
                <p>校园二手交易平台是一个专为大学生设计的二手物品交易服务，旨在促进校园内资源的高效循环利用，减少浪费。</p>
                
                <h4>项目特点</h4>
                <ul>
                    <li>校园实名认证，保障交易安全</li>
                    <li>智能物品分类，快速找到所需</li>
                    <li>便捷的校内面交系统，省去物流成本</li>
                    <li>信用评价机制，提升用户体验</li>
                </ul>
                
                <h4>资金用途</h4>
                <p>筹集的资金将用于平台开发、服务器维护、安全系统建设以及平台推广。我们希望打造一个真正服务于大学生的专属交易平台。</p>
            """
        },
        3: {
            'id': 3,
            'title': '大学生心理健康助手',
            'image': 'project3.jpg',
            'target_amount': 8000,
            'current_amount': 2000,
            'end_date': '2024-01-15',
            'description': '结合AI技术的心理健康评估与辅导系统，为大学生提供心理支持',
            'content': """
                <h4>项目介绍</h4>
                <p>大学生心理健康助手是一款结合AI技术的心理健康评估与辅导系统，旨在为大学生提供及时、专业的心理支持和辅导。</p>
                
                <h4>项目特点</h4>
                <ul>
                    <li>AI情绪分析，及时发现异常</li>
                    <li>心理测评工具，科学评估状态</li>
                    <li>匿名咨询服务，保护隐私</li>
                    <li>专业心理资源对接，提供专业辅导</li>
                </ul>
                
                <h4>资金用途</h4>
                <p>筹集的资金将用于AI算法开发、专业心理学内容制作、平台运维以及与专业心理咨询机构的合作。我们希望通过技术手段，让每个大学生都能获得及时的心理支持。</p>
            """
        }
    }
    
    project = projects.get(project_id)
    if not project:
        flash('项目不存在')
        return redirect(url_for('crowdfunding.index'))
    
    return render_template('crowdfunding/project_detail.html', project=project)

@crowdfunding.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """创建众筹项目"""
    if request.method == 'POST':
        # 这里应该处理表单提交，创建新项目
        flash('项目创建功能尚未实现')
        return redirect(url_for('crowdfunding.index'))
    
    return render_template('crowdfunding/create_project.html')

@crowdfunding.route('/donate/<int:project_id>', methods=['POST'])
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