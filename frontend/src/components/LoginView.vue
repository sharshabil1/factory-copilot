<template>
  <div class="login-wrapper">
    
    <div class="login-lang-toggle">
      <button @click="toggleLanguage" class="lang-btn">
        🌐 {{ locale === 'ar' ? 'English' : 'العربية' }}
      </button>
    </div>

    <div class="login-card">
      <div class="brand-header">
        <h1 class="brand-name">
          {{ $t('brand.name') }}<span class="brand-accent">{{ $t('brand.accent') }}</span>
        </h1>
        <p class="brand-tagline">{{ $t('brand.tagline') }}</p>
      </div>

      <form class="login-form" @submit.prevent="submit">
        
        <div class="input-group">
          <label for="username">{{ $t('login.username') }}</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            :placeholder="$t('login.username')"
            :disabled="loading"
            autocomplete="username"
            required
          />
        </div>

        <div class="input-group">
          <label for="password">{{ $t('login.password') }}</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            :disabled="loading"
            autocomplete="current-password"
            required
          />
        </div>

        <transition name="fade">
          <div v-if="error" class="error-message">
            ⚠️ {{ error }}
          </div>
        </transition>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="!loading">{{ $t('login.signIn') }}</span>
          <div v-else class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </button>
        
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAppStore } from '@/stores/app.js'
import { useI18n } from 'vue-i18n' // <-- Import i18n for logic translations

const store = useAppStore()
const { t, locale } = useI18n()

const loading = ref(false)
const error = ref('')

const form = reactive({ 
  username: '', 
  password: '' 
})

function toggleLanguage() {
  locale.value = locale.value === 'en' ? 'ar' : 'en'
}

async function submit() {
  if (!form.username || !form.password) {
    // Using the translation function inside the script setup
    error.value = t('login.errorEmpty')
    return
  }
  
  error.value = ''
  loading.value = true
  
  try {
    await store.login(form.username, form.password)
  } catch (err) {
    // Fall back to the translated error if the backend doesn't provide a specific one
    error.value = err.message ?? t('login.errorFail')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Keep your existing styles, but add the language toggle positioning */
.login-wrapper {
  position: fixed;
  inset: 0;
  background-color: var(--bg-shell); /* Switched to your app's shell token */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* Position the language toggle at the top right (or top left in RTL) */
.login-lang-toggle {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
}

[dir="rtl"] .login-lang-toggle {
  right: auto;
  left: 1.5rem;
}

.lang-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border-hi);
  color: var(--text-hi);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg-panel); /* Adjusted to match your dark mode theme */
  border-radius: 16px;
  padding: 3rem 2.5rem;
  border: 1px solid var(--border-hi);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* Header & Branding */
.brand-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.brand-name {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-hi);
  letter-spacing: -0.5px;
  margin: 0;
  font-family: 'Inter', sans-serif;
}

.brand-accent {
  color: var(--amber); /* Using your app's amber token */
}

.brand-tagline {
  font-size: 0.875rem;
  color: var(--text-mid);
  margin-top: 0.5rem;
}

/* Form Styles */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-hi);
}

.input-group input {
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-hi);
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: var(--text-hi);
  background-color: var(--bg-input);
  transition: all 0.2s ease;
  outline: none;
}

.input-group input:focus {
  border-color: var(--amber);
  box-shadow: 0 0 0 1px var(--amber);
}

/* Error State */
.error-message {
  font-size: 0.875rem;
  color: var(--red);
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Submit Button */
.submit-btn {
  margin-top: 0.5rem;
  background-color: var(--amber);
  color: #0D1B2A; /* High contrast text on amber background */
  font-family: inherit;
  font-weight: 700;
  font-size: 1rem;
  padding: 0.875rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 48px;
}

.submit-btn:hover:not(:disabled) {
  background-color: #D97706; /* Slightly darker amber */
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  background-color: var(--text-lo);
  cursor: not-allowed;
  opacity: 0.7;
}

/* Loading Animation */
.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  background-color: #0D1B2A;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>