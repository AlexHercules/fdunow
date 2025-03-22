# FDU校园众筹与协作平台

## 项目概述

FDU校园众筹与协作平台是一个为复旦大学师生提供的综合性服务平台，旨在满足校园内创新项目的众筹需求、团队协作以及社交互动。平台集成了项目众筹、团队组建、即时通讯等功能，为师生提供一站式的校园协作解决方案。

## 功能特性

### 用户系统
- 账号注册与登录：支持邮箱注册、登录和密码找回
- 个人资料管理：完善个人信息、技能、专业等
- 隐私设置：控制个人信息对外展示的权限
- 权限与角色管理：基于角色的权限系统，支持学生、开发者、管理员等角色

### 项目众筹
- 创建众筹项目：发起人可设置项目详情、目标金额、回报设置等
- 项目浏览与筛选：按类别、热度、时间等多维度筛选
- 项目支持：用户可支持感兴趣的项目并获得相应回报
- 项目进度跟踪：实时更新项目筹款进度、动态
- 多媒体支持：项目可添加图片、视频、文档等丰富内容
- 项目互动：支持评论、点赞、分享等互动功能

### 团队协作
- 团队创建与管理：创建团队、邀请成员、分配角色
- 任务管理：创建任务、分配责任人、设置截止日期
- 团队文档：共享文档、资料、协作编辑

### 社交网络
- 好友系统：添加好友、管理好友关系
- 私信系统：与好友进行即时通讯
- 群组聊天：创建群组、群组消息
- 社区讨论区：分类论坛，支持发布主题、评论、点赞等功能

### 实时通信
- WebSocket支持：实现实时消息推送和通知
- 在线状态：显示用户在线状态
- 已读回执：消息已读状态实时更新

### 个性化推荐
- 项目推荐：基于用户兴趣和行为推荐相关项目
- 团队推荐：根据用户技能和专业推荐适合的团队
- 论坛主题推荐：基于用户浏览和互动历史推荐感兴趣的讨论

### 系统安全与错误处理
- 完善的错误处理机制：用户友好的错误页面
- 事务安全：重要操作使用事务保证数据一致性
- 输入验证：防止XSS、CSRF等安全问题

## 技术栈

### 后端
- Flask：Python Web框架
- SQLAlchemy：ORM数据库映射
- Flask-Login：用户认证管理
- Flask-SocketIO：WebSocket支持
- Flask-Mail：邮件发送

### 前端
- Bootstrap：响应式UI框架
- JavaScript/jQuery：客户端交互
- Socket.IO：实时通信客户端

### 数据库
- SQLite（开发环境）
- MySQL/PostgreSQL（生产环境）

## 安装与运行

### 前提条件
- Python 3.7+
- pip 包管理器

### 安装步骤
1. 克隆项目代码
```bash
git clone https://github.com/yourusername/fdunow.git
cd fdunow
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖包
```bash
pip install -r requirements.txt
```

4. 初始化数据库
```bash
flask db init
flask db migrate
flask db upgrade
```

5. 运行应用
```bash
python application.py
```

### 配置选项
在`config.py`文件中可以修改以下配置：
- 数据库连接URI
- 邮件服务器设置
- 文件上传路径
- 安全密钥

## 项目结构

```
fdunow/
├── app/                    # 应用包
│   ├── auth/               # 认证模块
│   ├── main/               # 主页和通用视图
│   ├── profile/            # 个人中心模块
│   ├── project/            # 项目模块
│   ├── team/               # 团队模块
│   ├── user/               # 用户模块
│   ├── realtime/           # 实时通信模块
│   ├── utils.py            # 工具函数
│   └── errors.py           # 错误处理
├── migrations/             # 数据库迁移文件
├── static/                 # 静态资源
│   ├── css/                # CSS样式
│   ├── js/                 # JavaScript脚本
│   ├── uploads/            # 上传文件存储
│   └── img/                # 图片资源
├── templates/              # HTML模板
│   ├── auth/               # 认证相关模板
│   ├── errors/             # 错误页面模板
│   ├── main/               # 主页和通用模板
│   ├── profile/            # 个人中心模板
│   ├── project/            # 项目相关模板
│   ├── team/               # 团队相关模板
│   ├── user/               # 用户相关模板
│   └── base.html           # 基础模板
├── application.py          # 应用入口
├── config.py               # 配置文件
├── models.py               # 数据模型
└── requirements.txt        # 依赖包列表
```

## 开发进度

- [x] 用户模型与认证系统
- [x] 个人资料管理
- [x] 社交功能（好友、私信）
- [x] 项目众筹基础功能
- [x] 团队协作基础功能
- [x] 群组聊天功能
- [x] 错误处理与用户反馈
- [x] WebSocket实时通信
- [ ] 高级搜索功能
- [ ] 数据分析与报表
- [ ] 移动端适配优化

## 最近更新

### v0.4.0 (2023-11-15)
- 增强权限管理系统：实现基于角色的细粒度权限控制
- 添加项目多媒体支持：项目可添加图片、视频和文档
- 新增项目互动功能：评论、点赞、回复系统
- 创建社区讨论区：分类论坛，支持主题发布与互动
- 实现个性化推荐系统：基于用户行为和兴趣的智能推荐

### v0.3.0 (2023-11-10)
- 添加WebSocket支持，实现实时消息推送
- 统一消息模型，优化数据结构
- 完善错误处理机制，添加友好的错误页面
- 改进事务安全性，防止数据不一致
- 添加XSS防护，确保内容安全

## 贡献指南

我们欢迎所有形式的贡献，无论是新功能、bug修复还是文档改进。请遵循以下步骤：

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 联系方式

- 项目维护者：[Your Name](mailto:your.email@example.com)
- 项目仓库：[GitHub](https://github.com/yourusername/fdunow)

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件