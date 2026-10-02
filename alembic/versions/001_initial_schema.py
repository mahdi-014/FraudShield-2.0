"""Initial schema for FraudShield Milestone 2

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('client_transaction_id', sa.String(length=100), nullable=False),
        sa.Column('service_actor', sa.String(length=100), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('model_score', sa.Float(), nullable=False),
        sa.Column('model_factors', sa.JSON(), nullable=False),
        sa.Column('policy_reasons', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('policy_version', sa.String(length=64), nullable=False),
        sa.Column('schema_version', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_actor', 'idempotency_key', name='uq_service_actor_idempotency_key')
    )
    op.create_index('ix_transactions_client_transaction_id', 'transactions', ['client_transaction_id'])
    op.create_index('ix_transactions_service_actor', 'transactions', ['service_actor'])
    op.create_index('ix_transactions_idempotency_key', 'transactions', ['idempotency_key'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])

    op.create_table(
        'review_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('resolution', sa.String(length=32), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index('ix_review_cases_status', 'review_cases', ['status'])
    op.create_index('ix_review_cases_transaction_id', 'review_cases', ['transaction_id'])

    op.create_table(
        'analyst_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('previous_status', sa.String(length=32), nullable=False),
        sa.Column('resulting_status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['review_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analyst_actions_case_id', 'analyst_actions', ['case_id'])
    op.create_index('ix_analyst_actions_transaction_id', 'analyst_actions', ['transaction_id'])

    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=36), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('actor_role', sa.String(length=32), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.String(length=32), nullable=True),
        sa.Column('resulting_status', sa.String(length=32), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['review_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_transaction_id', 'audit_events', ['transaction_id'])
    op.create_index('ix_audit_events_case_id', 'audit_events', ['case_id'])
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])

def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('analyst_actions')
    op.drop_table('review_cases')
    op.drop_table('transactions')
