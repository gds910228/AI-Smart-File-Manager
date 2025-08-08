#!/usr/bin/env python3
"""
AI智能文件管理器测试示例
"""

import asyncio
import json
from main import AIFileManager, FileSearchCriteria

async def test_natural_language_parsing():
    """测试自然语言解析功能"""
    file_manager = AIFileManager()
    
    test_commands = [
        "帮我找一下上周做的那个PPT",
        "把桌面上所有的图片都列出来",
        "查找大于10MB的视频文件",
        "删除下载文件夹里所有体积大于100MB的文件",
        "创建一个叫'财务报告'的文件夹",
        "把这些文件打包成backup.zip",
        "复制项目A文件夹到D盘",
        "find all PDF files from last month",
        "move all images to Pictures folder"
    ]
    
    print("=== 自然语言指令解析测试 ===\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"{i}. 指令: {command}")
        result = file_manager.parse_natural_language(command)
        print(f"   解析结果:")
        print(f"   - 意图: {result['intent']}")
        print(f"   - 实体: {json.dumps(result['entities'], indent=6, ensure_ascii=False)}")
        print()

async def test_file_search():
    """测试文件搜索功能"""
    file_manager = AIFileManager()
    
    print("=== 文件搜索功能测试 ===\n")
    
    # 测试搜索当前目录下的Python文件
    criteria = FileSearchCriteria(
        file_type=["py"],
        path="."
    )
    
    print("搜索当前目录下的Python文件:")
    results = file_manager.search_files(criteria)
    
    for result in results[:5]:  # 只显示前5个结果
        print(f"- {result['name']} ({result['size']} bytes)")
    
    if len(results) > 5:
        print(f"... 还有 {len(results) - 5} 个文件")
    
    print(f"\n总共找到 {len(results)} 个Python文件\n")

async def test_directory_operations():
    """测试目录操作"""
    file_manager = AIFileManager()
    
    print("=== 目录操作测试 ===\n")
    
    # 测试创建目录
    test_dir = "./test_directory"
    result = file_manager.create_directory(test_dir)
    print(f"创建目录 {test_dir}: {result}")
    
    # 清理测试目录
    import shutil
    import os
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"清理测试目录: {test_dir}")

def main():
    """主测试函数"""
    print("AI智能文件管理器 - 功能测试\n")
    print("=" * 50)
    
    # 运行异步测试
    asyncio.run(test_natural_language_parsing())
    asyncio.run(test_file_search())
    asyncio.run(test_directory_operations())
    
    print("=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()