from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User, VerificationCode
from app.extensions import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, template_folder='templates')

def generate_verification_code(length=6):
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面和处理逻辑"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # 这里应当查询数据库验证用户
        # user = User.query.filter_by(email=email).first()
        
        # 目前返回404页面，表示功能尚未实现
        return render_template('errors/404.html'), 404
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册页面和处理逻辑"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        student_id = request.form.get('student_id')
        
        # 验证表单数据
        if not all([username, email, password, confirm_password]):
            flash('请填写所有必填字段')
            return render_template('auth/register.html', error='请填写所有必填字段', title='注册')
            
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return render_template('auth/register.html', error='两次输入的密码不一致', title='注册')
        
        # 在开发阶段简化注册流程，跳过验证码和数据库操作
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='注册')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出逻辑"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/send_verification_code', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': '邮箱地址不能为空'})
    
    # 生成验证码
    code = generate_verification_code()
    
    # 存储验证码到数据库
    verification = VerificationCode(email=email, code=code)
    db.session.add(verification)
    db.session.commit()
    
    # 发送验证码邮件
    try:
        msg = Message(
            '校园众创平台 - 邮箱验证码',
            sender=('校园众创平台', 'noreply@example.com'),
            recipients=[email]
        )
        msg.body = f'''您好，

感谢您注册校园众创平台。您的邮箱验证码是：{code}

该验证码有效期为10分钟，请勿将验证码透露给他人。

如果您没有注册我们的平台，请忽略此邮件。

校园众创平台团队
'''
        mail.send(msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """找回密码页面和处理逻辑"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        # 验证邮箱是否存在
        # user = User.query.filter_by(email=email).first()
        # if user:
        #     # 发送重置密码邮件
        #     # send_password_reset_email(user)
        #     flash('重置密码链接已发送到您的邮箱')
        # else:
        #     flash('该邮箱未注册')
        
        # 目前返回404页面，表示功能尚未实现
        return render_template('errors/404.html'), 404
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """重置密码页面和处理逻辑"""
    # 验证token
    # user = User.verify_reset_token(token)
    # if not user:
    #     flash('无效或过期的重置链接')
    #     return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('密码不匹配')
            return render_template('auth/reset_password.html')
        
        # 更新密码
        # user.password = generate_password_hash(password)
        # db.session.commit()
        # flash('密码已重置，请使用新密码登录')
        
        # 目前返回404页面，表示功能尚未实现
        return render_template('errors/404.html'), 404
    
    return render_template('auth/reset_password.html')

@auth_bp.route('/profile')
def profile():
    """用户个人资料页面"""
    # 验证用户是否登录
    # if not session.get('user_id'):
    #     return redirect(url_for('auth.login'))
    
    # user = User.query.get(session['user_id'])
    
    # 目前返回404页面，表示功能尚未实现
    return render_template('errors/404.html'), 404

@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    """更新用户个人资料"""
    # 验证用户是否登录
    # if not session.get('user_id'):
    #     return redirect(url_for('auth.login'))
    
    # 获取表单数据
    # username = request.form.get('username')
    # email = request.form.get('email')
    # student_id = request.form.get('student_id')
    # department = request.form.get('department')
    # bio = request.form.get('bio')
    # skills = request.form.get('skills')
    
    # 更新用户资料
    # user = User.query.get(session['user_id'])
    # user.username = username
    # user.email = email
    # user.student_id = student_id
    # user.department = department
    # user.bio = bio
    # user.skills = skills
    # db.session.commit()
    
    # flash('个人资料已更新')
    
    # 目前返回404页面，表示功能尚未实现
    return render_template('errors/404.html'), 404 