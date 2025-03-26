"""错误处理模块初始化"""

from flask import render_template

def register_error_handlers(app):
    """注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def page_not_found(e):
        """404错误处理"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """500错误处理"""
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        """403错误处理"""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request(e):
        """400错误处理"""
        return render_template('errors/400.html'), 400 