import subprocess
import json
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class BackupService:
    """Service for creating and managing Kubernetes cluster backups"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        # Use provided backup directory or default to 'backups' in current directory
        if backup_dir:
            self.backup_dir = Path(backup_dir).expanduser().resolve()
        else:
            # Check environment variable first
            env_backup_dir = os.environ.get('CLUSTER_BACKUP_DIR')
            if env_backup_dir:
                self.backup_dir = Path(env_backup_dir).expanduser().resolve()
            else:
                # Default to 'backups' directory in current working directory
                self.backup_dir = Path.cwd() / "backups"
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Backup directory: {self.backup_dir}")
    
    def get_backup_directory_info(self) -> Dict[str, Any]:
        """Get information about backup directory"""
        return {
            "backup_directory": str(self.backup_dir),
            "exists": self.backup_dir.exists(),
            "is_writable": os.access(self.backup_dir, os.W_OK),
            "total_backups": len(list(self.backup_dir.glob("*.zip"))),
            "total_size_mb": sum(f.stat().st_size for f in self.backup_dir.glob("*.zip")) / (1024 * 1024)
        }
    
    def change_backup_directory(self, new_directory: str) -> Dict[str, Any]:
        """Change backup directory to a new location"""
        try:
            new_path = Path(new_directory).expanduser().resolve()
            
            # Create directory if it doesn't exist
            new_path.mkdir(parents=True, exist_ok=True)
            
            # Test if we can write to the directory
            test_file = new_path / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Cannot write to directory: {str(e)}",
                    "message": f"Nie można zapisywać w katalogu {new_directory}"
                }
            
            # Update backup directory
            old_directory = str(self.backup_dir)
            self.backup_dir = new_path
            
            return {
                "success": True,
                "message": f"Katalog backup zmieniony z {old_directory} na {new_directory}",
                "old_directory": old_directory,
                "new_directory": str(new_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd podczas zmiany katalogu: {str(e)}"
            }
    
    def create_cluster_backup(self, cluster_name: str, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a comprehensive backup of a Kubernetes cluster using etcd snapshot"""
        
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{cluster_name}_backup_{timestamp}"
        
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            # Create temporary directory for backup files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 1. Try to create ETCD snapshot (primary backup method)
                etcd_success = self._backup_etcd_snapshot(cluster_name, temp_path)
                
                # 2. Backup Kubernetes resources as fallback/supplement
                resources_backed_up = self._backup_kubernetes_resources(cluster_name, temp_path)
                
                # 3. Backup cluster info
                cluster_info = self._backup_cluster_info(cluster_name, temp_path)
                
                # 4. Create backup manifest
                manifest = {
                    "backup_name": backup_name,
                    "cluster_name": cluster_name,
                    "created_at": datetime.now().isoformat(),
                    "etcd_snapshot": etcd_success,
                    "resources": resources_backed_up,
                    "cluster_info": cluster_info,
                    "backup_type": "etcd_snapshot" if etcd_success else "resources_only"
                }
                
                manifest_path = temp_path / "backup_manifest.json"
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                
                # 5. Create ZIP archive
                self._create_zip_archive(temp_path, backup_path)
                
                backup_type = "ETCD snapshot + zasoby" if etcd_success else "Tylko zasoby K8s"
                
                return {
                    "success": True,
                    "backup_name": backup_name,
                    "backup_path": str(backup_path),
                    "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2),
                    "resources_count": len(resources_backed_up),
                    "created_at": manifest["created_at"],
                    "backup_type": backup_type,
                    "etcd_snapshot": etcd_success,
                    "message": f"Backup klastra {cluster_name} utworzony pomyślnie ({backup_type})"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd podczas tworzenia backupu: {str(e)}"
            }
    
    def _backup_etcd_snapshot(self, cluster_name: str, backup_path: Path) -> bool:
        """Create ETCD snapshot backup for Kind cluster"""
        try:
            # For Kind clusters, we need to access etcd inside the control-plane container
            control_plane_container = f"{cluster_name}-control-plane"
            snapshot_file = backup_path / f"etcd_snapshot_{cluster_name}.db"
            
            # Method 1: Try to use etcdctl directly in the Kind container
            etcdctl_cmd = [
                "docker", "exec", control_plane_container,
                "etcdctl", "snapshot", "save", "/tmp/etcd_backup.db",
                "--endpoints=https://127.0.0.1:2379",
                "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
                "--cert=/etc/kubernetes/pki/etcd/server.crt", 
                "--key=/etc/kubernetes/pki/etcd/server.key"
            ]
            
            result = subprocess.run(etcdctl_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Copy the snapshot from container to host
                copy_cmd = [
                    "docker", "cp", 
                    f"{control_plane_container}:/tmp/etcd_backup.db",
                    str(snapshot_file)
                ]
                
                copy_result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=30)
                
                if copy_result.returncode == 0 and snapshot_file.exists():
                    # Clean up temporary file in container
                    subprocess.run([
                        "docker", "exec", control_plane_container,
                        "rm", "-f", "/tmp/etcd_backup.db"
                    ], capture_output=True, timeout=10)
                    
                    print(f"ETCD snapshot created successfully: {snapshot_file}")
                    return True
                else:
                    print(f"Failed to copy ETCD snapshot: {copy_result.stderr}")
            else:
                print(f"ETCD snapshot failed: {result.stderr}")
                
                # Method 2: Fallback - try alternative etcd backup approach
                return self._backup_etcd_alternative(cluster_name, backup_path)
                
        except subprocess.TimeoutExpired:
            print("ETCD snapshot timed out")
        except Exception as e:
            print(f"ETCD snapshot error: {e}")
        
        return False
    
    def _backup_etcd_alternative(self, cluster_name: str, backup_path: Path) -> bool:
        """Alternative ETCD backup method using kubectl"""
        try:
            # Try to backup etcd data directory directly
            control_plane_container = f"{cluster_name}-control-plane"
            etcd_data_backup = backup_path / f"etcd_data_{cluster_name}.tar.gz"
            
            # Create tar archive of etcd data directory
            tar_cmd = [
                "docker", "exec", control_plane_container,
                "tar", "-czf", "/tmp/etcd_data_backup.tar.gz",
                "-C", "/var/lib/etcd", "."
            ]
            
            result = subprocess.run(tar_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Copy the archive from container to host
                copy_cmd = [
                    "docker", "cp",
                    f"{control_plane_container}:/tmp/etcd_data_backup.tar.gz",
                    str(etcd_data_backup)
                ]
                
                copy_result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=30)
                
                if copy_result.returncode == 0 and etcd_data_backup.exists():
                    # Clean up temporary file
                    subprocess.run([
                        "docker", "exec", control_plane_container,
                        "rm", "-f", "/tmp/etcd_data_backup.tar.gz"
                    ], capture_output=True, timeout=10)
                    
                    print(f"ETCD data backup created: {etcd_data_backup}")
                    return True
                    
        except Exception as e:
            print(f"Alternative ETCD backup failed: {e}")
        
        return False
    
    def restore_cluster_backup(self, backup_name: str, new_cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Restore a cluster from backup"""
        backup_file = self.backup_dir / f"{backup_name}.zip"
        
        if not backup_file.exists():
            return {
                "success": False,
                "error": "Backup file not found",
                "message": f"Backup {backup_name} nie został znaleziony"
            }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract backup
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(temp_path)
                
                # Read manifest
                manifest_file = temp_path / "backup_manifest.json"
                if not manifest_file.exists():
                    return {
                        "success": False,
                        "error": "Invalid backup file - missing manifest"
                    }
                
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                original_cluster = manifest.get("cluster_name")
                target_cluster = new_cluster_name or f"{original_cluster}_restored"
                
                # Check if target cluster already exists
                result = subprocess.run([
                    "kind", "get", "clusters"
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and target_cluster in result.stdout:
                    return {
                        "success": False,
                        "error": f"Cluster {target_cluster} already exists",
                        "message": f"Klaster {target_cluster} już istnieje. Użyj innej nazwy."
                    }
                
                # Restore based on backup type
                if manifest.get("etcd_snapshot", False):
                    return self._restore_from_etcd_snapshot(manifest, temp_path, target_cluster)
                else:
                    return self._restore_from_resources(manifest, temp_path, target_cluster)
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd podczas przywracania backupu: {str(e)}"
            }
    
    def _restore_from_etcd_snapshot(self, manifest: Dict, backup_path: Path, target_cluster: str) -> Dict[str, Any]:
        """Restore cluster from ETCD snapshot"""
        try:
            # This is complex for Kind clusters - would require:
            # 1. Creating new cluster
            # 2. Stopping etcd
            # 3. Restoring snapshot
            # 4. Starting etcd
            # For now, fallback to resource restoration
            
            return {
                "success": False,
                "error": "ETCD snapshot restore not yet implemented for Kind clusters",
                "message": "Przywracanie z snapshotu ETCD nie jest jeszcze zaimplementowane dla klastrów Kind. Użyj przywracania z zasobów YAML."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd przywracania z ETCD: {str(e)}"
            }
    
    def _restore_from_resources(self, manifest: Dict, backup_path: Path, target_cluster: str) -> Dict[str, Any]:
        """Restore cluster from Kubernetes resource YAML files"""
        try:
            # Create new cluster first
            cluster_info = manifest.get("cluster_info", {})
            node_count = len(cluster_info.get("nodes", {}).get("items", [])) or 3
            
            # Use Kind to create new cluster
            create_cmd = [
                "kind", "create", "cluster",
                "--name", target_cluster,
                f"--config=-"  # We'll provide config via stdin
            ]
            
            # Basic cluster config
            cluster_config = f"""
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
"""
            for i in range(node_count - 1):
                cluster_config += "- role: worker\n"
            
            result = subprocess.run(create_cmd, input=cluster_config, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create cluster: {result.stderr}",
                    "message": f"Nie udało się utworzyć klastra {target_cluster}"
                }
            
            # Apply resources
            restored_resources = []
            for yaml_file in backup_path.glob("*.yaml"):
                if yaml_file.name != "cluster_info.yaml":
                    apply_result = subprocess.run([
                        "kubectl", "apply", "-f", str(yaml_file),
                        "--context", f"kind-{target_cluster}"
                    ], capture_output=True, text=True, timeout=60)
                    
                    if apply_result.returncode == 0:
                        restored_resources.append(yaml_file.name)
                    else:
                        print(f"Warning: Could not restore {yaml_file.name}: {apply_result.stderr}")
            
            return {
                "success": True,
                "message": f"Klaster {target_cluster} został przywrócony z backupu",
                "cluster_name": target_cluster,
                "restored_resources": restored_resources,
                "resources_count": len(restored_resources)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd przywracania z zasobów: {str(e)}"
            }
    
    def _backup_kubernetes_resources(self, cluster_name: str, backup_path: Path) -> List[Dict[str, Any]]:
        """Backup all Kubernetes resources"""
        resources_backed_up = []
        
        # Common Kubernetes resource types to backup
        resource_types = [
            "deployments",
            "services", 
            "configmaps",
            "secrets",
            "persistentvolumeclaims",
            "ingresses",
            "networkpolicies",
            "serviceaccounts",
            "roles",
            "rolebindings",
            "clusterroles", 
            "clusterrolebindings",
            "statefulsets",
            "daemonsets",
            "jobs",
            "cronjobs",
            "horizontalpodautoscalers"
        ]
        
        # Get all namespaces first
        namespaces = self._get_namespaces(cluster_name)
        
        for resource_type in resource_types:
            try:
                # Backup cluster-wide resources
                if resource_type in ["clusterroles", "clusterrolebindings", "persistentvolumes"]:
                    self._backup_resource_type(cluster_name, resource_type, None, backup_path)
                    resources_backed_up.append({
                        "type": resource_type,
                        "namespace": None,
                        "scope": "cluster"
                    })
                else:
                    # Backup namespaced resources
                    for namespace in namespaces:
                        if self._backup_resource_type(cluster_name, resource_type, namespace, backup_path):
                            resources_backed_up.append({
                                "type": resource_type,
                                "namespace": namespace,
                                "scope": "namespaced"
                            })
            except Exception as e:
                print(f"Warning: Could not backup {resource_type}: {e}")
        
        return resources_backed_up
    
    def _get_namespaces(self, cluster_name: str) -> List[str]:
        """Get all namespaces in the cluster"""
        try:
            result = subprocess.run([
                "kubectl", "get", "namespaces",
                "--context", f"kind-{cluster_name}",
                "-o", "jsonpath={.items[*].metadata.name}"
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                return result.stdout.strip().split()
            return ["default", "kube-system", "kube-public"]
        except:
            return ["default", "kube-system", "kube-public"]
    
    def _backup_resource_type(self, cluster_name: str, resource_type: str, namespace: Optional[str], backup_path: Path) -> bool:
        """Backup specific resource type"""
        try:
            cmd = ["kubectl", "get", resource_type, "--context", f"kind-{cluster_name}", "-o", "yaml"]
            
            if namespace:
                cmd.extend(["-n", namespace])
                output_file = backup_path / f"{namespace}_{resource_type}.yaml"
            else:
                output_file = backup_path / f"cluster_{resource_type}.yaml"
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0 and result.stdout.strip():
                # Clean up the YAML (remove runtime fields)
                cleaned_yaml = self._clean_kubernetes_yaml(result.stdout)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_yaml)
                return True
            return False
        except Exception:
            return False
    
    def _clean_kubernetes_yaml(self, yaml_content: str) -> str:
        """Clean up Kubernetes YAML by removing runtime/generated fields"""
        try:
            docs = list(yaml.safe_load_all(yaml_content))
            cleaned_docs = []
            
            for doc in docs:
                if doc and doc.get('kind') != 'List':
                    # Remove runtime fields
                    if 'metadata' in doc:
                        metadata = doc['metadata']
                        # Remove runtime metadata
                        for field in ['resourceVersion', 'uid', 'generation', 'managedFields', 'creationTimestamp']:
                            metadata.pop(field, None)
                    
                    # Remove status section
                    doc.pop('status', None)
                    
                    cleaned_docs.append(doc)
            
            # Convert back to YAML
            return yaml.dump_all(cleaned_docs, default_flow_style=False, allow_unicode=True)
        except:
            # If parsing fails, return original content
            return yaml_content
    
    def _backup_cluster_info(self, cluster_name: str, backup_path: Path) -> Dict[str, Any]:
        """Backup cluster information"""
        cluster_info = {
            "cluster_name": cluster_name,
            "context": f"kind-{cluster_name}"
        }
        
        try:
            # Get cluster version
            result = subprocess.run([
                "kubectl", "version", "--context", f"kind-{cluster_name}", "-o", "json"
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                version_info = json.loads(result.stdout)
                cluster_info["kubernetes_version"] = version_info.get("serverVersion", {})
        except:
            pass
        
        try:
            # Get nodes information
            result = subprocess.run([
                "kubectl", "get", "nodes", "--context", f"kind-{cluster_name}", "-o", "json"
            ], capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                nodes_info = json.loads(result.stdout)
                cluster_info["nodes"] = nodes_info
        except:
            pass
        
        # Save cluster info
        info_file = backup_path / "cluster_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(cluster_info, f, indent=2, ensure_ascii=False)
        
        return cluster_info
    
    def _create_zip_archive(self, source_dir: Path, output_path: Path):
        """Create ZIP archive from directory"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                # Extract backup manifest to get metadata
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if 'backup_manifest.json' in zipf.namelist():
                        manifest_content = zipf.read('backup_manifest.json').decode('utf-8')
                        manifest = json.loads(manifest_content)
                        
                        backup_info = {
                            "backup_name": manifest.get("backup_name", backup_file.stem),
                            "cluster_name": manifest.get("cluster_name", "unknown"),
                            "created_at": manifest.get("created_at", "unknown"),
                            "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                            "resources_count": len(manifest.get("resources", [])),
                            "backup_type": manifest.get("backup_type", "unknown"),
                            "file_path": str(backup_file)
                        }
                        backups.append(backup_info)
            except Exception as e:
                # If we can't read manifest, add basic info
                backups.append({
                    "backup_name": backup_file.stem,
                    "cluster_name": "unknown",
                    "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                    "resources_count": 0,
                    "backup_type": "unknown",
                    "file_path": str(backup_file),
                    "error": f"Could not read manifest: {str(e)}"
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Delete a backup file"""
        backup_file = self.backup_dir / f"{backup_name}.zip"
        
        if not backup_file.exists():
            return {
                "success": False,
                "error": "Backup file not found",
                "message": f"Backup {backup_name} nie został znaleziony"
            }
        
        try:
            backup_file.unlink()
            return {
                "success": True,
                "message": f"Backup {backup_name} został usunięty pomyślnie"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Błąd podczas usuwania backupu: {str(e)}"
            }
    
    def get_backup_details(self, backup_name: str) -> Dict[str, Any]:
        """Get detailed information about a backup"""
        backup_file = self.backup_dir / f"{backup_name}.zip"
        
        if not backup_file.exists():
            return {
                "success": False,
                "error": "Backup file not found"
            }
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                if 'backup_manifest.json' in zipf.namelist():
                    manifest_content = zipf.read('backup_manifest.json').decode('utf-8')
                    manifest = json.loads(manifest_content)
                    
                    # Add file information
                    manifest["file_info"] = {
                        "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                        "file_count": len(zipf.namelist()),
                        "files": zipf.namelist()
                    }
                    
                    return {
                        "success": True,
                        "backup_details": manifest
                    }
            
            return {
                "success": False,
                "error": "Backup manifest not found in archive"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
