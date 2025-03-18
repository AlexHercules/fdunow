from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Message, AnonymousChat, AnonymousChatMessage, GuidingQuestion, friendships
from datetime import datetime
from sqlalchemy import or_, and_
import random

# 创建蓝图
social_bp = Blueprint('social', __name__, url_prefix='/social')

# 社交首页
@social_bp.route('/')
@login_required
def index():
    # 获取用户的匿名聊天列表
    anonymous_chats = AnonymousChat.query.filter(
        or_(
            AnonymousChat.user1_id == current_user.id,
            AnonymousChat.user2_id == current_user.id
        )
    ).order_by(AnonymousChat.last_activity.desc()).all()
    
    # 获取用户的好友列表
    friends = db.session.query(User).join(
        friendships, 
        or_(
            and_(friendships.c.user_id == current_user.id, friendships.c.friend_id == User.id),
            and_(friendships.c.friend_id == current_user.id, friendships.c.user_id == User.id)
        )
    ).filter(friendships.c.status == 'accepted').all()
    
    return render_template('social/index.html',
                          title='社交中心',
                          anonymous_chats=anonymous_chats,
                          friends=friends)

# 开始新的匿名对话
@social_bp.route('/start_anonymous_chat', methods=['POST'])
@login_required
def start_anonymous_chat():
    # 在数据库中查找可配对的用户（排除已经是好友的用户和自己）
    friends_ids = db.session.query(friendships.c.friend_id).filter(
        friendships.c.user_id == current_user.id,
        friendships.c.status == 'accepted'
    ).all()
    
    friends_ids = [fid[0] for fid in friends_ids] + [current_user.id]
    
    # 查询当前没有与自己进行中的匿名聊天的用户
    current_chat_partners = db.session.query(
        AnonymousChat.user1_id if AnonymousChat.user2_id == current_user.id else AnonymousChat.user2_id
    ).filter(
        or_(
            AnonymousChat.user1_id == current_user.id,
            AnonymousChat.user2_id == current_user.id
        ),
        AnonymousChat.status == 'active'
    ).all()
    
    current_chat_partners = [p[0] for p in current_chat_partners]
    
    # 排除已经是聊天对象的用户
    excluded_ids = friends_ids + current_chat_partners
    
    # 查找符合条件的用户
    potential_users = User.query.filter(
        ~User.id.in_(excluded_ids)
    ).all()
    
    if not potential_users:
        flash('当前没有可匹配的用户，请稍后再试', 'info')
        return redirect(url_for('social.index'))
    
    # 随机选择一个用户
    matched_user = random.choice(potential_users)
    
    # 创建新的匿名聊天
    chat = AnonymousChat(
        user1_id=current_user.id,
        user2_id=matched_user.id,
        status='active',
        intimacy_level=1
    )
    
    db.session.add(chat)
    db.session.commit()
    
    # 获取一个初始引导问题
    guiding_question = GuidingQuestion.query.filter_by(intimacy_level=1).order_by(db.func.random()).first()
    
    if guiding_question:
        # 创建系统消息，显示引导问题
        system_message = AnonymousChatMessage(
            content=f"引导问题: {guiding_question.question}",
            is_from_user1=None,  # None表示系统消息
            chat_id=chat.id
        )
        db.session.add(system_message)
        db.session.commit()
    
    flash('匿名聊天已开始！', 'success')
    return redirect(url_for('social.anonymous_chat', chat_id=chat.id))

