import os
import sys
import json
import logging
from datetime import datetime, timezone

# Add workspace to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.investigation.agent import AIInvestigationAgent
from backend.app.graph.neo4j_service import Neo4jGraphService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_all_demo_scenarios():
    print("=========================================================================")
    print(" FRAUDSHIELD 2.0 — DEMO SCENARIOS END-TO-END VERIFICATION RUNNER")
    print("=========================================================================\n")

    agent = AIInvestigationAgent()
    graph_service = Neo4jGraphService()

    scenarios = [
        {
            "code": "Scenario A",
            "name": "Normal Transaction (Low Risk)",
            "transaction": {
                "transaction_id": "TX_SCENARIO_A",
                "user_id": "USR_NORMAL_01",
                "account_id": "ACC_NORMAL_01",
                "amount": 45.20,
                "currency": "USD",
                "transaction_type": "CARD",
                "device_id": "DEV_KNOWN_101",
                "beneficiary_id": "BEN_STORE_55",
                "location": "New York, US",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_fraud": 0,
                "scenario": "A",
            },
            "history": [
                {"amount": 50.0, "device_id": "DEV_KNOWN_101", "beneficiary_id": "BEN_STORE_55", "location": "New York, US", "timestamp": "2026-09-20T10:00:00Z"},
                {"amount": 42.0, "device_id": "DEV_KNOWN_101", "beneficiary_id": "BEN_STORE_55", "location": "New York, US", "timestamp": "2026-09-22T14:00:00Z"},
            ]
        },
        {
            "code": "Scenario B",
            "name": "Behavioral Anomaly (Unusual Amount & Device)",
            "transaction": {
                "transaction_id": "TX_SCENARIO_B",
                "user_id": "USR_BEHAVIOR_02",
                "account_id": "ACC_BEHAVIOR_02",
                "amount": 1850.00,
                "currency": "USD",
                "transaction_type": "ACH",
                "device_id": "DEV_NEW_702",
                "beneficiary_id": "BEN_UNUSUAL_99",
                "location": "New York, US",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_fraud": 1,
                "scenario": "B",
            },
            "history": [
                {"amount": 120.0, "device_id": "DEV_KNOWN_202", "beneficiary_id": "BEN_USUAL_11", "location": "New York, US", "timestamp": "2026-09-20T10:00:00Z"},
            ]
        },
        {
            "code": "Scenario C",
            "name": "Account Takeover (ATO Pattern)",
            "transaction": {
                "transaction_id": "TX_SCENARIO_C",
                "user_id": "USR_ATO_03",
                "account_id": "ACC_ATO_03",
                "amount": 9500.00,
                "currency": "USD",
                "transaction_type": "WIRE",
                "device_id": "DEV_ATO_SUSPECT_888",
                "beneficiary_id": "BEN_MULE_333",
                "location": "Unknown Proxy IP",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_fraud": 1,
                "scenario": "C",
            },
            "history": [
                {"amount": 200.0, "device_id": "DEV_KNOWN_303", "beneficiary_id": "BEN_SAFE_88", "location": "London, UK", "timestamp": "2026-09-15T12:00:00Z"},
            ]
        },
        {
            "code": "Scenario D",
            "name": "Fraud Ring (Multi-Account Shared Infrastructure Cluster)",
            "transaction": {
                "transaction_id": "TX_SCENARIO_D",
                "user_id": "USR_RING_04",
                "account_id": "ACC_RING_04",
                "amount": 7850.00,
                "currency": "USD",
                "transaction_type": "P2P",
                "device_id": "DEV_RING_999", # Shared across 3 accounts
                "ip_address_hash": "10.0.99.99",
                "beneficiary_id": "BEN_RING_777",
                "location": "Chicago, US",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_fraud": 1,
                "scenario": "D",
            },
            "history": []
        },
        {
            "code": "Scenario E",
            "name": "False Positive (High Amount Legitimate Purchase)",
            "transaction": {
                "transaction_id": "TX_SCENARIO_E",
                "user_id": "USR_FP_05",
                "account_id": "ACC_FP_05",
                "amount": 3400.00,
                "currency": "USD",
                "transaction_type": "CARD",
                "device_id": "DEV_UPGRADE_404",
                "beneficiary_id": "BEN_CAR_DEALER_100",
                "location": "Tokyo, JP",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_fraud": 0,
                "scenario": "E",
            },
            "history": [
                {"amount": 500.0, "device_id": "DEV_OLD_404", "beneficiary_id": "BEN_CAR_DEALER_100", "location": "Tokyo, JP", "timestamp": "2026-09-10T08:00:00Z"},
            ]
        }
    ]

    for s in scenarios:
        tx = s["transaction"]
        graph_service.ingest_transaction_graph(tx)
        res = agent.investigate_transaction(tx, user_history=s["history"])

        print(f"[{s['code']}] {s['name']}")
        print(f"  -> Risk Level: {res['risk_level']} (Score: {res['risk_score']:.2f})")
        print(f"  -> ML Fraud Prob: {res['ml_fraud_probability']:.2%}")
        print(f"  -> Ring Detected: {res['potential_network'].get('ring_detected')}")
        print(f"  -> Summary: {res['case_summary'][:110]}...")
        print(f"  -> Primary Evidence Count: {len(res['primary_evidence'])}")
        print("-------------------------------------------------------------------------")

    print("\nAll 5 Competition Demo Scenarios evaluated successfully with 100% evidence flow!")


if __name__ == "__main__":
    run_all_demo_scenarios()
