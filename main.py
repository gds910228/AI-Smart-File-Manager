#!/usr/bin/env python3
"""
AI智能文件管理器 MCP服务器 - FastMCP版本
支持自然语言文件操作指令
"""

import json
import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import mimetypes
from dataclasses import dataclass

# FastMCP导入
from mcp.server.fastmcp import FastMCP
from mcp import types

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-file-manager")

@dataclass
class FileSearchCriteria:
    """文件搜索条件"""
    name_pattern: Optional[str] = None
    file_type: Optional[str] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    path: Optional[str] = None

class NLPProcessor:
    """自然语言处理器"""
    
    def __init__(self):
        self.supported_operations = [
            "search", "find", "list", "move", "copy", "delete", 
            "create", "mkdir", "compress", "extract", "organize"
        ]
        
    def parse_natural_language(self, command: str) -> Dict[str, Any]:
        """解析自然语言指令"""
        command = command.lower().strip()
        
        # 意图识别
        intent = self._identify_intent(command)
        
        # 实体提取
        entities = self._extract_entities(command)
        
        return {
            "intent": intent,
            "entities": entities,
            "original_command": command
        }
    
    def _identify_intent(self, command: str) -> str:
        """识别用户意图"""
        if any(word in command for word in ["找", "搜索", "查找", "find", "search", "locate"]):
            return "search"
        elif any(word in command for word in ["移动", "move", "剪切", "cut"]):
            return "move"
        elif any(word in command for word in ["复制", "copy", "拷贝"]):
            return "copy"
        elif any(word in command for word in ["删除", "delete", "remove", "del"]):
            return "delete"
        elif any(word in command for word in ["创建", "新建", "create", "mkdir", "make"]):
            return "create"
        elif any(word in command for word in ["压缩", "打包", "zip", "compress"]):
            return "compress"
        elif any(word in command for word in ["解压", "解压缩", "unzip", "extract"]):
            return "extract"
        elif any(word in command for word in ["整理", "organize", "sort", "arrange"]):
            return "organize"
        elif any(word in command for word in ["列出", "显示", "list", "show"]):
            return "list"
        else:
            return "unknown"
    
    def _extract_entities(self, command: str) -> Dict[str, Any]:
        """提取实体信息"""
        entities = {}
        
        # 提取文件类型
        file_types = {
            "图片": ["jpg", "jpeg", "png", "gif", "bmp", "svg"],
            "视频": ["mp4", "avi", "mkv", "mov", "wmv", "flv"],
            "文档": ["doc", "docx", "pdf", "txt", "rtf"],
            "表格": ["xls", "xlsx", "csv"],
            "演示": ["ppt", "pptx"],
            "音频": ["mp3", "wav", "flac", "aac"]
        }
        
        for type_name, extensions in file_types.items():
            if type_name in command:
                entities["file_type"] = extensions
                break
        
        # 提取时间信息
        time_patterns = {
            "今天": 0,
            "昨天": 1,
            "前天": 2,
            "上周": 7,
            "上个月": 30,
            "去年": 365
        }
        
        for time_word, days_ago in time_patterns.items():
            if time_word in command:
                entities["date_from"] = datetime.now() - timedelta(days=days_ago)
                if days_ago == 0:  # 今天
                    entities["date_to"] = datetime.now()
                elif days_ago == 1:  # 昨天
                    entities["date_to"] = datetime.now() - timedelta(days=1)
                break
        
        # 提取文件大小
        size_pattern = r"(\d+)(mb|gb|kb|字节|bytes?)"
        size_match = re.search(size_pattern, command, re.IGNORECASE)
        if size_match:
            size_value = int(size_match.group(1))
            size_unit = size_match.group(2).lower()
            
            multiplier = {"kb": 1024, "mb": 1024**2, "gb": 1024**3, "字节": 1, "byte": 1, "bytes": 1}
            size_bytes = size_value * multiplier.get(size_unit, 1)
            
            if "大于" in command or "超过" in command or ">" in command:
                entities["size_min"] = size_bytes
            elif "小于" in command or "少于" in command or "<" in command:
                entities["size_max"] = size_bytes
        
        # 提取路径信息
        path_patterns = [
            r"桌面", r"desktop",
            r"下载", r"downloads?",
            r"文档", r"documents?",
            r"图片", r"pictures?",
            r"[a-zA-Z]:\\[^\\s]*",  # Windows路径
            r"/[^\\s]*"  # Unix路径
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                path_text = match.group()
                # 转换中文路径名
                path_mapping = {
                    "桌面": os.path.join(os.path.expanduser("~"), "Desktop"),
                    "下载": os.path.join(os.path.expanduser("~"), "Downloads"),
                    "文档": os.path.join(os.path.expanduser("~"), "Documents"),
                    "图片": os.path.join(os.path.expanduser("~"), "Pictures")
                }
                entities["path"] = path_mapping.get(path_text, path_text)
                break
        
        # 提取关键词
        # 移除常见的停用词后，剩余的词作为关键词
        stop_words = {"帮我", "请", "把", "将", "所有", "的", "文件", "找到", "查找", "搜索"}
        words = set(command.split()) - stop_words
        if words:
            entities["keywords"] = list(words)
        
        return entities

# 全局实例
nlp_processor = NLPProcessor()

# 创建FastMCP应用实例
app = FastMCP("AI Smart File Manager")

def search_files(criteria: FileSearchCriteria) -> List[Dict[str, Any]]:
    """搜索文件"""
    results = []
    search_path = Path(criteria.path) if criteria.path else Path.home()
    
    try:
        for file_path in search_path.rglob("*"):
            if file_path.is_file():
                if _matches_criteria(file_path, criteria):
                    file_info = _get_file_info(file_path)
                    results.append(file_info)
    except PermissionError as e:
        logger.warning(f"Permission denied accessing {search_path}: {e}")
    
    return results

def _matches_criteria(file_path: Path, criteria: FileSearchCriteria) -> bool:
    """检查文件是否符合搜索条件"""
    # 检查文件名模式
    if criteria.name_pattern:
        if not re.search(criteria.name_pattern, file_path.name, re.IGNORECASE):
            return False
    
    # 检查文件类型
    if criteria.file_type:
        file_ext = file_path.suffix.lower().lstrip('.')
        if file_ext not in criteria.file_type:
            return False
    
    # 检查文件大小
    try:
        file_size = file_path.stat().st_size
        if criteria.size_min and file_size < criteria.size_min:
            return False
        if criteria.size_max and file_size > criteria.size_max:
            return False
    except OSError:
        return False
    
    # 检查修改时间
    try:
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if criteria.date_from and mtime < criteria.date_from:
            return False
        if criteria.date_to and mtime > criteria.date_to:
            return False
    except OSError:
        return False
    
    return True

def _get_file_info(file_path: Path) -> Dict[str, Any]:
    """获取文件信息"""
    try:
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "type": mimetypes.guess_type(str(file_path))[0] or "unknown"
        }
    except OSError as e:
        return {
            "path": str(file_path),
            "name": file_path.name,
            "error": str(e)
        }

