"""
测试数据模型
"""
import pytest
from application import app
from models import db, User, Project, Team, ProjectCategory, TeamType
from flask import Flask

@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        db.session.remove()
        db.drop_all()

def test_user_model(client):
    """测试用户模型的基本功能"""
    # 创建测试用户
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # 查询并验证
    saved_user = User.query.filter_by(username='testuser').first()
    assert saved_user is not None
    assert saved_user.email == 'test@example.com'
    assert saved_user.check_password('password123') == True
    assert saved_user.check_password('wrongpassword') == False

def test_project_model(client):
    """测试项目模型的基本功能"""
    # 创建测试用户
    user = User(username='projectcreator', email='creator@example.com')
    db.session.add(user)
    db.session.flush()
    
    # 创建测试项目
    project = Project(
        title="测试项目",
        description="这是一个测试项目",
        category=ProjectCategory.TECH,
        target_amount=1000.0,
        creator_id=user.id
    )
    db.session.add(project)
    db.session.commit()
    
    # 查询并验证
    saved_project = Project.query.filter_by(title="测试项目").first()
    assert saved_project is not None
    assert saved_project.description == "这是一个测试项目"
    assert saved_project.category == ProjectCategory.TECH
    assert saved_project.creator_id == user.id

def test_team_model(client):
    """测试团队模型的基本功能"""
    # 创建测试用户
    user = User(username='teamcreator', email='teamcreator@example.com')
    db.session.add(user)
    db.session.flush()
    
    # 创建测试团队
    team = Team(
        name="测试团队",
        description="这是一个测试团队",
        team_type=TeamType.PROJECT,
        max_members=5,
        creator_id=user.id
    )
    db.session.add(team)
    db.session.commit()
    
    # 查询并验证
    saved_team = Team.query.filter_by(name="测试团队").first()
    assert saved_team is not None
    assert saved_team.description == "这是一个测试团队"
    assert saved_team.team_type == TeamType.PROJECT
    assert saved_team.creator_id == user.id 