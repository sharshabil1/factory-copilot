<template>
  <div class="chat-panel">
    
    <header class="chat-header">
      <div class="header-title">
        <span class="icon">💬</span>
        <h2>{{ $t('nav.chat') }}</h2>
      </div>
      <button v-if="store.messages.length > 0" @click="store.clearChat" class="clear-btn">
        🗑️ {{ $t('chat.clear') }}
      </button>
    </header>

    <div class="messages-container" ref="messagesContainer">
      
      <div v-if="store.messages.length === 0" class="empty-state">
        <p>🤖 {{ $t('chat.placeholder') }}</p>
      </div>

      <div
        v-for="msg in store.messages"
        :key="msg.id"
        :class="['message-wrapper', msg.role === 'user' ? 'is-user' : 'is-ai']"
      >
        <div class="message-bubble">
          
          <div class="message-header">
            <strong>{{ msg.role === 'user' ? store.user : 'Factory Copilot' }}</strong>
            <span class="message-time">{{ msg.timestamp }}</span>
          </div>
          
          <p class="message-text">{{ msg.text }}</p>

          <div v-if="msg.sources && msg.sources.length > 0" class="sources-list">
            <span class="sources-label">{{ $t('chat.sources') }}:</span>
            <button
              v-for="(src, idx) in msg.sources"
              :key="idx"
              class="source-chip"
              @click="openSource(src)"
            >
              📄 {{ typeof src === 'string' ? src : src.name }}
              <span v-if="src.page"> (p.{{ src.page }})</span>
            </button>
          </div>

          <div v-if="msg.tool" class="tool-badge">
            ⚙️ {{ msg.tool }}
          </div>

        </div>
      </div>

      <div v-if="store.isTyping" class="message-wrapper is-ai">
        <div class="message-bubble typing-bubble">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>

    </div>

    <div class="input-area">
      <input
        v-model="prompt"
        @keydown.enter="send"
        type="text"
        :placeholder="$t('chat.placeholder')"
        :disabled="store.isTyping"
        ref="inputField"
      />
      <button @click="send" :disabled="!prompt.trim() || store.isTyping" class="send-btn">
        {{ $t('chat.send') }}
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, watch, nextTick, inject } from 'vue'
import { useAppStore } from '@/stores/app.js'
import { useI18n } from 'vue-i18n'

const store = useAppStore()
const { t } = useI18n()
const showToast = inject('toast') // Grabbing the toast system from App.vue

const prompt = ref('')
const messagesContainer = ref(null)
const inputField = ref(null)

async function send() {
  if (!prompt.value.trim() || store.isTyping) return
  
  const text = prompt.value
  prompt.value = '' // Clear UI immediately

  try {
    await store.sendMessage(text)
  } catch (err) {
    showToast(err.message || 'Error connecting to AI', '⚠️')
  } finally {
    // Refocus the input field for rapid typing
    nextTick(() => inputField.value?.focus())
  }
}

function openSource(src) {
  const docName = typeof src === 'string' ? src : src.name
  showToast(`${t('chat.preview')}: ${docName}`, '📄')
  // Later: This can trigger store.activeView = 'documents' and open the specific PDF
}

// Auto-scroll to bottom whenever messages array changes or typing state changes
watch([() => store.messages.length, () => store.isTyping], async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-panel);
}

/* Header */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-shell);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-title h2 {
  font-size: 1.1rem;
  color: var(--text-hi);
  font-weight: 600;
}

.clear-btn {
  background: transparent;
  border: 1px solid var(--border-hi);
  color: var(--text-mid);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}
.clear-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--red);
  border-color: rgba(239, 68, 68, 0.3);
}

/* Messages Area */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.empty-state {
  margin: auto;
  color: var(--text-mid);
  font-size: 1.1rem;
  opacity: 0.6;
}

.message-wrapper {
  display: flex;
  width: 100%;
}

/* Flexbox automatically handles RTL/LTR side placement */
.is-user { justify-content: flex-end; }
.is-ai   { justify-content: flex-start; }

.message-bubble {
  max-width: 85%;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.is-user .message-bubble {
  background-color: var(--amber-dim);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-bottom-right-radius: 2px;
}
[dir="rtl"] .is-user .message-bubble {
  border-bottom-right-radius: 12px;
  border-bottom-left-radius: 2px;
}

.is-ai .message-bubble {
  background-color: var(--bg-card);
  border: 1px solid var(--border-hi);
  border-bottom-left-radius: 2px;
}
[dir="rtl"] .is-ai .message-bubble {
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 2px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  font-size: 0.85rem;
}

.is-user .message-header strong { color: var(--amber); }
.is-ai .message-header strong   { color: var(--text-hi); }
.message-time { color: var(--text-lo); font-size: 0.75rem; }

.message-text {
  color: var(--text-hi);
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Source Chips */
.sources-list {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.sources-label {
  font-size: 0.8rem;
  color: var(--text-mid);
}

.source-chip {
  background: var(--bg-input);
  color: var(--text-mid);
  border: 1px solid var(--border-hi);
  border-radius: 16px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}
.source-chip:hover {
  color: var(--text-hi);
  border-color: var(--text-lo);
}

/* Tool Badge */
.tool-badge {
  align-self: flex-start;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  background: rgba(16, 185, 129, 0.1); /* Green tint */
  color: var(--green);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

/* Typing Indicator */
.typing-bubble {
  flex-direction: row;
  align-items: center;
  gap: 4px;
  padding: 1rem 1.5rem;
}
.dot {
  width: 6px; height: 6px;
  background: var(--text-mid);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

/* Input Area */
.input-area {
  display: flex;
  padding: 1rem 1.5rem;
  background: var(--bg-shell);
  border-top: 1px solid var(--border);
  gap: 0.75rem;
}

.input-area input {
  flex: 1;
  background: var(--bg-input);
  border: 1px solid var(--border-hi);
  color: var(--text-hi);
  padding: 0.875rem 1rem;
  border-radius: 8px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.input-area input:focus { border-color: var(--amber); }

.send-btn {
  background: var(--amber);
  color: #0D1B2A;
  font-weight: 600;
  border: none;
  padding: 0 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.send-btn:hover:not(:disabled) { opacity: 0.85; }
.send-btn:disabled { background: var(--text-lo); cursor: not-allowed; }
</style>