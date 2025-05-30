import { createWebHistory, createRouter } from 'vue-router'

import SignIn from '../views/SignIn.vue'
import Register from '../views/Register.vue'
import HomeView from '../views/HomeView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/register', component: Register },
  { path: '/sign-in', component: SignIn },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router;