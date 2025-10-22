#!/bin/bash
set -e

echo "🚀 启动 GPG 自动加密服务..."

# 创建必要目录
mkdir -p /app/logs /app/gpg-keys /input /output

# 设置 GPG 目录权限
chmod 700 /app/gpg-keys

# 检查必需环境变量
if [ -z "$GPG_RECIPIENT" ]; then
    echo "❌ 错误：GPG_RECIPIENT 未设置"
    exit 1
fi

# 等待 GPG 密钥导入（如果存在）
if [ -f "/app/gpg-keys/public.key" ]; then
    echo "🔑 导入 GPG 公钥..."
    gpg --import /app/gpg-keys/public.key
fi

if [ -f "/app/gpg-keys/private.key" ]; then
    echo "🔐 导入 GPG 私钥..."
    gpg --batch --import /app/gpg-keys/private.key
fi

# 信任密钥（如果存在）
if [ -n "$GPG_RECIPIENT" ]; then
    echo "✅ 信任密钥 $GPG_RECIPIENT..."
    gpg --batch --yes --command-fd 0 --edit-key "$GPG_RECIPIENT" trust <<EOF
5
y
quit
EOF
fi

# 验证 Python 语法
python -m py_compile /app/app.py

# 启动主程序
exec python /app/app.py
