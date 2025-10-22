# 🔐 GPG 自动加密服务（Docker 版）

自动监控 `/input` 目录，发现新文件或目录后使用 GPG 公钥加密到 `/output`，并**删除原文件**，防止循环加密。

---

## 🧭 快速开始

```bash
# 1. 克隆项目
git clone &lt;your-repo&gt;
cd gpg-auto-encrypt

# 2. 配置环境
cp .env.example .env
# 编辑 .env，设置 GPG_RECIPIENT=your@email.com

# 3. 导入公钥（一次性）
cp your-public.key gpg-keys/public.key

# 4. 启动服务
docker-compose up -d

# 5. 测试
echo "hello" &gt; input/test.txt
ls output/  # 应该看到 test.txt.gpg
