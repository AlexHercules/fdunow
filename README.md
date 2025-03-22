# 校园众创平台

校园众创平台是一个为大学生提供创新创业服务的综合性平台，包括项目众筹、团队组建、创新展示等功能。

## 最近更新

- 实现了用户邮箱验证功能
- 修复了模型导入冲突问题
- 优化了邮件发送模块，支持异步发送
- 添加了邮件功能的测试用例
- 更新了文档说明

## 项目特性

- **项目众筹**：帮助创业团队募集资金，展示创意项目
- **团队组建**：匹配志同道合的伙伴，组建创新团队
- **社交互动**：促进校园内创新资源的流通与交流
- **支付系统**：安全可靠的资金流转解决方案
- **API接口**：丰富的接口文档，支持二次开发
- **邮箱验证**：注册时通过邮箱验证码保证用户真实性

## 技术栈

- **后端**：Flask框架
- **数据库**：SQLAlchemy ORM
- **前端**：Bootstrap 5
- **API文档**：Flask-RESTX
- **认证系统**：Flask-Login
- **邮件系统**：Flask-Mail

## 快速开始

### 环境准备

1. 安装Python 3.8+
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

### 运行项目

```bash
python run.py
```

默认访问地址：http://127.0.0.1:5000

### 配置邮件服务

修改`config.py`文件中的邮件服务器配置：

```python
# 邮件服务器配置
MAIL_SERVER = 'your-mail-server.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@example.com'
MAIL_PASSWORD = 'your-password'
```

或者通过环境变量设置：

```bash
export MAIL_SERVER=smtp.example.com
export MAIL_PORT=587
export MAIL_USE_TLS=True
export MAIL_USERNAME=your-email@example.com
export MAIL_PASSWORD=your-password
```

## 项目结构

项目采用Flask框架，主要文件说明：
- `application.py`：应用主模块，创建和配置Flask应用
- `run.py`：应用启动脚本
- `models.py`：定义数据模型
- `config.py`：配置文件
- `app/`：应用功能模块，包含蓝图
  - `app/auth/`：用户认证模块
  - `app/mail.py`：邮件发送模块
- `templates/`：HTML模板
- `static/`：静态文件（CSS、JS、图片等）
- `tests/`：测试代码

> 注意：为避免与`app`包冲突，我们将主应用文件从`app.py`重命名为`application.py`

## 项目功能

### 用户认证系统

- 用户注册（支持邮箱验证）
- 用户登录
- 密码重置
- 个人信息管理

#### 邮箱验证流程

1. 用户在注册页面输入邮箱地址
2. 点击"发送验证码"按钮
3. 系统发送6位数字验证码到用户邮箱
4. 用户输入收到的验证码完成注册

可以通过以下API测试邮件功能：
```
POST /mail/test
Content-Type: application/json

{
  "email": "your-email@example.com"
}
```

### 项目众筹模块

- 项目创建与管理
- 项目展示与搜索
- 众筹支持功能
- 众筹进度追踪

### 团队组建模块

- 团队创建与管理
- 团队成员招募
- 团队项目展示
- 团队交流工具

### 社交互动模块

- 用户关注功能
- 项目点赞与评论
- 消息通知系统
- 活动发布与报名

### 支付系统

- 安全支付流程
- 多种支付方式支持
- 交易记录查询
- 资金退回机制

## API文档

API文档访问地址：http://127.0.0.1:5000/api/docs

主要API模块包括：

- 众筹模块API：项目管理、众筹数据查询
- 团队模块API：团队管理、成员管理
- 社交模块API：互动功能接口
- 支付模块API：交易相关接口

大部分API需要用户登录后才能访问，请在请求头中携带认证信息。

API示例：
```
# 获取所有众筹项目
GET /api/crowdfunding/projects

# 创建新团队
POST /api/team/create
```

## 测试

运行测试：
```bash
pytest
```

## 贡献指南

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交Pull Request

## 许可证

MIT 

# run.py
import os
import app as app_module  # 导入app.py作为模块，避免与app包冲突
app = app_module.app  # 从模块中获取app实例

if __name__ == '__main__':
    app.run(debug=True)