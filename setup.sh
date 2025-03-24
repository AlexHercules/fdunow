#!/bin/bash

# 复旦创新创业平台快速启动脚本

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "未检测到Python3，请安装Python3.8或更高版本"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate || { echo "激活虚拟环境失败"; exit 1; }

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt || { echo "安装依赖失败"; exit 1; }

# 复制环境变量文件
echo "配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "已创建.env文件，请检查并根据需要修改配置"
else
    echo ".env文件已存在"
fi

# 初始化数据库
echo "初始化数据库..."
flask db init || echo "数据库已初始化，跳过此步骤"
flask db migrate -m "初始化数据库" || { echo "数据库迁移失败"; exit 1; }
flask db upgrade || { echo "数据库升级失败"; exit 1; }

# 部署应用
echo "部署应用基础数据..."
flask deploy || { echo "部署失败"; exit 1; }

# 提示完成
echo "=========================================="
echo "复旦创新创业平台配置完成!"
echo "运行应用: flask run 或 python run.py"
echo "默认管理员账户: admin@fdunow.com"
echo "默认密码: Admin123!"
echo "请务必在生产环境中修改这些默认值"
echo "==========================================" 