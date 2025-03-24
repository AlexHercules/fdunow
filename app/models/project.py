"""
众筹项目相关数据模型
"""

from datetime import datetime
from app.extensions import db

class ProjectCategory(db.Model):
    """项目类别模型"""
    __tablename__ = 'project_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    description = db.Column(db.String(255))
    projects = db.relationship('Project', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProjectCategory {self.name}>'
    
    @staticmethod
    def insert_categories():
        """插入默认项目类别"""
        categories = {
            '科技创新': '包括软件开发、硬件创新、人工智能等技术领域的创新项目',
            '文化艺术': '包括校园文化、艺术创作、传统文化传承等项目',
            '公益服务': '以服务校园和社会为目的的公益性项目',
            '创业孵化': '具有商业前景的创业项目',
            '学术研究': '各学科领域的学术研究项目',
            '校园生活': '改善校园生活、提升学生体验的项目',
            '体育竞技': '体育赛事、健身活动等相关项目',
            '环保可持续': '关注环境保护和可持续发展的项目',
            '其他': '不属于以上类别的其他创新项目'
        }
        
        for name, description in categories.items():
            category = ProjectCategory.query.filter_by(name=name).first()
            if category is None:
                category = ProjectCategory(name=name, description=description)
                db.session.add(category)
        
        db.session.commit()

class Project(db.Model):
    """众筹项目模型"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    details = db.Column(db.Text)
    target_amount = db.Column(db.Float)
    current_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    cover_image = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('project_categories.id'))
    
    # 关联
    updates = db.relationship('ProjectUpdate', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('ProjectComment', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    # 新增关联
    payments = db.relationship('Payment', backref='project', lazy='dynamic')
    rewards = db.relationship('ProjectReward', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    team = db.relationship('Team', backref='project', uselist=False)
    
    @property
    def progress_percentage(self):
        """计算项目筹款进度百分比"""
        if self.target_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.target_amount) * 100))
    
    @property
    def days_left(self):
        """计算剩余天数"""
        if not self.end_date:
            return 0
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_expired(self):
        """检查项目是否已过期"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date
    
    @property
    def supporter_count(self):
        """获取支持者数量"""
        return self.payments.filter_by(status='success').count()
    
    @property
    def is_successful(self):
        """判断项目是否筹款成功"""
        if self.is_expired:
            return self.current_amount >= self.target_amount
        return False
    
    def add_payment(self, payment):
        """添加支付记录并更新筹款金额"""
        if payment.status == 'success':
            self.current_amount += payment.amount
            
            # 更新项目状态
            if self.current_amount >= self.target_amount:
                self.status = 'completed'
                
            db.session.add(self)
        
    def refund_payment(self, payment):
        """退款并更新筹款金额"""
        if payment.status == 'success':
            self.current_amount = max(0, self.current_amount - payment.amount)
            db.session.add(self)
    
    def __repr__(self):
        return f'<Project {self.title}>'

class ProjectUpdate(db.Model):
    """项目更新模型"""
    __tablename__ = 'project_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<ProjectUpdate {self.id} - {self.title}>'

class ProjectComment(db.Model):
    """项目评论模型"""
    __tablename__ = 'project_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('project_comments.id', ondelete='SET NULL'), nullable=True)
    
    # 关联
    replies = db.relationship('ProjectComment', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProjectComment {self.id}>' 