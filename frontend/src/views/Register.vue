<template>
  <h1>Utwórz konto</h1>
  <p><input type="text" placeholder="Email" v-model="email"/></p>
  <p><input type="password" placeholder="Password" v-model="password"/></p>
  <p><button @click="register">Submit</button></p>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getAuth, createUserWithEmailAndPassword } from 'firebase/auth'
import { useRouter } from 'vue-router' 

const email = ref('')
const password = ref('')
const router = useRouter() 

const register = async () => {
  try {
    const userCredential = await createUserWithEmailAndPassword(getAuth(), email.value, password.value)
    const user = userCredential.user
    console.log('User registered:', user)
    router.push('/') 
  } catch (error: any) {
    const errorCode = error.code
    const errorMessage = error.message
    console.error('Error registering user:', errorCode, errorMessage)
    alert(`Błąd rejestracji: ${errorMessage}`)
  }
}
</script>