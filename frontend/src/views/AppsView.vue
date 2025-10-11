<template>
  <div class="container mx-auto p-6">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">🏪 App Store</h1>
      <p class="text-gray-600">Instaluj aplikacje na swoich klastrach Kubernetes jednym kliknięciem</p>
    </div>

    <!-- Cluster Selection -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">Wybierz klaster:</label>
      <div class="relative">
        <select 
          v-model="selectedCluster" 
          class="w-full md:w-1/3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          :disabled="isLoadingClusters"
        >
          <option value="">{{ isLoadingClusters ? 'Ładowanie klastrów...' : 'Wybierz klaster...' }}</option>
          <option v-for="cluster in clusters" :key="cluster.name" :value="cluster.name">
            {{ cluster.name }} ({{ cluster.status }})
          </option>
        </select>
        <div v-if="isLoadingClusters" class="absolute right-3 top-1/2 transform -translate-y-1/2">
          <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      </div>
    </div>

    <div v-if="!selectedCluster" class="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-blue-800">
            Wybierz klaster aby przeglądać dostępne aplikacje do instalacji.
          </p>
        </div>
      </div>
    </div>

    <!-- Apps Grid -->
    <div v-if="selectedCluster" class="space-y-8">
      <!-- Category: Databases -->
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
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
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
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
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
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
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
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
    <div v-if="statusMessage" class="fixed bottom-4 right-4 max-w-sm">
      <div class="rounded-md p-4 shadow-lg" 
           :class="statusType === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg v-if="statusType === 'success'" class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <svg v-else class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium" 
               :class="statusType === 'success' ? 'text-green-800' : 'text-red-800'">
              {{ statusMessage }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ApiService, type ClusterInfo } from '@/services/api'
import AppCard from '@/components/AppCard.vue'

// Types
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
const clusters = ref<ClusterInfo[]>([])
const installingApps = ref<string[]>([])
const statusMessage = ref('')
const statusType = ref<'success' | 'error'>('success')
const isLoadingClusters = ref(false)

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

// Methods
const loadClusters = async () => {
  isLoadingClusters.value = true
  try {
    // Szybkie ładowanie bez szczegółów o zasobach (Docker stats)
    clusters.value = await ApiService.getClusters(false)
  } catch (error) {
    console.error('Error loading clusters:', error)
  } finally {
    isLoadingClusters.value = false
  }
}

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
    
    showStatus(`${app.displayName} został zainstalowany na klastrze ${selectedCluster.value}!`, 'success')
    
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
  loadClusters()
})
</script>
