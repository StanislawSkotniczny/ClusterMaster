<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full p-8 bg-white rounded-lg shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">Logowanie</h2>
      <form @submit.prevent="doLogin" class="space-y-6">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">E-mail</label>
          <input 
            id="email"
            v-model="email" 
            type="email" 
            placeholder="Twój email" 
            required
            class="form-input mt-1"
          />
        </div>
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Hasło</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="Hasło" 
            required
            class="form-input mt-1"
          />
        </div>
        <div>
          <button type="submit" class="w-full btn btn-primary">Zaloguj się</button>
        </div>
        <div class="text-center mt-4">
          <router-link to="/register" class="text-sm text-primary hover:underline">
            Nie masz konta? Zarejestruj się
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useAuthStore } from "../stores/auth"
import { useRouter } from "vue-router" 

const email = ref("")
const password = ref("")
const authStore = useAuthStore()
const router = useRouter() 

async function doLogin() {
  try {
    await authStore.login(email.value, password.value)
    router.push("/")
  } catch (e) {
    alert("Błąd logowania")
  }
}
</script>