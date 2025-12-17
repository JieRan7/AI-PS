from pydantic import BaseModel


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu: float
    memory: float
    threads: int
    nice: int
    anomaly: bool
    score: float
