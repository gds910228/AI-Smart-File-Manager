# AI智能文件管理器性能优化指南

## 概述

本指南提供了优化AI智能文件管理器性能的详细说明，包括系统配置、代码优化和监控策略。

## 性能监控

### 启用性能监控

```python
from performance_monitor import performance_monitor

# 启动后台监控
performance_monitor.start_monitoring(interval=5.0)

# 获取性能报告
report = performance_monitor.get_performance_report()
print(json.dumps(report, indent=2, ensure_ascii=False))
```

### 监控指标

- **操作耗时**: 每个文件操作的执行时间
- **内存使用**: 系统和进程内存使用情况
- **CPU使用**: 处理器使用率
- **吞吐量**: 每秒处理的文件数量
- **成功率**: 操作成功的百分比

## 性能优化策略

### 1. 文件搜索优化

#### 索引缓存
```python
# 在config.py中配置
ENABLE_SEARCH_CACHE = True
SEARCH_CACHE_SIZE = 10000
SEARCH_CACHE_TTL = 300  # 5分钟
```

#### 并行搜索
```python
import concurrent.futures
from pathlib import Path

def parallel_search(directories, criteria):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(search_directory, dir_path, criteria)
            for dir_path in directories
        ]
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
    return results
```

#### 智能过滤
```python
def optimized_file_filter(file_path, criteria):
    # 先检查文件大小（最快）
    if criteria.size_min or criteria.size_max:
        try:
            size = file_path.stat().st_size
            if criteria.size_min and size < criteria.size_min:
                return False
            if criteria.size_max and size > criteria.size_max:
                return False
        except OSError:
            return False
    
    # 再检查扩展名
    if criteria.file_type:
        ext = file_path.suffix.lower().lstrip('.')
        if ext not in criteria.file_type:
            return False
    
    # 最后检查名称模式（最慢）
    if criteria.name_pattern:
        if not re.search(criteria.name_pattern, file_path.name, re.IGNORECASE):
            return False
    
    return True
```

### 2. 文件操作优化

#### 批量操作
```python
def batch_file_operation(files, operation, batch_size=100):
    results = {"success": [], "failed": []}
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batch_results = process_file_batch(batch, operation)
        results["success"].extend(batch_results["success"])
        results["failed"].extend(batch_results["failed"])
        
        # 避免内存积累
        if i % (batch_size * 10) == 0:
            import gc
            gc.collect()
    
    return results
```

#### 异步文件操作
```python
import asyncio
import aiofiles

async def async_file_copy(source, destination):
    async with aiofiles.open(source, 'rb') as src:
        async with aiofiles.open(destination, 'wb') as dst:
            while chunk := await src.read(8192):
                await dst.write(chunk)
```

### 3. 内存优化

#### 流式处理
```python
def stream_large_file_analysis(file_path, chunk_size=8192):
    """流式处理大文件，避免一次性加载到内存"""
    file_hash = hashlib.md5()
    file_size = 0
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
            file_size += len(chunk)
    
    return {
        "size": file_size,
        "hash": file_hash.hexdigest()
    }
```

#### 内存池管理
```python
class MemoryPool:
    def __init__(self, max_size=100 * 1024 * 1024):  # 100MB
        self.max_size = max_size
        self.current_size = 0
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def put(self, key, value):
        value_size = sys.getsizeof(value)
        
        if value_size > self.max_size:
            return False  # 值太大，不缓存
        
        # 清理空间
        while self.current_size + value_size > self.max_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.current_size += value_size
        return True
```

### 4. 磁盘I/O优化

#### SSD优化
```python
# 针对SSD的优化配置
SSD_OPTIMIZATIONS = {
    "read_ahead": False,  # SSD不需要预读
    "use_direct_io": True,  # 绕过系统缓存
    "batch_size": 1000,  # 增加批处理大小
    "concurrent_operations": 8  # 增加并发数
}

def optimize_for_ssd():
    """针对SSD存储的优化设置"""
    import os
    
    # 设置环境变量
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # 调整文件操作参数
    global BATCH_SIZE, MAX_CONCURRENT_OPERATIONS
    BATCH_SIZE = SSD_OPTIMIZATIONS["batch_size"]
    MAX_CONCURRENT_OPERATIONS = SSD_OPTIMIZATIONS["concurrent_operations"]
```

#### 磁盘缓存策略
```python
class DiskCache:
    def __init__(self, cache_dir="/tmp/ai_file_manager_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = 1024 * 1024 * 1024  # 1GB
    
    def get_file_info_cached(self, file_path):
        cache_key = hashlib.md5(str(file_path).encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            # 检查缓存是否过期
            cache_mtime = cache_file.stat().st_mtime
            file_mtime = Path(file_path).stat().st_mtime
            
            if cache_mtime > file_mtime:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        # 缓存不存在或过期，重新计算
        file_info = self.calculate_file_info(file_path)
        
        # 保存到缓存
        with open(cache_file, 'w') as f:
            json.dump(file_info, f)
        
        return file_info
```

