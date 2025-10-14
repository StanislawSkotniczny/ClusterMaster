<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">App Store</h1>
      <p class="text-gray-600 dark:text-gray-400">Instaluj aplikacje na swoich klastrach Kubernetes jednym kliknięciem</p>
    </div>

    <!-- Cluster Selection -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Wybierz klaster:</label>
      <div class="relative">
        <select 
          v-model="selectedCluster" 
          class="w-full md:w-1/3 rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500"
          :disabled="isLoadingClusters"
        >
          <option value="">{{ isLoadingClusters ? 'Ładowanie klastrów...' : 'Wybierz klaster...' }}</option>
          <option v-for="cluster in clusters" :key="cluster.name" :value="cluster.name">
            {{ cluster.name }} ({{ cluster.status }})
          </option>
        </select>
        <div v-if="isLoadingClusters" class="absolute right-3 top-1/2 transform -translate-y-1/2">
          <svg class="animate-spin h-5 w-5 text-blue-500 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      </div>
    </div>

    <!-- Search Section -->
    <div v-if="selectedCluster" class="mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
        <span class="text-2xl mr-2">🔍</span>
        Wyszukaj aplikacje w Helm Charts
      </h2>
      <div class="flex gap-3">
        <input
          v-model="searchQuery"
          @keyup.enter="performSearch"
          type="text"
          placeholder="Wpisz nazwę aplikacji (np. nginx, wordpress, jenkins)..."
          class="flex-1 rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
        <button
          @click="performSearch"
          :disabled="searchQuery.length < 2 || isSearching"
          class="px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-md hover:bg-blue-700 dark:hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          <svg v-if="isSearching" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ isSearching ? 'Szukam...' : 'Szukaj' }}</span>
        </button>
      </div>
      
      <!-- Search Results -->
      <div v-if="searchResults.length > 0" class="mt-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
          Znaleziono {{ searchResults.length }} aplikacji
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
          <div
            v-for="chart in searchResults"
            :key="chart.full_name"
            class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex justify-between items-start mb-2">
              <h4 class="font-semibold text-gray-900 dark:text-gray-100">{{ chart.name }}</h4>
              <span class="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 px-2 py-1 rounded">{{ chart.repository }}</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">{{ chart.description || 'Brak opisu' }}</p>
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-3">
              <div>Chart: v{{ chart.version }}</div>
              <div v-if="chart.app_version">App: v{{ chart.app_version }}</div>
            </div>
            <button
              @click="installCustomApp(chart)"
              :disabled="installingApps.includes(chart.full_name)"
              class="w-full px-3 py-2 bg-green-600 dark:bg-green-700 text-white text-sm rounded hover:bg-green-700 dark:hover:bg-green-600 disabled:bg-gray-400 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            >
              {{ installingApps.includes(chart.full_name) ? 'Instaluję...' : '+ Zainstaluj' }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-else-if="searchPerformed && !isSearching" class="mt-4 text-center text-gray-500 dark:text-gray-400">
        Nie znaleziono aplikacji dla zapytania "{{ searchQuery }}"
      </div>
    </div>

    <div v-if="!selectedCluster" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-md p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-blue-400 dark:text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-blue-800 dark:text-blue-300">
            Wybierz klaster aby przeglądać i instalować aplikacje.
          </p>
        </div>
      </div>
    </div>

    <!-- Recommended Apps -->
    <div v-if="selectedCluster" class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
        <span class="text-2xl mr-2">⭐</span>
        Polecane aplikacje
      </h2>
    </div>

    <!-- Apps Grid -->
    <div v-if="selectedCluster" class="space-y-8">
      <!-- Category: Databases -->
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
          <span class="text-2xl mr-2">🗄️</span>
          Bazy danych
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AppCard
            v-for="app in databaseApps"
            :key="app.name"
            :app="app"
            :cluster="selectedCluster"
            :installing="installingApps.includes(app.name)"
            @install="installApp"
          />
        </div>
      </div>

      <!-- Category: Message Brokers -->
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
          <span class="text-2xl mr-2">📨</span>
          Message Brokers
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AppCard
            v-for="app in messageBrokerApps"
            :key="app.name"
            :app="app"
            :cluster="selectedCluster"
            :installing="installingApps.includes(app.name)"
            @install="installApp"
          />
        </div>
      </div>

      <!-- Category: Storage -->
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
          <span class="text-2xl mr-2">💾</span>
          Storage
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AppCard
            v-for="app in storageApps"
            :key="app.name"
            :app="app"
            :cluster="selectedCluster"
            :installing="installingApps.includes(app.name)"
            @install="installApp"
          />
        </div>
      </div>

      <!-- Category: DevOps Tools -->
      <div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
          <span class="text-2xl mr-2">🔧</span>
          DevOps Tools
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AppCard
            v-for="app in devopsApps"
            :key="app.name"
            :app="app"
            :cluster="selectedCluster"
            :installing="installingApps.includes(app.name)"
            @install="installApp"
          />
        </div>
      </div>
    </div>

    <!-- Status Messages -->
    <div v-if="statusMessage" class="fixed bottom-4 right-4 max-w-sm z-50">
      <div class="rounded-md p-4 shadow-lg" 
           :class="statusType === 'success' ? 'bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700' : 'bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700'">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg v-if="statusType === 'success'" class="h-5 w-5 text-green-400 dark:text-green-500" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <svg v-else class="h-5 w-5 text-red-400 dark:text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium" 
               :class="statusType === 'success' ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'">
              {{ statusMessage }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useClustersStore } from '@/stores/clusters'
import { ApiService } from '@/services/api'
import AppCard from '@/components/AppCard.vue'

const clustersStore = useClustersStore()

interface App {
  name: string
  displayName: string
  description: string
  icon: string
  version: string
  namespace: string
  helmChart?: string
  values?: Record<string, unknown>
  installed?: boolean
}

// Reactive data
const selectedCluster = ref('')
const clusters = computed(() => clustersStore.clusters)
const installingApps = ref<string[]>([])
const statusMessage = ref('')
const statusType = ref<'success' | 'error'>('success')
const isLoadingClusters = computed(() => clustersStore.isLoading)

// Search functionality
const searchQuery = ref('')
const searchResults = ref<Array<{
  name: string
  full_name: string
  version: string
  app_version: string
  description: string
  repository: string
}>>([])
const isSearching = ref(false)
const searchPerformed = ref(false)

const performSearch = async () => {
  if (searchQuery.value.length < 2) {
    showStatus('Wpisz co najmniej 2 znaki do wyszukania', 'error')
    return
  }

  isSearching.value = true
  searchPerformed.value = true
  
  try {
    const result = await ApiService.searchHelmCharts(searchQuery.value)
    
    if (result.success) {
      searchResults.value = result.charts
      if (result.charts.length === 0) {
        showStatus(`Nie znaleziono aplikacji dla "${searchQuery.value}"`, 'error')
      } else {
        showStatus(`Znaleziono ${result.charts.length} aplikacji`, 'success')
      }
    } else {
      showStatus(result.error || 'Błąd wyszukiwania', 'error')
      searchResults.value = []
    }
  } catch (error) {
    console.error('Search error:', error)
    showStatus('Błąd podczas wyszukiwania aplikacji', 'error')
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

const installCustomApp = async (chart: typeof searchResults.value[0]) => {
  if (!selectedCluster.value) return
  
  installingApps.value.push(chart.full_name)
  
  try {
    await ApiService.installApp(selectedCluster.value, {
      name: chart.name,
      displayName: chart.name,
      namespace: 'default',
      helmChart: chart.full_name,
      values: {}
    })
    
    showStatus(`${chart.name} rozpoczął instalację na klastrze ${selectedCluster.value}. Instalacja może potrwać kilka minut...`, 'success')
    
    // Remove from search results after successful install
    searchResults.value = searchResults.value.filter(c => c.full_name !== chart.full_name)
    
  } catch (error) {
    console.error('Error installing app:', error)
    showStatus(`Błąd instalacji ${chart.name}: ${(error as Error).message}`, 'error')
  } finally {
    installingApps.value = installingApps.value.filter(name => name !== chart.full_name)
  }
}

// App definitions
const databaseApps = ref<App[]>([
  {
    name: 'postgresql',
    displayName: 'PostgreSQL',
    description: 'Zaawansowana baza danych relacyjna open source',
    icon: '🐘',
    version: '15.4.0',
    namespace: 'databases',
    helmChart: 'bitnami/postgresql',
    values: {
      auth: {
        postgresPassword: 'postgres123',
        database: 'myapp'
      },
      primary: {
        persistence: {
          size: '8Gi'
        }
      }
    }
  },
  {
    name: 'mysql',
    displayName: 'MySQL',
    description: 'Popularna baza danych relacyjna',
    icon: '🐬',
    version: '8.0.34',
    namespace: 'databases',
    helmChart: 'bitnami/mysql',
    values: {
      auth: {
        rootPassword: 'mysql123',
        database: 'myapp'
      },
      primary: {
        persistence: {
          size: '8Gi'
        }
      }
    }
  },
  {
    name: 'mongodb',
    displayName: 'MongoDB',
    description: 'Baza danych dokumentowa NoSQL',
    icon: '🍃',
    version: '7.0.2',
    namespace: 'databases',
    helmChart: 'bitnami/mongodb',
    values: {
      auth: {
        rootPassword: 'mongo123',
        database: 'myapp'
      },
      persistence: {
        size: '8Gi'
      }
    }
  },
  {
    name: 'redis',
    displayName: 'Redis',
    description: 'In-memory baza danych i cache',
    icon: '🔴',
    version: '7.2.1',
    namespace: 'databases',
    helmChart: 'bitnami/redis',
    values: {
      auth: {
        password: 'redis123'
      },
      master: {
        persistence: {
          size: '4Gi'
        }
      }
    }
  }
])

const messageBrokerApps = ref<App[]>([
  {
    name: 'rabbitmq',
    displayName: 'RabbitMQ',
    description: 'Message broker AMQP',
    icon: '🐰',
    version: '3.12.6',
    namespace: 'messaging',
    helmChart: 'bitnami/rabbitmq',
    values: {
      auth: {
        username: 'admin',
        password: 'rabbit123'
      },
      persistence: {
        size: '4Gi'
      }
    }
  },
  {
    name: 'kafka',
    displayName: 'Apache Kafka',
    description: 'Distributed streaming platform',
    icon: '📡',
    version: '3.5.1',
    namespace: 'messaging',
    helmChart: 'bitnami/kafka',
    values: {
      persistence: {
        size: '8Gi'
      },
      zookeeper: {
        persistence: {
          size: '4Gi'
        }
      }
    }
  }
])

const storageApps = ref<App[]>([
  {
    name: 'minio',
    displayName: 'MinIO',
    description: 'S3-compatible object storage',
    icon: '🪣',
    version: '2023.9.16',
    namespace: 'storage',
    helmChart: 'bitnami/minio',
    values: {
      auth: {
        rootUser: 'admin',
        rootPassword: 'minio123'
      },
      persistence: {
        size: '10Gi'
      }
    }
  }
])

const devopsApps = ref<App[]>([
  {
    name: 'jenkins',
    displayName: 'Jenkins',
    description: 'CI/CD automation server',
    icon: '🔧',
    version: '2.414.2',
    namespace: 'devops',
    helmChart: 'jenkins/jenkins',
    values: {
      controller: {
        adminPassword: 'jenkins123',
        persistence: {
          size: '8Gi'
        }
      }
    }
  },
  {
    name: 'gitea',
    displayName: 'Gitea',
    description: 'Lightweight Git service',
    icon: '🦆',
    version: '1.20.4',
    namespace: 'devops',
    helmChart: 'gitea-charts/gitea',
    values: {
      postgresql: {
        enabled: true
      },
      persistence: {
        size: '4Gi'
      }
    }
  }
])

// Load data on mount
onMounted(() => {
  // Use store clusters - will load if not already loaded
  if (clustersStore.clusters.length === 0) {
    clustersStore.fetchClusters()
  }
})

const installApp = async (app: App) => {
  if (!selectedCluster.value) return
  
  installingApps.value.push(app.name)
  
  try {
    await ApiService.installApp(selectedCluster.value, {
      name: app.name,
      displayName: app.displayName,
      namespace: app.namespace,
      helmChart: app.helmChart || '',
      values: app.values || {}
    })
    
    showStatus(`${app.displayName} rozpoczął instalację na klastrze ${selectedCluster.value}. Instalacja może potrwać kilka minut...`, 'success')
    
    // Mark as installed
    app.installed = true
    
  } catch (error) {
    console.error('Error installing app:', error)
    showStatus(`Błąd instalacji ${app.displayName}: ${(error as Error).message}`, 'error')
  } finally {
    installingApps.value = installingApps.value.filter(name => name !== app.name)
  }
}

const showStatus = (message: string, type: 'success' | 'error') => {
  statusMessage.value = message
  statusType.value = type
  
  setTimeout(() => {
    statusMessage.value = ''
  }, 5000)
}

// Load data on mount
onMounted(() => {
  // Use store clusters - will load if not already loaded
  if (clustersStore.clusters.length === 0) {
    clustersStore.fetchClusters()
  }
})
</script>
