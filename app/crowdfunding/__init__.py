"""
众筹项目模块初始化
"""

from flask import Blueprint

# 创建众筹蓝图
crowdfunding_bp = Blueprint('crowdfunding', __name__)

# 延迟导入路由，避免循环导入
def init_crowdfunding():
    """初始化众筹模块，返回蓝图"""
    from app.crowdfunding import routes
    return crowdfunding_bp

__all__ = ['crowdfunding_bp', 'init_crowdfunding'] 