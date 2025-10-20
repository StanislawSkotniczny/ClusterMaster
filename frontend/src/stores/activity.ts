import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ApiService, type ActivityLog } from '@/services/api'

export const useActivityStore = defineStore('activity', () => {
  const logs = ref<ActivityLog[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  let refreshInterval: number | null = null

  const fetchLogs = async (limit: number = 10) => {
    try {
      console.log('🔄 [ActivityStore] Pobieranie activity logs...')
      loading.value = true
      error.value = null
      
      const response = await ApiService.getActivityLog(limit)
      console.log('📊 [ActivityStore] Odpowiedź API:', response)
      
      if (response.success) {
        logs.value = response.logs
        console.log('✅ [ActivityStore] Załadowano', response.logs.length, 'logów')
      } else {
        error.value = response.error || 'Nie udało się pobrać logów aktywności'
        console.error('❌ [ActivityStore] Błąd:', error.value)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Nieznany błąd'
      console.error('❌ [ActivityStore] Wyjątek:', err)
    } finally {
      loading.value = false
    }
  }

  const startAutoRefresh = (intervalMs: number = 3000) => {
    console.log('🔄 [ActivityStore] Uruchamianie auto-refresh co', intervalMs, 'ms')
    
    // Clear existing interval if any
    stopAutoRefresh()
    
    // Initial fetch
    fetchLogs()
    
    // Set up interval
    refreshInterval = window.setInterval(() => {
      fetchLogs()
    }, intervalMs)
  }

  const stopAutoRefresh = () => {
    if (refreshInterval !== null) {
      console.log('⏸️ [ActivityStore] Zatrzymywanie auto-refresh')
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  const $reset = () => {
    logs.value = []
    loading.value = false
    error.value = null
    stopAutoRefresh()
  }

  return {
    logs,
    loading,
    error,
    fetchLogs,
    startAutoRefresh,
    stopAutoRefresh,
    $reset
  }
})
