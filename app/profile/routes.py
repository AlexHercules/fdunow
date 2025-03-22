from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from application import db
from models import User, Team, CrowdfundingProject, FriendRequest, ChatGroup, GroupMessage, Message

profile = Blueprint('profile', __name__)

@profile.route('/')
@login_required
def index():
    """个人中心首页"""
    # 获取用户创建的项目
    created_projects = current_user.created_projects.all()
    
    # 获取用户支持的项目
    donations = current_user.donations.all()
    supported_projects = [donation.project for donation in donations]
    
    # 获取用户的团队
    teams = current_user.teams.all()
    
    # 获取用户的好友
    friends = current_user.friends
    
    # 获取用户创建的群组
    created_groups = current_user.created_groups.all()
    
    # 获取用户加入的群组
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
            # 确保文件名安全
            filename = secure_filename(avatar_file.filename)
            # 生成唯一文件名
            unique_filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            # 设置存储路径
            avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', unique_filename)
            # 确保目录存在
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            # 保存文件
            avatar_file.save(avatar_path)
            # 更新用户头像路径
            current_user.avatar = f"/uploads/avatars/{unique_filename}"
        
        # 更新用户资料
        current_user.name = name
        current_user.bio = bio
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
        db.session.commit()
        
        flash('个人资料已更新', 'success')
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
def send_friend_request(user_id):
    """发送好友请求"""
    # 检查目标用户是否存在
    user = User.query.get_or_404(user_id)
    
    # 检查是否向自己发送请求
    if user.id == current_user.id:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='不能向自己发送好友请求')
        flash('不能向自己发送好友请求', 'danger')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查是否已经是好友
    if current_user.is_friend(user):
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='你们已经是好友了')
        flash('你们已经是好友了', 'info')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查是否已发送过请求
    existing_request = FriendRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=user_id,
        status='pending'
    ).first()
    
    if existing_request:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='已经发送过好友请求，等待对方回应')
        flash('已经发送过好友请求，等待对方回应', 'info')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 检查对方是否已经发送请求给自己
    reverse_request = FriendRequest.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        status='pending'
    ).first()
    
    if reverse_request:
        # 如果对方已经发送请求，则自动接受
        reverse_request.status = 'accepted'
        db.session.commit()
        
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=True, message='已成为好友')
        flash(f'你与 {user.username} 已成为好友', 'success')
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
    db.session.commit()
    
    if request.content_type and 'application/json' in request.content_type:
        return jsonify(success=True, message='好友请求已发送')
    
    flash(f'已向 {user.username} 发送好友请求', 'success')
    return redirect(url_for('user.detail', user_id=user_id))

