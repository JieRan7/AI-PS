# api_server.py
"""
智能进程分类与标签化模块 - 核心接口（GET版本）
"""

from fastapi import FastAPI, Query
from typing import Dict
import psutil
import uvicorn
import os
from datetime import datetime
import time

from process_classifier import ProcessClassifier
from label_manager import LabelManager

# ==================== 初始化 ====================
app = FastAPI(title="进程分类与标签化模块")

# 核心组件
config_file = "classifier_config.json"
if os.path.exists(config_file):
    classifier = ProcessClassifier(config_file)
else:
    classifier = ProcessClassifier()

label_manager = LabelManager()


# ==================== 核心接口（GET版本） ====================
@app.get("/api/classify-processes")
async def classify_and_tag_processes(
        limit: int = Query(30, ge=1, le=200, description="返回进程数量")
) -> Dict:
    """
    智能进程分类与标签化的核心接口 - GET版本

    功能：
    1. 获取系统进程
    2. 智能分类（基于名称、CPU、内存等多维特征）
    3. 合并标签信息
    4. 返回语义化分类结果

    在浏览器中直接访问：
    http://localhost:8000/api/classify-processes?limit=20
    """
    try:
        # 1. 获取进程基本信息
        processes = []
        # 第一次快速收集
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'] or 'unknown',
                    'cpu': 0.0,
                    'memory': float(proc.info['memory_percent'] or 0.0)
                })
                if len(processes) >= limit:
                    break
            except:
                continue

        # 第二次获取真实的CPU使用率
        for p in processes:
            try:
                proc = psutil.Process(p['pid'])
                p['cpu'] = float(proc.cpu_percent(interval=0.01))
            except:
                continue

        # 2. 智能分类
        classified_results = classifier.batch_classify(processes[:limit])

        # 3. 合并标签信息
        final_results = []
        for result in classified_results:
            pid = result.get('pid')
            if pid:
                labels = label_manager.get_process_labels(pid)
                result['user_labels'] = list(labels)
                result['is_tagged'] = len(labels) > 0
            else:
                result['user_labels'] = []
                result['is_tagged'] = False

            # 添加可视化标识
            result['visual_hint'] = get_visual_hint(result)
            final_results.append(result)

        # 4. 统计信息
        stats = calculate_statistics(final_results)

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_processes": len(final_results),
            "statistics": stats,
            "processes": final_results,
            "metadata": {
                "classifier_version": "1.0",
                "algorithm": "基于进程名称匹配、CPU/内存使用模式的多维特征综合评估"
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_visual_hint(process_info: Dict) -> Dict:
    """为进程生成可视化标识"""
    category = process_info.get('category', 'unknown')
    cpu = process_info.get('cpu_usage', 0)
    memory = process_info.get('memory_usage', 0)

    color_map = {
        'system_critical': 'red',
        'network_services': 'blue',
        'user_applications': 'green',
        'development_tools': 'cyan',
        'security_services': 'orange',
        'cpu_intensive': 'orange',
        'memory_intensive': 'purple',
    }

    color = 'gray'
    user_labels = process_info.get('user_labels', [])

    if 'high_priority' in user_labels:
        color = 'darkred'
    elif 'monitor_closely' in user_labels:
        color = 'orange'
    elif category in color_map:
        color = color_map[category]

    if cpu > 70 and color == 'gray':
        color = 'orange'
    if memory > 50 and color == 'gray':
        color = 'purple'

    return {
        "color": color,
        "icon": get_category_icon(category),
        "priority": calculate_priority(process_info)
    }


def get_category_icon(category: str) -> str:
    """获取分类对应的图标建议"""
    icons = {
        'system_critical': '🔴',
        'network_services': '🌐',
        'user_applications': '💻',
        'background_workers': '⚙️',
        'development_tools': '🔧',
        'security_services': '🔒',
        'cpu_intensive': '🔥',
        'memory_intensive': '💾',
        'idle_process': '💤',
        'unknown': '❓'
    }
    return icons.get(category, '❓')


def calculate_priority(process_info: Dict) -> int:
    priority = 5

    user_labels = process_info.get('user_labels', [])
    if 'high_priority' in user_labels:
        priority = 9
    elif 'business_critical' in user_labels:
        priority = 8

    category = process_info.get('category', '')
    if category == 'system_critical':
        priority = max(priority, 9)

    cpu = process_info.get('cpu_usage', 0)
    if cpu > 80:
        priority = max(priority, 8)

    return min(priority, 10)


def calculate_statistics(processes: list) -> Dict:
    stats = {
        "by_category": {},
        "tagged_processes": 0,
        "cpu_intensive": 0,
        "memory_intensive": 0
    }

    for proc in processes:
        category = proc.get('category', 'unknown')
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        if proc.get('is_tagged', False):
            stats["tagged_processes"] += 1

        cpu = proc.get('cpu_usage', 0)
        memory = proc.get('memory_usage', 0)
        if cpu > 70:
            stats["cpu_intensive"] += 1
        if memory > 30:
            stats["memory_intensive"] += 1

    return stats


# ==================== 启动 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🔧 智能进程分类与标签化模块")
    print("=" * 50)
    print("核心接口: GET /api/classify-processes")
    print("示例: http://localhost:8000/api/classify-processes?limit=20")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8000)