/**
 * Notifications Store - Real-time notifications via SSE
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Notification {
  id: string
  type: string // operation, alert, info, etc.
  severity: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
  metadata?: {
    cluster?: string
    app_name?: string
    error?: string
    operation_id?: string
    [key: string]: unknown
  }
}

export const useNotificationsStore = defineStore('notifications', () => {
  // State
  const notifications = ref<Notification[]>([])
  const eventSource = ref<EventSource | null>(null)
  const connected = ref(false)
  const loading = ref(false)
  
  // Computed
  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })
  
  const recentNotifications = computed(() => {
    return notifications.value.slice(0, 10)
  })
  
  // Connect to SSE stream
  const connect = (userId: string = 'default_user') => {
    if (eventSource.value) {
      console.log('[Notifications] Already connected')
      return
    }
    
    console.log('[Notifications] Connecting to SSE stream...')
    
    try {
      // Create EventSource connection
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      eventSource.value = new EventSource(`${baseUrl}/api/notifications/stream?user_id=${userId}`)
      
      // Handle connection open
      eventSource.value.onopen = () => {
        connected.value = true
        console.log('[Notifications] SSE connection established')
      }
      
      // Handle notification events
      eventSource.value.addEventListener('notification', (event: MessageEvent) => {
        try {
          const notification = JSON.parse(event.data) as Notification
          console.log('[Notifications] Received notification:', notification)
          
          // Add to beginning of array
          notifications.value.unshift(notification)
          
          // Keep only last 50 notifications
          if (notifications.value.length > 50) {
            notifications.value = notifications.value.slice(0, 50)
          }
          
          // Show browser notification if permitted
          showBrowserNotification(notification)
          
        } catch (error) {
          console.error('[Notifications] Error parsing notification:', error)
        }
      })
      
      // Handle ping/heartbeat
      eventSource.value.addEventListener('ping', () => {
        console.log('[Notifications] Heartbeat received')
      })
      
      // Handle errors
      eventSource.value.onerror = (error) => {
        console.error('[Notifications] SSE error:', error)
        connected.value = false
        
        // Auto-reconnect after 5 seconds
        disconnect()
        setTimeout(() => {
          console.log('[Notifications] Attempting to reconnect...')
          connect(userId)
        }, 5000)
      }
      
    } catch (error) {
      console.error('[Notifications] Error connecting to SSE:', error)
    }
  }
  
  // Disconnect from SSE stream
  const disconnect = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
      connected.value = false
      console.log('[Notifications] SSE connection closed')
    }
  }
  
  // Fetch notification history
  const fetchHistory = async (limit: number = 20) => {
    loading.value = true
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/notifications/history?limit=${limit}`)
      const data = await response.json()
      
      if (data.success) {
        notifications.value = data.notifications
        console.log(`[Notifications] Loaded ${data.notifications.length} notifications from history`)
      }
    } catch (error) {
      console.error('[Notifications] Error fetching history:', error)
    } finally {
      loading.value = false
    }
  }
  
  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/notifications/${notificationId}/read`, {
        method: 'POST'
      })
      
      if (response.ok) {
        // Update locally
        const notification = notifications.value.find(n => n.id === notificationId)
        if (notification) {
          notification.read = true
        }
      }
    } catch (error) {
      console.error('[Notifications] Error marking as read:', error)
    }
  }
  
  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      console.log('[Notifications] Marking all as read...')
      const response = await fetch(`${baseUrl}/api/notifications/read-all`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log('[Notifications] Mark all as read response:', result)
        // Update locally
        notifications.value.forEach(n => n.read = true)
        console.log('[Notifications] All notifications marked as read locally')
      } else {
        console.error('[Notifications] Failed to mark all as read:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('[Notifications] Error marking all as read:', error)
    }
  }
  
  // Show browser notification (if permission granted)
  const showBrowserNotification = (notification: Notification) => {
    if (Notification.permission === 'granted') {
      // Get icon based on severity
      const icon = notification.severity === 'success' ? '✅' :
                   notification.severity === 'error' ? '❌' :
                   notification.severity === 'warning' ? '⚠️' : 'ℹ️'
      
      new Notification(`${icon} ${notification.title}`, {
        body: notification.message,
        icon: '/logo.png',
        tag: notification.id
      })
    }
  }
  
  // Request browser notification permission
  const requestNotificationPermission = async () => {
    if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      console.log('[Notifications] Permission:', permission)
      return permission === 'granted'
    }
    return Notification.permission === 'granted'
  }
  
  // Delete notification
  const deleteNotification = async (notificationId: string) => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/notifications/${notificationId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        // Remove locally
        notifications.value = notifications.value.filter(n => n.id !== notificationId)
        console.log(`[Notifications] Deleted notification ${notificationId}`)
      }
    } catch (error) {
      console.error('[Notifications] Error deleting notification:', error)
    }
  }
  
  return {
    // State
    notifications,
    connected,
    loading,
    
    // Computed
    unreadCount,
    recentNotifications,
    
    // Actions
    connect,
    disconnect,
    fetchHistory,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    requestNotificationPermission
  }
})
