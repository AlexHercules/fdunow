"""
后台管理模块初始化
"""

from flask import Blueprint

# 创建后台管理蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 延迟导入路由，避免循环导入
def init_admin():
    """初始化后台管理模块，返回蓝图"""
    from app.admin import routes
    return admin_bp

__all__ = ['admin_bp', 'init_admin'] 