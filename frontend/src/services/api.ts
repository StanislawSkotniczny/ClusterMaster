// Serwis do komunikacji z backend API
const API_BASE_URL = 'http://localhost:8000/api/v1'

export interface ClusterCreateRequest {
    cluster_name: string
    node_count: number
    k8s_version?: string
}

export interface ClusterResponse {
    cluster_name?: string
    status: string
    message?: string
    error?: string  // Error message if status is 'error'
    provider?: string  // 'kind' or 'k3d'
}

export interface ClusterInfo {
    name: string
    status: string
    provider?: string  // 'kind' or 'k3d'
    node_count?: number
    context?: string
    kubernetes_version?: string  // Wersja Kubernetes
    created_at?: string  // Data utworzenia
    api_endpoint?: string  // Endpoint API
    assigned_ports?: {
        prometheus?: number
        grafana?: number
    }
    monitoring?: {
        installed?: boolean
        enabled?: boolean
    }
    resources?: {
        node_count?: number
        cpu_usage?: number
        memory_usage?: number
        nodes?: Array<{
            name: string
            cpu?: string
            memory?: string
            status?: string
            role?: string
            cpu_capacity?: string
            memory_capacity?: string
            cpu_allocatable?: string
            memory_allocatable?: string
            cpu_usage?: string
            memory_usage?: string
            memory_percent?: string
        }>
        summary?: string
        type?: string
        note?: string
        error?: string
    }
}

export interface BackupInfo {
    backup_name: string
    cluster_name: string
    created_at: string
    size_mb: number
    resources_count: number
    backup_type: string
    file_path: string
    error?: string
}

export interface BackupDetails {
    backup_name: string
    cluster_name: string
    created_at: string
    resources: Array<{
        type: string
        namespace: string | null
        scope: string
    }>
    cluster_info: Record<string, unknown>
    backup_type: string
    file_info: {
        size_mb: number
        file_count: number
        files: string[]
    }
}

export interface ActivityLog {
    id: string
    timestamp: string
    operation_type: string
    cluster_name: string
    details: string
    status: 'success' | 'error' | 'in-progress'
    metadata?: Record<string, unknown>
}

export class ApiService {
    private static async request(endpoint: string, options: RequestInit = {}) {
        const url = `${API_BASE_URL}${endpoint}`

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        return response.json()
    }

    // Health check
    static async healthCheck() {
        return this.request('/health')
    }

    // Klastry lokalne
    static async listClusters(): Promise<{ clusters: string[] }> {
        return this.request('/local-cluster/list')
    }

    static async listClustersDetailed(includeResources: boolean = false): Promise<{ clusters: ClusterInfo[] }> {
        const params = includeResources ? '?include_resources=true' : ''
        return this.request(`/local-cluster${params}`)
    }

    static async getClusters(includeResources: boolean = false): Promise<ClusterInfo[]> {
        const result = await this.listClustersDetailed(includeResources)
        return result.clusters
    }

