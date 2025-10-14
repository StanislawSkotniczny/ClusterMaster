import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

class AppService:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "cluster_apps"
        self.temp_dir.mkdir(exist_ok=True)
        self._ensure_helm_repos()
    
    def _get_cluster_context(self, cluster_name: str) -> str:
        """Get the correct kube-context for the cluster (kind- or k3d-)"""
        try:
            # Check if it's a k3d cluster
            result = subprocess.run(
                ["k3d", "cluster", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                k3d_clusters = json.loads(result.stdout)
                for cluster in k3d_clusters:
                    if cluster.get("name") == cluster_name:
                        return f"k3d-{cluster_name}"
            
            # Check if it's a kind cluster
            result = subprocess.run(
                ["kind", "get", "clusters"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                clusters = result.stdout.strip().split('\n')
                if cluster_name in clusters:
                    return f"kind-{cluster_name}"
            
            # Default to k3d if cluster name suggests it
            if "k3d" in cluster_name.lower():
                return f"k3d-{cluster_name}"
            
            # Default to kind for backward compatibility
            return f"kind-{cluster_name}"
            
        except Exception as e:
            print(f"Warning: Could not determine cluster type: {e}")
            # Default to kind for backward compatibility
            return f"kind-{cluster_name}"
    
    def _ensure_helm_repos(self):
        """Ensure common Helm repositories are added"""
        try:
            # Add common repos
            repos = {
                "bitnami": "https://charts.bitnami.com/bitnami",
                "stable": "https://charts.helm.sh/stable",
                "prometheus-community": "https://prometheus-community.github.io/helm-charts",
                "grafana": "https://grafana.github.io/helm-charts",
                "ingress-nginx": "https://kubernetes.github.io/ingress-nginx",
                "jetstack": "https://charts.jetstack.io",
            }
            
            for repo_name, repo_url in repos.items():
                subprocess.run([
                    "helm", "repo", "add", repo_name, repo_url
                ], capture_output=True, timeout=30)
            
            # Update repos
            subprocess.run([
                "helm", "repo", "update"
            ], capture_output=True, timeout=60)
            
        except Exception as e:
            print(f"Warning: Could not initialize Helm repositories: {e}")
    
    def search_helm_charts(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search for Helm charts across all repositories"""
        try:
            # Update repos first
            subprocess.run(["helm", "repo", "update"], capture_output=True, timeout=60)
            
            # Search for charts
            cmd = ["helm", "search", "repo", query, "--output", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                charts = json.loads(result.stdout) if result.stdout.strip() else []
                
                # Limit results and format
                formatted_charts = []
                for chart in charts[:max_results]:
                    formatted_charts.append({
                        "name": chart.get("name", "").split("/")[-1],  # Get chart name without repo
                        "full_name": chart.get("name", ""),  # Full name with repo
                        "version": chart.get("version", ""),
                        "app_version": chart.get("app_version", ""),
                        "description": chart.get("description", ""),
                        "repository": chart.get("name", "").split("/")[0] if "/" in chart.get("name", "") else "unknown"
                    })
                
                return {
                    "success": True,
                    "charts": formatted_charts,
                    "count": len(formatted_charts)
                }
            else:
                return {
                    "success": False,
                    "error": f"Search failed: {result.stderr}",
                    "charts": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Search error: {str(e)}",
                "charts": []
            }
    
    def install_app(self, cluster_name: str, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Install application on cluster using Helm"""
        try:
            app_name = app_data.get('name')
            display_name = app_data.get('displayName')
            namespace = app_data.get('namespace', 'default')
            helm_chart = app_data.get('helmChart')
            values = app_data.get('values', {})
            
            if not all([app_name, helm_chart]):
                return {
                    "success": False,
                    "error": "Missing required fields: name and helmChart"
                }
            
            if not self._cluster_exists(cluster_name):
                return {
                    "success": False,
                    "error": f"Cluster {cluster_name} does not exist"
                }
            
            self._create_namespace(cluster_name, namespace)
            
            self._add_helm_repos(helm_chart)
            
            values_file = self._create_values_file(app_name, values)
            
            try:

                result = self._helm_install(
                    cluster_name=cluster_name,
                    release_name=f"{app_name}-{cluster_name}",
                    chart=helm_chart,
                    namespace=namespace,
                    values_file=values_file
                )
                
                if result['success']:
                    return {
                        "success": True,
                        "message": f"{display_name} został zainstalowany na klastrze {cluster_name}",
                        "app_name": app_name,
                        "namespace": namespace,
                        "release_name": f"{app_name}-{cluster_name}"
                    }
                else:
                    return result
                    
            finally:

                if values_file and values_file.exists():
                    values_file.unlink()
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Installation failed: {str(e)}"
            }
    
    def get_installed_apps(self, cluster_name: str) -> Dict[str, Any]:
        """Get list of installed Helm releases"""
        try:
            if not self._cluster_exists(cluster_name):
                return {
                    "success": False,
                    "error": f"Cluster {cluster_name} does not exist"
                }
            
            context = self._get_cluster_context(cluster_name)

            cmd = [
                "helm", "list", "--all-namespaces",
                "--kube-context", context,
                "--output", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                releases = json.loads(result.stdout) if result.stdout.strip() else []
                
                return {
                    "success": True,
                    "apps": releases,
                    "count": len(releases)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get releases: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get installed apps: {str(e)}"
            }
    
    def uninstall_app(self, cluster_name: str, app_name: str) -> Dict[str, Any]:
        """Uninstall application from cluster"""
        try:
            print(f"=== UNINSTALL DEBUG ===")
            print(f"Cluster: {cluster_name}")
            print(f"App: {app_name}")
            
            if not self._cluster_exists(cluster_name):
                return {
                    "success": False,
                    "error": f"Cluster {cluster_name} does not exist"
                }
            
            if f"-{cluster_name}" in app_name:
                release_name = app_name  
            else:
                release_name = f"{app_name}-{cluster_name}"  
            
            print(f"Looking for release: {release_name}")
            
            context = self._get_cluster_context(cluster_name)
            
            list_cmd = [
                "helm", "list", "--all-namespaces",
                "--kube-context", context,
                "--output", "json"
            ]
            print(f"List command: {' '.join(list_cmd)}")
            
            list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=30)
            print(f"List result code: {list_result.returncode}")
            print(f"List stdout: {list_result.stdout}")
            print(f"List stderr: {list_result.stderr}")
            
            if list_result.returncode == 0:
                releases = json.loads(list_result.stdout) if list_result.stdout.strip() else []
                print(f"Found {len(releases)} releases")
                
                target_release = None
                for release in releases:
                    print(f"Checking release: {release.get('name')}")
                    if release.get('name') == release_name:
                        target_release = release
                        print(f"Found target release: {target_release}")
                        break
                
                if not target_release:
                    return {
                        "success": False,
                        "error": f"Release {release_name} not found"
                    }
                
                namespace = target_release.get('namespace')
                print(f"Target namespace: {namespace}")
                
                cmd = [
                    "helm", "uninstall", release_name,
                    "--namespace", namespace,
                    "--kube-context", context,
                    "--wait"
                ]
                print(f"Uninstall command: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                print(f"Uninstall result code: {result.returncode}")
                print(f"Uninstall stdout: {result.stdout}")
                print(f"Uninstall stderr: {result.stderr}")
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Application {app_name} has been uninstalled from cluster {cluster_name}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to uninstall: {result.stderr}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to list releases: {list_result.stderr}"
                }
                
        except Exception as e:
            print(f"Exception during uninstall: {str(e)}")
            return {
                "success": False,
                "error": f"Uninstall failed: {str(e)}"
            }
    
    def _cluster_exists(self, cluster_name: str) -> bool:
        """Check if cluster exists (supports both kind and k3d)"""
        try:
            # Check k3d clusters
            result = subprocess.run(
                ["k3d", "cluster", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                k3d_clusters = json.loads(result.stdout)
                for cluster in k3d_clusters:
                    if cluster.get("name") == cluster_name:
                        return True
            
            # Check kind clusters
            result = subprocess.run(
                ["kind", "get", "clusters"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                clusters = result.stdout.strip().split('\n')
                if cluster_name in clusters:
                    return True
            
            return False
        except Exception as e:
            print(f"Warning: Could not check cluster existence: {e}")
            return False
    
    def _create_namespace(self, cluster_name: str, namespace: str):
        """Create namespace if it doesn't exist"""
        try:
            context = self._get_cluster_context(cluster_name)
            
            cmd = [
                "kubectl", "create", "namespace", namespace,
                "--context", context,
                "--dry-run=client", "-o", "yaml"
            ]
            
            dry_run = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if dry_run.returncode == 0:
                apply_cmd = [
                    "kubectl", "apply", "--context", context,
                    "-f", "-"
                ]
                subprocess.run(apply_cmd, input=dry_run.stdout, capture_output=True, text=True, timeout=10)
                
        except Exception as e:
            print(f"Warning: Could not create namespace {namespace}: {e}")
    
    def _add_helm_repos(self, helm_chart: str):
        """Add Helm repository if needed"""
        try:
            repo_map = {
                'bitnami/': ('bitnami', 'https://charts.bitnami.com/bitnami'),
                'jenkins/': ('jenkins', 'https://charts.jenkins.io'),
                'gitea-charts/': ('gitea-charts', 'https://dl.gitea.io/charts/'),
                'prometheus-community/': ('prometheus-community', 'https://prometheus-community.github.io/helm-charts'),
                'grafana/': ('grafana', 'https://grafana.github.io/helm-charts'),
                'nginx/': ('nginx', 'https://kubernetes.github.io/ingress-nginx'),
                'traefik/': ('traefik', 'https://helm.traefik.io/traefik'),
            }
            
            for prefix, (repo_name, repo_url) in repo_map.items():
                if helm_chart.startswith(prefix):

                    subprocess.run([
                        "helm", "repo", "add", repo_name, repo_url
                    ], capture_output=True, timeout=30)
                    
                    subprocess.run([
                        "helm", "repo", "update"
                    ], capture_output=True, timeout=60)
                    break
                    
        except Exception as e:
            print(f"Warning: Could not add Helm repository: {e}")
    
    def _create_values_file(self, app_name: str, values: Dict[str, Any]) -> Optional[Path]:
        """Create temporary values file for Helm"""
        try:
            if not values:
                return None
                
            values_file = self.temp_dir / f"{app_name}-values.yaml"
            
            with open(values_file, 'w') as f:
                yaml.dump(values, f, default_flow_style=False)
            
            return values_file
            
        except Exception as e:
            print(f"Warning: Could not create values file: {e}")
            return None
    
    def _helm_install(self, cluster_name: str, release_name: str, chart: str, 
                     namespace: str, values_file: Optional[Path] = None) -> Dict[str, Any]:
        """Install Helm chart"""
        try:
            context = self._get_cluster_context(cluster_name)
            
            cmd = [
                "helm", "install", release_name, chart,
                "--namespace", namespace,
                "--create-namespace",
                "--kube-context", context,
                "--wait",
                "--timeout", "10m"
            ]
            
            if values_file and values_file.exists():
                cmd.extend(["-f", str(values_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully installed {release_name}",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": f"Helm install failed: {result.stderr}",
                    "output": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Installation timed out (10 minutes)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Installation error: {str(e)}"
            }
