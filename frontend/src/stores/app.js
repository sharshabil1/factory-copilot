import { defineStore } from 'pinia'
import { api }         from '@/services/api.js'

export const useAppStore = defineStore('app', {
  state: () => ({
    // ── auth ──────────────────────────
    token:      null,
    user:       null,
    userId:     null,
    role:       null,

    // ── navigation ────────────────────
    activeView: 'chat',   // 'chat' | 'documents' | 'admin'

    // ── chat ──────────────────────────
    messages:   [],
    sessionId:  null,
    isTyping:   false,

    // ── documents ─────────────────────
    documents:  [],

    // ── inventory (kept for the UI tab) ──
    inventory:  [],

    // ── admin ─────────────────────────
    logs:  [],
    stats: {
      totalQueries: 0,
      avgLatencyMs: 0,
      ragPct:       0,
      activeUsers:  0,
      dailySeries:  [],
    },
  }),

  getters: {
    isLoggedIn: s => !!s.token,
    isAdmin:    s => s.role === 'admin',
  },

  actions: {

    // ── AUTH ──────────────────────────────────────────────────────────────────
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password })

      this.token     = data.access_token
      this.user      = data.username
      this.userId    = data.user_id
      this.role      = data.role
      this.sessionId = 'sess-' + Math.random().toString(36).slice(2, 10)

      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
    },

    logout() {
      this.$reset()
      delete api.defaults.headers.common['Authorization']
    },

    // ── CHAT ──────────────────────────────────────────────────────────────────
    async sendMessage(prompt) {
      // 1. Push user bubble immediately
      this.messages.push({
        id:        Date.now(),
        role:      'user',
        text:      prompt,
        timestamp: _now(),
      })

      this.isTyping = true

      try {
        const started = Date.now()

        // Build conversation history for the backend (last 10 turns max)
        const history = this.messages
          .slice(-11, -1)          // exclude the message we just pushed
          .map(m => ({
            role:    m.role === 'ai' ? 'assistant' : 'user',
            content: m.text,
          }))

        const { data } = await api.post('/chat', {
          message:    prompt,
          history,
          user_id:    this.userId ?? null,
        })

        const latency = Date.now() - started

        // 2. Push AI bubble
        // Backend returns: { answer, sources[], tool_used, sql? }
        this.messages.push({
          id:        Date.now(),
          role:      'ai',
          text:      data.answer,
          tool:      data.tool_used,
          sources:   data.sources  ?? [],
          sql:       data.sql      ?? null,
          timestamp: _now(),
        })

        // 3. Live-append to admin log panel
        this.logs.unshift({
          time:    _now(),
          user:    this.user,
          prompt,
          tool:    data.tool_used,
          latency,
        })

      } catch (err) {
        // Show a friendly error bubble instead of crashing
        this.messages.push({
          id:        Date.now(),
          role:      'ai',
          text:      '⚠️ Something went wrong. Please try again.',
          tool:      'error',
          sources:   [],
          timestamp: _now(),
        })
        console.error('sendMessage error:', err)
      } finally {
        this.isTyping = false
      }
    },

    clearChat() {
      this.messages  = []
      this.sessionId = 'sess-' + Math.random().toString(36).slice(2, 10)
    },

    // ── DOCUMENTS ─────────────────────────────────────────────────────────────
    async fetchDocuments() {
      const { data } = await api.get('/documents')
      this.documents = data
    },

    async uploadDocument(file) {
      // Optimistic row while uploading
      const tempId     = 'temp-' + Date.now()
      const tempRecord = {
        id:            tempId,
        original_name: file.name,
        size_mb:       (file.size / 1024 / 1024).toFixed(1),
        status:        'processing',
        chunk_count:   null,
      }
      this.documents.unshift(tempRecord)

      try {
        const form = new FormData()
        form.append('file', file)

        const { data } = await api.post('/documents/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        // Replace the temp row with the real one from the server
        const idx = this.documents.findIndex(d => d.id === tempId)
        if (idx !== -1) this.documents[idx] = data

      } catch (err) {
        const idx = this.documents.findIndex(d => d.id === tempId)
        if (idx !== -1) this.documents[idx].status = 'failed'
        throw err
      }
    },

    // ── INVENTORY ─────────────────────────────────────────────────────────────
    async fetchInventory() {
      // Inventory data comes from the DB via the AI agent (Query_DB).
      // This endpoint returns raw rows from odoo_department_metrics
      // so the Inventory tab can show a table without needing the chat.
      const { data } = await api.get('/inventory')
      this.inventory = data
    },

    // ── ADMIN ─────────────────────────────────────────────────────────────────
    async fetchLogs() {
      const { data } = await api.get('/admin/logs')
      this.logs = data
    },

    async fetchStats() {
      const { data } = await api.get('/admin/stats')
      this.stats = data
    },
  },
})

// ── Helpers ──────────────────────────────────────────────────────────────────
function _now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}