<template>
  <!-- Success Notification -->
  <div 
    v-if="showSuccessNotification"
    class="fixed top-20 right-4 bg-green-500 dark:bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-sm animate-slide-in"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <span class="text-sm font-medium">Sukces!</span>
      </div>
      <button 
        @click="showSuccessNotification = false"
        class="text-white hover:text-gray-200 transition-colors"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    </div>
    <p class="text-sm mt-1">{{ successMessage }}</p>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div v-if="authStore.user" class="space-y-6">
        
        <!-- Statystyki -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Aktywne klastry -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Aktywne klastry</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ clusterDetails.length }}</p>
              </div>
              <div class="bg-blue-100 dark:bg-blue-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Dostępne zasoby -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Dostępne zasoby</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ totalNodesCount }}</p>
              </div>
              <div class="bg-green-100 dark:bg-green-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V8z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Zadania -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Zadania</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ activeTasksCount }}</p>
              </div>
              <div class="bg-purple-100 dark:bg-purple-900 p-3 rounded-lg">
                <svg class="w-6 h-6 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>

        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Klastry lokalne -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <div class="flex items-center space-x-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Klastry lokalne</h3>
                <svg 
                  v-if="clustersStore.isRefreshing" 
                  class="animate-spin h-4 w-4 text-blue-500 dark:text-blue-400" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <button 
                @click="loadClusters" 
                class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
                :disabled="loading"
              >
                {{ loading ? 'Ładowanie...' : 'Odśwież' }}
              </button>
            </div>
            <div class="p-6">
              <div v-if="loading" class="text-gray-500 dark:text-gray-400 text-center py-8">
                <svg class="animate-spin h-8 w-8 text-blue-500 dark:text-blue-400 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-sm">Ładowanie klastrów...</p>
              </div>
              <div v-else-if="localClusters.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-8">
                <svg class="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <p class="text-sm font-medium mb-1">Brak klastrów lokalnych</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Utwórz pierwszy klaster aby rozpocząć</p>
              </div>
              <ul v-else class="space-y-3">
                <li 
                  v-for="cluster in localClusters" 
                  :key="cluster.name" 
                  class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors group"
                >
                  <div class="flex items-center space-x-3">
                    <div class="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
                      <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="flex items-center space-x-2">
                        <span class="font-medium text-gray-900 dark:text-white">{{ cluster.name }}</span>
                        <span v-if="cluster.provider === 'k3d'" class="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">
                          🚀 k3d
                        </span>
                        <span v-else class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">
                          🔵 kind
                        </span>
                      </div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ cluster.node_count || 0 }} nodes</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium">
                      Aktywny
                    </span>
                    <router-link 
                      :to="`/clusters/${cluster.name}`"
                      class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Szczegóły →
                    </router-link>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <!-- Ostatnie operacje -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <div class="flex items-center space-x-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Ostatnie operacje</h3>
                <svg 
                  v-if="activityStore.loading" 
                  class="animate-spin h-4 w-4 text-blue-500 dark:text-blue-400" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <button 
                @click="activityStore.fetchLogs()" 
                class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
                :disabled="activityStore.loading"
              >
                {{ activityStore.loading ? 'Ładowanie...' : 'Odśwież' }}
              </button>
            </div>
            <div class="p-6 space-y-3">
              <!-- Activity logs -->
              <div 
                v-for="log in activityStore.logs.slice(0, 5)" 
                :key="log.id"
                @click="openLogDetails(log)"
                :class="[
                  'p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md',
                  log.status === 'success' ? 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-100 dark:border-green-800 hover:border-green-200 dark:hover:border-green-700' :
                  log.status === 'error' ? 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 border-red-100 dark:border-red-800 hover:border-red-200 dark:hover:border-red-700' :
                  'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-100 dark:border-blue-800 hover:border-blue-200 dark:hover:border-blue-700'
                ]"
              >
                <div class="flex items-start justify-between">
                  <div class="flex items-start space-x-3">
                    <div 
                      :class="[
                        'p-2 rounded-lg mt-0.5',
                        log.status === 'success' ? 'bg-green-100 dark:bg-green-900' :
                        log.status === 'error' ? 'bg-red-100 dark:bg-red-900' :
                        'bg-blue-100 dark:bg-blue-900'
                      ]"
                    >
                      <!-- Show spinner for in-progress operations -->
                      <svg 
                        v-if="log.status === 'in-progress'"
                        class="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin" 
                        xmlns="http://www.w3.org/2000/svg" 
                        fill="none" 
                        viewBox="0 0 24 24"
                      >
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <!-- Show icon for completed operations -->
                      <svg 
                        v-else
                        class="w-4 h-4"
                        :class="[
                          log.status === 'success' ? 'text-green-600 dark:text-green-400' :
                          'text-red-600 dark:text-red-400'
                        ]"
                        fill="none" 
                        stroke="currentColor" 
                        stroke-width="2" 
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" :d="getOperationIcon(log.operation_type)"></path>
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-white">
                        {{ getOperationDisplayName(log.operation_type) }}
                        <span v-if="log.status === 'in-progress'" class="inline-flex items-center ml-2">
                          <span class="flex h-2 w-2">
                            <span class="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75"></span>
                            <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                          </span>
                        </span>
                      </p>
                      <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                        Klaster: <span class="font-semibold">{{ log.cluster_name }}</span>
                      </p>
                      <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        {{ log.details }}
                      </p>
                    </div>
                  </div>
                  <div class="flex flex-col items-end space-y-1">
                    <span 
                      :class="[
                        'px-2.5 py-1 text-xs rounded-full font-medium flex items-center space-x-1',
                        log.status === 'success' ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' :
                        log.status === 'error' ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300' :
                        'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      ]"
                    >
                      <span>{{ log.status === 'success' ? 'Sukces' : log.status === 'error' ? 'Błąd' : 'W toku' }}</span>
                      <svg v-if="log.status === 'in-progress'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                      </svg>
                    </span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                      {{ formatRelativeTime(log.timestamp) }}
                    </span>
                    <!-- Click indicator -->
                    <span class="text-xs text-gray-400 dark:text-gray-500 flex items-center space-x-1 mt-1">
                      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                      </svg>
                      <span>Kliknij</span>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Empty state -->
              <div 
                v-if="activityStore.logs.length === 0 && !activityStore.loading"
                class="text-center py-8 text-gray-500 dark:text-gray-400"
              >
                <svg class="w-10 h-10 text-gray-400 dark:text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                </svg>
                <p class="text-sm font-medium mb-1">Brak operacji</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Historia operacji pojawi się tutaj</p>
              </div>

              <!-- Loading state -->
              <div 
                v-if="activityStore.logs.length === 0 && activityStore.loading"
                class="text-center py-8"
              >
                <svg class="animate-spin h-8 w-8 text-blue-500 dark:text-blue-400 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-sm text-gray-500 dark:text-gray-400">Ładowanie operacji...</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Klastry AWS (EKS) -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
          <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
            <div class="flex items-center space-x-2">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Klastry AWS (EKS)</h3>
              <svg 
                v-if="awsLoading" 
                class="animate-spin h-4 w-4 text-orange-500 dark:text-orange-400" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span v-if="awsStore.isConnected" class="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded-full">
                ✓ Połączono
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <button 
                v-if="!awsStore.isConnected"
                @click="showAwsCredentialsForm = !showAwsCredentialsForm" 
                class="text-sm px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors"
              >
                {{ showAwsCredentialsForm ? 'Ukryj' : 'Połącz z AWS' }}
              </button>
              <button 
                v-else
                @click="loadAwsClusters" 
                :disabled="awsLoading"
                class="text-sm px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
              >
                {{ awsLoading ? 'Ładowanie...' : 'Odśwież' }}
              </button>
              <button 
                v-if="awsStore.isConnected"
                @click="awsStore.clearCredentials(); awsClusters = []" 
                class="text-sm px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
                title="Wyloguj z AWS"
              >
                ✕
              </button>
            </div>
          </div>
          
          <!-- AWS Credentials Form -->
          <div v-if="showAwsCredentialsForm" class="p-6 bg-gray-50 dark:bg-gray-900 border-b border-gray-100 dark:border-gray-700">
            <div class="max-w-2xl">
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Wprowadź swoje credentials AWS. Będą zapisane w sesji do momentu wylogowania.
              </p>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Region</label>
                  <select 
                    v-model="awsCredentialsForm.region"
                    class="w-full rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  >
                    <option value="us-east-1">us-east-1 (N. Virginia)</option>
                    <option value="eu-central-1">eu-central-1 (Frankfurt)</option>
                    <option value="eu-west-1">eu-west-1 (Ireland)</option>
                    <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Access Key ID</label>
                  <input 
                    v-model="awsCredentialsForm.awsAccessKey"
                    type="text"
                    placeholder="AKIAIOSFODNN7EXAMPLE"
                    class="w-full rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Secret Access Key</label>
                  <input 
                    v-model="awsCredentialsForm.awsSecretKey"
                    type="password"
                    placeholder="wJalrXUtnFEMI/K7MDENG..."
                    class="w-full rounded-md bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <button 
                @click="loadAwsClusters"
                :disabled="!awsCredentialsForm.awsAccessKey || !awsCredentialsForm.awsSecretKey || awsLoading"
                class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
              >
                {{ awsLoading ? 'Ładowanie...' : 'Pokaż klastry' }}
              </button>
            </div>
          </div>

          <!-- AWS Clusters List -->
          <div class="p-6">
            <ul v-if="awsClusters.length > 0" class="space-y-3">
              <li 
                v-for="cluster in awsClusters" 
                :key="cluster.name"
                class="flex items-center justify-between p-4 bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 rounded-lg border border-orange-100 dark:border-orange-800 hover:shadow-md transition-all group"
              >
                <div class="flex items-center space-x-3">
                  <div class="bg-orange-100 dark:bg-orange-900 p-2 rounded-lg">
                    <svg class="w-5 h-5 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="flex items-center space-x-2">
                      <span class="font-semibold text-gray-900 dark:text-white">{{ cluster.name }}</span>
                      <span class="text-xs bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 px-2 py-0.5 rounded">EKS</span>
                      <span class="text-xs text-gray-500 dark:text-gray-400" v-if="cluster.kubernetes_version">v{{ cluster.kubernetes_version }}</span>
                    </div>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Region: {{ awsStore.currentRegion }}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <span 
                    :class="[
                      'px-2.5 py-1 text-xs rounded-full font-medium',
                      cluster.status === 'ACTIVE' ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' : 
                      cluster.status === 'CREATING' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' :
                      'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300'
                    ]"
                  >
                    {{ cluster.status }}
                  </span>
                  <router-link 
                    :to="`/clusters/${cluster.name}?provider=eks&region=${awsStore.currentRegion}`"
                    class="text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Szczegóły →
                  </router-link>
                </div>
              </li>
            </ul>

            <!-- Empty state -->
            <div v-else-if="!showAwsCredentialsForm" class="text-center py-8">
              <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"></path>
              </svg>
              <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Brak połączenia z AWS</h3>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Kliknij "Połącz z AWS" aby zobaczyć swoje klastry EKS
              </p>
            </div>

            <div v-else-if="awsClusters.length === 0 && !awsLoading" class="text-center py-8">
              <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
              </svg>
              <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Brak klastrów EKS</h3>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Nie znaleziono żadnych klastrów w regionie {{ awsStore.currentRegion }}
              </p>
            </div>
          </div>
        </div>

        <!-- Status monitoringu klastrów -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-all">
          <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
            <div class="flex items-center space-x-2">
              <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
              </svg>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Status monitoringu</h3>
            </div>
            <router-link 
              to="/monitoring"
              class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
            >
              Zobacz monitoring
            </router-link>
          </div>
          <div class="p-6">
            <div v-if="clusterDetails.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg class="w-10 h-10 text-gray-400 dark:text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              <p class="text-sm">Brak klastrów do monitorowania</p>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div 
                v-for="cluster in clusterDetails" 
                :key="`mon-status-${cluster.name}`"
                class="bg-gradient-to-br from-gray-50 to-slate-50 dark:from-gray-900/50 dark:to-slate-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all"
              >
                <div class="flex items-start justify-between mb-3">
                  <div class="flex items-center space-x-2">
                    <div class="bg-blue-100 dark:bg-blue-900 p-1.5 rounded-lg">
                      <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4z"></path>
                      </svg>
                    </div>
                    <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ cluster.name }}</h4>
                  </div>
                  <span 
                    v-if="cluster.monitoring?.installed"
                    class="flex items-center space-x-1 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full font-medium"
                  >
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                    <span>Aktywny</span>
                  </span>
                  <span 
                    v-else
                    class="flex items-center space-x-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded-full font-medium"
                  >
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <span>Brak</span>
                  </span>
                </div>
                <div v-if="cluster.monitoring?.installed" class="space-y-2 text-xs">
                  <div class="flex items-center justify-between text-gray-600 dark:text-gray-400">
                    <span class="flex items-center space-x-1">
                      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"></path>
                      </svg>
                      <span>Prometheus</span>
                    </span>
                    <span class="font-mono text-blue-600 dark:text-blue-400">
                      {{ cluster.assigned_ports?.prometheus || 'N/A' }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-gray-600 dark:text-gray-400">
                    <span class="flex items-center space-x-1">
                      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                      </svg>
                      <span>Grafana</span>
                    </span>
                    <span class="font-mono text-blue-600 dark:text-blue-400">
                      {{ cluster.assigned_ports?.grafana || 'N/A' }}
                    </span>
                  </div>
                </div>
                <div v-else class="text-xs text-gray-500 dark:text-gray-400 text-center py-2">
                  Monitoring nie został zainstalowany
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
  </main>

  <!-- Log Details Modal -->
  <div 
    v-if="showLogDetailsModal && selectedLog"
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
    @click.self="closeLogDetails"
  >
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div 
            :class="[
              'p-2 rounded-lg',
              selectedLog.status === 'success' ? 'bg-green-100 dark:bg-green-900' :
              selectedLog.status === 'error' ? 'bg-red-100 dark:bg-red-900' :
              'bg-blue-100 dark:bg-blue-900'
            ]"
          >
            <svg 
              class="w-5 h-5"
              :class="[
                selectedLog.status === 'success' ? 'text-green-600 dark:text-green-400' :
                selectedLog.status === 'error' ? 'text-red-600 dark:text-red-400' :
                'text-blue-600 dark:text-blue-400'
              ]"
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" :d="getOperationIcon(selectedLog.operation_type)"></path>
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ getOperationDisplayName(selectedLog.operation_type) }}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ formatRelativeTime(selectedLog.timestamp) }}
            </p>
          </div>
        </div>
        <button 
          @click="closeLogDetails"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
        <!-- Status Badge -->
        <div class="mb-4">
          <span 
            :class="[
              'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
              selectedLog.status === 'success' ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' :
              selectedLog.status === 'error' ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300' :
              'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
            ]"
          >
            {{ selectedLog.status === 'success' ? '✓ Sukces' : selectedLog.status === 'error' ? '✗ Błąd' : '⟳ W toku' }}
          </span>
        </div>

        <!-- Cluster Info -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Klaster</label>
          <p class="text-gray-900 dark:text-white font-mono">{{ selectedLog.cluster_name }}</p>
        </div>

        <!-- Details -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Szczegóły</label>
          <p class="text-gray-900 dark:text-white">{{ selectedLog.details }}</p>
        </div>

        <!-- Timestamp -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Znacznik czasu</label>
          <p class="text-gray-900 dark:text-white font-mono text-sm">{{ new Date(selectedLog.timestamp).toLocaleString('pl-PL') }}</p>
        </div>

        <!-- Metadata (Error Log for failed operations) -->
        <div v-if="selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0" class="mb-4">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ selectedLog.status === 'error' ? '🔴 Logi z błędu' : '📋 Szczegółowe informacje' }}
          </label>
          <div 
            class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700 space-y-3"
          >
            <!-- Error message (highlighted) -->
            <div v-if="selectedLog.status === 'error' && selectedLog.metadata.error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p class="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">❌ Błąd:</p>
              <pre class="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap font-mono leading-relaxed">{{ selectedLog.metadata.error }}</pre>
            </div>

            <!-- Command output (stdout/stderr) -->
            <div v-if="selectedLog.metadata.output" class="p-3 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path>
                </svg>
                Logi z klastra:
              </p>
              <pre class="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto">{{ selectedLog.metadata.output }}</pre>
            </div>

            <!-- Command executed -->
            <div v-if="selectedLog.metadata.command" class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p class="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-2 flex items-center">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                </svg>
                Wykonana komenda:
              </p>
              <pre class="text-xs text-blue-800 dark:text-blue-300 whitespace-pre-wrap font-mono bg-white dark:bg-gray-900 p-2 rounded">{{ selectedLog.metadata.command }}</pre>
            </div>

            <!-- Additional metadata fields (human-readable) -->
            <div v-if="hasAdditionalMetadata()" class="space-y-2">
              <div v-for="(value, key) in getDisplayableMetadata()" :key="key" class="flex justify-between items-start text-sm">
                <span class="font-medium text-gray-600 dark:text-gray-400 capitalize">{{ formatMetadataKey(key) }}:</span>
                <span class="text-gray-900 dark:text-white font-mono text-right ml-2">{{ formatMetadataValue(value) }}</span>
              </div>
            </div>

            <!-- Raw JSON (collapsed by default) -->
            <details class="text-sm">
              <summary class="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white font-medium py-2">
                📄 Pokaż surowe dane (JSON)
              </summary>
              <pre class="mt-2 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono bg-white dark:bg-gray-950 p-3 rounded border border-gray-200 dark:border-gray-700 max-h-64 overflow-y-auto">{{ JSON.stringify(selectedLog.metadata, null, 2) }}</pre>
            </details>
          </div>
        </div>

        <!-- Operation ID -->
        <div class="text-xs text-gray-500 dark:text-gray-400">
          ID operacji: <span class="font-mono">{{ selectedLog.id }}</span>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
        <button 
          @click="closeLogDetails"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
        >
          Zamknij
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useClustersStore } from '../stores/clusters'
import { useActivityStore } from '../stores/activity'
import { useAwsStore } from '../stores/aws'
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted, computed, onUnmounted } from 'vue'
import type { ActivityLog } from '../services/api'

