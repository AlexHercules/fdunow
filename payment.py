from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Donation, Project
from datetime import datetime
import random
import string

# 创建蓝图
payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

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