from pathlib import Path
from sys import stdout
from loguru import logger

from conf import BASE_DIR
from pathlib import Path as _Path


def log_formatter(record: dict) -> str:
    """
    Formatter for log records.
    :param dict record: Log object containing log metadata & message.
    :returns: str
    """
    colors = {
        "TRACE": "#cfe2f3",
        "INFO": "#9cbfdd",
        "DEBUG": "#8598ea",
        "WARNING": "#dcad5a",
        "SUCCESS": "#3dd08d",
        "ERROR": "#ae2c2c"
    }
    color = colors.get(record["level"].name, "#b3cfe7")
    return f"<fg #70acde>{{time:YYYY-MM-DD HH:mm:ss}}</fg #70acde> | <fg {color}>{{level}}</fg {color}>: <light-white>{{message}}</light-white>\n"


def create_logger(log_name: str, file_path: str):
    """
    Create custom logger for different business modules.
    :param str log_name: name of log
    :param str file_path: Optional path to log file
    :returns: Configured logger
    """
    def filter_record(record):
        return record["extra"].get("business_name") == log_name

    Path(BASE_DIR / file_path).parent.mkdir(exist_ok=True)
    logger.add(Path(BASE_DIR / file_path), filter=filter_record, level="INFO", rotation="10 MB", retention="10 days", backtrace=True, diagnose=True)
    return logger.bind(business_name=log_name)


# Remove all existing handlers
logger.remove()
# Add a standard console handler
logger.add(stdout, colorize=True, format=log_formatter)

douyin_logger = create_logger('douyin', 'logs/douyin.log')
tencent_logger = create_logger('tencent', 'logs/tencent.log')
xhs_logger = create_logger('xhs', 'logs/xhs.log')
tiktok_logger = create_logger('tiktok', 'logs/tiktok.log')
bilibili_logger = create_logger('bilibili', 'logs/bilibili.log')
kuaishou_logger = create_logger('kuaishou', 'logs/kuaishou.log')
baijiahao_logger = create_logger('baijiahao', 'logs/baijiahao.log')
xiaohongshu_logger = create_logger('xiaohongshu', 'logs/xiaohongshu.log')

# screenshot directories (created on import)
_SCREENSHOT_BASE = BASE_DIR / 'logs'
DOUYIN_SCREENSHOT_DIR = str(_Path(_SCREENSHOT_BASE / 'douyin_screenshot'))
KUAISHOU_SCREENSHOT_DIR = str(_Path(_SCREENSHOT_BASE / 'kuaishou_screenshot'))
TIKTOK_SCREENSHOT_DIR = str(_Path(_SCREENSHOT_BASE / 'tiktok_screenshot'))
XIAOHONGSHU_SCREENSHOT_DIR = str(_Path(_SCREENSHOT_BASE / 'xiaohongshu_screenshot'))

_Path(DOUYIN_SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
_Path(KUAISHOU_SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
_Path(TIKTOK_SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
_Path(XIAOHONGSHU_SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
