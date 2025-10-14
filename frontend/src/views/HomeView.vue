<template>
  <!-- Success Notification -->
  <div 
    v-if="showSuccessNotification"
    class="fixed top-20 right-4 bg-green-500 dark:bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-sm animate-slide-in"
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
        class="text-white hover:text-gray-200 transition-colors"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    </div>
    <p class="text-sm mt-1">{{ successMessage }}</p>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div v-if="authStore.user" class="space-y-6">
        
        <!-- Statystyki -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Aktywne klastry -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Aktywne klastry</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ clusterDetails.length }}</p>
              </div>
              <div class="bg-blue-100 dark:bg-blue-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Dostępne zasoby -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Dostępne zasoby</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ totalNodesCount }}</p>
              </div>
              <div class="bg-green-100 dark:bg-green-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V8z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Zadania -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Zadania</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ activeTasksCount }}</p>
              </div>
              <div class="bg-purple-100 dark:bg-purple-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Powiadomienia -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Powiadomienia</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ notificationsCount }}</p>
              </div>
              <div class="bg-amber-100 dark:bg-amber-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-amber-600 dark:text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Klastry lokalne -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <div class="flex items-center space-x-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Klastry lokalne</h3>
                <svg 
                  v-if="clustersStore.isRefreshing" 
                  class="animate-spin h-4 w-4 text-blue-500 dark:text-blue-400" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <button 
                @click="loadClusters" 
                class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
                :disabled="loading"
              >
                {{ loading ? 'Ładowanie...' : 'Odśwież' }}
              </button>
            </div>
            <div class="p-6">
              <div v-if="loading" class="text-gray-500 dark:text-gray-400 text-center py-8">
                <svg class="animate-spin h-8 w-8 text-blue-500 dark:text-blue-400 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-sm">Ładowanie klastrów...</p>
              </div>
              <div v-else-if="clusterDetails.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-8">
                <svg class="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <p class="text-sm font-medium mb-1">Brak klastrów lokalnych</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Utwórz pierwszy klaster aby rozpocząć</p>
              </div>
              <ul v-else class="space-y-3">
                <li 
                  v-for="cluster in clusterDetails" 
                  :key="cluster.name" 
                  class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                >
                  <div class="flex items-center space-x-3">
                    <div class="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
                      <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="flex items-center space-x-2">
                        <span class="font-medium text-gray-900 dark:text-white">{{ cluster.name }}</span>
                        <span v-if="cluster.provider === 'k3d'" class="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">
                          🚀 k3d
                        </span>
                        <span v-else class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">
                          🔵 kind
                        </span>
                      </div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ cluster.node_count || 0 }} nodes</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">
                      Aktywny
                    </span>
                    <router-link 
                      :to="`/clusters/${cluster.name}`"
                      class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Szczegóły →
                    </router-link>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <!-- Monitorowanie zasobów -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Monitorowanie zasobów</h3>
              <router-link 
                to="/monitoring" 
                class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
              >
                Szczegóły
              </router-link>
            </div>
            <div class="p-6 space-y-5">
              <!-- CPU -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Użycie CPU</span>
                  <span class="text-sm font-semibold text-gray-900 dark:text-white">65%</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                  <div class="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full" style="width: 65%"></div>
                </div>
              </div>

              <!-- Pamięć -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Użycie pamięci</span>
                  <span class="text-sm font-semibold text-gray-900 dark:text-white">42%</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                  <div class="bg-green-600 dark:bg-green-500 h-2.5 rounded-full" style="width: 42%"></div>
                </div>
              </div>

              <!-- Dysk -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Użycie dysku</span>
                  <span class="text-sm font-semibold text-gray-900 dark:text-white">78%</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                  <div class="bg-amber-500 dark:bg-amber-400 h-2.5 rounded-full" style="width: 78%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Ostatnie zadania -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
          <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Ostatnie zadania</h3>
            <button class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors">
              Zobacz wszystkie
            </button>
          </div>
          <div class="p-6">
            <ul class="space-y-3">
              <li class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span class="text-sm font-medium text-gray-900 dark:text-white">Aktualizacja oprogramowania</span>
                <span class="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">W trakcie</span>
              </li>
              <li class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span class="text-sm font-medium text-gray-900 dark:text-white">Backup danych</span>
                <span class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">Ukończone</span>
              </li>
              <li class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span class="text-sm font-medium text-gray-900 dark:text-white">Skalowanie klastra</span>
                <span class="px-3 py-1 bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 text-xs rounded-full font-medium">Oczekuje</span>
              </li>
            </ul>
          </div>
        </div>

      </div>
  </main>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useClustersStore } from '../stores/clusters'
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted, computed } from 'vue'

const authStore = useAuthStore()
const clustersStore = useClustersStore()
const router = useRouter()
const route = useRoute()
const showSuccessNotification = ref(false)
const successMessage = ref("")

// Use store data
const clusterDetails = computed(() => clustersStore.clusters)
const loading = computed(() => clustersStore.isLoading)

// Computed properties for statistics
const totalNodesCount = computed(() => {
  return clusterDetails.value.reduce((sum, cluster) => sum + (cluster.node_count || 0), 0)
})

const activeTasksCount = ref(12) // Placeholder - będzie z API później
const notificationsCount = ref(5) // Placeholder - będzie z API później

onMounted(async () => {
  // Check for success message from deployment
  if (route.query.success === 'cluster_created') {
    showSuccessNotification.value = true
    successMessage.value = route.query.message as string || "Klaster został utworzony pomyślnie!"
    
    // Clear query params
    router.replace({ query: {} })
    
    setTimeout(() => {
      showSuccessNotification.value = false
    }, 5000)
  }
  
  // Load clusters if not already loaded (App.vue handles auto-refresh)
  if (clustersStore.clusters.length === 0) {
    await clustersStore.fetchClusters()
  }
})

const loadClusters = async () => {
  try {
    console.log("Ładowanie klastrów...")
    await clustersStore.fetchClusters()
    console.log("Otrzymane szczegóły klastrów:", clustersStore.clusters)
  } catch (error) {
    console.error('Błąd ładowania klastrów:', error)
  }
}
</script>

<style scoped>
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
</style>
