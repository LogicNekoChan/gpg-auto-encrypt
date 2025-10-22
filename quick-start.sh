#!/usr/bin/env bash
set -eu

# ----------- 同时兼容 docker-compose / docker compose -----------
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

# ----------- 3. 导出公钥（去换行）并写单行文件 -----------
GPG_PUB_FILE=""
if command -v gpg &>/dev/null; then
    mapfile -t keys < <(gpg --list-public-keys --with-colons | awk -F: '$1=="pub"{print $5}')
    if [[ ${#keys[@]} -gt 0 ]]; then
        echo "Found local GPG public keys:"
        for i in "${!keys[@]}"; do
            echo "  $((i+1))) ${keys[i]}"
        done
        read -rp "Select public key to use for encryption (1-${#keys[@]}): " idx
        key_id="${keys[$((idx-1))]}"
        # 去换行写入文件
        gpg --armor --export "$key_id" | tr -d '\n' > gpg-pub.asc
        GPG_PUB_FILE=./gpg-pub.asc
        echo "✅ 公钥已写入 gpg-pub.asc（单行）"
    else
        echo "No local GPG public keys; you can place *.key files manually"
    fi
else
    echo "GPG not installed; you can place *.key files manually"
fi

# ----------- 4. 生成 .env -----------
cat > .env <<EOF
GPG_RECIPIENT=$gpg_recipient
INPUT_DIR=/input
OUTPUT_DIR=/output
DELETE_AFTER_ENCRYPT=true
POLL_INTERVAL=5
LOG_LEVEL=$log_level
EOF

# ----------- 5. 生成 docker-compose.yml（变量已展开） -----------
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
      - ./logs:/app/logs:rw
      - ./gpg-pub.asc:/app/gpg-pub.asc:ro
    environment:
      - GPG_RECIPIENT=${gpg_recipient}
      - INPUT_DIR=/input
      - OUTPUT_DIR=/output
      - DELETE_AFTER_ENCRYPT=true
      - POLL_INTERVAL=5
      - LOG_LEVEL=${log_level}
EOF

# ----------- 6. 启动服务 -----------
echo "Starting container..."
$COMPOSE up -d --build

echo "Done!"
echo "Input : $host_input"
echo "Output: $host_output"
echo "Logs  : $COMPOSE logs -f"
