from datetime import datetime, timedelta
from flask_login import UserMixin
from application import db
import json

# 创建索引辅助函数
def create_index(name, columns):
    return db.Index(name, *columns)

# 权限常量
class Permissions:
    """权限常量类"""
    # 基本权限
    READ = 'read'                      # 读取内容权限
    COMMENT = 'comment'                # 评论权限
    
    # 项目相关权限
    CREATE_PROJECT = 'create_project'  # 创建项目权限
    EDIT_PROJECT = 'edit_project'      # 编辑项目权限
    DELETE_PROJECT = 'delete_project'  # 删除项目权限
    FUND_PROJECT = 'fund_project'      # 资助项目权限
    MONITOR_PROJECT = 'monitor_project'# 监控项目权限
    
    # 用户相关权限
    EDIT_PROFILE = 'edit_profile'      # 编辑个人资料权限
    FOLLOW = 'follow'                  # 关注用户权限
    
    # 团队相关权限
    CREATE_TEAM = 'create_team'        # 创建团队权限
    JOIN_TEAM = 'join_team'            # 加入团队权限
    MANAGE_TEAM = 'manage_team'        # 管理团队权限
    
    # 管理员权限
    MODERATE = 'moderate'              # 内容审核权限
    ADMIN = 'admin'                    # 管理员权限
    
    # 系统权限组
    STUDENT_PERMISSIONS = [READ, COMMENT, CREATE_PROJECT, EDIT_PROFILE, FOLLOW, 
                         JOIN_TEAM, FUND_PROJECT]
    
    DEVELOPER_PERMISSIONS = STUDENT_PERMISSIONS + [EDIT_PROJECT, CREATE_TEAM, MANAGE_TEAM]
    
    MODERATOR_PERMISSIONS = DEVELOPER_PERMISSIONS + [MODERATE]
    
    ADMIN_PERMISSIONS = MODERATOR_PERMISSIONS + [DELETE_PROJECT, MONITOR_PROJECT, ADMIN]
    
    @classmethod
    def get_permissions_for_role(cls, role_name):
        """根据角色名获取权限列表"""
        role_map = {
            'student': cls.STUDENT_PERMISSIONS,
            'developer': cls.DEVELOPER_PERMISSIONS,
            'moderator': cls.MODERATOR_PERMISSIONS,
            'admin': cls.ADMIN_PERMISSIONS
        }
        return role_map.get(role_name.lower(), [])

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 个人资料字段
    name = db.Column(db.String(64))
    avatar = db.Column(db.String(256))
    bio = db.Column(db.Text)
    department = db.Column(db.String(64))
    major = db.Column(db.String(64))
    grade = db.Column(db.String(64))
    skills = db.Column(db.Text)
    interests = db.Column(db.Text)
    phone = db.Column(db.String(32))
    personal_website = db.Column(db.String(256))
    github = db.Column(db.String(256))
    
    # 隐私设置
    email_visibility = db.Column(db.String(20), default='public')
    phone_visibility = db.Column(db.String(20), default='private')
    project_visibility = db.Column(db.String(20), default='public')
    
    # 在线状态
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 角色与权限
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    
    # 关系
    # 团队和项目关系在各自模型中定义
    
    # 创建索引
    __table_args__ = (
        create_index('idx_user_skills', ['skills']),
        create_index('idx_user_department', ['department']),
        create_index('idx_user_major', ['major']),
    )
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_admin = db.Column(db.Boolean, default=False)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            # 如果管理员邮箱，设为管理员角色
            if self.email and self.email.endswith('@admin.fudan.edu.cn'):
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role:
                    self.role = admin_role
                    self.is_admin = True
            # 否则设为默认角色
            if self.role is None:
                default_role = Role.query.filter_by(default=True).first()
                if default_role:
                    self.role = default_role
    
    def has_role(self, role_name):
        """检查用户是否拥有指定角色"""
        return self.role and self.role.name == role_name
    
    def has_permission(self, permission):
        """检查用户是否拥有指定权限"""
        # 管理员拥有所有权限
        if self.is_admin:
            return True
        
        # 通过角色检查权限
        if self.role and self.role.has_permission(permission):
            return True
        
        return False
    
    def can(self, permission):
        """权限检查的简化方法"""
        return self.has_permission(permission)
    
    @property
    def is_administrator(self):
        """检查是否为管理员"""
        return self.is_admin
    
    def promote_to_role(self, role_name):
        """将用户提升到指定角色"""
        role = Role.query.filter_by(name=role_name).first()
        if role:
            self.role = role
            if role_name == 'admin':
                self.is_admin = True
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_friend(self, user):
        """检查给定用户是否是好友"""
        if not user or user.id == self.id:
            return False
        # 查找对应的好友关系
        friendship = FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user.id)) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == self.id))
        ).filter_by(status='accepted').first()
        return friendship is not None
    
    def has_sent_request_to(self, user):
        """检查是否已向给定用户发送好友请求"""
        if not user or user.id == self.id:
            return False
        # 查找是否有发送给该用户的待处理请求
        return FriendRequest.query.filter_by(
            sender_id=self.id,
            receiver_id=user.id,
            status='pending'
        ).first() is not None
    
    def has_received_request_from(self, user):
        """检查是否已收到给定用户的好友请求"""
        if not user or user.id == self.id:
            return False
        # 查找是否有来自该用户的待处理请求
        return FriendRequest.query.filter_by(
            sender_id=user.id,
            receiver_id=self.id,
            status='pending'
        ).first() is not None
    
    @property
    def friends(self):
        """获取所有好友"""
        # 获取已接受的好友请求，其中自己是发送者
        sent_friendships = FriendRequest.query.filter_by(
            sender_id=self.id,
            status='accepted'
        ).all()
        sent_friend_ids = [friendship.receiver_id for friendship in sent_friendships]
        
        # 获取已接受的好友请求，其中自己是接收者
        received_friendships = FriendRequest.query.filter_by(
            receiver_id=self.id,
            status='accepted'
        ).all()
        received_friend_ids = [friendship.sender_id for friendship in received_friendships]
        
        # 合并好友ID并查询用户
        friend_ids = set(sent_friend_ids + received_friend_ids)
        return User.query.filter(User.id.in_(friend_ids)).all()
    
    @property
    def friend_requests_received(self):
        """获取收到的待处理好友请求"""
        return FriendRequest.query.filter_by(
            receiver_id=self.id,
            status='pending'
        ).all()
    
    @property
    def friend_requests_sent(self):
        """获取发出的待处理好友请求"""
        return FriendRequest.query.filter_by(
            sender_id=self.id,
            status='pending'
        ).all()
    
    @property
    def unread_message_count(self):
        """获取未读消息数量"""
        return Message.query.filter_by(
            target_type='user',
            target_id=self.id,
            is_read=False
        ).count()

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Text)  # 存储JSON格式的权限列表
    description = db.Column(db.String(255))
    
    # 与用户的关系
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    @staticmethod
    def insert_roles():
        """初始化角色数据"""
        roles = {
            'student': {
                'permissions': Permissions.STUDENT_PERMISSIONS,
                'description': '普通学生用户',
                'default': True
            },
            'developer': {
                'permissions': Permissions.DEVELOPER_PERMISSIONS,
                'description': '项目开发者',
                'default': False
            },
            'moderator': {
                'permissions': Permissions.MODERATOR_PERMISSIONS,
                'description': '内容审核员',
                'default': False
            },
            'admin': {
                'permissions': Permissions.ADMIN_PERMISSIONS,
                'description': '管理员',
                'default': False
            }
        }
        
        for role_name, role_info in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
            
            role.permissions = json.dumps(role_info['permissions'])
            role.default = role_info['default']
            role.description = role_info['description']
            
            db.session.add(role)
        
        db.session.commit()
    
    def has_permission(self, permission):
        """检查角色是否拥有指定权限"""
        if self.permissions:
            permissions_list = json.loads(self.permissions)
            return permission in permissions_list
        return False
    
    def add_permission(self, permission):
        """添加权限到角色"""
        if self.permissions:
            permissions_list = json.loads(self.permissions)
            if permission not in permissions_list:
                permissions_list.append(permission)
                self.permissions = json.dumps(permissions_list)
                return True
        else:
            self.permissions = json.dumps([permission])
            return True
        return False
    
    def remove_permission(self, permission):
        """从角色中移除权限"""
        if self.permissions:
            permissions_list = json.loads(self.permissions)
            if permission in permissions_list:
                permissions_list.remove(permission)
                self.permissions = json.dumps(permissions_list)
                return True
        return False
    
    def reset_permissions(self):
        """重置角色权限"""
        self.permissions = json.dumps([])
        return True
    
    def __repr__(self):
        return f'<Role {self.name}>'

