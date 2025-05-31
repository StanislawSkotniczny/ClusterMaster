import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import SignIn from '../views/SignIn.vue'
import Register from '../views/Register.vue'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/register',
    component: Register
  },
  {
    path: '/sign-in',
    component: SignIn
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})


let authInitialized = false
let pendingNavigations: Array<{ to: any, from: any, next: any }> = []

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.authReady && !authInitialized) {
    authInitialized = true
    pendingNavigations.push({ to, from, next })

    try {
      await authStore.init()

      pendingNavigations.forEach(navigation => {
        const { to, next } = navigation
        if (to.meta.requiresAuth && !authStore.user) {
          next('/sign-in')
        } else {
          next()
        }
      })
      pendingNavigations = []
    } catch (error) {
      console.error('Błąd inicjalizacji autentykacji:', error)
      next('/sign-in')
    }
  } else if (authStore.authReady) {
    if (to.meta.requiresAuth && !authStore.user) {
      next('/sign-in')
    } else {
      next()
    }
  } else {
    pendingNavigations.push({ to, from, next })
  }
})

export default router