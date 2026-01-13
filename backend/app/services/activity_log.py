"""
Activity Log Service - logs cluster operations
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class ActivityLogService:
    def __init__(self, log_file: str = "activity_log.json"):
        self.log_file = Path(log_file)
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        if not self.log_file.exists():
            self.log_file.write_text("[]")
    
    def _read_logs(self) -> List[Dict[str, Any]]:
        """Read all logs from file"""
        try:
            return json.loads(self.log_file.read_text())
        except:
            return []
    
    def _write_logs(self, logs: List[Dict[str, Any]]):
        """Write logs to file"""
        self.log_file.write_text(json.dumps(logs, indent=2))
    
    def log_operation(
        self,
        operation_type: str,
        cluster_name: str,
        details: str = "",
        status: str = "success",
        metadata: Dict[str, Any] = None
    ):
        """
        Log a cluster operation
        
        Args:
            operation_type: Type of operation (cluster_create, cluster_delete, monitoring_install, etc.)
            cluster_name: Name of the cluster
            details: Additional details about the operation
            status: success, error, or in-progress
            metadata: Additional metadata (dict)
        
        Returns:
            log_entry with 'id' field for later updates
        """
        logs = self._read_logs()
        
        log_entry = {
            "id": f"{operation_type}_{cluster_name}_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "cluster_name": cluster_name,
            "details": details,
            "status": status,
            "metadata": metadata or {}
        }
        
        logs.insert(0, log_entry)  # Insert at beginning (newest first)
        
        # Keep only last 100 logs
        if len(logs) > 100:
            logs = logs[:100]
        
        self._write_logs(logs)
        return log_entry
    
    def update_operation_status(
        self,
        operation_id: str,
        status: str,
        details: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Update the status of an existing operation
        
        Args:
            operation_id: The ID of the operation to update
            status: New status (success, error, in-progress)
            details: Updated details (optional)
            metadata: Additional metadata to merge (optional)
        """
        logs = self._read_logs()
        
        for log in logs:
            if log.get("id") == operation_id:
                log["status"] = status
                if details:
                    log["details"] = details
                if metadata:
                    log["metadata"].update(metadata)
                log["updated_at"] = datetime.now().isoformat()
                break
        
        self._write_logs(logs)
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent logs"""
        logs = self._read_logs()
        return logs[:limit]
    
    def get_logs_by_cluster(self, cluster_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get logs for specific cluster"""
        logs = self._read_logs()
        cluster_logs = [log for log in logs if log.get("cluster_name") == cluster_name]
        return cluster_logs[:limit]
    
    def clear_old_logs(self, days: int = 30):
        """Clear logs older than specified days"""
        from datetime import timedelta
        
        logs = self._read_logs()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_logs = [
            log for log in logs
            if datetime.fromisoformat(log["timestamp"]) > cutoff_date
        ]
        
        self._write_logs(filtered_logs)
        return len(logs) - len(filtered_logs)  # Return number of deleted logs


# Global instance
activity_log = ActivityLogService()
