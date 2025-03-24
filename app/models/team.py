"""
团队相关数据模型
"""

from datetime import datetime
from app.extensions import db

class Team(db.Model):
    """团队模型"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    description = db.Column(db.Text)
    logo = db.Column(db.String(255))
    status = db.Column(db.String(20), default='recruiting')  # recruiting, active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    # 关联
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    requirements = db.relationship('TeamRequirement', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def member_count(self):
        """获取团队成员数量"""
        return self.members.filter_by(status='accepted').count()
    
    @property
    def active_requirements(self):
        """获取团队当前有效的需求"""
        return self.requirements.filter_by(status='open').all()
    
    def add_member(self, user, role='member'):
        """添加团队成员"""
        if self.members.filter_by(user_id=user.id).first():
            return False
        
        member = TeamMember(user_id=user.id, team_id=self.id, role=role, status='accepted')
        db.session.add(member)
        return True
    
    def remove_member(self, user):
        """移除团队成员"""
        member = self.members.filter_by(user_id=user.id).first()
        if member:
            db.session.delete(member)
            return True
        return False
    
    def __repr__(self):
        return f'<Team {self.name}>'

class TeamMember(db.Model):
    """团队成员模型"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(64))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<TeamMember {self.id}>'

class TeamRequirement(db.Model):
    """团队招募需求模型"""
    __tablename__ = 'team_requirements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    skills_required = db.Column(db.String(255))
    number_needed = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='open')  # open, closed, filled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'))
    
    def __repr__(self):
        return f'<TeamRequirement {self.title}>' 