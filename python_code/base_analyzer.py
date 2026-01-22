from collections import deque
from sklearn.ensemble import IsolationForest

class BaseAnalyzer:
    def __init__(self, thresholds, window=50):
        self.thresholds = thresholds
        self.buffer = deque(maxlen=window)
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.ready = False

    def update(self, value: float):
        self.buffer.append([value])
        if len(self.buffer) >= 20:
            self.model.fit(self.buffer)
            self.ready = True

    def decide(self, value: float) -> str:
        anomaly = False
        if self.ready:
            anomaly = self.model.predict([[value]])[0] == -1

        if value >= self.thresholds["critical"]:
            return "critical"
        elif value >= self.thresholds["warning"]:
            return "warning"
        elif anomaly:
            return "risk"
        else:
            return "normal"
