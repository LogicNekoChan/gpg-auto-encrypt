#!/usr/bin/env python3
import os
import signal
import sys
import time
import logging
from pathlib import Path

from config import Config
from encryptor import GPGEncryptor
from watcher import DirectoryWatcher
from logging_config import setup_logging

class AutoEncryptorService:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.encryptor = GPGEncryptor(self.config)
        self.watcher = DirectoryWatcher(self.config, self.encryptor)
        self.running = False
        
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        self.logger.info(f"收到信号 {signum}，正在关闭服务...")
        self.running = False
        
    def run(self):
        """运行服务"""
        self.logger.info("启动自动GPG加密服务...")
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # 创建PID文件
        pid_file = Path("/app/app.pid")
        pid_file.write_text(str(os.getpid()))
        
        try:
            self.running = True
            self.watcher.start()
            
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"服务运行错误: {e}")
        finally:
            self.watcher.stop()
            pid_file.unlink(missing_ok=True)
            self.logger.info("服务已停止")

if __name__ == "__main__":
    setup_logging()
    service = AutoEncryptorService()
    service.run()
