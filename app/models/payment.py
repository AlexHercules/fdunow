"""
支付相关数据模型
"""

from datetime import datetime
from app.extensions import db

class Payment(db.Model):
    """支付记录模型"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True, index=True)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    evidence = db.Column(db.String(255))  # 支付凭证图片路径
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    
    # 关联
    rewards = db.relationship('PaymentReward', backref='payment', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.amount}>'

class PaymentReward(db.Model):
    """支付回报模型"""
    __tablename__ = 'payment_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    delivery_status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered
    delivery_date = db.Column(db.DateTime)
    
    # 外键
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id', ondelete='CASCADE'))
    reward_id = db.Column(db.Integer, db.ForeignKey('project_rewards.id'))
    
    def __repr__(self):
        return f'<PaymentReward {self.id}>'

class ProjectReward(db.Model):
    """项目回报等级模型"""
    __tablename__ = 'project_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    inventory = db.Column(db.Integer, default=-1)  # -1表示无限
    shipping_date = db.Column(db.DateTime)
    is_limited = db.Column(db.Boolean, default=False)
    
    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    
    # 关联
    payments = db.relationship('PaymentReward', backref='reward', lazy='dynamic')
    
    @property
    def claimed(self):
        """已认领数量"""
        return self.payments.count()
    
    @property
    def available(self):
        """剩余可用数量"""
        if self.inventory == -1:
            return float('inf')
        return max(0, self.inventory - self.claimed)
    
    def __repr__(self):
        return f'<ProjectReward {self.name} - {self.amount}>' 