@echo off
REM 复旦创新创业平台快速启动脚本(Windows版)

echo 检查Python环境...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 未检测到Python，请安装Python3.8或更高版本
    exit /b 1
)

echo 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

echo 激活虚拟环境...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo 激活虚拟环境失败
    exit /b 1
)

echo 安装依赖包...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo 安装依赖失败
    exit /b 1
)

echo 配置环境变量...
if not exist .env (
    copy .env.example .env
    echo 已创建.env文件，请检查并根据需要修改配置
) else (
    echo .env文件已存在
)

echo 初始化数据库...
flask db init 2>nul || echo 数据库已初始化，跳过此步骤
flask db migrate -m "初始化数据库"
if %ERRORLEVEL% NEQ 0 (
    echo 数据库迁移失败
    exit /b 1
)
flask db upgrade
if %ERRORLEVEL% NEQ 0 (
    echo 数据库升级失败
    exit /b 1
)

echo 部署应用基础数据...
flask deploy
if %ERRORLEVEL% NEQ 0 (
    echo 部署失败
    exit /b 1
)

echo ==========================================
echo 复旦创新创业平台配置完成!
echo 运行应用: flask run 或 python run.py
echo 默认管理员账户: admin@fdunow.com
echo 默认密码: Admin123!
echo 请务必在生产环境中修改这些默认值
echo ==========================================

pause 