# 用户-角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class FriendRequest(db.Model):
    """好友请求模型"""
    __tablename__ = 'friend_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    message = db.Column(db.Text)  # 请求附带消息
    status = db.Column(db.String(20), default='pending', index=True)  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_requests', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_requests', lazy='dynamic'))
    
    def __repr__(self):
        return f'<FriendRequest {self.id}: {self.sender_id} -> {self.receiver_id}>'

class Message(db.Model):
    """统一消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # 多态关联字段
    target_type = db.Column(db.String(20), index=True)  # 'user' 或 'group'
    target_id = db.Column(db.Integer, index=True)  # 用户ID或群组ID
    
    # 消息状态
    is_read = db.Column(db.Boolean, default=False)  # 对于群消息，此字段忽略
    
    # 关系
    sender = db.relationship('User', backref=db.backref('sent_messages', lazy='dynamic'))
    
    # 创建组合索引
    __table_args__ = (
        create_index('idx_message_target', ['target_type', 'target_id']),
        create_index('idx_message_sender_target', ['sender_id', 'target_type', 'target_id']),
    )
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_id} -> {self.target_type}:{self.target_id}>'
    
    @classmethod
    def get_private_chat(cls, user1_id, user2_id, limit=20, offset=0):
        """获取两个用户间的私聊消息"""
        # 私聊消息查询
        # 查询 user1 -> user2 和 user2 -> user1 的消息
        query = cls.query.filter(
            ((cls.sender_id == user1_id) & (cls.target_type == 'user') & (cls.target_id == user2_id)) | 
            ((cls.sender_id == user2_id) & (cls.target_type == 'user') & (cls.target_id == user1_id))
        ).order_by(cls.created_at.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @classmethod
    def get_group_chat(cls, group_id, limit=20, offset=0):
        """获取群组消息"""
        # 查询群组消息
        query = cls.query.filter_by(
            target_type='group',
            target_id=group_id
        ).order_by(cls.created_at.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @classmethod
    def mark_as_read(cls, user_id, sender_id):
        """将来自特定发送者的所有未读消息标记为已读"""
        cls.query.filter_by(
            target_type='user',
            target_id=user_id,
            sender_id=sender_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()

class ChatGroup(db.Model):
    """聊天群组模型"""
    __tablename__ = 'chat_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    avatar = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # 关联团队（可选）
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    
    # 关系
    creator = db.relationship('User', backref=db.backref('created_groups', lazy='dynamic'))
    members = db.relationship('User', secondary='group_members', backref=db.backref('groups', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ChatGroup {self.name}>'
    
    def is_member(self, user):
        """检查用户是否是群成员"""
        return user in self.members
    
    @property
    def member_count(self):
        """群成员数量"""
        return len(self.members)
    
    def get_messages(self, limit=20, offset=0):
        """获取群组消息"""
        return Message.get_group_chat(self.id, limit, offset)

# 群组成员关联表
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('chat_groups.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

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

# 项目评论模型
class ProjectComment(db.Model):
    """项目评论模型"""
    __tablename__ = 'project_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)  # 被管理员隐藏
    likes_count = db.Column(db.Integer, default=0)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('crowdfunding_project.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('project_comments.id'), nullable=True)
    
    # 关系
    user = db.relationship('User', backref=db.backref('project_comments', lazy='dynamic'))
    project = db.relationship('CrowdfundingProject', backref=db.backref('comments', lazy='dynamic'))
    replies = db.relationship('ProjectComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<ProjectComment {self.id}>'
    
    @staticmethod
    def add_comment(user_id, project_id, content, is_anonymous=False, parent_id=None):
        """添加评论的静态方法"""
        comment = ProjectComment(
            user_id=user_id,
            project_id=project_id,
            content=content,
            is_anonymous=is_anonymous,
            parent_id=parent_id
        )
        db.session.add(comment)
        return comment
    
    def hide(self):
        """隐藏评论"""
        self.is_hidden = True
        return self
    
    def unhide(self):
        """取消隐藏评论"""
        self.is_hidden = False
        return self
    
    def like(self, user):
        """用户点赞评论"""
        like = CommentLike.query.filter_by(
            user_id=user.id,
            comment_id=self.id
        ).first()
        
        if not like:
            like = CommentLike(user_id=user.id, comment_id=self.id)
            db.session.add(like)
            self.likes_count += 1
            return True
        return False
    
    def unlike(self, user):
        """用户取消点赞评论"""
        like = CommentLike.query.filter_by(
            user_id=user.id,
            comment_id=self.id
        ).first()
        
        if like:
            db.session.delete(like)
            self.likes_count -= 1
            return True
        return False
    
    def to_dict(self):
        """将评论转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_anonymous': self.is_anonymous,
            'is_hidden': self.is_hidden,
            'likes_count': self.likes_count,
            'user': {
                'id': self.user.id,
                'username': '匿名用户' if self.is_anonymous else self.user.username,
                'avatar': None if self.is_anonymous else self.user.avatar
            },
            'replies_count': self.replies.count()
        }


