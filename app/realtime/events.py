from flask import request, session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from application import socketio, db
from models import User, Message, ChatGroup

@socketio.on('connect')
def handle_connect():
    """处理连接事件"""
    if not current_user.is_authenticated:
        return False
    
    # 将用户加入自己的私人频道
    join_room(f'user_{current_user.id}')
    
    # 更新用户在线状态
    current_user.is_online = True
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    
    # 通知好友上线
    for friend in current_user.friends:
        emit('user_status', {
            'user_id': current_user.id,
            'status': 'online',
            'username': current_user.username,
            'avatar': current_user.avatar
        }, room=f'user_{friend.id}')
    
    return True

@socketio.on('disconnect')
def handle_disconnect():
    """处理断开连接事件"""
    if not current_user.is_authenticated:
        return
    
    # 更新用户离线状态
    current_user.is_online = False
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    
    # 通知好友离线
    for friend in current_user.friends:
        emit('user_status', {
            'user_id': current_user.id,
            'status': 'offline',
            'username': current_user.username,
            'last_seen': current_user.last_seen.isoformat()
        }, room=f'user_{friend.id}')

@socketio.on('private_message')
def handle_private_message(data):
    """处理私聊消息"""
    if not current_user.is_authenticated:
        return False
    
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content:
        return False
    
    recipient = User.query.get(recipient_id)
    if not recipient:
        return False
    
    # 创建消息记录
    message = Message(
        content=content,
        sender_id=current_user.id,
        target_type='user',
        target_id=recipient_id,
        is_read=False
    )
    db.session.add(message)
    db.session.commit()
    
    # 发送给接收者
    emit('new_private_message', {
        'message_id': message.id,
        'sender_id': current_user.id,
        'sender_name': current_user.username,
        'sender_avatar': current_user.avatar,
        'content': content,
        'created_at': message.created_at.isoformat()
    }, room=f'user_{recipient_id}')
    
    # 发送给发送者（确认消息已发送）
    emit('message_sent', {
        'message_id': message.id,
        'recipient_id': recipient_id,
        'content': content,
        'created_at': message.created_at.isoformat()
    })
    
    return True

@socketio.on('group_message')
def handle_group_message(data):
    """处理群聊消息"""
    if not current_user.is_authenticated:
        return False
    
    group_id = data.get('group_id')
    content = data.get('content')
    
    if not group_id or not content:
        return False
    
    group = ChatGroup.query.get(group_id)
    if not group or not group.is_member(current_user):
        return False
    
    # 创建群消息
    message = Message(
        content=content,
        sender_id=current_user.id,
        target_type='group',
        target_id=group_id
    )
    db.session.add(message)
    db.session.commit()
    
    # 发送给群组所有成员
    emit('new_group_message', {
        'message_id': message.id,
        'group_id': group_id,
        'sender_id': current_user.id,
        'sender_name': current_user.username,
        'sender_avatar': current_user.avatar,
        'content': content,
        'created_at': message.created_at.isoformat()
    }, room=f'group_{group_id}')
    
    return True

@socketio.on('join_group')
def handle_join_group(data):
    """加入群聊频道"""
    if not current_user.is_authenticated:
        return False
    
    group_id = data.get('group_id')
    if not group_id:
        return False
    
    group = ChatGroup.query.get(group_id)
    if not group or not group.is_member(current_user):
        return False
    
    join_room(f'group_{group_id}')
    return True

@socketio.on('leave_group')
def handle_leave_group(data):
    """离开群聊频道"""
    group_id = data.get('group_id')
    if not group_id:
        return False
    
    leave_room(f'group_{group_id}')
    return True

@socketio.on('read_message')
def handle_read_message(data):
    """标记消息为已读"""
    if not current_user.is_authenticated:
        return False
    
    message_id = data.get('message_id')
    if not message_id:
        return False
    
    message = Message.query.get(message_id)
    if not message or message.target_type != 'user' or message.target_id != current_user.id:
        return False
    
    message.is_read = True
    db.session.commit()
    
    # 通知发送者消息已读
    emit('message_read', {
        'message_id': message_id
    }, room=f'user_{message.sender_id}')
    
    return True

@socketio.on('read_all_messages')
def handle_read_all_messages(data):
    """标记与某用户的所有消息为已读"""
    if not current_user.is_authenticated:
        return False
    
    sender_id = data.get('sender_id')
    if not sender_id:
        return False
    
    # 更新所有未读消息
    Message.mark_as_read(current_user.id, sender_id)
    
    return True 