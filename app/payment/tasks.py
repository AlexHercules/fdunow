"""支付相关任务"""
from datetime import datetime, timedelta
from app.extensions import db
from app.models.payment import Payment
from app.models.project import Project
from app.utils import send_email
from flask import current_app

def cancel_expired_payments():
    """取消超时未支付的订单"""
    try:
        # 获取超时时间（默认30分钟）
        timeout_minutes = current_app.config.get('PAYMENT_TIMEOUT_MINUTES', 30)
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        # 查询超时未支付的订单
        expired_payments = Payment.query.filter(
            Payment.status == 'pending',
            Payment.created_at < timeout_threshold
        ).all()
        
        for payment in expired_payments:
            # 更新支付状态
            payment.status = 'cancelled'
            payment.cancelled_at = datetime.utcnow()
            payment.cancel_reason = '支付超时'
            
            # 发送邮件通知
            try:
                send_email(
                    subject='支付超时提醒',
                    recipients=[payment.user.email],
                    template='email/payment_timeout',
                    payment=payment
                )
            except Exception as e:
                current_app.logger.error(f"发送支付超时邮件失败: {str(e)}")
        
        db.session.commit()
        current_app.logger.info(f"已取消 {len(expired_payments)} 个超时支付订单")
        
    except Exception as e:
        current_app.logger.error(f"处理支付超时任务时发生错误: {str(e)}")
        db.session.rollback()

def check_payment_status():
    """检查支付状态"""
    try:
        # 获取待支付订单
        pending_payments = Payment.query.filter_by(status='pending').all()
        
        for payment in pending_payments:
            # 根据支付方式查询支付状态
            status = query_payment_status(payment)
            
            if status != payment.status:
                # 更新支付状态
                payment.status = status
                if status == 'completed':
                    payment.paid_at = datetime.utcnow()
                    
                    # 更新项目筹集金额
                    project = Project.query.get(payment.project_id)
                    if project:
                        project.current_amount += payment.amount
                        
                        # 检查是否达到目标金额
                        if project.current_amount >= project.target_amount:
                            project.is_completed = True
                            project.completed_at = datetime.utcnow()
                
                db.session.commit()
                
                # 发送状态变更通知
                try:
                    send_email(
                        subject='支付状态更新',
                        recipients=[payment.user.email],
                        template='email/payment_status_update',
                        payment=payment
                    )
                except Exception as e:
                    current_app.logger.error(f"发送支付状态更新邮件失败: {str(e)}")
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"检查支付状态时发生错误: {str(e)}")
        db.session.rollback()

def query_payment_status(payment):
    """查询支付状态"""
    try:
        if payment.payment_method == 'wechat':
            return query_wechat_payment_status(payment)
        elif payment.payment_method == 'alipay':
            return query_alipay_payment_status(payment)
        else:  # campus_card
            return query_campus_card_payment_status(payment)
    except Exception as e:
        current_app.logger.error(f"查询支付状态失败: {str(e)}")
        return payment.status

def query_wechat_payment_status(payment):
    """查询微信支付状态"""
    # TODO: 实现微信支付状态查询
    return payment.status

def query_alipay_payment_status(payment):
    """查询支付宝支付状态"""
    # TODO: 实现支付宝支付状态查询
    return payment.status

def query_campus_card_payment_status(payment):
    """查询校园卡支付状态"""
    # TODO: 实现校园卡支付状态查询
    return payment.status 