const authStore = useAuthStore()
const clustersStore = useClustersStore()
const activityStore = useActivityStore()
const awsStore = useAwsStore()
const router = useRouter()
const route = useRoute()
const showSuccessNotification = ref(false)
const successMessage = ref("")
const showLogDetailsModal = ref(false)
const selectedLog = ref<ActivityLog | null>(null)

// AWS EKS state
const awsLoading = ref(false)
const showAwsCredentialsForm = ref(false)
const awsCredentialsForm = ref({
  region: awsStore.currentRegion || 'us-east-1',
  awsAccessKey: '',
  awsSecretKey: ''
})

// Use store data
const clusterDetails = computed(() => clustersStore.clusters)
const loading = computed(() => clustersStore.isLoading)

// Separate local and AWS clusters
const localClusters = computed(() => 
  clustersStore.clusters.filter(c => c.provider === 'kind' || c.provider === 'k3d')
)

const awsClusters = computed(() => 
  clustersStore.clusters.filter(c => c.provider === 'eks')
)

// Computed properties for statistics
const totalNodesCount = computed(() => {
  return clusterDetails.value.reduce((sum, cluster) => sum + (cluster.node_count || 0), 0)
})

// Count active tasks (operations in progress)
const activeTasksCount = computed(() => {
  let count = 0
  // Count clusters with monitoring being installed/uninstalled
  clusterDetails.value.forEach(cluster => {
    if (cluster.monitoring?.installed) count++
  })
  // Could add more: backups in progress, deployments, etc.
  return count
})

