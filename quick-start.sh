#!/usr/bin/env bash
set -e

REPO="https://github.com/LogicNekoChan/gpg-auto-encrypt.git"
DIR="gpg-auto-encrypt"

if [[ -d "$DIR" ]]; then
    echo "📂 目录已存在，拉取最新代码..."
    git -C "$DIR" pull
else
    echo "📥 克隆仓库..."
    git clone "$REPO" "$DIR"
fi
cd "$DIR"

# ---------------- 交互输入 ----------------
read -rp "🔑  GPG 收件人邮箱（GPG_RECIPIENT）: " gpg_recipient
read -rp "🗂️   日志级别（INFO/DEBUG）[INFO] : " log_level
log_level=${log_level:-INFO}

# ---------------- 写 .env ----------------
cat > .env <<EOF
GPG_RECIPIENT=$gpg_recipient
INPUT_DIR=/input
OUTPUT_DIR=/output
DELETE_AFTER_ENCRYPT=true
POLL_INTERVAL=5
LOG_LEVEL=$log_level
EOF

# ---------------- 导入公钥（可选） ----------------
echo "📎 如需导入公钥，请把 *.key 文件放到 $(pwd)/gpg-keys/ 目录下，然后按回车继续..."
read -rp "（若无公钥可直接回车）"

# ---------------- 启动 ----------------
echo "🚀 构建并启动容器..."
docker-compose up -d --build

echo "✅ 服务已后台启动！"
echo "查看日志：docker-compose logs -f"
