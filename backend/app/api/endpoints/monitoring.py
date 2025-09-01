from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from app.services.helm_service import helm_service
import subprocess

router = APIRouter()

@router.post("/install/{cluster_name}")
async def install_monitoring(
    cluster_name: str,
    namespace: str = "monitoring",
    install_prometheus: bool = True,
    install_grafana: bool = True
):
    """
    Zainstaluj stack monitoringu w klastrze
    """
    try:
        # Sprawdź czy klaster istnieje
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", "--context", f"kind-{cluster_name}"
        ], capture_output=True, text=True)
        
        if kubectl_result.returncode != 0:
            raise HTTPException(
                status_code=404,
                detail=f"Klaster {cluster_name} nie istnieje lub nie jest dostępny"
            )
        
        # Zainstaluj monitoring stack
        result = helm_service.install_monitoring_stack(cluster_name, namespace)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
        
        return {
            "cluster_name": cluster_name,
            "namespace": namespace,
            "status": "installed",
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas instalacji: {str(e)}"
        )

@router.get("/status/{cluster_name}")
async def get_monitoring_status(cluster_name: str, namespace: str = "monitoring"):
    """
    Sprawdź status aplikacji monitoringu
    """
    try:
        context = f"kind-{cluster_name}"
        
        # Sprawdź pody w namespace monitoring
        kubectl_result = subprocess.run([
            "kubectl", "get", "pods", 
            "--namespace", namespace,
            "--context", context,
            "-o", "json"
        ], capture_output=True, text=True)
        
        if kubectl_result.returncode != 0:
            return {
                "cluster_name": cluster_name,
                "namespace": namespace,
                "status": "not_installed",
                "message": "Namespace monitoring nie istnieje"
            }
        
        import json
        pods_data = json.loads(kubectl_result.stdout)
        
        prometheus_pods = []
        grafana_pods = []
        
        for pod in pods_data.get("items", []):
            pod_name = pod["metadata"]["name"]
            pod_status = pod["status"]["phase"]
            
            if "prometheus" in pod_name.lower():
                prometheus_pods.append({
                    "name": pod_name,
                    "status": pod_status,
                    "ready": all(
                        container.get("ready", False) 
                        for container in pod["status"].get("containerStatuses", [])
                    )
                })
            elif "grafana" in pod_name.lower():
                grafana_pods.append({
                    "name": pod_name,
                    "status": pod_status,
                    "ready": all(
                        container.get("ready", False) 
                        for container in pod["status"].get("containerStatuses", [])
                    )
                })
        
        # Sprawdź serwisy
        services_result = subprocess.run([
            "kubectl", "get", "svc",
            "--namespace", namespace,
            "--context", context,
            "-o", "json"
        ], capture_output=True, text=True)
        
        services_info = {}
        if services_result.returncode == 0:
            services_data = json.loads(services_result.stdout)
            for svc in services_data.get("items", []):
                svc_name = svc["metadata"]["name"]
                svc_type = svc["spec"]["type"]
                ports = svc["spec"].get("ports", [])
                
                services_info[svc_name] = {
                    "type": svc_type,
                    "ports": [{"port": p.get("port"), "nodePort": p.get("nodePort")} for p in ports]
                }
        
        return {
            "cluster_name": cluster_name,
            "namespace": namespace,
            "status": "running",
            "prometheus": {
                "pods": prometheus_pods,
                "pod_count": len(prometheus_pods),
                "running": len([p for p in prometheus_pods if p["status"] == "Running"])
            },
            "grafana": {
                "pods": grafana_pods,
                "pod_count": len(grafana_pods),
                "running": len([p for p in grafana_pods if p["status"] == "Running"])
            },
            "services": services_info,
            "access_info": {
                "prometheus": "kubectl port-forward svc/prometheus-server 9090:80 -n monitoring",
                "grafana": "kubectl port-forward svc/grafana 3000:80 -n monitoring (admin/admin123)"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas sprawdzania statusu: {str(e)}"
        )

@router.delete("/uninstall/{cluster_name}")
async def uninstall_monitoring(cluster_name: str, namespace: str = "monitoring"):
    """
    Usuń stack monitoringu
    """
    try:
        results = []
        
        # Usuń Grafana
        grafana_result = helm_service.uninstall_release("grafana", cluster_name, namespace)
        results.append({"service": "grafana", **grafana_result})
        
        # Usuń Prometheus  
        prometheus_result = helm_service.uninstall_release("prometheus", cluster_name, namespace)
        results.append({"service": "prometheus", **prometheus_result})
        
        # Usuń namespace (opcjonalnie)
        kubectl_result = subprocess.run([
            "kubectl", "delete", "namespace", namespace,
            "--context", f"kind-{cluster_name}"
        ], capture_output=True, text=True)
        
        return {
            "cluster_name": cluster_name,
            "namespace": namespace,
            "status": "uninstalled",
            "results": results,
            "namespace_deleted": kubectl_result.returncode == 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas usuwania: {str(e)}"
        )

@router.get("/releases/{cluster_name}")
async def list_helm_releases(cluster_name: str, namespace: str = None):
    """
    Lista zainstalowanych Helm releases
    """
    try:
        result = helm_service.list_releases(cluster_name, namespace)
        
        return {
            "cluster_name": cluster_name,
            "namespace": namespace or "all",
            **result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas pobierania listy releases: {str(e)}"
        )