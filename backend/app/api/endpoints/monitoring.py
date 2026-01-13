from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from app.services.helm_service import helm_service
from app.services.port_manager import port_manager
import subprocess
import os

router = APIRouter()

@router.post("/install/{cluster_name}")
async def install_monitoring(
    cluster_name: str,
    namespace: str = "monitoring",
    install_prometheus: bool = True,
    install_grafana: bool = True
):
    """
    Zainstaluj stack monitoringu w klastrze (EKS, k3d, kind)
    """
    try:
        # Sprawdź czy klaster istnieje - wykryj automatycznie typ
        from app.services.helm_service import get_cluster_context_for_helm
        
        try:
            context, provider = get_cluster_context_for_helm(cluster_name)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Nie znaleziono klastra {cluster_name}: {str(e)}"
            )
        
        # Sprawdź czy możemy połączyć się z klastrem
        kubectl_result = subprocess.run([
            "kubectl", "get", "nodes", "--context", context
        ], capture_output=True, text=True, timeout=30)
        
        if kubectl_result.returncode != 0:
            raise HTTPException(
                status_code=404,
                detail=f"Klaster {cluster_name} nie jest dostępny ({provider})"
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
    Sprawdź status aplikacji monitoringu (EKS, k3d, kind)
    """
    try:
        # Wykryj typ klastra
        from app.services.helm_service import get_cluster_context_for_helm
        
        try:
            context, provider = get_cluster_context_for_helm(cluster_name)
        except Exception:
            context = f"kind-{cluster_name}"
            provider = "kind"
        
        # Dla EKS sprawdź CloudWatch add-on
        if provider == "eks":
            from app.services.eks_service import eks_service
            credentials = eks_service.get_cluster_credentials(cluster_name)
            
            if credentials:
                region = credentials["region"]
                env = os.environ.copy()
                env.update({
                    "AWS_ACCESS_KEY_ID": credentials["aws_access_key"],
                    "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_key"],
                    "AWS_DEFAULT_REGION": region
                })
                
                # Sprawdź CloudWatch Observability add-on
                check_addon = subprocess.run(
                    ["aws", "eks", "describe-addon",
                     "--cluster-name", cluster_name,
                     "--addon-name", "amazon-cloudwatch-observability",
                     "--region", region,
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                if check_addon.returncode == 0:
                    import json
                    addon_data = json.loads(check_addon.stdout)
                    addon_status = addon_data.get("addon", {}).get("status", "UNKNOWN")
                    
                    container_insights_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#container-insights:infrastructure"
                    logs_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups"
                    
                    return {
                        "cluster_name": cluster_name,
                        "provider": "eks",
                        "status": "installed" if addon_status == "ACTIVE" else "installing",
                        "addon_status": addon_status,
                        "monitoring": {
                            "installed": addon_status == "ACTIVE",
                            "cloudwatch_url": container_insights_url,
                            "logs_url": logs_url
                        },
                        "message": f"CloudWatch Observability: {addon_status}"
                    }
                else:
                    return {
                        "cluster_name": cluster_name,
                        "provider": "eks",
                        "status": "not_installed",
                        "monitoring": {
                            "installed": False
                        },
                        "message": "CloudWatch Observability nie jest zainstalowany"
                    }
        
        # Sprawdź pody w namespace monitoring
        kubectl_result = subprocess.run([
            "kubectl", "get", "pods", 
            "--namespace", namespace,
            "--context", context,
            "-o", "json"
        ], capture_output=True, text=True, timeout=30)
        
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
            "provider": provider,
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
            "port_info": port_manager.get_cluster_urls(cluster_name),
            "access_info": {
                "note": f"Dostęp przez kubectl port-forward ({provider})",
                "check_ports": f"/api/v1/monitoring/ports/{cluster_name}"
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
    Usuń stack monitoringu (EKS, k3d, kind)
    """
    try:
        # Wykryj typ klastra
        from app.services.helm_service import get_cluster_context_for_helm
        
        try:
            context, provider = get_cluster_context_for_helm(cluster_name)
        except Exception:
            context = f"kind-{cluster_name}"
            provider = "kind"
        
        results = []
        
        # Usuń Grafana
        grafana_result = helm_service.uninstall_release("grafana", cluster_name, namespace, context)
        results.append({"service": "grafana", **grafana_result})
        
        # Usuń Prometheus  
        prometheus_result = helm_service.uninstall_release("prometheus", cluster_name, namespace, context)
        results.append({"service": "prometheus", **prometheus_result})
        
        # Wyczyść zasoby klastra (port-forward i porty)
        cleanup_result = helm_service.cleanup_cluster_resources(cluster_name)
        
        # Usuń namespace (opcjonalnie)
        kubectl_result = subprocess.run([
            "kubectl", "delete", "namespace", namespace,
            "--context", context
        ], capture_output=True, text=True, timeout=60)
        
        return {
            "cluster_name": cluster_name,
            "namespace": namespace,
            "status": "uninstalled",
            "results": results,
            "cleanup": cleanup_result,
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

@router.get("/ports/{cluster_name}")
async def get_cluster_ports(cluster_name: str):
    """
    Pobierz informacje o portach dla klastra
    """
    try:
        monitoring_info = helm_service.get_cluster_monitoring_info(cluster_name)
        
        if not monitoring_info:
            raise HTTPException(
                status_code=404,
                detail=f"Klaster {cluster_name} nie ma przypisanych portów"
            )
        
        return monitoring_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas pobierania portów: {str(e)}"
        )

@router.get("/ports")
async def list_all_cluster_ports():
    """
    Lista wszystkich przypisanych portów dla wszystkich klastrów
    """
    try:
        assignments = port_manager.list_all_assignments()
        
        # Dodaj informacje o URL-ach dla każdego klastra
        enriched_assignments = {}
        for cluster_name, ports in assignments.items():
            urls = port_manager.get_cluster_urls(cluster_name)
            enriched_assignments[cluster_name] = {
                "ports": ports,
                "urls": urls,
                "port_forward_active": cluster_name in helm_service.port_forward_threads
            }
        
        return {
            "total_clusters": len(assignments),
            "clusters": enriched_assignments
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas pobierania listy portów: {str(e)}"
        )

@router.post("/ports/{cluster_name}/release")
async def release_cluster_ports(cluster_name: str):
    """
    Zwolnij porty dla klastra (używaj ostrożnie!)
    """
    try:
        success = port_manager.release_cluster_ports(cluster_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Klaster {cluster_name} nie ma przypisanych portów"
            )
        
        return {
            "message": f"Porty dla klastra {cluster_name} zostały zwolnione",
            "cluster_name": cluster_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas zwalniania portów: {str(e)}"
        )

@router.get("/cloudwatch-metrics/{cluster_name}")
async def get_cloudwatch_metrics(cluster_name: str):
    """
    Pobierz metryki CloudWatch dla klastra EKS
    """
    try:
        from app.services.eks_service import eks_service
        from datetime import datetime, timedelta
        import json
        
        # Pobierz credentials
        credentials = eks_service.get_cluster_credentials(cluster_name)
        if not credentials:
            raise HTTPException(
                status_code=404,
                detail=f"Nie znaleziono credentials dla klastra {cluster_name}"
            )
        
        region = credentials["region"]
        env = os.environ.copy()
        env.update({
            "AWS_ACCESS_KEY_ID": credentials["aws_access_key"],
            "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_key"],
            "AWS_DEFAULT_REGION": region
        })
        
        # Przygotuj zakres czasu (ostatnie 5 minut)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        metrics_data = {}
        
        # Funkcja pomocnicza do pobierania metryk
        def get_metric(namespace, metric_name, dimensions, stat="Average"):
            try:
                result = subprocess.run([
                    "aws", "cloudwatch", "get-metric-statistics",
                    "--namespace", namespace,
                    "--metric-name", metric_name,
                    "--dimensions", *[f"Name={k},Value={v}" for k, v in dimensions.items()],
                    "--start-time", start_time.isoformat(),
                    "--end-time", end_time.isoformat(),
                    "--period", "300",  # 5 minut
                    "--statistics", stat,
                    "--region", region,
                    "--output", "json"
                ], capture_output=True, text=True, env=env, timeout=10)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    datapoints = data.get("Datapoints", [])
                    if datapoints:
                        # Weź ostatni datapoint
                        latest = max(datapoints, key=lambda x: x["Timestamp"])
                        return latest.get(stat, 0)
                return None
            except Exception as e:
                print(f"Error getting metric {metric_name}: {e}")
                return None
        
        # Pobierz CPU utilization dla klastra
        cpu_util = get_metric(
            "ContainerInsights",
            "cluster_cpu_utilization",
            {"ClusterName": cluster_name},
            "Average"
        )
        if cpu_util is not None:
            metrics_data["cpu_utilization"] = round(cpu_util, 2)
        
        # Pobierz Memory utilization
        mem_util = get_metric(
            "ContainerInsights",
            "cluster_memory_utilization",
            {"ClusterName": cluster_name},
            "Average"
        )
        if mem_util is not None:
            metrics_data["memory_utilization"] = round(mem_util, 2)
        
        # Pobierz liczbę running pods
        pod_count = get_metric(
            "ContainerInsights",
            "cluster_number_of_running_pods",
            {"ClusterName": cluster_name},
            "Average"
        )
        if pod_count is not None:
            metrics_data["running_pods"] = int(pod_count)
        
        # Pobierz liczbę failed pods
        failed_pods = get_metric(
            "ContainerInsights",
            "cluster_failed_pod_count",
            {"ClusterName": cluster_name},
            "Average"
        )
        if failed_pods is not None:
            metrics_data["failed_pods"] = int(failed_pods)
        
        # Pobierz network RX bytes
        net_rx = get_metric(
            "ContainerInsights",
            "cluster_network_rx_bytes",
            {"ClusterName": cluster_name},
            "Average"
        )
        if net_rx is not None:
            metrics_data["network_rx_bytes"] = round(net_rx / 1024 / 1024, 2)  # MB
        
        # Pobierz network TX bytes
        net_tx = get_metric(
            "ContainerInsights",
            "cluster_network_tx_bytes",
            {"ClusterName": cluster_name},
            "Average"
        )
        if net_tx is not None:
            metrics_data["network_tx_bytes"] = round(net_tx / 1024 / 1024, 2)  # MB
        
        # Pobierz liczbę nodes
        node_count = get_metric(
            "ContainerInsights",
            "cluster_node_count",
            {"ClusterName": cluster_name},
            "Average"
        )
        if node_count is not None:
            metrics_data["node_count"] = int(node_count)
        
        return {
            "cluster_name": cluster_name,
            "region": region,
            "metrics": metrics_data,
            "timestamp": end_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas pobierania metryk CloudWatch: {str(e)}"
        )