// Helper functions for metadata display
const hasAdditionalMetadata = () => {
  if (!selectedLog.value?.metadata) return false
  const excludeKeys = ['error', 'output', 'command']
  return Object.keys(selectedLog.value.metadata).some(key => !excludeKeys.includes(key))
}

const getDisplayableMetadata = () => {
  if (!selectedLog.value?.metadata) return {}
  const excludeKeys = ['error', 'output', 'command']
  const displayable: Record<string, unknown> = {}
  
  Object.entries(selectedLog.value.metadata).forEach(([key, value]) => {
    if (!excludeKeys.includes(key)) {
      displayable[key] = value
    }
  })
  
  return displayable
}

const formatMetadataKey = (key: string): string => {
  // Convert snake_case to Title Case
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const formatMetadataValue = (value: unknown): string => {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'boolean') return value ? 'Tak' : 'Nie'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

// Open log details modal
const openLogDetails = (log: ActivityLog) => {
  selectedLog.value = log
  showLogDetailsModal.value = true
}

// Close log details modal
const closeLogDetails = () => {
  showLogDetailsModal.value = false
  selectedLog.value = null
}

// Format timestamp to relative time
const formatRelativeTime = (timestamp: string): string => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'przed chwilą'
  if (diffMins < 60) return `${diffMins} min temu`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h temu`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d temu`
}

