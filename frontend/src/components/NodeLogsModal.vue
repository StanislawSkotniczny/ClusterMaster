<template>
  <Teleport to="body">
    <Transition name="modal">
      <div 
        v-if="isOpen"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        
        <!-- Modal Content -->
        <div class="flex min-h-full items-center justify-center p-4">
          <div 
            class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-6xl w-full transform transition-all"
            @click.stop
          >
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-start justify-between">
                <div class="flex items-center space-x-3">
                  <!-- Icon -->
                  <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                    <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                    </svg>
                  </div>
                  
                  <div>
                    <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                      {{ nodeName }}
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      Logi i szczegóły węzła
                    </p>
                  </div>
                </div>
                
                <!-- Close Button -->
                <button
                  @click="closeModal"
                  class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <!-- Tabs -->
            <div class="border-b border-gray-200 dark:border-gray-700">
              <nav class="flex -mb-px px-6" aria-label="Tabs">
                <button
                  v-for="tab in tabs"
                  :key="tab.id"
                  @click="activeTab = tab.id"
                  :class="[
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300',
                    'whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm transition-colors'
                  ]"
                >
                  {{ tab.label }}
                </button>
              </nav>
            </div>
            
            <!-- Body -->
            <div class="px-6 py-6 max-h-[600px] overflow-y-auto">
              <!-- Loading -->
              <div v-if="loading" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
                <span class="ml-3 text-gray-600 dark:text-gray-400">Ładowanie...</span>
              </div>
              
              <!-- Error -->
              <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
                <p class="text-red-800 dark:text-red-300">{{ error }}</p>
              </div>
              
              <!-- Content -->
              <div v-else-if="nodeData">
                <!-- Describe Tab -->
                <div v-if="activeTab === 'describe'">
                  <pre class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">{{ nodeData.describe }}</pre>
                </div>
                
                <!-- Events Tab -->
                <div v-else-if="activeTab === 'events'">
                  <pre class="bg-gray-900 text-yellow-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">{{ nodeData.events }}</pre>
                </div>
                
                <!-- Pods Tab -->
                <div v-else-if="activeTab === 'pods'">
                  <pre class="bg-gray-900 text-cyan-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">{{ nodeData.pods }}</pre>
                </div>
                
                <!-- Conditions Tab -->
                <div v-else-if="activeTab === 'conditions'">
                  <div class="space-y-3">
                    <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Warunki węzła (Node Conditions)</h4>
                    
                    <div v-if="parsedConditions.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div 
                        v-for="condition in parsedConditions" 
                        :key="condition.type"
                        class="p-3 rounded-lg border"
                        :class="getConditionClasses(condition.status)"
                      >
                        <div class="flex items-center justify-between">
                          <span class="font-medium">{{ condition.type }}</span>
                          <span class="text-sm font-semibold" :class="condition.status === 'True' ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                            {{ condition.status }}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div v-else class="text-gray-500 dark:text-gray-400 text-sm">
                      Brak informacji o warunkach węzła
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Footer -->
            <div class="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 rounded-b-2xl flex items-center justify-end gap-3">
              <button
                @click="refreshData"
                :disabled="loading"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                <svg v-if="loading" class="animate-spin h-4 w-4 mr-2 inline" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ loading ? 'Odświeżanie...' : 'Odśwież' }}
              </button>
              <button
                @click="closeModal"
                class="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg text-sm font-medium transition-colors"
              >
                Zamknij
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface Props {
  isOpen: boolean
  clusterName: string
  nodeName: string
}

interface NodeLogsData {
  success: boolean
  node_name: string
  cluster_name: string
  provider: string
  describe: string
  events: string
  pods: string
  conditions: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const nodeData = ref<NodeLogsData | null>(null)
const activeTab = ref('describe')

const tabs = [
  { id: 'describe', label: 'Szczegóły' },
  { id: 'events', label: 'Eventy' },
  { id: 'pods', label: 'Pody' },
  { id: 'conditions', label: 'Warunki' }
]

// Parse conditions from kubectl output
const parsedConditions = computed(() => {
  if (!nodeData.value?.conditions) return []
  
  try {
    const conditionsStr = nodeData.value.conditions
    // Format: "MemoryPressure DiskPressure PIDPressure Ready:False False False True"
    const parts = conditionsStr.split(':')
    if (parts.length === 2) {
      const types = parts[0].trim().split(/\s+/)
      const statuses = parts[1].trim().split(/\s+/)
      
      return types.map((type: string, index: number) => ({
        type,
        status: statuses[index] || 'Unknown'
      }))
    }
  } catch (e) {
    console.error('Error parsing conditions:', e)
  }
  
  return []
})

const getConditionClasses = (status: string) => {
  if (status === 'True') {
    return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700'
  }
  return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
}

const closeModal = () => {
  emit('close')
}

const fetchNodeLogs = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch(`http://localhost:8000/api/v1/local-cluster/${props.clusterName}/nodes/${props.nodeName}/logs`)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    nodeData.value = data
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Nie udało się pobrać logów węzła'
    error.value = errorMessage
    console.error('Error fetching node logs:', err)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchNodeLogs()
}

// Fetch data when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchNodeLogs()
  }
}, { immediate: true })
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: all 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
  opacity: 0;
}
</style>
