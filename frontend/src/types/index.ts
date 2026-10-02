export interface Actor {
  identity: string;
  role: 'service' | 'analyst' | 'legacy_scorer' | string;
}

export interface ModelFactor {
  feature: string;
  contribution_log_odds: number;
  direction: 'increases_score' | 'decreases_score';
  value: string | number | null;
}

export interface Transaction {
  id: string;
  client_transaction_id: string;
  service_actor: string;
  idempotency_key: string;
  request_hash: string;
  features?: Record<string, unknown>;
  model_score: number;
  model_factors: ModelFactor[];
  policy_reasons: string[];
  recommended_action: 'hold' | 'pause' | 'warn' | 'allow' | string;
  status: 'held_for_review' | 'pending_verification' | 'completed' | 'rejected' | 'awaiting_acknowledgement' | string;
  model_version: string;
  policy_version: string;
  schema_version: string;
  version: number;
  case_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewCase {
  id: string;
  transaction_id: string;
  status: 'open' | 'resolved' | string;
  resolution?: 'released' | 'rejected' | null;
  resolution_reason?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
  transaction?: Transaction | null;
}

export interface CasesResponse {
  items: ReviewCase[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditEvent {
  id: string;
  transaction_id: string;
  case_id?: string | null;
  event_type: string;
  actor: string;
  actor_role: string;
  action: string;
  reason?: string | null;
  previous_status?: string | null;
  resulting_status: string;
  payload?: Record<string, unknown>;
  created_at: string;
}

export interface AuditResponse {
  transaction_id: string;
  audit_events: AuditEvent[];
}

export interface HealthResponse {
  status: string;
  mode: string;
  database: 'connected' | 'disconnected' | 'unconfigured' | string;
}

export interface ActionRequest {
  action: 'release' | 'reject';
  reason: string;
  expected_version: number;
}

export interface ActionResponse {
  case: ReviewCase;
  transaction: Transaction;
  message: string;
}
