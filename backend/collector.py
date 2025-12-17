import psutil


def collect_processes(limit=100):
    processes = []

    for proc in psutil.process_iter(
        ['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'nice']
    ):
        try:
            p = {
                "pid": proc.pid,
                "name": proc.info["name"],
                "cpu": float(proc.info["cpu_percent"]),
                "memory": float(proc.info["memory_percent"]),
                "threads": int(proc.info["num_threads"]),
                "nice": int(proc.info["nice"]),
            }
            p["features"] = [
                p["cpu"],
                p["memory"],
                p["threads"],
                p["nice"]
            ]
            processes.append(p)
            if len(processes) >= limit:
                break
        except psutil.NoSuchProcess:
            continue

    return processes
