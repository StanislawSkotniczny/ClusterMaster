<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <button 
          @click="goBack" 
          class="mb-4 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-2"
        >
          ← Powrót do klastra
        </button>
        <div class="flex items-center gap-3 mb-2">
          <h1 class="text-3xl font-bold text-gray-800 dark:text-gray-100">
            Skalowanie Klastra: {{ clusterName }}
          </h1>
          <!-- Provider Badge -->
          <span 
            v-if="clusterProvider === 'k3d'" 
            class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-sm font-semibold"
          >
            🚀 k3d
          </span>
          <span 
            v-else-if="clusterProvider === 'kind'" 
            class="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm font-semibold"
          >
            🔵 kind
          </span>
        </div>
        <p class="text-gray-600 dark:text-gray-400">
          <span v-if="clusterProvider === 'k3d'">
            Zarządzaj liczbą nodów i ich zasobami (Live Scaling - bez utraty danych!)
          </span>
          <span v-else>
            Zarządzaj liczbą nodów i ich zasobami
          </span>
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
        <p class="mt-4 text-gray-600 dark:text-gray-400">Ładowanie konfiguracji klastra...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-6">
        <h3 class="text-red-800 dark:text-red-300 font-semibold mb-2">Błąd</h3>
        <p class="text-red-600 dark:text-red-400">{{ error }}</p>
      </div>

      <!-- Main Content -->
      <div v-else class="space-y-6">
        <!-- Current Configuration Card -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">Aktualna Konfiguracja</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800">
              <div class="text-sm text-blue-600 dark:text-blue-400 font-medium">Control Plane Nodes</div>
              <div class="text-2xl font-bold text-blue-900 dark:text-blue-300 mt-1">{{ currentConfig.controlPlaneNodes }}</div>
            </div>
            <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-100 dark:border-green-800">
              <div class="text-sm text-green-600 dark:text-green-400 font-medium">Worker Nodes</div>
              <div class="text-2xl font-bold text-green-900 dark:text-green-300 mt-1">{{ currentConfig.workerNodes }}</div>
            </div>
            <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-100 dark:border-purple-800">
              <div class="text-sm text-purple-600 dark:text-purple-400 font-medium">Łączna liczba nodów</div>
              <div class="text-2xl font-bold text-purple-900 dark:text-purple-300 mt-1">{{ currentConfig.totalNodes }}</div>
            </div>
          </div>
        </div>

        <!-- Node Scaling Card -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-6">Skalowanie Nodów</h2>
          
          <!-- Worker Nodes Slider -->
          <div class="mb-8">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Liczba Worker Nodes: <span class="text-blue-600 dark:text-blue-400 font-bold">{{ newWorkerNodes }}</span>
            </label>
            <input
              v-model.number="newWorkerNodes"
              type="range"
              min="0"
              max="10"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0</span>
              <span>5</span>
              <span>10</span>
            </div>
            <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">
              <span v-if="workerNodeDiff > 0" class="text-green-600 dark:text-green-400">
                +{{ workerNodeDiff }} {{ workerNodeDiff === 1 ? 'nod' : 'nody' }} zostaną dodane
              </span>
              <span v-else-if="workerNodeDiff < 0" class="text-red-600 dark:text-red-400">
                {{ Math.abs(workerNodeDiff) }} {{ Math.abs(workerNodeDiff) === 1 ? 'nod' : 'nody' }} zostaną usunięte
              </span>
              <span v-else class="text-gray-500 dark:text-gray-400">
                Brak zmian
              </span>
            </div>
          </div>

          <!-- Control Plane Nodes Info -->
          <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-6">
            <div class="flex items-start gap-2">
              <span class="text-yellow-600 dark:text-yellow-400 text-xl">⚠️</span>
              <div>
                <h4 class="font-medium text-yellow-800 dark:text-yellow-300">Control Plane Nodes</h4>
                <p class="text-sm text-yellow-700 dark:text-yellow-400 mt-1">
                  Dla Kind klastrów zalecane jest {{ currentConfig.controlPlaneNodes }} control plane node(y). 
                  Skalowanie control plane wymaga rekonfiguracji klastra.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Node Resources Card -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-6">Zasoby Nodów</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- CPU Configuration -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                CPU na Worker Node
              </label>
              <select 
                v-model="newCpuPerNode"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="1">1 CPU</option>
                <option value="2">2 CPUs</option>
                <option value="4">4 CPUs</option>
                <option value="8">8 CPUs</option>
              </select>
            </div>

            <!-- RAM Configuration -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                RAM na Worker Node
              </label>
              <select 
                v-model="newRamPerNode"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="2048">2 GB</option>
                <option value="4096">4 GB</option>
                <option value="8192">8 GB</option>
                <option value="16384">16 GB</option>
              </select>
            </div>
          </div>

          <div class="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <div class="flex items-start gap-2">
              <span class="text-blue-600 dark:text-blue-400 text-xl">ℹ️</span>
              <div>
                <h4 class="font-medium text-blue-800 dark:text-blue-300">Kind & Docker</h4>
                <p class="text-sm text-blue-700 dark:text-blue-400 mt-1">
                  Zasoby CPU/RAM są limitami dla Docker kontenerów nodów Kind. 
                  Zmiana wymaga recreate nodów.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Preview Changes -->
        <div v-if="hasChanges" class="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-6">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Podgląd Zmian</h3>
          
          <!-- Warning about cluster recreation (Kind only) -->
          <div v-if="clusterProvider === 'kind'" class="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg p-4 mb-4">
            <div class="flex items-start gap-2">
              <span class="text-red-600 dark:text-red-400 text-2xl">⚠️</span>
              <div>
                <h4 class="font-semibold text-red-800 dark:text-red-300">Uwaga: Klaster Kind będzie recreated!</h4>
                <p class="text-sm text-red-700 dark:text-red-400 mt-1">
                  Skalowanie klastra Kind wymaga jego usunięcia i ponownego stworzenia.
                  <strong>Wszystkie deployments i dane w klastrze zostaną utracone!</strong>
                </p>
                <p class="text-sm text-red-600 dark:text-red-400 mt-2 font-medium">
                  Upewnij się że masz backupy przed kontynuowaniem.
                </p>
              </div>
            </div>
          </div>
          
          <!-- Info about k3d live scaling -->
          <div v-else-if="clusterProvider === 'k3d'" class="bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700 rounded-lg p-4 mb-4">
            <div class="flex items-start gap-2">
              <span class="text-green-600 dark:text-green-400 text-2xl">✨</span>
              <div>
                <h4 class="font-semibold text-green-800 dark:text-green-300">k3d: Live Scaling!</h4>
                <p class="text-sm text-green-700 mt-1">
                  Klaster k3d wspiera live scaling - nody będą dodane/usunięte bez recreate.
                  <strong>Twoje deploymenty i dane będą zachowane!</strong>
                </p>
              </div>
            </div>
          </div>
          
          <div class="space-y-2 text-sm">
            <div v-if="workerNodeDiff !== 0" class="flex items-center gap-2">
              <span class="text-2xl">{{ workerNodeDiff > 0 ? '➕' : '➖' }}</span>
              <span class="font-medium">
                Worker Nodes: {{ currentConfig.workerNodes }} → {{ newWorkerNodes }}
              </span>
            </div>
            <div v-if="cpuChanged" class="flex items-center gap-2">
              <span class="text-2xl">🔧</span>
              <span class="font-medium">
                CPU per node: {{ currentConfig.cpuPerNode }} → {{ newCpuPerNode }}
              </span>
            </div>
            <div v-if="ramChanged" class="flex items-center gap-2">
              <span class="text-2xl">💾</span>
              <span class="font-medium">
                RAM per node: {{ formatMemory(currentConfig.ramPerNode) }} → {{ formatMemory(parseInt(newRamPerNode)) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-4">
          <button
            @click="applyChanges"
            :disabled="!hasChanges || applying"
            class="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <span v-if="applying">
              <span class="inline-block animate-spin mr-2">⚙️</span>
              Aplikowanie zmian...
            </span>
            <span v-else>
              Zastosuj Zmiany
            </span>
          </button>
          <button
            @click="resetChanges"
            :disabled="!hasChanges || applying"
            class="px-6 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Reset
          </button>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
          <div class="flex items-center gap-2">
            <span class="text-green-600 dark:text-green-400 text-xl">✅</span>
            <p class="text-green-800 dark:text-green-300 font-medium">{{ successMessage }}</p>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiService } from '@/services/api'

const route = useRoute()
const router = useRouter()

const clusterName = computed(() => route.params.name as string)

// State
const loading = ref(true)
const error = ref<string | null>(null)
const applying = ref(false)
const successMessage = ref<string | null>(null)

// Current Configuration
const currentConfig = ref({
  controlPlaneNodes: 1,
  workerNodes: 2,
  totalNodes: 3,
  cpuPerNode: 2,
  ramPerNode: 4096
})

// Provider info
const clusterProvider = ref<string>('kind') // 'kind' or 'k3d'
const providerInfo = ref<string>('')

// New Configuration
const newWorkerNodes = ref(2)
const newCpuPerNode = ref('2')
const newRamPerNode = ref('4096')

// Computed
const workerNodeDiff = computed(() => newWorkerNodes.value - currentConfig.value.workerNodes)

const cpuChanged = computed(() => parseInt(newCpuPerNode.value) !== currentConfig.value.cpuPerNode)

const ramChanged = computed(() => parseInt(newRamPerNode.value) !== currentConfig.value.ramPerNode)

const hasChanges = computed(() => 
  workerNodeDiff.value !== 0 || cpuChanged.value || ramChanged.value
)

// Methods
function formatMemory(mb: number): string {
  if (mb >= 1024) {
    return `${mb / 1024} GB`
  }
  return `${mb} MB`
}

function goBack() {
  router.push(`/clusters/${clusterName.value}`)
}

function resetChanges() {
  newWorkerNodes.value = currentConfig.value.workerNodes
  newCpuPerNode.value = currentConfig.value.cpuPerNode.toString()
  newRamPerNode.value = currentConfig.value.ramPerNode.toString()
  successMessage.value = null
}

async function loadClusterConfig() {
  try {
    loading.value = true
    error.value = null
    
    const response = await ApiService.getClusterScalingConfig(clusterName.value)
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to load cluster config')
    }
    
    if (response.config) {
      currentConfig.value = {
        controlPlaneNodes: response.config.controlPlaneNodes,
        workerNodes: response.config.workerNodes,
        totalNodes: response.config.totalNodes,
        cpuPerNode: response.config.cpuPerNode,
        ramPerNode: response.config.ramPerNode
      }
      
      // Store provider info
      clusterProvider.value = response.provider || 'kind'
      providerInfo.value = response.info || response.warning || ''
      
      resetChanges()
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Nie udało się załadować konfiguracji klastra'
    error.value = errorMessage
  } finally {
    loading.value = false
  }
}

async function applyChanges() {
  try {
    applying.value = true
    successMessage.value = null
    error.value = null
    
    // Potwierdzenie od użytkownika - różne dla Kind i k3d
    let confirmed = false
    
    if (clusterProvider.value === 'kind') {
      confirmed = confirm(
        '⚠️ UWAGA: Klaster Kind będzie usunięty i stworzony ponownie!\n\n' +
        'Wszystkie deployments, pods i dane w klastrze zostaną utracone.\n\n' +
        'Czy na pewno chcesz kontynuować?'
      )
    } else if (clusterProvider.value === 'k3d') {
      confirmed = confirm(
        '✨ k3d: Live Scaling\n\n' +
        'Nody zostaną dodane/usunięte bez recreate klastra.\n' +
        'Twoje deploymenty będą zachowane!\n\n' +
        'Czy chcesz kontynuować?'
      )
    } else {
      confirmed = confirm('Czy na pewno chcesz zastosować te zmiany?')
    }
    
    if (!confirmed) {
      applying.value = false
      return
    }
    
    const response = await ApiService.applyClusterScaling(clusterName.value, {
      workerNodes: newWorkerNodes.value,
      cpuPerNode: parseInt(newCpuPerNode.value),
      ramPerNode: parseInt(newRamPerNode.value)
    })
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to apply scaling')
    }
    
    // Show operations
    if (response.operations && response.operations.length > 0) {
      console.log('Scaling operations:', response.operations)
    }
    
    // Show warning/info if present
    if (response.warning) {
      console.warn(response.warning)
    }
    if (response.info) {
      console.info(response.info)
    }
    
    // Reload configuration from server
    await loadClusterConfig()
    
    successMessage.value = `✨ ${response.message || 'Klaster został pomyślnie przeskalowany!'}`
    
    if (response.warning) {
      successMessage.value += `\n⚠️ ${response.warning}`
    }
    if (response.info) {
      successMessage.value += `\n✨ ${response.info}`
    }
    
    // Auto-hide success message after 8 seconds
    setTimeout(() => {
      successMessage.value = null
    }, 8000)
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Nie udało się zastosować zmian'
    error.value = errorMessage
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  loadClusterConfig()
})
</script>

<style scoped>
.scale-view {
  padding: 2rem;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Custom slider styling */
.slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  border: none;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}
</style>
