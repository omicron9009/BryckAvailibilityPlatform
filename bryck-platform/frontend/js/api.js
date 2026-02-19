/**
 * API Client Module
 * Single place for all HTTP communication with the backend.
 * Throws structured errors; never catches silently.
 */

const BASE_URL = (window.ENV_API_URL || 'http://localhost:8000') + '/api/v1';

class APIError extends Error {
  constructor(status, detail) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== null) opts.body = JSON.stringify(body);

  const resp = await fetch(`${BASE_URL}${path}`, opts);

  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const err = await resp.json();
      detail = err.detail || detail;
    } catch (_) {}
    throw new APIError(resp.status, detail);
  }

  if (resp.status === 204) return null;
  return resp.json();
}

export const API = {
  machines: {
    list: (params = {}) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '') qs.set(k, v);
      });
      const q = qs.toString();
      return request('GET', `/machines${q ? '?' + q : ''}`);
    },
    get:    (id)           => request('GET',    `/machines/${id}`),
    create: (data)         => request('POST',   '/machines', data),
    update: (id, data)     => request('PATCH',  `/machines/${id}`, data),
    delete: (id)           => request('DELETE', `/machines/${id}`),
    healthCheck: (id)      => request('POST',   `/machines/${id}/health-check`),
  },
};

export { APIError };
