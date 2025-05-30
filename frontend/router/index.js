import { createMemoryHistory, createRouter } from 'vue-router'

import SignIn from './SignIn.vue'
import Register from './Register.vue'
import HomeView from './HomeView.vue'

const routes = [
    { path: '/', component: HomeView },
    { path: '/register', component: Register },
    { path: '/sign-in', component: SignIn },
]

const router = createRouter({
    history: createMemoryHistory(),
    routes,
})

export default router;