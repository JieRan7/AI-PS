import pandas as pd
import psutil
import threading
import time
import logging

# 禁用 Prophet 的繁琐日志
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

class ResourceMonitor:
    def __init__(self):
        # ds 是 Prophet 要求的列名（时间戳），y 是预测值
        self.history = pd.DataFrame(columns=['ds', 'pid', 'name', 'cpu', 'mem'])
        self.lock = threading.Lock()

    def collect_data(self):
        """后台循环采集系统资源数据"""
        print("[*] 资源采集线程已启动...")
        while True:
            now = pd.Timestamp.now()
            new_samples = []
            
            # 获取所有进程快照
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 获取 CPU 和内存占用
                    cpu = proc.cpu_percent(interval=None) 
                    mem = proc.memory_percent()
                    
                    new_samples.append({
                        'ds': now,
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': cpu,
                        'mem': mem
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            with self.lock:
                if new_samples:
                    new_df = pd.DataFrame(new_samples)
                    self.history = pd.concat([self.history, new_df], ignore_index=True)
                    # 打印当前进度
                    print(f"[*] 数据采集成功，当前总样本数: {len(self.history)}", flush=True)
                
                # 保持最近的记录，避免内存溢出
                if len(self.history) > 5000:
                    self.history = self.history.tail(2000)
            
            time.sleep(5)

    def start_monitoring(self):
        """以守护线程方式启动采集"""
        thread = threading.Thread(target=self.collect_data, daemon=True)
        thread.start()