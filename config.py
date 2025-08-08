#!/usr/bin/env python3
"""
AI智能文件管理器配置文件
"""

import os
from pathlib import Path

class Config:
    """配置类"""
    
    # 服务器配置
    SERVER_NAME = "ai-file-manager"
    SERVER_VERSION = "1.0.0"
    
    # 默认搜索路径
    DEFAULT_SEARCH_PATHS = {
        "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
        "videos": os.path.join(os.path.expanduser("~"), "Videos"),
        "music": os.path.join(os.path.expanduser("~"), "Music"),
    }
    
    # 文件类型映射
    FILE_TYPE_MAPPING = {
        "图片": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff"],
        "视频": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
        "文档": ["doc", "docx", "pdf", "txt", "rtf", "odt", "pages"],
        "表格": ["xls", "xlsx", "csv", "ods", "numbers"],
        "演示": ["ppt", "pptx", "odp", "key"],
        "音频": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"],
        "代码": ["py", "js", "html", "css", "java", "cpp", "c", "php", "rb", "go"],
        "压缩": ["zip", "rar", "7z", "tar", "gz", "bz2"],
        "图像": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff"],
        "picture": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff"],
        "video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
        "document": ["doc", "docx", "pdf", "txt", "rtf", "odt", "pages"],
        "audio": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"],
        "code": ["py", "js", "html", "css", "java", "cpp", "c", "php", "rb", "go"],
        "archive": ["zip", "rar", "7z", "tar", "gz", "bz2"],
    }
    
    # 时间表达式映射
    TIME_EXPRESSIONS = {
        "今天": 0,
        "昨天": 1,
        "前天": 2,
        "上周": 7,
        "上个月": 30,
        "去年": 365,
        "today": 0,
        "yesterday": 1,
        "last week": 7,
        "last month": 30,
        "last year": 365,
    }
    
    # 大小单位映射
    SIZE_UNITS = {
        "b": 1,
        "byte": 1,
        "bytes": 1,
        "字节": 1,
        "kb": 1024,
        "mb": 1024**2,
        "gb": 1024**3,
        "tb": 1024**4,
    }
    
    # 支持的操作
    SUPPORTED_OPERATIONS = [
        "search", "find", "list", "move", "copy", "delete", 
        "create", "mkdir", "compress", "extract", "organize",
        "搜索", "查找", "列出", "移动", "复制", "删除",
        "创建", "新建", "压缩", "解压", "整理"
    ]
    
    # 安全设置
    PROTECTED_PATHS = [
        "/System",
        "/Windows",
        "/Program Files",
        "/Program Files (x86)",
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
    ]
    
    # 最大文件大小限制 (10GB)
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024
    
    # 最大搜索结果数量
    MAX_SEARCH_RESULTS = 1000
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"