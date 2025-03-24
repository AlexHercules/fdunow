from datetime import datetime
from decimal import Decimal
from application import db
from enum import Enum, auto
import json

class TransactionType(Enum):
    """交易类型枚举"""
    DONATION = auto()       # 捐赠
    REFUND = auto()         # 退�?
    SERVICE_FEE = auto()    # 服务�?
    WITHDRAWAL = auto()     # 提现
    
    def __str__(self):
        return self.name

class PaymentStatus(Enum):
    """支付状态枚�?""
    PENDING = auto()        # 待处�?
    PROCESSING = auto()     # 处理�?
    COMPLETED = auto()      # 已完�?
    FAILED = auto()         # 失败
    REFUNDED = auto()       # 已退�?
    CANCELLED = auto()      # 已取�?
    
    def __str__(self):
        return self.name

class PaymentMethod(Enum):
    """支付方式枚举"""
    ALIPAY = auto()         # 支付�?
    WECHAT = auto()         # 微信支付
    BANK_TRANSFER = auto()  # 银行转账
    CAMPUS_CARD = auto()    # 校园�?
    
    def __str__(self):
        return self.name

class ProjectCategory(Enum):
    CHARITY = 'charity'
    STARTUP = 'startup'
    ACADEMIC = 'academic'
    CULTURAL = 'cultural'
    SPORTS = 'sports'

# 交易记录模型
class Transaction(db.Model):
    """交易记录模型"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(64), unique=True, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING.name)
    payment_method = db.Column(db.String(20))
    payment_evidence = db.Column(db.String(255))
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('transactions', lazy='dynamic'))
    
    # 关联项目（如果是捐赠�?
    project_id = db.Column(db.Integer, db.ForeignKey('crowdfunding_projects.id'), nullable=True)
    project = db.relationship('CrowdfundingProject', backref=db.backref('transactions', lazy='dynamic'))
    
    # 时间记录
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 备注
    note = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        if not self.transaction_number:
            # 生成交易编号：时间戳 + 用户ID + 随机字符
            import time
            import random
            import string
            timestamp = int(time.time())
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            user_id = kwargs.get('user_id', 0)
            self.transaction_number = f"TRX{timestamp}{user_id}{random_str}"

# 服务费模�?
class ServiceFee(db.Model):
    """服务费模�?""
    __tablename__ = 'service_fees'
    
    id = db.Column(db.Integer, primary_key=True)
    percentage = db.Column(db.Numeric(5, 2), nullable=False)  # 百分比，�?.00表示5%
    fixed_amount = db.Column(db.Numeric(10, 2), default=0)    # 固定金额部分
    description = db.Column(db.String(255))
    
    # 关联的交易（如果有）
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    transaction = db.relationship('Transaction', backref=db.backref('service_fee', uselist=False))
    
    # 时间记录
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 账单模型
class Invoice(db.Model):
    """发票模型"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), unique=True, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    
    # 发票接收人信�?
    recipient_name = db.Column(db.String(100))
    recipient_address = db.Column(db.String(255))
    recipient_email = db.Column(db.String(120))
    recipient_phone = db.Column(db.String(20))
    
    # 关联交易
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    transaction = db.relationship('Transaction', backref=db.backref('invoice', uselist=False))
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('invoices', lazy='dynamic'))
    
    # 时间记录
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 发票详情
    details = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Invoice, self).__init__(**kwargs)
        if not self.invoice_number:
            # 生成发票编号：INV + 年月�?+ 随机字符
            import random
            import string
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.invoice_number = f"INV{date_str}{random_str}"

# 退款模�?
class Refund(db.Model):
    """退款模�?""
    __tablename__ = 'refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    refund_number = db.Column(db.String(64), unique=True, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    reason = db.Column(db.Text)
    
    # 关联原始交易
    original_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    original_transaction = db.relationship('Transaction', foreign_keys=[original_transaction_id], 
                                         backref=db.backref('refund_requests', lazy='dynamic'))
    
    # 关联退款交易（如果已创建）
    refund_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    refund_transaction = db.relationship('Transaction', foreign_keys=[refund_transaction_id], 
                                       backref=db.backref('refund', uselist=False))
    
    # 关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('refunds', lazy='dynamic'))
    
    # 时间记录
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # 处理备注
    admin_note = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Refund, self).__init__(**kwargs)
        if not self.refund_number:
            # 生成退款编号：REF + 年月�?+ 随机字符
            import random
            import string
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.refund_number = f"REF{date_str}{random_str}"

# 争议处理模型
class Dispute(db.Model):
    """争议处理模型，处理交易纠�?""
    __tablename__ = 'disputes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, closed
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # 外键
    refund_id = db.Column(db.Integer, db.ForeignKey('refunds.id'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    complainant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    respondent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    resolver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 关系
    refund = db.relationship('Refund', backref=db.backref('dispute', uselist=False))
    transaction = db.relationship('Transaction', backref=db.backref('disputes', lazy='dynamic'))
    complainant = db.relationship('User', foreign_keys=[complainant_id], backref=db.backref('filed_disputes', lazy='dynamic'))
    respondent = db.relationship('User', foreign_keys=[respondent_id], backref=db.backref('received_disputes', lazy='dynamic'))
    resolver = db.relationship('User', foreign_keys=[resolver_id], backref=db.backref('resolved_disputes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Dispute {self.id}: {self.title} ({self.status})>'
    
    def resolve(self, resolver_id, resolution, status='resolved'):
        """解决争议
        
        Args:
            resolver_id: 解决者ID
            resolution: 解决方案
            status: 解决状�?(resolved, closed)
            
        Returns:
            bool: 操作是否成功
        """
        if self.status in ['resolved', 'closed']:
            return False
            
        self.resolver_id = resolver_id
        self.resolution = resolution
        self.status = status
        self.resolved_at = datetime.utcnow()
        return True 