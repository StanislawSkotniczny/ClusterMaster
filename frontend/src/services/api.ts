// Serwis do komunikacji z backend API
const API_BASE_URL = 'http://localhost:8000/api/v1'

export interface ClusterCreateRequest {
    cluster_name: string
    node_count: number
    k8s_version?: string
}

export interface ClusterResponse {
    cluster_name: string
    status: string
    message: string
}

export interface ClusterInfo {
    name: string
    status: string
    node_count?: number
    context?: string
    assigned_ports?: {
        prometheus: number
        grafana: number
    }
    monitoring?: {
        installed: boolean
    }
    resources?: {
        node_count: number
        nodes: Array<{
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
        summary: string
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

    static async listClustersDetailed(): Promise<{ clusters: ClusterInfo[] }> {
        return this.request('/local-cluster')
    }

    static async getClusters(): Promise<ClusterInfo[]> {
        const result = await this.listClustersDetailed()
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
}