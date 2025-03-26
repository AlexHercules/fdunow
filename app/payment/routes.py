from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.auth.decorators import admin_required, project_creator_required
from app.payment.models import Transaction, TransactionType, ServiceFee, Invoice, Refund, PaymentMethod
from app.payment.services import PaymentService, FinancialReportService
from app.models import CrowdfundingProject, User
from app.utils import pagination_dict
from app.models.payment import Payment, PaymentReward, ProjectReward
from app.models.project import Project
from app.payment.exceptions import (
    PaymentError, PaymentValidationError, PaymentAmountError,
    PaymentMethodError, PaymentTimeoutError, PaymentSignatureError,
    PaymentCallbackError, PaymentStatusError, PaymentRefundError
)
import logging

# 修改蓝图名称为payment_bp
payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

# 支付系统首页路由
@payment_bp.route('/')
@login_required
def index():
    """支付中心首页"""
    try:
        # 获取用户支付统计
        total_payments = Payment.query.filter_by(user_id=current_user.id).count()
        pending_payments = Payment.query.filter_by(
            user_id=current_user.id, status='pending'
        ).count()
        completed_payments = Payment.query.filter_by(
            user_id=current_user.id, status='completed'
        ).count()
        
        # 获取最近的支付记录
        recent_payments = Payment.query.filter_by(
            user_id=current_user.id
        ).order_by(Payment.created_at.desc()).limit(5).all()
        
        return render_template('payment/index.html',
                             total_payments=total_payments,
                             pending_payments=pending_payments,
                             completed_payments=completed_payments,
                             recent_payments=recent_payments)
    except Exception as e:
        logger.error(f"访问支付中心首页失败: {str(e)}")
        flash('访问支付中心失败，请稍后重试', 'error')
        return redirect(url_for('main.index'))

# 我的捐款页面
@payment_bp.route('/my_donations')
@login_required
def my_donations():
    """我的捐款页面"""
    return render_template('payment/my_donations.html')

# 处理支付页面
@payment_bp.route('/process_payment/<int:project_id>', methods=['GET', 'POST'])
@login_required
def process_payment_page(project_id):
    """处理支付页面"""
    project = CrowdfundingProject.query.get_or_404(project_id)
    return render_template('payment/payment_form.html', project=project)

# 支付帮助页面
@payment_bp.route('/help')
def help_page():
    """支付帮助页面"""
    return render_template('payment/help.html')

# 捐款相关接口
@payment_bp.route('/api/donations', methods=['POST'])
@login_required
def create_donation():
    """创建新的捐款交易"""
    data = request.get_json()
    
    # 验证输入
    if not all(k in data for k in ['project_id', 'amount', 'payment_method']):
        return jsonify({"error": "缺少必要字段"}), 400
    
    # 验证项目状态
    project = CrowdfundingProject.query.get_or_404(data['project_id'])
    if project.status != 'fundraising':
        return jsonify({"error": "项目不在筹款阶段"}), 400
    
    try:
        # 创建捐款交易
        transaction = PaymentService.create_donation(
            user_id=current_user.id,
            project_id=data['project_id'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            description=data.get('description')
        )
        
        return jsonify({
            "message": "捐款创建成功，请完成支付",
            "transaction": transaction.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"创建捐款失败: {str(e)}")
        return jsonify({"error": "服务器错误"}), 500

@payment_bp.route('/api/donations/<int:transaction_id>/pay', methods=['POST'])
@login_required
def process_payment(transaction_id):
    """处理支付"""
    data = request.get_json() or {}
    
    # 验证交易归属
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        return jsonify({"error": "无权限操作此交易"}), 403
    
    try:
        # 处理支付
        success = PaymentService.process_payment(transaction_id, data)
        
        if success:
            return jsonify({
                "message": "支付成功",
                "transaction": transaction.to_dict()
            })
        else:
            return jsonify({
                "message": "支付失败",
                "transaction": transaction.to_dict()
            }), 400
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"处理支付失败: {str(e)}")
        return jsonify({"error": "服务器错误"}), 500

@payment_bp.route('/api/users/<int:user_id>/donations', methods=['GET'])
@login_required
def get_user_donations(user_id):
    """获取用户的捐款记录"""
    # 只能查看自己的捐款记录或管理员可查看任意用户
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # 构建查询
    query = Transaction.query.filter_by(
        user_id=user_id,
        transaction_type=TransactionType.DONATION.value
    )
    
    # 按项目过滤
    project_id = request.args.get('project_id', type=int)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    # 按状态过滤
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    # 按时间范围过滤
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Transaction.created_at.between(start_date, end_date))
        except ValueError:
            return jsonify({"error": "日期格式无效"}), 400
    
    # 执行分页查询
    pagination = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # 准备响应数据
    donations = [t.to_dict() for t in pagination.items]
    
    # 添加项目信息
    for donation in donations:
        project = CrowdfundingProject.query.get(donation['project_id'])
        if project:
            donation['project'] = {
                'id': project.id,
                'title': project.title,
                'image_url': project.image_url
            }
    
    return jsonify({
        "donations": donations,
        "pagination": pagination_dict(pagination)
    })

