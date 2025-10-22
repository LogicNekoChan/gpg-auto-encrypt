#!/usr/bin/env bash
set -eu

# ----------- 兼容 docker-compose / docker compose -----------
compose_cmd(){
    if docker compose version &>/dev/null; then
        echo "docker compose"
    elif command -v docker-compose &>/dev/null; then
        echo "docker-compose"
    else
        echo "ERROR: docker-compose plugin or standalone binary not found" >&2
        exit 1
    fi
}
COMPOSE=$(compose_cmd)

REPO="https://github.com/LogicNekoChan/gpg-auto-encrypt.git"
PROJ_DIR="gpg-auto-encrypt"

# ----------- 1. 拉取/更新代码 -----------
if [[ -d "$PROJ_DIR/.git" ]]; then
    echo "Pulling latest code..."
    git -C "$PROJ_DIR" pull --ff-only
else
    echo "Cloning project..."
    git clone --depth 1 "$REPO" "$PROJ_DIR" || { echo "Git clone failed"; exit 1; }
fi
cd "$PROJ_DIR" || { echo "Project dir not found"; exit 1; }

# ----------- 2. 交互输入 -----------
read -rp "GPG recipient email: " gpg_recipient
read -rp "Log level (INFO/DEBUG) [INFO]: " log_level
log_level=${log_level:-INFO}

read -rp "Host input dir [/data/gpg-input]: " host_input
host_input=${host_input:-/data/gpg-input}
read -rp "Host output dir [/data/gpg-output]: " host_output
host_output=${host_output:-/data/gpg-output}

mkdir -p "$host_input" "$host_output"

# ----------- 3. 生成 .env -----------
cat > .env <<EOF
GPG_RECIPIENT=$gpg_recipient
INPUT_DIR=/input
OUTPUT_DIR=/output
DELETE_AFTER_ENCRYPT=true
POLL_INTERVAL=5
LOG_LEVEL=$log_level
EOF

# ----------- 4. 生成 docker-compose.yml（变量已展开） -----------
# 注意定界符用双引号，Shell 会先展开所有 ${} 再写文件
cat > docker-compose.yml <<EOF
version: '3.8'
services:
  gpg-encryptor:
    build: .
    container_name: gpg-encryptor
    restart: unless-stopped
    volumes:
      - ${host_input}:/input
      - ${host_output}:/output
      - ./gpg-keys:/app/gpg-keys:rw
      - ./logs:/app/logs:rw
    environment:
      - GPG_RECIPIENT=${gpg_recipient}
      - INPUT_DIR=/input
      - OUTPUT_DIR=/output
      - DELETE_AFTER_ENCRYPT=true
      - POLL_INTERVAL=5
      - LOG_LEVEL=${log_level}
EOF

# ----------- 5. 可选 GPG 密钥导出 -----------
if command -v gpg &>/dev/null; then
    mapfile -t keys < <(gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: '$1=="sec"{print $5}')
    if [[ ${#keys[@]} -gt 0 ]]; then
        echo "Found local GPG secret keys:"
        for i in "${!keys[@]}"; do
            echo "  $((i+1))) ${keys[i]}"
        done
        read -rp "Select key number to export (1-${#keys[@]}): " idx
        key_id="${keys[$((idx-1))]}"
        mkdir -p gpg-keys
        gpg --armor --export "$key_id"       > gpg-keys/public.key
        gpg --armor --export-secret-keys "$key_id" > gpg-keys/private.key
        chmod 600 gpg-keys/*.key
        echo "Keys exported to gpg-keys/"
    else
        echo "No local GPG keys found; place *.key files into gpg-keys/ manually"
    fi
else
    echo "GPG not installed; place *.key files into gpg-keys/ manually"
fi

# ----------- 6. 启动服务 -----------
echo "Starting container..."
$COMPOSE up -d --build

echo "Done!"
echo "Input : $host_input"
echo "Output: $host_output"
echo "Logs  : $COMPOSE logs -f"
