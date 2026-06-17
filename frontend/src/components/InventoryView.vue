<template>
  <div class="inventory-view">
    
    <!-- Table Header Toolbar -->
    <div class="toolbar">
      <div class="toolbar-title">
        <h2>📦 {{ $t('inventory.title') }}</h2>
      </div>
      
      <div class="toolbar-actions">
        <!-- Client-side quick search filtering -->
        <input 
          v-model="searchQuery" 
          type="text" 
          :placeholder="$t('inventory.searchPlaceholder')" 
          class="search-input"
        />
        
        <button @click="syncData" :disabled="isSyncing" class="sync-btn">
          <span v-if="!isSyncing">🔄 {{ $t('inventory.syncBtn') }}</span>
          <span v-else>⏳...</span>
        </button>
      </div>
    </div>

    <!-- Data Table Container -->
    <div class="table-container">
      <table class="inventory-table">
        <thead>
          <tr>
            <th>{{ $t('inventory.thItem') }}</th>
            <th>{{ $t('inventory.thSku') }}</th>
            <th>{{ $t('inventory.thQty') }}</th>
            <th>{{ $t('inventory.thLocation') }}</th>
            <th>{{ $t('inventory.thStatus') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredInventory.length === 0">
            <td colspan="5" class="empty-row">No matching inventory items found.</td>
          </tr>
          <tr v-for="item in filteredInventory" :key="item.id">
            <td class="font-bold text-hi">{{ item.name }}</td>
            <td class="font-mono text-mid">{{ item.sku }}</td>
            <td class="font-mono text-hi">{{ item.qty }}</td>
            <td class="text-mid">{{ item.location }}</td>
            <td>
              <span :class="['status-badge', `status--${item.status}`]">
                {{ getStatusLabel(item.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, inject } from 'vue'
import { useAppStore } from '@/stores/app.js'
import { useI18n } from 'vue-i18n'

const store = useAppStore()
const { t } = useI18n()
const showToast = inject('toast')

const searchQuery = ref('')
const isSyncing = ref(false)

// Dynamic computing filters table values instantly as user types
const filteredInventory = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return store.inventory

  return store.inventory.filter(item => 
    item.name.toLowerCase().includes(query) || 
    item.sku.toLowerCase().includes(query)
  )
})

async function syncData() {
  isSyncing.value = true
  try {
    await store.fetchInventory()
    showToast('Inventory database synchronized successfully', '✅')
  } catch (err) {
    showToast('Failed to connect to Odoo ERP instance', '⚠️')
  } finally {
    isSyncing.value = false
  }
}

function getStatusLabel(status) {
  if (status === 'in_stock') return t('inventory.statusInStock')
  if (status === 'low_stock') return t('inventory.statusLowStock')
  if (status === 'out_of_stock') return t('inventory.statusOutOfStock')
  return status
}

// Automatically load your stock tables right as the page mounts
onMounted(async () => {
  if (store.inventory.length === 0) {
    await store.fetchInventory()
  }
})
</script>

<style scoped>
.inventory-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-shell);
  padding: 1.5rem;
  overflow: hidden;
}

/* Toolbar Layout */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.toolbar-title h2 {
  font-size: 1.25rem;
  color: var(--text-hi);
  font-weight: 600;
}

.toolbar-actions {
  display: flex;
  gap: 0.75rem;
}

.search-input {
  background: var(--bg-input);
  border: 1px solid var(--border-hi);
  color: var(--text-hi);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  width: 260px;
  outline: none;
  font-family: inherit;
}
.search-input:focus { border-color: var(--amber); }

.sync-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-hi);
  color: var(--text-hi);
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.sync-btn:hover:not(:disabled) {
  background: var(--amber-dim);
  border-color: var(--amber);
  color: var(--amber);
}

/* Table Design styling */
.table-container {
  flex: 1;
  overflow-auto: auto;
  border: 1px solid var(--border-hi);
  border-radius: var(--radius);
  background: var(--bg-panel);
}

.inventory-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left; /* Default LTR alignment */
}

/* Automatic global RTL flipping support layout */
[dir="rtl"] .inventory-table {
  text-align: right;
}

.inventory-table th {
  background: var(--bg-card);
  color: var(--text-mid);
  font-weight: 600;
  padding: 1rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-hi);
  position: sticky;
  top: 0;
  z-index: 1;
}

.inventory-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.925rem;
  vertical-align: middle;
}

.inventory-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.empty-row {
  text-align: center;
  color: var(--text-lo);
  padding: 3rem !important;
  font-style: italic;
}

/* Utilities helpers layout context */
.font-mono { font-family: var(--mono); }
.font-bold { font-weight: 600; }
.text-hi { color: var(--text-hi); }
.text-mid { color: var(--text-mid); }

/* Status Badge Badging */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status--in_stock {
  background: rgba(16, 185, 129, 0.1);
  color: var(--green);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status--low_stock {
  background: rgba(245, 158, 11, 0.1);
  color: var(--amber);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status--out_of_stock {
  background: rgba(239, 68, 68, 0.1);
  color: var(--red);
  border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>