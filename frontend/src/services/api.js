import axios from 'axios'

/**
 * Central Axios instance.
 * VITE_API_URL is set in your .env file:
 *   VITE_API_URL=http://localhost:8000        ← local dev
 *   VITE_API_URL=http://<tailscale-ip>:8000   ← VM via Tailscale
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 30_000,   // 30 s — AI calls can be slow
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor: attach stored JWT if present ─────────────────────
api.interceptors.request.use(config => {
  const token = localStorage.getItem('fc_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor: surface backend error messages cleanly ──────────
api.interceptors.response.use(
  res => res,
  err => {
    const msg =
      err.response?.data?.detail ??
      err.response?.data?.message ??
      err.message ??
      'Unknown error'
    console.error(`[API] ${err.config?.method?.toUpperCase()} ${err.config?.url} → ${msg}`)
    return Promise.reject(new Error(msg))
  }
)