// Get icon for operation type
const getOperationIcon = (operationType: string) => {
  const icons: Record<string, string> = {
    cluster_create: 'M12 4v16m8-8H4',
    cluster_delete: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
    cluster_scale: 'M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4',
    monitoring_install: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    monitoring_uninstall: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    backup_create: 'M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4',
    app_install: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12',
    app_uninstall: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10',
  }
  return icons[operationType] || 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
}

// Get operation display name
const getOperationDisplayName = (operationType: string): string => {
  const names: Record<string, string> = {
    cluster_create: 'Utworzenie klastra',
    cluster_delete: 'Usunięcie klastra',
    cluster_scale: 'Skalowanie klastra',
    monitoring_install: 'Instalacja monitoringu',
    monitoring_uninstall: 'Odinstalowanie monitoringu',
    backup_create: 'Utworzenie backupu',
    app_install: 'Instalacja aplikacji',
    app_uninstall: 'Odinstalowanie aplikacji',
  }
  return names[operationType] || operationType
}

onMounted(async () => {
  // Check for success message from deployment
  if (route.query.success === 'cluster_created') {
    showSuccessNotification.value = true
    successMessage.value = route.query.message as string || "Klaster został utworzony pomyślnie!"
    
    // Clear query params
    router.replace({ query: {} })
    
    setTimeout(() => {
      showSuccessNotification.value = false
    }, 5000)
  }
  
  // Load clusters if not already loaded (App.vue handles auto-refresh)
  if (clustersStore.clusters.length === 0) {
    await clustersStore.fetchClusters()
  }
  
  // Auto-load AWS clusters if credentials are available
  if (awsStore.hasCredentials) {
    await loadAwsClusters()
  }
  
  // Start activity logs auto-refresh (persists across navigation)
  activityStore.startAutoRefresh(3000)
})