# FastMCP工具定义

@app.tool()
def natural_language_file_operation(command: str) -> str:
    """Execute file operations using natural language commands
    
    Args:
        command: Natural language command for file operation
    """
    try:
        parsed = nlp_processor.parse_natural_language(command)
        
        intent = parsed["intent"]
        entities = parsed["entities"]
        
        if intent == "search" or intent == "find" or intent == "list":
            criteria = FileSearchCriteria(
                name_pattern="|".join(entities.get("keywords", [])) if entities.get("keywords") else None,
                file_type=entities.get("file_type"),
                size_min=entities.get("size_min"),
                size_max=entities.get("size_max"),
                date_from=entities.get("date_from"),
                date_to=entities.get("date_to"),
                path=entities.get("path")
            )
            results = search_files(criteria)
            return json.dumps(results, indent=2, ensure_ascii=False)
        
        elif intent == "unknown":
            return f"无法理解指令: {command}\n支持的操作: 搜索、移动、复制、删除、创建、压缩文件"
        
        else:
            return f"解析结果: {json.dumps(parsed, indent=2, ensure_ascii=False)}"
    
    except Exception as e:
        logger.error(f"Error in natural_language_file_operation: {e}")
        return f"Error: {str(e)}"

@app.tool()
def search_files_advanced(
    name_pattern: Optional[str] = None,
    file_type: Optional[List[str]] = None,
    path: Optional[str] = None,
    size_min: Optional[int] = None,
    size_max: Optional[int] = None
) -> str:
    """Search for files based on criteria
    
    Args:
        name_pattern: File name pattern to match
        file_type: List of file extensions to search for
        path: Directory path to search in
        size_min: Minimum file size in bytes
        size_max: Maximum file size in bytes
    """
    try:
        criteria = FileSearchCriteria(
            name_pattern=name_pattern,
            file_type=file_type,
            path=path,
            size_min=size_min,
            size_max=size_max
        )
        results = search_files(criteria)
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in search_files_advanced: {e}")
        return f"Error: {str(e)}"

