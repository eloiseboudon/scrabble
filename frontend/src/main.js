import * as Vue from 'vue'
import { createApp } from 'vue'
import App from './App.vue'
import { apiGet, apiPost } from './api.js'

// Make Vue and API utilities available globally for non-module scripts
window.Vue = Vue
window.apiGet = apiGet
window.apiPost = apiPost

// Initialize the Vue app
const app = createApp(App)

// Handle visibility change
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible') {
    // Handle visibility change if needed
  }
})

// Mount the app
app.mount('#app')
