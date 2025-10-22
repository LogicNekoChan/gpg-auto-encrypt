# 使用Python 3.11 slim镜像
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gnupg \
    inotify-tools \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/gpg-keys /app/logs /input /output

# 设置权限
RUN chmod +x entrypoint.sh

# 创建非root用户
RUN groupadd -r encryptor && useradd -r -g encryptor encryptor
RUN chown -R encryptor:encryptor /app /input /output

# 切换到非root用户
USER encryptor

# 设置环境变量
ENV PYTHONPATH=/app
ENV GNUPGHOME=/app/gpg-keys

# 启动脚本
ENTRYPOINT ["./entrypoint.sh"]
