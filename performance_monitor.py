#!/usr/bin/env python3
"""
性能监控模块
监控文件操作性能和系统资源使用情况
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    timestamp: datetime
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    files_processed: int
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.operation_stats = defaultdict(list)
        self.start_time = datetime.now()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # 性能阈值
        self.thresholds = {
            "max_duration": 30.0,  # 秒
            "max_memory": 500.0,   # MB
            "max_cpu": 80.0,       # 百分比
            "min_success_rate": 0.95  # 95%
        }
    
    def start_monitoring(self, interval: float = 5.0):
        """启动后台监控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._background_monitor,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止后台监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("性能监控已停止")
    
    def _background_monitor(self, interval: float):
        """后台监控线程"""
        while self.monitoring_active:
            try:
                # 记录系统资源使用情况
                memory_usage = psutil.virtual_memory().percent
                cpu_usage = psutil.cpu_percent(interval=1)
                
                # 检查是否超过阈值
                if memory_usage > self.thresholds["max_memory"]:
                    logger.warning(f"内存使用率过高: {memory_usage:.1f}%")
                
                if cpu_usage > self.thresholds["max_cpu"]:
                    logger.warning(f"CPU使用率过高: {cpu_usage:.1f}%")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"后台监控出错: {e}")
                time.sleep(interval)
    
    def record_operation(self, operation: str, duration: float, 
                        files_processed: int = 0, success: bool = True,
                        error_message: Optional[str] = None):
        """记录操作性能"""
        try:
            # 获取当前系统资源使用情况
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                operation=operation,
                duration=duration,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                files_processed=files_processed,
                success=success,
                error_message=error_message
            )
            
            self.metrics_history.append(metric)
            self.operation_stats[operation].append(metric)
            
            # 检查性能阈值
            self._check_thresholds(metric)
            
        except Exception as e:
            logger.error(f"记录性能指标时出错: {e}")
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """检查性能阈值"""
        if metric.duration > self.thresholds["max_duration"]:
            logger.warning(f"操作 {metric.operation} 耗时过长: {metric.duration:.2f}秒")
        
        if metric.memory_usage > self.thresholds["max_memory"]:
            logger.warning(f"操作 {metric.operation} 内存使用过高: {metric.memory_usage:.1f}%")
        
        if not metric.success:
            logger.error(f"操作 {metric.operation} 失败: {metric.error_message}")
    
    def get_operation_stats(self, operation: Optional[str] = None, 
                           time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """获取操作统计信息"""
        if time_range:
            cutoff_time = datetime.now() - time_range
            metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        else:
            metrics = list(self.metrics_history)
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if not metrics:
            return {"error": "没有找到匹配的性能数据"}
        
        # 计算统计信息
        durations = [m.duration for m in metrics]
        memory_usages = [m.memory_usage for m in metrics]
        cpu_usages = [m.cpu_usage for m in metrics]
        success_count = sum(1 for m in metrics if m.success)
        total_files = sum(m.files_processed for m in metrics)
        
        stats = {
            "total_operations": len(metrics),
            "success_rate": success_count / len(metrics) if metrics else 0,
            "total_files_processed": total_files,
            "duration_stats": {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "total": sum(durations)
            },
            "memory_stats": {
                "min": min(memory_usages),
                "max": max(memory_usages),
                "avg": sum(memory_usages) / len(memory_usages)
            },
            "cpu_stats": {
                "min": min(cpu_usages),
                "max": max(cpu_usages),
                "avg": sum(cpu_usages) / len(cpu_usages)
            },
            "throughput": {
                "files_per_second": total_files / sum(durations) if sum(durations) > 0 else 0,
                "operations_per_minute": len(metrics) / (sum(durations) / 60) if sum(durations) > 0 else 0
            }
        }
        
        return stats
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 系统资源信息
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_count = psutil.cpu_count()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            health = {
                "system": {
                    "cpu_count": cpu_count,
                    "cpu_usage": psutil.cpu_percent(interval=1),
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "memory_usage_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                    "disk_usage_percent": (disk.used / disk.total) * 100
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                },
                "service": {
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "total_operations": len(self.metrics_history),
                    "monitoring_active": self.monitoring_active
                }
            }
            
            return health
            
        except Exception as e:
            logger.error(f"获取系统健康状态时出错: {e}")
            return {"error": str(e)}
    
    def get_performance_report(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """生成性能报告"""
        if time_range is None:
            time_range = timedelta(hours=24)  # 默认24小时
        
        report = {
            "report_time": datetime.now().isoformat(),
            "time_range_hours": time_range.total_seconds() / 3600,
            "system_health": self.get_system_health(),
            "overall_stats": self.get_operation_stats(time_range=time_range),
            "operation_breakdown": {},
            "performance_issues": [],
            "recommendations": []
        }
        
        # 按操作类型分解统计
        operations = set(m.operation for m in self.metrics_history)
        for op in operations:
            report["operation_breakdown"][op] = self.get_operation_stats(op, time_range)
        
        # 识别性能问题
        report["performance_issues"] = self._identify_performance_issues(time_range)
        
        # 生成优化建议
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _identify_performance_issues(self, time_range: timedelta) -> List[Dict[str, Any]]:
        """识别性能问题"""
        issues = []
        cutoff_time = datetime.now() - time_range
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return issues
        
        # 检查成功率
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        if success_rate < self.thresholds["min_success_rate"]:
            issues.append({
                "type": "low_success_rate",
                "severity": "high",
                "description": f"成功率过低: {success_rate:.2%}",
                "threshold": f"{self.thresholds['min_success_rate']:.2%}"
            })
        
        # 检查平均响应时间
        avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
        if avg_duration > self.thresholds["max_duration"] / 2:
            issues.append({
                "type": "slow_response",
                "severity": "medium",
                "description": f"平均响应时间过长: {avg_duration:.2f}秒",
                "threshold": f"{self.thresholds['max_duration']}秒"
            })
        
        # 检查内存使用趋势
        recent_memory = [m.memory_usage for m in recent_metrics[-10:]]  # 最近10次操作
        if recent_memory and max(recent_memory) > self.thresholds["max_memory"]:
            issues.append({
                "type": "high_memory_usage",
                "severity": "medium",
                "description": f"内存使用率过高: {max(recent_memory):.1f}%",
                "threshold": f"{self.thresholds['max_memory']}%"
            })
        
        return issues
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于性能问题生成建议
        for issue in report["performance_issues"]:
            if issue["type"] == "low_success_rate":
                recommendations.append("检查错误日志，修复导致操作失败的问题")
            elif issue["type"] == "slow_response":
                recommendations.append("考虑优化文件操作算法或增加并发处理")
            elif issue["type"] == "high_memory_usage":
                recommendations.append("优化内存使用，考虑分批处理大量文件")
        
        # 基于系统健康状态生成建议
        system = report["system_health"]["system"]
        if system["memory_usage_percent"] > 80:
            recommendations.append("系统内存使用率过高，建议增加内存或优化内存使用")
        
        if system["disk_usage_percent"] > 90:
            recommendations.append("磁盘空间不足，建议清理临时文件或扩展存储")
        
        # 基于操作统计生成建议
        overall = report["overall_stats"]
        if overall.get("throughput", {}).get("files_per_second", 0) < 10:
            recommendations.append("文件处理吞吐量较低，考虑启用并发处理")
        
        return recommendations
    
    def export_metrics(self, filepath: str, format: str = "json"):
        """导出性能指标"""
        try:
            metrics_data = []
            for metric in self.metrics_history:
                metric_dict = asdict(metric)
                metric_dict["timestamp"] = metric.timestamp.isoformat()
                metrics_data.append(metric_dict)
            
            if format.lower() == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "csv":
                import csv
                if metrics_data:
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
                        writer.writeheader()
                        writer.writerows(metrics_data)
            
            logger.info(f"性能指标已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出性能指标时出错: {e}")
    
    def clear_metrics(self, older_than: Optional[timedelta] = None):
        """清理旧的性能指标"""
        if older_than is None:
            self.metrics_history.clear()
            self.operation_stats.clear()
            logger.info("已清理所有性能指标")
        else:
            cutoff_time = datetime.now() - older_than
            
            # 清理历史记录
            self.metrics_history = deque(
                [m for m in self.metrics_history if m.timestamp >= cutoff_time],
                maxlen=self.max_history
            )
            
            # 清理操作统计
            for operation in list(self.operation_stats.keys()):
                self.operation_stats[operation] = [
                    m for m in self.operation_stats[operation] 
                    if m.timestamp >= cutoff_time
                ]
                if not self.operation_stats[operation]:
                    del self.operation_stats[operation]
            
            logger.info(f"已清理 {older_than} 之前的性能指标")

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            files_processed = 0
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                
                # 尝试从结果中提取文件处理数量
                if isinstance(result, dict):
                    if "organized_files" in result:
                        files_processed = result["organized_files"]
                    elif "renamed_files" in result:
                        files_processed = len(result["renamed_files"])
                    elif isinstance(result, list):
                        files_processed = len(result)
                    
                    success = result.get("success", True)
                    error_message = result.get("error")
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            
            finally:
                duration = time.time() - start_time
                performance_monitor.record_operation(
                    operation_name, duration, files_processed, success, error_message
                )
        
        return wrapper
    return decorator