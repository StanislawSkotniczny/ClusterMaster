<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Success Notification -->
    <div 
      v-if="showSuccessNotification"
      class="fixed top-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-sm"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span class="text-sm font-medium">Sukces!</span>
        </div>
        <button 
          @click="showSuccessNotification = false"
          class="text-white hover:text-gray-200"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
      <p class="text-sm mt-1">{{ successMessage }}</p>
    </div>

    <!-- Nagłówek -->
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold text-gray-900">ClusterMaster</h1>
          
          <!-- Nawigacja -->
          <nav class="hidden md:flex space-x-6">
            <router-link 
              to="/" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/' }"
            >
              🏠 Pulpit
            </router-link>
            <router-link 
              to="/deploy" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/deploy' }"
            >
              🚀 Deploy
            </router-link>
            <router-link 
              to="/monitoring" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/monitoring' }"
            >
              📊 Monitoring
            </router-link>
            <router-link 
              to="/backup" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/backup' }"
            >
              🗂️ Backup
            </router-link>
            <router-link 
              to="/apps" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'bg-gray-100 text-gray-900': $route.path === '/apps' }"
            >
              🏪 App Store
            </router-link>
          </nav>
          
          <div v-if="authStore.user" class="flex items-center space-x-4">
            <span class="text-gray-600 hidden lg:inline">{{ authStore.user.email }}</span>
            <button @click="logout" class="btn btn-danger text-sm py-1">Wyloguj się</button>
          </div>
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
              <h3 class="font-semibold text-lg">Klastry lokalne</h3>
              <button @click="loadClusters" class="text-sm text-primary hover:underline">
                {{ loading ? 'Ładowanie...' : 'Odśwież' }}
              </button>
            </div>
            <ul class="space-y-3">
              <li v-if="loading" class="text-gray-500 text-center py-4">
                Ładowanie klastrów...
              </li>
              <li v-else-if="clusters.length === 0" class="text-gray-500 text-center py-4">
                Brak klastrów lokalnych
              </li>
              <li v-else v-for="cluster in clusters" :key="cluster" class="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>{{ cluster }}</span>
                <div class="flex items-center space-x-2">
                  <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Aktywny</span>
                  <router-link 
                    :to="`/cluster/${cluster}`"
                    class="text-blue-600 hover:text-blue-800 text-xs font-medium"
                  >
                    Szczegóły
                  </router-link>
                </div>
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
            <button 
              @click="goToDeployView"
              class="btn bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 flex flex-col items-center py-3"
            >
              <span class="mb-1">🚀 Nowy klaster</span>
            </button>
            <button 
              @click="goToMonitoringView"
              class="btn bg-orange-50 text-orange-700 hover:bg-orange-100 border border-orange-200 flex flex-col items-center py-3"
            >
              <span class="mb-1">📊 Monitoring</span>
            </button>
            <button class="btn bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 flex flex-col items-center py-3">
              <span class="mb-1">📈 Skaluj</span>
            </button>
            <button class="btn bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 flex flex-col items-center py-3">
              <span class="mb-1">💾 Backup</span>
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
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { ApiService } from '@/services/api'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const clusters = ref<string[]>([])
const loading = ref(false)
const showSuccessNotification = ref(false)
const successMessage = ref("")

onMounted(() => {
  if (route.query.success === 'true') {
    showSuccessNotification.value = true
    successMessage.value = route.query.message as string || `Klaster "${route.query.cluster}" został utworzony!`
    
    router.replace({ path: route.path })
    
    setTimeout(() => {
      showSuccessNotification.value = false
    }, 5000)
  }
  
  loadClusters()
})

const logout = async () => {
  await authStore.logout()
  router.push('/sign-in')
}

const goToDeployView = () => {
  router.push('/deploy')
}

const goToMonitoringView = () => {
  router.push('/monitoring')
}

const loadClusters = async () => {
  loading.value = true
  try {
    console.log("Ładowanie klastrów...")
    const result = await ApiService.listClusters()
    console.log("Otrzymane klastry:", result)
    clusters.value = result.clusters || []
  } catch (error) {
    console.error('Błąd ładowania klastrów:', error)
    clusters.value = []
  } finally {
    loading.value = false
  }
}
</script>
