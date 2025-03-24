"""
用户相关数据模型
"""

from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from app.extensions import db

class Role(db.Model):
    """用户角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    @staticmethod
    def insert_roles():
        """插入默认角色"""
        roles = {
            'user': '普通用户',
            'moderator': '内容审核员',
            'admin': '平台管理员'
        }
        
        for name, description in roles.items():
            role = Role.query.filter_by(name=name).first()
            if role is None:
                role = Role(name=name, description=description)
                db.session.add(role)
        
        db.session.commit()

class UserRole(db.Model):
    """用户-角色关联表"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserRole {self.user_id}:{self.role_id}>'

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(255))
    student_id = db.Column(db.String(20), unique=True, index=True)
    department = db.Column(db.String(64))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关联
    roles = db.relationship('Role', secondary='user_roles', 
                          backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
    
    # 新增关联
    created_projects = db.relationship('Project', backref='creator', lazy='dynamic',
                                     foreign_keys='Project.creator_id')
    
    led_teams = db.relationship('Team', backref='leader', lazy='dynamic',
                              foreign_keys='Team.leader_id')
    
    team_memberships = db.relationship('TeamMember', backref='user', lazy='dynamic',
                                      cascade='all, delete-orphan')
    
    project_comments = db.relationship('ProjectComment', backref='user', lazy='dynamic',
                                      cascade='all, delete-orphan')
    
    project_updates = db.relationship('ProjectUpdate', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    payments = db.relationship('Payment', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    @property
    def password(self):
        """禁止直接访问密码属性"""
        raise AttributeError('密码不是可读属性')
    
    @password.setter
    def password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """检查用户是否拥有特定角色"""
        return self.roles.filter_by(name=role_name).first() is not None
    
    def add_role(self, role):
        """为用户添加角色"""
        if not self.has_role(role.name):
            self.roles.append(role)
            return True
        return False
    
    def remove_role(self, role):
        """移除用户角色"""
        if self.has_role(role.name):
            self.roles.remove(role)
            return True
        return False
    
    def generate_confirmation_token(self, expiration=3600):
        """生成邮箱确认令牌"""
        payload = {
            'confirm': self.id,
            'exp': datetime.utcnow() + timedelta(seconds=expiration)
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    def confirm(self, token):
        """确认邮箱令牌"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except:
            return False
        
        if payload.get('confirm') != self.id:
            return False
        
        self.email_confirmed = True
        db.session.add(self)
        return True
    
    def generate_reset_token(self, expiration=3600):
        """生成密码重置令牌"""
        payload = {
            'reset': self.id,
            'exp': datetime.utcnow() + timedelta(seconds=expiration)
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        """验证密码重置令牌"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except:
            return None
        
        return User.query.get(payload.get('reset'))
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def teams(self):
        """获取用户加入的所有团队"""
        return [tm.team for tm in self.team_memberships.filter_by(status='accepted').all()]
    
    @property
    def supported_projects(self):
        """获取用户支持的所有项目"""
        return [payment.project for payment in self.payments.filter_by(status='success').all()]
    
    def is_team_member(self, team_id):
        """检查用户是否是团队成员"""
        return self.team_memberships.filter_by(team_id=team_id, status='accepted').first() is not None
    
    def is_team_leader(self, team_id):
        """检查用户是否是团队领导者"""
        return self.led_teams.filter_by(id=team_id).first() is not None
    
    def is_project_creator(self, project_id):
        """检查用户是否是项目创建者"""
        return self.created_projects.filter_by(id=project_id).first() is not None
    
    def has_supported_project(self, project_id):
        """检查用户是否支持了项目"""
        return self.payments.filter_by(project_id=project_id, status='success').first() is not None

    @staticmethod
    def create_admin_user(email, username, password):
        """创建管理员用户"""
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role is None:
            Role.insert_roles()
            admin_role = Role.query.filter_by(name='admin').first()
        
        admin = User.query.filter_by(email=email).first()
        if admin is None:
            admin = User(email=email,
                        username=username,
                        password=password,
                        confirmed=True,
                        avatar='default.jpg')
            db.session.add(admin)
            
            user_role = UserRole(user=admin, role=admin_role)
            db.session.add(user_role)
            db.session.commit()
            return admin
        return None

class VerificationCode(db.Model):
    """邮箱验证码模型"""
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    code = db.Column(db.String(10))
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self, expiration=600):
        """检查验证码是否过期，默认10分钟"""
        return datetime.utcnow() > self.created_at + timedelta(seconds=expiration)
    
    def __repr__(self):
        return f'<VerificationCode {self.email}:{self.code}>' 