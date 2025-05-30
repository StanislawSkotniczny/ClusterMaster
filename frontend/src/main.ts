import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import "./firebase"
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

const initApp = async () => {
    const authStore = useAuthStore()

    try {
        await authStore.init()
        console.log("Inicjalizacja autentykacji zakończona", authStore.user ? "Zalogowany" : "Niezalogowany")
    } catch (error) {
        console.error("Błąd inicjalizacji autentykacji:", error)
    }
    app.mount('#app')
}

initApp()