# 匿名聊天页面
@social_bp.route('/anonymous_chat/<int:chat_id>')
@login_required
def anonymous_chat(chat_id):
    chat = AnonymousChat.query.get_or_404(chat_id)
    
    # 验证用户是否是聊天参与者
    if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
        flash('您无权访问此聊天', 'danger')
        return redirect(url_for('social.index'))
    
    # 确定当前用户是user1还是user2
    is_user1 = (chat.user1_id == current_user.id)
    
    # 获取对话中的另一个用户
    partner_id = chat.user2_id if is_user1 else chat.user1_id
    partner = User.query.get(partner_id)
    
    # 获取聊天消息
    messages = AnonymousChatMessage.query.filter_by(chat_id=chat_id).order_by(AnonymousChatMessage.created_at).all()
    
    # 根据聊天的亲密度和状态决定显示多少对方信息
    partner_info = {
        'id': partner.id
    }
    
    # 根据亲密度逐步显示信息
    if chat.intimacy_level >= 2 or chat.status == 'revealed':
        partner_info['interests'] = partner.interests
    
    if chat.intimacy_level >= 3 or chat.status == 'revealed':
        partner_info['major'] = partner.major
        partner_info['grade'] = partner.grade
    
    if chat.intimacy_level >= 4 or chat.status == 'revealed':
        partner_info['bio'] = partner.bio
    
    if chat.status == 'revealed':
        partner_info['username'] = partner.username
        partner_info['name'] = partner.name
        partner_info['avatar'] = partner.avatar
    
    # 检查是否已是好友
    is_friend = db.session.query(friendships).filter(
        or_(
            and_(friendships.c.user_id == current_user.id, friendships.c.friend_id == partner_id),
            and_(friendships.c.friend_id == current_user.id, friendships.c.user_id == partner_id)
        ),
        friendships.c.status == 'accepted'
    ).first() is not None
    
    # 获取下一个引导问题（如果有）
    next_question = None
    if chat.status == 'active':
        next_question = GuidingQuestion.query.filter_by(intimacy_level=chat.intimacy_level).order_by(db.func.random()).first()
    
    return render_template('social/anonymous_chat.html',
                          title='匿名对话',
                          chat=chat,
                          messages=messages,
                          is_user1=is_user1,
                          partner_info=partner_info,
                          is_friend=is_friend,
                          next_question=next_question)

# 发送匿名消息
@social_bp.route('/send_anonymous_message/<int:chat_id>', methods=['POST'])
@login_required
def send_anonymous_message(chat_id):
    chat = AnonymousChat.query.get_or_404(chat_id)
    
    # 验证用户是否是聊天参与者
    if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
        return jsonify({'status': 'error', 'message': '您无权在此聊天中发送消息'})
    
    # 检查聊天是否已关闭
    if chat.status == 'closed':
        return jsonify({'status': 'error', 'message': '此聊天已关闭'})
    
    content = request.form.get('content')
    
    if not content:
        return jsonify({'status': 'error', 'message': '消息不能为空'})
    
    # 确定消息是来自user1还是user2
    is_from_user1 = (chat.user1_id == current_user.id)
    
    # 创建新消息
    message = AnonymousChatMessage(
        content=content,
        is_from_user1=is_from_user1,
        chat_id=chat_id
    )
    
    # 更新聊天的最后活动时间
    chat.last_activity = datetime.utcnow()
    
    db.session.add(message)
    db.session.commit()
    
    # 检查是否应该增加亲密度
    messages_count = AnonymousChatMessage.query.filter_by(
        chat_id=chat_id
    ).filter(
        AnonymousChatMessage.is_from_user1 != None  # 排除系统消息
    ).count()
    
    # 每交换10条消息，亲密度+1
    if messages_count % 10 == 0 and chat.intimacy_level < 5:
        chat.intimacy_level += 1
        db.session.commit()
        
        # 获取新的引导问题
        guiding_question = GuidingQuestion.query.filter_by(
            intimacy_level=chat.intimacy_level
        ).order_by(db.func.random()).first()
        
        if guiding_question:
            # 创建系统消息，显示新的引导问题
            system_message = AnonymousChatMessage(
                content=f"引导问题: {guiding_question.question}",
                is_from_user1=None,  # None表示系统消息
                chat_id=chat.id
            )
            db.session.add(system_message)
            db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '消息已发送',
        'intimacy_level': chat.intimacy_level
    })