@payment_bp.route('/api/projects/<int:project_id>/donations', methods=['GET'])
def get_project_donations(project_id):
    """获取项目的捐款记录"""
    # 验证项目
    project = CrowdfundingProject.query.get_or_404(project_id)
    
    # 非公开项目需要身份验证
    if not project.is_public and (not current_user.is_authenticated or 
                                 (current_user.id != project.creator_id and not current_user.is_admin)):
        return jsonify({"error": "无权限查看"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # 构建查询
    query = Transaction.query.filter_by(
        project_id=project_id,
        transaction_type=TransactionType.DONATION.value,
        status='completed'  # 只显示完成的捐款
    )
    
    # 执行分页查询
    pagination = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # 准备响应数据
    donations = []
    for transaction in pagination.items:
        donation_dict = {
            'id': transaction.id,
            'amount': float(transaction.amount),
            'created_at': transaction.created_at.isoformat(),
            'user': None  # 默认匿名
        }
        
        # 如果用户允许显示个人信息
        user = User.query.get(transaction.user_id)
        if user and (user.is_public or current_user.is_authenticated and 
                     (current_user.id == user.id or current_user.id == project.creator_id or current_user.is_admin)):
            donation_dict['user'] = {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar
            }
        
        donations.append(donation_dict)
    
    return jsonify({
        "donations": donations,
        "pagination": pagination_dict(pagination)
    })

# 退款相关接口
@payment_bp.route('/api/refunds', methods=['POST'])
@login_required
def request_refund():
    """申请退款"""
    data = request.get_json()
    
    # 验证输入
    if not all(k in data for k in ['transaction_id', 'reason']):
        return jsonify({"error": "缺少必要字段"}), 400
    
    try:
        # 创建退款申请
        refund = PaymentService.request_refund(
            transaction_id=data['transaction_id'],
            user_id=current_user.id,
            reason=data['reason'],
            evidence_urls=data.get('evidence_urls')
        )
        
        return jsonify({
            "message": "退款申请已提交",
            "refund": refund.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"申请退款失败: {str(e)}")
        return jsonify({"error": "服务器错误"}), 500

@payment_bp.route('/api/refunds/<int:refund_id>', methods=['GET'])
@login_required
def get_refund(refund_id):
    """获取退款申请详细信息"""
    refund = Refund.query.get_or_404(refund_id)
    
    # 验证权限
    if current_user.id != refund.requester_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    return jsonify(refund.to_dict())

@payment_bp.route('/api/refunds/<int:refund_id>/process', methods=['PUT'])
@admin_required
def process_refund(refund_id):
    """处理退款申请"""
    data = request.get_json()
    
    # 验证输入
    if 'approve' not in data:
        return jsonify({"error": "缺少必要字段"}), 400
    
    try:
        # 处理退款申请
        success = PaymentService.process_refund(
            refund_id=refund_id,
            approver_id=current_user.id,
            approve=data['approve'],
            admin_notes=data.get('admin_notes')
        )
        
        if success:
            refund = Refund.query.get(refund_id)
            return jsonify({
                "message": "退款申请已处理",
                "refund": refund.to_dict()
            })
        else:
            return jsonify({"error": "处理失败，退款申请状态可能已变更"}), 400
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"处理退款失败: {str(e)}")
        return jsonify({"error": "服务器错误"}), 500

@payment_bp.route('/api/users/<int:user_id>/refunds', methods=['GET'])
@login_required
def get_user_refunds(user_id):
    """获取用户的退款申请记录"""
    # 只能查看自己的退款记录或管理员可查看任意用户
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # 构建查询
    query = Refund.query.filter_by(requester_id=user_id)
    
    # 按状态过滤
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    # 执行分页查询
    pagination = query.order_by(Refund.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # 准备响应数据
    refunds = [r.to_dict() for r in pagination.items]
    
    # 添加交易和项目信息
    for refund in refunds:
        transaction = Transaction.query.get(refund['transaction_id'])
        if transaction:
            refund['transaction'] = {
                'id': transaction.id,
                'amount': float(transaction.amount),
                'created_at': transaction.created_at.isoformat()
            }
            
            project = CrowdfundingProject.query.get(transaction.project_id)
            if project:
                refund['project'] = {
                    'id': project.id,
                    'title': project.title,
                    'image_url': project.image_url
                }
    
    return jsonify({
        "refunds": refunds,
        "pagination": pagination_dict(pagination)
    })

# 项目账单相关接口
@payment_bp.route('/api/projects/<int:project_id>/invoices', methods=['GET'])
@login_required
def get_project_invoices(project_id):
    """获取项目账单"""
    # 验证项目
    project = CrowdfundingProject.query.get_or_404(project_id)
    
    # 验证权限
    if current_user.id != project.creator_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    # 获取项目账单
    invoices = Invoice.query.filter_by(project_id=project_id).order_by(Invoice.created_at.desc()).all()
    
    return jsonify({
        "invoices": [i.to_dict() for i in invoices]
    })

@payment_bp.route('/api/invoices/<int:invoice_id>', methods=['GET'])
@login_required
def get_invoice(invoice_id):
    """获取账单详情"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # 验证权限
    if current_user.id != invoice.creator_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    return jsonify(invoice.to_dict())

# 财务报表接口
@payment_bp.route('/api/projects/<int:project_id>/financial-summary', methods=['GET'])
@login_required
def get_project_financial_summary(project_id):
    """获取项目财务摘要"""
    # 验证项目
    project = CrowdfundingProject.query.get_or_404(project_id)
    
    # 验证权限
    if current_user.id != project.creator_id and not current_user.is_admin:
        return jsonify({"error": "无权限查看"}), 403
    
    # 获取财务摘要
    summary = FinancialReportService.get_project_financial_summary(project_id)
    
    return jsonify(summary)

@payment_bp.route('/api/financial-summary', methods=['GET'])
@admin_required
def get_platform_financial_summary():
    """获取平台财务摘要"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 尝试转换日期
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "开始日期格式无效"}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "结束日期格式无效"}), 400
    
    # 获取平台财务摘要
    summary = FinancialReportService.get_platform_financial_summary(start_date, end_date)
    
    return jsonify(summary)