@profile.route('/friend/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    """接受好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否发给当前用户
    if friend_request.receiver_id != current_user.id:
        flash('无权处理此请求', 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状态
    if friend_request.status != 'pending':
        flash('该请求已处理', 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 更新请求状态
    friend_request.status = 'accepted'
    db.session.commit()
    
    # 获取发送者信息
    sender = User.query.get(friend_request.sender_id)
    
    flash(f'你已接受 {sender.username} 的好友请求', 'success')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_friend_request(request_id):
    """拒绝好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否发给当前用户
    if friend_request.receiver_id != current_user.id:
        flash('无权处理此请求', 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状态
    if friend_request.status != 'pending':
        flash('该请求已处理', 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 更新请求状态
    friend_request.status = 'rejected'
    db.session.commit()
    
    # 获取发送者信息
    sender = User.query.get(friend_request.sender_id)
    
    flash(f'你已拒绝 {sender.username} 的好友请求', 'info')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/cancel/<int:request_id>', methods=['POST'])
@login_required
def cancel_friend_request(request_id):
    """取消已发送的好友请求"""
    # 查找好友请求
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    # 校验请求是否由当前用户发出
    if friend_request.sender_id != current_user.id:
        flash('无权取消此请求', 'danger')
        return redirect(url_for('profile.friend_requests'))
    
    # 校验请求状态
    if friend_request.status != 'pending':
        flash('该请求已处理，无法取消', 'info')
        return redirect(url_for('profile.friend_requests'))
    
    # 删除请求
    db.session.delete(friend_request)
    db.session.commit()
    
    # 获取接收者信息
    receiver = User.query.get(friend_request.receiver_id)
    
    flash(f'你已取消向 {receiver.username} 发送的好友请求', 'info')
    return redirect(url_for('profile.friend_requests'))

@profile.route('/friend/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    """删除好友"""
    # 检查目标用户是否存在
    user = User.query.get_or_404(user_id)
    
    # 检查是否是好友
    if not current_user.is_friend(user):
        flash('你们不是好友，无法删除', 'danger')
        return redirect(url_for('user.detail', user_id=user_id))
    
    # 查找并删除好友关系
    friendship = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == current_user.id))
    ).filter_by(status='accepted').first()
    
    if friendship:
        db.session.delete(friendship)
        db.session.commit()
        
        flash(f'你已成功删除好友 {user.username}', 'success')
    else:
        flash('好友关系不存在', 'danger')
    
    return redirect(url_for('user.detail', user_id=user_id))

@profile.route('/friend/requests')
@login_required
def friend_requests():
    """好友请求列表页面"""
    # 获取收到的好友请求
    received_requests = current_user.friend_requests_received
    
    # 获取发出的好友请求
    sent_requests = current_user.friend_requests_sent
    
    return render_template(
        'profile/friend_requests.html',
        received_requests=received_requests,
        sent_requests=sent_requests
    )

@profile.route('/messages')
@login_required
def messages():
    """消息列表页面"""
    # 获取与当前用户相关的所有消息
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()
    
    # 获取所有聊天过的用户
    chat_users = set()
    for message in recent_messages:
        if message.sender_id == current_user.id:
            chat_users.add(message.receiver_id)
        else:
            chat_users.add(message.sender_id)
    
    # 为每个用户获取最新消息
    contacts = []
    for user_id in chat_users:
        user = User.query.get(user_id)
        if user:
            # 获取最新消息
            latest_message = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.created_at.desc()).first()
            
            # 获取未读消息数
            unread_count = Message.query.filter_by(
                sender_id=user_id,
                receiver_id=current_user.id,
                is_read=False
            ).count()
            
            # 添加联系人信息
            contacts.append({
                'user': user,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
    
    # 按最新消息时间排序
    contacts.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else datetime.min, reverse=True)
    
    # 获取用户的群组
    groups = current_user.groups.all()
    
    # 为每个群组获取最新消息
    group_contacts = []
    for group in groups:
        # 获取最新消息
        latest_group_message = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.created_at.desc()).first()
        
        # 添加群组信息
        group_contacts.append({
            'group': group,
            'latest_message': latest_group_message
        })
    
    # 按最新消息时间排序
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
    # 检查目标用户是否存在
    user = User.query.get_or_404(user_id)
    
    # 获取与该用户的所有消息
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
    # 检查目标用户是否存在
    user = User.query.get_or_404(user_id)
    
    # 检查是否向自己发送消息
    if user.id == current_user.id:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='不能向自己发送消息')
        flash('不能向自己发送消息', 'danger')
        return redirect(url_for('profile.messages'))
    
    # 获取消息内容
    content = request.form.get('content')
    
    if not content or content.strip() == '':
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='消息不能为空')
        flash('消息不能为空', 'danger')
        return redirect(url_for('profile.chat', user_id=user_id))
    
    # 创建新消息
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
    # 获取用户创建的群组
    created_groups = current_user.created_groups.all()
    
    # 获取用户加入的群组
    joined_groups = current_user.groups.all()
    
    return render_template(
        'profile/groups.html',
        created_groups=created_groups,
        joined_groups=joined_groups
    )

@profile.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    """创建新群组"""
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
            # 确保文件名安全
            filename = secure_filename(avatar_file.filename)
            # 生成唯一文件名
            unique_filename = f"group_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            # 设置存储路径
            avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'group_avatars', unique_filename)
            # 确保目录存在
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            # 保存文件
            avatar_file.save(avatar_path)
            # 设置头像路径
            avatar_path = f"/uploads/group_avatars/{unique_filename}"
        
        # 创建新群组
        new_group = ChatGroup(
            name=name,
            description=description,
            avatar=avatar_path,
            creator_id=current_user.id,
            team_id=team_id if team_id else None
        )
        
        db.session.add(new_group)
        db.session.flush()  # 获取新群组ID
        
        # 将创建者添加为群组成员（管理员）
        new_group.members.append(current_user)
        
        # 如果是基于团队创建的群组，将团队成员添加到群组
        if team_id:
            from app.models import Team
            team = Team.query.get(team_id)
            if team:
                for member in team.members:
                    if member.id != current_user.id:  # 避免重复添加创建者
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
    # 检查群组是否存在
    group = ChatGroup.query.get_or_404(group_id)
    
    # 检查当前用户是否是群组成员
    if current_user not in group.members:
        flash('你不是该群组的成员，无法查看', 'danger')
        return redirect(url_for('profile.groups'))
    
    # 获取群组消息
    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.created_at).all()
    
    # 检查当前用户是否是管理员
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
    """在群组中发送消息"""
    # 检查群组是否存在
    group = ChatGroup.query.get_or_404(group_id)
    
    # 检查当前用户是否是群组成员
    if current_user not in group.members:
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='你不是该群组的成员，无法发送消息')
        flash('你不是该群组的成员，无法发送消息', 'danger')
        return redirect(url_for('profile.groups'))
    
    # 获取消息内容
    content = request.form.get('content')
    
    if not content or content.strip() == '':
        if request.content_type and 'application/json' in request.content_type:
            return jsonify(success=False, message='消息不能为空')
        flash('消息不能为空', 'danger')
        return redirect(url_for('profile.group_detail', group_id=group_id))
    
    # 创建新消息
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