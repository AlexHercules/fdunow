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

# 定义群组成员关系表
chat_group_members = db.Table('chat_group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('chat_group.id'), primary_key=True),
    db.Column('join_time', db.DateTime, default=datetime.utcnow),
    db.Column('role', db.String(20), default='member')  # 角色：admin, member
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
    phone = db.Column(db.String(20))
    personal_website = db.Column(db.String(255))
    github = db.Column(db.String(255))
    school = db.Column(db.String(100), default='复旦大学')
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 隐私设置
    privacy_settings = db.Column(db.Text, default='{"email": "friends", "phone": "private", "projects": "public"}')
    
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
    
    # 好友相关
    friends = db.relationship(
        'User', secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref=db.backref('friended_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # 群组相关
    groups_created = db.relationship('ChatGroup', backref='creator', lazy='dynamic')
    
    # 密码处理
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_friend(self, user):
        """添加好友"""
        if not self.is_friend(user):
            self.friends.append(user)
            return True
        return False
    
    def remove_friend(self, user):
        """删除好友"""
        if self.is_friend(user):
            self.friends.remove(user)
            return True
        return False
    
    def is_friend(self, user):
        """检查是否为好友"""
        return self.friends.filter(friendships.c.friend_id == user.id).count() > 0
    
    def update_last_seen(self):
        """更新最后在线时间"""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def unread_message_count(self):
        """获取用户的未读消息数量"""
        return Message.query.filter_by(
            target_type='user',
            target_id=self.id,
            is_read=False
        ).count()

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
    """统一消息模型，用于私聊和群组消息"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # target_type 可以是 'user' 或 'group'
    target_type = db.Column(db.String(10), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    sender = db.relationship('User', backref='sent_messages')
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_id} to {self.target_type}_{self.target_id}>'
    
    @property
    def timestamp(self):
        """返回格式化的时间戳"""
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_private_chat(user1_id, user2_id, limit=100):
        """获取两个用户之间的私聊消息"""
        return Message.query.filter(
            (
                (Message.sender_id == user1_id) & 
                (Message.target_type == 'user') & 
                (Message.target_id == user2_id)
            ) | (
                (Message.sender_id == user2_id) & 
                (Message.target_type == 'user') & 
                (Message.target_id == user1_id)
            )
        ).order_by(Message.created_at).limit(limit).all()
    
    @staticmethod
    def get_group_chat(group_id, limit=100):
        """获取群组的聊天消息"""
        return Message.query.filter_by(
            target_type='group', 
            target_id=group_id
        ).order_by(Message.created_at).limit(limit).all()
    
    @staticmethod
    def mark_as_read(user_id, sender_id):
        """将来自特定用户的所有未读消息标记为已读"""
        unread_messages = Message.query.filter_by(
            sender_id=sender_id,
            target_type='user',
            target_id=user_id,
            is_read=False
        ).all()
        
        current_time = datetime.utcnow()
        for message in unread_messages:
            message.is_read = True
            message.read_at = current_time
        
        db.session.commit()
        return len(unread_messages)

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

# 添加群组模型
class ChatGroup(db.Model):
    """聊天群组模型"""
    __tablename__ = 'chat_group'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # 关联团队，可为空
    
    # 关系
    members = db.relationship(
        'User', secondary=chat_group_members,
        backref=db.backref('groups', lazy='dynamic'),
        lazy='dynamic'
    )
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic')
    
    def add_member(self, user, role='member'):
        """添加成员"""
        if not self.is_member(user):
            assoc = chat_group_members.insert().values(
                user_id=user.id, 
                group_id=self.id,
                role=role
            )
            db.session.execute(assoc)
            db.session.commit()
            return True
        return False
    
    def remove_member(self, user):
        """移除成员"""
        if self.is_member(user):
            stmt = chat_group_members.delete().where(
                (chat_group_members.c.user_id == user.id) &
                (chat_group_members.c.group_id == self.id)
            )
            db.session.execute(stmt)
            db.session.commit()
            return True
        return False
    
    def is_member(self, user):
        """检查用户是否是群组成员"""
        """检查是否为成员"""
        return self.members.filter(chat_group_members.c.user_id == user.id).count() > 0
    
    def get_member_role(self, user):
        """获取成员角色"""
        result = db.session.query(chat_group_members.c.role).filter(
            chat_group_members.c.user_id == user.id,
            chat_group_members.c.group_id == self.id
        ).first()
        return result[0] if result else None
    
    def __repr__(self):
        return f'<ChatGroup {self.name}>'

    @property
    def member_count(self):
        """获取群组成员数量"""
        return self.members.count()

# 群组消息模型
class GroupMessage(db.Model):
    """群聊消息模型"""
    __tablename__ = 'group_message'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('chat_group.id'))
    
    # 关系
    sender = db.relationship('User', backref='group_messages_sent')
    
    def __repr__(self):
        return f'<GroupMessage {self.id}>'

# 好友请求模型
class FriendRequest(db.Model):
    """好友请求模型"""
    __tablename__ = 'friend_request'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='friend_requests_sent')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='friend_requests_received')
    
    def accept(self):
        """接受好友请求"""
        if self.status == 'pending':
            self.status = 'accepted'
            # 建立双向好友关系
            self.from_user.add_friend(self.to_user)
            self.to_user.add_friend(self.from_user)
            db.session.commit()
            return True
        return False
    
    def reject(self):
        """拒绝好友请求"""
        if self.status == 'pending':
            self.status = 'rejected'
            db.session.commit()
            return True
        return False
    
    def __repr__(self):
        return f'<FriendRequest {self.id}>' 