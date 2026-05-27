from typing import List, Dict, Any
from backend.database.models import VitalsRecord

def calculate_slope(y_values: List[float]) -> float:
    """
    Simple linear regression slope (equivalent to numpy polyfit deg=1)
    """
    n = len(y_values)
    if n < 2:
        return 0.0
    x_values = list(range(n))
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_xx = sum(x * x for x in x_values)
    
    denominator = (n * sum_xx - sum_x * sum_x)
    if denominator == 0:
        return 0.0
    
    return (n * sum_xy - sum_x * sum_y) / denominator

class TrendAnalyzer:
    @staticmethod
    def analyze(vitals_history: List[VitalsRecord]) -> Dict[str, Any]:
        """
        Analyzes trends over time and returns state + score modifier.
        Requires history to be chronologically ordered (oldest to newest).
        """
        if len(vitals_history) < 2:
            return {"trend_state": "STABLE", "score_modifier": 0, "details": []}

        spo2_vals = [v.spo2 for v in vitals_history if v.spo2 is not None]
        hr_vals = [v.heart_rate for v in vitals_history if v.heart_rate is not None]
        
        details = []
        score_modifier = 0
        trend_state = "STABLE"
        
        # Analyze SpO2 (declining is bad)
        if len(spo2_vals) >= 2:
            slope = calculate_slope(spo2_vals)
            if slope < -1.0: # Dropping more than 1% per reading
                details.append("Declining SpO2")
                score_modifier += 15
                trend_state = "DECLINING"
            elif slope > 1.0:
                details.append("Improving SpO2")
                if trend_state != "DECLINING":
                    trend_state = "IMPROVING"

        # Analyze Heart Rate (rising is bad)
        if len(hr_vals) >= 2:
            slope = calculate_slope(hr_vals)
            if slope > 5.0: # Rising > 5 bpm per reading
                details.append("Rising Heart Rate")
                score_modifier += 10
                trend_state = "DECLINING"

        return {
            "trend_state": trend_state,
            "score_modifier": score_modifier,
            "details": details
        }
