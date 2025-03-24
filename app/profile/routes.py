from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from application import db
from app.utils import save_file, safe_transaction, permission_required, safe_html
from models import User, Team, CrowdfundingProject, FriendRequest, ChatGroup, GroupMessage, Message

profile = Blueprint('profile', __name__)

@profile.route('/')
@login_required
def index():
    """个人中心首页"""
    # 获取用户创建的项�?
    created_projects = current_user.created_projects.all()
    
    # 获取用户支持的项�?
    donations = current_user.donations.all()
    supported_projects = [donation.project for donation in donations]
    
    # 获取用户的团�?
    teams = current_user.teams.all()
    
    # 获取用户的好�?
    friends = current_user.friends
    
    # 获取用户创建的群�?
    created_groups = current_user.created_groups.all()
    
    # 获取用户加入的群�?
    joined_groups = current_user.groups.all()
    
    return render_template(
        'profile/index.html',
        created_projects=created_projects,
        supported_projects=supported_projects,
        teams=teams,
        friends=friends,
        created_groups=created_groups,
        joined_groups=joined_groups
    )

@profile.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """编辑个人资料"""
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        bio = request.form.get('bio')
        department = request.form.get('department')
        major = request.form.get('major')
        grade = request.form.get('grade')
        skills = request.form.get('skills')
        interests = request.form.get('interests')
        phone = request.form.get('phone')
        personal_website = request.form.get('personal_website')
        github = request.form.get('github')
        
        # 处理隐私设置
        email_visibility = request.form.get('email_visibility', 'public')
        phone_visibility = request.form.get('phone_visibility', 'private')
        project_visibility = request.form.get('project_visibility', 'public')
        
        # 处理头像上传
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            avatar_path = save_file(
                file=avatar_file,
                folder='avatars',
                prefix=str(current_user.id)
            )
            if avatar_path:
                current_user.avatar = avatar_path
        
        # 更新用户资料
        current_user.name = name
        current_user.bio = safe_html(bio) if bio else None
        current_user.department = department
        current_user.major = major
        current_user.grade = grade
        current_user.skills = skills
        current_user.interests = interests
        current_user.phone = phone
        current_user.personal_website = personal_website
        current_user.github = github
        
        # 更新隐私设置
        current_user.email_visibility = email_visibility
        current_user.phone_visibility = phone_visibility
        current_user.project_visibility = project_visibility
        
        # 保存到数据库
        try:
            db.session.commit()
            flash('个人资料已更�?, 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户资料失败: {str(e)}")
            flash('更新资料失败，请稍后重试', 'danger')
        
        return redirect(url_for('profile.index'))
    
    return render_template('profile/edit.html')

@profile.route('/projects')
@login_required
def projects():
    """我的众筹项目"""
    my_projects = CrowdfundingProject.query.filter_by(creator_id=current_user.id).all()
    supported_projects = current_user.donations.with_entities(
        CrowdfundingProject
    ).join(CrowdfundingProject).distinct().all()
    
    return render_template('profile/projects.html', 
                          my_projects=my_projects,
                          supported_projects=supported_projects)

@profile.route('/teams')
@login_required
def teams():
    """我的团队"""
    created_teams = Team.query.filter_by(creator_id=current_user.id).all()
    joined_teams = current_user.teams.all()
    
    return render_template('profile/teams.html', 
                          created_teams=created_teams,
                          joined_teams=joined_teams)

# 社交网络相关路由
@profile.route('/friends')
@login_required
def friends():
    """我的好友"""
    friends_list = current_user.friends.all()
    pending_requests = FriendRequest.query.filter_by(to_user_id=current_user.id, status='pending').all()
    
    return render_template('profile/friends.html', 
                          friends=friends_list,
                          pending_requests=pending_requests)

@profile.route('/friend/request/<int:user_id>', methods=['POST'])
@login_required
@safe_transaction
def send_friend_request(user_id):
    """发送好友请�?""
    # 检查目标用户是否存�?
    user = User.query.get_or_404(user_id)
    
    # 检查是否向自己发送请�?
    if user.id == current_user.id:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='不能向自己发送好友请�?)
        flash('不能向自己发送好友请�?, 'danger')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查是否已经是好友
    if current_user.is_friend(user):
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='你们已经是好友了')
        flash('你们已经是好友了', 'info')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查是否已发送过请求
    if current_user.has_sent_request_to(user):
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='已经发送过好友请求，等待对方回�?)
        flash('已经发送过好友请求，等待对方回�?, 'info')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查对方是否已经发送请求给自己
    if current_user.has_received_request_from(user):
        # 如果对方已经发送请求，则自动接�?
        reverse_request = FriendRequest.query.filter_by(
            sender_id=user_id,
            receiver_id=current_user.id,
            status='pending'
        ).first()
        
        reverse_request.status = 'accepted'
        db.session.commit()
        
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=True, message='已成为好�?)
        flash(f'你与 {user.username} 已成为好�?, 'success')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 创建新的好友请求
    message = request.form.get('message', '')
    friend_request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=user_id,
        message=message,
        status='pending'
    )
    
    db.session.add(friend_request)
    
    if request.content_type and 'application/json' in request.content_type:
        return jsonify(success=True, message='好友请求已发�?)
    
    flash(f'已向 {user.username} 发送好友请�?, 'success')
    return redirect(url_for('user.detail', user_id=user_id))

@profile.route('/friend/accept/<int:request_id>', methods=['POST'])
@login_required
@safe_transaction
def accept_friend_request(request_id):
    """接受好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否发给当前用户
    if friend_request.receiver_id != current_user.id:
        flash('无权处理此请�?, 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状�?
    if friend_request.status != 'pending':
        flash('该请求已处理', 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 更新请求状�?
    friend_request.status = 'accepted'
    
    # 获取发送者信�?
    sender = User.query.get(friend_request.sender_id)
    
    flash(f'你已接受 {sender.username} 的好友请�?, 'success')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/reject/<int:request_id>', methods=['POST'])
@login_required
@safe_transaction
def reject_friend_request(request_id):
    """拒绝好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否发给当前用户
    if friend_request.receiver_id != current_user.id:
        flash('无权处理此请�?, 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状�?
    if friend_request.status != 'pending':
        flash('该请求已处理', 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 更新请求状�?
    friend_request.status = 'rejected'
    
    # 获取发送者信�?
    sender = User.query.get(friend_request.sender_id)
    
    flash(f'你已拒绝 {sender.username} 的好友请�?, 'success')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/cancel/<int:request_id>', methods=['POST'])
@login_required
@safe_transaction
def cancel_friend_request(request_id):
    """取消好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否由当前用户发�?
    if friend_request.sender_id != current_user.id:
        flash('无权处理此请�?, 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状�?
    if friend_request.status != 'pending':
        flash('该请求已处理，无法取�?, 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 删除请求
    db.session.delete(friend_request)
    
    # 获取接收者信�?
    receiver = User.query.get(friend_request.receiver_id)
    
    flash(f'你已取消�?{receiver.username} 发送的好友请求', 'success')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/remove/<int:user_id>', methods=['POST'])
@login_required
@safe_transaction
def remove_friend(user_id):
    """删除好友"""
    # 检查用户是否存�?
    user = User.query.get_or_404(user_id)
    
    # 检查是否是好友
    if not current_user.is_friend(user):
        flash('该用户不是你的好�?, 'danger')
        return redirect(url_for('profile.friends'))
    
    # 查找并删除好友关�?
    friendship = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == current_user.id))
    ).filter_by(status='accepted').first()
    
    if friendship:
        db.session.delete(friendship)
        
        flash(f'已将 {user.username} 从好友列表中移除', 'success')
    else:
        flash('未找到好友关�?, 'danger')
    
    return redirect(url_for('profile.friends'))

@profile.route('/friend/requests')
@login_required
def friend_requests():
    """好友请求列表"""
    # 获取收到的请�?
    received_requests = FriendRequest.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    
    # 获取发出的请�?
    sent_requests = FriendRequest.query.filter_by(
        sender_id=current_user.id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    
    return render_template('profile/friend_requests.html',
                          received_requests=received_requests,
                          sent_requests=sent_requests)

@profile.route('/messages')
@login_required
def messages():
    """消息中心"""
    # 查询与当前用户有私聊记录的用�?
    private_chat_users = db.session.query(User).join(
        Message, 
        ((Message.sender_id == User.id) & (Message.target_type == 'user') & (Message.target_id == current_user.id)) |
        ((Message.sender_id == current_user.id) & (Message.target_type == 'user') & (Message.target_id == User.id))
    ).filter(User.id != current_user.id).distinct().all()
    
    # 查询用户所在的群组
    groups = current_user.groups.all()
    
    # 获取每个联系人的最新消息和未读消息�?
    contacts = []
    
    # 处理私聊联系�?
    for user in private_chat_users:
        # 查询最新一条消�?
        latest_message = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.target_type == 'user') & (Message.target_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.target_type == 'user') & (Message.target_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()
        
        # 查询未读消息�?
        unread_count = Message.query.filter_by(
            sender_id=user.id,
            target_type='user',
            target_id=current_user.id,
            is_read=False
        ).count()
        
        contacts.append({
            'type': 'user',
            'id': user.id,
            'name': user.name or user.username,
            'avatar': user.avatar,
            'latest_message': latest_message,
            'unread_count': unread_count,
            'is_online': user.is_online,
            'last_seen': user.last_seen
        })
    
    # 处理群组联系�?
    for group in groups:
        # 查询最新一条消�?
        latest_message = Message.query.filter_by(
            target_type='group',
            target_id=group.id
        ).order_by(Message.created_at.desc()).first()
        
        contacts.append({
            'type': 'group',
            'id': group.id,
            'name': group.name,
            'avatar': group.avatar,
            'latest_message': latest_message,
            'member_count': group.member_count
        })
    
    # 按最新消息时间排�?
    contacts.sort(key=lambda x: x.get('latest_message').created_at if x.get('latest_message') else datetime.min, reverse=True)
    
    return render_template('profile/messages.html',
                          contacts=contacts)

@profile.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    """私聊页面"""
    # 查询聊天对象
    user = User.query.get_or_404(user_id)
    
    # 获取聊天记录
    messages = Message.get_private_chat(current_user.id, user_id)
    
    # 将未读消息标记为已读
    Message.mark_as_read(current_user.id, user_id)
    
    return render_template('profile/chat.html',
                          user=user,
                          messages=messages)

@profile.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
@safe_transaction
def send_message(user_id):
    """发送私聊消�?""
    # 检查用户是否存�?
    user = User.query.get_or_404(user_id)
    
    # 检查是否向自己发送消�?
    """消息列表页面"""
    # 获取与当前用户相关的所有消�?
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    
    # 获取所有聊天过的用�?
    chat_users = set()
    for message in recent_messages:
        if message.sender_id == current_user.id:
            chat_users.add(message.receiver_id)
        else:
            chat_users.add(message.sender_id)
    
    # 为每个用户获取最新消�?
    contacts = []
    for user_id in chat_users:
        user = User.query.get(user_id)
        if user:
            # 获取最新消�?
            latest_message = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.created_at.desc()).first()
            
            # 获取未读消息�?
            unread_count = Message.query.filter_by(
                sender_id=user_id,
                receiver_id=current_user.id,
                is_read=False
            ).count()
            
            # 添加联系人信�?
            contacts.append({
                'user': user,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
    
    # 按最新消息时间排�?
    contacts.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else datetime.min, reverse=True)
    
    # 获取用户的群�?
    groups = current_user.groups.all()
    
    # 为每个群组获取最新消�?
    group_contacts = []
    for group in groups:
        # 获取最新消�?
        latest_group_message = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.created_at.desc()).first()
        
        # 添加群组信息
        group_contacts.append({
            'group': group,
            'latest_message': latest_group_message
        })
    
    # 按最新消息时间排�?
    group_contacts.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else datetime.min, reverse=True)
    
    return render_template(
        'profile/messages.html',
        contacts=contacts,
        group_contacts=group_contacts
    )

@profile.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    """与特定用户的聊天页面"""
    # 检查目标用户是否存�?
    user = User.query.get_or_404(user_id)
    
    # 获取与该用户的所有消�?
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    # 将发送给当前用户的消息标记为已读
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    return render_template(
        'profile/chat.html',
        user=user,
        messages=messages
    )

@profile.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    """发送私信给特定用户"""
    # 检查目标用户是否存�?
    user = User.query.get_or_404(user_id)
    
    # 检查是否向自己发送消�?
    if user.id == current_user.id:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='不能向自己发送消�?)
        flash('不能向自己发送消�?, 'danger')
        return redirect(url_for('profile.messages'))
    
    # 获取消息内容
    content = request.form.get('content')
    
    if not content or content.strip() == '':
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='消息不能为空')
        flash('消息不能为空', 'danger')
        return redirect(url_for('profile.chat', user_id=user_id))
    
    # 创建新消�?
    message = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    if request.content_type and 'application/json' in request.content_type:
        return jsonify(
            success=True,
            message_id=message.id,
            content=message.content,
            created_at=message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    return redirect(url_for('profile.chat', user_id=user_id))

@profile.route('/groups')
@login_required
def groups():
    """群组列表页面"""
    # 获取用户创建的群�?
    created_groups = current_user.created_groups.all()
    
    # 获取用户加入的群�?
    joined_groups = current_user.groups.all()
    
    return render_template(
        'profile/groups.html',
        created_groups=created_groups,
        joined_groups=joined_groups
    )

@profile.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    """创建新群�?""
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        description = request.form.get('description')
        team_id = request.form.get('team_id')
        
        # 验证数据
        if not name:
            flash('群组名称不能为空', 'danger')
            return redirect(url_for('profile.create_group'))
        
        # 处理头像上传
        avatar_file = request.files.get('avatar')
        avatar_path = None
        
        if avatar_file and avatar_file.filename:
            # 确保文件名安�?
            filename = secure_filename(avatar_file.filename)
            # 生成唯一文件�?
            unique_filename = f"group_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            # 设置存储路径
            avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'group_avatars', unique_filename)
            # 确保目录存在
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            # 保存文件
            avatar_file.save(avatar_path)
            # 设置头像路径
            avatar_path = f"/uploads/group_avatars/{unique_filename}"
        
        # 创建新群�?
        new_group = ChatGroup(
            name=name,
            description=description,
            avatar=avatar_path,
            creator_id=current_user.id,
            team_id=team_id if team_id else None
        )
        
        db.session.add(new_group)
        db.session.flush()  # 获取新群组ID
        
        # 将创建者添加为群组成员（管理员�?
        new_group.members.append(current_user)
        
        # 如果是基于团队创建的群组，将团队成员添加到群�?
        if team_id:
            from app.models import Team
            team = Team.query.get(team_id)
            if team:
                for member in team.members:
                    if member.id != current_user.id:  # 避免重复添加创建�?
                        new_group.members.append(member)
        
        db.session.commit()
        
        flash(f'群组 "{name}" 创建成功', 'success')
        return redirect(url_for('profile.group_detail', group_id=new_group.id))
    
    # 获取用户的团队以供选择
    from app.models import Team, team_members
    teams = Team.query.join(team_members).filter(team_members.c.user_id == current_user.id).all()
    
    return render_template('profile/create_group.html', teams=teams)

@profile.route('/group/<int:group_id>')
@login_required
def group_detail(group_id):
    """群组详情页面"""
    # 检查群组是否存�?
    group = ChatGroup.query.get_or_404(group_id)
    
    # 检查当前用户是否是群组成员
    if current_user not in group.members:
        flash('你不是该群组的成员，无法查看', 'danger')
        return redirect(url_for('profile.groups'))
    
    # 获取群组消息
    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.created_at).all()
    
    # 检查当前用户是否是管理�?
    is_admin = current_user.id == group.creator_id
    
    return render_template(
        'profile/group_detail.html',
        group=group,
        messages=messages,
        is_admin=is_admin
    )

@profile.route('/group/<int:group_id>/send_message', methods=['POST'])
@login_required
def send_group_message(group_id):
    """在群组中发送消�?""
    # 检查群组是否存�?
    group = ChatGroup.query.get_or_404(group_id)
    
    # 检查当前用户是否是群组成员
    if current_user not in group.members:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='你不是该群组的成员，无法发送消�?)
        flash('你不是该群组的成员，无法发送消�?, 'danger')
        return redirect(url_for('profile.groups'))
    
    # 获取消息内容
    content = request.form.get('content')
    
    if not content or content.strip() == '':
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='消息不能为空')
        flash('消息不能为空', 'danger')
        return redirect(url_for('profile.group_detail', group_id=group_id))
    
    # 创建新消�?
    message = GroupMessage(
        group_id=group_id,
        sender_id=current_user.id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    if request.content_type and 'application/json' in request.content_type:
        return jsonify(
            success=True,
            message_id=message.id,
            content=message.content,
            sender_name=current_user.username,
            sender_avatar=current_user.avatar,
            created_at=message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    return redirect(url_for('profile.group_detail', group_id=group_id)) 