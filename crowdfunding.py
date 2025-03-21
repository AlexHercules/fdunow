from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource, fields, reqparse
from models import db, Project, ProjectUpdate, Team, Donation, ProjectCategory, user_likes
from datetime import datetime
import os

# 创建蓝图
crowdfunding_bp = Blueprint('crowdfunding', __name__, url_prefix='/crowdfunding')

# 创建API命名空间
ns = Namespace('众筹', description='众筹模块API接口')

# 定义API模型
project_model = ns.model('Project', {
    'id': fields.Integer(readonly=True, description='项目ID'),
    'title': fields.String(required=True, description='项目标题'),
    'description': fields.String(required=True, description='项目描述'),
    'category': fields.String(required=True, description='项目分类', enum=[cat.name for cat in ProjectCategory]),
    'target_amount': fields.Float(required=True, description='目标金额'),
    'current_amount': fields.Float(readonly=True, description='已筹集金额'),
    'start_date': fields.DateTime(readonly=True, description='开始日期'),
    'end_date': fields.DateTime(description='结束日期'),
    'status': fields.String(readonly=True, description='项目状态', enum=['draft', 'active', 'funded', 'closed']),
    'likes_count': fields.Integer(readonly=True, description='点赞数'),
    'creator_id': fields.Integer(readonly=True, description='创建者ID'),
    'team_id': fields.Integer(description='团队ID'),
    'image_url': fields.String(description='项目图片URL')
})

project_update_model = ns.model('ProjectUpdate', {
    'id': fields.Integer(readonly=True, description='更新ID'),
    'title': fields.String(required=True, description='更新标题'),
    'content': fields.String(required=True, description='更新内容'),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'project_id': fields.Integer(readonly=True, description='项目ID')
})

donation_model = ns.model('Donation', {
    'id': fields.Integer(readonly=True, description='捐赠ID'),
    'amount': fields.Float(required=True, description='捐赠金额'),
    'message': fields.String(description='留言'),
    'is_anonymous': fields.Boolean(description='是否匿名', default=False),
    'created_at': fields.DateTime(readonly=True, description='捐赠时间'),
    'donor_id': fields.Integer(readonly=True, description='捐赠者ID'),
    'project_id': fields.Integer(readonly=True, description='项目ID')
})

# 定义查询参数解析器
project_list_parser = reqparse.RequestParser()
project_list_parser.add_argument('category', type=str, help='项目分类')
project_list_parser.add_argument('sort_by', choices=('latest', 'popular', 'funding'), default='latest', help='排序方式')
project_list_parser.add_argument('page', type=int, default=1, help='页码')
project_list_parser.add_argument('per_page', type=int, default=10, help='每页数量')

# API资源
@ns.route('/projects')
class ProjectList(Resource):
    @ns.doc('获取项目列表')
    @ns.expect(project_list_parser)
    @ns.marshal_list_with(project_model)
    def get(self):
        """获取众筹项目列表"""
        args = project_list_parser.parse_args()
        category = args.get('category', 'all')
        sort_by = args.get('sort_by', 'latest')
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        
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
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items
    
    @ns.doc('创建项目')
    @ns.expect(project_model)
    @ns.marshal_with(project_model, code=201)
    @ns.response(403, '没有权限')
    @ns.response(400, '无效请求')
    def post(self):
        """创建新众筹项目"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/projects/<int:id>')
@ns.param('id', '项目ID')
@ns.response(404, '项目不存在')
class ProjectDetail(Resource):
    @ns.doc('获取项目详情')
    @ns.marshal_with(project_model)
    def get(self, id):
        """获取众筹项目详情"""
        project = Project.query.get_or_404(id)
        return project
    
    @ns.doc('更新项目')
    @ns.expect(project_model)
    @ns.marshal_with(project_model)
    @ns.response(403, '没有权限')
    def put(self, id):
        """更新众筹项目"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501
    
    @ns.doc('删除项目')
    @ns.response(204, '项目已删除')
    @ns.response(403, '没有权限')
    def delete(self, id):
        """删除众筹项目"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/projects/<int:id>/like')
@ns.param('id', '项目ID')
class ProjectLike(Resource):
    @ns.doc('点赞项目')
    @ns.response(200, '操作成功')
    @ns.response(404, '项目不存在')
    def post(self, id):
        """给项目点赞"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/projects/<int:id>/updates')
@ns.param('id', '项目ID')
class ProjectUpdateList(Resource):
    @ns.doc('获取项目更新列表')
    @ns.marshal_list_with(project_update_model)
    def get(self, id):
        """获取项目更新列表"""
        updates = ProjectUpdate.query.filter_by(project_id=id).order_by(ProjectUpdate.created_at.desc()).all()
        return updates
    
    @ns.doc('添加项目更新')
    @ns.expect(project_update_model)
    @ns.marshal_with(project_update_model, code=201)
    @ns.response(403, '没有权限')
    def post(self, id):
        """添加项目更新"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/projects/<int:id>/donations')
@ns.param('id', '项目ID')
class ProjectDonationList(Resource):
    @ns.doc('获取项目捐赠列表')
    @ns.marshal_list_with(donation_model)
    def get(self, id):
        """获取项目捐赠列表"""
        donations = Donation.query.filter_by(project_id=id).order_by(Donation.created_at.desc()).all()
        return donations
    
    @ns.doc('捐赠项目')
    @ns.expect(donation_model)
    @ns.marshal_with(donation_model, code=201)
    def post(self, id):
        """向项目捐赠"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

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
                          user_liked=user_liked,
                          now=datetime.utcnow())

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
            flash('捐赠金额必须大于0', 'danger')
            return render_template('crowdfunding/donate.html', project=project)
        
        # 重定向到支付处理页面
        return redirect(url_for('payment.process_payment', 
                               amount=amount, 
                               project_id=project_id,
                               message=message,
                               is_anonymous=is_anonymous))
    
    return render_template('crowdfunding/donate.html', project=project) 