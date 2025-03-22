# 校园众创平台

这是一个校园众创平台，旨在促进校园内的创新创业项目，帮助学生寻找团队成员，发起众筹项目，以及社交交流。

## 主要功能

### 用户模块
- **注册登录**: 用户可以通过邮箱注册账号并登录
- **个人资料**: 用户可以上传头像、填写个人信息
- **用户列表**: 浏览所有用户，支持按专业、技能过滤
- **用户详情**: 查看用户的详细资料、项目、团队和好友

### 个人中心模块
- **个人主页**: 显示用户的项目、团队、好友和群组
- **资料编辑**: 编辑个人资料，包括头像、基本信息、学术信息和联系方式
- **隐私设置**: 控制资料的可见范围，如邮箱、电话、项目等

### 社交功能
- **好友系统**: 可以添加、接受、拒绝好友请求，管理好友列表
- **私聊功能**: 与好友进行一对一聊天
- **聊天群组**: 创建群组、邀请成员、群聊
- **消息中心**: 统一查看私聊和群聊消息

### 项目众筹
- **发起项目**: 创建众筹项目，设置目标金额、描述和回报
- **支持项目**: 浏览项目列表，支持喜欢的项目
- **项目管理**: 管理自己发起的项目，更新进展
- **收藏项目**: 收藏感兴趣的项目

### 团队协作
- **创建团队**: 根据项目需求创建团队
- **招募成员**: 设置团队需要的角色和技能
- **加入团队**: 浏览团队列表，申请加入感兴趣的团队
- **团队管理**: 管理团队成员，更新团队信息

## 技术栈
- **后端**: Flask, SQLAlchemy
- **前端**: HTML, CSS, JavaScript, Bootstrap
- **数据库**: SQLite (开发), MySQL (生产)
- **部署**: Docker, Nginx

## 如何使用

### 1. 注册和登录
- 访问首页，点击"注册"按钮
- 填写邮箱、用户名和密码
- 通过邮箱验证链接激活账号
- 登录系统

### 2. 完善个人资料
- 登录后，点击右上角头像，选择"个人中心"
- 点击"编辑资料"按钮
- 上传头像，填写个人信息，如学院、专业、年级、技能等
- 设置隐私选项，控制信息可见范围

### 3. 社交功能
- 在"用户列表"页面浏览用户，添加好友
- 在"消息"页面查看和回复消息
- 创建聊天群组，邀请好友加入
- 通过私聊或群聊与他人交流

### 4. 众筹项目
- 在"项目"页面浏览项目列表
- 点击"发起项目"创建自己的众筹项目
- 支持喜欢的项目，关注项目进展

### 5. 团队协作
- 在"团队"页面浏览团队列表
- 创建新团队，设置招募需求
- 申请加入感兴趣的团队
- 在团队内部协作，分享资源

## 开发环境配置

### 环境要求
- Python 3.8+
- pip
- virtualenv (推荐)

### 安装步骤
1. 克隆代码库
   ```
   git clone https://github.com/yourusername/campus-crowdfunding.git
   cd campus-crowdfunding
   ```

2. 创建虚拟环境
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖
   ```
   pip install -r requirements.txt
   ```

4. 设置环境变量
   ```
   export FLASK_APP=application.py
   export FLASK_ENV=development
   ```

5. 初始化数据库
   ```
   flask db upgrade
   ```

6. 启动开发服务器
   ```
   flask run
   ```

7. 访问开发服务器
   ```
   http://localhost:5000
   ```

## 贡献指南

我们欢迎任何形式的贡献，包括但不限于：
- 报告Bug
- 提交功能需求
- 提交Pull Request
- 改进文档

### 贡献流程
1. Fork代码库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 许可证

该项目基于MIT许可证 - 详情请查看 [LICENSE](LICENSE) 文件

# run.py
import os
import app as app_module  # 导入app.py作为模块，避免与app包冲突
app = app_module.app  # 从模块中获取app实例

if __name__ == '__main__':
    app.run(debug=True)