### 5. 网络优化

#### 连接池管理
```python
import asyncio
from asyncio import Semaphore

class ConnectionPool:
    def __init__(self, max_connections=10):
        self.semaphore = Semaphore(max_connections)
        self.active_connections = 0
    
    async def acquire(self):
        await self.semaphore.acquire()
        self.active_connections += 1
    
    def release(self):
        self.semaphore.release()
        self.active_connections -= 1
```

#### 请求优化
```python
async def optimized_mcp_request(request_data):
    # 压缩请求数据
    if len(json.dumps(request_data)) > 1024:
        import gzip
        compressed_data = gzip.compress(
            json.dumps(request_data).encode('utf-8')
        )
        request_data = {
            "compressed": True,
            "data": compressed_data.hex()
        }
    
    return request_data
```

## 性能基准测试

### 基准测试套件

```python
import time
import statistics
from pathlib import Path

class PerformanceBenchmark:
    def __init__(self):
        self.results = {}
    
    def benchmark_search(self, test_dir, iterations=10):
        """基准测试文件搜索性能"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # 执行搜索操作
            criteria = FileSearchCriteria(
                path=str(test_dir),
                file_type=["txt", "pdf", "jpg"]
            )
            results = self.file_manager.search_files(criteria)
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        self.results["search"] = {
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "files_found": len(results)
        }
    
    def benchmark_organization(self, test_dir, iterations=5):
        """基准测试文件整理性能"""
        times = []
        
        for _ in range(iterations):
            # 准备测试环境
            self.setup_test_files(test_dir)
            
            start_time = time.time()
            
            # 执行整理操作
            result = self.advanced_ops.smart_organize_directory(
                str(test_dir), "type"
            )
            
            end_time = time.time()
            times.append(end_time - start_time)
            
            # 清理测试环境
            self.cleanup_test_files(test_dir)
        
        self.results["organization"] = {
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "files_organized": result.get("organized_files", 0)
        }
    
    def run_all_benchmarks(self, test_dir):
        """运行所有基准测试"""
        print("开始性能基准测试...")
        
        self.benchmark_search(test_dir)
        self.benchmark_organization(test_dir)
        
        return self.results
```

### 性能目标

| 操作类型 | 目标性能 | 测试条件 |
|---------|---------|---------|
| 文件搜索 | < 2秒 | 10,000个文件 |
| 文件整理 | < 5秒 | 1,000个文件 |
| 批量重命名 | < 3秒 | 500个文件 |
| 文件分析 | < 10秒 | 5,000个文件 |
| 压缩操作 | < 30秒 | 100MB数据 |

## 系统调优

### 操作系统级优化

#### Linux系统
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "vm.swappiness=10" >> /etc/sysctl.conf
echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf

# 应用设置
sysctl -p
```

#### Windows系统
```powershell
# 增加系统缓存
fsutil behavior set DisableLastAccess 1

# 优化磁盘性能
fsutil behavior set DisableDeleteNotify 0
```

### Python解释器优化

```bash
# 使用优化的Python解释器
export PYTHONOPTIMIZE=2

# 启用垃圾回收优化
export PYTHONGC=1

# 设置内存分配器
export PYTHONMALLOC=pymalloc
```

### 依赖库优化

```python
# 使用更快的JSON库
try:
    import orjson as json
except ImportError:
    import json

# 使用更快的正则表达式库
try:
    import regex as re
except ImportError:
    import re

# 使用更快的哈希库
try:
    import xxhash
    def fast_hash(data):
        return xxhash.xxh64(data).hexdigest()
except ImportError:
    import hashlib
    def fast_hash(data):
        return hashlib.md5(data).hexdigest()
```

## 监控和告警

### 性能监控仪表板

```python
def generate_performance_dashboard():
    """生成性能监控仪表板数据"""
    monitor = performance_monitor
    
    dashboard_data = {
        "current_time": datetime.now().isoformat(),
        "system_health": monitor.get_system_health(),
        "recent_operations": monitor.get_operation_stats(
            time_range=timedelta(hours=1)
        ),
        "performance_trends": get_performance_trends(),
        "alerts": get_active_alerts()
    }
    
    return dashboard_data

