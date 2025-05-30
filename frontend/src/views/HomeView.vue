<template>
  <main>
    <div v-if="authStore.user">
      <p class="text-center text-2xl font-bold mb-4">Welcome to the Home Page</p>
      <p class="text-center">Zalogowany jako: {{ authStore.user.email }}</p>
      <button @click="logout" class="mt-4 px-4 py-2 bg-red-500 text-white rounded">
        Wyloguj się
      </button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const logout = async () => {
  await authStore.logout()
  router.push('/sign-in')
}
</script>
