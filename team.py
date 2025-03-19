from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource, fields, reqparse
from models import db, Team, TeamType, team_members, User
from datetime import datetime
import os

# 创建蓝图
team_bp = Blueprint('team', __name__, url_prefix='/team')

# 创建API命名空间
ns = Namespace('组队', description='组队模块API接口')

# 定义API模型
team_model = ns.model('Team', {
    'id': fields.Integer(readonly=True, description='团队ID'),
    'name': fields.String(required=True, description='团队名称'),
    'description': fields.String(required=True, description='团队描述'),
    'team_type': fields.String(required=True, description='团队类型', enum=[t.name for t in TeamType]),
    'max_members': fields.Integer(required=True, description='最大成员数', default=5),
    'required_skills': fields.String(description='所需技能'),
    'status': fields.String(readonly=True, description='团队状态', enum=['recruiting', 'full', 'closed']),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'creator_id': fields.Integer(readonly=True, description='创建者ID'),
    'image_url': fields.String(description='团队图片URL')
})

member_model = ns.model('TeamMember', {
    'user_id': fields.Integer(readonly=True, description='用户ID'),
    'team_id': fields.Integer(readonly=True, description='团队ID'),
    'role': fields.String(description='角色', enum=['creator', 'member']),
    'join_time': fields.DateTime(readonly=True, description='加入时间'),
    'username': fields.String(readonly=True, description='用户名'),
    'avatar': fields.String(readonly=True, description='用户头像')
})

# 定义查询参数解析器
team_list_parser = reqparse.RequestParser()
team_list_parser.add_argument('type', type=str, help='团队类型')
team_list_parser.add_argument('status', type=str, choices=('recruiting', 'full', 'closed', 'all'), default='all', help='团队状态')
team_list_parser.add_argument('page', type=int, default=1, help='页码')
team_list_parser.add_argument('per_page', type=int, default=10, help='每页数量')

