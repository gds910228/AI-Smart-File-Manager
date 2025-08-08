#!/usr/bin/env python3
"""
自然语言处理模块
提供更高级的自然语言理解和意图识别功能
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from config import Config
from utils import parse_time_expression, extract_keywords_from_text, parse_size_string

@dataclass
class Intent:
    """意图数据类"""
    name: str
    confidence: float
    entities: Dict[str, Any]
    original_text: str

class NLPProcessor:
    """自然语言处理器"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_extractors = self._load_entity_extractors()
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """加载意图识别模式"""
        return {
            "search": [
                r"(找|搜索|查找|寻找|locate|find|search)",
                r"(显示|列出|show|list|display)",
                r"(在哪|where)",
                r"(有没有|是否存在|exist)"
            ],
            "move": [
                r"(移动|剪切|move|cut)",
                r"(搬到|移到|move.*to)",
                r"(转移|transfer)"
            ],
            "copy": [
                r"(复制|拷贝|copy|duplicate)",
                r"(备份|backup)",
                r"(克隆|clone)"
            ],
            "delete": [
                r"(删除|移除|remove|delete|del)",
                r"(清理|清除|clean|clear)",
                r"(丢弃|discard)"
            ],
            "create": [
                r"(创建|新建|建立|create|make|new)",
                r"(生成|generate)",
                r"(添加|add)"
            ],
            "organize": [
                r"(整理|组织|organize|sort|arrange)",
                r"(分类|classify|categorize)",
                r"(归档|archive)"
            ],
            "compress": [
                r"(压缩|打包|zip|compress|pack)",
                r"(归档|archive.*zip)"
            ],
            "extract": [
                r"(解压|解压缩|unzip|extract|unpack)",
                r"(展开|expand)"
            ],
            "analyze": [
                r"(分析|analyze|analysis)",
                r"(统计|statistics|stats)",
                r"(报告|report)"
            ],
            "rename": [
                r"(重命名|改名|rename)",
                r"(更名|change.*name)"
            ]
        }
    
    def _load_entity_extractors(self) -> Dict[str, callable]:
        """加载实体提取器"""
        return {
            "file_type": self._extract_file_type,
            "time_range": self._extract_time_range,
            "size_constraint": self._extract_size_constraint,
            "path": self._extract_path,
            "keywords": self._extract_keywords,
            "number": self._extract_number,
            "operation_target": self._extract_operation_target,
            "organization_type": self._extract_organization_type
        }
    
    def process_natural_language(self, text: str) -> Intent:
        """处理自然语言输入"""
        text = text.strip()
        
        # 意图识别
        intent_name, confidence = self._identify_intent(text)
        
        # 实体提取
        entities = {}
        for entity_type, extractor in self.entity_extractors.items():
            try:
                entity_value = extractor(text)
                if entity_value is not None:
                    entities[entity_type] = entity_value
            except Exception as e:
                # 忽略单个实体提取错误
                continue
        
        return Intent(
            name=intent_name,
            confidence=confidence,
            entities=entities,
            original_text=text
        )
    
    def _identify_intent(self, text: str) -> Tuple[str, float]:
        """识别用户意图"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matches += 1
                    # 根据匹配的模式给分
                    score += 1.0 / len(patterns)
            
            if matches > 0:
                # 考虑匹配数量和模式质量
                intent_scores[intent] = score * (matches / len(patterns))
        
        if not intent_scores:
            return "unknown", 0.0
        
        # 返回得分最高的意图
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], min(best_intent[1], 1.0)
    
    def _extract_file_type(self, text: str) -> Optional[List[str]]:
        """提取文件类型"""
        text_lower = text.lower()
        
        for type_name, extensions in Config.FILE_TYPE_MAPPING.items():
            if type_name.lower() in text_lower:
                return extensions
        
        # 直接匹配扩展名
        ext_pattern = r'\.(jpg|jpeg|png|gif|pdf|doc|docx|txt|mp4|avi|mp3|wav|zip|rar)\b'
        matches = re.findall(ext_pattern, text_lower)
        if matches:
            return list(set(matches))
        
        return None
    
    def _extract_time_range(self, text: str) -> Optional[Dict[str, datetime]]:
        """提取时间范围"""
        time_range = {}
        
        # 使用utils中的时间解析函数
        parsed_time = parse_time_expression(text)
        if parsed_time:
            time_range["from"] = parsed_time
            
            # 尝试确定时间范围的结束时间
            if "今天" in text or "today" in text.lower():
                time_range["to"] = datetime.now()
            elif "昨天" in text or "yesterday" in text.lower():
                time_range["to"] = datetime.now() - timedelta(days=1)
            elif "上周" in text or "last week" in text.lower():
                time_range["to"] = datetime.now() - timedelta(days=7)
        
        # 提取具体的日期范围
        date_range_pattern = r'(\d{4}-\d{1,2}-\d{1,2})\s*到\s*(\d{4}-\d{1,2}-\d{1,2})'
        match = re.search(date_range_pattern, text)
        if match:
            try:
                from_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                to_date = datetime.strptime(match.group(2), "%Y-%m-%d")
                time_range["from"] = from_date
                time_range["to"] = to_date
            except ValueError:
                pass
        
        return time_range if time_range else None
    
    def _extract_size_constraint(self, text: str) -> Optional[Dict[str, int]]:
        """提取大小约束"""
        size_constraint = {}
        
        # 使用utils中的大小解析函数
        size_bytes = parse_size_string(text)
        if size_bytes:
            if any(word in text for word in ["大于", "超过", "大过", "more than", "larger than", ">"]):
                size_constraint["min"] = size_bytes
            elif any(word in text for word in ["小于", "少于", "小过", "less than", "smaller than", "<"]):
                size_constraint["max"] = size_bytes
            else:
                # 默认为精确匹配范围
                size_constraint["min"] = int(size_bytes * 0.9)
                size_constraint["max"] = int(size_bytes * 1.1)
        
        return size_constraint if size_constraint else None
    
    def _extract_path(self, text: str) -> Optional[str]:
        """提取路径信息"""
        # 中文路径映射
        path_mapping = {
            "桌面": Config.DEFAULT_SEARCH_PATHS.get("desktop"),
            "下载": Config.DEFAULT_SEARCH_PATHS.get("downloads"),
            "文档": Config.DEFAULT_SEARCH_PATHS.get("documents"),
            "图片": Config.DEFAULT_SEARCH_PATHS.get("pictures"),
            "视频": Config.DEFAULT_SEARCH_PATHS.get("videos"),
            "音乐": Config.DEFAULT_SEARCH_PATHS.get("music"),
            "desktop": Config.DEFAULT_SEARCH_PATHS.get("desktop"),
            "downloads": Config.DEFAULT_SEARCH_PATHS.get("downloads"),
            "documents": Config.DEFAULT_SEARCH_PATHS.get("documents"),
            "pictures": Config.DEFAULT_SEARCH_PATHS.get("pictures"),
            "videos": Config.DEFAULT_SEARCH_PATHS.get("videos"),
            "music": Config.DEFAULT_SEARCH_PATHS.get("music"),
        }
        
        text_lower = text.lower()
        for path_name, path_value in path_mapping.items():
            if path_name in text_lower:
                return path_value
        
        # 提取绝对路径
        path_patterns = [
            r'[a-zA-Z]:\\[^\\s]*',  # Windows路径
            r'/[^\\s]*'  # Unix路径
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _extract_keywords(self, text: str) -> Optional[List[str]]:
        """提取关键词"""
        keywords = extract_keywords_from_text(text)
        return keywords if keywords else None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """提取数字"""
        number_pattern = r'\b(\d+)\b'
        matches = re.findall(number_pattern, text)
        
        if matches:
            # 返回第一个找到的数字
            return int(matches[0])
        
        # 中文数字转换
        chinese_numbers = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
            "零": 0
        }
        
        for chinese, number in chinese_numbers.items():
            if chinese in text:
                return number
        
        return None
    
    def _extract_operation_target(self, text: str) -> Optional[str]:
        """提取操作目标"""
        # 提取引号中的内容
        quoted_pattern = r'["\']([^"\']+)["\']'
        match = re.search(quoted_pattern, text)
        if match:
            return match.group(1)
        
        # 提取"叫做"、"名为"等后面的内容
        name_patterns = [
            r'叫做\s*([^\s，。]+)',
            r'名为\s*([^\s，。]+)',
            r'called\s+([^\s，。]+)',
            r'named\s+([^\s，。]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_organization_type(self, text: str) -> Optional[str]:
        """提取整理类型"""
        text_lower = text.lower()
        
        type_patterns = {
            "type": ["类型", "种类", "type", "category"],
            "date": ["日期", "时间", "date", "time"],
            "size": ["大小", "尺寸", "size"],
            "extension": ["扩展名", "后缀", "extension", "suffix"],
            "name": ["名称", "文件名", "name", "filename"]
        }
        
        for org_type, patterns in type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return org_type
        
        return None
    
    def generate_command_suggestions(self, partial_text: str) -> List[str]:
        """生成命令建议"""
        suggestions = []
        text_lower = partial_text.lower()
        
        # 基于部分输入生成建议
        command_templates = {
            "搜索": [
                "搜索桌面上的图片文件",
                "搜索大于10MB的视频文件",
                "搜索上周修改的文档",
                "搜索包含'报告'的PDF文件"
            ],
            "整理": [
                "按类型整理当前目录",
                "按日期整理下载文件夹",
                "按大小整理图片文件",
                "整理桌面文件"
            ],
            "删除": [
                "删除空文件夹",
                "删除大于100MB的临时文件",
                "删除重复文件",
                "删除过期文件"
            ],
            "压缩": [
                "压缩选中的文件为backup.zip",
                "压缩图片文件夹",
                "压缩文档文件为archive.zip"
            ]
        }
        
        # 根据输入匹配建议
        for command, templates in command_templates.items():
            if command in text_lower or any(word in text_lower for word in command):
                suggestions.extend(templates)
        
        # 如果没有匹配，返回通用建议
        if not suggestions:
            suggestions = [
                "搜索文件：搜索桌面上的图片",
                "整理文件：按类型整理当前目录", 
                "删除文件：删除空文件夹",
                "压缩文件：压缩选中文件为backup.zip",
                "重命名：批量重命名文件为新格式"
            ]
        
        return suggestions[:5]  # 返回前5个建议
    
    def validate_command(self, text: str) -> Dict[str, Any]:
        """验证命令的有效性"""
        intent = self.process_natural_language(text)
        
        validation = {
            "valid": True,
            "confidence": intent.confidence,
            "warnings": [],
            "suggestions": []
        }
        
        # 检查意图置信度
        if intent.confidence < 0.3:
            validation["warnings"].append("命令意图不够明确")
            validation["suggestions"].extend(self.generate_command_suggestions(text))
        
        # 检查必要的实体
        required_entities = {
            "search": ["keywords", "file_type", "path"],
            "move": ["operation_target", "path"],
            "copy": ["operation_target", "path"],
            "delete": ["operation_target"],
            "organize": ["path", "organization_type"]
        }
        
        if intent.name in required_entities:
            missing_entities = []
            for entity in required_entities[intent.name]:
                if entity not in intent.entities:
                    missing_entities.append(entity)
            
            if missing_entities:
                validation["warnings"].append(f"缺少必要信息: {', '.join(missing_entities)}")
        
        # 安全性检查
        if intent.name == "delete" and not intent.entities.get("operation_target"):
            validation["warnings"].append("删除操作需要明确指定目标")
        
        return validation
    
    def extract_batch_operations(self, text: str) -> List[Intent]:
        """提取批量操作"""
        # 分割复合命令
        separators = ["然后", "接着", "再", "and then", "then", ";", "，"]
        
        parts = [text]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        # 处理每个部分
        intents = []
        for part in parts:
            part = part.strip()
            if part:
                intent = self.process_natural_language(part)
                if intent.confidence > 0.2:  # 只保留有一定置信度的意图
                    intents.append(intent)
        
        return intents
    
    def get_context_aware_suggestions(self, current_directory: str, recent_operations: List[str]) -> List[str]:
        """获取上下文感知的建议"""
        suggestions = []
        
        # 基于当前目录的建议
        if "Desktop" in current_directory or "桌面" in current_directory:
            suggestions.extend([
                "整理桌面文件按类型分类",
                "清理桌面上的临时文件",
                "搜索桌面上的重要文档"
            ])
        elif "Downloads" in current_directory or "下载" in current_directory:
            suggestions.extend([
                "整理下载文件夹",
                "删除下载的临时文件",
                "按日期归档下载文件"
            ])
        
        # 基于最近操作的建议
        if recent_operations:
            last_operation = recent_operations[-1]
            if "搜索" in last_operation or "search" in last_operation.lower():
                suggestions.append("对搜索结果进行批量操作")
            elif "整理" in last_operation or "organize" in last_operation.lower():
                suggestions.append("清理整理过程中产生的空文件夹")
        
        return suggestions[:3]  # 返回前3个建议
