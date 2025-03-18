from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Project, ProjectUpdate, Team, Donation, ProjectCategory, user_likes
from datetime import datetime
import os

# 创建蓝图
crowdfunding_bp = Blueprint('crowdfunding', __name__, url_prefix='/crowdfunding')

# 众筹项目列表页
@crowdfunding_bp.route('/')
def index():
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort_by', 'latest')
    
    query = Project.query.filter(Project.status == 'active')
    
    # 按分类筛选
    if category != 'all' and category in [cat.name for cat in ProjectCategory]:
        query = query.filter(Project.category == ProjectCategory[category])
    
    # 排序
    if sort_by == 'latest':
        query = query.order_by(Project.created_at.desc())
    elif sort_by == 'popular':
        query = query.order_by(Project.likes_count.desc())
    elif sort_by == 'funding':
        query = query.order_by(Project.current_amount.desc())
    
    projects = query.all()
    
    return render_template('crowdfunding/index.html', 
                          title='众筹项目', 
                          projects=projects,
                          categories=ProjectCategory,
                          current_category=category,
                          current_sort=sort_by)

# 项目详情页
@crowdfunding_bp.route('/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    updates = project.updates.order_by(ProjectUpdate.created_at.desc()).all()
    
    # 计算项目进度
    if project.target_amount > 0:
        progress = int((project.current_amount / project.target_amount) * 100)
    else:
        progress = 0
        
    # 检查当前用户是否已点赞
    user_liked = False
    if current_user.is_authenticated:
        liked_query = db.session.query(user_likes).filter(
            user_likes.c.user_id == current_user.id,
            user_likes.c.project_id == project_id
        ).first()
        user_liked = liked_query is not None
    
    return render_template('crowdfunding/project_detail.html',
                          title=project.title,
                          project=project,
                          updates=updates,
                          progress=progress,
                          user_liked=user_liked)

# 创建项目页面
@crowdfunding_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        target_amount = float(request.form.get('target_amount', 0))
        end_date_str = request.form.get('end_date')
        
        # 验证表单数据
        if not title or not description or not category:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('crowdfunding.create_project'))
        
        # 处理结束日期
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = None
            
        # 创建新项目
        new_project = Project(
            title=title,
            description=description,
            category=ProjectCategory[category],
            target_amount=target_amount,
            end_date=end_date,
            status='draft',
            creator_id=current_user.id
        )
        
        # 处理上传的图片
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                # 这里应添加实际的图片保存逻辑
                # 在实际应用中，应使用更安全的方法处理文件名和路径
                filename = f"project_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                image_path = os.path.join('static/img/projects', filename)
                image.save(image_path)
                new_project.image_url = image_path
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('项目创建成功！现在您可以发布或继续编辑它。', 'success')
        return redirect(url_for('crowdfunding.project_detail', project_id=new_project.id))
    
    return render_template('crowdfunding/create_project.html', 
                          title='创建众筹项目',
                          categories=ProjectCategory)

# 编辑项目
@crowdfunding_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user.id:
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    if request.method == 'POST':
        # 处理表单提交，更新项目信息
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.category = ProjectCategory[request.form.get('category')]
        project.target_amount = float(request.form.get('target_amount', 0))
        
        end_date_str = request.form.get('end_date')
        if end_date_str:
            project.end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # 处理上传的新图片
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            filename = f"project_{project.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image_path = os.path.join('static/img/projects', filename)
            image.save(image_path)
            project.image_url = image_path
        
        db.session.commit()
        flash('项目更新成功', 'success')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    return render_template('crowdfunding/edit_project.html',
                          title='编辑项目',
                          project=project,
                          categories=ProjectCategory)

# 发布项目（从草稿状态变为活跃状态）
@crowdfunding_bp.route('/<int:project_id>/publish', methods=['POST'])
@login_required
def publish_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user.id:
        flash('您没有权限发布此项目', 'danger')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    # 检查项目是否符合发布条件
    if not project.title or not project.description or not project.category:
        flash('项目信息不完整，无法发布', 'warning')
        return redirect(url_for('crowdfunding.edit_project', project_id=project_id))
    
    # 更新项目状态为活跃
    project.status = 'active'
    project.start_date = datetime.utcnow()
    db.session.commit()
    
    flash('项目已成功发布！', 'success')
    return redirect(url_for('crowdfunding.project_detail', project_id=project_id))

