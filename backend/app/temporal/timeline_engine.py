from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone


class TemporalRiskEngine:
    """
    Computes step-by-step risk evolution timeline events for transactions.
    Tracks how risk accumulated over event sequence.
    """

    def compute_risk_timeline(
        self,
        transaction: Dict[str, Any],
        behavior_res: Dict[str, Any],
        rule_res: Dict[str, Any],
        graph_res: Dict[str, Any],
        fused_risk_score: float
    ) -> List[Dict[str, Any]]:
        ts_raw = transaction.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                base_time = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                base_time = datetime.now(timezone.utc)
        else:
            base_time = datetime.now(timezone.utc)

        events = []
        curr_risk = 0.15 # Baseline initial account risk

        # Event 1: Transaction Initiated
        events.append({
            "timestamp": (base_time - timedelta(minutes=5)).isoformat(),
            "event_name": "Transaction Ingested",
            "risk_delta": round(curr_risk, 4),
            "resulting_risk_score": round(curr_risk, 4),
            "description": f"Initial transaction ingest (${transaction.get('amount', 0):.2f} via {transaction.get('transaction_type', 'CARD')})",
        })

        # Event 2: Device Check
        if behavior_res.get("is_new_device"):
            delta = 0.25
            curr_risk = min(curr_risk + delta, 1.0)
            events.append({
                "timestamp": (base_time - timedelta(minutes=4)).isoformat(),
                "event_name": "New Device Detected",
                "risk_delta": round(delta, 4),
                "resulting_risk_score": round(curr_risk, 4),
                "description": f"First time device '{transaction.get('device_id')}' used for account",
            })

        # Event 3: Beneficiary Check
        if behavior_res.get("is_new_beneficiary"):
            delta = 0.20
            curr_risk = min(curr_risk + delta, 1.0)
            events.append({
                "timestamp": (base_time - timedelta(minutes=3)).isoformat(),
                "event_name": "New Beneficiary Target",
                "risk_delta": round(delta, 4),
                "resulting_risk_score": round(curr_risk, 4),
                "description": f"Unverified destination account '{transaction.get('beneficiary_id')}'",
            })

        # Event 4: Amount & Velocity Check
        if behavior_res.get("amount_ratio", 1.0) > 4.0:
            delta = 0.25
            curr_risk = min(curr_risk + delta, 1.0)
            events.append({
                "timestamp": (base_time - timedelta(minutes=2)).isoformat(),
                "event_name": "High Amount Spike",
                "risk_delta": round(delta, 4),
                "resulting_risk_score": round(curr_risk, 4),
                "description": f"Amount is {behavior_res.get('amount_ratio')}x historical average baseline",
            })

        # Event 5: Entity Graph & Fraud Ring Check
        if graph_res.get("ring_detected"):
            delta = 0.25
            curr_risk = min(curr_risk + delta, 1.0)
            events.append({
                "timestamp": (base_time - timedelta(minutes=1)).isoformat(),
                "event_name": "Fraud Ring Network Connection",
                "risk_delta": round(delta, 4),
                "resulting_risk_score": round(curr_risk, 4),
                "description": "Multi-account shared infrastructure cluster detected on graph topology",
            })

        # Final Event: Risk Fusion Evaluation
        events.append({
            "timestamp": base_time.isoformat(),
            "event_name": "Risk Fusion Final Score",
            "risk_delta": round(fused_risk_score - curr_risk, 4),
            "resulting_risk_score": round(fused_risk_score, 4),
            "description": f"Final multi-signal risk rating: {fused_risk_score:.2f}",
        })

        return events
