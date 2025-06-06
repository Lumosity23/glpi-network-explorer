import click
from rich.console import Console
from . import config  # Importe notre module config.py

console = Console()

@click.group()
def main_cli():
    """
    GLPI Network Explorer
    
    Un outil en ligne de commande pour explorer et tracer votre réseau via l'API GLPI.
    """
    pass

@main_cli.command()
def reconfigure():
    """Force la re-saisie des informations de connexion à GLPI."""
    console.print("[bold yellow]Lancement de la reconfiguration...[/bold yellow]")
    config.prompt_for_config()

@main_cli.command(name="check-config")
def check_config_command():
    """Charge et affiche la configuration actuelle (sans le mot de passe)."""
    try:
        conf = config.get_or_create_config()
        # On ne veut jamais afficher le mot de passe !
        display_conf = {k: v for k, v in conf.items() if k != 'user_password'}
        
        console.print("[bold green]Configuration chargée avec succès :[/bold green]")
        console.print(display_conf)
    except Exception as e:
        console.print(f"[bold red]Impossible de charger la configuration: {e}[/bold red]")