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
        self.process_existing_files()

    def stop(self):
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

    # ---------- 稳定期工具 ----------
    @staticmethod
    def wait_until_stable(path: Path, stable_sec: int = 3, check_interval: int = 1):
        """文件大小连续 stable_sec 秒不变才返回"""
        last_size = -1
        stable_since = None
        while True:
            try:
                current_size = path.stat().st_size
            except FileNotFoundError:
                return False
            if current_size == last_size:
                if stable_since and (time.time() - stable_since) >= stable_sec:
                    return True
            else:
                stable_since = time.time()
                last_size = current_size
            time.sleep(check_interval)

    # ---------- 事件回调 ----------
    def on_created(self, event):
        if not event.is_directory:
            self.logger.info(f"检测到新文件: {event.src_path}")
            self.process_item(Path(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self.logger.info(f"检测到文件修改: {event.src_path}")
            self.process_item(Path(event.src_path))

    # ---------- 真正处理 ----------
    def process_item(self, item_path: Path):
        try:
            # 跳过隐藏、临时、已加密
            if item_path.name.startswith('.') or item_path.name.endswith(('~', '.tmp', '.filepart', '.gpg')):
                return

            # 等大文件写完
            if not self.wait_until_stable(item_path, stable_sec=3):
                self.logger.warning(f"文件未稳定或已被删除：{item_path}")
                return

            relative_path = item_path.relative_to(self.config.input_dir)
            output_path = Path(self.config.output_dir) / relative_path.parent

            success = self.encryptor.encrypt_file(item_path, output_path)
            if success and self.config.delete_after_encrypt:
                self.encryptor.delete_original(item_path)

        except Exception as e:
            self.logger.error(f"处理文件事件失败 {item_path}: {e}")
