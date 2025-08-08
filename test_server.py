#!/usr/bin/env python3
"""
测试MCP服务器启动
"""

import asyncio
import sys
from main import main

async def test_server_startup():
    """测试服务器启动"""
    try:
        print("正在测试MCP服务器启动...")
        # 由于stdio_server需要实际的stdin/stdout，我们只测试导入和基本功能
        from main import server, nlp_processor, search_files, FileSearchCriteria
        
        print("✅ 服务器模块导入成功")
        
        # 测试NLP处理器
        test_command = "搜索所有图片文件"
        parsed = nlp_processor.parse_natural_language(test_command)
        print(f"✅ NLP处理器工作正常: {parsed['intent']}")
        
        # 测试文件搜索功能
        criteria = FileSearchCriteria(path=".")
        results = search_files(criteria)
        print(f"✅ 文件搜索功能正常: 找到 {len(results)} 个文件")
        
        # 测试工具列表
        from main import handle_list_tools
        tools = await handle_list_tools()
        print(f"✅ 工具注册成功: {len(tools)} 个工具可用")
        
        print("\n🎉 MCP服务器测试通过！所有核心功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 服务器测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server_startup())
    sys.exit(0 if success else 1)