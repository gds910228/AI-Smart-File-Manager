# 股票代码提取器使用说明

## 功能概述

股票代码提取器是AI智能文件管理器MCP服务器的一个功能模块，用于从指定目录中的文件名提取股票代码。

## 主要特性

- 🔍 **智能识别**: 从文件名中精确提取6位股票代码
- 📁 **批量处理**: 递归扫描目录及子目录中的所有文件
- 🎯 **精确匹配**: 支持精确模式和通用模式两种匹配方式
- 📄 **结果导出**: 自动去重并按数字顺序排序，保存到文本文件
- 🛡️ **错误处理**: 完善的异常处理和错误提示

## 使用方法

### 1. 通过MCP工具调用

```json
{
  "tool": "extract_stock_codes",
  "arguments": {
    "directory_path": "F:\\doc\\mine\\理财相关\\量化分析",
    "output_file": "extracted_codes.txt",
    "use_precise_pattern": true
  }
}
```

### 2. 直接使用Python模块

```python
from stock_code_extractor import extract_stock_codes_from_path

# 提取股票代码
result = extract_stock_codes_from_path(
    directory_path="F:\\doc\\mine\\理财相关\\量化分析",
    output_file="stock_codes.txt"
)

if result["success"]:
    print(f"成功提取 {result['total_codes']} 个股票代码")
    print(f"代码列表: {result['codes']}")
else:
    print(f"提取失败: {result['error']}")
```

## 参数说明

### extract_stock_codes 工具参数

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| directory_path | string | 是 | - | 要扫描的目录路径 |
| output_file | string | 否 | "stock_codes.txt" | 输出文件路径 |
| use_precise_pattern | boolean | 否 | true | 是否使用精确模式匹配 |

### 匹配模式说明

#### 精确模式 (use_precise_pattern=true)
- 匹配格式: `stock_analysis_sse_XXXXXX` 或 `stock_analysis_szse_XXXXXX`
- 示例: `三一重工stock_analysis_sse_600031_20250808T040636.md` → `600031`
- 优点: 准确性高，不会误匹配日期时间等数字

#### 通用模式 (use_precise_pattern=false)
- 匹配格式: 任意6位连续数字
- 会自动过滤明显的日期格式数字
- 适用于文件名格式不规范的情况

## 返回结果格式

```json
{
  "success": true,
  "total_codes": 25,
  "codes": [
    "000429",
    "002130",
    "002230",
    "600031",
    "601899"
  ],
  "processed_files_count": 29,
  "output_file": "stock_codes.txt",
  "message": "成功提取到 25 个不重复的股票代码"
}
```

## 支持的文件名格式

### 标准格式
- `公司名stock_analysis_sse_代码_时间戳.md`
- `公司名stock_analysis_szse_代码_时间戳.md`

### 示例文件名
- `三一重工stock_analysis_sse_600031_20250808T040636.md`
- `科大讯飞stock_analysis_sse_002230_20250808T081955.md`
- `东方财富stock_analysis_sse_300059_20250808T073342.md`

## 错误处理

常见错误及解决方案：

1. **目录不存在**
   ```json
   {
     "success": false,
     "error": "目录不存在: F:\\不存在的路径",
     "message": "提取过程中出现错误: 目录不存在"
   }
   ```

2. **权限不足**
   - 确保对目标目录有读取权限
   - 确保对输出文件路径有写入权限

3. **没有找到股票代码**
   ```json
   {
     "success": true,
     "total_codes": 0,
     "codes": [],
     "message": "成功提取到 0 个不重复的股票代码"
   }
   ```

## 集成示例

### 在MCP客户端中使用

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def extract_codes():
    server_params = StdioServerParameters(
        command="python",
        args=["main.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "extract_stock_codes",
                {
                    "directory_path": "F:\\doc\\mine\\理财相关\\量化分析",
                    "output_file": "my_stock_codes.txt"
                }
            )
            
            print(result.content[0].text)

# 运行
asyncio.run(extract_codes())
```

## 注意事项

1. **路径格式**: Windows路径使用双反斜杠 `\\` 或正斜杠 `/`
2. **文件编码**: 输出文件使用UTF-8编码
3. **去重处理**: 自动去除重复的股票代码
4. **排序**: 结果按数字顺序排序
5. **递归扫描**: 会扫描指定目录及其所有子目录

## 更新日志

### v1.0.0 (2025-01-14)
- ✅ 初始版本发布
- ✅ 支持精确模式和通用模式匹配
- ✅ 集成到MCP服务器
- ✅ 完善的错误处理和日志记录