import json
from pathlib import Path
import getpass
from rich.prompt import Prompt
from rich.console import Console

# Le chemin du fichier de configuration sera ~/.config/glpi_explorer/config.json
# C'est un emplacement standard et propre pour les fichiers de config utilisateur.
CONFIG_DIR = Path.home() / ".config" / "glpi_explorer"
CONFIG_FILE = CONFIG_DIR / "config.json"

console = Console()

def load_config() -> dict | None:
    """Charge la configuration depuis le fichier JSON.
    
    Retourne:
        Un dictionnaire avec la configuration si le fichier existe, sinon None.
    """
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config_data: dict) -> None:
    """Sauvegarde le dictionnaire de configuration dans le fichier JSON.
    
    Crée le dossier parent si nécessaire.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        console.print(f"[green]Configuration sauvegardée dans {CONFIG_FILE}[/green]")
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la sauvegarde de la configuration: {e}[/bold red]")


def prompt_for_config() -> dict:
    """Demande interactivement les informations de connexion à l'utilisateur."""
    console.print("[bold cyan]Configuration de la connexion à l'API GLPI[/bold cyan]")
    
    glpi_url = Prompt.ask("Entrez l'URL de votre API GLPI (ex: http://glpi.example.com/apirest.php)")
    user_login = Prompt.ask("Entrez votre login GLPI")
    
    # getpass est utilisé pour que le mot de passe ne s'affiche pas dans le terminal
    user_password = getpass.getpass("Entrez votre mot de passe GLPI: ")
    
    app_token = Prompt.ask("Entrez votre App-Token GLPI")

    config_data = {
        "glpi_url": glpi_url,
        "user_login": user_login,
        "user_password": user_password,
        "app_token": app_token,
        "session_token": None # Le session_token sera stocké ici plus tard
    }
    
    save_config(config_data)
    return config_data


def get_or_create_config() -> dict:
    """
    Tente de charger la configuration. Si elle n'existe pas,
    la demande à l'utilisateur et la crée.
    """
    config = load_config()
    if config is None:
        console.print("[yellow]Fichier de configuration introuvable. Lancement de l'assistant...[/yellow]")
        config = prompt_for_config()
    return config