    static async createCluster(data: ClusterCreateRequest): Promise<ClusterResponse> {
        return this.request('/local-cluster/create', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    }

    static async deleteCluster(clusterName: string): Promise<{ message: string }> {
        return this.request(`/local-cluster/${clusterName}`, {
            method: 'DELETE',
        })
    }

    static async getClusterStatus(clusterName: string) {
        return this.request(`/local-cluster/${clusterName}/status`)
    }

    // Debug endpoints
    static async debugDocker() {
        return this.request('/debug/docker')
    }

    static async debugKind() {
        return this.request('/debug/kind')
    }

    // Monitoring
    static async installMonitoring(clusterName: string) {
        return this.request(`/monitoring/install/${clusterName}`, {
            method: 'POST',
        })
    }

    static async getMonitoringStatus(clusterName: string) {
        return this.request(`/monitoring/status/${clusterName}`)
    }

    static async uninstallMonitoring(clusterName: string) {
        return this.request(`/monitoring/uninstall/${clusterName}`, {
            method: 'DELETE',
        })
    }

    static async getClusterPorts(clusterName: string) {
        return this.request(`/monitoring/ports/${clusterName}`)
    }

    static async getAllClusterPorts() {
        return this.request('/monitoring/ports')
    }

    static async listHelmReleases(clusterName: string, namespace?: string) {
        const endpoint = namespace
            ? `/monitoring/releases/${clusterName}?namespace=${namespace}`
            : `/monitoring/releases/${clusterName}`
        return this.request(endpoint)
    }

    static async installMetricsServer(clusterName: string) {
        return this.request(`/monitoring/install-metrics-server/${clusterName}`, {
            method: 'POST',
        })
    }

    static async startPortForward(clusterName: string) {
        return this.request(`/monitoring/port-forward/start/${clusterName}`, {
            method: 'POST',
        })
    }

    static async stopPortForward(clusterName: string) {
        return this.request(`/monitoring/port-forward/stop/${clusterName}`, {
            method: 'POST',
        })
    }

    // Backup endpoints
    static async getBackupInfo() {
        return this.request('/backup/info')
    }

    static async changeBackupDirectory(directory: string): Promise<{ success: boolean; error?: string; message: string }> {
        return this.request('/backup/change-directory', {
            method: 'POST',
            body: JSON.stringify({ directory }),
        })
    }

    // Apps management
    static async installApp(clusterName: string, appData: {
        name: string
        displayName: string
        namespace: string
        helmChart: string
        values: Record<string, unknown>
    }) {
        return this.request(`/apps/install/${clusterName}`, {
            method: 'POST',
            body: JSON.stringify(appData),
        })
    }

    static async getInstalledApps(clusterName: string) {
        return this.request(`/apps/installed/${clusterName}`)
    }

    static async uninstallApp(clusterName: string, appName: string) {
        return this.request(`/apps/uninstall/${clusterName}/${appName}`, {
            method: 'DELETE',
        })
    }

    static async searchHelmCharts(query: string, maxResults: number = 20): Promise<{
        success: boolean
        charts: Array<{
            name: string
            full_name: string
            version: string
            app_version: string
            description: string
            repository: string
        }>
        count: number
        error?: string
    }> {
        return this.request(`/apps/search?query=${encodeURIComponent(query)}&max_results=${maxResults}`)
    }

    static async createBackup(clusterName: string, backupName?: string): Promise<{ success: boolean; backup_name?: string; error?: string; message: string }> {
        const endpoint = backupName
            ? `/backup/create/${clusterName}?backup_name=${encodeURIComponent(backupName)}`
            : `/backup/create/${clusterName}`
        return this.request(endpoint, {
            method: 'POST',
        })
    }

    static async listBackups(): Promise<{ success: boolean; backups: BackupInfo[]; total_count: number }> {
        return this.request('/backup/list')
    }

    static async getBackupDetails(backupName: string): Promise<{ success: boolean; backup_details?: BackupDetails; error?: string }> {
        return this.request(`/backup/details/${backupName}`)
    }

    static async deleteBackup(backupName: string): Promise<{ success: boolean; error?: string; message: string }> {
        return this.request(`/backup/delete/${backupName}`, {
            method: 'DELETE',
        })
    }

    static async restoreBackup(backupName: string, newClusterName?: string): Promise<{ success: boolean; error?: string; message: string }> {
        const endpoint = newClusterName
            ? `/backup/restore/${backupName}?new_cluster_name=${encodeURIComponent(newClusterName)}`
            : `/backup/restore/${backupName}`
        return this.request(endpoint, {
            method: 'POST',
        })
    }

    static async downloadBackup(backupName: string) {
        const response = await fetch(`${API_BASE_URL}/backup/download/${backupName}`, {
            method: 'GET',
        })

        if (!response.ok) {
            throw new Error(`Download failed: ${response.status} ${response.statusText}`)
        }

        return response.blob()
    }

    // Cluster Scaling
    static async getClusterScalingConfig(clusterName: string): Promise<{
        success: boolean
        provider?: string  // 'kind' or 'k3d'
        config?: {
            controlPlaneNodes: number
            workerNodes: number
            totalNodes: number
            cpuPerNode: number
            ramPerNode: number
        }
        info?: string      // Additional info (e.g., k3d live scaling support)
        warning?: string   // Warnings (e.g., Kind requires recreate)
        error?: string
    }> {
        return this.request(`/clusters/${clusterName}/scaling/config`)
    }

    static async applyClusterScaling(clusterName: string, config: {
        workerNodes: number
        cpuPerNode: number
        ramPerNode: number
    }): Promise<{
        success: boolean
        provider?: string  // 'kind' or 'k3d'
        message?: string
        operations?: string[]
        info?: string      // Success info (e.g., k3d live scaling notice)
        warning?: string   // Warnings (e.g., Kind recreate warning)
        error?: string
    }> {
        return this.request(`/clusters/${clusterName}/scaling/apply`, {
            method: 'POST',
            body: JSON.stringify(config)
        })
    }

    // Activity Log
    static async getActivityLog(limit: number = 20): Promise<{ success: boolean; logs: ActivityLog[]; error?: string }> {
        return this.request(`/activity-log?limit=${limit}`)
    }

    static async getClusterActivityLog(clusterName: string, limit: number = 10): Promise<{ success: boolean; logs: ActivityLog[]; error?: string }> {
        return this.request(`/activity-log/${clusterName}?limit=${limit}`)
    }
}
