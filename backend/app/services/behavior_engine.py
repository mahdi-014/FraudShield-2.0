import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timezone


class BehaviorEngine:
    """
    Evaluates user transaction behavior against historical baseline profiles.
    Returns quantitative behavioral deviation scores and anomalous indicators.
    """

    def analyze_behavior(
        self,
        transaction: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        account_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        amount = float(transaction.get("amount", 0.0))
        device_id = transaction.get("device_id")
        beneficiary_id = transaction.get("beneficiary_id")
        location = transaction.get("location")
        
        ts_raw = transaction.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                tx_time = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                tx_time = datetime.now(timezone.utc)
        else:
            tx_time = datetime.now(timezone.utc)

        tx_hour = tx_time.hour

        if not user_history:
            # Cold start user — baseline initial assessment
            return {
                "behavior_score": 0.35 if amount > 1000.0 else 0.15,
                "amount_deviation": 0.0,
                "is_new_device": True,
                "is_new_beneficiary": True,
                "is_unusual_hour": False,
                "is_unusual_location": False,
                "velocity_1h": 1,
                "velocity_24h": 1,
                "behavior_summary": "First recorded transaction for user baseline.",
            }

        # Calculate historical stats
        historical_amounts = [float(h.get("amount", 0.0)) for h in user_history]
        mean_amount = float(np.mean(historical_amounts))
        std_amount = float(np.std(historical_amounts)) if len(historical_amounts) > 1 else max(mean_amount * 0.3, 10.0)

        amount_z_score = (amount - mean_amount) / (std_amount + 1e-5)
        amount_ratio = amount / (mean_amount + 1e-5)

        # Device & Beneficiary check
        seen_devices = {h.get("device_id") for h in user_history if h.get("device_id")}
        seen_beneficiaries = {h.get("beneficiary_id") for h in user_history if h.get("beneficiary_id")}
        seen_locations = {h.get("location") for h in user_history if h.get("location")}
        seen_hours = {datetime.fromisoformat(h.get("timestamp").replace("Z", "+00:00")).hour for h in user_history if h.get("timestamp")}

        is_new_device = device_id not in seen_devices if device_id else False
        is_new_beneficiary = beneficiary_id not in seen_beneficiaries if beneficiary_id else False
        is_unusual_location = location not in seen_locations if location and seen_locations else False
        is_unusual_hour = (tx_hour not in seen_hours) and (tx_hour in [1, 2, 3, 4]) # Late night / unusual window

        # Velocity check (1h and 24h)
        t_1h_ago = tx_time.timestamp() - 3600
        t_24h_ago = tx_time.timestamp() - 86400

        vel_1h = 1
        vel_24h = 1
        for h in user_history:
            h_ts = h.get("timestamp")
            if h_ts:
                try:
                    dt = datetime.fromisoformat(h_ts.replace("Z", "+00:00")).timestamp()
                    if dt >= t_1h_ago:
                        vel_1h += 1
                    if dt >= t_24h_ago:
                        vel_24h += 1
                except Exception:
                    pass

        # Compute composite behavior score (0.0 to 1.0)
        behavior_points = 0.0
        reasons = []

        if amount_ratio > 10.0:
            behavior_points += 0.35
            reasons.append(f"Amount (${amount:.2f}) is >10x baseline average (${mean_amount:.2f})")
        elif amount_ratio > 4.0:
            behavior_points += 0.20
            reasons.append(f"Amount (${amount:.2f}) is >4x baseline average (${mean_amount:.2f})")

        if is_new_device:
            behavior_points += 0.20
            reasons.append("Initiated from a new device")

        if is_new_beneficiary:
            behavior_points += 0.15
            reasons.append("Transfer recipient is a new beneficiary")

        if is_unusual_hour:
            behavior_points += 0.10
            reasons.append(f"Transaction time ({tx_hour:02d}:00) outside normal activity hours")

        if is_unusual_location:
            behavior_points += 0.10
            reasons.append(f"Location '{location}' differs from historical locations")

        if vel_1h > 3:
            behavior_points += 0.15
            reasons.append(f"High transaction velocity ({vel_1h} transactions in past hour)")

        behavior_score = float(np.clip(behavior_points, 0.0, 1.0))
        summary = "; ".join(reasons) if reasons else "Behavior consistent with normal historical baseline."

        return {
            "behavior_score": round(behavior_score, 4),
            "amount_deviation": round(float(amount_z_score), 2),
            "amount_ratio": round(float(amount_ratio), 2),
            "historical_mean_amount": round(mean_amount, 2),
            "is_new_device": is_new_device,
            "is_new_beneficiary": is_new_beneficiary,
            "is_unusual_hour": is_unusual_hour,
            "is_unusual_location": is_unusual_location,
            "velocity_1h": vel_1h,
            "velocity_24h": vel_24h,
            "behavior_summary": summary,
        }
