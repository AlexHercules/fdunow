from flask import Blueprint, render_template, jsonify, request, current_app
import traceback
import sys

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def page_not_found(e):
    """处理404错误"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='页面未找�?), 404
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def forbidden(e):
    """处理403错误"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='权限不足'), 403
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def internal_server_error(e):
    """处理500错误"""
    # 记录详细错误信息
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
    current_app.logger.error('服务器错�? %s', ''.join(error_details))
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='服务器错�?), 500
    return render_template('errors/500.html'), 500

@errors.app_errorhandler(400)
def bad_request(e):
    """处理400错误"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='错误的请�?), 400
    return render_template('errors/400.html'), 400

@errors.app_errorhandler(405)
def method_not_allowed(e):
    """处理405错误"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='方法不允�?), 405
    return render_template('errors/405.html'), 405

@errors.app_errorhandler(429)
def too_many_requests(e):
    """处理429错误"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='请求过于频繁，请稍后再试'), 429
    return render_template('errors/429.html'), 429

def handle_exception(e):
    """处理未捕获的异常"""
    # 记录错误信息
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
    current_app.logger.error('未捕获异�? %s', ''.join(error_details))
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error='服务器内部错�?), 500
    return render_template('errors/500.html'), 500

def register_error_handlers(app):
    """注册错误处理�?""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """处理404错误 - 页面未找�?""
        current_app.logger.info(f"404错误: {error}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """处理403错误 - 禁止访问"""
        current_app.logger.warning(f"403错误: {error}")
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误 - 服务器内部错�?""
        current_app.logger.error(f"500错误: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """处理400错误 - 错误的请�?""
        current_app.logger.warning(f"400错误: {error}")
        return render_template('errors/500.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """处理401错误 - 未授权访�?""
        current_app.logger.warning(f"401错误: {error}")
        return render_template('errors/403.html'), 401

    app.register_blueprint(errors)
    app.register_error_handler(Exception, handle_exception) 