#!/usr/bin/env python3
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from encryptor import GPGEncryptor
from config import Config

class DirectoryWatcher:
    def __init__(self, config: Config, encryptor: GPGEncryptor):
        self.config = config
        self.encryptor = encryptor
        self.logger = logging.getLogger(__name__)
        self.observer = None

    def start(self):
        """启动监控"""
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

    def process_existing_files(self):
        """服务启动时处理已存在的文件"""
        self.logger.info("检查已存在的文件...")
        input_path = Path(self.config.input_dir)

        for item in input_path.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                self.process_item(item)

    def process_item(self, item_path: Path):
        """加密并处理单个文件或目录"""
        try:
            relative_path = item_path.relative_to(self.config.input_dir)
            output_path = Path(self.config.output_dir) / relative_path.parent

            if item_path.is_file():
                success = self.encryptor.encrypt_file(item_path, output_path)
            elif item_path.is_dir():
                success = self.encryptor.encrypt_directory(item_path, output_path)
            else:
                self.logger.warning(f"跳过非文件/目录项: {item_path}")
                return

            if success and self.config.delete_after_encrypt:
                self.encryptor.delete_original(item_path)

        except Exception as e:
            self.logger.error(f"处理项目失败 {item_path}: {e}")


class EncryptEventHandler(FileSystemEventHandler):
    def __init__(self, config: Config, encryptor: GPGEncryptor):
        self.config = config
        self.encryptor = encryptor
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        """文件或目录创建事件"""
        if not event.is_directory:
            self.logger.info(f"检测到新文件: {event.src_path}")
            time.sleep(1)  # 等待文件写入完成
            self.process_item(Path(event.src_path))

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self.logger.info(f"检测到文件修改: {event.src_path}")
            self.process_item(Path(event.src_path))

    def process_item(self, item_path: Path):
        """处理单个文件"""
        try:
            # 跳过隐藏文件、临时文件、加密文件
            if item_path.name.startswith('.') or item_path.name.endswith('~') or item_path.suffix == '.gpg':
                return

            # 等待文件完全写入（防止大文件）
            time.sleep(2)

            relative_path = item_path.relative_to(self.config.input_dir)
            output_path = Path(self.config.output_dir) / relative_path.parent

            success = self.encryptor.encrypt_file(item_path, output_path)

            if success and self.config.delete_after_encrypt:
                self.encryptor.delete_original(item_path)

        except Exception as e:
            self.logger.error(f"处理文件事件失败 {item_path}: {e}")
