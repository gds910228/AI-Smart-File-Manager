#!/usr/bin/env python3
"""
AI智能文件管理器工具函数
"""

import os
import re
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import Config

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def parse_size_string(size_str: str) -> Optional[int]:
    """解析大小字符串为字节数"""
    size_pattern = r"(\d+(?:\.\d+)?)\s*(b|byte|bytes|字节|kb|mb|gb|tb)"
    match = re.search(size_pattern, size_str.lower())
    
    if not match:
        return None
    
    size_value = float(match.group(1))
    size_unit = match.group(2).lower()
    
    multiplier = Config.SIZE_UNITS.get(size_unit, 1)
    return int(size_value * multiplier)

def is_safe_path(path: str) -> bool:
    """检查路径是否安全"""
    path = os.path.abspath(path)
    
    for protected in Config.PROTECTED_PATHS:
        if path.startswith(protected):
            return False
    
    return True

def get_file_type_category(file_path: Path) -> str:
    """获取文件类型分类"""
    extension = file_path.suffix.lower().lstrip('.')
    
    for category, extensions in Config.FILE_TYPE_MAPPING.items():
        if extension in extensions:
            return category
    
    return "其他"

def extract_keywords_from_text(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 移除常见停用词
    stop_words = {
        "帮我", "请", "把", "将", "所有", "的", "文件", "找到", "查找", "搜索",
        "help", "me", "please", "all", "the", "file", "files", "find", "search",
        "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"
    }
    
    # 使用正则表达式提取单词
    words = re.findall(r'\b\w+\b', text.lower())
    
    # 过滤停用词和短词
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    return list(set(keywords))  # 去重

def parse_time_expression(text: str) -> Optional[datetime]:
    """解析时间表达式"""
    text = text.lower()
    
    for expression, days_ago in Config.TIME_EXPRESSIONS.items():
        if expression in text:
            return datetime.now() - timedelta(days=days_ago)
    
    # 尝试解析具体日期
    date_patterns = [
        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
        r"(\d{1,2})/(\d{1,2})/(\d{4})",  # MM/DD/YYYY
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",  # YYYY年MM月DD日
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if "年" in pattern:
                    year, month, day = map(int, match.groups())
                elif pattern.startswith(r"(\d{4})"):
                    year, month, day = map(int, match.groups())
                else:
                    month, day, year = map(int, match.groups())
                
                return datetime(year, month, day)
            except ValueError:
                continue
    
    return None

def get_mime_type(file_path: Path) -> str:
    """获取文件MIME类型"""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"

def validate_file_operation(operation: str, paths: List[str]) -> Dict[str, Any]:
    """验证文件操作的安全性"""
    result = {"valid": True, "errors": []}
    
    # 检查操作类型
    if operation not in Config.SUPPORTED_OPERATIONS:
        result["valid"] = False
        result["errors"].append(f"不支持的操作: {operation}")
    
    # 检查路径安全性
    for path in paths:
        if not is_safe_path(path):
            result["valid"] = False
            result["errors"].append(f"不安全的路径: {path}")
        
        # 检查路径是否存在（对于某些操作）
        if operation in ["move", "copy", "delete"] and not os.path.exists(path):
            result["valid"] = False
            result["errors"].append(f"路径不存在: {path}")
    
    return result

def create_backup_name(original_path: str) -> str:
    """创建备份文件名"""
    path = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if path.is_file():
        stem = path.stem
        suffix = path.suffix
        return f"{stem}_backup_{timestamp}{suffix}"
    else:
        return f"{path.name}_backup_{timestamp}"

def get_directory_size(directory: Path) -> int:
    """计算目录大小"""
    total_size = 0
    try:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except (PermissionError, OSError):
        pass
    
    return total_size

def is_hidden_file(file_path: Path) -> bool:
    """检查是否为隐藏文件"""
    return file_path.name.startswith('.')

def get_file_permissions(file_path: Path) -> Dict[str, bool]:
    """获取文件权限信息"""
    try:
        stat = file_path.stat()
        return {
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK),
            "executable": os.access(file_path, os.X_OK),
        }
    except OSError:
        return {"readable": False, "writable": False, "executable": False}

def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # Windows和Unix系统的非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # 移除前后空格和点
    cleaned = cleaned.strip('. ')
    
    # 确保文件名不为空
    if not cleaned:
        cleaned = "unnamed_file"
    
    return cleaned

def group_files_by_type(file_paths: List[str]) -> Dict[str, List[str]]:
    """按文件类型分组"""
    groups = {}
    
    for file_path in file_paths:
        path = Path(file_path)
        category = get_file_type_category(path)
        
        if category not in groups:
            groups[category] = []
        
        groups[category].append(file_path)
    
    return groups