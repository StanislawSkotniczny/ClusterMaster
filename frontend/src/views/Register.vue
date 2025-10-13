<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full p-8 bg-white rounded-lg shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-800 mb-8">Utwórz konto</h2>
      <form @submit.prevent="register" class="space-y-6">
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
          <button type="submit" class="w-full btn btn-primary">Zarejestruj się</button>
        </div>
        <div class="text-center mt-4">
          <router-link to="/sign-in" class="text-sm text-primary hover:underline">
            Masz już konto? Zaloguj się
          </router-link>
        </div>
      </form>
    </div>
  </div>
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

<style scoped>
.form-input {
  display: block;
  width: 100%;
  padding-left: 0.75rem;
  padding-right: 0.75rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  outline: none;
}
.form-input:focus {
  box-shadow: 0 0 0 3px rgba(59,130,246,0.5);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  font-size: 0.875rem;
  font-weight: 500;
}

.btn-primary {
  color: #fff;
  background-color: #2563eb;
}
.btn-primary:hover {
  background-color: #1d4ed8;
}
.btn-primary:focus {
  outline: none;
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #3b82f6;
}
</style>