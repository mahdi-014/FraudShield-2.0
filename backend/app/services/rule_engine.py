from typing import Dict, List, Any


class RuleEngine:
    """
    Configurable deterministic fraud detection rules engine.
    Stores and evaluates business rules against transaction & entity metadata.
    """

    def __init__(self):
        self.rules = [
            {
                "rule_id": "RULE_001",
                "rule_name": "NEW_DEVICE_HIGH_AMOUNT",
                "severity": "HIGH",
                "points": 0.30,
                "condition": lambda tx, beh, net: beh.get("is_new_device") and tx.get("amount", 0) > 2500.0,
                "description": "Transaction >$2,500 initiated from an unrecognized new device",
            },
            {
                "rule_id": "RULE_002",
                "rule_name": "NEW_BENEFICIARY_UNUSUAL_AMOUNT",
                "severity": "MEDIUM",
                "points": 0.25,
                "condition": lambda tx, beh, net: beh.get("is_new_beneficiary") and beh.get("amount_ratio", 1.0) > 3.0,
                "description": "Funds transfer >3x baseline sent to a newly added beneficiary",
            },
            {
                "rule_id": "RULE_003",
                "rule_name": "HIGH_TRANSACTION_VELOCITY",
                "severity": "HIGH",
                "points": 0.25,
                "condition": lambda tx, beh, net: beh.get("velocity_1h", 1) >= 4,
                "description": "Rapid velocity burst: 4 or more transactions executed within 1 hour",
            },
            {
                "rule_id": "RULE_004",
                "rule_name": "UNUSUAL_LOCATION_ATO_PATTERN",
                "severity": "HIGH",
                "points": 0.30,
                "condition": lambda tx, beh, net: beh.get("is_unusual_location") and tx.get("transaction_type") in ["WIRE", "P2P"],
                "description": "High-risk transfer (WIRE/P2P) originating from abnormal geographic location",
            },
            {
                "rule_id": "RULE_005",
                "rule_name": "MULTIPLE_ACCOUNTS_SHARED_DEVICE",
                "severity": "CRITICAL",
                "points": 0.35,
                "condition": lambda tx, beh, net: net.get("shared_device_count", 1) >= 3,
                "description": "Device is linked to 3 or more distinct user accounts (potential fraud ring node)",
            },
            {
                "rule_id": "RULE_006",
                "rule_name": "SHARED_IP_INFRASTRUCTURE",
                "severity": "MEDIUM",
                "points": 0.20,
                "condition": lambda tx, beh, net: net.get("shared_ip_count", 1) >= 4,
                "description": "IP address hash shared across 4+ accounts",
            },
        ]

    def evaluate_rules(
        self,
        transaction: Dict[str, Any],
        behavior_res: Dict[str, Any],
        network_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        matched_rules = []
        total_points = 0.0

        for rule in self.rules:
            try:
                if rule["condition"](transaction, behavior_res, network_stats):
                    matched_rules.append({
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["rule_name"],
                        "severity": rule["severity"],
                        "points": rule["points"],
                        "description": rule["description"],
                    })
                    total_points += rule["points"]
            except Exception as e:
                pass

        rule_score = min(total_points, 1.0)

        return {
            "rule_score": round(rule_score, 4),
            "matched_rules_count": len(matched_rules),
            "rule_matches": matched_rules,
        }