@app.tool()
def move_files(source_paths: List[str], destination: str) -> str:
    """Move files to a destination directory
    
    Args:
        source_paths: List of source file paths to move
        destination: Destination directory path
    """
    try:
        results = {"success": [], "failed": []}
        dest_path = Path(destination)
        
        # 确保目标目录存在
        dest_path.mkdir(parents=True, exist_ok=True)
        
        for source in source_paths:
            try:
                source_path = Path(source)
                if source_path.exists():
                    dest_file = dest_path / source_path.name
                    shutil.move(str(source_path), str(dest_file))
                    results["success"].append({"from": source, "to": str(dest_file)})
                else:
                    results["failed"].append({"path": source, "error": "File not found"})
            except Exception as e:
                results["failed"].append({"path": source, "error": str(e)})
        
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in move_files: {e}")
        return f"Error: {str(e)}"

@app.tool()
def copy_files(source_paths: List[str], destination: str) -> str:
    """Copy files to a destination directory
    
    Args:
        source_paths: List of source file paths to copy
        destination: Destination directory path
    """
    try:
        results = {"success": [], "failed": []}
        dest_path = Path(destination)
        
        # 确保目标目录存在
        dest_path.mkdir(parents=True, exist_ok=True)
        
        for source in source_paths:
            try:
                source_path = Path(source)
                if source_path.exists():
                    if source_path.is_file():
                        dest_file = dest_path / source_path.name
                        shutil.copy2(str(source_path), str(dest_file))
                        results["success"].append({"from": source, "to": str(dest_file)})
                    elif source_path.is_dir():
                        dest_dir = dest_path / source_path.name
                        shutil.copytree(str(source_path), str(dest_dir))
                        results["success"].append({"from": source, "to": str(dest_dir)})
                else:
                    results["failed"].append({"path": source, "error": "Path not found"})
            except Exception as e:
                results["failed"].append({"path": source, "error": str(e)})
        
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in copy_files: {e}")
        return f"Error: {str(e)}"

@app.tool()
def delete_files(file_paths: List[str]) -> str:
    """Delete files or directories
    
    Args:
        file_paths: List of file or directory paths to delete
    """
    try:
        results = {"success": [], "failed": []}
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(str(path))
                    results["success"].append(file_path)
                else:
                    results["failed"].append({"path": file_path, "error": "Path not found"})
            except Exception as e:
                results["failed"].append({"path": file_path, "error": str(e)})
        
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in delete_files: {e}")
        return f"Error: {str(e)}"

@app.tool()
def create_directory(dir_path: str) -> str:
    """Create a new directory
    
    Args:
        dir_path: Path of the directory to create
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        result = {"success": True, "path": dir_path}
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in create_directory: {e}")
        result = {"success": False, "error": str(e)}
        return json.dumps(result, indent=2, ensure_ascii=False)

@app.tool()
def compress_files(file_paths: List[str], output_path: str) -> str:
    """Compress files into a ZIP archive
    
    Args:
        file_paths: List of file or directory paths to compress
        output_path: Output ZIP file path
    """
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                path = Path(file_path)
                if path.exists():
                    if path.is_file():
                        zipf.write(str(path), path.name)
                    elif path.is_dir():
                        for file in path.rglob("*"):
                            if file.is_file():
                                zipf.write(str(file), str(file.relative_to(path.parent)))
        
        result = {"success": True, "output": output_path}
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in compress_files: {e}")
        result = {"success": False, "error": str(e)}
        return json.dumps(result, indent=2, ensure_ascii=False)

@app.tool()
def extract_archive(archive_path: str, destination: str) -> str:
    """Extract files from a ZIP archive
    
    Args:
        archive_path: Path to the ZIP archive to extract
        destination: Directory to extract files to
    """
    try:
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            zipf.extractall(str(dest_path))
        
        result = {"success": True, "destination": destination}
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in extract_archive: {e}")
        result = {"success": False, "error": str(e)}
        return json.dumps(result, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    app.run()
