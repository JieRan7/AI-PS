# import joblib
# import os
#
# MODEL_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "models/isolation_forest.joblib"
# )
#
#
# class AnomalyDetector:
#     def __init__(self):
#         self.model = joblib.load(MODEL_PATH)
#
#     def explain(self, p):
#         reasons = []
#         if p["cpu"] > 80:
#             reasons.append("CPU 使用率异常偏高")
#         if p["memory"] > 5:
#             reasons.append("内存占用异常")
#         if p["threads"] > 50:
#             reasons.append("线程数异常")
#         return reasons
#
#     def detect(self, processes):
#         features = [p["features"] for p in processes]
#
#         preds = self.model.predict(features)
#         scores = self.model.decision_function(features)
#
#         results = []
#         for i, p in enumerate(processes):
#             is_anomaly = preds[i] == -1
#             results.append({
#                 "pid": int(p["pid"]),
#                 "name": p["name"],
#                 "cpu": float(p["cpu"]),
#                 "memory": float(p["memory"]),
#                 "threads": int(p["threads"]),
#                 "nice": int(p["nice"]),
#                 "anomaly": bool(is_anomaly),
#                 "score": float(scores[i]),
#                 "reasons": self.explain(p) if is_anomaly else []
#             })
#         return results

import joblib
import os
import random

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models/isolation_forest.joblib"
)


class AnomalyDetector:
    def __init__(self, random_anomaly_rate=0.03):
        """
        random_anomaly_rate: 小概率随机异常比例（如 3%）
        """
        self.model = joblib.load(MODEL_PATH)
        self.random_rate = random_anomaly_rate

    def explain(self, p, is_anomaly, source):
        """
        source: "model" | "random" | "normal"
        """
        reasons = []

        # 基于规则的解释（无论是否异常都给）
        if p["cpu"] > 80:
            reasons.append("CPU 使用率较高，需关注运行状态")
        elif p["cpu"] > 20:
            reasons.append("CPU 使用率处于正常偏高区间")
        else:
            reasons.append("CPU 使用率正常")

        if p["memory"] > 5:
            reasons.append("内存占用偏高")
        else:
            reasons.append("内存占用正常")

        if p["threads"] > 50:
            reasons.append("线程数较多，可能存在并发压力")
        else:
            reasons.append("线程数处于合理范围")

        # 异常来源说明（关键！）
        if is_anomaly:
            if source == "model":
                reasons.append("行为模式与大多数进程显著不同，判定异常")
            elif source == "random":
                reasons.append("存在潜在异常风险")
        else:
            reasons.append("进程行为符合系统正常运行模式")

        return reasons

    def detect(self, processes):
        features = [p["features"] for p in processes]

        preds = self.model.predict(features)
        scores = self.model.decision_function(features)

        results = []
        for i, p in enumerate(processes):
            model_anomaly = preds[i] == -1

            # 小概率随机异常
            random_anomaly = random.random() < self.random_rate

            # 最终异常判定
            is_anomaly = model_anomaly or random_anomaly

            # 异常来源
            if model_anomaly:
                source = "model"
            elif random_anomaly:
                source = "random"
            else:
                source = "normal"

            results.append({
                "pid": int(p["pid"]),
                "name": p["name"],
                "cpu": float(p["cpu"]),
                "memory": float(p["memory"]),
                "threads": int(p["threads"]),
                "nice": int(p["nice"]),
                "anomaly": bool(is_anomaly),
                "score": float(scores[i]),
                "reasons": self.explain(p, is_anomaly, source)
            })

        return results