@payment_bp.route('/api/transactions/report', methods=['GET'])
@admin_required
def get_transaction_report():
    """获取交易报表"""
    # 解析过滤条件
    filters = {}
    
    # 日期范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date:
        try:
            filters['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')
            filters['end_date'] = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "日期格式无效"}), 400
    
    # 交易类型
    transaction_type = request.args.get('transaction_type')
    if transaction_type:
        filters['transaction_type'] = transaction_type
    
    # 交易状态
    status = request.args.get('status')
    if status:
        filters['status'] = status
    
    # 项目ID
    project_id = request.args.get('project_id', type=int)
    if project_id:
        filters['project_id'] = project_id
    
    # 用户ID
    user_id = request.args.get('user_id', type=int)
    if user_id:
        filters['user_id'] = user_id
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # 获取交易报表
    report = FinancialReportService.get_transaction_report(filters, page, per_page)
    
    return jsonify(report)

@payment_bp.route('/api/payment-methods/report', methods=['GET'])
@admin_required
def get_payment_methods_report():
    """获取支付方式使用统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 尝试转换日期
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "开始日期格式无效"}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "结束日期格式无效"}), 400
    
    # 获取支付方式使用统计
    report = FinancialReportService.get_payment_methods_report(start_date, end_date)
    
    return jsonify({
        "payment_methods": report
    })

@payment_bp.route('/checkout/<int:project_id>', methods=['GET', 'POST'])
@login_required
def checkout(project_id):
    """支付结算页面"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            # 验证支付金额
            amount = float(request.form.get('amount', 0))
            if amount <= 0:
                raise PaymentAmountError('支付金额必须大于0')
            
            # 验证支付方式
            payment_method = request.form.get('payment_method')
            if payment_method not in ['wechat', 'alipay', 'campus_card']:
                raise PaymentMethodError('不支持的支付方式')
            
            # 创建支付记录
            payment = Payment(
                user_id=current_user.id,
                project_id=project_id,
                amount=amount,
                payment_method=payment_method,
                message=request.form.get('message'),
                anonymous=bool(request.form.get('anonymous'))
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # 根据支付方式跳转到不同的支付页面
            if payment_method == 'wechat':
                return redirect(url_for('payment.wechat_pay', payment_id=payment.id))
            elif payment_method == 'alipay':
                return redirect(url_for('payment.alipay_pay', payment_id=payment.id))
            else:
                return redirect(url_for('payment.campus_card_pay', payment_id=payment.id))
        
        return render_template('payment/checkout.html', project=project)
    except PaymentValidationError as e:
        flash(str(e), 'error')
        return redirect(url_for('payment.checkout', project_id=project_id))
    except Exception as e:
        logger.error(f"支付结算失败: {str(e)}")
        flash('支付结算失败，请稍后重试', 'error')
        return redirect(url_for('main.index'))

@payment_bp.route('/confirm/<int:payment_id>')
@login_required
def confirm(payment_id):
    """支付确认页面"""
    payment = Payment.query.get_or_404(payment_id)
    
    # 检查支付是否属于当前用户
    if payment.user_id != current_user.id:
        flash('您无权访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    project = Project.query.get(payment.project_id)
    payment_reward = PaymentReward.query.filter_by(payment_id=payment.id).first()
    reward = None
    if payment_reward:
        reward = ProjectReward.query.get(payment_reward.reward_id)
    
    return render_template('payment/confirm.html',
                          title='支付确认',
                          payment=payment,
                          project=project,
                          reward=reward)

@payment_bp.route('/callback/<payment_method>', methods=['POST'])
def payment_callback(payment_method):
    """支付回调接口"""
    try:
        # 获取回调数据
        data = request.get_json()
        if not data:
            raise PaymentCallbackError('无效的回调数据')
            
        # 验证签名
        if not verify_payment_signature(data):
            raise PaymentSignatureError('签名验证失败')
            
        # 获取必要参数
        payment_id = data.get('payment_id')
        status = data.get('status')
        transaction_id = data.get('transaction_id')
        amount = float(data.get('amount', 0))
        
        if not all([payment_id, status, transaction_id, amount]):
            raise PaymentCallbackError('缺少必要参数')
            
        # 查询支付记录
        payment = Payment.query.get(payment_id)
        if not payment:
            raise PaymentCallbackError('支付记录不存在')
            
        # 验证金额
        if payment.amount != amount:
            raise PaymentAmountError('支付金额不匹配')
            
        # 更新支付状态
        if status == 'success':
            payment.status = 'completed'
            payment.transaction_id = transaction_id
            payment.completed_at = datetime.utcnow()
            
            # 更新项目筹款金额
            project = payment.project
            project.current_amount += amount
            
            # 检查是否达到目标金额
            if project.current_amount >= project.target_amount:
                project.status = 'completed'
                
            db.session.commit()
            return jsonify({'code': 0, 'message': 'success'})
        else:
            payment.status = 'failed'
            payment.failed_reason = data.get('reason', '支付失败')
            db.session.commit()
            return jsonify({'code': 1, 'message': '支付失败'})
            
    except PaymentError as e:
        logger.error(f"支付回调处理失败: {str(e)}")
        return jsonify({'code': 1, 'message': str(e)})
    except Exception as e:
        logger.error(f"支付回调处理异常: {str(e)}")
        db.session.rollback()
        return jsonify({'code': 1, 'message': '系统错误'})

def verify_payment_signature(data):
    """验证支付签名"""
    try:
        # 获取签名
        signature = data.pop('signature', None)
        if not signature:
            return False
            
        # 按字母顺序排序参数
        sorted_params = sorted(data.items())
        
        # 拼接参数
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 添加密钥
        sign_str += f"&key={current_app.config['PAYMENT_SECRET_KEY']}"
        
        # 计算MD5
        import hashlib
        calculated_signature = hashlib.md5(sign_str.encode()).hexdigest().upper()
        
        # 验证签名
        return calculated_signature == signature
    except Exception as e:
        logger.error(f"签名验证失败: {str(e)}")
        return False

@payment_bp.route('/my_payments')
@login_required
def my_payments():
    """我的支付记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Payment.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
            
        pagination = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('payment/my_payments.html',
                             pagination=pagination,
                             status=status,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        logger.error(f"获取支付记录失败: {str(e)}")
        flash('获取支付记录失败，请稍后重试', 'error')
        return redirect(url_for('payment.index'))

@payment_bp.route('/api/payments')
@login_required
def get_payments():
    """获取支付记录API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Payment.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
            
        pagination = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'pagination': pagination_dict(pagination),
                'payments': [{
                    'id': payment.id,
                    'project_title': payment.project.title,
                    'amount': payment.amount,
                    'payment_method': payment.payment_method,
                    'status': payment.status,
                    'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                } for payment in pagination.items]
            }
        })
    except Exception as e:
        logger.error(f"获取支付记录API失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取支付记录失败',
            'data': None
        })