# 揭示身份
@social_bp.route('/reveal_identity/<int:chat_id>', methods=['POST'])
@login_required
def reveal_identity(chat_id):
    chat = AnonymousChat.query.get_or_404(chat_id)
    
    # 验证用户是否是聊天参与者
    if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
        flash('您无权在此聊天中揭示身份', 'danger')
        return redirect(url_for('social.anonymous_chat', chat_id=chat_id))
    
    # 检查亲密度是否达到要求（至少3级）
    if chat.intimacy_level < 3 and chat.status == 'active':
        flash('需要更多互动才能揭示身份', 'warning')
        return redirect(url_for('social.anonymous_chat', chat_id=chat_id))
    
    # 更新聊天状态为已揭示
    chat.status = 'revealed'
    
    # 创建系统消息，通知双方身份已揭示
    system_message = AnonymousChatMessage(
        content=f"身份已揭示！现在你们可以看到对方的个人信息。",
        is_from_user1=None,  # None表示系统消息
        chat_id=chat.id
    )
    
    db.session.add(system_message)
    db.session.commit()
    
    flash('您已成功揭示身份！', 'success')
    return redirect(url_for('social.anonymous_chat', chat_id=chat_id))

# 添加好友
@social_bp.route('/add_friend/<int:user_id>', methods=['POST'])
@login_required
def add_friend(user_id):
    if user_id == current_user.id:
        flash('不能添加自己为好友', 'warning')
        return redirect(url_for('social.index'))
    
    # 检查用户是否存在
    user = User.query.get_or_404(user_id)
    
    # 检查是否已经是好友或有待处理的请求
    existing_friendship = db.session.query(friendships).filter(
        or_(
            and_(friendships.c.user_id == current_user.id, friendships.c.friend_id == user_id),
            and_(friendships.c.friend_id == current_user.id, friendships.c.user_id == user_id)
        )
    ).first()
    
    if existing_friendship:
        status = existing_friendship.status
        if status == 'accepted':
            flash('你们已经是好友了', 'info')
        elif status == 'pending':
            flash('好友请求已发送，等待对方接受', 'info')
        return redirect(url_for('social.view_profile', user_id=user_id))
    
    # 添加好友关系（待接受）
    stmt = friendships.insert().values(
        user_id=current_user.id,
        friend_id=user_id,
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.execute(stmt)
    db.session.commit()
    
    # 创建通知消息
    message = Message(
        content=f"{current_user.username}请求添加您为好友",
        sender_id=current_user.id,
        recipient_id=user_id,
        is_anonymous=False
    )
    db.session.add(message)
    db.session.commit()
    
    flash('好友请求已发送', 'success')
    return redirect(url_for('social.view_profile', user_id=user_id))

# 接受好友请求
@social_bp.route('/accept_friend/<int:user_id>', methods=['POST'])
@login_required
def accept_friend(user_id):
    # 查找好友请求
    friendship = db.session.query(friendships).filter(
        friendships.c.user_id == user_id,
        friendships.c.friend_id == current_user.id,
        friendships.c.status == 'pending'
    ).first()
    
    if not friendship:
        flash('没有找到待处理的好友请求', 'warning')
        return redirect(url_for('social.index'))
    
    # 更新好友状态为已接受
    stmt = friendships.update().where(
        friendships.c.user_id == user_id,
        friendships.c.friend_id == current_user.id
    ).values(status='accepted')
    db.session.execute(stmt)
    
    # 创建通知消息
    message = Message(
        content=f"{current_user.username}已接受您的好友请求",
        sender_id=current_user.id,
        recipient_id=user_id,
        is_anonymous=False
    )
    db.session.add(message)
    db.session.commit()
    
    flash('已接受好友请求', 'success')
    return redirect(url_for('social.index'))

# 拒绝好友请求
@social_bp.route('/reject_friend/<int:user_id>', methods=['POST'])
@login_required
def reject_friend(user_id):
    # 查找好友请求
    friendship = db.session.query(friendships).filter(
        friendships.c.user_id == user_id,
        friendships.c.friend_id == current_user.id,
        friendships.c.status == 'pending'
    ).first()
    
    if not friendship:
        flash('没有找到待处理的好友请求', 'warning')
        return redirect(url_for('social.index'))
    
    # 删除好友请求
    stmt = friendships.delete().where(
        friendships.c.user_id == user_id,
        friendships.c.friend_id == current_user.id
    )
    db.session.execute(stmt)
    db.session.commit()
    
    flash('已拒绝好友请求', 'success')
    return redirect(url_for('social.index'))

# 结束聊天
@social_bp.route('/close_chat/<int:chat_id>', methods=['POST'])
@login_required
def close_chat(chat_id):
    chat = AnonymousChat.query.get_or_404(chat_id)
    
    # 验证用户是否是聊天参与者
    if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
        flash('您无权结束此聊天', 'danger')
        return redirect(url_for('social.index'))
    
    # 更新聊天状态为已关闭
    chat.status = 'closed'
    
    # 创建系统消息，通知双方聊天已结束
    system_message = AnonymousChatMessage(
        content=f"聊天已结束。",
        is_from_user1=None,  # None表示系统消息
        chat_id=chat.id
    )
    
    db.session.add(system_message)
    db.session.commit()
    
    flash('聊天已结束', 'success')
    return redirect(url_for('social.index'))

# 查看用户资料
@social_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # 检查是否是好友
    is_friend = db.session.query(friendships).filter(
        or_(
            and_(friendships.c.user_id == current_user.id, friendships.c.friend_id == user_id),
            and_(friendships.c.friend_id == current_user.id, friendships.c.user_id == user_id)
        ),
        friendships.c.status == 'accepted'
    ).first() is not None
    
    # 检查是否有待处理的好友请求
    pending_request = db.session.query(friendships).filter(
        friendships.c.user_id == user_id,
        friendships.c.friend_id == current_user.id,
        friendships.c.status == 'pending'
    ).first() is not None
    
    # 检查是否已发送好友请求
    sent_request = db.session.query(friendships).filter(
        friendships.c.user_id == current_user.id,
        friendships.c.friend_id == user_id,
        friendships.c.status == 'pending'
    ).first() is not None
    
    return render_template('social/profile.html',
                          title=f"{user.username}的资料",
                          user=user,
                          is_friend=is_friend,
                          pending_request=pending_request,
                          sent_request=sent_request)

# 好友列表页面
@social_bp.route('/friends')
@login_required
def friends_list():
    # 获取用户的好友列表
    friends = db.session.query(User).join(
        friendships, 
        or_(
            and_(friendships.c.user_id == current_user.id, friendships.c.friend_id == User.id),
            and_(friendships.c.friend_id == current_user.id, friendships.c.user_id == User.id)
        )
    ).filter(friendships.c.status == 'accepted').all()
    
    # 获取待处理的好友请求
    pending_requests = db.session.query(User).join(
        friendships,
        friendships.c.user_id == User.id
    ).filter(
        friendships.c.friend_id == current_user.id,
        friendships.c.status == 'pending'
    ).all()
    
    # 获取已发送的好友请求
    sent_requests = db.session.query(User).join(
        friendships,
        friendships.c.friend_id == User.id
    ).filter(
        friendships.c.user_id == current_user.id,
        friendships.c.status == 'pending'
    ).all()
    
    return render_template('social/friends.html',
                          title='我的好友',
                          friends=friends,
                          pending_requests=pending_requests,
                          sent_requests=sent_requests)

# 消息中心
@social_bp.route('/messages')
@login_required
def messages():
    # 获取收到的消息
    received_messages = Message.query.filter_by(
        recipient_id=current_user.id
    ).order_by(Message.created_at.desc()).all()
    
    # 标记所有消息为已读
    for message in received_messages:
        if not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    return render_template('social/messages.html',
                          title='消息中心',
                          messages=received_messages) 