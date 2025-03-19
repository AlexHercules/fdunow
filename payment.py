from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource, fields, reqparse
from models import db, Donation, Project, User
from datetime import datetime
import random
import string

# 创建蓝图
payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# 创建API命名空间
ns = Namespace('支付', description='支付与捐赠模块API接口')

# 定义API模型
donation_model = ns.model('Donation', {
    'id': fields.Integer(readonly=True, description='捐赠ID'),
    'amount': fields.Float(required=True, description='捐赠金额'),
    'message': fields.String(description='留言'),
    'is_anonymous': fields.Boolean(description='是否匿名', default=False),
    'created_at': fields.DateTime(readonly=True, description='捐赠时间'),
    'donor_id': fields.Integer(readonly=True, description='捐赠者ID'),
    'project_id': fields.Integer(required=True, description='项目ID')
})

payment_model = ns.model('Payment', {
    'id': fields.String(readonly=True, description='支付ID'),
    'amount': fields.Float(required=True, description='支付金额'),
    'status': fields.String(readonly=True, description='支付状态', enum=['pending', 'success', 'failed']),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'completed_at': fields.DateTime(readonly=True, description='完成时间'),
    'donation_id': fields.Integer(readonly=True, description='关联的捐赠ID')
})

# 查询参数解析器
donation_list_parser = reqparse.RequestParser()
donation_list_parser.add_argument('project_id', type=int, help='项目ID')
donation_list_parser.add_argument('user_id', type=int, help='用户ID')
donation_list_parser.add_argument('page', type=int, default=1, help='页码')
donation_list_parser.add_argument('per_page', type=int, default=10, help='每页数量')

# API资源
@ns.route('/donations')
class DonationList(Resource):
    @ns.doc('获取捐赠列表')
    @ns.expect(donation_list_parser)
    @ns.marshal_list_with(donation_model)
    def get(self):
        """获取捐赠列表"""
        args = donation_list_parser.parse_args()
        project_id = args.get('project_id')
        user_id = args.get('user_id')
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        
        query = Donation.query
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        if user_id:
            query = query.filter_by(donor_id=user_id)
        
        # 分页
        pagination = query.order_by(Donation.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items
    
    @ns.doc('创建捐赠')
    @ns.expect(donation_model)
    @ns.marshal_with(donation_model, code=201)
    @ns.response(401, '未登录')
    @ns.response(400, '无效请求')
    def post(self):
        """创建新捐赠"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/donations/<int:id>')
@ns.param('id', '捐赠ID')
@ns.response(404, '捐赠不存在')
class DonationDetail(Resource):
    @ns.doc('获取捐赠详情')
    @ns.marshal_with(donation_model)
    def get(self, id):
        """获取捐赠详情"""
        donation = Donation.query.get_or_404(id)
        return donation

@ns.route('/pay')
class PaymentCreate(Resource):
    @ns.doc('创建支付')
    @ns.expect(ns.model('NewPayment', {
        'donation_id': fields.Integer(required=True, description='捐赠ID'),
        'payment_method': fields.String(required=True, description='支付方式', enum=['alipay', 'wechat', 'creditcard'])
    }))
    @ns.marshal_with(payment_model, code=201)
    @ns.response(401, '未登录')
    @ns.response(400, '无效请求')
    def post(self):
        """创建支付请求"""
        # 这里仅是API文档演示，实际需要验证用户权限
        return {'message': '功能未实现'}, 501

@ns.route('/pay/callback')
class PaymentCallback(Resource):
    @ns.doc('支付回调')
    @ns.response(200, '处理成功')
    def post(self):
        """支付结果回调处理"""
        # 这里仅是API文档演示
        return {'message': '功能未实现'}, 501

@ns.route('/pay/<string:payment_id>/status')
@ns.param('payment_id', '支付ID')
class PaymentStatus(Resource):
    @ns.doc('查询支付状态')
    @ns.marshal_with(payment_model)
    @ns.response(404, '支付不存在')
    def get(self, payment_id):
        """查询支付状态"""
        # 这里仅是API文档演示
        return {'message': '功能未实现'}, 501

# 模拟支付处理
@payment_bp.route('/process', methods=['POST'])
@login_required
def process_payment():
    amount = float(request.form.get('amount', 0))
    project_id = request.form.get('project_id')
    message = request.form.get('message', '')
    is_anonymous = 'is_anonymous' in request.form
    
    if amount <= 0:
        flash('支付金额必须大于0', 'danger')
        return redirect(url_for('crowdfunding.donate', project_id=project_id))
    
    # 检查项目是否存在
    project = Project.query.get_or_404(project_id)
    
    # 生成唯一的支付ID，实际环境中可能来自第三方支付平台
    payment_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    # 创建支付处理页面的上下文
    context = {
        'amount': amount,
        'project': project,
        'payment_id': payment_id,
        'message': message,
        'is_anonymous': is_anonymous
    }
    
    return render_template('payment/process.html', **context)

# 模拟支付完成回调
@payment_bp.route('/complete', methods=['POST'])
@login_required
def complete_payment():
    payment_id = request.form.get('payment_id')
    project_id = request.form.get('project_id')
    amount = float(request.form.get('amount', 0))
    message = request.form.get('message', '')
    is_anonymous = request.form.get('is_anonymous') == 'True'
    
    # 检查项目是否存在
    project = Project.query.get_or_404(project_id)
    
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
    
    flash('支付成功！感谢您的支持！', 'success')
    return redirect(url_for('crowdfunding.project_detail', project_id=project_id))

# 查看捐赠记录
@payment_bp.route('/donations')
@login_required
def my_donations():
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    
    return render_template('payment/donations.html',
                          title='我的捐赠记录',
                          donations=donations)

# 查看项目的捐赠记录（项目创建者可查看）
@payment_bp.route('/project/<int:project_id>/donations')
@login_required
def project_donations(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查权限，只有项目创建者可以查看
    if project.creator_id != current_user.id:
        flash('您没有权限查看此项目的捐赠记录', 'danger')
        return redirect(url_for('crowdfunding.project_detail', project_id=project_id))
    
    donations = Donation.query.filter_by(project_id=project_id).order_by(Donation.created_at.desc()).all()
    
    return render_template('payment/project_donations.html',
                          title=f'{project.title}的捐赠记录',
                          project=project,
                          donations=donations)

# 支付API状态查询（模拟第三方支付平台的API）
@payment_bp.route('/api/status/<payment_id>')
def payment_status(payment_id):
    # 这里模拟支付状态查询，实际环境中会调用第三方支付平台的API
    # 随机返回支付状态，在真实环境中不应该这样做
    statuses = ['processing', 'success', 'failed']
    weights = [0.1, 0.8, 0.1]  # 80%概率成功，10%概率处理中，10%概率失败
    
    status = random.choices(statuses, weights=weights, k=1)[0]
    
    return jsonify({
        'payment_id': payment_id,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }) 