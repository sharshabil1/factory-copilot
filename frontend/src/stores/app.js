import { defineStore } from 'pinia'
import { api }         from '@/services/api.js'


export const useAppStore = defineStore('app', {
  state: () => ({
    // ── auth ──────────────────────────
    token:      null,
    user:       null,
    role:       null,
    activeView: 'workflow',

    // ── navigation ────────────────────
    activeView: 'chat',        // 'chat' | 'inventory' | 'admin'

    // ── chat ──────────────────────────
    messages:   [],
    sessionId:  null,
    isTyping:   false,

    // ── documents ─────────────────────
    documents:  [],

    // ── inventory ─────────────────────
    inventory:  [],

    // ── admin ─────────────────────────
    logs:       [],
    stats:      {
      totalQueries:  0,
      avgLatencyMs:  0,
      ragPct:        0,
      activeUsers:   0,
      dailySeries:   [],    // [{ day, rag, odoo }]
    },
  }),

  getters: {
    isLoggedIn: s => !!s.token,
    isAdmin:    s => s.role === 'admin',
  },

  actions: {


// ── AUTH ────────────────────────────────────────────
    async login(username, password) {
      
      // 🚨 MOCK HACKATHON LOGIN 🚨
      // Simulate a 800ms network delay so the UI loading dots show up
      await new Promise(resolve => setTimeout(resolve, 800))

      // Assign fake data so the app thinks we are logged in
      this.token     = 'fake-jwt-token-for-testing'
      this.user      = username
      this.role      = username.toLowerCase() === 'admin' ? 'admin' : 'operator'
      this.sessionId = 'sess-' + Math.random().toString(36).slice(2, 10)
      
      // (Keep this so your future Axios calls attach the fake token)
      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

      /* // 🔒 UNCOMMENT THIS LATER WHEN FASTAPI IS READY
      const { data } = await api.post('/auth/login', { username, password })
      this.token     = data.access_token
      this.user      = data.username
      this.role      = data.role
      this.sessionId = 'sess-' + Math.random().toString(36).slice(2, 10)
      api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      */
    },

    logout() {
      this.$reset()
      delete api.defaults.headers.common['Authorization']
    },

    // ── CHAT ────────────────────────────────────────────
    async sendMessage(prompt) {
      // 1. Append user message immediately to the UI array
      this.messages.push({
        id:        Date.now(),
        role:      'user',
        text:      prompt,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      })

      this.isTyping = true

      try {
        const started = Date.now()
        let data

        // 💡 HACKATHON TOGGLE: Set to false when your FastAPI backend is running!
        const useMock = true

        if (useMock) {
          // 🚨 MOCK MODE: Simulate a 1.5s network delay
          await new Promise(resolve => setTimeout(resolve, 1500))
          
          data = {
            response: `This is a mock response to: "${prompt}". According to the enterprise safety manual, proper lockdown procedures must be verified via the control panel before maintenance starts.`,
            tool_used: 'Search_Docs',
            sources: [
              { name: 'Safety_Manual_v2.pdf', page: 12 }, 
              { name: 'Odoo_Log_#81', page: null }
            ]
          }
        } else {
          // 🔒 LIVE BACKEND: Hit your real FastAPI server
          const response = await api.post('/chat', {
            prompt,
            session_id: this.sessionId,
          })
          data = response.data
        }

        const latency = Date.now() - started

        // 2. Append AI response to the UI array
        this.messages.push({
          id:        Date.now(),
          role:      'ai',
          text:      data.response,
          tool:      data.tool_used, // 'Search_Docs' | 'Query_Odoo'
          sources:   data.sources ?? [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        })

        // 3. Live-append to admin log history panel tracking latency
        this.logs.unshift({
          time:    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          user:    this.user,
          prompt,
          tool:    data.tool_used,
          latency,
        })

      } catch (err) {
        console.error("Failed to process message:", err)
        throw err
      } finally {
        this.isTyping = false
      }
    },


    clearChat() {
      this.messages  = []
      this.sessionId = 'sess-' + Math.random().toString(36).slice(2, 10)
    },

    // ── DOCUMENTS ───────────────────────────────────────
// ── DOCUMENTS ───────────────────────────────────────
    async fetchDocuments() {
      // 💡 HACKATHON TOGGLE: Set to false when your FastAPI backend is running!
      const useMock = true

      try {
        if (useMock) {
          if (this.documents.length === 0) {
            this.documents = [
              { id: 101, original_name: 'CNC_Safety_Protocols_2026.pdf', size_mb: '2.4', status: 'completed', chunk_count: 42 },
              { id: 102, original_name: 'Odoo_Inventory_UserGuide.pdf', size_mb: '5.1', status: 'completed', chunk_count: 118 }
            ]
          }
        } else {
          const { data } = await api.get('/documents')
          this.documents = data
        }
      } catch (err) {
        console.error("Failed to fetch docs:", err)
        throw err
      }
    },

    async uploadDocument(file) {
      // 💡 HACKATHON TOGGLE: Set to false when your FastAPI backend is running!
      const useMock = true

      // Optimistic state update: show processing row immediately
      const tempId = 'temp-' + Date.now()
      const tempRecord = {
        id:            tempId,
        original_name: file.name,
        size_mb:       (file.size / 1024 / 1024).toFixed(1),
        status:        'processing',
        chunk_count:   null,
      }
      this.documents.unshift(tempRecord)

      try {
        if (useMock) {
          // Simulate 2.5s chunking processing network lag
          await new Promise(resolve => setTimeout(resolve, 2500))
          
          const idx = this.documents.findIndex(d => d.id === tempId)
          if (idx !== -1) {
            this.documents[idx] = {
              id:            Date.now(),
              original_name: file.name,
              size_mb:       (file.size / 1024 / 1024).toFixed(1),
              status:        'completed',
              chunk_count:   Math.floor(Math.random() * 50) + 10 // Mock generated chunks count
            }
          }
        } else {
          const form = new FormData()
          form.append('file', file)

          const { data } = await api.post('/documents/upload', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
          
          const idx = this.documents.findIndex(d => d.id === tempId)
          if (idx !== -1) this.documents[idx] = data
        }
      } catch (err) {
        const idx = this.documents.findIndex(d => d.id === tempId)
        if (idx !== -1) this.documents[idx].status = 'failed'
        throw err
      }
    },

    // ── INVENTORY ───────────────────────────────────────
// ── INVENTORY ───────────────────────────────────────
    async fetchInventory() {
      // 💡 HACKATHON TOGGLE: Set to false when your FastAPI backend is running!
      const useMock = true

      try {
        if (useMock) {
          // Simulate 600ms Odoo API response network lag
          await new Promise(resolve => setTimeout(resolve, 600))
          
          this.inventory = [
            { id: 1, name: 'Ball Bearing 6204-2RSH', sku: 'BRG-6204', qty: 142, location: 'Aisle B-4', status: 'in_stock' },
            { id: 2, name: 'HMI Touch Panel 10-inch', sku: 'HMI-TP10', qty: 3, location: 'Cabinet C-2', status: 'low_stock' },
            { id: 3, name: 'Proximity Sensor M18 NPN', sku: 'SEN-M18', qty: 45, location: 'Aisle A-1', status: 'in_stock' },
            { id: 4, name: 'Servo Motor 1.5kW', sku: 'MOT-SV15', qty: 0, location: 'Warehouse 2', status: 'out_of_stock' },
            { id: 5, name: 'Hydraulic Seal Kit 40mm', sku: 'HYD-SL40', qty: 12, location: 'Aisle D-3', status: 'low_stock' },
            { id: 6, name: 'Pneumatic Valve 5/2 Way', sku: 'PNE-V52', qty: 88, location: 'Aisle A-4', status: 'in_stock' }
          ]
        } else {
          const { data } = await api.get('/inventory')
          this.inventory = data
        }
      } catch (err) {
        console.error("Failed to fetch inventory:", err)
        throw err
      }
    },

    // ── ADMIN ───────────────────────────────────────────
    async fetchStats() {
      const { data } = await api.get('/admin/stats')
      this.stats     = data
    },

    async fetchLogs() {
      const { data } = await api.get('/admin/logs')
      this.logs      = data
    },
  },
})