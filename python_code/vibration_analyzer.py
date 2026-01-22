from base_analyzer import BaseAnalyzer

VIB_THRESHOLDS = {
    "warning": 2.5,
    "critical": 4.0
}

class VibrationAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(VIB_THRESHOLDS)
