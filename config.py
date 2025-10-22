#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Config:
    def __init__(self):
        # 基础目录配置
        self.input_dir = Path(os.getenv('INPUT_DIR', '/input'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR', '/output'))
        self.gpg_home = Path(os.getenv('GNUPGHOME', '/app/gpg-keys'))
        self.temp_dir = Path(os.getenv('TEMP_DIR', '/tmp/encryptor'))
        
        # GPG配置
        self.gpg_recipient = os.getenv('GPG_RECIPIENT', '')
        self.gpg_sign = os.getenv('GPG_SIGN', 'false').lower() == 'true'
        self.gpg_signer = os.getenv('GPG_SIGNER', '')
        
        # 加密选项
        self.cipher_algo = os.getenv('CIPHER_ALGO', 'AES256')
        self.compress_algo = os.getenv('COMPRESS_ALGO', '2')
        self.armor = os.getenv('ARMOR', 'false').lower() == 'true'
        
        # 行为配置
        self.delete_after_encrypt = os.getenv('DELETE_AFTER_ENCRYPT', 'true').lower() == 'true'
        self.preserve_permissions = os.getenv('PRESERVE_PERMISSIONS', 'true').lower() == 'true'
        self.create_backup = os.getenv('CREATE_BACKUP', 'false').lower() == 'true'
        self.backup_dir = Path(os.getenv('BACKUP_DIR', '/backup'))
        
        # 监控配置
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '5'))
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '1073741824'))  # 1GB
        self.allowed_extensions = self._parse_extensions(os.getenv('ALLOWED_EXTENSIONS', ''))
        self.excluded_patterns = self._parse_patterns(os.getenv('EXCLUDED_PATTERNS', '.tmp,.temp,~'))
        
        # 性能配置
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.worker_threads = int(os.getenv('WORKER_THREADS', '2'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        
        # 通知配置
        self.email_notify = os.getenv('EMAIL_NOTIFY', 'false').lower() == 'true'
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_pass = os.getenv('SMTP_PASS', '')
        self.notify_email = os.getenv('NOTIFY_EMAIL', '')
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_max_size = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
        self.log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # 验证配置
        self.validate()
        
    def _parse_extensions(self, extensions_str: str) -> List[str]:
        """解析允许的文件扩展名"""
        if not extensions_str:
            return []
        return [ext.strip().lower() for ext in extensions_str.split(',')]
        
    def _parse_patterns(self, patterns_str: str) -> List[str]:
        """解析排除模式"""
        if not patterns_str:
            return []
        return [pattern.strip() for pattern in patterns_str.split(',')]
        
    def validate(self):
        """验证配置"""
        if not self.gpg_recipient:
            raise ValueError("GPG_RECIPIENT 环境变量必须设置")
            
        if self.gpg_sign and not self.gpg_signer:
            raise ValueError("启用签名时需要设置 GPG_SIGNER")
            
        # 创建必要的目录
        for directory in [self.input_dir, self.output_dir, self.temp_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
