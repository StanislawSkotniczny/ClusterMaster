import subprocess
import os
import shutil
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
import time
from .port_manager import port_manager

class HelmService:
    def __init__(self):
        self.helm_bin = self.find_helm_executable()
        self.port_forward_threads = {}  # Przechowuj wątki port-forward
        
    def find_helm_executable(self) -> str:
        """Znajdź ścieżkę do helm.exe"""
        helm_path = shutil.which("helm")
        if helm_path:
            return helm_path
        
        # Sprawdź typowe lokalizacje na Windows
        possible_paths = [
            "C:\\tools\\helm.exe",
            "C:\\Program Files\\helm\\helm.exe",
            os.path.expanduser("~\\AppData\\Local\\Programs\\helm\\helm.exe")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "helm"  # Fallback
    
    def run_helm_command(self, args: List[str], cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Uruchom komendę helm"""
        try:
            cmd = [self.helm_bin] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                encoding='utf-8',
                errors='replace'
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": f"Komenda helm przekroczyła limit czasu ({timeout}s)",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def install_monitoring_stack(self, cluster_name: str, namespace: str = "monitoring") -> Dict[str, Any]:
        """Zainstaluj monitoring + automatyczny port-forward"""
        try:
            # Detect cluster provider (k3d or kind)
            from .k3d_service import k3d_service
            provider = "kind"  # default
            
            # Check if it's a k3d cluster
            try:
                k3d_clusters = k3d_service.list_clusters()
                if cluster_name in k3d_clusters:
                    provider = "k3d"
            except:
                pass
            
            context = f"{provider}-{cluster_name}"
            
            # Przypisz porty dla klastra
            cluster_ports = port_manager.assign_ports_for_cluster(cluster_name)
            
            # 1. Dodaj repozytoria Helm
            repos_to_add = [
                ("prometheus-community", "https://prometheus-community.github.io/helm-charts"),
                ("grafana", "https://grafana.github.io/helm-charts")
            ]
            
            for repo_name, repo_url in repos_to_add:
                result = self.run_helm_command([
                    "repo", "add", repo_name, repo_url,
                    "--kube-context", context
                ])
                if not result["success"]:
                    return {
                        "success": False,
                        "error": f"Nie udało się dodać repo {repo_name}: {result['stderr']}"
                    }
            
            # 2. Aktualizuj repozytoria
            result = self.run_helm_command([
                "repo", "update",
                "--kube-context", context
            ])
            if not result["success"]:
                return {
                    "success": False,
                    "error": f"Nie udało się zaktualizować repo: {result['stderr']}"
                }
            
            # 3. Utwórz namespace
            kubectl_result = subprocess.run([
                "kubectl", "create", "namespace", namespace,
                "--context", context
            ], capture_output=True, text=True)
            # Ignoruj błąd jeśli namespace już istnieje
            
            # 4. Zainstaluj Prometheus z dynamicznym portem
            prometheus_result = self.install_prometheus(cluster_name, namespace, context, cluster_ports["prometheus"])
            
            if not prometheus_result["success"]:
                return prometheus_result
            
            # 5. Zainstaluj Grafana z dynamicznym portem
            grafana_result = self.install_grafana(cluster_name, namespace, context, cluster_ports["grafana"])
            
            if not grafana_result["success"]:
                return grafana_result
            
            # Po instalacji, uruchom automatyczne port-forward
            if prometheus_result["success"] and grafana_result["success"]:
                # Uruchom port-forward w tle po instalacji
                self.start_background_port_forward(cluster_name, namespace, cluster_ports)
                
                return {
                    "success": True,
                    "message": "Stack monitoringu zainstalowany pomyślnie",
                    "services": {
                        "prometheus": f"http://localhost:{cluster_ports['prometheus']}",
                        "grafana": f"http://localhost:{cluster_ports['grafana']} (admin/admin123)"
                    },
                    "access_info": {
                        "prometheus_url": f"http://localhost:{cluster_ports['prometheus']}",
                        "grafana_url": f"http://localhost:{cluster_ports['grafana']}",
                        "grafana_credentials": "admin / admin123",
                        "assigned_ports": cluster_ports
                    },
                    "namespace": namespace
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def install_prometheus(self, cluster_name: str, namespace: str, context: str, node_port: int) -> Dict[str, Any]:
        """Zainstaluj Prometheus z dynamicznym NodePort"""
        
        prometheus_values = {
            "server": {
                "service": {
                    "type": "NodePort",
                    "nodePort": node_port
                }
            },
            "alertmanager": {"enabled": False},
            "pushgateway": {"enabled": False},
            "nodeExporter": {"enabled": True},
            "kubeStateMetrics": {"enabled": True}
        }
        
        return self.install_chart(
            release_name="prometheus",
            chart="prometheus-community/prometheus",
            namespace=namespace,
            values=prometheus_values,
            context=context
        )
    
    def install_grafana(self, cluster_name: str, namespace: str, context: str, node_port: int) -> Dict[str, Any]:
        """Zainstaluj Grafana z dynamicznym NodePort"""
        
        grafana_values = {
            "service": {
                "type": "NodePort",
                "nodePort": node_port
            },
            "adminPassword": "admin123",
            "datasources": {
                "datasources.yaml": {
                    "apiVersion": 1,
                    "datasources": [{
                        "name": "Prometheus",
                        "type": "prometheus",
                        "url": f"http://prometheus-server.{namespace}.svc.cluster.local",
                        "access": "proxy",
                        "isDefault": True
                    }]
                }
            }
        }
        
        return self.install_chart(
            release_name="grafana",
            chart="grafana/grafana",
            namespace=namespace,
            values=grafana_values,
            context=context
        )
    
    def install_chart(self, release_name: str, chart: str, namespace: str, 
                     values: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Zainstaluj konkretny chart Helm"""
        
        # Utwórz tymczasowy plik z values
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(values, f)
            values_file = f.name
        
        try:
            result = self.run_helm_command([
                "install", release_name, chart,
                "--namespace", namespace,
                "--values", values_file,
                "--kube-context", context,
                "--wait",
                "--timeout", "10m"
            ])
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Chart {chart} zainstalowany jako {release_name}",
                    "release": release_name,
                    "namespace": namespace
                }
            else:
                return {
                    "success": False,
                    "error": f"Instalacja {chart} nie powiodła się: {result['stderr']}"
                }
                
        finally:
            # Usuń tymczasowy plik
            try:
                os.unlink(values_file)
            except:
                pass
    
    def start_background_port_forward(self, cluster_name: str, namespace: str, cluster_ports: Dict[str, int]):
        """Uruchom port-forward w tle jako daemon z dynamicznymi portami"""
        def run_port_forward():
            context = f"kind-{cluster_name}"
            
            # Czekaj na gotowość podów
            print(f"Waiting for monitoring pods in {cluster_name}...")
            time.sleep(45)  # Daj więcej czasu na startup
            
            try:
                # Uruchom Prometheus port-forward z dynamicznym portem
                prometheus_proc = subprocess.Popen([
                    "kubectl", "port-forward", 
                    "service/prometheus-server", f"{cluster_ports['prometheus']}:80",
                    "-n", namespace, "--context", context
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Uruchom Grafana port-forward z dynamicznym portem
                grafana_proc = subprocess.Popen([
                    "kubectl", "port-forward",
                    "service/grafana", f"{cluster_ports['grafana']}:80",
                    "-n", namespace, "--context", context  
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"✅ Monitoring dostępny dla klastra {cluster_name}:")
                print(f"📊 Prometheus: http://localhost:{cluster_ports['prometheus']}")
                print(f"📈 Grafana: http://localhost:{cluster_ports['grafana']} (admin/admin123)")
                
                # Zapisz procesy (opcjonalnie)
                self.port_forward_threads[cluster_name] = {
                    "prometheus": prometheus_proc,
                    "grafana": grafana_proc,
                    "ports": cluster_ports
                }
                
                # Czekaj na zakończenie (daemon)
                prometheus_proc.wait()
                grafana_proc.wait()
                
            except Exception as e:
                print(f"Port-forward error: {str(e)}")
        
        # Uruchom w osobnym wątku jako daemon
        thread = threading.Thread(target=run_port_forward, daemon=True)
        thread.start()
        print(f"Started background port-forward for {cluster_name} on ports {cluster_ports}")

    def cleanup_cluster_resources(self, cluster_name: str) -> Dict[str, Any]:
        """Wyczyść zasoby klastra (port-forward i porty)"""
        try:
            # Zatrzymaj port-forward procesy
            if cluster_name in self.port_forward_threads:
                processes = self.port_forward_threads[cluster_name]
                
                for service_name, proc in processes.items():
                    if service_name != "ports" and hasattr(proc, 'terminate'):
                        try:
                            proc.terminate()
                        except:
                            pass
                
                del self.port_forward_threads[cluster_name]
            
            # Zwolnij porty w port_manager
            port_manager.release_cluster_ports(cluster_name)
            
            return {
                "success": True,
                "message": f"Zasoby klastra {cluster_name} zostały wyczyszczone"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas czyszczenia zasobów: {str(e)}"
            }

    def get_cluster_monitoring_info(self, cluster_name: str) -> Optional[Dict[str, Any]]:
        """Pobierz informacje o monitoringu dla klastra"""
        ports = port_manager.get_cluster_ports(cluster_name)
        if not ports:
            return None
        
        return {
            "cluster_name": cluster_name,
            "ports": ports,
            "urls": port_manager.get_cluster_urls(cluster_name),
            "port_forward_active": cluster_name in self.port_forward_threads
        }

    def uninstall_release(self, release_name: str, cluster_name: str, namespace: str) -> Dict[str, Any]:
        """Usuń Helm release"""
        try:
            context = f"kind-{cluster_name}"
            
            result = self.run_helm_command([
                "uninstall", release_name,
                "--namespace", namespace,
                "--kube-context", context
            ])
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Release {release_name} został usunięty",
                    "release": release_name,
                    "namespace": namespace
                }
            else:
                return {
                    "success": False,
                    "error": f"Nie udało się usunąć release {release_name}: {result['stderr']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas usuwania release: {str(e)}"
            }

    def list_releases(self, cluster_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Lista Helm releases w klastrze"""
        try:
            context = f"kind-{cluster_name}"
            
            args = ["list", "--kube-context", context, "-o", "json"]
            if namespace:
                args.extend(["--namespace", namespace])
            else:
                args.append("--all-namespaces")
            
            result = self.run_helm_command(args)
            
            if result["success"]:
                import json
                try:
                    releases = json.loads(result["stdout"]) if result["stdout"].strip() else []
                    return {
                        "success": True,
                        "releases": releases,
                        "count": len(releases)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "releases": [],
                        "count": 0,
                        "note": "Brak releases lub błąd parsowania JSON"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Nie udało się pobrać listy releases: {result['stderr']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas pobierania releases: {str(e)}"
            }

# Singleton instance
helm_service = HelmService()