# API资源
@ns.route('/teams')
class TeamList(Resource):
    @ns.doc('获取团队列表')
    @ns.expect(team_list_parser)
    @ns.marshal_list_with(team_model)
    def get(self):
        """获取团队列表"""
        args = team_list_parser.parse_args()
        team_type = args.get('type', 'all')
        status = args.get('status', 'all')
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        
        query = Team.query
        
        # 按团队类型筛选
        if team_type != 'all' and team_type in [t.name for t in TeamType]:
            query = query.filter(Team.team_type == TeamType[team_type])
        
        # 按团队状态筛选
        if status != 'all':
            query = query.filter(Team.status == status)
        
        # 分页
        pagination = query.order_by(Team.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items
    
    @ns.doc('创建团队')
    @ns.expect(team_model)
    @ns.marshal_with(team_model, code=201)
    @ns.response(403, '没有权限')
    @ns.response(400, '无效请求')
    def post(self):
        """创建新团队"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/teams/<int:id>')
@ns.param('id', '团队ID')
@ns.response(404, '团队不存在')
class TeamDetail(Resource):
    @ns.doc('获取团队详情')
    @ns.marshal_with(team_model)
    def get(self, id):
        """获取团队详情"""
        team = Team.query.get_or_404(id)
        return team
    
    @ns.doc('更新团队')
    @ns.expect(team_model)
    @ns.marshal_with(team_model)
    @ns.response(403, '没有权限')
    def put(self, id):
        """更新团队信息"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501
    
    @ns.doc('关闭团队')
    @ns.response(204, '团队已关闭')
    @ns.response(403, '没有权限')
    def delete(self, id):
        """关闭团队"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/teams/<int:id>/members')
@ns.param('id', '团队ID')
class TeamMemberList(Resource):
    @ns.doc('获取团队成员')
    @ns.marshal_list_with(member_model)
    def get(self, id):
        """获取团队成员列表"""
        team = Team.query.get_or_404(id)
        members = []
        
        for user in team.members:
            # 查找团队成员关系信息
            member_info = db.session.query(team_members).filter_by(
                user_id=user.id, team_id=id
            ).first()
            
            if member_info:
                members.append({
                    'user_id': user.id,
                    'team_id': id,
                    'role': member_info.role,
                    'join_time': member_info.join_time,
                    'username': user.username,
                    'avatar': user.avatar
                })
                
        return members

@ns.route('/teams/<int:id>/join')
@ns.param('id', '团队ID')
class TeamJoin(Resource):
    @ns.doc('加入团队')
    @ns.response(200, '加入成功')
    @ns.response(403, '没有权限或团队已满')
    @ns.response(404, '团队不存在')
    def post(self, id):
        """加入团队"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/teams/<int:id>/leave')
@ns.param('id', '团队ID')
class TeamLeave(Resource):
    @ns.doc('离开团队')
    @ns.response(200, '离开成功')
    @ns.response(403, '没有权限或您是创建者')
    @ns.response(404, '团队不存在')
    def post(self, id):
        """离开团队"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

# 所有团队列表页面
@team_bp.route('/')
def index():
    team_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    
    query = Team.query
    
    # 按团队类型筛选
    if team_type != 'all' and team_type in [t.name for t in TeamType]:
        query = query.filter(Team.team_type == TeamType[team_type])
    
    # 按团队状态筛选
    if status != 'all':
        query = query.filter(Team.status == status)
    
    # 默认按创建时间降序排列
    teams = query.order_by(Team.created_at.desc()).all()
    
    return render_template('team/index.html',
                          title='组队中心',
                          teams=teams,
                          team_types=TeamType,
                          current_type=team_type,
                          current_status=status)

# 团队详情页
@team_bp.route('/<int:team_id>')
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    members = team.members.all()
    
    # 检查当前用户是否已是团队成员
    is_member = False
    is_creator = False
    if current_user.is_authenticated:
        for member in members:
            if member.id == current_user.id:
                is_member = True
                # 检查是否是创建者
                if team.creator_id == current_user.id:
                    is_creator = True
                break
    
    # 检查团队是否已满
    is_full = len(members) >= team.max_members
    
    # 获取团队创建者信息
    creator = User.query.get(team.creator_id)
    
    # 获取团队关联的项目
    projects = team.projects.all()
    
    return render_template('team/team_detail.html',
                          title=team.name,
                          team=team,
                          members=members,
                          creator=creator,
                          projects=projects,
                          is_member=is_member,
                          is_creator=is_creator,
                          is_full=is_full)

# 创建新团队
@team_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_team():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        team_type = request.form.get('team_type')
        max_members = int(request.form.get('max_members', 5))
        required_skills = request.form.get('required_skills', '')
        
        # 验证表单数据
        if not name or not description or not team_type:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('team.create_team'))
        
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
        
        # 处理上传的图片
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = f"team_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                image_path = os.path.join('static/img/teams', filename)
                image.save(image_path)
                team.image_url = image_path
        
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
        
        db.session.commit()
        
        flash('团队创建成功！', 'success')
        return redirect(url_for('team.team_detail', team_id=team.id))
    
    return render_template('team/create_team.html',
                          title='创建团队',
                          team_types=TeamType)

# 编辑团队
@team_bp.route('/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    # 检查权限，只有创建者可以编辑团队
    if team.creator_id != current_user.id:
        flash('您没有权限编辑此团队', 'danger')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    if request.method == 'POST':
        team.name = request.form.get('name')
        team.description = request.form.get('description')
        team.team_type = TeamType[request.form.get('team_type')]
        team.max_members = int(request.form.get('max_members', 5))
        team.required_skills = request.form.get('required_skills', '')
        team.status = request.form.get('status', 'recruiting')
        
        # 处理上传的新图片
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            filename = f"team_{team.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image_path = os.path.join('static/img/teams', filename)
            image.save(image_path)
            team.image_url = image_path
        
        db.session.commit()
        
        flash('团队信息已更新', 'success')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    return render_template('team/edit_team.html',
                          title='编辑团队',
                          team=team,
                          team_types=TeamType)

# 加入团队
@team_bp.route('/<int:team_id>/join', methods=['POST'])
@login_required
def join_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    # 检查团队是否招募中
    if team.status != 'recruiting':
        flash('该团队当前不接受新成员', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 检查用户是否已经是成员
    is_member = db.session.query(team_members).filter(
        team_members.c.user_id == current_user.id,
        team_members.c.team_id == team_id
    ).first() is not None
    
    if is_member:
        flash('您已经是该团队的成员', 'info')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 检查团队是否已满
    members_count = db.session.query(team_members).filter(
        team_members.c.team_id == team_id
    ).count()
    
    if members_count >= team.max_members:
        flash('该团队已满员', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 添加用户为团队成员
    stmt = team_members.insert().values(
        user_id=current_user.id,
        team_id=team_id,
        role='member',
        join_time=datetime.utcnow()
    )
    db.session.execute(stmt)
    
    # 如果团队满员，更新状态
    if members_count + 1 >= team.max_members:
        team.status = 'full'
    
    db.session.commit()
    
    flash('您已成功加入团队', 'success')
    return redirect(url_for('team.team_detail', team_id=team_id))

# 离开团队
@team_bp.route('/<int:team_id>/leave', methods=['POST'])
@login_required
def leave_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    # 创建者不能离开团队
    if team.creator_id == current_user.id:
        flash('作为创建者，您不能离开团队。如需解散团队，请使用关闭团队功能。', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 检查用户是否是成员
    is_member = db.session.query(team_members).filter(
        team_members.c.user_id == current_user.id,
        team_members.c.team_id == team_id
    ).first() is not None
    
    if not is_member:
        flash('您不是该团队的成员', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 从团队中移除用户
    stmt = team_members.delete().where(
        team_members.c.user_id == current_user.id,
        team_members.c.team_id == team_id
    )
    db.session.execute(stmt)
    
    # 如果团队之前是满员状态，现在有空位，更新状态
    if team.status == 'full':
        team.status = 'recruiting'
    
    db.session.commit()
    
    flash('您已离开团队', 'success')
    return redirect(url_for('team.team_detail', team_id=team_id))

# 关闭/解散团队
@team_bp.route('/<int:team_id>/close', methods=['POST'])
@login_required
def close_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    # 检查权限，只有创建者可以关闭团队
    if team.creator_id != current_user.id:
        flash('您没有权限关闭此团队', 'danger')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 更新团队状态为关闭
    team.status = 'closed'
    db.session.commit()
    
    flash('团队已关闭', 'success')
    return redirect(url_for('team.team_detail', team_id=team_id))

# 移除团队成员（仅创建者可操作）
@team_bp.route('/<int:team_id>/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_member(team_id, user_id):
    team = Team.query.get_or_404(team_id)
    
    # 检查权限，只有创建者可以移除成员
    if team.creator_id != current_user.id:
        flash('您没有权限从此团队中移除成员', 'danger')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 创建者不能被移除
    if user_id == team.creator_id:
        flash('创建者不能被移除', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 检查用户是否存在且是否是团队成员
    user = User.query.get_or_404(user_id)
    is_member = db.session.query(team_members).filter(
        team_members.c.user_id == user_id,
        team_members.c.team_id == team_id
    ).first() is not None
    
    if not is_member:
        flash('该用户不是团队成员', 'warning')
        return redirect(url_for('team.team_detail', team_id=team_id))
    
    # 从团队中移除用户
    stmt = team_members.delete().where(
        team_members.c.user_id == user_id,
        team_members.c.team_id == team_id
    )
    db.session.execute(stmt)
    
    # 如果团队之前是满员状态，现在有空位，更新状态
    if team.status == 'full':
        team.status = 'recruiting'
    
    db.session.commit()
    
    flash(f'成员 {user.username} 已从团队中移除', 'success')
    return redirect(url_for('team.team_detail', team_id=team_id))

# 搜索团队API
@team_bp.route('/search')
def search_teams():
    keyword = request.args.get('q', '')
    team_type = request.args.get('type', 'all')
    
    if not keyword:
        return jsonify([])
    
    # 构建搜索查询
    query = Team.query.filter(
        (Team.name.contains(keyword) | Team.description.contains(keyword)) &
        (Team.status != 'closed')
    )
    
    # 按团队类型筛选
    if team_type != 'all' and team_type in [t.name for t in TeamType]:
        query = query.filter(Team.team_type == TeamType[team_type])
    
    teams = query.limit(10).all()
    
    # 格式化结果
    results = []
    for team in teams:
        results.append({
            'id': team.id,
            'name': team.name,
            'description': team.description[:100] + '...' if len(team.description) > 100 else team.description,
            'team_type': team.team_type.value,
            'image_url': team.image_url,
            'member_count': team.members.count(),
            'max_members': team.max_members,
            'status': team.status
        })
    
    return jsonify(results) 