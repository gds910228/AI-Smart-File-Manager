# AI智能文件管理器部署指南

## 系统要求

### 最低要求
- Python 3.8+
- 内存: 512MB
- 磁盘空间: 100MB
- 操作系统: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

### 推荐配置
- Python 3.10+
- 内存: 2GB+
- 磁盘空间: 1GB+
- SSD存储（提升文件操作性能）

## 安装步骤

### 1. 环境准备

```bash
# 克隆或下载项目
git clone <repository-url>
cd ai-file-manager

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 验证安装
python -c "import mcp; print('MCP installed successfully')"
```

### 3. 配置验证

```bash
# 运行基础测试
python test_examples.py

# 运行集成测试
python integration_test.py
```

## MCP客户端集成

### Claude Desktop集成

1. 找到Claude Desktop配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

2. 添加服务器配置：
```json
{
  "mcpServers": {
    "ai-file-manager": {
      "command": "python",
      "args": ["/path/to/ai-file-manager/main.py"],
      "env": {
        "PYTHONPATH": "/path/to/ai-file-manager"
      }
    }
  }
}
```

3. 重启Claude Desktop

### 其他MCP客户端

使用提供的 `mcp_server_config.json` 文件作为配置模板，根据具体客户端要求调整路径和参数。

## 生产环境部署

### Docker部署

创建 `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

构建和运行：
```bash
docker build -t ai-file-manager .
docker run -p 8000:8000 -v /host/files:/app/files ai-file-manager
```

### 系统服务部署

创建systemd服务文件 `/etc/systemd/system/ai-file-manager.service`:
```ini
[Unit]
Description=AI File Manager MCP Server
After=network.target

[Service]
Type=simple
User=filemanager
WorkingDirectory=/opt/ai-file-manager
ExecStart=/opt/ai-file-manager/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable ai-file-manager
sudo systemctl start ai-file-manager
```

## 性能优化

### 1. 缓存配置

在 `config.py` 中调整缓存设置：
```python
# 文件分析缓存大小
ANALYSIS_CACHE_SIZE = 1000

# 搜索结果缓存时间（秒）
SEARCH_CACHE_TTL = 300
```

### 2. 并发处理

对于大量文件操作，启用并发处理：
```python
# 最大并发线程数
MAX_CONCURRENT_OPERATIONS = 4

# 批处理大小
BATCH_SIZE = 100
```

### 3. 内存优化

```python
# 大文件处理阈值
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB

# 流式处理块大小
STREAM_CHUNK_SIZE = 8192
```

## 安全配置

### 1. 路径限制

在 `config.py` 中配置允许访问的路径：
```python
ALLOWED_PATHS = [
    "/home/user/Documents",
    "/home/user/Downloads",
    "/home/user/Desktop"
]
```

### 2. 操作权限

```python
# 禁用的操作
DISABLED_OPERATIONS = ["delete", "move"]

# 需要确认的操作
REQUIRE_CONFIRMATION = ["delete", "batch_rename"]
```

### 3. 日志配置

```python
LOGGING_CONFIG = {
    "level": "INFO",
    "file": "/var/log/ai-file-manager.log",
    "max_size": "10MB",
    "backup_count": 5
}
```

## 监控和维护

### 1. 健康检查

创建健康检查端点：
```python
@server.list_resources()
async def health_check():
    return [Resource(
        uri="health://status",
        name="Health Status",
        mimeType="application/json"
    )]
```

### 2. 性能监控

```bash
# 监控内存使用
ps aux | grep main.py

# 监控文件操作
lsof -p <pid>

# 监控网络连接
netstat -tulpn | grep python
```

### 3. 日志分析

```bash
# 查看错误日志
grep ERROR /var/log/ai-file-manager.log

# 分析操作统计
grep "operation:" /var/log/ai-file-manager.log | sort | uniq -c
```

## 故障排除

### 常见问题

1. **权限错误**
   ```bash
   # 检查文件权限
   ls -la /path/to/files
   
   # 修复权限
   chmod 755 /path/to/directory
   ```

2. **依赖问题**
   ```bash
   # 重新安装依赖
   pip install --force-reinstall -r requirements.txt
   ```

3. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   
   # 调整配置
   # 减少 MAX_SEARCH_RESULTS 和 ANALYSIS_CACHE_SIZE
   ```

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

运行调试测试：
```bash
python -m pytest tests/ -v --tb=long
```

## 备份和恢复

### 配置备份

```bash
# 备份配置文件
cp config.py config.py.backup
cp mcp_server_config.json mcp_server_config.json.backup
```

### 数据备份

```bash
# 备份操作历史
cp operation_history.json operation_history.json.backup

# 备份缓存数据
cp -r cache/ cache_backup/
```

## 更新升级

### 版本更新

```bash
# 停止服务
sudo systemctl stop ai-file-manager

# 备份当前版本
cp -r /opt/ai-file-manager /opt/ai-file-manager.backup

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl start ai-file-manager
```

### 配置迁移

更新配置文件时，注意保留自定义设置：
```bash
# 合并配置
python scripts/merge_config.py config.py.backup config.py
```

## 支持和社区

- 问题报告: [GitHub Issues]
- 功能请求: [GitHub Discussions]
- 文档更新: [Wiki]
- 社区交流: [Discord/Slack]

## 许可证

本项目采用MIT许可证，详见LICENSE文件。