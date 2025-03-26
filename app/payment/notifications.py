"""支付通知功能"""
from flask import current_app
from app.utils import send_email
from app.models.payment import Payment, Refund
import logging

logger = logging.getLogger(__name__)

def send_payment_notification(payment):
    """发送支付通知"""
    try:
        # 发送给支付用户
        send_email(
            subject='支付成功通知',
            recipients=[payment.user.email],
            template='email/payment_success',
            payment=payment
        )
        
        # 发送给项目创建者
        send_email(
            subject='收到新的支付',
            recipients=[payment.project.creator.email],
            template='email/new_payment',
            payment=payment
        )
        
        # 如果是管理员,发送平台通知
        if current_app.config.get('ADMIN_EMAIL'):
            send_email(
                subject='新的支付通知',
                recipients=[current_app.config['ADMIN_EMAIL']],
                template='email/admin_payment_notification',
                payment=payment
            )
            
    except Exception as e:
        logger.error(f"发送支付通知失败: {str(e)}")

def send_payment_failed_notification(payment):
    """发送支付失败通知"""
    try:
        send_email(
            subject='支付失败通知',
            recipients=[payment.user.email],
            template='email/payment_failed',
            payment=payment
        )
    except Exception as e:
        logger.error(f"发送支付失败通知失败: {str(e)}")

def send_payment_timeout_notification(payment):
    """发送支付超时通知"""
    try:
        send_email(
            subject='支付超时提醒',
            recipients=[payment.user.email],
            template='email/payment_timeout',
            payment=payment
        )
    except Exception as e:
        logger.error(f"发送支付超时通知失败: {str(e)}")

def send_refund_notification(refund):
    """发送退款通知"""
    try:
        if refund.status == 'pending':
            # 发送给用户
            send_email(
                subject='退款申请已提交',
                recipients=[refund.user.email],
                template='email/refund_requested',
                refund=refund
            )
            
            # 发送给管理员
            if current_app.config.get('ADMIN_EMAIL'):
                send_email(
                    subject='新的退款申请',
                    recipients=[current_app.config['ADMIN_EMAIL']],
                    template='email/admin_refund_request',
                    refund=refund
                )
                
        elif refund.status == 'approved':
            # 发送给用户
            send_email(
                subject='退款申请已通过',
                recipients=[refund.user.email],
                template='email/refund_approved',
                refund=refund
            )
            
            # 发送给项目创建者
            send_email(
                subject='退款已通过',
                recipients=[refund.payment.project.creator.email],
                template='email/refund_approved_creator',
                refund=refund
            )
            
        elif refund.status == 'rejected':
            # 发送给用户
            send_email(
                subject='退款申请已拒绝',
                recipients=[refund.user.email],
                template='email/refund_rejected',
                refund=refund
            )
            
    except Exception as e:
        logger.error(f"发送退款通知失败: {str(e)}")

def send_payment_status_update_notification(payment):
    """发送支付状态更新通知"""
    try:
        send_email(
            subject='支付状态更新',
            recipients=[payment.user.email],
            template='email/payment_status_update',
            payment=payment
        )
    except Exception as e:
        logger.error(f"发送支付状态更新通知失败: {str(e)}") 