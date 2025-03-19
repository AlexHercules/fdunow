# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 复制所有代码到工作目录
COPY . .

# 暴露端口
EXPOSE 5000

# 使用 gunicorn 运行应用
CMD ["gunicorn", "-w", "4", "app:app", "-b", "0.0.0.0:5000"] 