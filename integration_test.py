#!/usr/bin/env python3
"""
AI智能文件管理器集成测试
测试所有模块的协同工作
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from main import AIFileManager, FileSearchCriteria
from advanced_operations import AdvancedFileOperations
from file_analyzer import FileAnalyzer
from nlp_processor import NLPProcessor

class IntegrationTester:
    """集成测试类"""
    
    def __init__(self):
        self.file_manager = AIFileManager()
        self.advanced_ops = AdvancedFileOperations()
        self.analyzer = FileAnalyzer()
        self.nlp = NLPProcessor()
        self.test_dir = None
    
    def setup_test_environment(self):
        """设置测试环境"""
        # 创建临时测试目录
        self.test_dir = Path(tempfile.mkdtemp(prefix="ai_file_manager_test_"))
        print(f"创建测试目录: {self.test_dir}")
        
        # 创建测试文件
        test_files = [
            ("document1.pdf", "这是一个PDF文档"),
            ("image1.jpg", "fake image data"),
            ("video1.mp4", "fake video data"),
            ("report_2024.docx", "年度报告内容"),
            ("data.csv", "姓名,年龄\n张三,25\n李四,30"),
            ("script.py", "print('Hello World')"),
            ("large_file.txt", "x" * 1024 * 1024),  # 1MB文件
            ("empty_file.txt", ""),
        ]
        
        for filename, content in test_files:
            file_path = self.test_dir / filename
            file_path.write_text(content, encoding='utf-8')
        
        # 创建子目录
        sub_dirs = ["images", "documents", "videos"]
        for dir_name in sub_dirs:
            (self.test_dir / dir_name).mkdir()
        
        print(f"创建了 {len(test_files)} 个测试文件和 {len(sub_dirs)} 个子目录")
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"清理测试目录: {self.test_dir}")
    
    async def test_nlp_processing(self):
        """测试自然语言处理"""
        print("\n=== 测试自然语言处理 ===")
        
        test_commands = [
            "搜索桌面上的图片文件",
            "删除大于1MB的文件",
            "按类型整理当前目录",
            "压缩所有PDF文件",
            "重命名文件为新格式",
            "find all video files from last week",
            "organize files by date in downloads folder"
        ]
        
        for command in test_commands:
            intent = self.nlp.process_natural_language(command)
            print(f"命令: {command}")
            print(f"  意图: {intent.name} (置信度: {intent.confidence:.2f})")
            print(f"  实体: {json.dumps(intent.entities, ensure_ascii=False, indent=4)}")
            
            # 验证命令
            validation = self.nlp.validate_command(command)
            if validation["warnings"]:
                print(f"  警告: {validation['warnings']}")
            print()
    
    async def test_file_search(self):
        """测试文件搜索功能"""
        print("\n=== 测试文件搜索功能 ===")
        
        # 测试基本搜索
        criteria = FileSearchCriteria(
            path=str(self.test_dir),
            file_type=["pdf", "docx"]
        )
        
        results = self.file_manager.search_files(criteria)
        print(f"搜索PDF和DOCX文件: 找到 {len(results)} 个文件")
        for result in results:
            print(f"  - {result['name']} ({result['size']} bytes)")
        
        # 测试大小过滤
        criteria = FileSearchCriteria(
            path=str(self.test_dir),
            size_min=1024 * 500  # 大于500KB
        )
        
        results = self.file_manager.search_files(criteria)
        print(f"\n搜索大于500KB的文件: 找到 {len(results)} 个文件")
        for result in results:
            print(f"  - {result['name']} ({result['size']} bytes)")
    
    async def test_advanced_operations(self):
        """测试高级操作"""
        print("\n=== 测试高级操作 ===")
        
        # 测试智能整理
        result = self.advanced_ops.smart_organize_directory(str(self.test_dir), "type")
        print(f"按类型整理目录:")
        print(f"  整理文件数: {result['organized_files']}")
        print(f"  创建目录: {result['created_directories']}")
        if result['errors']:
            print(f"  错误: {result['errors']}")
        
        # 测试批量重命名（预览模式）
        result = self.advanced_ops.batch_rename_files(
            str(self.test_dir), 
            "file_{index:02d}_{name}{ext}", 
            preview=True
        )
        print(f"\n批量重命名预览:")
        for item in result['renamed_files'][:3]:  # 只显示前3个
            print(f"  {item['original']} -> {item['new']}")
        
        # 测试清理空目录
        result = self.advanced_ops.cleanup_empty_directories(str(self.test_dir))
        print(f"\n清理空目录: 删除了 {len(result['removed_directories'])} 个空目录")
    
    async def test_file_analysis(self):
        """测试文件分析"""
        print("\n=== 测试文件分析 ===")
        
        # 分析目录
        analysis = self.analyzer.analyze_directory(str(self.test_dir))
        print(f"目录分析结果:")
        print(f"  总文件数: {analysis['total_files']}")
        print(f"  总目录数: {analysis['total_directories']}")
        print(f"  总大小: {analysis['total_size_formatted']}")
        print(f"  文件类型分布: {json.dumps(analysis['file_types'], ensure_ascii=False)}")
        print(f"  大小分布: {json.dumps(analysis['size_distribution'], ensure_ascii=False)}")
        
        if analysis['empty_files']:
            print(f"  空文件: {len(analysis['empty_files'])} 个")
        
        if analysis['duplicate_files']:
            print(f"  重复文件组: {len(analysis['duplicate_files'])} 组")
        
        # 分析文件模式
        patterns = self.analyzer.analyze_file_patterns(str(self.test_dir))
        print(f"\n文件模式分析:")
        print(f"  命名模式: {json.dumps(patterns['naming_patterns'], ensure_ascii=False)}")
        print(f"  扩展名分布: {json.dumps(patterns['extension_patterns'], ensure_ascii=False)}")
        
        if patterns['suggestions']:
            print(f"  整理建议:")
            for suggestion in patterns['suggestions']:
                print(f"    - {suggestion}")
    
    async def test_natural_language_integration(self):
        """测试自然语言集成"""
        print("\n=== 测试自然语言集成 ===")
        
        # 测试复杂的自然语言命令
        complex_commands = [
            f"搜索 {self.test_dir} 目录下大于500KB的文档文件",
            f"按类型整理 {self.test_dir} 目录",
            f"分析 {self.test_dir} 目录的文件分布情况"
        ]
        
        for command in complex_commands:
            print(f"\n处理命令: {command}")
            
            # 解析自然语言
            parsed = self.file_manager.parse_natural_language(command)
            print(f"解析结果: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
            
            # 根据意图执行相应操作
            intent = parsed["intent"]
            entities = parsed["entities"]
            
            if intent == "search":
                criteria = FileSearchCriteria(
                    path=entities.get("path", str(self.test_dir)),
                    file_type=entities.get("file_type"),
                    size_min=entities.get("size_min"),
                    keywords=entities.get("keywords")
                )
                results = self.file_manager.search_files(criteria)
                print(f"搜索结果: 找到 {len(results)} 个文件")
            
            elif intent == "organize":
                org_type = entities.get("organization_type", "type")
                result = self.advanced_ops.smart_organize_directory(
                    entities.get("path", str(self.test_dir)), 
                    org_type
                )
                print(f"整理结果: 整理了 {result['organized_files']} 个文件")
            
            elif intent == "analyze":
                analysis = self.analyzer.analyze_directory(
                    entities.get("path", str(self.test_dir))
                )
                print(f"分析结果: {analysis['total_files']} 个文件, {analysis['total_size_formatted']}")
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试不存在的路径
        result = self.file_manager.search_files(
            FileSearchCriteria(path="/nonexistent/path")
        )
        print(f"搜索不存在路径: 返回 {len(result)} 个结果")
        
        # 测试无效的自然语言命令
        parsed = self.file_manager.parse_natural_language("这是一个无意义的命令")
        print(f"无效命令解析: 意图={parsed['intent']}")
        
        # 测试权限受限的操作
        try:
            result = self.advanced_ops.smart_organize_directory("/root", "type")
            print(f"受限路径操作: {result.get('error', '成功')}")
        except Exception as e:
            print(f"受限路径操作异常: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始AI智能文件管理器集成测试")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            
            await self.test_nlp_processing()
            await self.test_file_search()
            await self.test_advanced_operations()
            await self.test_file_analysis()
            await self.test_natural_language_integration()
            await self.test_error_handling()
            
            print("\n" + "=" * 50)
            print("所有测试完成！")
            
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup_test_environment()

async def main():
    """主函数"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())