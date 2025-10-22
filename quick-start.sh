#!/usr/bin/env bash
set -e

REPO="https://github.com/LogicNekoChan/gpg-auto-encrypt.git"
DIR="gpg-auto-encrypt"

# ----------- 克隆/更新 -----------
if [[ -d "$DIR" ]]; then
    echo "📂 目录已存在，拉取最新代码..."
    git -C "$DIR" pull
else
    echo "📥 克隆仓库..."
    git clone "$REPO" "$DIR"
fi
cd "$DIR"

# ----------- 交互输入 -----------
read -rp "🔑 GPG 收件人邮箱（GPG_RECIPIENT）: " gpg_recipient
read -rp "🗂️ 日志级别（INFO/DEBUG）[INFO] : " log_level
log_level=${log_level:-INFO}

# ✅ 自定义映射目录
read -rp "📂 宿主机输入目录（/input 映射）[/data/gpg-input] : " host_input
host_input=${host_input:-/data/gpg-input}
read -rp "📂 宿主机输出目录（/output 映射）[/data/gpg-output] : " host_output
host_output=${host_output:-/data/gpg-output}

# ----------- 创建宿主机目录 -----------
mkdir -p "$host_input" "$host_output"

# ----------- 写 .env -----------
cat > .env <<EOF
GPG_RECIPIENT=$gpg_recipient
INPUT_DIR=/input
OUTPUT_DIR=/output
DELETE_AFTER_ENCRYPT=true
POLL_INTERVAL=5
LOG_LEVEL=$log_level
EOF

# ----------- 写 docker-compose.override.yml 覆盖映射 -----------
cat > docker-compose.override.yml <<EOF
version: '3.8'
services:
  gpg-encryptor:
    volumes:
      - ${host_input}:/input
      - ${host_output}:/output
EOF

# ----------- 本机 GPG 密钥检测与选择 -----------
echo "🔍 检测本机 GPG 密钥..."
if ! command -v gpg &>/dev/null; then
    echo "⚠️  本机未安装 GPG，跳过密钥选择；请手动把 *.key 文件放进 $(pwd)/gpg-keys/"
else
    mapfile -t keys < <(gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: '$1=="sec"{print $5}')
    if [[ ${#keys[@]} -eq 0 ]]; then
        echo "⚠️  本机未发现 GPG 私钥，请手动把 *.key 文件放进 $(pwd)/gpg-keys/"
    else
        echo "发现以下私钥（公钥同步列出）："
        for i in "${!keys[@]}"; do
            echo "  $((i+1))) ${keys[i]}"
        done
        read -rp "请选择要导出的密钥编号（1-${#keys[@]}）：" idx
        key_id="${keys[$((idx-1))]}"
        echo "正在导出密钥到 $(pwd)/gpg-keys/ ..."
        mkdir -p gpg-keys
        gpg --armor --export "$key_id" > gpg-keys/public.key
        gpg --armor --export-secret-keys "$key_id" > gpg-keys/private.key
        chmod 600 gpg-keys/*.key
        echo "✅ 密钥已导出至 $(pwd)/gpg-keys/"
    fi
fi

# ----------- 可选补充导入提示 -----------
echo "📎 如需补充或替换密钥，请把 *.key 文件放进 $(pwd)/gpg-keys/ 目录，然后按回车继续..."
read -rp "（无操作可直接回车）"

# ----------- 启动服务 -----------
echo "🚀 构建并启动容器..."
docker compose up -d --build

echo "✅ 服务已后台启动！"
echo "宿主机输入目录 : $host_input"
echo "宿主机输出目录 : $host_output"
echo "查看日志       : docker-compose logs -f"