# 评论点赞模型
class CommentLike(db.Model):
    """评论点赞模型"""
    __tablename__ = 'comment_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('project_comments.id'), nullable=False)
    
    # 关系
    user = db.relationship('User', backref=db.backref('comment_likes', lazy='dynamic'))
    comment = db.relationship('ProjectComment', backref=db.backref('likes', lazy='dynamic'))
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),)
    
    def __repr__(self):
        return f'<CommentLike {self.id}>'

# 项目多媒体模型
class ProjectMedia(db.Model):
    """项目多媒体模型，用于管理项目相关的图片、视频、文档等"""
    __tablename__ = 'project_media'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)  # 'image', 'video', 'document'
    file_size = db.Column(db.Integer)  # 文件大小，单位为字节
    mime_type = db.Column(db.String(100))  # MIME类型
    description = db.Column(db.String(255))
    is_cover = db.Column(db.Boolean, default=False)  # 是否为项目封面
    order = db.Column(db.Integer, default=0)  # 显示顺序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('crowdfunding_project.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 关系
    project = db.relationship('CrowdfundingProject', backref=db.backref('media', lazy='dynamic'))
    uploader = db.relationship('User', backref=db.backref('uploaded_media', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProjectMedia {self.id}: {self.media_type}>'
    
    @property
    def url(self):
        """获取媒体文件的URL"""
        return f'/static/{self.file_path}'
    
    @property
    def thumbnail_url(self):
        """获取媒体缩略图URL"""
        if self.media_type == 'image':
            # 路径分解
            path_parts = self.file_path.rsplit('.', 1)
            if len(path_parts) > 1:
                return f'/static/{path_parts[0]}_thumb.{path_parts[1]}'
        elif self.media_type == 'video':
            return '/static/img/video-thumbnail.png'
        elif self.media_type == 'document':
            return '/static/img/document-thumbnail.png'
        return None
    
    def to_dict(self):
        """将媒体对象转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'media_type': self.media_type,
            'description': self.description,
            'is_cover': self.is_cover,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat()
        }

# 论坛分类模型
class ForumCategory(db.Model):
    """论坛分类模型"""
    __tablename__ = 'forum_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(128))  # 分类图标
    order = db.Column(db.Integer, default=0)  # 显示顺序
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    topics = db.relationship('ForumTopic', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ForumCategory {self.name}>'
    
    @property
    def topics_count(self):
        """获取分类下的主题数量"""
        return self.topics.filter_by(is_hidden=False).count()
    
    @property
    def latest_topic(self):
        """获取分类下的最新主题"""
        return self.topics.filter_by(is_hidden=False).order_by(ForumTopic.created_at.desc()).first()


# 论坛主题模型
class ForumTopic(db.Model):
    """论坛主题模型"""
    __tablename__ = 'forum_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    is_highlighted = db.Column(db.Boolean, default=False)  # 是否加精
    is_hidden = db.Column(db.Boolean, default=False)  # 是否隐藏
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_comment_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 关系
    author = db.relationship('User', backref=db.backref('forum_topics', lazy='dynamic'))
    comments = db.relationship('ForumComment', backref='topic', lazy='dynamic')
    
    def __repr__(self):
        return f'<ForumTopic {self.id}: {self.title}>'
    
    def increase_view_count(self):
        """增加浏览量"""
        self.views_count += 1
        return self
    
    def pin(self):
        """置顶主题"""
        self.is_pinned = True
        return self
    
    def unpin(self):
        """取消置顶"""
        self.is_pinned = False
        return self
    
    def highlight(self):
        """加精主题"""
        self.is_highlighted = True
        return self
    
    def unhighlight(self):
        """取消加精"""
        self.is_highlighted = False
        return self
    
    def hide(self):
        """隐藏主题"""
        self.is_hidden = True
        return self
    
    def unhide(self):
        """取消隐藏"""
        self.is_hidden = False
        return self
    
    def like(self, user):
        """用户点赞主题"""
        like = TopicLike.query.filter_by(
            user_id=user.id,
            topic_id=self.id
        ).first()
        
        if not like:
            like = TopicLike(user_id=user.id, topic_id=self.id)
            db.session.add(like)
            self.likes_count += 1
            return True
        return False
    
    def unlike(self, user):
        """用户取消点赞主题"""
        like = TopicLike.query.filter_by(
            user_id=user.id,
            topic_id=self.id
        ).first()
        
        if like:
            db.session.delete(like)
            self.likes_count -= 1
            return True
        return False
    
    def to_dict(self):
        """将主题转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'is_pinned': self.is_pinned,
            'is_highlighted': self.is_highlighted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_comment_at': self.last_comment_at.isoformat() if self.last_comment_at else None,
            'category': {
                'id': self.category.id,
                'name': self.category.name
            },
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'avatar': self.author.avatar
            }
        }


