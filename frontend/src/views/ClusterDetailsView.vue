<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      <span class="ml-3 text-gray-600 dark:text-gray-400">Ładowanie szczegółów klastra...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-300">Błąd ładowania klastra</h3>
          <p class="mt-1 text-sm text-red-700 dark:text-red-400">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div v-else-if="clusterDetails">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
              {{ clusterName }}
              <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" 
                    :class="statusClasses">
                {{ clusterDetails.status }}
              </span>
            </h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">Szczegółowe informacje o klastrze Kubernetes</p>
          </div>
          <div class="flex space-x-3">
            <button 
              @click="refreshData"
              :disabled="refreshing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
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
              @click="goToScaling"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
              </svg>
              Skaluj
            </button>
            <button 
              @click="deleteCluster"
              class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
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
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Informacje podstawowe</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Nazwa klastra</label>
                <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ clusterDetails.name }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ clusterDetails.status }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Liczba węzłów</label>
                <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ clusterDetails.node_count || 'N/A' }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Kontekst</label>
                <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ clusterDetails.context || 'N/A' }}</p>
              </div>
            </div>
          </div>

          <!-- Resource Usage -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Wykorzystanie zasobów</h2>
            <div v-if="clusterDetails.resources" class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">CPU</span>
                  <span class="text-sm text-gray-500 dark:text-gray-400">{{ clusterDetails.resources.cpu_usage }}%</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div class="bg-blue-600 dark:bg-blue-500 h-2 rounded-full" :style="`width: ${clusterDetails.resources.cpu_usage}%`"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">RAM</span>
                  <span class="text-sm text-gray-500 dark:text-gray-400">{{ clusterDetails.resources.memory_usage }}%</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div class="bg-green-600 dark:bg-green-500 h-2 rounded-full" :style="`width: ${clusterDetails.resources.memory_usage}%`"></div>
                </div>
              </div>
            </div>
            <div v-else class="text-gray-500 dark:text-gray-400 text-sm">Brak danych o zasobach</div>
          </div>

          <!-- Applications -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">Zainstalowane aplikacje</h2>
              <router-link 
                to="/apps"
                class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-lg text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                </svg>
                Dodaj aplikację
              </router-link>
            </div>
            <div v-if="installedApps.length > 0" class="space-y-3">
              <div v-for="app in installedApps" :key="app.name" class="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900/20 hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors">
                <div class="flex items-center flex-1">
                  <div class="text-2xl mr-3">{{ app.icon }}</div>
                  <div class="flex-1">
                    <p class="font-medium text-gray-900 dark:text-gray-100">{{ app.name }}</p>
                    <div class="flex items-center text-sm text-gray-500 dark:text-gray-400 space-x-2">
                      <span>{{ app.namespace }}</span>
                      <span v-if="app.chart" class="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">{{ app.chart }}</span>
                      <span v-if="app.app_version" class="text-xs text-blue-600 dark:text-blue-400">v{{ app.app_version }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="app.status === 'deployed' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300'">
                    {{ app.status }}
                  </span>
                  <button
                    @click="uninstallApp(app.name)"
                    :disabled="uninstallingApps.includes(app.name)"
                    class="inline-flex items-center px-3 py-1 border border-red-300 dark:border-red-700 rounded-lg text-sm font-medium text-red-700 dark:text-red-400 bg-white dark:bg-gray-800 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg v-if="uninstallingApps.includes(app.name)" class="animate-spin -ml-1 mr-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <svg v-else class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                    {{ uninstallingApps.includes(app.name) ? 'Odinstalowywanie...' : 'Odinstaluj' }}
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8">
              <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-4.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 009.586 13H7"></path>
              </svg>
              <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">Brak aplikacji</h3>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Rozpocznij od zainstalowania swojej pierwszej aplikacji</p>
              <div class="mt-6">
                <router-link 
                  to="/apps"
                  class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-lg text-white bg-blue-600 dark:bg-blue-700 hover:bg-blue-700 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Przeglądaj aplikacje
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Monitoring & Quick Stats -->
        <div class="space-y-6">
          <!-- Quick Stats -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Statystyki</h2>
            <div class="space-y-4">
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Namespace'y</span>
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ namespaceCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Pod'y</span>
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ podCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Serwisy</span>
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ serviceCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Deployment'y</span>
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ deploymentCount }}</span>
              </div>
            </div>
          </div>

          <!-- Monitoring Links -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Monitoring</h2>
            <div class="space-y-3">
              <div v-if="clusterDetails.monitoring?.enabled">
                <div v-if="clusterDetails.assigned_ports?.prometheus" class="flex items-center justify-between p-3 border border-gray-100 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900/20">
                  <div class="flex items-center">
                    <div class="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg mr-3">
                      <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-gray-900 dark:text-gray-100">Prometheus</p>
                      <p class="text-sm text-gray-500 dark:text-gray-400">Port {{ clusterDetails.assigned_ports.prometheus }}</p>
                    </div>
                  </div>
                  <a 
                    :href="`http://localhost:${clusterDetails.assigned_ports.prometheus}`" 
                    target="_blank"
                    class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
                  >
                    Otwórz
                  </a>
                </div>
                <div v-if="clusterDetails.assigned_ports?.grafana" class="flex items-center justify-between p-3 border border-gray-100 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900/20">
                  <div class="flex items-center">
                    <div class="bg-orange-100 dark:bg-orange-900 p-2 rounded-lg mr-3">
                      <svg class="w-5 h-5 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                      </svg>
                    </div>
                    <div>
                      <p class="font-medium text-gray-900 dark:text-gray-100">Grafana</p>
                      <p class="text-sm text-gray-500 dark:text-gray-400">Port {{ clusterDetails.assigned_ports.grafana }}</p>
                    </div>
                  </div>
                  <a 
                    :href="`http://localhost:${clusterDetails.assigned_ports.grafana}`" 
                    target="_blank"
                    class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium"
                  >
                    Otwórz
                  </a>
                </div>
              </div>
              <div v-else class="text-gray-500 dark:text-gray-400 text-sm">Monitoring nie jest zainstalowany</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl border border-gray-100 dark:border-gray-700 p-6">
            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Akcje</h2>
            <div class="space-y-3">
              <router-link 
                :to="`/backup`"
                class="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                Utwórz backup
              </router-link>
              <router-link 
                :to="`/monitoring/${clusterName}`"
                class="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
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
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ApiService } from '@/services/api'
import type { ClusterInfo } from '@/services/api'
import { useClustersStore } from '@/stores/clusters'

