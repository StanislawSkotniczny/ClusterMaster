import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ApiService, type ClusterInfo } from '@/services/api'

export type { ClusterInfo }

export const useClustersStore = defineStore('clusters', () => {
  const clusters = ref<ClusterInfo[]>([])
  const isLoading = ref(false)
  const isRefreshing = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<Date | null>(null)

  // Auto-refresh interval (optional)
  let refreshInterval: number | null = null

  const activeClusters = computed(() => 
    clusters.value.filter(c => c.status === 'running')
  )

  const inactiveClusters = computed(() => 
    clusters.value.filter(c => c.status !== 'running')
  )

  const clusterCount = computed(() => clusters.value.length)

  async function fetchClusters(silent = false) {
    // Use isRefreshing for background updates, isLoading only for initial load
    if (!silent && clusters.value.length === 0) {
      isLoading.value = true
    } else {
      isRefreshing.value = true
    }
    error.value = null

    try {
      const data = await ApiService.getClusters()
      clusters.value = data
      lastUpdate.value = new Date()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch clusters'
      console.error('Error fetching clusters:', err)
      throw err
    } finally {
      isLoading.value = false
      isRefreshing.value = false
    }
  }

  function startAutoRefresh(intervalMs = 10000) {
    if (refreshInterval) {
      stopAutoRefresh()
    }
    
    refreshInterval = window.setInterval(() => {
      // Silent refresh - don't show loading spinner
      fetchClusters(true)
    }, intervalMs)
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  function getClusterByName(name: string) {
    return clusters.value.find(c => c.name === name)
  }

  function updateCluster(name: string, updates: Partial<ClusterInfo>) {
    const index = clusters.value.findIndex(c => c.name === name)
    if (index !== -1) {
      clusters.value[index] = { ...clusters.value[index], ...updates }
    }
  }

  function removeCluster(name: string) {
    clusters.value = clusters.value.filter(c => c.name !== name)
  }

  function $reset() {
    clusters.value = []
    isLoading.value = false
    isRefreshing.value = false
    error.value = null
    lastUpdate.value = null
    stopAutoRefresh()
  }

  return {
    // State
    clusters,
    isLoading,
    isRefreshing,
    error,
    lastUpdate,
    
    // Computed
    activeClusters,
    inactiveClusters,
    clusterCount,
    
    // Actions
    fetchClusters,
    startAutoRefresh,
    stopAutoRefresh,
    getClusterByName,
    updateCluster,
    removeCluster,
    $reset
  }
})
