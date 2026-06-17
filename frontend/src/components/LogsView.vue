<template>
  <div class="logs-layout">
    
    <header class="toolbar">
      <div class="toolbar-title">
        <h2>📊 {{ $t('logs.title') }}</h2>
      </div>
      
      <div class="toolbar-actions">
        <input 
          v-model="searchQuery" 
          type="text" 
          :placeholder="$t('logs.search')" 
          class="search-input"
        />
        <button @click="refreshLogs" :disabled="isLoading" class="refresh-btn">
          <span v-if="!isLoading">🔄 {{ $t('logs.refresh') }}</span>
          <span v-else>⏳...</span>
        </button>
      </div>
    </header>

    <div class="table-container">
      <table class="logs-table">
        <thead>
          <tr>
            <th>{{ $t('logs.thTime') }}</th>
            <th>{{ $t('logs.thUser') }}</th>
            <th>{{ $t('logs.thPrompt') }}</th>
            <th>{{ $t('logs.thTool') }}</th>
            <th>{{ $t('logs.thLatency') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredLogs.length === 0">
            <td colspan="5" class="empty-row">{{ $t('logs.empty') }}</td>
          </tr>
          <tr v-for="log in filteredLogs" :key="log.id">
            
            <td class="col-time font-mono text-mid">
              {{ formatDate(log.created_at) }}
            </td>
            
            <td class="col-user">
              <span class="user-id">U-{{ log.user_id || 'Sys' }}</span>
              <br>
              <span class="session-id text-lo">{{ log.session_id }}</span>
            </td>
            
            <td class="col-prompt">
              <div class="prompt-text">{{ log.user_prompt }}</div>
              </td>
            
            <td class="col-tool">
              <span :class="['tool-badge', `tool--${log.tool_used}`]">
                {{ formatTool(log.tool_used) }}
              </span>
            </td>
            
            <td class="col-latency">
              <span :class="['latency-text', getLatencyClass(log.execution_latency_ms)]">
                {{ log.execution_latency_ms }} ms
              </span>
            </td>
            
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useAppStore } from '@/stores/app.js'
import { useI18n } from 'vue-i18n'

const store = useAppStore()
const { t } = useI18n()
const showToast = inject('toast')

const searchQuery = ref('')
const isLoading = ref(false)

// Instant client-side filtering
const filteredLogs = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return store.logs

  return store.logs.filter(log => 
    log.user_prompt.toLowerCase().includes(query) || 
    log.tool_used.toLowerCase().includes(query) ||
    log.session_id.toLowerCase().includes(query)
  )
})

async function refreshLogs() {
  isLoading.value = true
  try {
    await store.fetchLogs()
    showToast('Logs synchronized', '✅')
  } catch (err) {
    showToast('Failed to fetch logs', '❌')
  } finally {
    isLoading.value = false
  }
}

// ── UTILITIES ──
function formatDate(dateString) {
  const d = new Date(dateString)
  return d.toLocaleString(undefined, { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' 
  })
}

function formatTool(tool) {
  if (tool === 'Search_Docs') return t('logs.toolDocs')
  if (tool === 'Query_Odoo') return t('logs.toolOdoo')
  return t('logs.toolNone')
}

// Color code latency: <1s Green, 1s-3s Yellow, >3s Red
function getLatencyClass(ms) {
  if (ms < 1000) return 'text-green'
  if (ms < 3000) return 'text-amber'
  return 'text-red'
}

onMounted(async () => {
  if (!store.logs || store.logs.length === 0) {
    await refreshLogs()
  }
})
</script>

<style scoped>
.logs-layout {
  display: flex; flex-direction: column; height: 100%;
  background-color: var(--bg-shell); padding: 1.5rem; overflow: hidden;
}

/* Toolbar */
.toolbar {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;
}
.toolbar-title h2 { font-size: 1.25rem; color: var(--text-hi); font-weight: 600; }
.toolbar-actions { display: flex; gap: 0.75rem; }

.search-input {
  background: var(--bg-input); border: 1px solid var(--border-hi);
  color: var(--text-hi); padding: 0.5rem 1rem; border-radius: 6px;
  width: 260px; outline: none; font-family: inherit;
}
.search-input:focus { border-color: var(--amber); }

.refresh-btn {
  background: var(--bg-card); border: 1px solid var(--border-hi);
  color: var(--text-hi); padding: 0.5rem 1.25rem; border-radius: 6px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.refresh-btn:hover:not(:disabled) {
  background: var(--amber-dim); border-color: var(--amber); color: var(--amber);
}

/* Table Container */
.table-container {
  flex: 1; overflow-y: auto;
  border: 1px solid var(--border-hi); border-radius: var(--radius);
  background: var(--bg-panel);
}

.logs-table { width: 100%; border-collapse: collapse; text-align: left; }
[dir="rtl"] .logs-table { text-align: right; }

.logs-table th {
  background: var(--bg-card); color: var(--text-mid); font-weight: 600;
  padding: 1rem; font-size: 0.85rem; text-transform: uppercase;
  letter-spacing: 0.5px; border-bottom: 1px solid var(--border-hi);
  position: sticky; top: 0; z-index: 1;
}

.logs-table td {
  padding: 1rem; border-bottom: 1px solid var(--border);
  font-size: 0.9rem; vertical-align: middle;
}
.logs-table tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
.empty-row { text-align: center; color: var(--text-lo); padding: 3rem !important; font-style: italic; }

/* Utilities */
.font-mono { font-family: var(--mono); font-size: 0.85rem; }
.text-hi { color: var(--text-hi); }
.text-mid { color: var(--text-mid); }
.text-lo { color: var(--text-lo); font-size: 0.75rem; }

.text-green { color: var(--green); }
.text-amber { color: var(--amber); }
.text-red { color: var(--red); }
.latency-text { font-weight: 600; font-family: var(--mono); }

.col-prompt { max-width: 300px; }
.prompt-text {
  color: var(--text-hi); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; font-weight: 500;
}

.user-id { font-weight: 600; color: var(--text-hi); }

/* Tool Badges */
.tool-badge {
  display: inline-block; padding: 0.25rem 0.6rem;
  border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
}
.tool--Search_Docs { background: rgba(245, 158, 11, 0.1); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.2); }
.tool--Query_Odoo { background: rgba(59, 130, 246, 0.1); color: var(--blue); border: 1px solid rgba(59, 130, 246, 0.2); }
.tool--None { background: var(--bg-card); color: var(--text-mid); border: 1px solid var(--border-hi); }
</style>