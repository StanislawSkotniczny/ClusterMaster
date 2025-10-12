<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow duration-200">
    <div class="p-6">
      <div class="flex items-start justify-between">
        <div class="flex items-center">
          <div class="text-3xl mr-3">{{ app.icon }}</div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ app.displayName }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">v{{ app.version }}</p>
          </div>
        </div>
        <div v-if="app.installed" class="flex-shrink-0">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300">
            Zainstalowana
          </span>
        </div>
      </div>
      
      <p class="mt-3 text-gray-600 dark:text-gray-400 text-sm">{{ app.description }}</p>
      
      <div class="mt-4 flex items-center justify-between">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          <span class="inline-flex items-center">
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
            {{ app.namespace }}
          </span>
        </div>
        
        <button
          @click="$emit('install', app)"
          :disabled="installing || app.installed"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200"
          :class="app.installed 
            ? 'bg-gray-400 dark:bg-gray-700 cursor-not-allowed' 
            : installing 
              ? 'bg-blue-400 dark:bg-blue-600 cursor-not-allowed' 
              : 'bg-blue-600 dark:bg-blue-700 hover:bg-blue-700 dark:hover:bg-blue-600 focus:ring-blue-500'"
        >
          <template v-if="installing">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Instalowanie...
          </template>
          <template v-else-if="app.installed">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Zainstalowana
          </template>
          <template v-else>
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Zainstaluj
          </template>
        </button>
      </div>
      
      <!-- Additional Info -->
      <div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
        <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span v-if="app.helmChart">
            📦 {{ app.helmChart }}
          </span>
          <span class="flex items-center">
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            Helm Chart
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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

interface Props {
  app: App
  cluster: string
  installing: boolean
}

defineProps<Props>()

defineEmits<{
  install: [app: App]
}>()
</script>
