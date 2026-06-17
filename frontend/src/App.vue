<template>
  <Teleport to="body">
    <div :class="['toast', toast.show && 'toast--show']">
      <span class="toast__icon">{{ toast.icon }}</span>
      <span>{{ toast.msg }}</span>
    </div>
  </Teleport>

  <LoginView v-if="!store.isLoggedIn" />

  <div v-else class="shell">

    <nav class="sidebar">
      <div class="sidebar__logo">⚙</div>

      <button
        v-for="item in navItems"
        :key="item.view"
        :class="['nav-item', store.activeView === item.view && 'nav-item--active']"
        @click="store.activeView = item.view"
        :title="$t(item.labelKey)"
      >
        <span class="nav-item__icon">{{ item.icon }}</span>
        <span class="nav-item__needle" v-if="store.activeView === item.view" />
        <span class="nav-item__tooltip">{{ $t(item.labelKey) }}</span>
      </button>

      <div class="sidebar__spacer" />

      <button class="nav-item lang-toggle" @click="toggleLanguage" :title="locale === 'ar' ? 'Switch to English' : 'التبديل للعربية'">
        <span class="nav-item__icon">🌐</span>
        <span class="nav-item__tooltip">{{ locale === 'ar' ? 'English' : 'العربية' }}</span>
      </button>

      <div class="sidebar__avatar" @click="store.logout()" :title="$t('nav.logout')">
        {{ store.user?.[0]?.toUpperCase() || 'A' }}
      </div>
    </nav>

    <div class="view-area">
      
      <template v-if="store.activeView === 'chat'">
        <div class="split">
          <ChatPanel     class="split__left"  />
          <DocumentPanel class="split__right" />
        </div>
      </template>

      <WorkflowView v-else-if="store.activeView === 'workflow'" />

    </div>
  </div>
</template>

<script setup>
import { reactive, provide, watchEffect } from 'vue'
import { useAppStore }       from '@/stores/app.js'
import { useI18n }           from 'vue-i18n'

// Import only the views that actually exist
import LoginView             from '@/components/LoginView.vue'
import ChatPanel             from '@/components/ChatPanel.vue'
import DocumentPanel         from '@/components/DocumentPanel.vue'
import WorkflowView          from '@/components/WorkflowView.vue'

const store = useAppStore()
const { locale, t } = useI18n()

watchEffect(() => {
  document.documentElement.dir = locale.value === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = locale.value;
})

function toggleLanguage() {
  locale.value = locale.value === 'en' ? 'ar' : 'en'
}

// Updated navigation array (Removed Inventory & Admin)
const navItems = [
  { view: 'chat',     icon: '💬', labelKey: 'nav.chat' },
  { view: 'workflow', icon: '⚡', labelKey: 'nav.workflow' } // The new Workflow button
]

// Toast system
const toast = reactive({ show: false, icon: '✅', msg: '', _timer: null })

function showToast(msg, icon = '✅') {
  toast.icon = icon
  toast.msg  = msg
  toast.show = true
  clearTimeout(toast._timer)
  toast._timer = setTimeout(() => { toast.show = false }, 3000)
}

provide('toast', showToast)
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
/* ── RESET & TOKENS ──────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-shell:   #0D1B2A;
  --bg-panel:   #1C2F44;
  --bg-card:    #243650;
  --bg-input:   #162033;
  --amber:      #F59E0B;
  --amber-dim:  rgba(245,158,11,0.1);
  --text-hi:    #F8FAFC;
  --text-mid:   #94A3B8;
  --text-lo:    #4A6080;
  --border:     #243650;
  --border-hi:  #2E4A6A;
  --green:      #10B981;
  --red:        #EF4444;
  --blue:       #3B82F6;
  --mono:       'JetBrains Mono', monospace;
  --sans:       'IBM Plex Sans Arabic', 'Inter', sans-serif;
  --nav-w:      64px;
  --radius:     8px;
}

html, body {
  height: 100%; overflow: hidden;
  background: var(--bg-shell);
  font-family: var(--sans);
  color: var(--text-hi);
  font-size: 14px;
}

/* ── SHELL ───────────────────────────────────────────────── */
.shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.view-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.split {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.split__left  { flex: 1; min-width: 0; border-right: 1px solid var(--border); }
.split__right { width: 300px; flex-shrink: 0; }

/* ── SIDEBAR ─────────────────────────────────────────────── */
.sidebar {
  width: var(--nav-w);
  flex-shrink: 0;
  background: var(--bg-shell);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 4px;
  z-index: 10;
}

.sidebar__logo { font-size: 22px; color: var(--amber); margin-bottom: 12px; }
.sidebar__spacer { flex: 1; }
.lang-toggle { margin-bottom: 8px; }

.sidebar__avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(245,158,11,0.15); color: var(--amber);
  font-weight: 600; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background 0.15s;
}
.sidebar__avatar:hover { background: rgba(245,158,11,0.25); }

/* ── NAV ITEMS ───────────────────────────────────────────── */
.nav-item {
  position: relative; width: 44px; height: 44px; border-radius: var(--radius);
  background: transparent; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-lo); font-size: 18px; transition: background 0.15s, color 0.15s;
}
.nav-item:hover { background: var(--bg-card); color: var(--text-mid); }
.nav-item--active { background: var(--amber-dim); color: var(--amber); }

.nav-item__needle {
  position: absolute; left: -1px; top: 50%; transform: translateY(-50%);
  width: 3px; height: 24px; background: var(--amber); border-radius: 0 2px 2px 0;
}

.nav-item__tooltip {
  display: none; position: absolute; left: 52px; background: var(--bg-card);
  color: var(--text-hi); font-size: 12px; padding: 5px 10px; border-radius: 5px;
  white-space: nowrap; border: 1px solid var(--border-hi); pointer-events: none; z-index: 99;
}
.nav-item:hover .nav-item__tooltip { display: block; }

/* ── TOAST ───────────────────────────────────────────────── */
.toast {
  position: fixed; bottom: 24px; right: 24px; background: var(--bg-card);
  border: 1px solid var(--border-hi); border-radius: var(--radius);
  padding: 12px 16px; font-size: 13px; color: var(--text-hi); z-index: 999;
  display: flex; align-items: center; gap: 8px; transform: translateY(80px);
  opacity: 0; transition: transform 0.25s, opacity 0.25s; pointer-events: none;
}
.toast--show { transform: translateY(0); opacity: 1; }
.toast__icon { font-size: 16px; }

/* ── RTL OVERRIDES (ARABIC) ──────────────────────────────── */
[dir="rtl"] .sidebar { border-right: none; border-left: 1px solid var(--border); }
[dir="rtl"] .nav-item__needle { left: auto; right: -1px; border-radius: 2px 0 0 2px; }
[dir="rtl"] .nav-item__tooltip { left: auto; right: 52px; }
[dir="rtl"] .split__left { border-right: none; border-left: 1px solid var(--border); }
[dir="rtl"] .toast { right: auto; left: 24px; }

/* ── GLOBAL SCROLLBAR ────────────────────────────────────── */
* { scrollbar-width: thin; scrollbar-color: var(--border-hi) transparent; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }

/* ── GOOGLE FONTS ────────────────────────────────────────── */

</style>