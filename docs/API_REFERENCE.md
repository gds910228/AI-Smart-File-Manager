# AI智能文件管理器 API参考文档

## 概述

AI智能文件管理器提供了一套完整的MCP工具，支持通过自然语言进行文件操作。本文档详细描述了所有可用的工具和它们的参数。

## MCP工具列表

### 1. natural_language_file_operation

**描述**: 使用自然语言执行文件操作的主要工具

**输入参数**:
```json
{
  "command": {
    "type": "string",
    "description": "自然语言文件操作指令",
    "required": true
  }
}
```

**支持的自然语言指令示例**:
- `"搜索桌面上的图片文件"`
- `"删除大于100MB的视频文件"`
- `"按类型整理下载文件夹"`
- `"压缩所有PDF文件为backup.zip"`
- `"find all documents from last week"`

**返回格式**:
```json
{
  "type": "text",
  "text": "操作结果的JSON格式字符串"
}
```

### 2. search_files

**描述**: 基于条件搜索文件

**输入参数**:
```json
{
  "name_pattern": {
    "type": "string",
    "description": "文件名模式（正则表达式）",
    "required": false
  },
  "file_type": {
    "type": "array",
    "items": {"type": "string"},
    "description": "文件扩展名列表",
    "required": false
  },
  "path": {
    "type": "string",
    "description": "搜索路径",
    "required": false
  },
  "size_min": {
    "type": "integer",
    "description": "最小文件大小（字节）",
    "required": false
  },
  "size_max": {
    "type": "integer",
    "description": "最大文件大小（字节）",
    "required": false
  }
}
```

**使用示例**:
```json
{
  "name_pattern": "report.*2024",
  "file_type": ["pdf", "docx"],
  "path": "/home/user/Documents",
  "size_min": 1048576
}
```

**返回格式**:
```json
[
  {
    "path": "/path/to/file.pdf",
    "name": "file.pdf",
    "size": 2048576,
    "modified": "2024-01-15T10:30:00",
    "type": "application/pdf"
  }
]
```

### 3. move_files

**描述**: 移动文件到指定位置

**输入参数**:
```json
{
  "source_paths": {
    "type": "array",
    "items": {"type": "string"},
    "description": "源文件路径列表",
    "required": true
  },
  "destination": {
    "type": "string",
    "description": "目标目录路径",
    "required": true
  }
}
```

**返回格式**:
```json
{
  "success": [
    {"from": "/path/to/source.txt", "to": "/path/to/dest/source.txt"}
  ],
  "failed": [
    {"path": "/path/to/missing.txt", "error": "File not found"}
  ]
}
```

### 4. copy_files

**描述**: 复制文件到指定位置

**输入参数**: 与 `move_files` 相同

**返回格式**: 与 `move_files` 相同

### 5. delete_files

**描述**: 删除文件或目录

**输入参数**:
```json
{
  "file_paths": {
    "type": "array",
    "items": {"type": "string"},
    "description": "要删除的文件/目录路径列表",
    "required": true
  }
}
```

**返回格式**:
```json
{
  "success": ["/path/to/deleted/file.txt"],
  "failed": [
    {"path": "/path/to/protected.txt", "error": "Permission denied"}
  ]
}
```

### 6. compress_files

**描述**: 压缩文件为ZIP格式

**输入参数**:
```json
{
  "file_paths": {
    "type": "array",
    "items": {"type": "string"},
    "description": "要压缩的文件路径列表",
    "required": true
  },
  "output_path": {
    "type": "string",
    "description": "输出ZIP文件路径",
    "required": true
  }
}
```

**返回格式**:
```json
{
  "success": true,
  "output": "/path/to/archive.zip"
}
```

## 高级功能API

### 智能整理

通过自然语言指令 `"按[类型|日期|大小|扩展名]整理[目录路径]"` 调用

**整理类型**:
- `type`: 按文件类型分类
- `date`: 按修改日期分类
- `size`: 按文件大小分类
- `extension`: 按文件扩展名分类

### 批量重命名

通过自然语言指令 `"批量重命名文件为[模式]"` 调用

**重命名模式变量**:
- `{name}`: 原文件名（不含扩展名）
- `{ext}`: 文件扩展名
- `{index}`: 序号
- `{index:02d}`: 两位数序号（补零）
- `{date}`: 修改日期（YYYYMMDD）
- `{time}`: 修改时间（HHMMSS）
- `{year}`, `{month}`, `{day}`: 年月日
- `{size}`: 文件大小

**示例模式**:
- `"file_{index:03d}_{name}{ext}"` → `file_001_document.pdf`
- `"backup_{date}_{name}{ext}"` → `backup_20240115_report.docx`

### 文件分析

通过自然语言指令 `"分析[目录路径]"` 调用

**分析结果包含**:
- 文件和目录统计
- 文件类型分布
- 大小分布
- 重复文件检测
- 最大/最新/最旧文件
- 整理建议

## 错误处理

所有工具都包含错误处理机制：

**常见错误类型**:
- `"File not found"`: 文件不存在
- `"Permission denied"`: 权限不足
- `"Invalid path"`: 路径无效
- `"Unsafe path"`: 不安全的路径（系统目录）

**错误返回格式**:
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

## 安全限制

为确保系统安全，以下路径受到保护：
- `/System` (macOS)
- `/Windows`, `/Program Files` (Windows)
- 其他系统关键目录

## 使用建议

1. **自然语言优先**: 优先使用 `natural_language_file_operation` 工具
2. **预览模式**: 对于批量操作，建议先使用预览模式
3. **路径验证**: 确保提供的路径存在且有适当权限
4. **备份重要文件**: 在执行删除或移动操作前备份重要文件

## 示例工作流

### 清理下载文件夹
```json
{
  "tool": "natural_language_file_operation",
  "arguments": {
    "command": "按类型整理下载文件夹，然后删除空文件夹"
  }
}
```

### 备份重要文档
```json
{
  "tool": "natural_language_file_operation",
  "arguments": {
    "command": "搜索文档文件夹中的PDF文件，然后压缩为documents_backup.zip"
  }
}
```

### 清理大文件
```json
{
  "tool": "natural_language_file_operation",
  "arguments": {
    "command": "搜索大于500MB的文件，显示列表供用户确认删除"
  }
}