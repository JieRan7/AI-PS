"""
标签管理器
管理进程标签的增删改查和持久化存储
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set

class LabelManager:
    def __init__(self, storage_file: str = 'process_labels.json'):
        """
        初始化标签管理器
        :param storage_file: 标签存储文件路径
        """
        self.storage_file = storage_file
        self.labels_db = {}  # 格式: {pid: {'tags': set(), 'notes': str, 'last_updated': str}}
        self.tag_definitions = {
            'high_priority': {'color': 'red', 'description': '高优先级进程'},
            'monitor_closely': {'color': 'orange', 'description': '需要密切监控'},
            'auto_restart': {'color': 'blue', 'description': '自动重启'},
            'ignore_alert': {'color': 'gray', 'description': '忽略告警'},
            'business_critical': {'color': 'purple', 'description': '业务关键'},
            'experimental': {'color': 'yellow', 'description': '实验性进程'}
        }

        # 加载已有标签
        self.load_labels()

    def add_label(self, pid: int, label: str, note: str = None) -> bool:
        """
        为进程添加标签
        :return: 是否成功添加
        """
        if pid not in self.labels_db:
            self.labels_db[pid] = {
                'tags': set(),
                'notes': '',
                'last_updated': datetime.now().isoformat()
            }

        # 检查标签是否在定义中
        if label not in self.tag_definitions:
            print(f"警告: 标签 '{label}' 未在定义中，是否要创建新标签?")

        self.labels_db[pid]['tags'].add(label)
        if note:
            self.labels_db[pid]['notes'] = note
        self.labels_db[pid]['last_updated'] = datetime.now().isoformat()

        # 自动保存
        self.save_labels()
        return True

    def remove_label(self, pid: int, label: str) -> bool:
        """移除进程的指定标签"""
        if pid in self.labels_db and label in self.labels_db[pid]['tags']:
            self.labels_db[pid]['tags'].remove(label)
            self.labels_db[pid]['last_updated'] = datetime.now().isoformat()

            # 如果没有标签了，删除该进程记录
            if not self.labels_db[pid]['tags']:
                del self.labels_db[pid]

            self.save_labels()
            return True
        return False

    def get_process_labels(self, pid: int) -> Set[str]:
        """获取进程的所有标签"""
        return self.labels_db.get(pid, {}).get('tags', set())

    def get_process_info(self, pid: int) -> Dict:
        """获取进程的完整标签信息"""
        return self.labels_db.get(pid, {})

    def search_by_tag(self, tag: str) -> List[int]:
        """根据标签查找进程"""
        result = []
        for pid, info in self.labels_db.items():
            if tag in info['tags']:
                result.append(pid)
        return result

    def get_all_tags(self) -> Dict[str, Dict]:
        """获取所有标签定义"""
        return self.tag_definitions

    def add_tag_definition(self, tag: str, color: str = 'white', description: str = ''):
        """添加新的标签定义"""
        self.tag_definitions[tag] = {
            'color': color,
            'description': description
        }

    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签使用统计"""
        stats = {}
        for info in self.labels_db.values():
            for tag in info['tags']:
                stats[tag] = stats.get(tag, 0) + 1
        return stats

    def merge_with_classification(self, classification_results: List[Dict]) -> List[Dict]:
        """
        将分类结果与标签合并
        :param classification_results: 分类器返回的结果列表
        :return: 合并后的结果
        """
        merged_results = []
        for result in classification_results:
            pid = result.get('pid')
            if pid:
                labels = self.get_process_labels(pid)
                result['manual_labels'] = list(labels)
                result['has_manual_labels'] = len(labels) > 0
            else:
                result['manual_labels'] = []
                result['has_manual_labels'] = False
            merged_results.append(result)
        return merged_results


    def save_labels(self):
        """保存标签到文件"""
        # 转换set为list以便JSON序列化
        save_data = {}
        for pid, info in self.labels_db.items():
            save_data[str(pid)] = {
                'tags': list(info['tags']),
                'notes': info['notes'],
                'last_updated': info['last_updated']
            }

        with open(self.storage_file, 'w') as f:
            json.dump({
                'labels': save_data,
                'tag_definitions': self.tag_definitions,
                'last_saved': datetime.now().isoformat()
            }, f, indent=2)

    def load_labels(self):
        """从文件加载标签"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)

                    # 恢复labels_db
                    self.labels_db = {}
                    for pid_str, info in data.get('labels', {}).items():
                        self.labels_db[int(pid_str)] = {
                            'tags': set(info['tags']),
                            'notes': info['notes'],
                            'last_updated': info['last_updated']
                        }

                    # 恢复标签定义
                    self.tag_definitions.update(data.get('tag_definitions', {}))
            except Exception as e:
                print(f"加载标签文件失败: {e}")
                self.labels_db = {}