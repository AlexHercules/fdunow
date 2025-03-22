from datetime import datetime, timedelta
from flask_login import UserMixin
from application import db

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    # projects = db.relationship('Project', backref='creator', lazy='dynamic')
    # teams = db.relationship('Team', backref='leader', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'

class VerificationCode(db.Model):
    """邮箱验证码模型"""
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    code = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    def is_expired(self):
        """检查验证码是否已过期（10分钟有效期）"""
        return datetime.utcnow() > self.created_at + timedelta(minutes=10)
    
    def __repr__(self):
        return f'<VerificationCode {self.code} for {self.email}>' 