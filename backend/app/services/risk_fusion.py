from typing import Dict, Any
from backend.app.core.config import settings


class RiskFusionEngine:
    """
    Calibrated multi-signal Risk Fusion engine.
    Fuses Supervised ML, Anomaly Detection, Behavioral Deviation, Rule Triggers,
    Graph Topology, and Temporal Risk Evolution into a transparent, audit-ready score.
    """

    def __init__(self):
        self.w_ml = settings.WEIGHT_ML_FRAUD
        self.w_anomaly = settings.WEIGHT_ANOMALY
        self.w_behavior = settings.WEIGHT_BEHAVIOR
        self.w_rule = settings.WEIGHT_RULE
        self.w_graph = settings.WEIGHT_GRAPH

    def fuse_risk_scores(
        self,
        ml_fraud_prob: float,
        anomaly_score: float,
        behavior_score: float,
        rule_score: float,
        graph_score: float,
        temporal_score: float = 0.0
    ) -> Dict[str, Any]:
        # Calibrated weighted linear component
        raw_weighted_score = (
            (ml_fraud_prob * self.w_ml) +
            (anomaly_score * self.w_anomaly) +
            (behavior_score * self.w_behavior) +
            (rule_score * self.w_rule) +
            (graph_score * self.w_graph)
        )

        # Multi-signal co-occurrence multiplier (non-linear risk amplification)
        # If at least 3 distinct signals exceed 0.60, amplify composite risk score
        high_signals = sum(1 for s in [ml_fraud_prob, anomaly_score, behavior_score, rule_score, graph_score] if s >= 0.60)
        
        amplification_factor = 1.0
        if high_signals >= 4:
            amplification_factor = 1.25
        elif high_signals >= 3:
            amplification_factor = 1.15
        elif high_signals >= 2:
            amplification_factor = 1.05

        fused_score = min(raw_weighted_score * amplification_factor + (temporal_score * 0.05), 1.0)
        fused_score = float(round(fused_score, 4))

        # Determine explicit risk level tier
        if fused_score >= 0.80:
            risk_level = "CRITICAL"
        elif fused_score >= 0.60:
            risk_level = "HIGH"
        elif fused_score >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "fused_risk_score": fused_score,
            "risk_level": risk_level,
            "signal_breakdown": {
                "ml_fraud_probability": round(float(ml_fraud_prob), 4),
                "anomaly_score": round(float(anomaly_score), 4),
                "behavior_score": round(float(behavior_score), 4),
                "rule_score": round(float(rule_score), 4),
                "graph_score": round(float(graph_score), 4),
                "temporal_score": round(float(temporal_score), 4),
            },
            "weights": {
                "ml": self.w_ml,
                "anomaly": self.w_anomaly,
                "behavior": self.w_behavior,
                "rule": self.w_rule,
                "graph": self.w_graph,
            },
            "amplification_applied": amplification_factor > 1.0,
            "amplification_factor": amplification_factor,
        }