onUnmounted(() => {
  // Stop auto-refresh when leaving the page
  activityStore.stopAutoRefresh()
})

const loadClusters = async () => {
  try {
    console.log("Ładowanie klastrów...")
    await clustersStore.fetchClusters()
    console.log("Otrzymane szczegóły klastrów:", clustersStore.clusters)
  } catch (error) {
    console.error('Błąd ładowania klastrów:', error)
  }
}

// Load AWS EKS clusters
const loadAwsClusters = async () => {
  // Use credentials from form on first login, otherwise from store
  const accessKey = awsCredentialsForm.value.awsAccessKey || awsStore.credentials?.accessKey
  const secretKey = awsCredentialsForm.value.awsSecretKey || awsStore.credentials?.secretKey
  const region = awsCredentialsForm.value.region || awsStore.currentRegion
  
  if (!accessKey || !secretKey) {
    return
  }
  
  // Save credentials to store
  awsStore.setCredentials(region, accessKey, secretKey)
  
  // Hide form after successful connection
  showAwsCredentialsForm.value = false
  
  awsLoading.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/eks-cluster/list', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        region: region,
        aws_access_key: accessKey,
        aws_secret_key: secretKey
      })
    })
    
    const data = await response.json()
    
    console.log('AWS EKS Response:', data)
    
    if (data.success && data.clusters) {
      // Add EKS clusters to clusters store with provider='eks'
      const eksClusters = data.clusters.map((cluster: any) => ({
        name: cluster.name,
        provider: 'eks',
        status: cluster.status === 'ACTIVE' ? 'Running' : cluster.status,
        region: cluster.region,
        endpoint: cluster.endpoint,
        kubernetes_version: cluster.version,
        node_count: cluster.nodegroups?.[0]?.desiredSize || 0,
        monitoring: {
          installed: false // EKS monitoring is separate
        }
      }))
      
      // Update clusters store - remove old EKS clusters and add new ones
      clustersStore.clusters = [
        ...clustersStore.clusters.filter(c => c.provider !== 'eks'),
        ...eksClusters
      ]
      
      console.log('Added EKS clusters to store:', eksClusters)
    } else {
      console.error('Failed to load EKS clusters:', data.error)
      alert('Błąd podczas ładowania klastrów EKS: ' + (data.error || 'Nieznany błąd'))
    }
   
  } catch (error) {
    console.error('Błąd ładowania klastrów AWS:', error)
    alert('Błąd połączenia z AWS. Sprawdź swoje credentials.')
  } finally {
    awsLoading.value = false
  }
}
</script>

<style scoped>
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
</style>
