<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Nagłówek -->
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-900">ClusterMaster</h1>
        <div v-if="authStore.user" class="flex items-center space-x-4">
          <span class="text-gray-600 hidden md:inline">{{ authStore.user.email }}</span>
          <button @click="logout" class="btn btn-danger text-sm py-1">Wyloguj się</button>
        </div>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-12">
      <div v-if="authStore.user" class="space-y-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-2xl font-bold text-center text-gray-800 mb-4">Witaj w ClusterMaster</h2>
          <p class="text-center text-gray-600 mb-6">
            Zalogowany jako: <span class="font-medium">{{ authStore.user.email }}</span>
          </p>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <h4 class="font-medium text-blue-700 text-sm mb-1">Aktywne klastry</h4>
              <p class="text-2xl font-bold text-blue-800">3</p>
            </div>
            <div class="bg-green-50 p-4 rounded-lg border border-green-100">
              <h4 class="font-medium text-green-700 text-sm mb-1">Dostępne zasoby</h4>
              <p class="text-2xl font-bold text-green-800">85%</p>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg border border-purple-100">
              <h4 class="font-medium text-purple-700 text-sm mb-1">Zadania</h4>
              <p class="text-2xl font-bold text-purple-800">12</p>
            </div>
            <div class="bg-amber-50 p-4 rounded-lg border border-amber-100">
              <h4 class="font-medium text-amber-700 text-sm mb-1">Powiadomienia</h4>
              <p class="text-2xl font-bold text-amber-800">5</p>
            </div>
          </div>
        </div>
        
        <!-- Sekcja paneli -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Panel 1 -->
          <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-semibold text-lg">Klastry</h3>
              <button class="text-sm text-primary hover:underline">Zarządzaj</button>
            </div>
            <ul class="space-y-3">
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Klaster produkcyjny</span>
                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Aktywny</span>
              </li>
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Klaster testowy</span>
                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Aktywny</span>
              </li>
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Klaster deweloperski</span>
                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Aktywny</span>
              </li>
            </ul>
          </div>
          
          <!-- Panel 2 -->
          <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-semibold text-lg">Ostatnie zadania</h3>
              <button class="text-sm text-primary hover:underline">Zobacz wszystkie</button>
            </div>
            <ul class="space-y-3">
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Aktualizacja oprogramowania</span>
                <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">W trakcie</span>
              </li>
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Backup danych</span>
                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Ukończone</span>
              </li>
              <li class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Skalowanie klastra</span>
                <span class="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full">Oczekuje</span>
              </li>
            </ul>
          </div>
          
          <!-- Panel 3 -->
          <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-semibold text-lg">Monitorowanie</h3>
              <button class="text-sm text-primary hover:underline">Szczegóły</button>
            </div>
            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span>Użycie CPU</span>
                  <span>65%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-blue-500 h-2 rounded-full" style="width: 65%"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span>Użycie pamięci</span>
                  <span>42%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-green-500 h-2 rounded-full" style="width: 42%"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-sm mb-1">
                  <span>Użycie dysku</span>
                  <span>78%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-amber-500 h-2 rounded-full" style="width: 78%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Dodatkowa sekcja -->
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-semibold text-lg">Szybkie akcje</h3>
            <span class="text-xs text-gray-500">Wybierz akcję</span>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            <button class="btn bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 flex flex-col items-center py-3">
              <span class="mb-1">Nowy klaster</span>
            </button>
            <button class="btn bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 flex flex-col items-center py-3">
              <span class="mb-1">Skaluj</span>
            </button>
            <button class="btn bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 flex flex-col items-center py-3">
              <span class="mb-1">Backup</span>
            </button>
            <button class="btn bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 flex flex-col items-center py-3">
              <span class="mb-1">Raporty</span>
            </button>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="bg-white border-t border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <p class="text-center text-sm text-gray-600">
          © 2025 ClusterMaster. Wszystkie prawa zastrzeżone.
        </p>
      </div>
    </footer>
  </div>
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
