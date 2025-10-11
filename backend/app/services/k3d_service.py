import subprocess
import json
from typing import Dict, List, Optional


class K3dService:
    
    def is_installed(self) -> bool:
        try:
            result = subprocess.run(
                ['k3d', 'version'],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def create_cluster(
        self,
        cluster_name: str,
        agents: int = 2,
        servers: int = 1,
        ports: Dict = None
    ) -> Dict:

        try:
            cmd = [
                'k3d', 'cluster', 'create', cluster_name,
                '--agents', str(agents),
                '--servers', str(servers),
                '--api-port', '127.0.0.1:6550',  # WAŻNE: 127.0.0.1 zamiast 0.0.0.0 dla Windows
                '--wait'
            ]
            
            # Add port mappings if provided
            if ports:
                if 'prometheus' in ports:
                    cmd.extend(['--port', f'{ports["prometheus"]}:{ports["prometheus"]}@loadbalancer'])
                if 'grafana' in ports:
                    cmd.extend(['--port', f'{ports["grafana"]}:{ports["grafana"]}@loadbalancer'])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'cluster_name': cluster_name,
                'provider': 'k3d',
                'message': f'Cluster {cluster_name} created successfully',
                'agents': agents,
                'servers': servers
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to create k3d cluster: {e.stderr}'
            }
    
    def delete_cluster(self, cluster_name: str) -> Dict:

        try:
            subprocess.run(
                ['k3d', 'cluster', 'delete', cluster_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f'Cluster {cluster_name} deleted successfully'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to delete cluster: {e.stderr}'
            }
    
    def list_clusters(self) -> List[str]:

        try:
            result = subprocess.run(
                ['k3d', 'cluster', 'list', '-o', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            clusters = json.loads(result.stdout)
            return [c['name'] for c in clusters]
            
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def get_cluster_info(self, cluster_name: str) -> Dict:
 
        try:
            # Get cluster basic info
            cluster_result = subprocess.run(
                ['k3d', 'cluster', 'list', cluster_name, '-o', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            clusters = json.loads(cluster_result.stdout)
            if not clusters:
                return {'success': False, 'error': 'Cluster not found'}
            
            cluster_info = clusters[0]
            
            # Get nodes info
            nodes_result = subprocess.run(
                ['k3d', 'node', 'list', '-o', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            all_nodes = json.loads(nodes_result.stdout)
            
            # Filter nodes for this cluster and extract role info
            cluster_nodes = []
            for node in all_nodes:
                if node.get('cluster') == cluster_name:
                    # Determine role from node name
                    node_name = node.get('name', '')
                    if 'server' in node_name:
                        role = 'server'
                    elif 'agent' in node_name:
                        role = 'agent'
                    else:
                        role = 'unknown'
                    
                    cluster_nodes.append({
                        'name': node_name,
                        'role': role,
                        'state': node.get('state', 'unknown')
                    })
            
            return {
                'success': True,
                'cluster': cluster_info,
                'nodes': cluster_nodes
            }
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_agent(self, cluster_name: str, agent_name: Optional[str] = None) -> Dict:

        try:
            if not agent_name:
                # Auto-generate name
                nodes = self.list_nodes(cluster_name)
                agent_count = sum(1 for n in nodes if 'agent' in n)
                agent_name = f"agent-{agent_count}"
            
            cmd = [
                'k3d', 'node', 'create', agent_name,
                '--cluster', cluster_name,
                '--role', 'agent',
                '--wait'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f'Agent {agent_name} added to cluster {cluster_name}',
                'node_name': agent_name
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to add agent: {e.stderr}'
            }
    
    def delete_node(self, cluster_name: str, node_name: str) -> Dict:
        """Usuń node z klastra"""
        try:
            full_node_name = f'k3d-{cluster_name}-{node_name}'
            
            subprocess.run(
                ['k3d', 'node', 'delete', full_node_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f'Node {node_name} deleted from cluster {cluster_name}'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to delete node: {e.stderr}'
            }
    
    def list_nodes(self, cluster_name: str) -> List[str]:
        """Lista nodów w klastrze"""
        try:
            result = subprocess.run(
                ['k3d', 'node', 'list', '-o', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            nodes = json.loads(result.stdout)
            cluster_nodes = [
                n['name'] for n in nodes 
                if n.get('cluster') == cluster_name
            ]
            
            return cluster_nodes
            
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def scale_cluster(self, cluster_name: str, target_agents: int) -> Dict:

        try:
            # Pobierz obecną liczbę agentów
            nodes = self.list_nodes(cluster_name)
            current_agents = sum(1 for n in nodes if 'agent' in n)
            
            operations = []
            
            if target_agents > current_agents:
                # Dodaj agentów
                agents_to_add = target_agents - current_agents
                operations.append(f'Adding {agents_to_add} agent(s)...')
                
                for i in range(agents_to_add):
                    result = self.add_agent(cluster_name)
                    if result['success']:
                        operations.append(f"✅ Added {result['node_name']}")
                    else:
                        operations.append(f"❌ Failed to add agent: {result.get('error')}")
                        
            elif target_agents < current_agents:
                # Usuń agentów
                agents_to_remove = current_agents - target_agents
                operations.append(f'Removing {agents_to_remove} agent(s)...')
                
                # Usuń ostatnich N agentów
                agent_nodes = [n for n in nodes if 'agent' in n]
                for i in range(agents_to_remove):
                    node_to_remove = agent_nodes[-(i+1)]
                    # Extract simple name from full k3d name
                    simple_name = node_to_remove.replace(f'k3d-{cluster_name}-', '')
                    result = self.delete_node(cluster_name, simple_name)
                    if result['success']:
                        operations.append(f"✅ Removed {simple_name}")
                    else:
                        operations.append(f"❌ Failed to remove {simple_name}")
            else:
                operations.append('No changes needed - cluster already at target size')
            
            return {
                'success': True,
                'message': f'Cluster scaled to {target_agents} agents',
                'operations': operations,
                'previous_agents': current_agents,
                'current_agents': target_agents
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_cluster(self, cluster_name: str) -> Dict:

        try:
            subprocess.run(
                ['k3d', 'cluster', 'start', cluster_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f'Cluster {cluster_name} started'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to start cluster: {e.stderr}'
            }
    
    def stop_cluster(self, cluster_name: str) -> Dict:

        try:
            subprocess.run(
                ['k3d', 'cluster', 'stop', cluster_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'message': f'Cluster {cluster_name} stopped'
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Failed to stop cluster: {e.stderr}'
            }


# Singleton instance
k3d_service = K3dService()
