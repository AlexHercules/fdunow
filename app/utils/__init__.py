"""工具包初始化"""

def pagination_dict(pagination, endpoint, **kwargs):
    """
    将SQLAlchemy分页对象转换为字典，包含分页信息
    
    :param pagination: SQLAlchemy分页对象
    :param endpoint: 当前路由端点
    :param kwargs: 额外参数
    :return: 包含分页信息的字典
    """
    data = {
        'items': pagination.items,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'next_num': pagination.next_num if pagination.has_next else None,
        'prev_num': pagination.prev_num if pagination.has_prev else None,
    }
    
    return data

def get_client_ip():
    """
    获取客户端IP地址
    
    :return: IP地址字符串
    """
    from flask import request
    
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    
    return ip

__all__ = ['pagination_dict', 'get_client_ip'] 