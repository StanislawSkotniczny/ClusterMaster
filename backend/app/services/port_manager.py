import json
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import socket

class PortManager:
    def __init__(self, port_file_path: str = "cluster_ports.json"):
        """
        Menedżer portów dla klastrów
        
        Args:
            port_file_path: Ścieżka do pliku z zapisanymi portami
        """
        self.port_file_path = Path(port_file_path)
        self.base_prometheus_port = 30090
        self.base_grafana_port = 30030
        self.port_increment = 10  # Różnica między portami dla różnych klastrów
        
    def _load_port_assignments(self) -> Dict[str, Dict[str, int]]:
        """Załaduj zapisane przypisania portów"""
        if not self.port_file_path.exists():
            return {}
        
        try:
            with open(self.port_file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_port_assignments(self, assignments: Dict[str, Dict[str, int]]) -> None:
        """Zapisz przypisania portów do pliku"""
        with open(self.port_file_path, 'w') as f:
            json.dump(assignments, f, indent=2)
    
    def _is_port_available(self, port: int) -> bool:
        """Sprawdź czy port jest dostępny"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0  # Port dostępny jeśli połączenie nie powiodło się
        except:
            return True
    
    def _find_next_available_port_pair(self, used_ports: List[int]) -> Tuple[int, int]:
        """
        Znajdź następną dostępną parę portów (prometheus, grafana)
        
        Returns:
            Tuple[prometheus_port, grafana_port]
        """
        prometheus_port = self.base_prometheus_port
        grafana_port = self.base_grafana_port
        
        while True:
            # Sprawdź czy oba porty są dostępne
            if (prometheus_port not in used_ports and 
                grafana_port not in used_ports and
                self._is_port_available(prometheus_port) and 
                self._is_port_available(grafana_port)):
                return prometheus_port, grafana_port
            
            # Przejdź do następnej pary portów
            prometheus_port += self.port_increment
            grafana_port += self.port_increment
            
            # Zabezpieczenie przed nieskończoną pętlą
            if prometheus_port > 32767:  # Maksymalny port NodePort w K8s
                raise Exception("Brak dostępnych portów w zakresie NodePort")
    
    def assign_ports_for_cluster(self, cluster_name: str) -> Dict[str, int]:
        """
        Przypisz porty dla nowego klastra
        
        Args:
            cluster_name: Nazwa klastra
            
        Returns:
            Dict z portami: {"prometheus": port, "grafana": port}
        """
        assignments = self._load_port_assignments()
        
        # Jeśli klaster już ma przypisane porty, zwróć je
        if cluster_name in assignments:
            return assignments[cluster_name]
        
        # Zbierz wszystkie używane porty
        used_ports = []
        for cluster_ports in assignments.values():
            used_ports.extend(cluster_ports.values())
        
        # Znajdź dostępne porty
        prometheus_port, grafana_port = self._find_next_available_port_pair(used_ports)
        
        # Zapisz nowe przypisanie
        assignments[cluster_name] = {
            "prometheus": prometheus_port,
            "grafana": grafana_port
        }
        
        self._save_port_assignments(assignments)
        
        return assignments[cluster_name]
    
    def get_cluster_ports(self, cluster_name: str) -> Optional[Dict[str, int]]:
        """
        Pobierz porty dla istniejącego klastra
        
        Args:
            cluster_name: Nazwa klastra
            
        Returns:
            Dict z portami lub None jeśli klaster nie istnieje
        """
        assignments = self._load_port_assignments()
        return assignments.get(cluster_name)
    
    def release_cluster_ports(self, cluster_name: str) -> bool:
        """
        Zwolnij porty dla usuwanego klastra
        
        Args:
            cluster_name: Nazwa klastra
            
        Returns:
            True jeśli porty zostały zwolnione, False jeśli klaster nie istniał
        """
        assignments = self._load_port_assignments()
        
        if cluster_name in assignments:
            del assignments[cluster_name]
            self._save_port_assignments(assignments)
            return True
        
        return False
    
    def list_all_assignments(self) -> Dict[str, Dict[str, int]]:
        """Zwróć wszystkie przypisania portów"""
        return self._load_port_assignments()
    
    def get_cluster_urls(self, cluster_name: str) -> Optional[Dict[str, str]]:
        """
        Pobierz URL-e dla serwisów monitoringu klastra
        
        Args:
            cluster_name: Nazwa klastra
            
        Returns:
            Dict z URL-ami lub None jeśli klaster nie istnieje
        """
        ports = self.get_cluster_ports(cluster_name)
        if not ports:
            return None
        
        return {
            "prometheus_url": f"http://localhost:{ports['prometheus']}",
            "grafana_url": f"http://localhost:{ports['grafana']}",
            "grafana_credentials": "admin / admin123"
        }
    
    def get_all_ports(self) -> Dict[str, Dict[str, int]]:
        """
        Pobierz wszystkie przypisane porty dla wszystkich klastrów
        
        Returns:
            Dict z przypisaniami portów dla wszystkich klastrów
        """
        return self._load_port_assignments()

# Singleton instance
port_manager = PortManager()
