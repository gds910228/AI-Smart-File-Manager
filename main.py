#!/usr/bin/env python3
"""
AI智能文件管理器 MCP服务器
支持自然语言文件操作指令
"""

import asyncio
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re
import mimetypes
from dataclasses import dataclass

# MCP相关导入
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

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

class AIFileManager:
    """AI文件管理器核心类"""
    
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

    def search_files(self, criteria: FileSearchCriteria) -> List[Dict[str, Any]]:
        """搜索文件"""
        results = []
        search_path = Path(criteria.path) if criteria.path else Path.home()
        
        try:
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    if self._matches_criteria(file_path, criteria):
                        file_info = self._get_file_info(file_path)
                        results.append(file_info)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing {search_path}: {e}")
        
        return results
    
    def _matches_criteria(self, file_path: Path, criteria: FileSearchCriteria) -> bool:
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
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
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
    
    def move_files(self, source_paths: List[str], destination: str) -> Dict[str, Any]:
        """移动文件"""
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
        
        return results
    
    def copy_files(self, source_paths: List[str], destination: str) -> Dict[str, Any]:
        """复制文件"""
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
        
        return results
    
    def delete_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """删除文件"""
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
        
        return results
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": dir_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def compress_files(self, file_paths: List[str], output_path: str) -> Dict[str, Any]:
        """压缩文件"""
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
            
            return {"success": True, "output": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

# 创建MCP服务器实例
server = Server("ai-file-manager")
file_manager = AIFileManager()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="natural_language_file_operation",
            description="Execute file operations using natural language commands",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Natural language command for file operation"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files based on criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_pattern": {"type": "string", "description": "File name pattern"},
                    "file_type": {"type": "array", "items": {"type": "string"}, "description": "File extensions"},
                    "path": {"type": "string", "description": "Search path"},
                    "size_min": {"type": "integer", "description": "Minimum file size in bytes"},
                    "size_max": {"type": "integer", "description": "Maximum file size in bytes"}
                }
            }
        ),
        Tool(
            name="move_files",
            description="Move files to a destination",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_paths": {"type": "array", "items": {"type": "string"}},
                    "destination": {"type": "string"}
                },
                "required": ["source_paths", "destination"]
            }
        ),
        Tool(
            name="copy_files",
            description="Copy files to a destination",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_paths": {"type": "array", "items": {"type": "string"}},
                    "destination": {"type": "string"}
                },
                "required": ["source_paths", "destination"]
            }
        ),
        Tool(
            name="delete_files",
            description="Delete files or directories",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["file_paths"]
            }
        ),
        Tool(
            name="compress_files",
            description="Compress files into a ZIP archive",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {"type": "array", "items": {"type": "string"}},
                    "output_path": {"type": "string"}
                },
                "required": ["file_paths", "output_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        if name == "natural_language_file_operation":
            command = arguments.get("command", "")
            parsed = file_manager.parse_natural_language(command)
            
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
                results = file_manager.search_files(criteria)
                return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
            
            elif intent == "unknown":
                return [TextContent(type="text", text=f"无法理解指令: {command}\n支持的操作: 搜索、移动、复制、删除、创建、压缩文件")]
            
            else:
                return [TextContent(type="text", text=f"解析结果: {json.dumps(parsed, indent=2, ensure_ascii=False)}")]
        
        elif name == "search_files":
            criteria = FileSearchCriteria(**arguments)
            results = file_manager.search_files(criteria)
            return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
        
        elif name == "move_files":
            results = file_manager.move_files(arguments["source_paths"], arguments["destination"])
            return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
        
        elif name == "copy_files":
            results = file_manager.copy_files(arguments["source_paths"], arguments["destination"])
            return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
        
        elif name == "delete_files":
            results = file_manager.delete_files(arguments["file_paths"])
            return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
        
        elif name == "compress_files":
            results = file_manager.compress_files(arguments["file_paths"], arguments["output_path"])
            return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-file-manager",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())