from flask import Flask, jsonify
from collector import collect_processes
from detector import AnomalyDetector

app = Flask(__name__)
detector = AnomalyDetector()


@app.route("/api/processes")
def get_processes():
    processes = collect_processes()
    analyzed = detector.detect(processes)
    return jsonify(analyzed)


@app.route("/")
def index():
    return "AI-enhanced ps backend running"


if __name__ == "__main__":
    app.run()