# 论坛评论模型
class ForumComment(db.Model):
    """论坛评论模型"""
    __tablename__ = 'forum_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    is_hidden = db.Column(db.Boolean, default=False)  # 是否隐藏
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_comments.id'), nullable=True)
    
    # 关系
    author = db.relationship('User', backref=db.backref('forum_comments', lazy='dynamic'))
    replies = db.relationship('ForumComment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<ForumComment {self.id}>'
    
    def hide(self):
        """隐藏评论"""
        self.is_hidden = True
        return self
    
    def unhide(self):
        """取消隐藏"""
        self.is_hidden = False
        return self
    
    def like(self, user):
        """用户点赞评论"""
        like = CommentLike.query.filter_by(
            user_id=user.id,
            comment_id=self.id
        ).first()
        
        if not like:
            like = CommentLike(user_id=user.id, comment_id=self.id)
            db.session.add(like)
            self.likes_count += 1
            return True
        return False
    
    def unlike(self, user):
        """用户取消点赞评论"""
        like = CommentLike.query.filter_by(
            user_id=user.id,
            comment_id=self.id
        ).first()
        
        if like:
            db.session.delete(like)
            self.likes_count -= 1
            return True
        return False
    
    def to_dict(self):
        """将评论转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'likes_count': self.likes_count,
            'is_hidden': self.is_hidden,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'avatar': self.author.avatar
            },
            'replies_count': self.replies.count()
        }


# 主题点赞模型
class TopicLike(db.Model):
    """主题点赞模型"""
    __tablename__ = 'topic_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)
    
    # 关系
    user = db.relationship('User', backref=db.backref('topic_likes', lazy='dynamic'))
    topic = db.relationship('ForumTopic', backref=db.backref('likes', lazy='dynamic'))
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'topic_id', name='unique_user_topic_like'),)
    
    def __repr__(self):
        return f'<TopicLike {self.id}>' 