import axios from 'axios'

export const api = axios.create({
  // Pointing directly to your local FastAPI server
  baseURL: 'http://localhost:8000',
  timeout: 30_000,        // 30s — LLM calls can be slow
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: Attach JWT Token automatically ──
api.interceptors.request.use(
  config => {
    // We can pull the token directly from localStorage or pinia here if needed,
    // but your app.js Pinia store already injects it globally via defaults!
    return config
  },
  error => Promise.reject(error)
)

// ── Response interceptor: surface backend error messages cleanly ──
api.interceptors.response.use(
  res => res,
  err => {
    // Extracts FastAPI's "detail" array/string or standard error messages
    let msg = err.message ?? 'Unknown error'
    
    if (err.response?.data) {
      const data = err.response.data
      msg = data.detail 
        ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
        : data.message ?? msg
    }
    
    return Promise.reject(new Error(msg))
  }
)