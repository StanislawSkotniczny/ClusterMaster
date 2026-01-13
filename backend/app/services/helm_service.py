import subprocess
import os
import shutil
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
import time
from .port_manager import port_manager

def get_cluster_context_for_helm(cluster_name: str) -> tuple[str, str]:
    """Pobierz prawidłowy kontekst kubectl dla klastra (obsługa EKS, k3d, kind)
    Returns: (context, provider) gdzie provider to 'eks', 'k3d' lub 'kind'
    """
    from .k3d_service import k3d_service
    
    # Sprawdź czy to klaster EKS
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            contexts = result.stdout.strip().split('\n')
            for context in contexts:
                if cluster_name in context and 'arn:aws:eks' in context:
                    print(f"🔍 Znaleziono klaster EKS: {context}")
                    return context, 'eks'
    except Exception as e:
        print(f"⚠️ Błąd podczas sprawdzania contextu: {e}")
    
    # Sprawdź k3d
    try:
        k3d_clusters = k3d_service.list_clusters()
        if cluster_name in k3d_clusters:
            return f"k3d-{cluster_name}", 'k3d'
    except Exception:
        pass
    
    # Default to kind
    return f"kind-{cluster_name}", 'kind'

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
        """Zainstaluj monitoring + automatyczny port-forward (dla EKS, k3d, kind)"""
        try:
            # Pobierz prawidłowy kontekst klastra i typ providera
            context, provider = get_cluster_context_for_helm(cluster_name)
            print(f"📦 Instalacja monitoringu dla {cluster_name} (provider: {provider}, context: {context})")
            
            # Jeśli to EKS, użyj CloudWatch Container Insights zamiast Helm
            if provider == "eks":
                print(f"☁️ EKS wykryty - używam AWS CloudWatch Container Insights")
                return self.install_cloudwatch_insights(cluster_name, context)
            
            # Przypisz porty dla klastra
            cluster_ports = port_manager.assign_ports_for_cluster(cluster_name)
            
            # 1. Dodaj repozytoria Helm
            repos_to_add = [
                ("prometheus-community", "https://prometheus-community.github.io/helm-charts"),
                ("grafana", "https://grafana.github.io/helm-charts")
            ]
            
            for repo_name, repo_url in repos_to_add:
                print(f"📦 Dodawanie repo Helm: {repo_name}")
                result = self.run_helm_command([
                    "repo", "add", repo_name, repo_url,
                    "--kube-context", context
                ])
                if not result["success"]:
                    error_msg = f"Nie udało się dodać repo {repo_name}: {result['stderr']}"
                    print(f"❌ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
                    }
                print(f"✅ Repo {repo_name} dodane")
            
            # 2. Aktualizuj repozytoria
            print(f"🔄 Aktualizacja repozytoriów Helm...")
            result = self.run_helm_command([
                "repo", "update",
                "--kube-context", context
            ])
            if not result["success"]:
                error_msg = f"Nie udało się zaktualizować repo: {result['stderr']}"
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            print(f"✅ Repozytoria zaktualizowane")
            
            # 3. Utwórz namespace
            print(f"📁 Tworzenie namespace: {namespace}")
            kubectl_result = subprocess.run([
                "kubectl", "create", "namespace", namespace,
                "--context", context
            ], capture_output=True, text=True)
            # Ignoruj błąd jeśli namespace już istnieje
            if kubectl_result.returncode == 0:
                print(f"✅ Namespace {namespace} utworzony")
            else:
                print(f"ℹ️ Namespace {namespace} już istnieje lub wystąpił błąd: {kubectl_result.stderr[:100]}")
            
            # 4. Sprawdź czy monitoring jest już zainstalowany
            print(f"🔍 Sprawdzam istniejące releases Helm...")
            existing_releases = self.list_releases(cluster_name, namespace, context)
            releases_names = []
            if existing_releases.get("success") and existing_releases.get("releases"):
                releases_names = [r.get("name") for r in existing_releases["releases"]]
                print(f"📋 Znalezione releases: {', '.join(releases_names) if releases_names else 'brak'}")
            
            # 5. Zainstaluj lub zaktualizuj Prometheus
            prometheus_exists = "prometheus" in releases_names
            print(f"📊 {'Aktualizacja' if prometheus_exists else 'Instalacja'} Prometheus...")
            prometheus_result = self.install_or_upgrade_prometheus(cluster_name, namespace, context, cluster_ports["prometheus"], prometheus_exists)
            
            if not prometheus_result["success"]:
                print(f"❌ {'Aktualizacja' if prometheus_exists else 'Instalacja'} Prometheus nie powiodła się: {prometheus_result.get('error', 'Unknown error')}")
                return prometheus_result
            print(f"✅ Prometheus {'zaktualizowany' if prometheus_exists else 'zainstalowany'}")
            
            # 6. Zainstaluj lub zaktualizuj Grafana
            grafana_exists = "grafana" in releases_names
            print(f"📈 {'Aktualizacja' if grafana_exists else 'Instalacja'} Grafana...")
            grafana_result = self.install_or_upgrade_grafana(cluster_name, namespace, context, cluster_ports["grafana"], grafana_exists)
            
            if not grafana_result["success"]:
                print(f"❌ {'Aktualizacja' if grafana_exists else 'Instalacja'} Grafana nie powiodła się: {grafana_result.get('error', 'Unknown error')}")
                return grafana_result
            print(f"✅ Grafana {'zaktualizowana' if grafana_exists else 'zainstalowana'}")
            
            # Po instalacji, uruchom automatyczne port-forward
            if prometheus_result["success"] and grafana_result["success"]:
                # Uruchom port-forward w tle po instalacji
                self.start_background_port_forward(cluster_name, namespace, cluster_ports, context, provider)
                
                return {
                    "success": True,
                    "message": f"Stack monitoringu zainstalowany pomyślnie na {provider.upper()}",
                    "provider": provider,
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
            error_msg = f"Wyjątek podczas instalacji monitoringu: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def install_prometheus(self, cluster_name: str, namespace: str, context: str, node_port: int) -> Dict[str, Any]:
        """Zainstaluj Prometheus z ClusterIP (dostęp przez port-forward)"""
        
        prometheus_values = {
            "server": {
                "service": {
                    "type": "ClusterIP"  # ClusterIP działa na EKS i lokalnych klastrach
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
    
    def install_cloudwatch_insights(self, cluster_name: str, context: str) -> Dict[str, Any]:
        """Zainstaluj AWS CloudWatch Container Insights dla EKS używając AWS add-ona"""
        try:
            from .eks_service import eks_service
            credentials = eks_service.get_cluster_credentials(cluster_name)
            
            if not credentials:
                return {
                    "success": False,
                    "error": f"Brak credentials dla klastra EKS: {cluster_name}"
                }
            
            region = credentials["region"]
            
            # Ustaw credentials
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": credentials["aws_access_key"],
                "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_key"],
                "AWS_DEFAULT_REGION": region
            })
            
            print(f"📊 Instaluję CloudWatch Observability add-on dla EKS...")
            
            # Krok 1: Zainstaluj EKS Pod Identity agent (jeśli nie istnieje)
            print(f"🔧 Sprawdzam EKS Pod Identity agent...")
            
            # Sprawdź czy już jest zainstalowany
            check_pod_identity = subprocess.run(
                ["aws", "eks", "describe-addon",
                 "--cluster-name", cluster_name,
                 "--addon-name", "eks-pod-identity-agent",
                 "--region", region],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if check_pod_identity.returncode != 0:
                # Nie ma - instaluj
                print(f"📦 Instaluję EKS Pod Identity agent...")
                pod_identity_result = subprocess.run(
                    ["aws", "eks", "create-addon",
                     "--cluster-name", cluster_name,
                     "--addon-name", "eks-pod-identity-agent",
                     "--region", region],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120
                )
                
                if pod_identity_result.returncode != 0:
                    error_msg = f"Nie udało się zainstalować EKS Pod Identity agent: {pod_identity_result.stderr}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg}
                
                print(f"✅ EKS Pod Identity agent instaluje się...")
                
                # Czekaj aż będzie active (max 2 minuty)
                print(f"⏳ Czekam na aktywację Pod Identity agent...")
                for i in range(24):  # 24 * 5s = 120s
                    time.sleep(5)
                    check_status = subprocess.run(
                        ["aws", "eks", "describe-addon",
                         "--cluster-name", cluster_name,
                         "--addon-name", "eks-pod-identity-agent",
                         "--region", region,
                         "--query", "addon.status",
                         "--output", "text"],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=30
                    )
                    
                    if check_status.returncode == 0:
                        status = check_status.stdout.strip()
                        print(f"   Status: {status}")
                        if status == "ACTIVE":
                            print(f"✅ Pod Identity agent aktywny")
                            break
                        elif "FAILED" in status or "DEGRADED" in status:
                            return {"success": False, "error": f"Pod Identity agent w stanie: {status}"}
            else:
                print(f"✅ EKS Pod Identity agent już zainstalowany")
            
            # Krok 2: Dodaj wymagane polityki IAM do node role
            print(f"🔐 Konfiguruję uprawnienia IAM dla CloudWatch...")
            
            # Pobierz nazwę node role z klastra
            try:
                node_role_result = subprocess.run(
                    ["aws", "eks", "describe-nodegroup",
                     "--cluster-name", cluster_name,
                     "--nodegroup-name", 
                     subprocess.run(
                         ["aws", "eks", "list-nodegroups",
                          "--cluster-name", cluster_name,
                          "--region", region,
                          "--query", "nodegroups[0]",
                          "--output", "text"],
                         capture_output=True,
                         text=True,
                         env=env,
                         timeout=30
                     ).stdout.strip(),
                     "--region", region,
                     "--query", "nodegroup.nodeRole",
                     "--output", "text"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                if node_role_result.returncode == 0:
                    node_role_arn = node_role_result.stdout.strip()
                    # Wyciągnij samą nazwę roli z ARN (np. awsczwartek-eks-node-role z arn:aws:iam::123:role/awsczwartek-eks-node-role)
                    node_role_name = node_role_arn.split('/')[-1]
                    print(f"📋 Znaleziona node role: {node_role_name}")
                    
                    # Dodaj CloudWatchAgentServerPolicy
                    attach_policy = subprocess.run(
                        ["aws", "iam", "attach-role-policy",
                         "--role-name", node_role_name,
                         "--policy-arn", "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=30
                    )
                    
                    if attach_policy.returncode == 0 or "already attached" in attach_policy.stderr.lower():
                        print(f"✅ Polityka CloudWatchAgentServerPolicy dodana")
                    else:
                        print(f"⚠️  Nie udało się dodać polityki: {attach_policy.stderr[:100]}")
                else:
                    print(f"⚠️  Nie udało się pobrać node role")
            except Exception as e:
                print(f"⚠️  Błąd konfiguracji IAM: {e}")
            
            # Krok 3: Zainstaluj CloudWatch Observability add-on
            print(f"📊 Instaluję CloudWatch Observability add-on...")
            
            # Sprawdź czy już istnieje
            check_cloudwatch = subprocess.run(
                ["aws", "eks", "describe-addon",
                 "--cluster-name", cluster_name,
                 "--addon-name", "amazon-cloudwatch-observability",
                 "--region", region],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if check_cloudwatch.returncode == 0:
                print(f"ℹ️  CloudWatch Observability add-on już istnieje")
            else:
                # Zainstaluj add-on
                cloudwatch_result = subprocess.run(
                    ["aws", "eks", "create-addon",
                     "--cluster-name", cluster_name,
                     "--addon-name", "amazon-cloudwatch-observability",
                     "--region", region],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120
                )
                
                if cloudwatch_result.returncode != 0:
                    error_msg = f"Nie udało się zainstalować CloudWatch Observability: {cloudwatch_result.stderr}"
                    print(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg}
                
                print(f"✅ CloudWatch Observability add-on instaluje się...")
                
                # Czekaj na aktywację (max 3 minuty)
                print(f"⏳ Czekam na aktywację CloudWatch Observability...")
                for i in range(36):  # 36 * 5s = 180s
                    time.sleep(5)
                    check_status = subprocess.run(
                        ["aws", "eks", "describe-addon",
                         "--cluster-name", cluster_name,
                         "--addon-name", "amazon-cloudwatch-observability",
                         "--region", region,
                         "--query", "addon.status",
                         "--output", "text"],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=30
                    )
                    
                    if check_status.returncode == 0:
                        status = check_status.stdout.strip()
                        if i % 4 == 0:  # Co 20 sekund
                            print(f"   Status: {status}")
                        if status == "ACTIVE":
                            print(f"✅ CloudWatch Observability aktywny")
                            break
                        elif "FAILED" in status or "DEGRADED" in status:
                            return {"success": False, "error": f"CloudWatch Observability w stanie: {status}"}
            
            print(f"✅ CloudWatch Container Insights zainstalowany!")
            
            # Krok 4: Restartuj worker nodes, żeby nowe uprawnienia IAM zadziałały
            print(f"🔄 Restartuję worker nodes dla zastosowania uprawnień IAM...")
            
            try:
                # Pobierz listę wszystkich node groups
                nodegroups_result = subprocess.run(
                    ["aws", "eks", "list-nodegroups",
                     "--cluster-name", cluster_name,
                     "--region", region,
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                if nodegroups_result.returncode == 0:
                    import json
                    nodegroups_data = json.loads(nodegroups_result.stdout)
                    nodegroups = nodegroups_data.get("nodegroups", [])
                    
                    if nodegroups:
                        # Dla każdej node group, pobierz instancje i zrestartuj je
                        for ng in nodegroups:
                            print(f"   Restartuję instancje w node group: {ng}")
                            
                            # Pobierz Auto Scaling Group name z node group
                            ng_details = subprocess.run(
                                ["aws", "eks", "describe-nodegroup",
                                 "--cluster-name", cluster_name,
                                 "--nodegroup-name", ng,
                                 "--region", region,
                                 "--query", "nodegroup.resources.autoScalingGroups[0].name",
                                 "--output", "text"],
                                capture_output=True,
                                text=True,
                                env=env,
                                timeout=30
                            )
                            
                            if ng_details.returncode == 0:
                                asg_name = ng_details.stdout.strip()
                                
                                if asg_name and asg_name != "None":
                                    # Pobierz instance IDs z ASG
                                    instances_result = subprocess.run(
                                        ["aws", "autoscaling", "describe-auto-scaling-groups",
                                         "--auto-scaling-group-names", asg_name,
                                         "--region", region,
                                         "--query", "AutoScalingGroups[0].Instances[*].InstanceId",
                                         "--output", "text"],
                                        capture_output=True,
                                        text=True,
                                        env=env,
                                        timeout=30
                                    )
                                    
                                    if instances_result.returncode == 0:
                                        instance_ids = instances_result.stdout.strip().split()
                                        
                                        if instance_ids:
                                            # Restartuj instancje
                                            reboot_result = subprocess.run(
                                                ["aws", "ec2", "reboot-instances",
                                                 "--instance-ids"] + instance_ids +
                                                ["--region", region],
                                                capture_output=True,
                                                text=True,
                                                env=env,
                                                timeout=60
                                            )
                                            
                                            if reboot_result.returncode == 0:
                                                print(f"   ✅ Zrestartowano {len(instance_ids)} instancji")
                                            else:
                                                print(f"   ⚠️  Błąd restartu instancji: {reboot_result.stderr[:100]}")
                
                print(f"✅ Worker nodes restartują się (to potrwa ~2-3 minuty)")
            except Exception as e:
                print(f"⚠️  Błąd podczas restartu nodes: {e}")
            
            # URL do CloudWatch Console - Container Insights
            container_insights_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#container-insights:infrastructure"
            # Logi z klastra  
            logs_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups"
            
            return {
                "success": True,
                "message": "CloudWatch Container Insights został zainstalowany pomyślnie. Worker nodes restartują się, metryki pojawią się za ~5 minut.",
                "provider": "eks",
                "monitoring_type": "cloudwatch",
                "services": {
                    "cloudwatch": container_insights_url,
                    "logs": logs_url
                },
                "access_info": {
                    "cloudwatch_url": container_insights_url,
                    "logs_url": logs_url,
                    "note": "Metryki i logi będą dostępne w AWS CloudWatch Console po ~5 minutach (po restarcie worker nodes).",
                    "region": region
                },
                "namespace": "amazon-cloudwatch"
            }
            
        except Exception as e:
            error_msg = f"Błąd instalacji CloudWatch Insights: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": error_msg}
    
    def install_or_upgrade_prometheus(self, cluster_name: str, namespace: str, context: str, node_port: int, upgrade: bool = False) -> Dict[str, Any]:
        """Zainstaluj lub zaktualizuj Prometheus"""
        
        # Sprawdź provider - dla k3d używamy NodePort, dla innych ClusterIP
        _, provider = get_cluster_context_for_helm(cluster_name)
        
        if provider == "k3d":
            # K3d wymaga NodePort żeby loadbalancer mógł przekierować ruch
            prometheus_values = {
                "server": {
                    "service": {
                        "type": "NodePort",
                        "nodePort": node_port
                    }
                },
                "alertmanager": {"enabled": False},
                "pushgateway": {"enabled": True},
                "nodeExporter": {"enabled": True},
                "kubeStateMetrics": {"enabled": True}
            }
        else:
            # Kind i inne - ClusterIP + port-forward
            prometheus_values = {
                "server": {
                    "service": {
                        "type": "ClusterIP"
                    }
                },
                "alertmanager": {"enabled": False},
                "pushgateway": {"enabled": True},
                "nodeExporter": {"enabled": True},
                "kubeStateMetrics": {"enabled": True}
            }
        
        return self.install_or_upgrade_chart(
            release_name="prometheus",
            chart="prometheus-community/prometheus",
            namespace=namespace,
            values=prometheus_values,
            context=context,
            upgrade=upgrade
        )
    
    def install_grafana(self, cluster_name: str, namespace: str, context: str, node_port: int) -> Dict[str, Any]:
        """Zainstaluj Grafana z ClusterIP (dostęp przez port-forward)"""
        
        grafana_values = {
            "service": {
                "type": "ClusterIP"  # ClusterIP działa na EKS i lokalnych klastrach
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
    
    def install_or_upgrade_grafana(self, cluster_name: str, namespace: str, context: str, node_port: int, upgrade: bool = False) -> Dict[str, Any]:
        """Zainstaluj lub zaktualizuj Grafana"""
        
        # Sprawdź provider - dla k3d używamy NodePort, dla innych ClusterIP
        _, provider = get_cluster_context_for_helm(cluster_name)
        
        if provider == "k3d":
            # K3d wymaga NodePort żeby loadbalancer mógł przekierować ruch
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
        else:
            # Kind i inne - ClusterIP + port-forward
            grafana_values = {
                "service": {
                    "type": "ClusterIP"
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
        
        return self.install_or_upgrade_chart(
            release_name="grafana",
            chart="grafana/grafana",
            namespace=namespace,
            values=grafana_values,
            context=context,
            upgrade=upgrade
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
    
    def install_or_upgrade_chart(self, release_name: str, chart: str, namespace: str, 
                                 values: Dict[str, Any], context: str, upgrade: bool = False, 
                                 wait: bool = True, timeout_minutes: int = 10) -> Dict[str, Any]:
        """Zainstaluj lub zaktualizuj chart Helm (używa helm upgrade --install)"""
        
        # Utwórz tymczasowy plik z values
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(values, f)
            values_file = f.name
        
        try:
            # helm upgrade --install działa zarówno dla nowej instalacji jak i aktualizacji
            cmd = [
                "upgrade", "--install", release_name, chart,
                "--namespace", namespace,
                "--values", values_file,
                "--kube-context", context
            ]
            
            # Dla EKS nie czekamy (asynchroniczne), dla lokalnych czekamy
            if wait:
                cmd.extend(["--wait", "--timeout", f"{timeout_minutes}m"])
            
            result = self.run_helm_command(cmd, timeout=timeout_minutes * 60 + 30)
            
            if result["success"]:
                action = "zaktualizowany" if upgrade else "zainstalowany"
                return {
                    "success": True,
                    "message": f"Chart {chart} {action} jako {release_name}",
                    "release": release_name,
                    "namespace": namespace
                }
            else:
                action = "aktualizacji" if upgrade else "instalacji"
                return {
                    "success": False,
                    "error": f"Błąd {action} {chart}: {result['stderr']}"
                }
                
        finally:
            # Usuń tymczasowy plik
            try:
                os.unlink(values_file)
            except:
                pass
    
    def start_background_port_forward(self, cluster_name: str, namespace: str, cluster_ports: Dict[str, int], context: str, provider: str):
        """Uruchom port-forward w tle jako daemon z dynamicznymi portami (EKS, k3d, kind)"""
        def run_port_forward():
            # Używamy przekazanego contextu (może być ARN dla EKS)
            print(f"🚀 Uruchamianie port-forward dla {cluster_name} ({provider})")
            print(f"   Context: {context}")
            
            # Dla EKS: ustaw AWS credentials w środowisku tego wątku
            env = os.environ.copy()
            if provider == 'eks':
                from .eks_service import eks_service
                credentials = eks_service.get_cluster_credentials(cluster_name)
                if credentials:
                    env.update({
                        "AWS_ACCESS_KEY_ID": credentials["aws_access_key"],
                        "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_key"],
                        "AWS_DEFAULT_REGION": credentials["region"]
                    })
                    print(f"   ✅ AWS credentials załadowane dla port-forward")
            
            # Czekaj na gotowość podów
            print(f"⏳ Czekam na gotowość podów monitoringu...")
            time.sleep(60 if provider == 'eks' else 45)  # EKS może potrzebować więcej czasu
            
            try:
                # Uruchom Prometheus port-forward z dynamicznym portem
                prometheus_proc = subprocess.Popen([
                    "kubectl", "port-forward", 
                    "service/prometheus-server", f"{cluster_ports['prometheus']}:80",
                    "-n", namespace, "--context", context
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                
                # Uruchom Grafana port-forward z dynamicznym portem
                grafana_proc = subprocess.Popen([
                    "kubectl", "port-forward",
                    "service/grafana", f"{cluster_ports['grafana']}:80",
                    "-n", namespace, "--context", context  
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                
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

    def uninstall_release(self, release_name: str, cluster_name: str, namespace: str, context: str = None) -> Dict[str, Any]:
        """Usuń Helm release"""
        try:
            if not context:
                context, _ = get_cluster_context_for_helm(cluster_name)
            
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

    def list_releases(self, cluster_name: str, namespace: Optional[str] = None, context: str = None) -> Dict[str, Any]:
        """Lista Helm releases w klastrze"""
        try:
            if not context:
                context, _ = get_cluster_context_for_helm(cluster_name)
            
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