from rich.console import Console

from .glpi_client import GLPIClient
from .models import create_device_from_glpi, BaseDevice

console = Console()

class Engine:
    """
    Le moteur logique de l'application.
    Orchestre les appels à l'API et la manipulation des modèles.
    """
    def __init__(self, client: GLPIClient):
        self.client = client

    def find_device(self, device_name: str) -> BaseDevice | None:
        """
        Trouve un équipement par son nom, et le retourne sous forme d'objet modèle.
        
        Args:
            device_name: Le nom de l'équipement à trouver.

        Returns:
            Un objet (Computer, Switch, etc.) ou None si non trouvé.
        """
        # On utilise la nouvelle méthode de notre client API
        glpi_item = self.client.search_by_name(device_name)
        
        if not glpi_item:
            return None
        
        # On utilise notre "usine" de modèles pour créer le bon objet Python
        device_model = create_device_from_glpi(glpi_item)
        
        console.print(f"Modèle de données créé: [bold cyan]{type(device_model).__name__}[/bold cyan]")
        
        return device_model