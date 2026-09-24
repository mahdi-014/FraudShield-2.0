import unittest
from backend.app.services.behavior_engine import BehaviorEngine
from backend.app.services.risk_fusion import RiskFusionEngine
from backend.app.services.rule_engine import RuleEngine
from backend.app.graph.neo4j_service import Neo4jGraphService
from backend.app.temporal.timeline_engine import TemporalRiskEngine
from backend.app.investigation.agent import AIInvestigationAgent


class TestFraudShieldPipeline(unittest.TestCase):

    def setUp(self):
        self.behavior_engine = BehaviorEngine()
        self.risk_fusion = RiskFusionEngine()
        self.rule_engine = RuleEngine()
        self.graph_service = Neo4jGraphService()
        self.temporal_engine = TemporalRiskEngine()
        self.investigation_agent = AIInvestigationAgent()

    def test_behavior_engine_deviation(self):
        tx = {"amount": 5000.0, "device_id": "DEV_NEW_1", "beneficiary_id": "BEN_NEW_1"}
        history = [{"amount": 100.0, "device_id": "DEV_OLD", "beneficiary_id": "BEN_OLD"}]
        res = self.behavior_engine.analyze_behavior(tx, history, {})
        self.assertTrue(res["is_new_device"])
        self.assertTrue(res["is_new_beneficiary"])
        self.assertGreater(res["amount_ratio"], 4.0)
        self.assertGreater(res["behavior_score"], 0.5)

    def test_rule_engine_triggers(self):
        tx = {"amount": 3000.0, "transaction_type": "WIRE"}
        behavior_res = {"is_new_device": True, "is_new_beneficiary": True, "amount_ratio": 5.0}
        net_stats = {"shared_device_count": 3, "shared_ip_count": 1}

        rule_res = self.rule_engine.evaluate_rules(tx, behavior_res, net_stats)
        self.assertGreaterEqual(rule_res["matched_rules_count"], 2)
        self.assertGreater(rule_res["rule_score"], 0.4)

    def test_risk_fusion_scoring(self):
        fusion = self.risk_fusion.fuse_risk_scores(
            ml_fraud_prob=0.90,
            anomaly_score=0.85,
            behavior_score=0.75,
            rule_score=0.60,
            graph_score=0.90
        )
        self.assertEqual(fusion["risk_level"], "CRITICAL")
        self.assertGreaterEqual(fusion["fused_risk_score"], 0.80)

    def test_fraud_ring_detection(self):
        ring_res = self.graph_service.detect_fraud_ring(
            account_id="ACC_RING_01",
            shared_device_count=3,
            shared_ip_count=4
        )
        self.assertTrue(ring_res["ring_detected"])
        self.assertGreater(ring_res["ring_risk"], 0.70)

    def test_ai_investigation_agent_end_to_end(self):
        tx = {
            "transaction_id": "TX_TEST_99",
            "user_id": "USR_TEST",
            "account_id": "ACC_TEST",
            "amount": 8900.0,
            "currency": "USD",
            "transaction_type": "WIRE",
            "device_id": "DEV_RING_999",
            "beneficiary_id": "BEN_RING_777",
            "is_fraud": 1,
            "scenario": "D"
        }
        res = self.investigation_agent.investigate_transaction(tx)
        self.assertIn("case_summary", res)
        self.assertIn("primary_evidence", res)
        self.assertIn("risk_timeline", res)
        self.assertIn("shap_explanation", res)
        self.assertIn("recommended_next_steps", res)
        self.assertEqual(res["confidence"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
