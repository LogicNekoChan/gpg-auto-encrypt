#!/usr/bin/env python3
import gnupg
import os
import logging
from pathlib import Path
import shutil

class GPGEncryptor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.gpg = gnupg.GPG(gnupghome=config.gpg_home)
        self.gpg.encoding = 'utf-8'
        
    def encrypt_file(self, file_path: Path, output_dir: Path) -> bool:
        """加密单个文件"""
        try:
            self.logger.info(f"开始加密文件: {file_path}")
            
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 读取文件
            with open(file_path, 'rb') as f:
                status = self.gpg.encrypt_file(
                    f,
                    recipients=[self.config.gpg_recipient],
                    output=str(output_dir / f"{file_path.name}.gpg"),
                    armor=False
                )
            
            if status.ok:
                self.logger.info(f"文件加密成功: {file_path}")
                return True
            else:
                self.logger.error(f"文件加密失败: {file_path}, 错误: {status.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"加密文件时出错 {file_path}: {e}")
            return False
            
    def encrypt_directory(self, dir_path: Path, output_dir: Path) -> bool:
        """加密整个目录（打包成tar后加密）"""
        try:
            self.logger.info(f"开始加密目录: {dir_path}")
            
            # 创建临时tar文件
            tar_path = dir_path.with_suffix('.tar')
            
            # 打包目录
            shutil.make_archive(
                str(dir_path),
                'tar',
                str(dir_path.parent),
                dir_path.name
            )
            
            # 加密tar文件
            success = self.encrypt_file(tar_path, output_dir)
            
            # 删除临时tar文件
            tar_path.unlink(missing_ok=True)
            
            return success
            
        except Exception as e:
            self.logger.error(f"加密目录时出错 {dir_path}: {e}")
            return False
            
    def delete_original(self, path: Path) -> bool:
        """删除原始文件或目录"""
        try:
            if path.is_file():
                path.unlink()
                self.logger.info(f"已删除原始文件: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                self.logger.info(f"已删除原始目录: {path}")
            return True
        except Exception as e:
            self.logger.error(f"删除原始文件时出错 {path}: {e}")
            return False
