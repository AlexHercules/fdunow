"""主页模块初始化"""

from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.main import routes

__all__ = ['main_bp'] 