"""团队模块"""

from flask import Blueprint

# 创建团队蓝图
team_bp = Blueprint('team', __name__)

# 延迟导入路由，避免循环导入
def init_team():
    """初始化团队模块，返回蓝图"""
    from app.team import routes
    return team_bp

__all__ = ['team_bp', 'init_team'] 