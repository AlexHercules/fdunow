from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.auth.decorators import admin_required, project_creator_required
from app.payment.models import Transaction, TransactionType, ServiceFee, Invoice, Refund, PaymentMethod
from app.payment.services import PaymentService, FinancialReportService
from app.models import CrowdfundingProject, User
from app.utils import pagination_dict

# 修改蓝图名称为payment_bp
payment_bp = Blueprint('payment', __name__)

# 支付系统首页路由
@payment_bp.route('/')
def index():
    """支付系统首页"""
    flash('支付功能已经准备就绪，您可以开始使用！', 'success')
    return render_template('payment/index.html')

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
    
    # 验证项目状�?
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
        return jsonify({"error": "服务器错�?}), 500

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
        return jsonify({"error": "服务器错�?}), 500

@payment_bp.route('/api/users/<int:user_id>/donations', methods=['GET'])
@login_required
def get_user_donations(user_id):
    """获取用户的捐款记�?""
    # 只能查看自己的捐款记录或管理员可查看任意用户
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({"error": "无权限查�?}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # 构建查询
    query = Transaction.query.filter_by(
        user_id=user_id,
        transaction_type=TransactionType.DONATION.value
    )
    
    # 按项目过�?
    project_id = request.args.get('project_id', type=int)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    # 按状态过�?
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    # 按时间范围过�?
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
    """获取项目的捐款记�?""
    # 验证项目
    project = CrowdfundingProject.query.get_or_404(project_id)
    
    # 非公开项目需要身份验�?
    if not project.is_public and (not current_user.is_authenticated or 
                                 (current_user.id != project.creator_id and not current_user.is_admin)):
        return jsonify({"error": "无权限查�?}), 403
    
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

# 退款相关接�?
@payment_bp.route('/api/refunds', methods=['POST'])
@login_required
def request_refund():
    """申请退�?""
    data = request.get_json()
    
    # 验证输入
    if not all(k in data for k in ['transaction_id', 'reason']):
        return jsonify({"error": "缺少必要字段"}), 400
    
    try:
        # 创建退款申�?
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
        current_app.logger.error(f"申请退款失�? {str(e)}")
        return jsonify({"error": "服务器错�?}), 500

@payment_bp.route('/api/refunds/<int:refund_id>', methods=['GET'])
@login_required
def get_refund(refund_id):
    """获取退款申请详�?""
    refund = Refund.query.get_or_404(refund_id)
    
    # 验证权限
    if current_user.id != refund.requester_id and not current_user.is_admin:
        return jsonify({"error": "无权限查�?}), 403
    
    return jsonify(refund.to_dict())

@payment_bp.route('/api/refunds/<int:refund_id>/process', methods=['PUT'])
@admin_required
def process_refund(refund_id):
    """处理退款申�?""
    data = request.get_json()
    
    # 验证输入
    if 'approve' not in data:
        return jsonify({"error": "缺少必要字段"}), 400
    
    try:
        # 处理退款申�?
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
        current_app.logger.error(f"处理退款失�? {str(e)}")
        return jsonify({"error": "服务器错�?}), 500

@payment_bp.route('/api/users/<int:user_id>/refunds', methods=['GET'])
@login_required
def get_user_refunds(user_id):
    """获取用户的退款申请记�?""
    # 只能查看自己的退款记录或管理员可查看任意用户
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({"error": "无权限查�?}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # 构建查询
    query = Refund.query.filter_by(requester_id=user_id)
    
    # 按状态过�?
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    # 执行分页查询
    pagination = query.order_by(Refund.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # 准备响应数据
    refunds = [r.to_dict() for r in pagination.items]
    
    # 添加交易和项目信�?
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
        return jsonify({"error": "无权限查�?}), 403
    
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
        return jsonify({"error": "无权限查�?}), 403
    
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
        return jsonify({"error": "无权限查�?}), 403
    
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
            return jsonify({"error": "开始日期格式无�?}), 400
    
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
    
    # 交易状�?
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
            return jsonify({"error": "开始日期格式无�?}), 400
    
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