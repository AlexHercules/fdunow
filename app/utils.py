import os
from flask import current_app, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from application import db

def allowed_file(filename, allowed_extensions=None):
    """
    检查文件类型是否允许上传
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表，默认为图片格式
    
    Returns:
        bool: 文件是否允许上传
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder, prefix='', allowed_extensions=None):
    """
    保存文件到指定目录
    
    Args:
        file: 文件对象
        folder: 保存的子文件夹名称
        prefix: 文件名前缀
        allowed_extensions: 允许的文件扩展名
    
    Returns:
        str: 保存后的文件路径(相对于静态文件夹)，失败返回None
    """
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename, allowed_extensions):
        return None
    
    # 确保文件名安全
    filename = secure_filename(file.filename)
    
    # 生成唯一文件名
    unique_filename = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    
    # 设置保存路径
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    file_path = os.path.join(upload_folder, folder, unique_filename)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        # 保存文件
        file.save(file_path)
        # 返回相对路径
        return os.path.join('uploads', folder, unique_filename)
    except Exception as e:
        current_app.logger.error(f"文件保存失败: {str(e)}")
        return None

def safe_transaction(func):
    """
    数据库事务装饰器，自动处理提交和回滚
    
    Args:
        func: 要装饰的函数
    
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"数据库事务失败: {str(e)}")
            flash('操作失败，请稍后重试', 'danger')
            return False
    return wrapper

