import logging
from sqlalchemy.orm import Session
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.entities import User, ModelVersion, ModelMetric
from backend.app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session = None):
    Base.metadata.create_all(bind=engine)

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Seed default admin / analyst user
        default_user = db.query(User).filter(User.username == "analyst1").first()
        if not default_user:
            analyst = User(
                username="analyst1",
                email="analyst1@fraudshield.ai",
                password_hash=get_password_hash("FraudShield2026!"),
                role="ANALYST",
                is_active=True,
            )
            db.add(analyst)

            admin = User(
                username="admin",
                email="admin@fraudshield.ai",
                password_hash=get_password_hash("FraudShieldAdmin2026!"),
                role="ADMIN",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Created default system users (analyst1, admin)")

        # Seed default model registry entry
        existing_model = db.query(ModelVersion).filter(ModelVersion.version == "xgb-v1.0").first()
        if not existing_model:
            model_v1 = ModelVersion(
                model_name="Supervised XGBoost Fraud Classifier",
                version="xgb-v1.0",
                algorithm="XGBoost Classifier",
                training_dataset="Synthetic Financial Transactions 2.0 (100k samples)",
                features_used=[
                    "amount", "amount_log", "transaction_hour", "transaction_day",
                    "amount_deviation", "frequency_deviation", "device_novelty",
                    "beneficiary_novelty", "transaction_velocity", "shared_device_count"
                ],
                threshold=0.75,
                status="ACTIVE",
                created_by="system_ml_pipeline",
            )
            db.add(model_v1)
            db.flush()

            # Seed model baseline metrics
            metrics = [
                ModelMetric(model_version_id=model_v1.id, metric_name="PRECISION", metric_value=0.942),
                ModelMetric(model_version_id=model_v1.id, metric_name="RECALL", metric_value=0.915),
                ModelMetric(model_version_id=model_v1.id, metric_name="F1", metric_value=0.928),
                ModelMetric(model_version_id=model_v1.id, metric_name="PR_AUC", metric_value=0.961),
                ModelMetric(model_version_id=model_v1.id, metric_name="FPR", metric_value=0.012),
                ModelMetric(model_version_id=model_v1.id, metric_name="LATENCY_MS", metric_value=14.5),
            ]
            db.add_all(metrics)
            db.commit()
            logger.info("Seeded default active model version (xgb-v1.0)")

    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
