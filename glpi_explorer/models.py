import re
from dataclasses import dataclass, field
from typing import Optional

# Les dataclasses sont parfaites pour ce genre de structure.
# Elles créent automatiquement le constructeur (__init__), la représentation (__repr__), etc.

@dataclass
class DevicePort:
    """Représente un port sur un équipement."""
    raw_name: str
    number: Optional[int] = None
    direction: Optional[str] = None # 'IN' ou 'OUT'

@dataclass
class BaseDevice:
    """Classe de base pour tous les équipements."""
    glpi_id: int
    name: str
    item_type: str # Le type GLPI (Computer, NetworkEquipment, etc.)
    ports: list[DevicePort] = field(default_factory=list)

    @classmethod
    def from_glpi_item(cls, item: dict):
        """Méthode de fabrique pour créer un objet depuis un JSON GLPI."""
        # Cette méthode sera surchargée par les classes filles
        return cls(glpi_id=item['id'], name=item['name'], item_type=item['itemtype'])

@dataclass
class Computer(BaseDevice):
    """Représente un ordinateur."""
    pass # Pour l'instant, pas de logique spécifique

@dataclass
class Cable(BaseDevice):
    """Représente un câble."""
    pass # Pas de parsing de nom complexe pour le câble lui-même

@dataclass
class NetworkDevice(BaseDevice):
    """Classe de base pour les équipements réseau actifs ou passifs."""
    device_type: Optional[str] = None # SW, PP, WO, HB
    short_name: Optional[str] = None

    @classmethod
    def from_glpi_item(cls, item: dict):
        """Parse le nom pour extraire le type et le nom court."""
        instance = super().from_glpi_item(item)
        
        # Exemple de parsing: "SW-CORE-01" -> type="SW", short_name="CORE-01"
        # Exemple: "WO Bureau 204" -> type="WO", short_name="Bureau 204"
        # On utilise une expression régulière pour plus de flexibilité
        
        # Regex qui capture le préfixe (PP, SW, HB, WO) et le reste du nom
        match = re.match(r'^(PP|SW|HB|WO)\s*(.*)', item['name'], re.IGNORECASE)
        if match:
            instance.device_type = match.group(1).upper()
            instance.short_name = match.group(2).strip()
        else:
            # Cas où le nom ne suit pas la nomenclature attendue
            instance.device_type = "UNKNOWN"
            instance.short_name = item['name']
            
        # Ici, on pourrait aussi récupérer les ports associés via un autre appel API
        # mais on le fera dans le 'engine.py' pour séparer les responsabilités.

        return instance

@dataclass
class Switch(NetworkDevice):
    """Représente un Switch."""
    device_type: str = "SW"

@dataclass
class Hub(NetworkDevice):
    """Représente un Hub Ethernet."""
    device_type: str = "HB"

    def get_out_port(self) -> Optional[DevicePort]:
        """Retourne le port de sortie (celui avec le numéro le plus élevé)."""
        if not self.ports:
            return None
        
        numbered_ports = [p for p in self.ports if p.number is not None]
        if not numbered_ports:
            return None
            
        return max(numbered_ports, key=lambda p: p.number)

@dataclass
class PassiveDevice(NetworkDevice):
    """Classe de base pour les équipements passifs (Patch Panel, WallOutlet)."""
    
    def get_internal_link(self, in_port: DevicePort) -> Optional[DevicePort]:
        """
        Pour un port d'entrée donné, trouve le port de sortie correspondant
        (même numéro, direction opposée).
        """
        if in_port.direction != 'IN' or in_port.number is None:
            return None

        for out_port in self.ports:
            if out_port.number == in_port.number and out_port.direction == 'OUT':
                return out_port
        return None

@dataclass
class PatchPanel(PassiveDevice):
    """Représente un Panneau de Brassage."""
    device_type: str = "PP"

@dataclass
class WallOutlet(PassiveDevice):
    """Représente une Prise Murale."""
    device_type: str = "WO"

# Une fonction 'usine' pour créer le bon type d'objet à partir d'un item GLPI
def create_device_from_glpi(item: dict) -> BaseDevice:
    """Analyse un item GLPI et retourne l'objet modèle correspondant."""
    item_type = item.get('itemtype')
    name = item.get('name', '').upper()

    if item_type == 'Computer':
        return Computer.from_glpi_item(item)
    elif item_type == 'Cable':
        return Cable.from_glpi_item(item)
    elif item_type == 'NetworkEquipment':
        if name.startswith('SW'):
            return Switch.from_glpi_item(item)
        elif name.startswith('HB'):
            return Hub.from_glpi_item(item)
    elif item_type == 'PassiveDevice':
        if name.startswith('PP'):
            return PatchPanel.from_glpi_item(item)
        elif name.startswith('WO'):
            return WallOutlet.from_glpi_item(item)
    
    # Si aucun type spécifique ne correspond, on retourne un objet de base
    # ou un NetworkDevice générique si le nom correspond.
    if name.startswith(('PP', 'SW', 'HB', 'WO')):
        return NetworkDevice.from_glpi_item(item)
    else:
        return BaseDevice.from_glpi_item(item)