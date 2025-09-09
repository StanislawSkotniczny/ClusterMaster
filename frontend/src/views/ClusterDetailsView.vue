<template>
  <div class="container mx-auto p-6">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <span class="ml-3 text-gray-600">Ładowanie szczegółów klastra...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Błąd ładowania klastra</h3>
          <p class="mt-1 text-sm text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div v-else-if="clusterDetails">
      <!-- Header with breadcrumbs -->
      <div class="mb-8">
        <nav class="flex mb-4" aria-label="Breadcrumb">
          <ol class="flex items-center space-x-4">
            <li>
              <div>
                <router-link to="/" class="text-gray-400 hover:text-gray-500">
                  <svg class="flex-shrink-0 h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
                  </svg>
                  <span class="sr-only">Home</span>
                </router-link>
              </div>
            </li>
            <li>
              <div class="flex items-center">
                <svg class="flex-shrink-0 h-5 w-5 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
                <router-link to="/" class="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">Klastry</router-link>
              </div>
            </li>
            <li>
              <div class="flex items-center">
                <svg class="flex-shrink-0 h-5 w-5 text-gray-300" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
                <span class="ml-4 text-sm font-medium text-gray-500">{{ clusterName }}</span>
              </div>
            </li>
          </ol>
        </nav>

        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 flex items-center">
              <span class="mr-3">🏗️</span>
              {{ clusterName }}
              <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" 
                    :class="statusClasses">
                {{ clusterDetails.status }}
              </span>
            </h1>
            <p class="text-gray-600 mt-1">Szczegółowe informacje o klastrze Kubernetes</p>
          </div>
          <div class="flex space-x-3">
            <button 
              @click="refreshData"
              :disabled="refreshing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <svg v-if="refreshing" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              Odśwież
            </button>
            <button 
              @click="deleteCluster"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Usuń klaster
            </button>
          </div>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column - Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Basic Info -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Informacje podstawowe</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-500">Nazwa klastra</label>
                <p class="mt-1 text-sm text-gray-900">{{ clusterDetails.name }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500">Status</label>
                <p class="mt-1 text-sm text-gray-900">{{ clusterDetails.status }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500">Liczba węzłów</label>
                <p class="mt-1 text-sm text-gray-900">{{ clusterDetails.node_count || 'N/A' }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500">Kontekst</label>
                <p class="mt-1 text-sm text-gray-900">{{ clusterDetails.context || 'N/A' }}</p>
              </div>
            </div>
          </div>

          <!-- Resource Usage -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Wykorzystanie zasobów</h2>
            <div v-if="clusterDetails.resources" class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700">CPU</span>
                  <span class="text-sm text-gray-500">{{ clusterDetails.resources.cpu_usage }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-blue-600 h-2 rounded-full" :style="`width: ${clusterDetails.resources.cpu_usage}%`"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700">RAM</span>
                  <span class="text-sm text-gray-500">{{ clusterDetails.resources.memory_usage }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-green-600 h-2 rounded-full" :style="`width: ${clusterDetails.resources.memory_usage}%`"></div>
                </div>
              </div>
            </div>
            <div v-else class="text-gray-500 text-sm">Brak danych o zasobach</div>
          </div>

          <!-- Applications -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Zainstalowane aplikacje</h2>
            <div v-if="installedApps.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="app in installedApps" :key="app.name" class="flex items-center justify-between p-3 border rounded-lg">
                <div class="flex items-center">
                  <div class="text-2xl mr-3">{{ app.icon }}</div>
                  <div>
                    <p class="font-medium text-gray-900">{{ app.name }}</p>
                    <p class="text-sm text-gray-500">{{ app.namespace }}</p>
                  </div>
                </div>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Zainstalowana
                </span>
              </div>
            </div>
            <div v-else class="text-gray-500 text-sm">Brak dodatkowych aplikacji</div>
          </div>
        </div>

        <!-- Right Column - Monitoring & Quick Stats -->
        <div class="space-y-6">
          <!-- Quick Stats -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Statystyki</h2>
            <div class="space-y-4">
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">Namespace'y</span>
                <span class="text-sm font-medium text-gray-900">{{ namespaceCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">Pod'y</span>
                <span class="text-sm font-medium text-gray-900">{{ podCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">Serwisy</span>
                <span class="text-sm font-medium text-gray-900">{{ serviceCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">Deployment'y</span>
                <span class="text-sm font-medium text-gray-900">{{ deploymentCount }}</span>
              </div>
            </div>
          </div>

          <!-- Monitoring Links -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Monitoring</h2>
            <div class="space-y-3">
              <div v-if="clusterDetails.monitoring?.enabled">
                <div v-if="clusterDetails.assigned_ports?.prometheus" class="flex items-center justify-between p-3 border rounded-lg">
                  <div class="flex items-center">
                    <span class="text-2xl mr-3">📊</span>
                    <div>
                      <p class="font-medium text-gray-900">Prometheus</p>
                      <p class="text-sm text-gray-500">Port {{ clusterDetails.assigned_ports.prometheus }}</p>
                    </div>
                  </div>
                  <a 
                    :href="`http://localhost:${clusterDetails.assigned_ports.prometheus}`" 
                    target="_blank"
                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Otwórz
                  </a>
                </div>
                <div v-if="clusterDetails.assigned_ports?.grafana" class="flex items-center justify-between p-3 border rounded-lg">
                  <div class="flex items-center">
                    <span class="text-2xl mr-3">📈</span>
                    <div>
                      <p class="font-medium text-gray-900">Grafana</p>
                      <p class="text-sm text-gray-500">Port {{ clusterDetails.assigned_ports.grafana }}</p>
                    </div>
                  </div>
                  <a 
                    :href="`http://localhost:${clusterDetails.assigned_ports.grafana}`" 
                    target="_blank"
                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Otwórz
                  </a>
                </div>
              </div>
              <div v-else class="text-gray-500 text-sm">Monitoring nie jest zainstalowany</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Akcje</h2>
            <div class="space-y-3">
              <router-link 
                :to="`/backup`"
                class="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                Utwórz backup
              </router-link>
              <router-link 
                :to="`/monitoring/${clusterName}`"
                class="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                Przejdź do monitoringu
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiService, type ClusterInfo } from '@/services/api'

// Router
const route = useRoute()
const router = useRouter()
const clusterName = route.params.name as string

// Reactive data
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const clusterDetails = ref<ClusterInfo | null>(null)

// Mock data for installed apps - będziemy to później pobierać z API
const installedApps = ref([
  { name: 'Prometheus', namespace: 'monitoring', icon: '📊' },
  { name: 'Grafana', namespace: 'monitoring', icon: '📈' }
])

// Mock stats - będziemy to później pobierać z API
const namespaceCount = ref(5)
const podCount = ref(12)
const serviceCount = ref(8)
const deploymentCount = ref(6)

// Computed
const statusClasses = computed(() => {
  if (!clusterDetails.value) return 'bg-gray-100 text-gray-800'
  
  switch (clusterDetails.value.status) {
    case 'Running':
    case 'Aktywny':
      return 'bg-green-100 text-green-800'
    case 'Stopped':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
})

// Methods
const loadClusterDetails = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const clusters = await ApiService.getClusters()
    const cluster = clusters.find((c: ClusterInfo) => c.name === clusterName)
    
    if (!cluster) {
      error.value = `Klaster "${clusterName}" nie został znaleziony`
      return
    }
    
    clusterDetails.value = cluster
  } catch (err) {
    error.value = (err as Error).message || 'Błąd podczas ładowania szczegółów klastra'
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  refreshing.value = true
  await loadClusterDetails()
  refreshing.value = false
}

const deleteCluster = async () => {
  if (!clusterDetails.value) return
  
  const confirmed = confirm(`Czy na pewno chcesz usunąć klaster "${clusterDetails.value.name}"?`)
  if (!confirmed) return
  
  try {
    await ApiService.deleteCluster(clusterDetails.value.name)
    router.push('/')
  } catch (err) {
    alert('Błąd podczas usuwania klastra: ' + (err as Error).message)
  }
}

// Load data on mount
onMounted(() => {
  loadClusterDetails()
})
</script>
