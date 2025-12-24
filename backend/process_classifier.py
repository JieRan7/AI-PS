"""
智能进程分类器
扩展原有分类器，增加更多功能和标签化支持
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
import psutil
import time

class ProcessClassifier:
    def __init__(self, config_file: str = None):
        """初始化分类器，可加载配置文件"""
        self.process_categories = {
            'system_critical': ['systemd', 'init', 'kthreadd', 'udevd', 'dbus'],
            'network_services': ['sshd', 'nginx', 'apache', 'postgres', 'mysql', 'redis'],
            'user_applications': ['chrome', 'firefox', 'code', 'pycharm', 'sublime', 'thunderbird'],
            'background_workers': ['cron', 'atd', 'worker', 'celery', 'supervisord'],
            'development_tools': ['python', 'java', 'node', 'golang', 'docker'],
            'security_services': ['fail2ban', 'firewalld', 'auditd', 'clamav']
        }

        # 性能标签定义
        self.performance_tags = {
            'cpu_intensive': lambda cpu, mem: cpu > 70,
            'memory_intensive': lambda cpu, mem: mem > 30,
            'low_resource': lambda cpu, mem: cpu < 5 and mem < 5,
            'stable_process': lambda cpu, mem: 5 <= cpu <= 30 and 5 <= mem <= 20,
            'high_io': lambda cpu, mem: False
        }

        # 自定义分类规则
        self.custom_rules = []

        # 添加这些新属性来支持配置
        self.performance_thresholds = {}
        self.tag_definitions = {}
        self.system_settings = {}

        # 加载配置文件 - 改为更安全的加载方式
        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str):
        """从文件加载配置"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)

                    # 更新各个配置部分
                    self.process_categories.update(config.get('process_categories', {}))
                    self.custom_rules = config.get('custom_rules', [])

                    # 加载新的配置项
                    self.performance_thresholds = config.get('performance_thresholds', {})
                    self.tag_definitions = config.get('tag_definitions', {})
                    self.system_settings = config.get('system_settings', {})

                    # 根据配置文件更新性能标签
                    self._update_performance_tags_from_config()

                    print(f"✓ 配置文件加载成功: {config_file}")
                    return True
            else:
                print(f"⚠ 配置文件不存在: {config_file}，使用默认配置")
                return False
        except Exception as e:
            print(f"✗ 加载配置文件失败: {e}")
            return False

    def _update_performance_tags_from_config(self):
        """根据配置文件更新性能标签"""
        if self.performance_thresholds:
            # 更新性能标签的阈值
            cpu_intensive_thresh = self.performance_thresholds.get('cpu_intensive', 70)
            memory_intensive_thresh = self.performance_thresholds.get('memory_intensive', 30)
            low_cpu_thresh = self.performance_thresholds.get('low_resource_cpu', 5)
            low_mem_thresh = self.performance_thresholds.get('low_resource_memory', 5)
            stable_cpu_min = self.performance_thresholds.get('stable_cpu_min', 5)
            stable_cpu_max = self.performance_thresholds.get('stable_cpu_max', 30)
            stable_mem_min = self.performance_thresholds.get('stable_memory_min', 5)
            stable_mem_max = self.performance_thresholds.get('stable_memory_max', 20)

            self.performance_tags = {
                'cpu_intensive': lambda cpu, mem: cpu > cpu_intensive_thresh,
                'memory_intensive': lambda cpu, mem: mem > memory_intensive_thresh,
                'low_resource': lambda cpu, mem: cpu < low_cpu_thresh and mem < low_mem_thresh,
                'stable_process': lambda cpu, mem: stable_cpu_min <= cpu <= stable_cpu_max
                                                   and stable_mem_min <= mem <= stable_mem_max,
                'high_io': lambda cpu, mem: False
            }

    def classify_process(self, process_name: str, cpu_usage: float, memory_usage: float) -> Dict[str, Any]:
        """
        基于多维度特征分类进程，返回分类和标签信息
        返回格式: {'category': '类别', 'tags': ['标签1', '标签2'], 'confidence': 置信度}
        """
        category_scores = {}
        suggested_tags = []
        # 1. 基于名称匹配
        for category, keywords in self.process_categories.items():
            for keyword in keywords:
                if keyword.lower() in process_name.lower():
                    category_scores[category] = category_scores.get(category, 0) + 1

        # 2. 基于资源使用模式
        if cpu_usage < 1 and memory_usage < 1:
            category_scores['idle_process'] = category_scores.get('idle_process', 0) + 2
            suggested_tags.append('low_resource')

        elif cpu_usage > 50:
            category_scores['cpu_intensive'] = category_scores.get('cpu_intensive', 0) + 2
            suggested_tags.append('cpu_intensive')
        elif memory_usage > 30:
            suggested_tags.append('memory_intensive')
        elif 5 <= cpu_usage <= 30 and 5 <= memory_usage <= 20:
            suggested_tags.append('stable_process')
        # 3. 应用自定义规则
        for rule in self.custom_rules:
            if self._match_rule(rule, process_name, cpu_usage, memory_usage):
                category_scores[rule['category']] = category_scores.get(rule['category'], 0) + rule.get('weight', 1)

        # 4. 确定最终分类
        if category_scores:
            final_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[final_category] / sum(category_scores.values())
        else:
            final_category = 'unknown'
            confidence = 0.0

        # 5. 自动添加性能标签
        for tag_name, condition_func in self.performance_tags.items():
            if condition_func(cpu_usage, memory_usage):
                if tag_name not in suggested_tags:
                    suggested_tags.append(tag_name)

        return {
            'category': final_category,
            'tags': suggested_tags,
            'confidence': round(confidence, 2),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'process_name': process_name
        }

    def add_custom_rule(self, category: str, keywords: List[str],
                        cpu_threshold: float = None,
                        memory_threshold: float = None,
                        weight: int = 1):
        """添加自定义分类规则"""
        rule = {
            'category': category,
            'keywords': keywords,
            'cpu_threshold': cpu_threshold,
            'memory_threshold': memory_threshold,
            'weight': weight
        }
        self.custom_rules.append(rule)

    def _match_rule(self, rule: Dict, process_name: str, cpu: float, memory: float) -> bool:
        """检查进程是否匹配规则"""
        try:
            # 检查关键词
            keyword_match = any(keyword.lower() in process_name.lower()
                                for keyword in rule.get('keywords', []))

            # 检查CPU阈值（安全地获取）
            cpu_threshold = rule.get('cpu_threshold')
            cpu_match = True if cpu_threshold is None else cpu > cpu_threshold

            # 检查内存阈值（安全地获取）
            memory_threshold = rule.get('memory_threshold')
            memory_match = True if memory_threshold is None else memory > memory_threshold

            return keyword_match and cpu_match and memory_match
        except Exception as e:
            print(f"匹配规则时出错: {e}, rule: {rule}")
            return False

    def save_config(self, config_file: str):
        """保存配置到文件"""
        config = {
            'process_categories': self.process_categories,
            'custom_rules': self.custom_rules,
            'timestamp': datetime.now().isoformat()
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    """
    def load_config(self, config_file: str):
        # 从文件加载配置
        with open(config_file, 'r') as f:
            config = json.load(f)
            self.process_categories.update(config.get('process_categories', {}))
            self.custom_rules = config.get('custom_rules', [])
    """

    def batch_classify(self, process_list: List[Dict]) -> List[Dict]:
        """批量分类进程列表"""
        results = []
        for process in process_list:
            result = self.classify_process(
                process.get('name', ''),
                process.get('cpu', 0),
                process.get('memory', 0)
            )
            result['pid'] = process.get('pid', 'N/A')
            results.append(result)
        return results

    def monitor_and_classify(self, interval: float = 2.0, duration: int = None):
        """
        实时监控并分类进程
        :param interval: 监控间隔（秒）
        :param duration: 监控时长（秒），None表示无限
        """
        print(f"🔍 开始实时进程监控 (间隔: {interval}秒)")
        print("按 Ctrl+C 停止监控")
        try:
            start_time = time.time()
            iteration = 0
            while True:
                iteration += 1
                current_time = time.time()

                # 检查是否超过指定时长
                if duration and (current_time - start_time) > duration:
                    break

                # 获取当前进程
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'] or 'unknown',
                            'cpu': proc.info['cpu_percent'] or 0.0,
                            'memory': proc.info['memory_percent'] or 0.0
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # 分类并显示结果
                results = self.batch_classify(processes)
                # 显示统计信息
                self.display_monitoring_stats(results, iteration, current_time)
                # 等待下一次监控
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n🛑 监控已停止")

    def display_monitoring_stats(self, results, iteration, timestamp):
        """显示监控统计信息"""
        # 按类别统计
        category_counts = {}
        for result in results:
            category = result['category']
            category_counts[category] = category_counts.get(category, 0) + 1

        print(f"\n📊 监控轮次 #{iteration} - {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
        print(f"进程总数: {len(results)}")

        # 显示前5个最常见的类别
        print("主要类别分布:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = (count / len(results)) * 100
            print(f"  {category:<20}: {count:3} ({percentage:.1f}%)")