"""
根目录下的models.py文件，包含所有数据库模型
注意：此文件与app/models.py不同，是项目的主数据模型文件

如果遇到错误"could not find table 'user' with which to generate a foreign key"，
可能是因为User类的__tablename__设置为'users'，而外键引用了'user.id'。
确保表名称一致。
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta
import enum
from application import db
import uuid

# 定义团队成员关系表（多对多）
team_members = db.Table('team_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('role', db.String(50), default='member'),  # 角色：创建者、成员等
    db.Column('join_time', db.DateTime, default=datetime.utcnow)
)

# 定义用户收藏项目关系表（多对多）
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('crowdfunding_project.id'), primary_key=True),
    db.Column('favorite_time', db.DateTime, default=datetime.utcnow)
)

# 定义用户点赞项目关系表（多对多）
user_likes = db.Table('user_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('crowdfunding_project.id'), primary_key=True),
    db.Column('like_time', db.DateTime, default=datetime.utcnow)
)

# 定义好友关系表（自引用多对多）
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('status', db.String(20), default='pending'),  # pending, accepted, rejected
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# 项目分类枚举
class ProjectCategory(enum.Enum):
    TECH = '技术'
    DESIGN = '设计'
    ART = '艺术'
    EDUCATION = '教育'
    SOCIAL = '社会'
    BUSINESS = '商业'
    OTHER = '其他'

# 组队类型枚举
class TeamType(enum.Enum):
    STUDY = '学习'
    DAILY = '日常'
    COMPETITION = '比赛'
    PROJECT = '项目'
    RESEARCH = '科研'
    STARTUP = '创业'
    CLUB = '社团'
    STUDENT_WORK = '学工'
    OTHER = '其他'

# 用户模型
class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    major = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    skills = db.Column(db.Text)
    interests = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    projects_created = db.relationship('CrowdfundingProject', backref='creator', lazy='dynamic')
    teams_created = db.relationship('Team', backref='creator', lazy='dynamic')
    donations = db.relationship('CrowdfundingDonation', backref='donor', lazy='dynamic')
    messages_sent = db.relationship(
        'Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic'
    )
    messages_received = db.relationship(
        'Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic'
    )
    
    # 密码处理
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# 项目模型（众筹模块）
class CrowdfundingProject(db.Model):
    """众筹项目模型"""
    __tablename__ = 'crowdfunding_project'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    image = db.Column(db.String(256))  # 存储图片路径
    target_amount = db.Column(db.Float)
    current_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, funded, closed
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    donations = db.relationship('CrowdfundingDonation', backref='project', lazy='dynamic')
    liked_by = db.relationship('User', secondary=user_likes, lazy='dynamic',
                              backref=db.backref('liked_projects', lazy='dynamic'))
    favorited_by = db.relationship('User', secondary=user_favorites, lazy='dynamic',
                                  backref=db.backref('favorite_projects', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CrowdfundingProject {self.title}>'
    
    @property
    def progress(self):
        """计算众筹进度百分比"""
        if self.target_amount == 0:
            return 0
        return min(100, int(self.current_amount / self.target_amount * 100))
    
    @property
    def days_left(self):
        """计算剩余天数"""
        if not self.end_date:
            return 0
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_active(self):
        """项目是否处于活跃状态"""
        return self.status == 'active' and self.end_date > datetime.utcnow()
    
    @property
    def supporters_count(self):
        """获取支持者数量"""
        return self.donations.with_entities(db.func.count(db.distinct(CrowdfundingDonation.donor_id))).scalar()

# 团队模型（组队模块）
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    team_type = db.Column(db.Enum(TeamType))
    max_members = db.Column(db.Integer, default=5)
    required_skills = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='recruiting')  # recruiting, full, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 关系
    projects = db.relationship('CrowdfundingProject', backref='team', lazy='dynamic')
    members = db.relationship(
        'User', secondary=team_members,
        primaryjoin=(team_members.c.team_id == id),
        backref=db.backref('teams', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Team {self.name}>'

# 项目更新模型
class ProjectUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('crowdfunding_project.id'))
    
    def __repr__(self):
        return f'<ProjectUpdate {self.title}>'

# 捐赠/资金支持模型
class CrowdfundingDonation(db.Model):
    """众筹捐款模型"""
    __tablename__ = 'crowdfunding_donation'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    project_id = db.Column(db.Integer, db.ForeignKey('crowdfunding_project.id'))
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    transaction_id = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()))
    message = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CrowdfundingDonation {self.amount} for Project {self.project_id}>'

# 消息模型（社交模块）
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Message {self.id}>'

# 引导问题模型（社交模块）
class GuidingQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    category = db.Column(db.String(50))
    intimacy_level = db.Column(db.Integer)  # 1-5，表示问题的亲密程度
    
    def __repr__(self):
        return f'<GuidingQuestion {self.id}>'

# 匿名对话模型（社交模块）
class AnonymousChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='active')  # active, revealed, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    intimacy_level = db.Column(db.Integer, default=1)  # 1-5，表示对话的亲密程度
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 关系
    messages = db.relationship('AnonymousChatMessage', backref='chat', lazy='dynamic')
    
    def __repr__(self):
        return f'<AnonymousChat {self.id}>'

# 匿名对话消息模型
class AnonymousChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_from_user1 = db.Column(db.Boolean)  # True表示消息来自user1，False表示来自user2
    chat_id = db.Column(db.Integer, db.ForeignKey('anonymous_chat.id'))
    
    def __repr__(self):
        return f'<AnonymousChatMessage {self.id}>'

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