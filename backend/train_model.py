import time
import psutil
import joblib
from sklearn.ensemble import IsolationForest

MODEL_PATH = "models/isolation_forest.joblib"


def collect_features(rounds=10, interval=1):
    data = []
    for _ in range(rounds):
        for proc in psutil.process_iter(
            ['cpu_percent', 'memory_percent', 'num_threads', 'nice']
        ):
            try:
                data.append([
                    float(proc.cpu_percent()),
                    float(proc.memory_percent()),
                    int(proc.num_threads()),
                    int(proc.nice())
                ])
            except psutil.NoSuchProcess:
                continue
        time.sleep(interval)
    return data


if __name__ == "__main__":
    print("[*] Collecting process behavior data...")
    X = collect_features()

    print("[*] Training IsolationForest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    model.fit(X)

    print("[*] Saving model...")
    joblib.dump(model, MODEL_PATH)

    print("[✓] Model saved to", MODEL_PATH)
