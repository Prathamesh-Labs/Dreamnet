from app.engines.discovery.schemas import DetectedPattern

class DiscoveryScorer:
    @staticmethod
    def score_pattern(pattern: DetectedPattern, evaluations_confidence: float = 0.90) -> tuple[float, float, float, float]:
        # 1. Novelty Score
        if pattern.pattern_type == "contradiction":
            novelty = 0.85
        elif pattern.pattern_type == "unexpected_magnitude":
            novelty = 0.80
        elif pattern.pattern_type == "unexpected_direction":
            novelty = 0.75
        elif pattern.pattern_type == "repeated_pattern":
            novelty = 0.60
        else:
            novelty = 0.50

        # 2. Confidence Score
        confidence = evaluations_confidence

        # 3. Significance Score
        if pattern.pattern_type == "unexpected_magnitude":
            delta_pct = pattern.evidence.get("delta_pct", 0.0)
            significance = min(0.60 + (delta_pct / 200.0), 0.98)
        elif pattern.pattern_type == "contradiction":
            significance = 0.90
        elif pattern.pattern_type == "unexpected_direction":
            significance = 0.80
        elif pattern.pattern_type == "repeated_pattern":
            significance = 0.75
        else:
            significance = 0.50

        # 4. Reproducibility Score
        supporting_count = len(pattern.supporting_experiments)
        if supporting_count == 1:
            reproducibility = 0.50
        elif supporting_count == 2:
            reproducibility = 0.80
        else:
            reproducibility = 0.95

        return novelty, confidence, significance, reproducibility