const clustersStore = useClustersStore()

// Router
const route = useRoute()
const router = useRouter()
const clusterName = route.params.name as string

// Reactive data
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const clusterDetails = ref<ClusterInfo | null>(null)

// Real data for installed apps
const installedApps = ref<Array<{ name: string; namespace: string; icon: string; status?: string; chart?: string; app_version?: string; revision?: string }>>([])
const uninstallingApps = ref<string[]>([])

// Real stats
const namespaceCount = ref(0)
const podCount = ref(0)
const serviceCount = ref(0)
const deploymentCount = ref(0)

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
    
    // Simply get cluster from store - App.vue handles fetching
    const cluster = clustersStore.getClusterByName(clusterName)
    
    if (!cluster) {
      error.value = `Klaster "${clusterName}" nie został znaleziony`
      return
    }
    
    // Assign cluster data directly - no need for toRaw
    clusterDetails.value = { ...cluster }
    
    // Load additional data
    await loadInstalledApps()
    await loadClusterStats()
  } catch (err) {
    console.error('Error loading cluster details:', err)
    error.value = (err as Error).message || 'Błąd podczas ładowania szczegółów klastra'
  } finally {
    loading.value = false
  }
}

const loadInstalledApps = async () => {
  try {
    const result = await ApiService.getInstalledApps(clusterName)
    if (result.success) {
      // Map Helm releases to our app format
      installedApps.value = result.apps.map((app: Record<string, unknown>) => ({
        name: app.name as string || 'Unknown',
        namespace: app.namespace as string || 'default',
        icon: getAppIcon(app.name as string, app.chart as string),
        status: app.status as string || 'unknown',
        chart: app.chart as string || '',
        app_version: app.app_version as string || '',
        revision: app.revision as string || '1'
      }))
    }
  } catch (err) {
    console.error('Error loading installed apps:', err)
  }
}

const loadClusterStats = async () => {
  try {
    // This would be a new API endpoint to get cluster statistics
    // For now, we'll keep the mock values but you can implement this
    namespaceCount.value = 5
    podCount.value = 12  
    serviceCount.value = 8
    deploymentCount.value = 6
  } catch (err) {
    console.error('Error loading cluster stats:', err)
  }
}

const getAppIcon = (appName: string, chart: string): string => {
  const iconMap: Record<string, string> = {
    'prometheus': '📊',
    'grafana': '📈', 
    'postgresql': '🐘',
    'mysql': '🐬',
    'mongodb': '🍃',
    'redis': '🔴',
    'rabbitmq': '🐰',
    'kafka': '📡',
    'minio': '🪣',
    'jenkins': '🔧',
    'gitea': '🦆'
  }
  
  const name = appName.toLowerCase()
  for (const [key, icon] of Object.entries(iconMap)) {
    if (name.includes(key) || chart?.toLowerCase().includes(key)) {
      return icon
    }
  }
  return '📦' // default icon
}

const uninstallApp = async (appName: string) => {
  if (!confirm(`Czy na pewno chcesz odinstalować aplikację "${appName}"?`)) {
    return
  }
  
  uninstallingApps.value.push(appName)
  
  try {
    await ApiService.uninstallApp(clusterName, appName)
    
    // Remove from installed apps list
    installedApps.value = installedApps.value.filter(app => app.name !== appName)
    
    // Show success message (you might want to add a notification system)
    alert(`Aplikacja "${appName}" została odinstalowana`)
    
  } catch (err) {
    console.error('Error uninstalling app:', err)
    alert(`Błąd podczas odinstalowywania aplikacji: ${(err as Error).message}`)
  } finally {
    uninstallingApps.value = uninstallingApps.value.filter(name => name !== appName)
  }
}

const refreshData = async () => {
  refreshing.value = true
  await loadClusterDetails()
  await loadInstalledApps() 
  await loadClusterStats()
  refreshing.value = false
}

const goToScaling = () => {
  router.push(`/clusters/${clusterName}/scale`)
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
onMounted(async () => {
  console.log('ClusterDetailsView mounted for:', clusterName)
  await loadClusterDetails()
})
</script>
