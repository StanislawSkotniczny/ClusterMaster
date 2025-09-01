<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Nagłówek z nawigacją -->
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
          </nav>
          
          <div class="flex items-center space-x-4">
            <span class="text-gray-600 hidden lg:inline">{{ clusters.length }} klastrów</span>
          </div>
        </div>
      </div>
    </header>
    
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">
          🖥️ Monitoring Klastrów
        </h1>
        <p class="mt-2 text-gray-600">
          Zarządzaj monitoringiem swoich klastrów Kubernetes
        </p>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Ładowanie danych klastrów...</span>
      </div>

      <!-- Error state -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Błąd</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Actions bar -->
      <div class="mb-6 flex flex-wrap gap-3">
        <button 
          @click="refreshData"
          :disabled="loading"
          class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          Odśwież
        </button>
        
        <button 
          @click="showAllPorts = !showAllPorts"
          class="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md shadow-sm bg-blue-50 text-sm font-medium text-blue-700 hover:bg-blue-100"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          {{ showAllPorts ? 'Ukryj' : 'Pokaż' }} wszystkie porty
        </button>
      </div>

      <!-- All ports overview (gdy showAllPorts jest true) -->
      <div v-if="showAllPorts && allPortsData" class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">
          📊 Przegląd wszystkich portów ({{ allPortsData.total_clusters }} klastrów)
        </h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="(clusterInfo, clusterName) in allPortsData.clusters" 
            :key="clusterName"
            class="border border-gray-200 rounded-lg p-4"
          >
            <h3 class="font-medium text-gray-900 mb-2">{{ clusterName }}</h3>
            <div class="space-y-1 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Prometheus:</span>
                <span class="font-mono text-blue-600">{{ clusterInfo.ports.prometheus }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Grafana:</span>
                <span class="font-mono text-blue-600">{{ clusterInfo.ports.grafana }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Port-forward:</span>
                <span :class="clusterInfo.port_forward_active ? 'text-green-600' : 'text-red-600'">
                  {{ clusterInfo.port_forward_active ? '✅ Aktywny' : '❌ Nieaktywny' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Clusters list -->
      <div v-if="!loading" class="space-y-6">
        <div 
          v-for="cluster in clusters" 
          :key="cluster.name"
          class="bg-white rounded-lg shadow-md overflow-hidden"
        >
          <!-- Cluster header -->
          <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-xl font-semibold text-gray-900">
                  🏗️ {{ cluster.name }}
                </h2>
                <p class="text-sm text-gray-500 mt-1">
                  Status: 
                  <span :class="getStatusColor(cluster.status)">
                    {{ cluster.status === 'ready' ? '✅ Gotowy' : '⏳ Inicjalizacja' }}
                  </span>
                </p>
              </div>
              
              <div class="flex space-x-2">
                <button 
                  @click="refreshClusterStatus(cluster.name)"
                  class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                >
                  🔄 Odśwież
                </button>
                
                <button 
                  v-if="cluster.monitoring?.installed"
                  @click="openMonitoringUrls(cluster.name)"
                  class="inline-flex items-center px-3 py-1.5 border border-blue-300 shadow-sm text-xs font-medium rounded text-blue-700 bg-blue-50 hover:bg-blue-100"
                >
                  📊 Otwórz monitoring
                </button>
              </div>
            </div>
          </div>

          <!-- Cluster details -->
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              <!-- Basic info -->
              <div>
                <h3 class="text-sm font-medium text-gray-900 mb-2">Informacje podstawowe</h3>
                <dl class="space-y-1 text-sm">
                  <div class="flex justify-between">
                    <dt class="text-gray-500">Węzły:</dt>
                    <dd class="font-medium">{{ cluster.node_count || 'N/A' }}</dd>
                  </div>
                  <div class="flex justify-between">
                    <dt class="text-gray-500">Context:</dt>
                    <dd class="font-mono text-xs">{{ cluster.context || `kind-${cluster.name}` }}</dd>
                  </div>
                  <div v-if="cluster.assigned_ports" class="flex justify-between">
                    <dt class="text-gray-500">Porty przypisane:</dt>
                    <dd class="text-green-600">✅ Tak</dd>
                  </div>
                </dl>
              </div>

              <!-- Monitoring info -->
              <div>
                <h3 class="text-sm font-medium text-gray-900 mb-2">Monitoring</h3>
                <div v-if="cluster.monitoring?.installed" class="space-y-2">
                  <div class="text-sm text-green-600 mb-2">✅ Zainstalowany</div>
                  
                  <div v-if="cluster.assigned_ports" class="space-y-1 text-sm">
                    <div class="flex justify-between">
                      <span class="text-gray-500">Prometheus:</span>
                      <a 
                        :href="`http://localhost:${cluster.assigned_ports.prometheus}`" 
                        target="_blank"
                        class="font-mono text-blue-600 hover:text-blue-800"
                      >
                        :{{ cluster.assigned_ports.prometheus }}
                      </a>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-500">Grafana:</span>
                      <a 
                        :href="`http://localhost:${cluster.assigned_ports.grafana}`" 
                        target="_blank"
                        class="font-mono text-blue-600 hover:text-blue-800"
                      >
                        :{{ cluster.assigned_ports.grafana }}
                      </a>
                    </div>
                  </div>
                  
                  <div class="mt-2 text-xs text-gray-500">
                    Grafana: admin / admin123
                  </div>
                </div>
                
                <div v-else class="text-sm text-gray-500">
                  ❌ Nie zainstalowany
                  <button 
                    @click="installMonitoring(cluster.name)"
                    :disabled="installingMonitoring[cluster.name]"
                    class="ml-2 text-blue-600 hover:text-blue-800 underline disabled:opacity-50"
                  >
                    {{ installingMonitoring[cluster.name] ? 'Instalowanie...' : 'Zainstaluj' }}
                  </button>
                </div>
              </div>

              <!-- Resources info -->
              <div>
                <h3 class="text-sm font-medium text-gray-900 mb-2">Zasoby systemu</h3>
                <div v-if="cluster.resources" class="space-y-2">
                  
                  <!-- Jeśli są metryki CPU/RAM -->
                  <div v-if="cluster.resources.nodes && cluster.resources.nodes.some(n => n.cpu)" class="space-y-1">
                    <div v-for="node in cluster.resources.nodes" :key="node.name" class="text-xs">
                      <div class="font-medium text-gray-700">{{ node.name }}:</div>
                      <div class="flex justify-between ml-2">
                        <span class="text-gray-500">CPU:</span>
                        <span class="font-mono">{{ node.cpu || 'N/A' }}</span>
                      </div>
                      <div class="flex justify-between ml-2">
                        <span class="text-gray-500">RAM:</span>
                        <span class="font-mono">{{ node.memory || 'N/A' }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Jeśli tylko podstawowe info -->
                  <div v-else-if="cluster.resources.nodes" class="space-y-1">
                    <div class="text-sm text-gray-600 mb-1">{{ cluster.resources.summary }}</div>
                    <div v-for="node in cluster.resources.nodes" :key="node.name" class="text-xs flex justify-between">
                      <span class="font-mono">{{ node.name }}</span>
                      <span class="text-gray-500">{{ node.role || 'worker' }}</span>
                    </div>
                    <div v-if="cluster.resources.note" class="text-xs text-yellow-600 mt-1">
                      ⚠️ {{ cluster.resources.note }}
                      <button 
                        @click="installMetricsServer(cluster.name)"
                        :disabled="installingMetrics[cluster.name]"
                        class="ml-2 text-blue-600 hover:text-blue-800 underline disabled:opacity-50"
                      >
                        {{ installingMetrics[cluster.name] ? 'Instalowanie...' : 'Zainstaluj metrics-server' }}
                      </button>
                    </div>
                  </div>
                  
                  <!-- Jeśli błąd -->
                  <div v-else-if="cluster.resources.error" class="text-xs text-red-600">
                    ❌ {{ cluster.resources.error }}
                  </div>
                  
                </div>
                <div v-else class="text-sm text-gray-500">
                  ❓ Brak danych o zasobach
                </div>
              </div>

              <!-- Actions -->
              <div>
                <h3 class="text-sm font-medium text-gray-900 mb-2">Akcje</h3>
                <div class="space-y-2">
                  <button 
                    @click="getMonitoringStatus(cluster.name)"
                    :disabled="loadingStatus[cluster.name]"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    {{ loadingStatus[cluster.name] ? 'Sprawdzanie...' : '📈 Status monitoringu' }}
                  </button>
                  
                  <button 
                    v-if="cluster.monitoring?.installed"
                    @click="uninstallMonitoring(cluster.name)"
                    :disabled="uninstallingMonitoring[cluster.name]"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border border-red-300 shadow-sm text-xs font-medium rounded text-red-700 bg-red-50 hover:bg-red-100 disabled:opacity-50"
                  >
                    {{ uninstallingMonitoring[cluster.name] ? 'Usuwanie...' : '🗑️ Usuń monitoring' }}
                  </button>
                  
                  <button 
                    @click="deleteCluster(cluster.name)"
                    :disabled="deletingCluster[cluster.name]"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border border-red-600 shadow-sm text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
                  >
                    {{ deletingCluster[cluster.name] ? 'Usuwanie...' : '💀 Usuń klaster' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Detailed monitoring status -->
            <div v-if="monitoringDetails[cluster.name]" class="mt-6 border-t border-gray-200 pt-6">
              <h3 class="text-lg font-medium text-gray-900 mb-4">📊 Szczegóły monitoringu</h3>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Prometheus details -->
                <div class="bg-blue-50 rounded-lg p-4">
                  <h4 class="font-medium text-blue-900 mb-2">
                    🔍 Prometheus
                    <span class="text-sm font-normal">
                      ({{ monitoringDetails[cluster.name].prometheus.running }}/{{ monitoringDetails[cluster.name].prometheus.pod_count }} running)
                    </span>
                  </h4>
                  
                  <div class="space-y-2">
                    <div 
                      v-for="pod in monitoringDetails[cluster.name].prometheus.pods" 
                      :key="pod.name"
                      class="flex justify-between items-center text-sm"
                    >
                      <span class="font-mono text-xs">{{ pod.name }}</span>
                      <span :class="getPodStatusColor(pod.status, pod.ready)">
                        {{ pod.status }} {{ pod.ready ? '✅' : '⏳' }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Grafana details -->
                <div class="bg-orange-50 rounded-lg p-4">
                  <h4 class="font-medium text-orange-900 mb-2">
                    📈 Grafana
                    <span class="text-sm font-normal">
                      ({{ monitoringDetails[cluster.name].grafana.running }}/{{ monitoringDetails[cluster.name].grafana.pod_count }} running)
                    </span>
                  </h4>
                  
                  <div class="space-y-2">
                    <div 
                      v-for="pod in monitoringDetails[cluster.name].grafana.pods" 
                      :key="pod.name"
                      class="flex justify-between items-center text-sm"
                    >
                      <span class="font-mono text-xs">{{ pod.name }}</span>
                      <span :class="getPodStatusColor(pod.status, pod.ready)">
                        {{ pod.status }} {{ pod.ready ? '✅' : '⏳' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Services info -->
              <div v-if="monitoringDetails[cluster.name].services" class="mt-4">
                <h4 class="font-medium text-gray-900 mb-2">🔗 Serwisy</h4>
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div 
                      v-for="(service, serviceName) in monitoringDetails[cluster.name].services" 
                      :key="serviceName"
                      class="text-sm"
                    >
                      <div class="font-medium text-gray-900">{{ serviceName }}</div>
                      <div class="text-gray-600">Type: {{ service.type }}</div>
                      <div v-if="service.ports" class="text-xs text-gray-500 mt-1">
                        Porty: 
                        <span v-for="port in service.ports" :key="port.port" class="font-mono">
                          {{ port.port }}{{ port.nodePort ? `:${port.nodePort}` : '' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="clusters.length === 0" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Brak klastrów</h3>
          <p class="mt-1 text-sm text-gray-500">Utwórz pierwszy klaster aby zobaczyć jego monitoring</p>
          <div class="mt-6">
            <router-link 
              to="/deploy" 
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              ➕ Utwórz klaster
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ApiService, type ClusterInfo } from '@/services/api'

// Additional Types
interface PodInfo {
  name: string
  status: string
  ready: boolean
}

interface ServiceInfo {
  type: string
  ports: Array<{
    port: number
    nodePort?: number
  }>
}

interface MonitoringDetail {
  prometheus: {
    pods: PodInfo[]
    pod_count: number
    running: number
  }
  grafana: {
    pods: PodInfo[]
    pod_count: number
    running: number
  }
  services: Record<string, ServiceInfo>
}

interface AllPortsData {
  total_clusters: number
  clusters: Record<string, {
    ports: {
      prometheus: number
      grafana: number
    }
    urls: {
      prometheus_url: string
      grafana_url: string
    }
    port_forward_active: boolean
  }>
}

interface ApiError {
  response?: {
    data?: {
      detail?: string
    }
  }
  message?: string
}

// Helper function for error handling
const getErrorMessage = (e: unknown): string => {
  const error = e as ApiError
  return error.response?.data?.detail || error.message || 'Nieznany błąd'
}

// Reactive data
const loading = ref(true)
const error = ref('')
const clusters = ref<ClusterInfo[]>([])
const monitoringDetails = reactive<Record<string, MonitoringDetail>>({})
const allPortsData = ref<AllPortsData | null>(null)
const showAllPorts = ref(false)

// Loading states for various operations
const loadingStatus = reactive<Record<string, boolean>>({})
const installingMonitoring = reactive<Record<string, boolean>>({})
const uninstallingMonitoring = reactive<Record<string, boolean>>({})
const deletingCluster = reactive<Record<string, boolean>>({})
const installingMetrics = reactive<Record<string, boolean>>({})

// Methods
const refreshData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Pobierz szczegółowe informacje o klastrach
    const clustersResponse = await ApiService.listClustersDetailed()
    clusters.value = clustersResponse.clusters || []
    
    // Pobierz informacje o wszystkich portach
    try {
      const portsResponse = await ApiService.getAllClusterPorts()
      allPortsData.value = portsResponse
    } catch (e) {
      console.warn('Nie udało się pobrać informacji o portach:', e)
    }
    
  } catch (e: unknown) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

const refreshClusterStatus = async (clusterName: string) => {
  try {
    const response = await ApiService.getClusterStatus(clusterName)
    
    // Zaktualizuj klaster w liście
    const clusterIndex = clusters.value.findIndex(c => c.name === clusterName)
    if (clusterIndex !== -1) {
      clusters.value[clusterIndex] = { ...clusters.value[clusterIndex], ...response }
    }
  } catch (e: unknown) {
    error.value = `Błąd odświeżania ${clusterName}: ${getErrorMessage(e)}`
  }
}

const getMonitoringStatus = async (clusterName: string) => {
  loadingStatus[clusterName] = true
  
  try {
    const response = await ApiService.getMonitoringStatus(clusterName)
    monitoringDetails[clusterName] = response
  } catch (e: unknown) {
    error.value = `Błąd pobierania statusu monitoringu ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    loadingStatus[clusterName] = false
  }
}

const installMonitoring = async (clusterName: string) => {
  installingMonitoring[clusterName] = true
  
  try {
    const response = await ApiService.installMonitoring(clusterName)
    
    // Zaktualizuj informacje o klastrze
    const clusterIndex = clusters.value.findIndex(c => c.name === clusterName)
    if (clusterIndex !== -1) {
      clusters.value[clusterIndex].monitoring = { installed: true }
    }
    
    // Odśwież dane portów
    await refreshData()
    
    alert(`Monitoring zainstalowany pomyślnie!\nPrometheus: http://localhost:${response.access_info?.assigned_ports?.prometheus}\nGrafana: http://localhost:${response.access_info?.assigned_ports?.grafana}`)
    
  } catch (e: unknown) {
    error.value = `Błąd instalacji monitoringu ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    installingMonitoring[clusterName] = false
  }
}

const uninstallMonitoring = async (clusterName: string) => {
  if (!confirm(`Czy na pewno chcesz usunąć monitoring z klastra ${clusterName}?`)) {
    return
  }
  
  uninstallingMonitoring[clusterName] = true
  
  try {
    await ApiService.uninstallMonitoring(clusterName)
    
    // Zaktualizuj informacje o klastrze
    const clusterIndex = clusters.value.findIndex(c => c.name === clusterName)
    if (clusterIndex !== -1) {
      clusters.value[clusterIndex].monitoring = { installed: false }
    }
    
    // Usuń szczegóły monitoringu
    delete monitoringDetails[clusterName]
    
    // Odśwież dane
    await refreshData()
    
  } catch (e: unknown) {
    error.value = `Błąd usuwania monitoringu ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    uninstallingMonitoring[clusterName] = false
  }
}

const deleteCluster = async (clusterName: string) => {
  if (!confirm(`Czy na pewno chcesz usunąć cały klaster ${clusterName}? Ta operacja jest nieodwracalna!`)) {
    return
  }
  
  deletingCluster[clusterName] = true
  
  try {
    await ApiService.deleteCluster(clusterName)
    
    // Usuń klaster z listy
    clusters.value = clusters.value.filter(c => c.name !== clusterName)
    delete monitoringDetails[clusterName]
    
    // Odśwież dane portów
    await refreshData()
    
  } catch (e: unknown) {
    error.value = `Błąd usuwania klastra ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    deletingCluster[clusterName] = false
  }
}

const openMonitoringUrls = async (clusterName: string) => {
  try {
    const response = await ApiService.getClusterPorts(clusterName)
    const urls = response.urls
    
    if (urls) {
      // Otwórz Prometheus
      window.open(urls.prometheus_url, '_blank')
      // Otwórz Grafana
      setTimeout(() => {
        window.open(urls.grafana_url, '_blank')
      }, 500)
    }
  } catch (e: unknown) {
    error.value = `Błąd otwierania monitoringu ${clusterName}: ${getErrorMessage(e)}`
  }
}

const installMetricsServer = async (clusterName: string) => {
  installingMetrics[clusterName] = true
  
  try {
    const response = await ApiService.installMetricsServer(clusterName)
    
    if (response.success) {
      alert(`${response.message}\n\n${response.note}`)
      // Odśwież dane po 5 sekundach
      setTimeout(() => {
        refreshData()
      }, 5000)
    } else {
      error.value = `Błąd instalacji metrics-server: ${response.error}`
    }
    
  } catch (e: unknown) {
    error.value = `Błąd instalacji metrics-server ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    installingMetrics[clusterName] = false
  }
}

// Helper functions
const getStatusColor = (status: string) => {
  switch(status) {
    case 'ready': return 'text-green-600'
    case 'running': return 'text-green-600'
    case 'pending': return 'text-yellow-600'
    case 'error': return 'text-red-600'
    default: return 'text-gray-600'
  }
}

const getPodStatusColor = (status: string, ready: boolean) => {
  if (status === 'Running' && ready) return 'text-green-600'
  if (status === 'Running' && !ready) return 'text-yellow-600'
  if (status === 'Pending') return 'text-yellow-600'
  return 'text-red-600'
}

// Initialize
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
/* Dodatkowe style jeśli potrzebne */
</style>
