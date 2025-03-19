# 校园众创平台

这是一个专为校园用户打造的集众筹、组队和社交于一体的综合平台，旨在促进校园创新与合作。

## 功能概述

平台包含三大核心模块：

1. **众筹模块**：
   - 发布创意项目
   - 点赞验证项目可行性
   - 一键组队功能
   - 经济支持/捐赠功能

2. **组队模块**：
   - 按场景分类（学习、日常、比赛、项目、科研、创业、社团、学工等）
   - 发起组队需求
   - 加入已有团队

3. **社交模块**：
   - 匿名对话系统
   - 引导式问题推送
   - 渐进式身份揭示
   - 好友添加与社交圈拓展

## 技术架构

- **后端**：Python Flask + SQLAlchemy
- **前端**：HTML5 + CSS3 + JavaScript/jQuery + Bootstrap 5
- **数据库**：SQLite (开发阶段)，可扩展至MySQL/PostgreSQL
- **部署**：可部署于Heroku、PythonAnywhere等PaaS平台

## 项目结构

```
校园众创平台/
├── app.py                # 应用入口
├── models.py             # 数据模型
├── crowdfunding.py       # 众筹模块API
├── team.py               # 组队模块API
├── social.py             # 社交模块API
├── payment.py            # 支付/互动模块API
├── templates/            # 页面模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── crowdfunding.html # 众筹页面
│   ├── team.html         # 组队页面
│   └── social.html       # 社交页面
├── static/               # 静态资源
│   ├── css/              # 样式文件
│   │   └── styles.css    # 主样式文件
│   ├── js/               # JavaScript脚本
│   │   ├── app.js        # 主脚本文件
│   │   ├── crowdfunding.js # 众筹模块脚本
│   │   ├── team.js       # 组队模块脚本
│   │   └── social.js     # 社交模块脚本
│   └── img/              # 图片资源
└── requirements.txt      # 项目依赖
```

## 如何运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 初始化数据库：
```bash
flask db init
flask db migrate
flask db upgrade
```

3. 启动应用：
```bash
flask run
```

4. 在浏览器中访问：`http://127.0.0.1:5000/`

## 如何运行测试

1. 安装测试依赖：
```bash
pip install pytest
```

2. 运行所有测试：
```bash
pytest
```

3. 运行特定测试文件：
```bash
pytest tests/test_app.py
```

4. 查看测试覆盖率：
```bash
pytest --cov=. tests/
```
注意：需要安装pytest-cov包 `pip install pytest-cov`

## 模块功能详解

### 众筹模块
- 用户可以发布自己的创意项目，描述项目内容、目标和所需资源
- 其他用户可以通过点赞来验证项目的可行性和价值
- "一键组队"功能允许项目发起人快速组建团队
- 用户可以选择对感兴趣的项目提供经济支持

### 组队模块
- 根据不同场景（学习、比赛、创业等）分类展示组队信息
- 用户可以根据自己的需求发起组队
- 提供详细的团队成员筛选和匹配机制
- 组队完成后可以转化为项目众筹

### 社交模块
- 初始阶段用户以匿名方式进行对话
- 系统推送引导式问题，促进深度交流
- 随着交流深入，系统逐步揭示双方身份
- 用户可以添加好友，扩展自己的社交圈

## 开发进度

- [x] 基础项目结构搭建
- [x] 数据模型设计与实现
- [ ] 众筹模块开发
- [ ] 组队模块开发
- [ ] 社交模块开发
- [ ] 前端基础页面设计
- [ ] 用户认证系统
- [ ] 支付模拟功能
- [ ] 响应式设计优化
- [ ] 部署与测试

## 未来规划

- 集成第三方支付系统
- 添加更多社交功能，如群组讨论
- 开发移动端应用
- 增加数据分析功能，为用户提供个性化推荐

## 贡献指南

欢迎提出建议和改进意见，共同完善这个校园创新平台！

## 许可证

MIT License 