def permission_required(permission):
    """
    权限检查装饰器
    
    Args:
        permission: 需要的权限
    
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            if not current_user.has_permission(permission):
                flash('你没有权限执行此操作', 'danger')
                return current_app.login_manager.unauthorized()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def resource_permission_required(permission_check_function):
    """
    资源权限检查装饰器，用于检查用户对特定资源的权限
    
    Args:
        permission_check_function: 一个函数，接受request和资源ID，返回布尔值表示是否有权限
    
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            # 如果用户是管理员，直接允许访问
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # 检查用户对特定资源的权限
            if not permission_check_function(request, **kwargs):
                flash('你没有权限访问此资源', 'danger')
                return current_app.login_manager.unauthorized()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(role_name):
    """
    角色检查装饰器
    
    Args:
        role_name: 需要的角色名称，可以是字符串或角色名列表
    
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            # 如果提供的是单个角色名
            if isinstance(role_name, str):
                if not current_user.has_role(role_name):
                    flash(f'需要 {role_name} 角色才能访问', 'danger')
                    return current_app.login_manager.unauthorized()
            # 如果提供的是角色名列表（满足其一即可）
            elif isinstance(role_name, (list, tuple)):
                if not any(current_user.has_role(role) for role in role_name):
                    roles_str = ', '.join(role_name)
                    flash(f'需要以下角色之一才能访问: {roles_str}', 'danger')
                    return current_app.login_manager.unauthorized()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def safe_html(text):
    """
    清理HTML内容，防止XSS攻击
    
    Args:
        text: 要清理的文本
    
    Returns:
        清理后的安全HTML
    """
    try:
        import bleach
        allowed_tags = ['p', 'b', 'i', 'u', 'a', 'h1', 'h2', 'h3', 'br', 'ul', 'ol', 'li', 'code', 'pre']
        allowed_attrs = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt']
        }
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    except ImportError:
        # 如果没有安装bleach，则返回纯文本
        import html
        return html.escape(text)

def paginate(query, page, per_page=20):
    """
    查询分页助手函数
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码
        per_page: 每页条数
    
    Returns:
        分页对象
    """
    return query.paginate(page=page, per_page=per_page)

# 个性化推荐服务
class RecommendationService:
    """提供个性化推荐功能的服务类"""
    
    @staticmethod
    def get_project_recommendations(user, limit=5):
        """
        为用户推荐项目
        
        Args:
            user: 用户对象
            limit: 推荐数量
        
        Returns:
            推荐项目列表
        """
        from models import CrowdfundingProject, User
        from sqlalchemy import func
        
        # 基于用户兴趣的推荐
        user_interests = user.interests.split(',') if user.interests else []
        
        recommended_projects = []
        
        if user_interests:
            # 查找包含用户兴趣关键词的项目
            interest_projects = CrowdfundingProject.query.filter(
                CrowdfundingProject.tags.like(func.concat('%', func.any_(user_interests), '%'))
            ).limit(limit).all()
            
            recommended_projects.extend(interest_projects)
        
        # 如果通过兴趣没有找到足够多的项目，则基于用户的专业补充推荐
        if len(recommended_projects) < limit and user.department and user.major:
            # 查找同专业用户创建的项目
            major_projects = CrowdfundingProject.query.join(
                User, CrowdfundingProject.creator_id == User.id
            ).filter(
                User.department == user.department,
                User.major == user.major,
                ~CrowdfundingProject.id.in_([p.id for p in recommended_projects])
            ).limit(limit - len(recommended_projects)).all()
            
            recommended_projects.extend(major_projects)
        
        # 如果仍然不够，则添加最热门的项目
        if len(recommended_projects) < limit:
            # 查找最热门的项目（根据支持人数）
            popular_projects = CrowdfundingProject.query.filter(
                ~CrowdfundingProject.id.in_([p.id for p in recommended_projects])
            ).order_by(
                CrowdfundingProject.supporters_count.desc()
            ).limit(limit - len(recommended_projects)).all()
            
            recommended_projects.extend(popular_projects)
        
        return recommended_projects
    
    @staticmethod
    def get_team_recommendations(user, limit=5):
        """
        为用户推荐团队
        
        Args:
            user: 用户对象
            limit: 推荐数量
        
        Returns:
            推荐团队列表
        """
        from models import Team, User
        from sqlalchemy import func
        
        # 基于用户技能的推荐
        user_skills = user.skills.split(',') if user.skills else []
        
        recommended_teams = []
        
        if user_skills:
            # 查找需要用户技能的团队
            skills_teams = Team.query.filter(
                Team.required_skills.like(func.concat('%', func.any_(user_skills), '%'))
            ).limit(limit).all()
            
            recommended_teams.extend(skills_teams)
        
        # 如果通过技能没有找到足够多的团队，则基于用户的专业补充推荐
        if len(recommended_teams) < limit and user.department and user.major:
            # 查找同专业用户创建的团队
            major_teams = Team.query.join(
                User, Team.creator_id == User.id
            ).filter(
                User.department == user.department,
                User.major == user.major,
                ~Team.id.in_([t.id for t in recommended_teams])
            ).limit(limit - len(recommended_teams)).all()
            
            recommended_teams.extend(major_teams)
        
        # 如果仍然不够，则添加最新创建的团队
        if len(recommended_teams) < limit:
            # 查找最新创建的团队
            recent_teams = Team.query.filter(
                ~Team.id.in_([t.id for t in recommended_teams])
            ).order_by(
                Team.created_at.desc()
            ).limit(limit - len(recommended_teams)).all()
            
            recommended_teams.extend(recent_teams)
        
        return recommended_teams
    
    @staticmethod
    def get_forum_topic_recommendations(user, limit=5):
        """
        为用户推荐论坛主题
        
        Args:
            user: 用户对象
            limit: 推荐数量
        
        Returns:
            推荐主题列表
        """
        from models import ForumTopic, ForumCategory, TopicLike
        
        recommended_topics = []
        
        # 基于用户点赞历史的推荐
        liked_categories = db.session.query(
            ForumCategory.id
        ).join(
            ForumTopic, ForumTopic.category_id == ForumCategory.id
        ).join(
            TopicLike, TopicLike.topic_id == ForumTopic.id
        ).filter(
            TopicLike.user_id == user.id
        ).group_by(
            ForumCategory.id
        ).all()
        
        if liked_categories:
            # 查找用户喜欢的分类中的热门主题
            liked_category_ids = [c[0] for c in liked_categories]
            popular_topics = ForumTopic.query.filter(
                ForumTopic.category_id.in_(liked_category_ids),
                ForumTopic.is_hidden == False,
                ~ForumTopic.id.in_([t.id for t in user.topic_likes.with_entities(TopicLike.topic_id).all()])
            ).order_by(
                ForumTopic.likes_count.desc()
            ).limit(limit).all()
            
            recommended_topics.extend(popular_topics)
        
        # 如果仍然不够，则添加最热门的主题
        if len(recommended_topics) < limit:
            # 查找最热门的主题
            popular_topics = ForumTopic.query.filter(
                ForumTopic.is_hidden == False,
                ~ForumTopic.id.in_([t.id for t in recommended_topics])
            ).order_by(
                ForumTopic.likes_count.desc()
            ).limit(limit - len(recommended_topics)).all()
            
            recommended_topics.extend(popular_topics)
        
        return recommended_topics 