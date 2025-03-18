from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import enum

# 初始化SQLAlchemy
db = SQLAlchemy()

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
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('favorite_time', db.DateTime, default=datetime.utcnow)
)

# 定义用户点赞项目关系表（多对多）
user_likes = db.Table('user_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    projects_created = db.relationship('Project', backref='creator', lazy='dynamic')
    teams_created = db.relationship('Team', backref='creator', lazy='dynamic')
    donations = db.relationship('Donation', backref='donor', lazy='dynamic')
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
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    category = db.Column(db.Enum(ProjectCategory))
    target_amount = db.Column(db.Float, default=0)
    current_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    image_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='draft')  # draft, active, funded, closed
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    
    # 关系
    donations = db.relationship('Donation', backref='project', lazy='dynamic')
    updates = db.relationship('ProjectUpdate', backref='project', lazy='dynamic')
    
    def __repr__(self):
        return f'<Project {self.title}>'

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
    projects = db.relationship('Project', backref='team', lazy='dynamic')
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
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    def __repr__(self):
        return f'<ProjectUpdate {self.title}>'

# 捐赠/资金支持模型
class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    message = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    def __repr__(self):
        return f'<Donation {self.id} - ¥{self.amount}>'

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