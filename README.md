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

### 支付系统与财务管理
- 多种支付方式：支持支付宝、微信支付、校园卡、银行转账等多种支付方式
- 安全的交易处理：SSL加密保护，第三方支付机构合作，个人信息保护
- 服务费计算与账单管理
  - 基于项目类型的差异化费率：公益项目2%，学术项目3%，文化体育项目4%，创业项目5%
  - 大额筹款优惠机制：筹款金额达到一定级别自动降低服务费率
  - 透明的账单生成和结算：自动生成账单，清晰展示费用明细
- 退款与争议处理
  - 阶段性退款策略：根据项目进度提供不同比例的退款
  - 争议提交和仲裁流程：支持用户提交争议申请，平台介入协调
  - 自动化退款处理：项目未达标自动退款机制
- 财务报表与统计分析
  - 项目财务摘要：展示项目筹款、费用、净收入情况
  - 平台收支报表：管理员可查看平台整体财务状况
  - 交易记录查询：支持多维度筛选和查询交易记录
  - 支付方式使用分析：分析不同支付方式的使用情况和偏好

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

## 安装与运行指南

### 系统要求
- Python 3.8+
- pip 包管理器
- 虚拟环境 (推荐)

### 安装步骤

1. 克隆项目仓库
```bash
git clone [仓库地址]
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

4. 配置环境变量
```bash
# 复制示例环境变量文件
cp .env.example .env
# 编辑.env文件，设置必要的配置，如数据库连接、邮箱等
```

5. 初始化数据库
```bash
flask db init
flask db migrate -m "初始化数据库"
flask db upgrade
```

6. 部署基础数据
```bash
flask deploy
```

7. 运行应用
```bash
flask run
# 或者
python run.py
```

8. 访问应用
在浏览器中访问 http://localhost:5000

### 管理员账户
初始管理员账户信息:
- 用户名: admin
- 邮箱: admin@fdunow.com
- 密码: Admin123!

可以通过在.env文件中设置ADMIN_EMAIL、ADMIN_USERNAME和ADMIN_PASSWORD来自定义管理员信息。

## 项目结构

```
fdunow/
├── app/                        # 应用主目录
│   ├── __init__.py             # 应用初始化
│   ├── extensions.py           # 扩展库初始化
│   ├── models/                 # 数据模型
│   ├── main/                   # 主模块（首页等）
│   ├── auth/                   # 认证模块（登录、注册等）
│   ├── crowdfunding/           # 众筹项目模块
│   ├── team/                   # 团队组建模块
│   ├── payment/                # 支付模块
│   ├── admin/                  # 后台管理模块
│   └── templates/              # 模板文件
│       ├── main/               # 主模块模板
│       ├── auth/               # 认证模块模板
│       ├── crowdfunding/       # 众筹项目模板
│       ├── team/               # 团队模板
│       ├── payment/            # 支付模板
│       ├── admin/              # 后台管理模板
│       └── errors/             # 错误页面模板
├── config.py                   # 配置文件
├── requirements.txt            # 项目依赖
└── run.py                      # 应用启动脚本
```

## 功能模块

### 主模块
- 首页：展示平台介绍、热门项目、数据统计等
- "关于我们"页面：介绍平台目标、团队成员和联系方式

### 认证模块
- 用户注册：支持邮箱验证、学生身份验证
- 用户登录：账号密码登录，支持记住密码功能
- 密码找回：通过邮箱验证找回密码
- 个人资料：用户可以编辑个人信息、查看项目和团队情况

### 众筹项目模块
- 项目列表：展示所有众筹项目，支持分类筛选和搜索
- 项目详情：展示项目详细信息、进度和支持者
- 项目创建：用户可以创建新的众筹项目
- 项目支持：用户可以支持感兴趣的项目

### 团队组建模块
- 团队列表：展示所有创业团队，支持筛选和搜索
- 团队详情：展示团队详细信息和成员
- 团队创建：用户可以创建新的创业团队
- 团队加入：用户可以申请加入感兴趣的团队

### 支付模块
- 支付记录：用户可以查看自己的支付记录
- 支付处理：处理项目支持的支付流程
- 资金管理：管理项目资金的流转

### 后台管理模块
- 用户管理：管理员可以查看、编辑和管理用户信息
- 项目管理：管理员可以审核、编辑和管理众筹项目
- 团队管理：管理员可以审核、编辑和管理创业团队
- 支付管理：管理员可以查看和处理支付记录
- 数据统计：统计平台活跃度、项目成功率等数据
- 内容审核：审核用户发布的项目、团队和评论内容

## 前端页面

### 已完成页面
- 首页（app/templates/main/index.html）
- 错误页面（app/templates/errors/404.html）
- 注册页面（app/templates/auth/register.html）
- 登录页面（app/templates/auth/login.html）
- 找回密码页面（app/templates/auth/forgot_password.html）
- 重置密码页面（app/templates/auth/reset_password.html）
- 个人资料页面（app/templates/auth/profile.html）
- 后台管理首页（app/templates/admin/index.html）
- 后台数据统计页面（app/templates/admin/statistics.html）
- 后台内容审核页面（app/templates/admin/content_audit.html）

### 需要开发的页面
- 众筹项目列表页
- 众筹项目详情页
- 创建众筹项目页面
- 团队列表页
- 团队详情页
- 创建团队页面
- 支付中心页面
- 更多后台管理页面

## 支付模块说明

支付模块是校园众筹平台的核心功能之一，提供安全可靠的资金流转服务：

### 数据模型
- Transaction：交易记录模型，记录所有资金流动
- ServiceFee：服务费模型，记录平台收取的服务费
- Invoice：账单模型，用于项目方和平台结算
- Refund：退款模型，处理用户的退款请求
- Dispute：争议处理模型，处理交易纠纷

### 主要功能
1. **交易处理**
   - 创建捐款交易：用户支持项目时创建交易记录
   - 处理支付：接收支付网关回调，更新交易状态
   - 服务费计算：根据项目类型自动计算服务费
   - 项目资金统计：实时更新项目筹款进度

2. **退款管理**
   - 退款申请：用户可申请退款并提供证据
   - 退款审核：管理员审核退款申请
   - 退款处理：自动处理已批准的退款
   - 争议处理：处理退款争议和纠纷

3. **财务报表**
   - 项目财务摘要：展示项目筹款、退款、服务费和净收入
   - 平台财务报表：平台整体收支状况
   - 交易记录查询：支持多条件筛选查询
   - 支付方式统计：分析不同支付方式的使用情况

### API接口
- `/payment/api/donations`：创建捐款交易
- `/payment/api/donations/<id>/pay`：处理支付
- `/payment/api/refunds`：申请退款
- `/payment/api/refunds/<id>/process`：处理退款
- `/payment/api/projects/<id>/financial-summary`：获取项目财务摘要
- `/payment/api/transactions/report`：获取交易报表

### 页面路由
- `/payment/`：支付系统首页
- `/payment/my_donations`：我的捐款记录
- `/payment/process_payment/<project_id>`：处理支付页面
- `/payment/help`：支付帮助页面

### 使用方法
1. 浏览项目列表，选择感兴趣的项目
2. 点击"支持项目"按钮，进入支付页面
3. 选择金额和支付方式，完成支付
4. 在"我的捐款"页面查看捐款记录和状态
5. 如需退款，可在交易详情页申请退款

## 开发进度

- [x] 用户模型与认证系统
- [x] 个人资料管理
- [x] 社交功能（好友、私信）
- [x] 项目众筹基础功能
- [x] 团队协作基础功能
- [x] 群组聊天功能
- [x] 错误处理与用户反馈
- [x] WebSocket实时通信
- [x] 支付系统与财务管理
- [ ] 高级搜索功能
- [ ] 数据分析与报表
- [ ] 移动端适配优化

## 最近更新

### v0.5.0 (2023-11-20)
- 新增支付系统模块：支持多种支付方式，提供安全的交易处理
- 实现服务费计算与账单管理：基于项目类型的差异化费率，大额筹款优惠
- 添加退款与争议处理：阶段性退款策略，争议提交和仲裁流程
- 开发财务报表与统计分析：项目财务摘要，平台收支报表，交易记录查询
- 优化用户体验：支付流程简化，资金安全保障，交易透明化

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

# 校园众创平台

校园众创平台是一个专为高校学生设计的创新创业服务平台，帮助学生实现创意项目、组建团队、获取资金支持。

## 项目结构

```
fdunow/
├── app/                      # 应用主目录
│   ├── __init__.py           # 应用初始化
│   ├── extensions.py         # Flask扩展初始化
│   ├── utils.py              # 工具函数
│   ├── main/                 # 主页模块
│   │   ├── __init__.py
│   │   └── routes.py         # 主页路由
│   ├── auth/                 # 认证模块
│   │   ├── __init__.py
│   │   └── routes.py         # 认证路由
│   ├── crowdfunding/         # 众筹模块
│   │   ├── __init__.py
│   │   └── routes.py         # 众筹路由
│   ├── team/                 # 团队模块
│   │   ├── __init__.py
│   │   └── routes.py         # 团队路由
│   ├── payment/              # 支付模块
│   │   ├── __init__.py
│   │   ├── routes.py         # 支付路由
│   │   ├── models.py         # 支付数据模型
│   │   └── services.py       # 支付服务逻辑
│   ├── admin/                # 管理后台模块
│   │   ├── __init__.py
│   │   └── routes.py         # 管理路由
│   ├── static/               # 静态资源
│   │   ├── css/              # CSS样式文件
│   │   ├── js/               # JavaScript文件
│   │   └── images/           # 图片资源
│   └── templates/            # 模板文件
│       ├── main/             # 主页模板
│       ├── auth/             # 认证模板
│       ├── crowdfunding/     # 众筹模板
│       ├── team/             # 团队模板
│       ├── payment/          # 支付模板
│       ├── admin/            # 管理后台模板
│       └── errors/           # 错误页面模板
├── config.py                 # 配置文件
├── app_starter.py            # 应用启动文件
└── README.md                 # 项目说明
```

## 功能模块

### 主页模块

主页展示平台特色、项目统计和热门项目，为用户提供平台整体概览。

- 首页：展示平台特色、项目统计和热门项目
- 关于我们：介绍平台的使命、愿景和核心功能

### 认证模块

处理用户注册、登录、密码重置等认证相关功能。

- 注册：新用户注册
- 登录：用户登录
- 忘记密码：密码重置功能
- 邮箱验证：验证用户邮箱有效性

### 众筹模块

提供项目展示、创建和支持功能，是平台的核心功能模块之一。

- 项目列表：展示所有众筹项目
- 项目详情：查看项目详细信息
- 创建项目：创建新的众筹项目（需登录）
- 支持项目：为项目提供资金支持（需登录）

### 团队模块

帮助用户组建团队、发布招募需求和申请加入项目团队。

- 团队需求列表：展示所有团队招募需求
- 发布需求：发布团队招募需求（需登录）
- 申请加入：申请加入团队（需登录）
- 查看申请记录：查看自己的申请记录（需登录）

### 支付模块

处理资金交易、捐款、退款等财务相关功能。

- 支付主页：展示支付相关信息和入口
- 捐款表单：填写捐款信息并选择支付方式
- 交易记录：查看个人交易记录（需登录）
- 财务报表：查看项目财务报表（项目创建者可见）
- 发票/收据：申请和下载捐款发票或收据
- 退款申请：申请退款（需登录）

### 管理后台模块

为管理员提供全方位的平台管理功能。

- 控制面板：展示平台概况和关键指标
- 用户管理：查看、编辑和管理用户账户
- 项目管理：监控和管理众筹项目
- 团队管理：审核和管理团队申请
- 支付管理：监控交易记录和处理退款申请
- 数据统计：分析平台数据，生成各类报表
- 内容审核：审核用户发布的内容，防止不当信息

## 前端页面

### 主页页面
- `app/templates/main/index.html` - 首页，展示平台特色和热门项目
- `app/templates/main/about.html` - 关于我们页面，介绍平台背景和团队

### 众筹页面
- `app/templates/crowdfunding/index.html` - 众筹项目列表页面

### 团队页面
- `app/templates/team/index.html` - 团队组建页面，展示团队需求列表

### 支付页面
- `app/templates/payment/index.html` - 支付中心页面，提供支付相关功能入口

### 管理后台页面
- `app/templates/admin/index.html` - 管理控制台，展示平台概况
- `app/templates/admin/statistics.html` - 数据统计页面，分析平台数据
- `app/templates/admin/content_audit.html` - 内容审核页面，审核用户发布的内容

### 错误页面
- `app/templates/errors/404.html` - 404错误页面，用于处理页面未找到的情况

## 系统优化

### 前端用户体验优化

- **响应式设计**：所有页面均采用响应式设计，确保在移动设备、平板和桌面端有良好的展示效果
- **UI/UX细节优化**：精心设计的用户界面，考虑用户交互流程的顺畅性和直观性
- **无障碍支持**：遵循WCAG 2.1标准，确保残障用户可以无障碍地使用平台
- **多语言支持**：支持中英文双语切换，满足国际学生的需求

### 性能优化

- **前端缓存**：使用浏览器缓存和CDN加速静态资源加载
- **数据库优化**：合理设计索引，优化查询性能
- **懒加载**：使用懒加载技术减少首屏加载时间
- **页面压缩**：对HTML、CSS和JavaScript文件进行压缩，减少传输大小
- **图片优化**：使用WebP等现代图片格式和响应式图片加载策略

### 第三方服务集成

- **社交登录**：支持微信、QQ和微博等社交平台登录
- **支付集成**：对接微信支付、支付宝和校园支付系统
- **邮件通知**：使用SendGrid发送系统通知邮件
- **短信验证**：集成阿里云短信服务进行手机号验证
- **地图服务**：整合百度地图API提供位置相关功能

### DevOps与自动化测试

- **CI/CD流水线**：使用GitHub Actions实现持续集成和部署
- **自动化测试**：包含单元测试、集成测试和端到端测试
- **代码质量检查**：使用SonarQube进行代码质量扫描
- **监控与日志**：使用Prometheus和ELK Stack进行系统监控和日志管理
- **容器化部署**：使用Docker和Docker Compose简化部署流程

## 启动应用

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 设置环境变量：
```
# Windows
set FLASK_APP=app_starter.py
set FLASK_ENV=development

# Linux/macOS
export FLASK_APP=app_starter.py
export FLASK_ENV=development
```

3. 初始化数据库：
```
flask db init
flask db migrate
flask db upgrade
```

4. 启动应用：
```
flask run
```

## 贡献指南

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交修改：`git commit -am 'Add my feature'`
4. 推送到分支：`git push origin feature/my-feature`
5. 创建Pull Request

## 项目反思与改进方向

1. **用户体验优化**：进一步完善前端页面设计，提升用户操作体验
2. **功能完善**：继续开发更多功能，如项目进度跟踪、团队管理等
3. **安全性增强**：加强支付安全和用户数据保护
4. **性能优化**：优化数据库查询和页面加载速度
5. **智能推荐**：引入机器学习算法，为用户推荐感兴趣的项目和团队
6. **数据分析**：深入挖掘平台数据，为决策提供更精准的支持
7. **国际化**：支持更多语言，拓展国际学生用户群体