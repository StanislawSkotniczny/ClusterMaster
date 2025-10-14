import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import SignIn from '../views/SignIn.vue'
import Register from '../views/Register.vue'
import HomeView from '../views/HomeView.vue'
import DeployView from '../views/DeployView.vue'
import MonitoringView from '../views/MonitoringView.vue'
import BackupView from '../views/BackupView.vue'
import ClusterDetailsView from '../views/ClusterDetailsView.vue'
import AppsView from '../views/AppsView.vue'
import ScaleView from '../views/ScaleView.vue'

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
  {
    path: '/deploy',
    component: DeployView,
    meta: { requiresAuth: true }
  },
  {
    path: '/monitoring',
    component: MonitoringView,
    meta: { requiresAuth: true }
  },
  {
    path: '/backup',
    component: BackupView,
    meta: { requiresAuth: true }
  },
  {
    path: '/clusters/:name',
    component: ClusterDetailsView,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/clusters/:name/scale',
    name: 'scale',
    component: ScaleView,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/apps',
    component: AppsView,
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})


let authInitialized = false
interface PendingNavigation {
  to: RouteLocationNormalized
  from: RouteLocationNormalized
  next: NavigationGuardNext
}
let pendingNavigations: PendingNavigation[] = []

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