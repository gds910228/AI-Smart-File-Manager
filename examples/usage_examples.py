#!/usr/bin/env python3
"""
AI智能文件管理器使用示例
展示各种实际使用场景
"""

import asyncio
import json
from pathlib import Path
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import AIFileManager, FileSearchCriteria
from advanced_operations import AdvancedFileOperations
from file_analyzer import FileAnalyzer
from nlp_processor import NLPProcessor

class UsageExamples:
    """使用示例类"""
    
    def __init__(self):
        self.file_manager = AIFileManager()
        self.advanced_ops = AdvancedFileOperations()
        self.analyzer = FileAnalyzer()
        self.nlp = NLPProcessor()
    
    def example_1_basic_search(self):
        """示例1: 基础文件搜索"""
        print("=== 示例1: 基础文件搜索 ===")
        
        # 自然语言搜索
        command = "搜索桌面上的图片文件"
        parsed = self.file_manager.parse_natural_language(command)
        print(f"用户指令: {command}")
        print(f"解析结果: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
        
        # 执行搜索
        entities = parsed["entities"]
        criteria = FileSearchCriteria(
            path=entities.get("path", str(Path.home() / "Desktop")),
            file_type=entities.get("file_type", ["jpg", "jpeg", "png", "gif"])
        )
        
        results = self.file_manager.search_files(criteria)
        print(f"搜索结果: 找到 {len(results)} 个图片文件")
        
        for result in results[:3]:  # 显示前3个结果
            print(f"  - {result['name']} ({result['size']} bytes)")
        print()
    
    def example_2_smart_organization(self):
        """示例2: 智能文件整理"""
        print("=== 示例2: 智能文件整理 ===")
        
        # 自然语言整理指令
        command = "按类型整理下载文件夹"
        parsed = self.file_manager.parse_natural_language(command)
        print(f"用户指令: {command}")
        
        # 执行整理
        downloads_path = str(Path.home() / "Downloads")
        result = self.advanced_ops.smart_organize_directory(downloads_path, "type")
        
        print(f"整理结果:")
        print(f"  - 整理文件数: {result.get('organized_files', 0)}")
        print(f"  - 创建目录: {result.get('created_directories', [])}")
        if result.get('errors'):
            print(f"  - 错误: {result['errors']}")
        print()
    
    def example_3_file_analysis(self):
        """示例3: 文件分析和优化建议"""
        print("=== 示例3: 文件分析和优化建议 ===")
        
        # 分析当前目录
        current_dir = "."
        analysis = self.analyzer.analyze_directory(current_dir)
        
        print(f"目录分析结果 ({current_dir}):")
        print(f"  - 总文件数: {analysis.get('total_files', 0)}")
        print(f"  - 总大小: {analysis.get('total_size_formatted', '0 B')}")
        print(f"  - 文件类型分布: {json.dumps(analysis.get('file_types', {}), ensure_ascii=False)}")
        
        # 获取优化建议
        recommendations = self.analyzer.get_storage_recommendations(current_dir)
        print(f"优化建议:")
        for opportunity in recommendations.get('cleanup_opportunities', []):
            print(f"  - {opportunity}")
        print()
    
    def example_4_batch_operations(self):
        """示例4: 批量操作"""
        print("=== 示例4: 批量操作 ===")
        
        # 批量重命名预览
        command = "将文件重命名为 file_{index:03d}_{name}{ext} 格式"
        print(f"用户指令: {command}")
        
        # 解析重命名模式
        pattern = "file_{index:03d}_{name}{ext}"
        current_dir = "."
        
        result = self.advanced_ops.batch_rename_files(current_dir, pattern, preview=True)
        
        print(f"批量重命名预览:")
        for item in result.get('renamed_files', [])[:5]:  # 显示前5个
            print(f"  {item['original']} -> {item['new']}")
        print()
    
    def example_5_natural_language_queries(self):
        """示例5: 复杂自然语言查询"""
        print("=== 示例5: 复杂自然语言查询 ===")
        
        complex_queries = [
            "找到上周修改的大于10MB的视频文件",
            "搜索包含'报告'关键词的PDF文档",
            "列出桌面上所有空文件",
            "查找重复的图片文件"
        ]
        
        for query in complex_queries:
            print(f"查询: {query}")
            
            # 使用NLP处理器分析
            intent = self.nlp.process_natural_language(query)
            print(f"  意图: {intent.name} (置信度: {intent.confidence:.2f})")
            print(f"  实体: {json.dumps(intent.entities, ensure_ascii=False)}")
            
            # 验证查询
            validation = self.nlp.validate_command(query)
            if validation["warnings"]:
                print(f"  警告: {validation['warnings']}")
            print()
    
    def example_6_file_compression(self):
        """示例6: 文件压缩和归档"""
        print("=== 示例6: 文件压缩和归档 ===")
        
        # 压缩Python文件
        python_files = [str(p) for p in Path(".").glob("*.py")][:3]  # 取前3个Python文件
        
        if python_files:
            result = self.file_manager.compress_files(python_files, "python_files_backup.zip")
            print(f"压缩Python文件:")
            print(f"  - 源文件: {len(python_files)} 个")
            print(f"  - 输出文件: python_files_backup.zip")
            print(f"  - 结果: {'成功' if result.get('success') else '失败'}")
            
            if not result.get('success'):
                print(f"  - 错误: {result.get('error')}")
        else:
            print("未找到Python文件进行压缩测试")
        print()
    
    def example_7_command_suggestions(self):
        """示例7: 智能命令建议"""
        print("=== 示例7: 智能命令建议 ===")
        
        partial_inputs = [
            "搜索",
            "整理文件",
            "删除大文件",
            "压缩"
        ]
        
        for partial in partial_inputs:
            suggestions = self.nlp.generate_command_suggestions(partial)
            print(f"输入: '{partial}'")
            print(f"建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
            print()
    
    def example_8_error_handling(self):
        """示例8: 错误处理和恢复"""
        print("=== 示例8: 错误处理和恢复 ===")
        
        # 测试无效路径
        invalid_path = "/nonexistent/directory"
        result = self.advanced_ops.smart_organize_directory(invalid_path, "type")
        print(f"无效路径操作:")
        print(f"  - 路径: {invalid_path}")
        print(f"  - 结果: {result.get('error', '未知错误')}")
        
        # 测试模糊指令
        ambiguous_command = "做一些文件操作"
        parsed = self.file_manager.parse_natural_language(ambiguous_command)
        print(f"\n模糊指令处理:")
        print(f"  - 指令: {ambiguous_command}")
        print(f"  - 识别意图: {parsed['intent']}")
        
        validation = self.nlp.validate_command(ambiguous_command)
        if validation["warnings"]:
            print(f"  - 警告: {validation['warnings']}")
        if validation["suggestions"]:
            print(f"  - 建议: {validation['suggestions'][:2]}")  # 显示前2个建议
        print()
    
    def run_all_examples(self):
        """运行所有示例"""
        print("AI智能文件管理器 - 使用示例演示")
        print("=" * 60)
        
        examples = [
            self.example_1_basic_search,
            self.example_2_smart_organization,
            self.example_3_file_analysis,
            self.example_4_batch_operations,
            self.example_5_natural_language_queries,
            self.example_6_file_compression,
            self.example_7_command_suggestions,
            self.example_8_error_handling
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                example()
            except Exception as e:
                print(f"示例 {i} 执行出错: {str(e)}")
                print()
        
        print("=" * 60)
        print("所有示例演示完成！")

def main():
    """主函数"""
    examples = UsageExamples()
    examples.run_all_examples()

if __name__ == "__main__":
    main()