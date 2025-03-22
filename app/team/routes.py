"""
团队模块路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import User, Team, TeamType
from application import db
from datetime import datetime

team = Blueprint('team', __name__)

@team.route('/')
def index():
    """团队列表页面"""
    # 这里应该从数据库获取团队列表
    # 由于模型可能还未完全实现，先使用静态数据
    teams = [
        {
            'id': 1,
            'name': '智能校园导航团队',
            'image': 'team1.jpg',
            'team_type': '项目',
            'members_count': 5,
            'max_members': 8,
            'description': '开发基于AR技术的校园导航系统，帮助新生和访客快速熟悉校园环境'
        },
        {
            'id': 2,
            'name': '二手交易平台开发团队',
            'image': 'team2.jpg',
            'team_type': '创业',
            'members_count': 4,
            'max_members': 6,
            'description': '构建校园二手物品交易平台，促进资源循环利用，解决学生闲置物品问题'
        },
        {
            'id': 3,
            'name': '算法竞赛小组',
            'image': 'team3.jpg',
            'team_type': '比赛',
            'members_count': 3,
            'max_members': 5,
            'description': '备战全国高校算法竞赛，共同提升算法设计与编程能力'
        },
    ]
    
    return render_template('team/index.html', teams=teams)

@team.route('/team/<int:team_id>')
def team_detail(team_id):
    """团队详情页面"""
    # 模拟团队数据
    teams = {
        1: {
            'id': 1,
            'name': '智能校园导航团队',
            'image': 'team1.jpg',
            'team_type': '项目',
            'members_count': 5,
            'max_members': 8,
            'description': '开发基于AR技术的校园导航系统，帮助新生和访客快速熟悉校园环境',
            'required_skills': '前端开发、AR技术、UI设计、Android/iOS开发',
            'content': """
                <h4>团队介绍</h4>
                <p>我们是一支致力于解决校园新生和访客导航问题的团队。团队成员来自计算机科学、设计和地理信息系统等不同专业背景，力图通过AR技术打造一款直观易用的校园导航应用。</p>
                
                <h4>项目目标</h4>
                <ul>
                    <li>开发功能完善的AR校园导航应用</li>
                    <li>解决校园新生和访客找路难的问题</li>
                    <li>提升校园信息化和智能化水平</li>
                    <li>打造可推广到其他高校的导航解决方案</li>
                </ul>
                
                <h4>招募需求</h4>
                <p>我们目前需要有以下技能的同学加入：</p>
                <ul>
                    <li>前端开发：熟悉React/Vue等前端框架</li>
                    <li>AR开发：有ARCore/ARKit经验者优先</li>
                    <li>UI设计：擅长移动应用界面设计</li>
                    <li>后端开发：熟悉Flask/Django/Node.js等后端框架</li>
                </ul>
            """
        },
        2: {
            'id': 2,
            'name': '二手交易平台开发团队',
            'image': 'team2.jpg',
            'team_type': '创业',
            'members_count': 4,
            'max_members': 6,
            'description': '构建校园二手物品交易平台，促进资源循环利用，解决学生闲置物品问题',
            'required_skills': '全栈开发、产品设计、运营推广、UI/UX设计',
            'content': """
                <h4>团队介绍</h4>
                <p>我们是一支热爱互联网创业的团队，希望通过技术手段解决校园二手物品交易中的痛点问题。团队成员来自计算机、设计和市场营销等专业，拥有丰富的校园生活经验和技术积累。</p>
                
                <h4>项目目标</h4>
                <ul>
                    <li>打造安全、便捷的校园二手交易平台</li>
                    <li>减少资源浪费，促进循环利用</li>
                    <li>解决大学生离校处理物品的难题</li>
                    <li>建立校园内的信任交易环境</li>
                </ul>
                
                <h4>招募需求</h4>
                <p>我们目前需要以下角色的同学加入：</p>
                <ul>
                    <li>后端开发：熟悉数据库设计和API开发</li>
                    <li>产品经理：有产品设计和用户研究经验</li>
                    <li>运营专员：擅长社区运营和用户增长</li>
                    <li>UI/UX设计师：能够设计美观易用的界面</li>
                </ul>
            """
        },
        3: {
            'id': 3,
            'name': '算法竞赛小组',
            'image': 'team3.jpg',
            'team_type': '比赛',
            'members_count': 3,
            'max_members': 5,
            'description': '备战全国高校算法竞赛，共同提升算法设计与编程能力',
            'required_skills': '数据结构、算法设计、竞赛编程、问题分析能力',
            'content': """
                <h4>团队介绍</h4>
                <p>我们是一群热爱算法和编程的同学，希望通过组队参加各类算法竞赛来提升自己的技术能力。团队成员主要来自计算机科学相关专业，有良好的数学基础和编程能力。</p>
                
                <h4>目标赛事</h4>
                <ul>
                    <li>ACM-ICPC国际大学生程序设计竞赛</li>
                    <li>蓝桥杯全国软件和信息技术专业人才大赛</li>
                    <li>全国高校计算机能力挑战赛</li>
                    <li>各类企业举办的算法编程比赛</li>
                </ul>
                
                <h4>招募需求</h4>
                <p>我们希望招募以下特质的队友：</p>
                <ul>
                    <li>扎实的数据结构和算法基础</li>
                    <li>较强的逻辑思维和问题分析能力</li>
                    <li>熟练掌握至少一种编程语言（C++/Java/Python）</li>
                    <li>有竞赛经验者优先，但对新手也很欢迎</li>
                </ul>
            """
        }
    }
    
    team = teams.get(team_id)
    if not team:
        flash('团队不存在')
        return redirect(url_for('team.index'))
    
    return render_template('team/team_detail.html', team=team)

@team.route('/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """创建团队"""
    if request.method == 'POST':
        # 这里应该处理表单提交，创建新团队
        flash('团队创建功能尚未实现')
        return redirect(url_for('team.index'))
    
    return render_template('team/create_team.html')

@team.route('/join/<int:team_id>', methods=['POST'])
@login_required
def join_team(team_id):
    """加入团队"""
    # 这里应该处理加入团队的逻辑
    return jsonify({
        'success': True, 
        'message': f'已申请加入团队ID:{team_id}，等待团队创建者审核',
        'redirect': url_for('team.team_detail', team_id=team_id)
    }) 