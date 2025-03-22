from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, VerificationCode
from application import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)

def generate_verification_code(length=6):
    """生成指定长度的数字验证码"""
    return ''.join(random.choices(string.digits, k=length))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
            return render_template('auth/login.html', error='用户名或密码错误')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        verification_code = request.form.get('verification_code')
        
        # 验证表单
        if not all([username, email, password, confirm_password, verification_code]):
            flash('请填写所有必填字段')
            return render_template('auth/register.html', error='请填写所有必填字段')
            
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return render_template('auth/register.html', error='两次输入的密码不一致')
            
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return render_template('auth/register.html', error='用户名已存在')
            
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return render_template('auth/register.html', error='邮箱已被注册')
        
        # 验证邮箱验证码
        valid_code = VerificationCode.query.filter_by(
            email=email,
            code=verification_code,
            used=False
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if not valid_code or valid_code.is_expired():
            flash('验证码无效或已过期')
            return render_template('auth/register.html', error='验证码无效或已过期')
        
        # 标记验证码为已使用
        valid_code.used = True
        db.session.add(valid_code)
        
        # 创建新用户
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth.route('/send_verification_code', methods=['POST'])
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