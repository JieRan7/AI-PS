# analyzer.py
import numpy as np
from sklearn.ensemble import IsolationForest


class ProcessAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42
        )

    def detect(self, processes):
        if len(processes) < 10:
            for p in processes:
                p["anomaly"] = False
                p["score"] = 0.0
            return processes

        features = []
        for p in processes:
            features.append([
                p["cpu"],
                p["memory"],
                p["threads"],
                p["nice"]
            ])

        X = np.array(features)
        preds = self.model.fit_predict(X)
        scores = self.model.decision_function(X)

        for i, p in enumerate(processes):
            p["anomaly"] = (preds[i] == -1)
            p["score"] = float(scores[i])

        return processes
