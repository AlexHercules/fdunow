"""支付模块"""

from flask import Blueprint

# 创建支付蓝图
payment_bp = Blueprint('payment', __name__)

# 延迟导入路由，避免循环导入
def init_payment():
    """初始化支付模块，返回蓝图"""
    from app.payment import routes
    return payment_bp

__all__ = ['payment_bp', 'init_payment'] 