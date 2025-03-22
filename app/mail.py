"""
邮件发送模块
"""
from flask import Blueprint, current_app, jsonify, request
from application import mail
from flask_mail import Message
import threading

mail_bp = Blueprint('mail', __name__)

def send_async_email(app, msg):
    """异步发送邮件"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"邮件发送失败: {str(e)}")

def send_email(subject, recipients, body, html=None):
    """发送邮件
    
    参数:
        subject: 邮件主题
        recipients: 收件人列表
        body: 纯文本内容
        html: HTML内容
    """
    app = current_app._get_current_object()
    msg = Message(subject=subject, recipients=recipients)
    msg.body = body
    if html:
        msg.html = html
    
    # 使用线程异步发送邮件
    thread = threading.Thread(target=send_async_email, args=[app, msg])
    thread.start()
    return thread

@mail_bp.route('/test', methods=['POST'])
def test_email():
    """测试邮件发送"""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'success': False, 'message': '请提供有效的邮箱地址'})
    
    email = data['email']
    subject = "校园众创平台 - 测试邮件"
    body = """
    您好，
    
    这是一封测试邮件，用于验证校园众创平台的邮件发送功能是否正常。
    
    如果您收到此邮件，表示邮件系统工作正常。
    
    校园众创平台团队
    """
    
    try:
        send_email(subject=subject, recipients=[email], body=body)
        return jsonify({'success': True, 'message': '测试邮件已发送'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'邮件发送失败: {str(e)}'}) 