from base_analyzer import BaseAnalyzer

TEMP_THRESHOLDS = {
    "warning": 80,
    "critical": 90
}

class TempAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(TEMP_THRESHOLDS)
