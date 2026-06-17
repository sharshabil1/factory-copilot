import { createApp } from 'vue'
import { createPinia } from 'pinia'
import i18n from './i18n.js'
import App from './App.vue'

const app = createApp(App)

// 1. Initialize Plugins FIRST
app.use(createPinia())
app.use(i18n)

// 2. Mount the app LAST
app.mount('#app')