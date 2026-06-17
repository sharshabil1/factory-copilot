<template>
  <div class="document-panel">
    <header class="panel-header">
      <h3>📚 {{ $t('docs.title') }}</h3>
    </header>

    <!-- Drag and Drop Upload Box Container -->
    <div 
      :class="['drop-zone', isDragging && 'drop-zone--active']"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerFileSelect"
    >
      <input 
        type="file" 
        ref="fileInput" 
        accept=".pdf" 
        class="hidden-input" 
        @change="handleFileSelect"
      />
      <div class="drop-zone-content">
        <span class="upload-icon">📤</span>
        <p class="main-text">{{ $t('docs.dragZone') }}</p>
        <span class="sub-text">{{ $t('docs.onlyPdf') }}</span>
      </div>
    </div>

    <!-- Document Log Table Feed -->
    <div class="docs-list">
      <div v-if="store.documents.length === 0" class="empty-state">
        <p>{{ $t('docs.empty') }}</p>
      </div>

      <div 
        v-for="doc in store.documents" 
        :key="doc.id" 
        class="doc-card"
      >
        <div class="doc-info">
          <span class="doc-name" :title="doc.original_name">{{ doc.original_name }}</span>
          <span class="doc-meta">
            {{ doc.size_mb }} MB 
            <template v-if="doc.chunk_count">
              • {{ doc.chunk_count }} {{ $t('docs.chunks') }}
            </template>
          </span>
        </div>

        <div class="doc-status">
          <span :class="['status-badge', `status--${doc.status}`]">
            <template v-if="doc.status === 'processing'">⏳ {{ $t('docs.statusProcessing') }}</template>
            <template v-else-if="doc.status === 'completed'">✅ {{ $t('docs.statusCompleted') }}</template>
            <template v-else>❌ {{ $t('docs.statusFailed') }}</template>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useAppStore } from '@/stores/app.js'

const store = useAppStore()
const showToast = inject('toast')

const isDragging = ref(false)
const fileInput = ref(null)

function triggerFileSelect() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

function handleDrop(event) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

async function processFile(file) {
  // Enforce strict extension guard rules for vector embedding constraints
  if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
    showToast('Invalid format. PDF manuals only.', '⚠️')
    return
  }

  try {
    showToast(`Uploading ${file.name}...`, '📤')
    await store.uploadDocument(file)
    showToast('Document vectorized successfully', '✅')
  } catch (err) {
    showToast(err.message || 'Failed to analyze document', '❌')
  }
}

onMounted(async () => {
  await store.fetchDocuments()
})
</script>

<style scoped>
.document-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel);
  border-left: 1px solid var(--border);
  padding: 1rem;
  overflow: hidden;
}

[dir="rtl"] .document-panel {
  border-left: none;
  border-right: 1px solid var(--border);
}

.panel-header {
  margin-bottom: 1rem;
}

.panel-header h3 {
  font-size: 1rem;
  color: var(--text-hi);
  font-weight: 600;
}

/* Drag Area Shell Style Box */
.drop-zone {
  border: 2px dashed var(--border-hi);
  border-radius: var(--radius);
  padding: 1.5rem 1rem;
  text-align: center;
  background: var(--bg-input);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  margin-bottom: 1.5rem;
}

.drop-zone:hover, .drop-zone--active {
  border-color: var(--amber);
  background: var(--amber-dim);
}

.hidden-input {
  display: none;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.upload-icon {
  font-size: 1.5rem;
}

.main-text {
  font-size: 0.85rem;
  color: var(--text-hi);
  font-weight: 500;
  line-height: 1.4;
}

.sub-text {
  font-size: 0.75rem;
  color: var(--text-lo);
}

/* Scroll list configuration style */
.docs-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-state {
  margin: auto;
  text-align: center;
  color: var(--text-lo);
  font-style: italic;
  font-size: 0.85rem;
  padding: 2rem 0;
}

.doc-card {
  background: var(--bg-card);
  border: 1px solid var(--border-hi);
  border-radius: var(--radius);
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.doc-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.doc-name {
  font-size: 0.85rem;
  color: var(--text-hi);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 0.75rem;
  color: var(--text-mid);
  font-family: var(--mono);
}

/* Badge Layout controls inside list item matrix */
.status-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

.status--processing {
  background: rgba(245, 158, 11, 0.1);
  color: var(--amber);
}

.status--completed {
  background: rgba(16, 185, 129, 0.1);
  color: var(--green);
}

.status--failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--red);
}
</style>