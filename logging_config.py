#!/usr/bin/env python3
import logging
import logging.handlers
from pathlib import Path

def setup_logging(level='INFO'):
    """配置日志：目录可写就用文件，不可写就只用控制台"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台必须保留
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件日志：目录可写才启用
    log_dir = Path('/app/logs')
    try:
        log_dir.mkdir(exist_ok=True)
        # 测试写权限
        (log_dir / '.write_test').write_text('test')
        (log_dir / '.write_test').unlink()

        # 按日轮转
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / 'encryptor.log',
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'error.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    except (PermissionError, OSError):
        # 不可写就只用控制台
        logger.warning("Log directory not writable, using console only.")

    return logger
