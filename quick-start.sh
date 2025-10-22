#!/usr/bin/env bash
set -e

# ----------- 兼容 docker-compose / docker compose -----------
compose_cmd(){
    if docker compose version &>/dev/null; then
        echo "docker compose"
    elif command -v docker-compose &>/dev/null; then
        echo "docker-compose"
    else
        echo "❌ 未安装 docker-compose 插件，也没有独立二进制" >&2
        exit 1
    fi
}
COMPOSE=$(compose_cmd)

# ----------- 交互输入 -----------
read -rp "🔑 GPG 收件人邮箱（GPG_RECIPIENT）: " gpg_recipient
read -rp "🗂️ 日志级别（INFO/DEBUG）[INFO] : " log_level
log_level=${log_level:-INFO}

read -rp "📂 宿主机输入目录（/input 映射）[/data/gpg-input] : " host_input
host_input=${host_input:-/data/gpg-input}
read -rp "📂 宿主机输出目录（/output 映射）[/data/gpg-output] : " host_output
host_output=${host_output:-/data/gpg-output}

mkdir -p "$host_input" "$host_output"

# ----------- 生成 .env -----------
cat > .env <<EOF
GPG_RECIPIENT=$gpg_recipient
INPUT_DIR=/input
OUTPUT_DIR=/output
DELETE_AFTER_ENCRYPT=true
POLL_INTERVAL=5
LOG_LEVEL=$log_level
EOF

# ----------- 生成 docker-compose.override.yml -----------
cat > docker-compose.override.yml <<EOF
version: '3.8'
services:
  gpg-encryptor:
    volumes:
      - ${host_input}:/input
      - ${host_output}:/output
EOF

# ----------- 本机 GPG 密钥检测与导出 -----------
echo "🔍 检测本机 GPG 密钥..."
if command -v gpg &>/dev/null; then
    mapfile -t keys < <(gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: '$1=="sec"{print $5}')
    if [[ ${#keys[@]} -gt 0 ]]; then
        echo "发现以下私钥（公钥同步导出）："
        for i in "${!keys[@]}"; do
            echo "  $((i+1))) ${keys[i]}"
        done
        read -rp "请选择要导出的密钥编号（1-${#keys[@]}）: " idx
        key_id="${keys[$((idx-1))]}"
        mkdir -p gpg-keys
        gpg --armor --export "$key_id"       > gpg-keys/public.key
        gpg --armor --export-secret-keys "$key_id" > gpg-keys/private.key
        chmod 600 gpg-keys/*.key
        echo "✅ 密钥已导出至 gpg-keys/"
    else
        echo "⚠️  本机无 GPG 密钥，请手动将 *.key 文件放入 gpg-keys/ 目录"
    fi
else
    echo "⚠️  本机未安装 GPG，请手动将 *.key 文件放入 gpg-keys/ 目录"
fi

# ----------- 检测 YAML 生成成功 -----------
if [[ -f docker-compose.override.yml && -f .env ]]; then
    echo "✅ 配置文件生成成功"
else
    echo "❌ 配置文件生成失败"
    exit 1
fi

# ----------- 启动服务 -----------
echo "🚀 启动容器..."
$COMPOSE up -d --build

echo "✅ 服务已在后台运行！"
echo "宿主机输入目录 : $host_input"
echo "宿主机输出目录 : $host_output"
echo "查看日志       : $COMPOSE logs -f"
