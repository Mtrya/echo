import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// Create the Vue app
const app = createApp(App)

// Add Pinia for state management (like a brain for our app)
const pinia = createPinia()
app.use(pinia)

// Mount the app to the DOM
app.mount('#app')