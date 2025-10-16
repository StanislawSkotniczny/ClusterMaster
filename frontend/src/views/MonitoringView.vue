<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center space-x-3">
        <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-3 rounded-xl">
          <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path>
            <path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
            Monitoring Klastrów
          </h1>
          <p class="mt-1 text-gray-600 dark:text-gray-400">
            Zarządzaj monitoringiem swoich klastrów Kubernetes
          </p>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400"></div>
      <span class="ml-3 text-gray-600 dark:text-gray-400">Ładowanie danych klastrów...</span>
    </div>

    <!-- Error state -->
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-300">Błąd</h3>
          <p class="mt-1 text-sm text-red-700 dark:text-red-400">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Actions bar -->
    <div class="mb-6 flex flex-wrap gap-3">
      <button 
        @click="refreshData"
        :disabled="loading"
        class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Odśwież
      </button>
      
      <button 
        @click="showAllPorts = !showAllPorts"
        class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 text-sm font-medium text-white hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 transition-colors"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        {{ showAllPorts ? 'Ukryj' : 'Pokaż' }} wszystkie porty
      </button>
    </div>

    <!-- All ports overview (gdy showAllPorts jest true) -->
    <div v-if="showAllPorts && allPortsData" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 mb-6 transition-all">
        <div class="flex items-center space-x-3 mb-4">
          <div class="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
            <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Przegląd wszystkich portów
            <span class="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">({{ allPortsData.total_clusters }} klastrów)</span>
          </h2>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="(clusterInfo, clusterName) in allPortsData.clusters" 
            :key="clusterName"
            class="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900/50 dark:to-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:shadow-md transition-all"
          >
            <div class="flex items-center space-x-2 mb-3">
              <div class="bg-blue-100 dark:bg-blue-900 p-1.5 rounded-lg">
                <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                </svg>
              </div>
              <h3 class="font-medium text-gray-900 dark:text-gray-100">{{ clusterName }}</h3>
            </div>
            <div class="space-y-2 text-sm">
              <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-2">
                <span class="text-gray-600 dark:text-gray-400">Prometheus:</span>
                <span class="font-mono text-blue-600 dark:text-blue-400">{{ clusterInfo.ports.prometheus }}</span>
              </div>
              <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-2">
                <span class="text-gray-600 dark:text-gray-400">Grafana:</span>
                <span class="font-mono text-blue-600 dark:text-blue-400">{{ clusterInfo.ports.grafana }}</span>
              </div>
              <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-2">
                <span class="text-gray-600 dark:text-gray-400">Port-forward:</span>
                <span class="inline-flex items-center" :class="clusterInfo.port_forward_active ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                  <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path v-if="clusterInfo.port_forward_active" fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    <path v-else fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                  </svg>
                  {{ clusterInfo.port_forward_active ? 'Aktywny' : 'Nieaktywny' }}
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
          :id="cluster.name"
          class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-all"
        >
          <!-- Cluster header -->
          <div class="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                  <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                  </svg>
                </div>
                <div>
                  <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {{ cluster.name }}
                  </h2>
                  <div class="flex items-center mt-1 space-x-2">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Status:</span>
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="cluster.status === 'ready' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300'">
                      <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path v-if="cluster.status === 'ready'" fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        <path v-else fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                      </svg>
                      {{ cluster.status === 'ready' ? 'Gotowy' : 'Inicjalizacja' }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="flex space-x-2">
                <button 
                  @click="refreshClusterStatus(cluster.name)"
                  class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 shadow-sm text-xs font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Odśwież
                </button>
                
                <button 
                  v-if="cluster.monitoring?.installed"
                  @click="openMonitoringUrls(cluster.name)"
                  class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-xs font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 transition-colors"
                >
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                  Otwórz monitoring
                </button>
              </div>
            </div>
          </div>

          <!-- Cluster details -->
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              <!-- Basic info -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800">
                <div class="flex items-center space-x-2 mb-3">
                  <div class="bg-blue-100 dark:bg-blue-900 p-1.5 rounded-lg">
                    <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Informacje podstawowe</h3>
                </div>
                <dl class="space-y-2 text-sm">
                  <div class="flex justify-between items-center">
                    <dt class="text-gray-600 dark:text-gray-400">Węzły:</dt>
                    <dd class="font-medium text-gray-900 dark:text-gray-100">{{ cluster.node_count || 'N/A' }}</dd>
                  </div>
                  <div class="flex justify-between items-center">
                    <dt class="text-gray-600 dark:text-gray-400">Context:</dt>
                    <dd class="font-mono text-xs text-gray-900 dark:text-gray-100">{{ cluster.context || `kind-${cluster.name}` }}</dd>
                  </div>
                  <div v-if="cluster.assigned_ports" class="flex justify-between items-center">
                    <dt class="text-gray-600 dark:text-gray-400">Porty przypisane:</dt>
                    <dd class="inline-flex items-center text-green-600 dark:text-green-400">
                      <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                      </svg>
                      Tak
                    </dd>
                  </div>
                </dl>
              </div>

              <!-- Monitoring info -->
              <div class="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-4 border border-purple-100 dark:border-purple-800">
                <div class="flex items-center space-x-2 mb-3">
                  <div class="bg-purple-100 dark:bg-purple-900 p-1.5 rounded-lg">
                    <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                    </svg>
                  </div>
                  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Monitoring</h3>
                </div>
                <div v-if="cluster.monitoring?.installed" class="space-y-2">
                  <div class="inline-flex items-center text-sm text-green-600 dark:text-green-400 mb-2">
                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                    Zainstalowany
                  </div>
                  
                  <div v-if="cluster.assigned_ports" class="space-y-2 text-sm">
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">Prometheus:</span>
                      <a 
                        :href="`http://localhost:${cluster.assigned_ports.prometheus}`" 
                        target="_blank"
                        class="font-mono text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                      >
                        :{{ cluster.assigned_ports.prometheus }}
                      </a>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">Grafana:</span>
                      <a 
                        :href="`http://localhost:${cluster.assigned_ports.grafana}`" 
                        target="_blank"
                        class="font-mono text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                      >
                        :{{ cluster.assigned_ports.grafana }}
                      </a>
                    </div>
                  </div>
                  
                  <div class="mt-3 text-xs bg-white dark:bg-gray-800 rounded p-2 text-gray-600 dark:text-gray-400">
                    <span class="font-medium">Grafana:</span> admin / admin123
                  </div>
                </div>
                
                <div v-else class="text-sm">
                  <div class="inline-flex items-center text-gray-500 dark:text-gray-400 mb-2">
                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    Nie zainstalowany
                  </div>
                  <button 
                    @click="installMonitoring(cluster.name)"
                    :disabled="installingMonitoring[cluster.name]"
                    class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline disabled:opacity-50 transition-colors"
                  >
                    {{ installingMonitoring[cluster.name] ? 'Instalowanie...' : 'Zainstaluj' }}
                  </button>
                </div>
              </div>

              <!-- Resources info -->
              <div class="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-100 dark:border-green-800">
                <div class="flex items-center space-x-2 mb-3">
                  <div class="bg-green-100 dark:bg-green-900 p-1.5 rounded-lg">
                    <svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Zasoby systemu</h3>
                </div>
                <div v-if="cluster.resources" class="space-y-3">
                  
                  <!-- Jeśli są metryki CPU/RAM w czasie rzeczywistym -->
                  <div v-if="cluster.resources.nodes && cluster.resources.nodes.some(n => n.cpu)" class="space-y-2">
                    <div class="inline-flex items-center text-xs text-green-600 dark:text-green-400 mb-1">
                      <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                      </svg>
                      Metryki na żywo
                    </div>
                    <div v-for="node in cluster.resources.nodes" :key="node.name" class="text-xs bg-white dark:bg-gray-800 rounded-lg p-2">
                      <div class="font-medium text-gray-900 dark:text-gray-100 mb-1">{{ node.name }}</div>
                      <div class="space-y-1">
                        <div class="flex justify-between">
                          <span class="text-gray-600 dark:text-gray-400">CPU:</span>
                          <span class="font-mono text-gray-900 dark:text-gray-100">{{ node.cpu || 'N/A' }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600 dark:text-gray-400">RAM:</span>
                          <span class="font-mono text-gray-900 dark:text-gray-100">{{ node.memory || 'N/A' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Jeśli są metryki Docker stats -->
                  <div v-else-if="cluster.resources.type === 'docker_stats' && cluster.resources.nodes" class="space-y-2">
                    <div class="inline-flex items-center text-xs text-blue-600 dark:text-blue-400 mb-1">
                      <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H6zm1 2a1 1 0 000 2h6a1 1 0 100-2H7zm6 7a1 1 0 011 1v3a1 1 0 11-2 0v-3a1 1 0 011-1zm-3 3a1 1 0 100 2h.01a1 1 0 100-2H10zm-4 1a1 1 0 011-1h.01a1 1 0 110 2H7a1 1 0 01-1-1zm1-4a1 1 0 100 2h.01a1 1 0 100-2H7zm2 1a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1zm4-4a1 1 0 100 2h.01a1 1 0 100-2H13zM9 9a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1zM7 8a1 1 0 000 2h.01a1 1 0 000-2H7z" clip-rule="evenodd"></path>
                      </svg>
                      Docker (na żywo)
                    </div>
                    <div v-for="node in cluster.resources.nodes" :key="node.name" class="text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2">
                      <div class="font-medium text-gray-900 dark:text-gray-100 mb-1">{{ node.name }} <span class="text-gray-500 dark:text-gray-400">({{ node.role }})</span></div>
                      <div class="space-y-1">
                        <div class="flex justify-between">
                          <span class="text-gray-600 dark:text-gray-400">CPU:</span>
                          <span class="font-mono text-blue-600 dark:text-blue-400">{{ node.cpu_usage || 'N/A' }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600 dark:text-gray-400">RAM:</span>
                          <span class="font-mono text-blue-600 dark:text-blue-400">{{ node.memory_usage || 'N/A' }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600 dark:text-gray-400">RAM %:</span>
                          <span class="font-mono text-green-600 dark:text-green-400">{{ node.memory_percent || 'N/A' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Jeśli są rozszerzone informacje (CPU capacity/allocatable) -->
                  <div v-else-if="cluster.resources.type === 'enhanced' && cluster.resources.nodes" class="space-y-1">
                    <div class="text-xs text-blue-600 mb-1">🔧 Informacje szczegółowe</div>
                    <div v-for="node in cluster.resources.nodes" :key="node.name" class="text-xs border rounded p-2">
                      <div class="font-medium text-gray-700 mb-1">{{ node.name }} ({{ node.role }})</div>
                      <div v-if="node.cpu_capacity" class="space-y-1 ml-2">
                        <div class="flex justify-between">
                          <span class="text-gray-500">CPU całkowite:</span>
                          <span class="font-mono">{{ node.cpu_capacity }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-500">CPU dostępne:</span>
                          <span class="font-mono">{{ node.cpu_allocatable }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-500">RAM całkowita:</span>
                          <span class="font-mono">{{ node.memory_capacity }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-500">RAM dostępna:</span>
                          <span class="font-mono">{{ node.memory_allocatable }}</span>
                        </div>
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
              <div class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-4 border border-amber-100 dark:border-amber-800">
                <div class="flex items-center space-x-2 mb-3">
                  <div class="bg-amber-100 dark:bg-amber-900 p-1.5 rounded-lg">
                    <svg class="w-4 h-4 text-amber-600 dark:text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"></path>
                    </svg>
                  </div>
                  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Akcje</h3>
                </div>
                <div class="space-y-2">
                  <button 
                    @click="getMonitoringStatus(cluster.name)"
                    :disabled="loadingStatus[cluster.name]"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-xs font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
                  >
                    <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    {{ loadingStatus[cluster.name] ? 'Sprawdzanie...' : 'Status monitoringu' }}
                  </button>
                  
                  <!-- Port-forward toggle button -->
                  <button 
                    v-if="cluster.monitoring?.installed && allPortsData?.clusters[cluster.name]"
                    @click="togglePortForward(cluster.name, allPortsData.clusters[cluster.name].port_forward_active)"
                    :disabled="portForwardLoading[cluster.name]"
                    :class="allPortsData.clusters[cluster.name].port_forward_active 
                      ? 'border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50'
                      : 'border-green-300 dark:border-green-700 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 hover:bg-green-100 dark:hover:bg-green-900/50'"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border shadow-sm text-xs font-medium rounded-lg disabled:opacity-50 transition-colors"
                  >
                    <svg v-if="portForwardLoading[cluster.name]" class="animate-spin -ml-1 mr-1.5 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <svg v-else-if="allPortsData.clusters[cluster.name].port_forward_active" class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                    <svg v-else class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                    {{ portForwardLoading[cluster.name] 
                      ? 'Ładowanie...' 
                      : allPortsData.clusters[cluster.name].port_forward_active 
                        ? 'Zatrzymaj port-forward' 
                        : 'Uruchom port-forward' 
                    }}
                  </button>
                  
                  <button 
                    v-if="cluster.monitoring?.installed"
                    @click="uninstallMonitoring(cluster.name)"
                    :disabled="uninstallingMonitoring[cluster.name]"
                    class="w-full inline-flex items-center justify-center px-3 py-2 border border-red-300 dark:border-red-700 shadow-sm text-xs font-medium rounded-lg text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 disabled:opacity-50 transition-colors"
                  >
                    <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                    {{ uninstallingMonitoring[cluster.name] ? 'Usuwanie...' : 'Usuń monitoring' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Detailed monitoring status -->
            <div v-if="monitoringDetails[cluster.name]" class="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-2">
                  <div class="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
                    <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Szczegóły monitoringu</h3>
                </div>
                <button
                  @click="delete monitoringDetails[cluster.name]"
                  class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                  </svg>
                  Zwiń
                </button>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Prometheus details -->
                <div class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800">
                  <div class="flex items-center space-x-2 mb-3">
                    <div class="bg-blue-100 dark:bg-blue-900 p-1.5 rounded-lg">
                      <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"></path>
                      </svg>
                    </div>
                    <h4 class="font-semibold text-blue-900 dark:text-blue-300">
                      Prometheus
                      <span class="text-sm font-normal text-blue-700 dark:text-blue-400 ml-1">
                        ({{ monitoringDetails[cluster.name].prometheus.running }}/{{ monitoringDetails[cluster.name].prometheus.pod_count }})
                      </span>
                    </h4>
                  </div>
                  
                  <div class="space-y-2">
                    <div 
                      v-for="pod in monitoringDetails[cluster.name].prometheus.pods" 
                      :key="pod.name"
                      class="flex justify-between items-center text-sm bg-white dark:bg-gray-800 rounded-lg p-2"
                    >
                      <span class="font-mono text-xs text-gray-900 dark:text-gray-100">{{ pod.name }}</span>
                      <span class="inline-flex items-center" :class="getPodStatusColor(pod.status, pod.ready)">
                        <svg v-if="pod.ready" class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                        <svg v-else class="w-4 h-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {{ pod.status }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Grafana details -->
                <div class="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-xl p-4 border border-orange-100 dark:border-orange-800">
                  <div class="flex items-center space-x-2 mb-3">
                    <div class="bg-orange-100 dark:bg-orange-900 p-1.5 rounded-lg">
                      <svg class="w-4 h-4 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path>
                      </svg>
                    </div>
                    <h4 class="font-semibold text-orange-900 dark:text-orange-300">
                      Grafana
                      <span class="text-sm font-normal text-orange-700 dark:text-orange-400 ml-1">
                        ({{ monitoringDetails[cluster.name].grafana.running }}/{{ monitoringDetails[cluster.name].grafana.pod_count }})
                      </span>
                    </h4>
                  </div>
                  
                  <div class="space-y-2">
                    <div 
                      v-for="pod in monitoringDetails[cluster.name].grafana.pods" 
                      :key="pod.name"
                      class="flex justify-between items-center text-sm bg-white dark:bg-gray-800 rounded-lg p-2"
                    >
                      <span class="font-mono text-xs text-gray-900 dark:text-gray-100">{{ pod.name }}</span>
                      <span class="inline-flex items-center" :class="getPodStatusColor(pod.status, pod.ready)">
                        <svg v-if="pod.ready" class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                        <svg v-else class="w-4 h-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {{ pod.status }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Services info -->
              <div v-if="monitoringDetails[cluster.name].services" class="mt-6">
                <div class="flex items-center space-x-2 mb-3">
                  <div class="bg-purple-100 dark:bg-purple-900 p-1.5 rounded-lg">
                    <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <h4 class="font-semibold text-gray-900 dark:text-gray-100">Serwisy</h4>
                </div>
                <div class="bg-gradient-to-br from-gray-50 to-slate-50 dark:from-gray-900/20 dark:to-slate-900/20 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div 
                      v-for="(service, serviceName) in monitoringDetails[cluster.name].services" 
                      :key="serviceName"
                      class="text-sm bg-white dark:bg-gray-800 rounded-lg p-3"
                    >
                      <div class="font-medium text-gray-900 dark:text-gray-100">{{ serviceName }}</div>
                      <div class="text-gray-600 dark:text-gray-400 text-xs mt-1">Type: {{ service.type }}</div>
                      <div v-if="service.ports" class="text-xs text-gray-500 dark:text-gray-500 mt-2">
                        <span class="font-medium">Porty: </span>
                        <span v-for="port in service.ports" :key="port.port" class="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded mr-1">
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
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
            >
              + Utwórz klaster
            </router-link>
          </div>
        </div>
      </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { useClustersStore } from '@/stores/clusters'
import { ApiService } from '@/services/api'

const clustersStore = useClustersStore()

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
const loading = computed(() => clustersStore.isLoading)
const error = ref('')
const clusters = computed(() => clustersStore.clusters)
const monitoringDetails = reactive<Record<string, MonitoringDetail>>({})
const allPortsData = ref<AllPortsData | null>(null)
const showAllPorts = ref(false)

// Loading states for various operations
const loadingStatus = reactive<Record<string, boolean>>({})
const installingMonitoring = reactive<Record<string, boolean>>({})
const uninstallingMonitoring = reactive<Record<string, boolean>>({})
const installingMetrics = reactive<Record<string, boolean>>({})
const portForwardLoading = reactive<Record<string, boolean>>({})

// Methods
const refreshData = async () => {
  error.value = ''
  
  try {
    // Use store clusters - will refresh automatically
    if (clustersStore.clusters.length === 0) {
      await clustersStore.fetchClusters()
    }
    
    // Pobierz informacje o wszystkich portach
    try {
      const portsResponse = await ApiService.getAllClusterPorts()
      allPortsData.value = portsResponse
    } catch (e) {
      console.warn('Nie udało się pobrać informacji o portach:', e)
    }
    
  } catch (e: unknown) {
    error.value = getErrorMessage(e)
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

const openMonitoringUrls = async (clusterName: string) => {
  try {
    // Sprawdź czy port-forward jest aktywny
    const portsData = allPortsData.value?.clusters[clusterName]
    
    if (portsData && !portsData.port_forward_active) {
      // Port-forward nie jest aktywny - zapytaj czy uruchomić
      if (confirm(`Port-forward nie jest uruchomiony!\n\nCzy chcesz automatycznie uruchomić port-forward i otworzyć monitoring?`)) {
        // Uruchom port-forward
        portForwardLoading[clusterName] = true
        try {
          const pfResponse = await ApiService.startPortForward(clusterName)
          if (!pfResponse.success) {
            error.value = `Błąd uruchamiania port-forward: ${pfResponse.error}`
            return
          }
          
          // Odśwież dane portów
          const refreshedPorts = await ApiService.getAllClusterPorts()
          allPortsData.value = refreshedPorts
          
          // Poczekaj chwilę aż port-forward się ustabilizuje
          await new Promise(resolve => setTimeout(resolve, 2000))
          
        } finally {
          portForwardLoading[clusterName] = false
        }
      } else {
        // Użytkownik nie chce uruchamiać port-forward
        return
      }
    }
    
    // Teraz otwórz URL-e
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

const togglePortForward = async (clusterName: string, isActive: boolean) => {
  portForwardLoading[clusterName] = true
  
  try {
    if (isActive) {
      // Stop port-forward
      const response = await ApiService.stopPortForward(clusterName)
      if (response.success) {
        // Refresh ports data to update status
        const portsResponse = await ApiService.getAllClusterPorts()
        allPortsData.value = portsResponse
      } else {
        error.value = `Błąd zatrzymywania port-forward: ${response.error}`
      }
    } else {
      // Start port-forward
      const response = await ApiService.startPortForward(clusterName)
      if (response.success) {
        // Refresh ports data to update status
        const portsResponse = await ApiService.getAllClusterPorts()
        allPortsData.value = portsResponse
        
        // Optionally open URLs
        if (confirm(`Port-forward uruchomiony!\n\nPrometheus: ${response.urls.prometheus}\nGrafana: ${response.urls.grafana}\n\nCzy chcesz otworzyć Prometheus i Grafana w przeglądarce?`)) {
          console.log('Opening Prometheus:', response.urls.prometheus)
          window.open(response.urls.prometheus, '_blank')
          setTimeout(() => {
            console.log('Opening Grafana:', response.urls.grafana)
            window.open(response.urls.grafana, '_blank')
          }, 500)
        }
      } else {
        error.value = `Błąd uruchamiania port-forward: ${response.error}`
      }
    }
  } catch (e: unknown) {
    error.value = `Błąd zarządzania port-forward ${clusterName}: ${getErrorMessage(e)}`
  } finally {
    portForwardLoading[clusterName] = false
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
const getPodStatusColor = (status: string, ready: boolean) => {
  if (status === 'Running' && ready) return 'text-green-600'
  if (status === 'Running' && !ready) return 'text-yellow-600'
  if (status === 'Pending') return 'text-yellow-600'
  return 'text-red-600'
}

// Initialize
onMounted(async () => {
  await refreshData()
  
  // Scroll to cluster if hash is present
  if (window.location.hash) {
    const clusterName = window.location.hash.substring(1) // Remove #
    setTimeout(() => {
      const element = document.getElementById(clusterName)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        // Optional: highlight the card briefly
        element.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.5)'
        setTimeout(() => {
          element.style.boxShadow = ''
        }, 2000)
      }
    }, 500) // Wait for data to load
  }
})
</script>

<style scoped>
/* Dodatkowe style jeśli potrzebne */
</style>
