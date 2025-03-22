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
        sent_friends = [friendship.receiver for friendship in sent_friendships]
        
        # 获取已接受的好友请求，其中自己是接收者
        received_friendships = FriendRequest.query.filter_by(
            receiver_id=self.id,
            status='accepted'
        ).all()
        received_friends = [friendship.sender for friendship in received_friendships]
        
        # 合并并返回所有好友
        return sent_friends + received_friends
    
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