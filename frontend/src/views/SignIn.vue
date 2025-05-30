<template>
  <form @submit.prevent="doLogin">
    <input v-model="email" placeholder="E-mail" />
    <input type="password" v-model="password" placeholder="Hasło" />
    <button type="submit">Zaloguj</button>
  </form>
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