# 点赞项目
@crowdfunding_bp.route('/<int:project_id>/like', methods=['POST'])
@login_required
def like_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查用户是否已点赞
    liked_query = db.session.query(user_likes).filter(
        user_likes.c.user_id == current_user.id,
        user_likes.c.project_id == project_id
    ).first()
    
    if liked_query is None:
        # 添加点赞记录
        stmt = user_likes.insert().values(
            user_id=current_user.id,
            project_id=project_id,
            like_time=datetime.utcnow()
        )
        db.session.execute(stmt)
        
        # 更新项目点赞数
        project.likes_count += 1
        db.session.commit()
        
        return jsonify({'status': 'success', 'likes': project.likes_count, 'action': 'liked'})
    else:
        # 取消点赞
        stmt = user_likes.delete().where(
            user_likes.c.user_id == current_user.id,
            user_likes.c.project_id == project_id
        )
        db.session.execute(stmt)
        
        # 更新项目点赞数
        project.likes_count -= 1
        db.session.commit()
        
        return jsonify({'status': 'success', 'likes': project.likes_count, 'action': 'unliked'})

# 添加项目更新
@crowdfunding_bp.route('/<int:project_id>/update', methods=['POST'])
@login_required
def add_project_update(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user.id:
        flash('您没有权限更新此项目', 'danger')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('标题和内容不能为空', 'warning')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    update = ProjectUpdate(
        title=title,
        content=content,
        project_id=project_id
    )
    
    db.session.add(update)
    db.session.commit()
    
    flash('项目更新已发布', 'success')
    return redirect(url_for('crowdfunding.project_detail', project_id=project_id))

# 一键组队功能
@crowdfunding_bp.route('/<int:project_id>/team', methods=['GET', 'POST'])
@login_required
def create_team(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查权限
    if project.creator_id != current_user.id:
        flash('您没有权限为此项目创建团队', 'danger')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    # 检查项目是否已有团队
    if project.team_id is not None:
        flash('此项目已有团队', 'info')
        return redirect(url_for('team.team_detail', team_id=project.team_id))
    
    if request.method == 'POST':
        name = request.form.get('name', f"{project.title}团队")
        description = request.form.get('description', project.description)
        team_type = request.form.get('team_type', 'PROJECT')
        max_members = int(request.form.get('max_members', 5))
        required_skills = request.form.get('required_skills', '')
        
        # 创建新团队
        team = Team(
            name=name,
            description=description,
            team_type=TeamType[team_type],
            max_members=max_members,
            required_skills=required_skills,
            creator_id=current_user.id,
            status='recruiting'
        )
        
        db.session.add(team)
        db.session.flush()  # 获取team的id
        
        # 将创建者添加为团队成员
        stmt = team_members.insert().values(
            user_id=current_user.id,
            team_id=team.id,
            role='creator',
            join_time=datetime.utcnow()
        )
        db.session.execute(stmt)
        
        # 更新项目关联的团队
        project.team_id = team.id
        
        db.session.commit()
        
        flash('团队创建成功！', 'success')
        return redirect(url_for('team.team_detail', team_id=team.id))
    
    return render_template('crowdfunding/create_team.html',
                          title='创建项目团队',
                          project=project,
                          team_types=TeamType)

# 捐赠/支持项目
@crowdfunding_bp.route('/<int:project_id>/donate', methods=['GET', 'POST'])
@login_required
def donate(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查项目状态
    if project.status != 'active':
        flash('该项目当前不接受捐赠', 'warning')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        message = request.form.get('message', '')
        is_anonymous = 'is_anonymous' in request.form
        
        if amount <= 0:
            flash('捐赠金额必须大于0', 'warning')
            return redirect(url_for('crowdfunding.donate', project_id=project_id))
        
        # 创建捐赠记录
        donation = Donation(
            amount=amount,
            message=message,
            is_anonymous=is_anonymous,
            donor_id=current_user.id,
            project_id=project_id
        )
        
        db.session.add(donation)
        
        # 更新项目筹集金额
        project.current_amount += amount
        
        # 检查是否达到目标金额
        if project.current_amount >= project.target_amount and project.target_amount > 0:
            project.status = 'funded'
        
        db.session.commit()
        
        flash('感谢您的支持！', 'success')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    return render_template('crowdfunding/donate.html',
                          title='支持项目',
                          project=project) 