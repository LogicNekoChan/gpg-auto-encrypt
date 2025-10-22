#!/usr/bin/env python3
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DirectoryWatcher:
    def __init__(self, config, encryptor):
        self.config = config
        self.encryptor = encryptor
        self.logger = logging.getLogger(__name__)
        self.observer = None
        
    def start(self):
        """开始监控目录"""
        self.logger.info(f"开始监控目录: {self.config.input_dir}")
        
        event_handler = EncryptEventHandler(self.config, self.encryptor)
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            str(self.config.input_dir),
            recursive=True
        )
        self.observer.start()
        
        # 处理已存在的文件
        self.process_existing_files()
        
    def stop(self):
        """停止监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("目录监控已停止")
            
    def
