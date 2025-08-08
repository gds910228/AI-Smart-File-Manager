#!/usr/bin/env python3
"""
高级文件操作模块
提供智能文件整理、批量重命名等高级功能
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from config import Config
from utils import (
    format_file_size, get_file_type_category, clean_filename,
    group_files_by_type, is_safe_path, create_backup_name
)

class AdvancedFileOperations:
    """高级文件操作类"""
    
    def __init__(self):
        self.operation_history = []
    
    def smart_organize_directory(self, directory_path: str, organization_type: str = "type") -> Dict[str, Any]:
        """智能整理目录"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {"success": False, "error": "目录不存在或不是有效目录"}
        
        if not is_safe_path(str(path)):
            return {"success": False, "error": "不安全的路径"}
        
        results = {
            "success": True,
            "organized_files": 0,
            "created_directories": [],
            "errors": [],
            "organization_type": organization_type
        }
        
        try:
            files = [f for f in path.iterdir() if f.is_file()]
            
            if organization_type == "type":
                results.update(self._organize_by_type(files, path))
            elif organization_type == "date":
                results.update(self._organize_by_date(files, path))
            elif organization_type == "size":
                results.update(self._organize_by_size(files, path))
            elif organization_type == "extension":
                results.update(self._organize_by_extension(files, path))
            else:
                return {"success": False, "error": f"不支持的整理类型: {organization_type}"}
        
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        # 记录操作历史
        self.operation_history.append({
            "operation": "smart_organize",
            "path": str(path),
            "type": organization_type,
            "timestamp": datetime.now().isoformat(),
            "result": results
        })
        
        return results
    
    def _organize_by_type(self, files: List[Path], base_path: Path) -> Dict[str, Any]:
        """按文件类型整理"""
        results = {"organized_files": 0, "created_directories": [], "errors": []}
        
        # 按类型分组文件
        type_groups = defaultdict(list)
        for file_path in files:
            file_type = get_file_type_category(file_path)
            type_groups[file_type].append(file_path)
        
        # 为每种类型创建目录并移动文件
        for file_type, file_list in type_groups.items():
            if file_type == "其他":
                continue  # 跳过未分类文件
            
            type_dir = base_path / file_type
            
            try:
                type_dir.mkdir(exist_ok=True)
                if str(type_dir) not in results["created_directories"]:
                    results["created_directories"].append(str(type_dir))
                
                for file_path in file_list:
                    dest_path = type_dir / file_path.name
                    
                    # 处理重名文件
                    counter = 1
                    original_dest = dest_path
                    while dest_path.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        dest_path = type_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(dest_path))
                    results["organized_files"] += 1
            
            except Exception as e:
                results["errors"].append(f"整理 {file_type} 类型文件时出错: {str(e)}")
        
        return results
    
    def _organize_by_date(self, files: List[Path], base_path: Path) -> Dict[str, Any]:
        """按修改日期整理"""
        results = {"organized_files": 0, "created_directories": [], "errors": []}
        
        # 按年月分组
        date_groups = defaultdict(list)
        for file_path in files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                date_key = mtime.strftime("%Y年%m月")
                date_groups[date_key].append(file_path)
            except OSError as e:
                results["errors"].append(f"获取文件 {file_path.name} 的修改时间失败: {str(e)}")
        
        # 创建日期目录并移动文件
        for date_key, file_list in date_groups.items():
            date_dir = base_path / date_key
            
            try:
                date_dir.mkdir(exist_ok=True)
                results["created_directories"].append(str(date_dir))
                
                for file_path in file_list:
                    dest_path = date_dir / file_path.name
                    
                    # 处理重名文件
                    counter = 1
                    original_dest = dest_path
                    while dest_path.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        dest_path = date_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(dest_path))
                    results["organized_files"] += 1
            
            except Exception as e:
                results["errors"].append(f"整理日期 {date_key} 的文件时出错: {str(e)}")
        
        return results
    
    def _organize_by_size(self, files: List[Path], base_path: Path) -> Dict[str, Any]:
        """按文件大小整理"""
        results = {"organized_files": 0, "created_directories": [], "errors": []}
        
        # 定义大小分类
        size_categories = [
            ("小文件_小于1MB", 0, 1024**2),
            ("中等文件_1MB到100MB", 1024**2, 100 * 1024**2),
            ("大文件_大于100MB", 100 * 1024**2, float('inf'))
        ]
        
        # 按大小分组
        size_groups = defaultdict(list)
        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                
                for category, min_size, max_size in size_categories:
                    if min_size <= file_size < max_size:
                        size_groups[category].append(file_path)
                        break
            
            except OSError as e:
                results["errors"].append(f"获取文件 {file_path.name} 的大小失败: {str(e)}")
        
        # 创建大小目录并移动文件
        for category, file_list in size_groups.items():
            size_dir = base_path / category
            
            try:
                size_dir.mkdir(exist_ok=True)
                results["created_directories"].append(str(size_dir))
                
                for file_path in file_list:
                    dest_path = size_dir / file_path.name
                    
                    # 处理重名文件
                    counter = 1
                    original_dest = dest_path
                    while dest_path.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        dest_path = size_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(dest_path))
                    results["organized_files"] += 1
            
            except Exception as e:
                results["errors"].append(f"整理大小分类 {category} 的文件时出错: {str(e)}")
        
        return results
    
    def _organize_by_extension(self, files: List[Path], base_path: Path) -> Dict[str, Any]:
        """按文件扩展名整理"""
        results = {"organized_files": 0, "created_directories": [], "errors": []}
        
        # 按扩展名分组
        ext_groups = defaultdict(list)
        for file_path in files:
            ext = file_path.suffix.lower() or "无扩展名"
            ext_groups[ext].append(file_path)
        
        # 创建扩展名目录并移动文件
        for ext, file_list in ext_groups.items():
            # 清理扩展名作为目录名
            dir_name = clean_filename(ext.replace(".", "").upper() + "文件")
            ext_dir = base_path / dir_name
            
            try:
                ext_dir.mkdir(exist_ok=True)
                results["created_directories"].append(str(ext_dir))
                
                for file_path in file_list:
                    dest_path = ext_dir / file_path.name
                    
                    # 处理重名文件
                    counter = 1
                    original_dest = dest_path
                    while dest_path.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        dest_path = ext_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(file_path), str(dest_path))
                    results["organized_files"] += 1
            
            except Exception as e:
                results["errors"].append(f"整理扩展名 {ext} 的文件时出错: {str(e)}")
        
        return results
    
    def batch_rename_files(self, directory_path: str, rename_pattern: str, preview: bool = True) -> Dict[str, Any]:
        """批量重命名文件"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {"success": False, "error": "目录不存在或不是有效目录"}
        
        if not is_safe_path(str(path)):
            return {"success": False, "error": "不安全的路径"}
        
        results = {
            "success": True,
            "preview": preview,
            "renamed_files": [],
            "errors": [],
            "pattern": rename_pattern
        }
        
        try:
            files = [f for f in path.iterdir() if f.is_file()]
            
            for i, file_path in enumerate(files, 1):
                try:
                    # 解析重命名模式
                    new_name = self._apply_rename_pattern(file_path, rename_pattern, i)
                    new_path = file_path.parent / new_name
                    
                    # 避免重名
                    counter = 1
                    original_new_path = new_path
                    while new_path.exists() and new_path != file_path:
                        stem = original_new_path.stem
                        suffix = original_new_path.suffix
                        new_path = file_path.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    rename_info = {
                        "original": file_path.name,
                        "new": new_path.name,
                        "path": str(file_path)
                    }
                    
                    if not preview and new_path != file_path:
                        file_path.rename(new_path)
                        rename_info["status"] = "renamed"
                    else:
                        rename_info["status"] = "preview" if preview else "unchanged"
                    
                    results["renamed_files"].append(rename_info)
                
                except Exception as e:
                    results["errors"].append(f"重命名文件 {file_path.name} 时出错: {str(e)}")
        
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        # 记录操作历史
        if not preview:
            self.operation_history.append({
                "operation": "batch_rename",
                "path": str(path),
                "pattern": rename_pattern,
                "timestamp": datetime.now().isoformat(),
                "result": results
            })
        
        return results
    
    def _apply_rename_pattern(self, file_path: Path, pattern: str, index: int) -> str:
        """应用重命名模式"""
        # 获取文件信息
        stat = file_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        
        # 替换模式变量
        replacements = {
            "{name}": file_path.stem,
            "{ext}": file_path.suffix,
            "{index}": str(index),
            "{index:02d}": f"{index:02d}",
            "{index:03d}": f"{index:03d}",
            "{date}": mtime.strftime("%Y%m%d"),
            "{time}": mtime.strftime("%H%M%S"),
            "{year}": mtime.strftime("%Y"),
            "{month}": mtime.strftime("%m"),
            "{day}": mtime.strftime("%d"),
            "{size}": str(stat.st_size),
        }
        
        new_name = pattern
        for placeholder, value in replacements.items():
            new_name = new_name.replace(placeholder, value)
        
        # 清理文件名
        new_name = clean_filename(new_name)
        
        # 确保有扩展名
        if not Path(new_name).suffix and file_path.suffix:
            new_name += file_path.suffix
        
        return new_name
    
    def cleanup_empty_directories(self, directory_path: str) -> Dict[str, Any]:
        """清理空目录"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return {"success": False, "error": "目录不存在或不是有效目录"}
        
        if not is_safe_path(str(path)):
            return {"success": False, "error": "不安全的路径"}
        
        results = {
            "success": True,
            "removed_directories": [],
            "errors": []
        }
        
        try:
            # 从最深层开始检查
            for dir_path in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if dir_path.is_dir() and dir_path != path:
                    try:
                        # 检查目录是否为空
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            results["removed_directories"].append(str(dir_path))
                    except OSError as e:
                        results["errors"].append(f"删除空目录 {dir_path} 时出错: {str(e)}")
        
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        # 记录操作历史
        self.operation_history.append({
            "operation": "cleanup_empty_directories",
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
            "result": results
        })
        
        return results
    
    def create_file_shortcuts(self, source_files: List[str], shortcut_directory: str) -> Dict[str, Any]:
        """创建文件快捷方式"""
        shortcut_dir = Path(shortcut_directory)
        
        if not shortcut_dir.exists():
            shortcut_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "success": True,
            "created_shortcuts": [],
            "errors": []
        }
        
        try:
            for source_file in source_files:
                source_path = Path(source_file)
                
                if not source_path.exists():
                    results["errors"].append(f"源文件不存在: {source_file}")
                    continue
                
                if not is_safe_path(source_file):
                    results["errors"].append(f"不安全的路径: {source_file}")
                    continue
                
                # 创建符号链接（在支持的系统上）
                shortcut_path = shortcut_dir / source_path.name
                
                try:
                    # 处理重名
                    counter = 1
                    original_shortcut = shortcut_path
                    while shortcut_path.exists():
                        stem = original_shortcut.stem
                        suffix = original_shortcut.suffix
                        shortcut_path = shortcut_dir / f"{stem}_shortcut_{counter}{suffix}"
                        counter += 1
                    
                    # 在Windows上创建快捷方式，在Unix系统上创建符号链接
                    if os.name == 'nt':
                        # Windows快捷方式需要额外的库，这里创建硬链接作为替代
                        if source_path.is_file():
                            shortcut_path.hardlink_to(source_path)
                        else:
                            # 对于目录，创建一个文本文件记录路径
                            shortcut_path = shortcut_dir / f"{source_path.name}_路径.txt"
                            shortcut_path.write_text(str(source_path), encoding='utf-8')
                    else:
                        # Unix系统使用符号链接
                        shortcut_path.symlink_to(source_path)
                    
                    results["created_shortcuts"].append({
                        "source": str(source_path),
                        "shortcut": str(shortcut_path)
                    })
                
                except Exception as e:
                    results["errors"].append(f"创建快捷方式失败 {source_file}: {str(e)}")
        
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.operation_history[-limit:] if limit > 0 else self.operation_history
    
    def undo_last_operation(self) -> Dict[str, Any]:
        """撤销最后一次操作（有限支持）"""
        if not self.operation_history:
            return {"success": False, "error": "没有可撤销的操作"}
        
        last_operation = self.operation_history[-1]
        operation_type = last_operation["operation"]
        
        # 目前只支持撤销某些操作
        if operation_type == "cleanup_empty_directories":
            return {"success": False, "error": "无法撤销删除空目录操作"}
        elif operation_type == "batch_rename":
            return self._undo_batch_rename(last_operation)
        elif operation_type == "smart_organize":
            return self._undo_smart_organize(last_operation)
        else:
            return {"success": False, "error": f"不支持撤销操作类型: {operation_type}"}
    
    def _undo_batch_rename(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """撤销批量重命名"""
        results = {"success": True, "undone_files": [], "errors": []}
        
        try:
            renamed_files = operation["result"]["renamed_files"]
            
            for file_info in renamed_files:
                if file_info["status"] == "renamed":
                    try:
                        current_path = Path(file_info["path"]).parent / file_info["new"]
                        original_path = Path(file_info["path"])
                        
                        if current_path.exists():
                            current_path.rename(original_path)
                            results["undone_files"].append(file_info["original"])
                    
                    except Exception as e:
                        results["errors"].append(f"撤销重命名 {file_info['new']} 时出错: {str(e)}")
            
            # 从历史中移除已撤销的操作
            if results["success"] and not results["errors"]:
                self.operation_history.pop()
        
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def _undo_smart_organize(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """撤销智能整理（简化版本）"""
        return {"success": False, "error": "智能整理操作的撤销功能尚未实现，建议手动恢复"}