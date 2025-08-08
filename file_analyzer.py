#!/usr/bin/env python3
"""
文件分析器 - 提供高级文件分析功能
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import mimetypes

from utils import format_file_size, get_file_type_category, get_directory_size

class FileAnalyzer:
    """文件分析器类"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """分析目录结构和统计信息"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {"error": "目录不存在或不是有效目录"}
        
        analysis = {
            "path": str(path),
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "file_types": defaultdict(int),
            "size_distribution": defaultdict(int),
            "largest_files": [],
            "newest_files": [],
            "oldest_files": [],
            "duplicate_files": [],
            "empty_files": [],
            "hidden_files": 0,
        }
        
        files_info = []
        
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        stat = item.stat()
                        file_info = {
                            "path": str(item),
                            "name": item.name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "created": datetime.fromtimestamp(stat.st_ctime),
                            "type": get_file_type_category(item),
                            "extension": item.suffix.lower(),
                            "is_hidden": item.name.startswith('.')
                        }
                        
                        files_info.append(file_info)
                        analysis["total_files"] += 1
                        analysis["total_size"] += stat.st_size
                        analysis["file_types"][file_info["type"]] += 1
                        
                        # 大小分布
                        if stat.st_size == 0:
                            analysis["empty_files"].append(str(item))
                            analysis["size_distribution"]["空文件"] += 1
                        elif stat.st_size < 1024:
                            analysis["size_distribution"]["< 1KB"] += 1
                        elif stat.st_size < 1024**2:
                            analysis["size_distribution"]["1KB - 1MB"] += 1
                        elif stat.st_size < 1024**3:
                            analysis["size_distribution"]["1MB - 1GB"] += 1
                        else:
                            analysis["size_distribution"]["> 1GB"] += 1
                        
                        # 隐藏文件计数
                        if file_info["is_hidden"]:
                            analysis["hidden_files"] += 1
                            
                    except (PermissionError, OSError) as e:
                        continue
                
                elif item.is_dir():
                    analysis["total_directories"] += 1
        
        except PermissionError:
            analysis["error"] = "权限不足，无法完全分析目录"
        
        # 排序和筛选
        files_info.sort(key=lambda x: x["size"], reverse=True)
        analysis["largest_files"] = [
            {"name": f["name"], "path": f["path"], "size": format_file_size(f["size"])}
            for f in files_info[:10]
        ]
        
        files_info.sort(key=lambda x: x["modified"], reverse=True)
        analysis["newest_files"] = [
            {"name": f["name"], "path": f["path"], "modified": f["modified"].isoformat()}
            for f in files_info[:10]
        ]
        
        files_info.sort(key=lambda x: x["modified"])
        analysis["oldest_files"] = [
            {"name": f["name"], "path": f["path"], "modified": f["modified"].isoformat()}
            for f in files_info[:10]
        ]
        
        # 查找重复文件
        analysis["duplicate_files"] = self.find_duplicate_files(files_info)
        
        # 转换为普通字典
        analysis["file_types"] = dict(analysis["file_types"])
        analysis["size_distribution"] = dict(analysis["size_distribution"])
        analysis["total_size_formatted"] = format_file_size(analysis["total_size"])
        
        return analysis
    
    def find_duplicate_files(self, files_info: List[Dict]) -> List[Dict[str, Any]]:
        """查找重复文件"""
        size_groups = defaultdict(list)
        
        # 按大小分组
        for file_info in files_info:
            if file_info["size"] > 0:  # 忽略空文件
                size_groups[file_info["size"]].append(file_info)
        
        duplicates = []
        
        # 对于相同大小的文件，计算哈希值
        for size, files in size_groups.items():
            if len(files) > 1:
                hash_groups = defaultdict(list)
                
                for file_info in files:
                    try:
                        file_hash = self.calculate_file_hash(file_info["path"])
                        hash_groups[file_hash].append(file_info)
                    except (PermissionError, OSError):
                        continue
                
                # 找到真正的重复文件
                for file_hash, duplicate_files in hash_groups.items():
                    if len(duplicate_files) > 1:
                        duplicates.append({
                            "hash": file_hash,
                            "size": format_file_size(size),
                            "count": len(duplicate_files),
                            "files": [
                                {"name": f["name"], "path": f["path"]}
                                for f in duplicate_files
                            ]
                        })
        
        return duplicates
    
    def calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """计算文件哈希值"""
        if file_path in self.analysis_cache:
            return self.analysis_cache[file_path]
        
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hash_md5.update(chunk)
            
            file_hash = hash_md5.hexdigest()
            self.analysis_cache[file_path] = file_hash
            return file_hash
            
        except (PermissionError, OSError):
            return ""
    
    def analyze_file_patterns(self, directory_path: str) -> Dict[str, Any]:
        """分析文件命名模式和组织结构"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {"error": "目录不存在或不是有效目录"}
        
        patterns = {
            "naming_patterns": defaultdict(int),
            "extension_patterns": defaultdict(int),
            "directory_depth": defaultdict(int),
            "file_age_distribution": defaultdict(int),
            "suggestions": []
        }
        
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    # 分析命名模式
                    name = item.stem.lower()
                    
                    # 检查常见模式
                    if any(char.isdigit() for char in name):
                        patterns["naming_patterns"]["包含数字"] += 1
                    if "_" in name:
                        patterns["naming_patterns"]["下划线分隔"] += 1
                    if "-" in name:
                        patterns["naming_patterns"]["连字符分隔"] += 1
                    if " " in name:
                        patterns["naming_patterns"]["空格分隔"] += 1
                    if name.isupper():
                        patterns["naming_patterns"]["全大写"] += 1
                    elif name.islower():
                        patterns["naming_patterns"]["全小写"] += 1
                    
                    # 扩展名统计
                    ext = item.suffix.lower()
                    if ext:
                        patterns["extension_patterns"][ext] += 1
                    
                    # 目录深度
                    depth = len(item.relative_to(path).parts) - 1
                    patterns["directory_depth"][f"深度{depth}"] += 1
                    
                    # 文件年龄分布
                    try:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        age_days = (datetime.now() - mtime).days
                        
                        if age_days < 7:
                            patterns["file_age_distribution"]["一周内"] += 1
                        elif age_days < 30:
                            patterns["file_age_distribution"]["一月内"] += 1
                        elif age_days < 365:
                            patterns["file_age_distribution"]["一年内"] += 1
                        else:
                            patterns["file_age_distribution"]["一年以上"] += 1
                    except OSError:
                        continue
        
        except PermissionError:
            patterns["error"] = "权限不足，无法完全分析目录"
        
        # 生成整理建议
        patterns["suggestions"] = self.generate_organization_suggestions(patterns)
        
        # 转换为普通字典
        for key in ["naming_patterns", "extension_patterns", "directory_depth", "file_age_distribution"]:
            patterns[key] = dict(patterns[key])
        
        return patterns
    
    def generate_organization_suggestions(self, patterns: Dict) -> List[str]:
        """生成文件整理建议"""
        suggestions = []
        
        # 基于扩展名的建议
        extensions = patterns.get("extension_patterns", {})
        if len(extensions) > 10:
            suggestions.append("建议按文件类型创建子目录进行分类")
        
        # 基于命名模式的建议
        naming = patterns.get("naming_patterns", {})
        if naming.get("空格分隔", 0) > naming.get("下划线分隔", 0):
            suggestions.append("建议将文件名中的空格替换为下划线，提高兼容性")
        
        # 基于目录深度的建议
        depth = patterns.get("directory_depth", {})
        deep_files = sum(count for key, count in depth.items() if "深度" in key and int(key.replace("深度", "")) > 3)
        if deep_files > 50:
            suggestions.append("目录层级过深，建议重新组织文件结构")
        
        # 基于文件年龄的建议
        age = patterns.get("file_age_distribution", {})
        old_files = age.get("一年以上", 0)
        if old_files > 100:
            suggestions.append("存在大量旧文件，建议创建归档目录")
        
        return suggestions
    
    def get_storage_recommendations(self, directory_path: str) -> Dict[str, Any]:
        """获取存储优化建议"""
        analysis = self.analyze_directory(directory_path)
        
        recommendations = {
            "cleanup_opportunities": [],
            "compression_candidates": [],
            "archive_candidates": [],
            "potential_savings": 0
        }
        
        # 清理机会
        if analysis.get("empty_files"):
            empty_count = len(analysis["empty_files"])
            recommendations["cleanup_opportunities"].append(
                f"发现 {empty_count} 个空文件，可以安全删除"
            )
        
        if analysis.get("duplicate_files"):
            duplicate_size = sum(
                len(dup["files"]) - 1 for dup in analysis["duplicate_files"]
            )
            recommendations["cleanup_opportunities"].append(
                f"发现重复文件，删除副本可节省空间"
            )
            recommendations["potential_savings"] += duplicate_size
        
        # 压缩候选
        large_files = [f for f in analysis.get("largest_files", []) if "MB" in f["size"] or "GB" in f["size"]]
        if large_files:
            recommendations["compression_candidates"] = large_files[:5]
        
        # 归档候选
        old_files = analysis.get("oldest_files", [])[:10]
        if old_files:
            recommendations["archive_candidates"] = old_files
        
        return recommendations