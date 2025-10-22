# 🔐 GPG 自动加密服务（Docker 版）

自动监控 `/input` 目录，发现新文件或目录后使用 GPG 公钥加密到 `/output`，并**删除原文件**，防止循环加密。

---

## 🧭 快速开始

```bash

bash <(curl -fsSL https://raw.githubusercontent.com/LogicNekoChan/gpg-auto-encrypt/main/quick-start.sh)