@payment_bp.route('/statistics')
@login_required
def payment_statistics():
    """支付统计页面"""
    try:
        # 获取时间范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = Payment.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
            
        # 获取支付总额
        total_amount = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).scalar() or 0
        
        # 获取支付方式统计
        payment_methods = db.session.query(
            Payment.payment_method,
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).group_by(Payment.payment_method).all()
        
        # 获取支付状态统计
        payment_status = db.session.query(
            Payment.status,
            db.func.count(Payment.id).label('count')
        ).filter(
            Payment.user_id == current_user.id
        ).group_by(Payment.status).all()
        
        # 获取每日支付统计
        daily_payments = db.session.query(
            db.func.date(Payment.created_at).label('date'),
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).group_by(
            db.func.date(Payment.created_at)
        ).order_by(
            db.func.date(Payment.created_at).desc()
        ).limit(30).all()
        
        return render_template('payment/statistics.html',
                             total_amount=total_amount,
                             payment_methods=payment_methods,
                             payment_status=payment_status,
                             daily_payments=daily_payments,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        logger.error(f"获取支付统计失败: {str(e)}")
        flash('获取支付统计失败，请稍后重试', 'error')
        return redirect(url_for('payment.index'))

@payment_bp.route('/api/statistics')
@login_required
def get_payment_statistics():
    """获取支付统计API"""
    try:
        # 获取时间范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = Payment.query.filter_by(user_id=current_user.id)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
            
        # 获取支付总额
        total_amount = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).scalar() or 0
        
        # 获取支付方式统计
        payment_methods = db.session.query(
            Payment.payment_method,
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).group_by(Payment.payment_method).all()
        
        # 获取支付状态统计
        payment_status = db.session.query(
            Payment.status,
            db.func.count(Payment.id).label('count')
        ).filter(
            Payment.user_id == current_user.id
        ).group_by(Payment.status).all()
        
        # 获取每日支付统计
        daily_payments = db.session.query(
            db.func.date(Payment.created_at).label('date'),
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed'
        ).group_by(
            db.func.date(Payment.created_at)
        ).order_by(
            db.func.date(Payment.created_at).desc()
        ).limit(30).all()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'total_amount': float(total_amount),
                'payment_methods': [{
                    'method': method,
                    'count': count,
                    'amount': float(amount)
                } for method, count, amount in payment_methods],
                'payment_status': [{
                    'status': status,
                    'count': count
                } for status, count in payment_status],
                'daily_payments': [{
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count,
                    'amount': float(amount)
                } for date, count, amount in daily_payments]
            }
        })
    except Exception as e:
        logger.error(f"获取支付统计API失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取支付统计失败',
            'data': None
        })

