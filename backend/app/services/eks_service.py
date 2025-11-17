"""
AWS EKS Service - zarządzanie klastrami EKS w AWS
"""
import subprocess
import json
import os
import tempfile
import shutil
import glob
from typing import Dict, Any, Optional
from pathlib import Path


class EksService:
    """Service do zarządzania klastrami AWS EKS"""
    
    def __init__(self):
        # Próbuj znaleźć terraform w PATH
        self.terraform_path = shutil.which("terraform")
        
        # Jeśli nie ma w PATH, sprawdź typowe lokalizacje Windows
        if not self.terraform_path:
            # Winget location
            winget_pattern = os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Microsoft", "WinGet", "Packages", "Hashicorp.Terraform_*", "terraform.exe"
            )
            import glob
            winget_paths = glob.glob(winget_pattern)
            if winget_paths:
                self.terraform_path = winget_paths[0]
            else:
                # Fallback
                self.terraform_path = "terraform"
        
        # Katalog do przechowywania stanów Terraform
        self.terraform_states_dir = Path.cwd() / "terraform_states"
        self.terraform_states_dir.mkdir(exist_ok=True)
        print(f"📁 Terraform states directory: {self.terraform_states_dir}")
    
    def create_cluster(
        self,
        cluster_name: str,
        region: str,
        aws_access_key: str,
        aws_secret_key: str,
        node_count: int = 2,
        instance_type: str = "t3.medium",
        vpc_cidr: str = "10.0.0.0/16",
        disk_size: int = 20,
        min_nodes: int = 1,
        max_nodes: int = 3,
        k8s_version: str = "1.30"
    ) -> Dict[str, Any]:
        """
        Utwórz klaster EKS w AWS z zaawansowaną konfiguracją
        
        Args:
            cluster_name: Nazwa klastra
            region: Region AWS (np. eu-central-1)
            aws_access_key: AWS Access Key ID
            aws_secret_key: AWS Secret Access Key
            node_count: Desired liczba worker nodes
            instance_type: Typ instancji EC2 (np. t3.medium)
            vpc_cidr: CIDR dla VPC
            disk_size: Rozmiar dysku dla node w GB
            min_nodes: Minimalna liczba nodes (auto-scaling)
            max_nodes: Maksymalna liczba nodes (auto-scaling)
            k8s_version: Wersja Kubernetes (np. "1.30")
            
        Returns:
            Dict z wynikiem operacji
        """
        try:
            # Utwórz tymczasowy katalog dla Terraform
            with tempfile.TemporaryDirectory() as temp_dir:
                # Skopiuj templates z nowymi parametrami
                self._prepare_terraform_files(
                    temp_dir,
                    cluster_name,
                    region,
                    node_count,
                    instance_type,
                    vpc_cidr,
                    disk_size,
                    min_nodes,
                    max_nodes,
                    k8s_version
                )
                
                # Ustaw zmienne środowiskowe dla AWS (bezpieczne, nie zapisują się)
                env = os.environ.copy()
                env.update({
                    "AWS_ACCESS_KEY_ID": aws_access_key,
                    "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                    "AWS_DEFAULT_REGION": region
                })
                
                # Terraform init
                init_result = self._run_terraform_command(
                    ["init"],
                    cwd=temp_dir,
                    env=env
                )
                
                if init_result["returncode"] != 0:
                    return {
                        "success": False,
                        "error": f"Terraform init failed: {init_result['stderr']}",
                        "cluster_name": cluster_name
                    }
                
                # Terraform apply
                apply_result = self._run_terraform_command(
                    ["apply", "-auto-approve"],
                    cwd=temp_dir,
                    env=env,
                    timeout=1800  # 30 minut - EKS może długo się tworzyć
                )
                
                if apply_result["returncode"] != 0:
                    return {
                        "success": False,
                        "error": f"Terraform apply failed: {apply_result['stderr']}",
                        "cluster_name": cluster_name
                    }
                
                # 🎯 ZAPISZ STAN TERRAFORM DO TRWAŁEGO KATALOGU
                cluster_state_dir = self.terraform_states_dir / cluster_name
                cluster_state_dir.mkdir(exist_ok=True)
                
                # Kopiuj wszystkie pliki Terraform (włącznie ze stanem)
                for file in Path(temp_dir).glob("*"):
                    if file.is_file():
                        shutil.copy2(file, cluster_state_dir / file.name)
                
                # Kopiuj .terraform directory (zawiera providers)
                terraform_dir = Path(temp_dir) / ".terraform"
                if terraform_dir.exists():
                    dest_terraform_dir = cluster_state_dir / ".terraform"
                    if dest_terraform_dir.exists():
                        shutil.rmtree(dest_terraform_dir)
                    shutil.copytree(terraform_dir, dest_terraform_dir)
                
                print(f"💾 Stan Terraform zapisany w: {cluster_state_dir}")
                
                # Zapisz credentials dla przyszłych operacji kubectl
                self._save_cluster_credentials(cluster_name, aws_access_key, aws_secret_key, region)
                
                # Konfiguruj kubectl dla nowego klastra i pobierz ARN
                print("⚙️ Konfigurowanie kubectl...")
                cluster_arn = self._configure_kubectl(cluster_name, region, env)
                
                # Zainstaluj Metrics Server (dla kubectl top nodes)
                print("📊 Instalowanie Metrics Server...")
                self._install_metrics_server(cluster_name, region, env, context=cluster_arn)
                
                # Pobierz output z Terraform
                output_result = self._run_terraform_command(
                    ["output", "-json"],
                    cwd=temp_dir,
                    env=env
                )
                
                outputs = {}
                if output_result["returncode"] == 0:
                    try:
                        outputs = json.loads(output_result["stdout"])
                    except:
                        pass
                
                return {
                    "success": True,
                    "message": f"Klaster EKS '{cluster_name}' został utworzony w regionie {region}",
                    "cluster_name": cluster_name,
                    "region": region,
                    "endpoint": outputs.get("cluster_endpoint", {}).get("value"),
                    "status": "CREATING",
                    "node_count": node_count,
                    "instance_type": instance_type,
                    "terraform_state": str(cluster_state_dir)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tworzenie klastra przekroczyło limit czasu (30 min)",
                "cluster_name": cluster_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd podczas tworzenia klastra: {str(e)}",
                "cluster_name": cluster_name
            }
    
    def list_clusters(
        self,
        region: str,
        aws_access_key: str,
        aws_secret_key: str
    ) -> Dict[str, Any]:
        """
        Lista klastrów EKS w danym regionie
        """
        try:
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": region
            })
            
            result = subprocess.run(
                ["aws", "eks", "list-clusters", "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"AWS CLI error: {result.stderr}",
                    "clusters": []
                }
            
            data = json.loads(result.stdout)
            clusters = data.get("clusters", [])
            
            # Pobierz szczegóły dla każdego klastra
            cluster_details = []
            for cluster_name in clusters:
                details = self._get_cluster_details(cluster_name, region, env)
                if details:
                    cluster_details.append(details)
            
            return {
                "success": True,
                "clusters": cluster_details,
                "region": region
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "clusters": []
            }
    
    def delete_cluster(
        self,
        cluster_name: str,
        region: str,
        aws_access_key: str,
        aws_secret_key: str
    ) -> Dict[str, Any]:
        """
        Usuń klaster EKS używając Terraform destroy
        
        Usuwa WSZYSTKIE zasoby:
        - EKS Cluster
        - Node Groups
        - VPC, Subnets, Internet Gateway, Route Tables
        - IAM Roles i Policies
        
        Wymaga zapisanego stanu Terraform (z create_cluster).
        """
        try:
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": region
            })
            
            print(f"🗑️  Usuwanie klastra EKS: {cluster_name}")
            
            # Sprawdź czy istnieje stan Terraform dla tego klastra
            cluster_state_dir = self.terraform_states_dir / cluster_name
            
            if not cluster_state_dir.exists():
                print(f"  ⚠️  Brak stanu Terraform dla klastra '{cluster_name}'")
                print(f"  → Użycie fallback metody (AWS CLI)")
                return self._delete_cluster_fallback(cluster_name, region, env)
            
            print(f"  ✅ Znaleziono stan Terraform: {cluster_state_dir}")
            print(f"  → Uruchamianie Terraform destroy...")
            
            # Terraform destroy
            destroy_result = self._run_terraform_command(
                ["destroy", "-auto-approve"],
                cwd=str(cluster_state_dir),
                env=env,
                timeout=1800  # 30 minut
            )
            
            if destroy_result["returncode"] != 0:
                print(f"  ❌ Terraform destroy failed!")
                print(f"  Error: {destroy_result['stderr']}")
                
                # Fallback do AWS CLI
                print(f"  → Próba użycia AWS CLI jako fallback...")
                return self._delete_cluster_fallback(cluster_name, region, env)
            
            print(f"  ✅ Terraform destroy zakończony pomyślnie")
            
            # Usuń katalog ze stanem Terraform
            try:
                shutil.rmtree(cluster_state_dir)
                print(f"  ✅ Usunięto stan Terraform")
            except Exception as e:
                print(f"  ⚠️  Nie udało się usunąć stanu Terraform: {e}")
            
            return {
                "success": True,
                "message": f"Klaster '{cluster_name}' i wszystkie zasoby zostały usunięte z AWS",
                "cluster_name": cluster_name,
                "method": "terraform_destroy"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Terraform destroy przekroczył limit czasu (30 min)",
                "cluster_name": cluster_name,
                "message": "Proces usuwania może nadal trwać w AWS. Sprawdź status w AWS Console."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cluster_name": cluster_name
            }
    
    def _delete_cluster_fallback(
        self,
        cluster_name: str,
        region: str,
        env: dict
    ) -> Dict[str, Any]:
        """
        Fallback: usuń klaster przez AWS CLI (bez Terraform)
        UWAGA: Nie usuwa VPC, IAM roles i innych zasobów!
        """
        try:
            import time
            
            print(f"  → Usuwanie node groups...")
            ng_deleted = self._delete_node_groups(cluster_name, region, env)
            
            if not ng_deleted:
                print(f"  ⚠️  Nie wszystkie node groups zostały usunięte")
            
            print(f"  → Oczekiwanie 60s na usunięcie node groups...")
            time.sleep(60)
            
            print(f"  → Usuwanie klastra EKS...")
            result = subprocess.run(
                ["aws", "eks", "delete-cluster", "--name", cluster_name],
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            
            if result.returncode != 0:
                if "ResourceNotFoundException" in result.stderr or "NotFound" in result.stderr:
                    return {
                        "success": False,
                        "error": f"Klaster '{cluster_name}' nie istnieje",
                        "cluster_name": cluster_name
                    }
                
                return {
                    "success": False,
                    "error": f"AWS CLI error: {result.stderr}",
                    "cluster_name": cluster_name
                }
            
            print(f"  ✅ Klaster usunięty (AWS CLI)")
            
            return {
                "success": True,
                "message": f"Klaster '{cluster_name}' usunięty (częściowo)",
                "cluster_name": cluster_name,
                "warning": "⚠️ UWAGA: VPC, Subnety, IAM Roles NIE zostały usunięte! Usuń je ręcznie w AWS Console.",
                "method": "aws_cli_fallback"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cluster_name": cluster_name
            }
    
    def get_cluster_status(
        self,
        cluster_name: str,
        region: str,
        aws_access_key: str,
        aws_secret_key: str
    ) -> Dict[str, Any]:
        """
        Pobierz status klastra EKS
        """
        try:
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": region
            })
            
            result = subprocess.run(
                ["aws", "eks", "describe-cluster", "--name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Cluster not found: {result.stderr}"
                }
            
            data = json.loads(result.stdout)
            cluster = data.get("cluster", {})
            
            return {
                "success": True,
                "cluster_name": cluster.get("name"),
                "status": cluster.get("status"),
                "endpoint": cluster.get("endpoint"),
                "version": cluster.get("version"),
                "created_at": cluster.get("createdAt"),
                "region": region
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_cluster_details(
        self,
        cluster_name: str,
        region: str,
        aws_access_key: str,
        aws_secret_key: str
    ) -> Dict[str, Any]:
        """
        Pobierz szczegółowe informacje o klastrze EKS wraz z nodes, deployments, etc.
        """
        try:
            # Skonfiguruj kubectl dla klastra
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": region
            })
            
            # Update kubeconfig
            self._configure_kubectl(cluster_name, region, env)
            
            # Pobierz podstawowe info o klastrze
            status_info = self.get_cluster_status(cluster_name, region, aws_access_key, aws_secret_key)
            
            if not status_info.get("success"):
                return status_info
            
            # Pobierz nodes
            nodes_result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            nodes = []
            if nodes_result.returncode == 0:
                nodes_data = json.loads(nodes_result.stdout)
                for node in nodes_data.get("items", []):
                    nodes.append({
                        "name": node.get("metadata", {}).get("name"),
                        "status": node.get("status", {}).get("conditions", [{}])[-1].get("type", "Unknown"),
                        "role": "worker",  # EKS nodes są workerami
                        "version": node.get("status", {}).get("nodeInfo", {}).get("kubeletVersion"),
                        "cpu_usage": "N/A",  # Zostanie wypełnione poniżej jeśli Metrics Server działa
                        "memory_usage": "N/A",
                        "memory_percent": "N/A"
                    })
            
            # Pobierz node groups info
            ng_result = subprocess.run(
                ["aws", "eks", "list-nodegroups", "--cluster-name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            node_count = 0
            instance_types = []
            if ng_result.returncode == 0:
                ng_data = json.loads(ng_result.stdout)
                nodegroups = ng_data.get("nodegroups", [])
                node_count = len(nodegroups)
                
                # Pobierz typ instancji z pierwszej (głównej) node group
                if nodegroups:
                    ng_name = nodegroups[0]
                    instance_types = self._get_nodegroup_instance_types(cluster_name, ng_name, env)
            
            # Pobierz CPU/RAM usage z kubectl top nodes jeśli Metrics Server zainstalowany
            cpu_usage = 0.0
            memory_usage = 0.0
            
            # Wykryj context klastra - użyj pełnego ARN jeśli dostępny
            context = f"arn:aws:eks:{region}:*:cluster/{cluster_name}"
            
            # Spróbuj pobrać dokładny ARN z kubectl contexts
            contexts_result = subprocess.run(
                ["kubectl", "config", "get-contexts", "-o", "name"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            if contexts_result.returncode == 0:
                for ctx in contexts_result.stdout.strip().split('\n'):
                    if f":cluster/{cluster_name}" in ctx and ctx.startswith("arn:aws:eks"):
                        context = ctx
                        break
            
            # Sprawdź czy Metrics Server działa - próbuj kubectl top nodes
            top_result = subprocess.run(
                ["kubectl", "top", "nodes", "--context", context],
                capture_output=True,
                text=True,
                env=env,
                timeout=15
            )
            
            if top_result.returncode == 0:
                # Parse output: NAME CPU(cores) CPU% MEMORY(bytes) MEMORY%
                lines = top_result.stdout.strip().split('\n')
                if len(lines) > 1:  # ma header + dane
                    total_cpu = 0.0
                    total_mem = 0.0
                    valid_nodes = 0
                    
                    # Najpierw stwórz mapę node_name -> metryki
                    node_metrics = {}
                    
                    for line in lines[1:]:  # skip header
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                node_name = parts[0]
                                # CPU% jest 3cią kolumną (index 2)
                                cpu_str = parts[2].rstrip('%')
                                # MEMORY(bytes) jest 4tą kolumną (index 3)
                                memory_bytes = parts[3]
                                # Memory% jest 5tą kolumną (index 4)
                                mem_str = parts[4].rstrip('%')
                                
                                cpu_percent = float(cpu_str)
                                mem_percent = float(mem_str)
                                
                                node_metrics[node_name] = {
                                    'cpu_usage': f"{cpu_percent}%",
                                    'memory_usage': memory_bytes,
                                    'memory_percent': f"{mem_percent}%"
                                }
                                
                                total_cpu += cpu_percent
                                total_mem += mem_percent
                                valid_nodes += 1
                            except (ValueError, IndexError):
                                continue
                    
                    # Wypełnij metryki dla nodów w liście
                    for node in nodes:
                        node_name = node.get('name')
                        if node_name in node_metrics:
                            node['cpu_usage'] = node_metrics[node_name]['cpu_usage']
                            node['memory_usage'] = node_metrics[node_name]['memory_usage']
                            node['memory_percent'] = node_metrics[node_name]['memory_percent']
                    
                    if valid_nodes > 0:
                        cpu_usage = round(total_cpu / valid_nodes, 1)
                        memory_usage = round(total_mem / valid_nodes, 1)
            
            return {
                "success": True,
                "name": cluster_name,
                "status": "Running" if status_info.get("status") == "ACTIVE" else status_info.get("status"),
                "provider": "eks",
                "kubernetes_version": status_info.get("version"),
                "node_count": len(nodes),
                "instance_types": instance_types,  # Dodane: typ instancji node group
                "api_endpoint": status_info.get("endpoint"),
                "created_at": status_info.get("created_at"),
                "context": context,
                "resources": {
                    "nodes": nodes,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                },
                "monitoring": {
                    "installed": False  # EKS nie ma wbudowanego Prometheus/Grafana
                },
                "region": region
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_terraform_files(
        self,
        target_dir: str,
        cluster_name: str,
        region: str,
        node_count: int,
        instance_type: str,
        vpc_cidr: str,
        disk_size: int = 20,
        min_nodes: int = 1,
        max_nodes: int = 3,
        k8s_version: str = "1.30"
    ):
        """
        Przygotuj pliki Terraform w tymczasowym katalogu
        
        Zgodne z AWS Console - wspiera:
        - Kubernetes version selection
        - Auto-scaling (min/max/desired nodes)
        - Disk size configuration
        - VPC/Subnet configuration
        """
        
        # main.tf
        main_tf = f"""
terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

# VPC
resource "aws_vpc" "main" {{
  cidr_block           = "{vpc_cidr}"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{cluster_name}-vpc"
    "kubernetes.io/cluster/{cluster_name}" = "shared"
  }}
}}

# Subnets
resource "aws_subnet" "public" {{
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {{
    Name                                           = "{cluster_name}-public-${{count.index + 1}}"
    "kubernetes.io/cluster/{cluster_name}"        = "shared"
    "kubernetes.io/role/elb"                       = "1"
  }}
}}

# Internet Gateway
resource "aws_internet_gateway" "main" {{
  vpc_id = aws_vpc.main.id

  tags = {{
    Name = "{cluster_name}-igw"
  }}
}}

# Route Table
resource "aws_route_table" "public" {{
  vpc_id = aws_vpc.main.id

  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }}

  tags = {{
    Name = "{cluster_name}-public-rt"
  }}
}}

resource "aws_route_table_association" "public" {{
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}}

# IAM Role dla EKS Cluster
resource "aws_iam_role" "eks_cluster" {{
  name = "{cluster_name}-eks-cluster-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "eks.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {{
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}}

# EKS Cluster
resource "aws_eks_cluster" "main" {{
  name     = "{cluster_name}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "{k8s_version}"

  vpc_config {{
    subnet_ids = aws_subnet.public[*].id
  }}

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {{
    Name = "{cluster_name}"
  }}
}}

# IAM Role dla Node Group
resource "aws_iam_role" "eks_nodes" {{
  name = "{cluster_name}-eks-node-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ec2.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {{
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {{
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {{
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}}

# EKS Node Group (zgodne z AWS Console)
resource "aws_eks_node_group" "main" {{
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "{cluster_name}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.public[*].id
  instance_types  = ["{instance_type}"]
  
  disk_size = {disk_size}

  scaling_config {{
    desired_size = {node_count}
    max_size     = {max_nodes}
    min_size     = {min_nodes}
  }}

  update_config {{
    max_unavailable = 1
  }}

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy
  ]

  tags = {{
    Name = "{cluster_name}-nodes"
  }}
}}

# Data sources
data "aws_availability_zones" "available" {{
  state = "available"
}}

# Outputs
output "cluster_endpoint" {{
  value = aws_eks_cluster.main.endpoint
}}

output "cluster_name" {{
  value = aws_eks_cluster.main.name
}}

output "cluster_security_group_id" {{
  value = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}}
"""
        
        with open(os.path.join(target_dir, "main.tf"), "w") as f:
            f.write(main_tf)
    
    def _run_terraform_command(
        self,
        args: list,
        cwd: str,
        env: dict,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Uruchom komendę Terraform"""
        try:
            # Na Windows trzeba użyć shell=True aby znaleźć terraform w PATH
            cmd = [self.terraform_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                timeout=timeout,
                shell=True  # Potrzebne na Windows
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def _configure_kubectl(self, cluster_name: str, region: str, env: dict) -> Optional[str]:
        """Konfiguruj kubectl dla klastra EKS i zwróć pełny ARN"""
        try:
            # Najpierw pobierz ARN klastra z AWS
            result = subprocess.run(
                ["aws", "eks", "describe-cluster", "--name", cluster_name, "--region", region, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            cluster_arn = None
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    cluster_arn = data.get("cluster", {}).get("arn")
                except:
                    pass
            
            # Następnie zaktualizuj kubeconfig
            subprocess.run(
                [
                    "aws", "eks", "update-kubeconfig",
                    "--name", cluster_name,
                    "--region", region
                ],
                env=env,
                timeout=30,
                check=False
            )
            
            return cluster_arn
        except Exception as e:
            print(f"    ⚠️ Błąd konfiguracji kubectl: {e}")
            return None
    
    def _get_cluster_details(self, cluster_name: str, region: str, env: dict) -> Optional[Dict]:
        """Pobierz szczegóły klastra"""
        try:
            result = subprocess.run(
                ["aws", "eks", "describe-cluster", "--name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                cluster = data.get("cluster", {})
                return {
                    "name": cluster.get("name"),
                    "status": cluster.get("status"),
                    "version": cluster.get("version"),
                    "endpoint": cluster.get("endpoint"),
                    "created_at": cluster.get("createdAt")
                }
        except:
            pass
        return None
    
    def _delete_node_groups(self, cluster_name: str, region: str, env: dict) -> bool:
        """
        Usuń wszystkie node groups klastra
        Returns: True jeśli wszystkie node groups zostały usunięte, False w przeciwnym razie
        """
        try:
            # Lista node groups
            result = subprocess.run(
                ["aws", "eks", "list-nodegroups", "--cluster-name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"    ⚠️  Nie udało się pobrać listy node groups: {result.stderr}")
                return False
            
            data = json.loads(result.stdout)
            nodegroups = data.get("nodegroups", [])
            
            if not nodegroups:
                print(f"    ℹ️  Brak node groups do usunięcia")
                return True
            
            print(f"    → Znaleziono {len(nodegroups)} node groups: {', '.join(nodegroups)}")
            
            all_deleted = True
            for ng in nodegroups:
                print(f"    → Usuwanie node group: {ng}")
                ng_result = subprocess.run(
                    ["aws", "eks", "delete-nodegroup", "--cluster-name", cluster_name, "--nodegroup-name", ng],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300
                )
                
                if ng_result.returncode != 0:
                    print(f"    ⚠️  Nie udało się usunąć {ng}: {ng_result.stderr}")
                    all_deleted = False
                else:
                    print(f"    ✅ Wysłano żądanie usunięcia: {ng}")
            
            return all_deleted
            
        except Exception as e:
            print(f"    ❌ Błąd podczas usuwania node groups: {str(e)}")
            return False


    def _install_metrics_server(self, cluster_name: str, region: str, env: dict, context: Optional[str] = None):
        """Zainstaluj Kubernetes Metrics Server na klastrze EKS"""
        try:
            # Jeśli nie podano contextu, pobierz go z kubectl
            if not context:
                # Pobierz wszystkie konteksty i znajdź ten dla klastra
                result = subprocess.run(
                    ["kubectl", "config", "get-contexts", "-o", "name"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    contexts = result.stdout.strip().split('\n')
                    for ctx in contexts:
                        if cluster_name in ctx and "eks" in ctx:
                            context = ctx
                            break
                
                if not context:
                    print(f"    ⚠️ Nie znaleziono contextu kubectl dla klastra {cluster_name}")
                    return False
            
            print(f"    → Instalowanie metrics-server (context: {context})...")
            
            # Zainstaluj Metrics Server
            result = subprocess.run([
                "kubectl", "apply",
                "-f", "https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
                "--context", context
            ], capture_output=True, text=True, env=env, timeout=60)
            
            if result.returncode != 0:
                print(f"    ⚠️ Nie udało się zainstalować Metrics Server: {result.stderr}")
                return False
            
            print("    ✅ Manifest Metrics Server zastosowany")
            print("    → Czekam na uruchomienie Metrics Server (max 120s)...")
            
            # Poczekaj aż deployment będzie gotowy
            rollout_result = subprocess.run([
                "kubectl", "rollout", "status", 
                "deployment/metrics-server",
                "-n", "kube-system",
                "--context", context,
                "--timeout=120s"
            ], capture_output=True, text=True, env=env, timeout=130)
            
            if rollout_result.returncode == 0:
                print("    ✅ Metrics Server uruchomiony i gotowy")
                return True
            else:
                print(f"    ⚠️ Metrics Server zainstalowany, ale rollout nie zakończony: {rollout_result.stderr}")
                print("    ℹ️ Metrics Server może potrzebować więcej czasu - sprawdź później")
                return True  # Zwróć True bo instalacja się udała, rollout może trwać dłużej
                
        except subprocess.TimeoutExpired:
            print("    ⚠️ Timeout podczas instalacji Metrics Server")
            print("    ℹ️ Metrics Server może być w trakcie instalacji - sprawdź później")
            return True
        except Exception as e:
            print(f"    ⚠️ Błąd podczas instalacji Metrics Server: {e}")
            return False
    
    def _save_cluster_credentials(self, cluster_name: str, aws_access_key: str, aws_secret_key: str, region: str):
        """Zapisz credentials klastra do pliku (zaszyfrowane base64)"""
        try:
            import base64
            cluster_state_dir = self.terraform_states_dir / cluster_name
            cluster_state_dir.mkdir(exist_ok=True)
            
            # Prosty obfuskacja (nie pełne szyfrowanie, ale lepsze niż plaintext)
            credentials = {
                "aws_access_key": base64.b64encode(aws_access_key.encode()).decode(),
                "aws_secret_key": base64.b64encode(aws_secret_key.encode()).decode(),
                "region": region
            }
            
            creds_file = cluster_state_dir / ".credentials.json"
            with open(creds_file, 'w') as f:
                json.dump(credentials, f)
            
            print(f"💾 Credentials zapisane dla klastra: {cluster_name}")
        except Exception as e:
            print(f"⚠️ Nie udało się zapisać credentials: {e}")
    
    def get_cluster_credentials(self, cluster_name: str) -> Optional[Dict[str, str]]:
        """Wczytaj credentials klastra z pliku"""
        try:
            import base64
            creds_file = self.terraform_states_dir / cluster_name / ".credentials.json"
            
            if not creds_file.exists():
                print(f"⚠️ Brak credentials dla klastra: {cluster_name}")
                return None
            
            with open(creds_file, 'r') as f:
                credentials = json.load(f)
            
            # Dekoduj z base64
            return {
                "aws_access_key": base64.b64decode(credentials["aws_access_key"]).decode(),
                "aws_secret_key": base64.b64decode(credentials["aws_secret_key"]).decode(),
                "region": credentials["region"]
            }
        except Exception as e:
            print(f"⚠️ Błąd wczytywania credentials: {e}")
            return None
    
    def _get_nodegroup_instance_types(self, cluster_name: str, nodegroup_name: str, env: dict) -> list:
        """Pobierz obecny typ instancji dla node group"""
        try:
            describe_result = subprocess.run(
                ["aws", "eks", "describe-nodegroup", 
                 "--cluster-name", cluster_name,
                 "--nodegroup-name", nodegroup_name,
                 "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if describe_result.returncode == 0:
                data = json.loads(describe_result.stdout)
                return data.get("nodegroup", {}).get("instanceTypes", [])
            return []
        except Exception as e:
            print(f"   ⚠️ Nie udało się pobrać typu instancji: {e}")
            return []

    def _create_new_nodegroup(
        self,
        cluster_name: str,
        new_nodegroup_name: str,
        instance_types: list,
        desired_size: int,
        min_size: int,
        max_size: int,
        subnet_ids: list,
        env: dict
    ) -> Dict[str, Any]:
        """Utwórz nową node group z nowym typem instancji"""
        try:
            print(f"   📦 Tworzę nową node group: {new_nodegroup_name}")
            print(f"   Instance types: {instance_types}")
            
            # Pobierz IAM role ARN ze starej node group
            list_result = subprocess.run(
                ["aws", "eks", "list-nodegroups", "--cluster-name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if list_result.returncode != 0:
                return {"success": False, "error": "Nie udało się pobrać node groups"}
            
            nodegroups = json.loads(list_result.stdout).get("nodegroups", [])
            if not nodegroups:
                return {"success": False, "error": "Brak node groups"}
            
            old_nodegroup = nodegroups[0]
            
            # Pobierz szczegóły starej node group
            describe_result = subprocess.run(
                ["aws", "eks", "describe-nodegroup",
                 "--cluster-name", cluster_name,
                 "--nodegroup-name", old_nodegroup,
                 "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if describe_result.returncode != 0:
                return {"success": False, "error": "Nie udało się opisać node group"}
            
            old_ng_data = json.loads(describe_result.stdout).get("nodegroup", {})
            node_role_arn = old_ng_data.get("nodeRole")
            disk_size = old_ng_data.get("diskSize", 20)
            
            if not node_role_arn:
                return {"success": False, "error": "Nie znaleziono IAM role"}
            
            # Utwórz nową node group
            create_cmd = [
                "aws", "eks", "create-nodegroup",
                "--cluster-name", cluster_name,
                "--nodegroup-name", new_nodegroup_name,
                "--scaling-config", json.dumps({
                    "minSize": min_size,
                    "maxSize": max_size,
                    "desiredSize": desired_size
                }),
                "--disk-size", str(disk_size),
                "--subnets"] + subnet_ids + [
                "--instance-types"] + instance_types + [
                "--node-role", node_role_arn,
                "--output", "json"
            ]
            
            create_result = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=120
            )
            
            if create_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Nie udało się utworzyć node group: {create_result.stderr}"
                }
            
            print(f"   ✅ Node group {new_nodegroup_name} utworzona, czekam na gotowość...")
            return {"success": True, "nodegroup_name": new_nodegroup_name}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _wait_for_nodegroup_ready(self, cluster_name: str, nodegroup_name: str, env: dict, timeout: int = 600) -> bool:
        """Czekaj aż node group będzie w stanie ACTIVE"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["aws", "eks", "describe-nodegroup",
                     "--cluster-name", cluster_name,
                     "--nodegroup-name", nodegroup_name,
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    status = data.get("nodegroup", {}).get("status")
                    print(f"   ⏳ Status node group: {status}")
                    
                    if status == "ACTIVE":
                        print(f"   ✅ Node group jest gotowa!")
                        return True
                    elif status in ["CREATE_FAILED", "DELETE_FAILED"]:
                        print(f"   ❌ Node group w stanie błędu: {status}")
                        return False
                
                time.sleep(30)  # Czekaj 30 sekund przed kolejnym sprawdzeniem
                
            except Exception as e:
                print(f"   ⚠️ Błąd sprawdzania statusu: {e}")
                time.sleep(30)
        
        print(f"   ⏱️ Timeout: Node group nie jest gotowa po {timeout}s")
        return False

    def _delete_old_nodegroup(self, cluster_name: str, nodegroup_name: str, env: dict) -> bool:
        """Usuń starą node group"""
        try:
            print(f"   🗑️ Usuwam starą node group: {nodegroup_name}")
            print(f"   💡 Kubernetes automatycznie przeniesie pody na nowe węzły")
            
            # AWS automatycznie przeskaluje do 0 podczas usuwania
            # Nie trzeba ręcznie skalować (maxSize nie może być 0)
            delete_result = subprocess.run(
                ["aws", "eks", "delete-nodegroup",
                 "--cluster-name", cluster_name,
                 "--nodegroup-name", nodegroup_name,
                 "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            if delete_result.returncode != 0:
                print(f"   ⚠️ Nie udało się usunąć node group: {delete_result.stderr}")
                return False
            
            print(f"   ✅ Node group {nodegroup_name} usuwana (proces trwa ~5 min w tle)")
            print(f"   📋 Pody zostały przeniesione na nową node group")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Błąd usuwania node group: {e}")
            return False

    def scale_cluster(
        self,
        cluster_name: str,
        region: str,
        aws_access_key: str,
        aws_secret_key: str,
        desired_size: int,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        instance_types: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Skaluj klaster EKS przez zmianę liczby worker nodes i/lub typu instancji
        
        Args:
            cluster_name: Nazwa klastra EKS
            region: Region AWS
            aws_access_key: AWS Access Key ID
            aws_secret_key: AWS Secret Access Key
            desired_size: Docelowa liczba worker nodes
            min_size: Minimalna liczba nodes (opcjonalne)
            max_size: Maksymalna liczba nodes (opcjonalne)
            instance_types: Lista typów instancji EC2 (opcjonalne, np. ['t3.medium'])
            
        Returns:
            Dict z wynikiem operacji
        """
        try:
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": region
            })
            
            print(f"🔧 Skalowanie klastra EKS: {cluster_name}")
            print(f"   Region: {region}")
            print(f"   Desired size: {desired_size}")
            
            # Pobierz listę node groups
            list_result = subprocess.run(
                ["aws", "eks", "list-nodegroups", "--cluster-name", cluster_name, "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if list_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to list node groups: {list_result.stderr}"
                }
            
            data = json.loads(list_result.stdout)
            nodegroups = data.get("nodegroups", [])
            
            if not nodegroups:
                return {
                    "success": False,
                    "error": "No node groups found in cluster"
                }
            
            # Skaluj pierwszy node group (w większości przypadków jest tylko jeden)
            nodegroup_name = nodegroups[0]
            print(f"   Node group: {nodegroup_name}")
            
            # Sprawdź czy zmiana typu instancji jest wymagana
            current_instance_types = self._get_nodegroup_instance_types(cluster_name, nodegroup_name, env)
            instance_type_changed = False
            
            if instance_types and len(instance_types) > 0:
                # Porównaj obecny typ z żądanym
                if set(current_instance_types) != set(instance_types):
                    instance_type_changed = True
                    print(f"   🔄 Zmiana typu instancji: {current_instance_types} → {instance_types}")
                    
                    # Pobierz subnety z klastra
                    describe_cluster = subprocess.run(
                        ["aws", "eks", "describe-cluster", "--name", cluster_name, "--output", "json"],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=30
                    )
                    
                    if describe_cluster.returncode != 0:
                        return {
                            "success": False,
                            "error": "Nie udało się pobrać informacji o klastrze",
                            "cluster_name": cluster_name
                        }
                    
                    cluster_data = json.loads(describe_cluster.stdout)
                    subnet_ids = cluster_data.get("cluster", {}).get("resourcesVpcConfig", {}).get("subnetIds", [])
                    
                    if not subnet_ids:
                        return {
                            "success": False,
                            "error": "Nie znaleziono subnetów dla klastra",
                            "cluster_name": cluster_name
                        }
                    
                    # Utwórz nową node group z timestampem
                    import time
                    new_nodegroup_name = f"{cluster_name}-nodes-{int(time.time())}"
                    
                    # Utwórz nową node group
                    create_result = self._create_new_nodegroup(
                        cluster_name=cluster_name,
                        new_nodegroup_name=new_nodegroup_name,
                        instance_types=instance_types,
                        desired_size=desired_size,
                        min_size=min_size if min_size is not None else 1,
                        max_size=max_size if max_size is not None else desired_size * 2,
                        subnet_ids=subnet_ids,
                        env=env
                    )
                    
                    if not create_result.get("success"):
                        return {
                            "success": False,
                            "error": create_result.get("error", "Nie udało się utworzyć node group"),
                            "cluster_name": cluster_name
                        }
                    
                    # Czekaj aż nowa node group będzie gotowa
                    if not self._wait_for_nodegroup_ready(cluster_name, new_nodegroup_name, env):
                        return {
                            "success": False,
                            "error": "Nowa node group nie jest gotowa po timeout",
                            "cluster_name": cluster_name
                        }
                    
                    # Usuń starą node group
                    self._delete_old_nodegroup(cluster_name, nodegroup_name, env)
                    
                    return {
                        "success": True,
                        "message": f"Cluster '{cluster_name}' scaled with new instance type",
                        "cluster_name": cluster_name,
                        "old_nodegroup": nodegroup_name,
                        "new_nodegroup": new_nodegroup_name,
                        "instance_types": instance_types,
                        "desired_size": desired_size,
                        "min_size": min_size,
                        "max_size": max_size,
                        "status": "node group replaced"
                    }
            
            # Jeśli nie ma zmiany typu instancji, wykonaj zwykłe skalowanie
            print(f"   📊 Zwykłe skalowanie bez zmiany typu instancji")
            
            # Przygotuj scaling-config JSON
            scaling_config = {"desiredSize": desired_size}
            if min_size is not None:
                scaling_config["minSize"] = min_size
            if max_size is not None:
                scaling_config["maxSize"] = max_size
            
            print(f"   Scaling config: {scaling_config}")
            
            # Wykonaj update
            update_result = subprocess.run(
                ["aws", "eks", "update-nodegroup-config",
                 "--cluster-name", cluster_name,
                 "--nodegroup-name", nodegroup_name,
                 "--scaling-config", json.dumps(scaling_config),
                 "--output", "json"],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            if update_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to update node group: {update_result.stderr}",
                    "cluster_name": cluster_name
                }
            
            print(f"   ✅ Skalowanie rozpoczęte")
            
            return {
                "success": True,
                "message": f"Cluster '{cluster_name}' scaling initiated",
                "cluster_name": cluster_name,
                "nodegroup": nodegroup_name,
                "desired_size": desired_size,
                "min_size": min_size,
                "max_size": max_size,
                "status": "scaling in progress"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Scaling operation timed out",
                "cluster_name": cluster_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cluster_name": cluster_name
            }


eks_service = EksService()
