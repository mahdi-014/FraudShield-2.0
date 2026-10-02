import type {
  Actor,
  ReviewCase,
  CasesResponse,
  AuditResponse,
  HealthResponse,
  ActionRequest,
  ActionResponse,
} from '../types';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  url: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');

  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new ApiError(0, 'Unable to connect to FraudShield backend. Ensure the server is online.');
  }

  let data: unknown;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    let message = 'An unexpected server error occurred';
    if (data && typeof data === 'object' && 'detail' in data) {
      const d = (data as { detail: unknown }).detail;
      message = typeof d === 'string' ? d : JSON.stringify(d);
    } else if (response.status === 401) {
      message = 'Invalid or expired credentials. Please sign in with a valid analyst token.';
    } else if (response.status === 403) {
      message = 'Forbidden: this token role lacks permissions for analyst operations.';
    } else if (response.status === 404) {
      message = 'Resource not found.';
    } else if (response.status === 409) {
      message = 'Conflict detected: record version or state conflict.';
    } else if (response.status === 503) {
      message = 'Database or backend service is temporarily unavailable.';
    }
    if (token && (response.status === 401 || response.status === 403)) {
      window.dispatchEvent(new CustomEvent('fraudshield-auth-error', {
        detail: { token, message },
      }));
    }
    throw new ApiError(response.status, message);
  }

  return data as T;
}

export const api = {
  async checkHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health/ready');
  },

  async getMe(token: string): Promise<Actor> {
    return request<Actor>('/v1/auth/me', { method: 'GET' }, token);
  },

  async getCases(
    token: string,
    params: {
      status?: string;
      resolution?: string;
      recommended_action?: string;
      limit?: number;
      offset?: number;
    } = {},
    signal?: AbortSignal
  ): Promise<CasesResponse> {
    const search = new URLSearchParams();
    if (params.status && params.status !== 'all') {
      search.set('status', params.status);
    }
    if (params.resolution && params.resolution !== 'all') {
      search.set('resolution', params.resolution);
    }
    if (params.recommended_action && params.recommended_action !== 'all') {
      search.set('recommended_action', params.recommended_action);
    }
    if (params.limit !== undefined) {
      search.set('limit', String(params.limit));
    }
    if (params.offset !== undefined) {
      search.set('offset', String(params.offset));
    }

    const query = search.toString();
    const url = `/v1/cases${query ? `?${query}` : ''}`;
    return request<CasesResponse>(url, { method: 'GET', signal }, token);
  },

  async getCase(token: string, caseId: string, signal?: AbortSignal): Promise<ReviewCase> {
    return request<ReviewCase>(`/v1/cases/${encodeURIComponent(caseId)}`, { method: 'GET', signal }, token);
  },

  async executeAction(
    token: string,
    caseId: string,
    payload: ActionRequest
  ): Promise<ActionResponse> {
    return request<ActionResponse>(
      `/v1/cases/${encodeURIComponent(caseId)}/actions`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      token
    );
  },

  async getTransactionAudit(token: string, transactionId: string, signal?: AbortSignal): Promise<AuditResponse> {
    return request<AuditResponse>(
      `/v1/transactions/${encodeURIComponent(transactionId)}/audit`,
      { method: 'GET', signal },
      token
    );
  },
};

/**
 * Format a UTC ISO timestamp into Asia/Dhaka time zone.
 * Displays date, time, and timezone identifier.
 */
export function formatDhakaTime(isoString?: string | null): string {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;

    const formatter = new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Dhaka',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

    return `${formatter.format(date)} (Asia/Dhaka)`;
  } catch {
    return isoString;
  }
}