@payment_bp.route('/refund/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def refund(payment_id):
    """退款申请页面"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # 检查权限
        if payment.user_id != current_user.id and not current_user.is_admin:
            flash('您无权申请退款', 'error')
            return redirect(url_for('payment.index'))
            
        # 检查支付状态
        if payment.status != 'completed':
            flash('只有已完成的支付才能申请退款', 'error')
            return redirect(url_for('payment.index'))
            
        if request.method == 'POST':
            # 验证退款原因
            reason = request.form.get('reason')
            if not reason:
                raise PaymentValidationError('请填写退款原因')
                
            # 创建退款记录
            refund = Refund(
                payment_id=payment_id,
                user_id=current_user.id,
                amount=payment.amount,
                reason=reason,
                status='pending'
            )
            
            db.session.add(refund)
            db.session.commit()
            
            # 发送邮件通知
            try:
                send_email(
                    subject='退款申请已提交',
                    recipients=[current_user.email],
                    template='email/refund_requested',
                    refund=refund
                )
            except Exception as e:
                logger.error(f"发送退款申请邮件失败: {str(e)}")
                
            flash('退款申请已提交,请等待审核', 'success')
            return redirect(url_for('payment.index'))
            
        return render_template('payment/refund.html', payment=payment)
        
    except PaymentValidationError as e:
        flash(str(e), 'error')
        return redirect(url_for('payment.refund', payment_id=payment_id))
    except Exception as e:
        logger.error(f"退款申请失败: {str(e)}")
        flash('退款申请失败,请稍后重试', 'error')
        return redirect(url_for('payment.index'))

@payment_bp.route('/admin/refunds')
@admin_required
def admin_refunds():
    """管理员退款审核页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Refund.query
        
        if status:
            query = query.filter_by(status=status)
            
        pagination = query.order_by(Refund.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('payment/admin/refunds.html',
                             pagination=pagination,
                             status=status)
                             
    except Exception as e:
        logger.error(f"获取退款申请列表失败: {str(e)}")
        flash('获取退款申请列表失败,请稍后重试', 'error')
        return redirect(url_for('admin.index'))

@payment_bp.route('/admin/refunds/<int:refund_id>/process', methods=['POST'])
@admin_required
def process_refund(refund_id):
    """处理退款申请"""
    try:
        refund = Refund.query.get_or_404(refund_id)
        
        # 检查退款状态
        if refund.status != 'pending':
            raise PaymentStatusError('退款申请状态已变更')
            
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes')
        
        if action == 'approve':
            # 更新退款状态
            refund.status = 'approved'
            refund.approved_at = datetime.utcnow()
            refund.approved_by = current_user.id
            refund.admin_notes = admin_notes
            
            # 更新支付状态
            payment = refund.payment
            payment.status = 'refunded'
            payment.refunded_at = datetime.utcnow()
            
            # 更新项目筹款金额
            project = payment.project
            project.current_amount -= payment.amount
            
            db.session.commit()
            
            # 发送邮件通知
            try:
                send_email(
                    subject='退款申请已通过',
                    recipients=[refund.user.email],
                    template='email/refund_approved',
                    refund=refund
                )
            except Exception as e:
                logger.error(f"发送退款通过邮件失败: {str(e)}")
                
            flash('退款申请已通过', 'success')
            
        elif action == 'reject':
            # 更新退款状态
            refund.status = 'rejected'
            refund.rejected_at = datetime.utcnow()
            refund.rejected_by = current_user.id
            refund.admin_notes = admin_notes
            
            db.session.commit()
            
            # 发送邮件通知
            try:
                send_email(
                    subject='退款申请已拒绝',
                    recipients=[refund.user.email],
                    template='email/refund_rejected',
                    refund=refund
                )
            except Exception as e:
                logger.error(f"发送退款拒绝邮件失败: {str(e)}")
                
            flash('退款申请已拒绝', 'success')
            
        else:
            raise PaymentValidationError('无效的操作')
            
        return redirect(url_for('payment.admin_refunds'))
        
    except PaymentError as e:
        flash(str(e), 'error')
        return redirect(url_for('payment.admin_refunds'))
    except Exception as e:
        logger.error(f"处理退款申请失败: {str(e)}")
        flash('处理退款申请失败,请稍后重试', 'error')
        return redirect(url_for('payment.admin_refunds')) 