def get_performance_trends():
    """获取性能趋势数据"""
    # 按小时统计最近24小时的性能数据
    trends = {}
    for hour in range(24):
        start_time = datetime.now() - timedelta(hours=hour+1)
        end_time = datetime.now() - timedelta(hours=hour)
        
        hour_metrics = [
            m for m in performance_monitor.metrics_history
            if start_time <= m.timestamp < end_time
        ]
        
        if hour_metrics:
            trends[f"hour_{hour}"] = {
                "operations": len(hour_metrics),
                "avg_duration": sum(m.duration for m in hour_metrics) / len(hour_metrics),
                "success_rate": sum(1 for m in hour_metrics if m.success) / len(hour_metrics)
            }
    
    return trends
```

### 告警系统

```python
class AlertManager:
    def __init__(self):
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda stats: stats.get("success_rate", 1) < 0.9,
                "severity": "high",
                "message": "错误率过高"
            },
            {
                "name": "slow_response",
                "condition": lambda stats: stats.get("duration_stats", {}).get("avg", 0) > 10,
                "severity": "medium",
                "message": "响应时间过慢"
            },
            {
                "name": "high_memory",
                "condition": lambda health: health.get("system", {}).get("memory_usage_percent", 0) > 90,
                "severity": "high",
                "message": "内存使用率过高"
            }
        ]
    
    def check_alerts(self):
        """检查告警条件"""
        active_alerts = []
        
        # 获取当前统计数据
        stats = performance_monitor.get_operation_stats(
            time_range=timedelta(minutes=10)
        )
        health = performance_monitor.get_system_health()
        
        for rule in self.alert_rules:
            try:
                if rule["name"].startswith("high_memory"):
                    triggered = rule["condition"](health)
                else:
                    triggered = rule["condition"](stats)
                
                if triggered:
                    active_alerts.append({
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"检查告警规则 {rule['name']} 时出错: {e}")
        
        return active_alerts
```

## 故障排除

### 常见性能问题

1. **内存泄漏**
   ```python
   # 检测内存泄漏
   import tracemalloc
   
   tracemalloc.start()
   
   # 执行操作
   perform_file_operations()
   
   # 检查内存使用
   current, peak = tracemalloc.get_traced_memory()
   print(f"当前内存: {current / 1024 / 1024:.1f} MB")
   print(f"峰值内存: {peak / 1024 / 1024:.1f} MB")
   
   tracemalloc.stop()
   ```

2. **CPU使用率过高**
   ```python
   # 使用cProfile分析性能瓶颈
   import cProfile
   import pstats
   
   profiler = cProfile.Profile()
   profiler.enable()
   
   # 执行操作
   perform_file_operations()
   
   profiler.disable()
   
   # 分析结果
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(10)  # 显示前10个最耗时的函数
   ```

3. **磁盘I/O瓶颈**
   ```python
   # 监控磁盘I/O
   import psutil
   
   def monitor_disk_io():
       disk_io_start = psutil.disk_io_counters()
       
       # 执行文件操作
       perform_file_operations()
       
       disk_io_end = psutil.disk_io_counters()
       
       read_bytes = disk_io_end.read_bytes - disk_io_start.read_bytes
       write_bytes = disk_io_end.write_bytes - disk_io_start.write_bytes
       
       print(f"读取: {read_bytes / 1024 / 1024:.1f} MB")
       print(f"写入: {write_bytes / 1024 / 1024:.1f} MB")
   ```

### 性能调试工具

```python
class PerformanceProfiler:
    def __init__(self):
        self.profiles = {}
    
    def profile_function(self, func_name):
        """函数性能分析装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    
                    profile_data = {
                        "duration": end_time - start_time,
                        "memory_delta": end_memory - start_memory,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if func_name not in self.profiles:
                        self.profiles[func_name] = []
                    
                    self.profiles[func_name].append(profile_data)
            
            return wrapper
        return decorator
    
    def get_profile_summary(self, func_name):
        """获取函数性能摘要"""
        if func_name not in self.profiles:
            return None
        
        profiles = self.profiles[func_name]
        durations = [p["duration"] for p in profiles]
        memory_deltas = [p["memory_delta"] for p in profiles]
        
        return {
            "call_count": len(profiles),
            "avg_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "avg_memory_delta": statistics.mean(memory_deltas),
            "total_duration": sum(durations)
        }
```

## 最佳实践

1. **定期性能测试**: 在每次代码更新后运行基准测试
2. **监控关键指标**: 持续监控响应时间、内存使用和错误率
3. **渐进式优化**: 先优化最影响性能的部分
4. **缓存策略**: 合理使用缓存，但要注意缓存一致性
5. **资源清理**: 及时释放不再使用的资源
6. **并发控制**: 合理设置并发数，避免资源竞争
7. **错误处理**: 优雅处理错误，避免性能下降
8. **日志优化**: 在生产环境中减少详细日志输出

通过遵循这些性能优化指南，AI智能文件管理器可以在各种环境下保持高效运行。
