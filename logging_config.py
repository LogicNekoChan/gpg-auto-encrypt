#!/usr/bin/env python3
import logging
import logging.handlers
from pathlib import Path

def setup_logging(level='INFO'):
    log_dir = Path('/app/logs')
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件（按日轮转）
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
