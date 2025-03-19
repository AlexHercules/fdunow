"""
测试Flask应用的主要功能
"""
import pytest
from app import app

@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        yield client

def test_index(client):
    """测试首页是否正常访问"""
    response = client.get('/')
    assert response.status_code == 200

def test_error_404(client):
    """测试404错误处理"""
    response = client.get('/non_existent_page')
    assert response.status_code == 404  # 只检查状态码，不检查内容 