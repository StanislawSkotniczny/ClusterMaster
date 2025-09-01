import subprocess
import os
import shutil
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
import time

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
            context = f"kind-{cluster_name}"
            
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
            
            # 4. Zainstaluj Prometheus
            prometheus_result = self.install_prometheus(cluster_name, namespace, context)
            
            if not prometheus_result["success"]:
                return prometheus_result
            
            # 5. Zainstaluj Grafana
            grafana_result = self.install_grafana(cluster_name, namespace, context)
            
            if not grafana_result["success"]:
                return grafana_result
            
            # Po instalacji, uruchom automatyczne port-forward
            if prometheus_result["success"] and grafana_result["success"]:
                # Uruchom port-forward w tle po instalacji
                self.start_background_port_forward(cluster_name, namespace)
                
                return {
                    "success": True,
                    "message": "Stack monitoringu zainstalowany pomyślnie",
                    "services": {
                        "prometheus": "http://localhost:30090",
                        "grafana": "http://localhost:30030 (admin/admin123)"
                    },
                    "access_info": {
                        "prometheus_url": "http://localhost:30090",
                        "grafana_url": "http://localhost:30030",
                        "grafana_credentials": "admin / admin123"
                    },
                    "namespace": namespace
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def install_prometheus(self, cluster_name: str, namespace: str, context: str) -> Dict[str, Any]:
        """Zainstaluj Prometheus z NodePort"""
        
        prometheus_values = {
            "server": {
                "service": {
                    "type": "NodePort",
                    "nodePort": 30090  # Port mapowany w Kind config
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
    
    def install_grafana(self, cluster_name: str, namespace: str, context: str) -> Dict[str, Any]:
        """Zainstaluj Grafana z NodePort"""
        
        grafana_values = {
            "service": {
                "type": "NodePort",
                "nodePort": 30030  # Port mapowany w Kind config
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
    
    def start_background_port_forward(self, cluster_name: str, namespace: str):
        """Uruchom port-forward w tle jako daemon"""
        def run_port_forward():
            context = f"kind-{cluster_name}"
            
            # Czekaj na gotowość podów
            print(f"Waiting for monitoring pods in {cluster_name}...")
            time.sleep(45)  # Daj więcej czasu na startup
            
            try:
                # Uruchom Prometheus port-forward
                prometheus_proc = subprocess.Popen([
                    "kubectl", "port-forward", 
                    "service/prometheus-server", "9090:80",
                    "-n", namespace, "--context", context
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Uruchom Grafana port-forward
                grafana_proc = subprocess.Popen([
                    "kubectl", "port-forward",
                    "service/grafana", "3000:80",
                    "-n", namespace, "--context", context  
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"✅ Monitoring dostępny:")
                print(f"📊 Prometheus: http://localhost:9090")
                print(f"📈 Grafana: http://localhost:3000 (admin/admin123)")
                
                # Zapisz procesy (opcjonalnie)
                self.port_forward_threads[cluster_name] = {
                    "prometheus": prometheus_proc,
                    "grafana": grafana_proc
                }
                
                # Czekaj na zakończenie (daemon)
                prometheus_proc.wait()
                grafana_proc.wait()
                
            except Exception as e:
                print(f"Port-forward error: {str(e)}")
        
        # Uruchom w osobnym wątku jako daemon
        thread = threading.Thread(target=run_port_forward, daemon=True)
        thread.start()
        print(f"Started background port-forward for {cluster_name}")

# Singleton instance
helm_service = HelmService()