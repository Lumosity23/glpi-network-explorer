import click
from rich.console import Console
from rich import print as rprint # Utiliser la fonction print de rich

# On importe maintenant nos modules
from . import config
from . import glpi_client
from . import engine # Le nouveau moteur

console = Console()

@click.group()
@click.pass_context
def main_cli(ctx):
    """
    GLPI Network Explorer
    
    Un outil en ligne de commande pour explorer et tracer votre réseau via l'API GLPI.
    """
    ctx.obj = {}
    
    conf = config.get_or_create_config()
    
    # On vérifie si on a déjà un session_token valide. Sinon, on demande de se connecter.
    if not conf.get('session_token'):
        console.print("[bold yellow]Attention: Vous n'êtes pas connecté.[/bold yellow]")
        console.print("Utilisez la commande 'login' pour ouvrir une session.")
        # On continue quand même pour permettre les commandes comme 'login' et 'reconfigure'.

    client = glpi_client.GLPIClient(conf)
    
    # On stocke le client et le moteur dans le contexte pour les réutiliser
    ctx.obj['glpi_client'] = client
    ctx.obj['engine'] = engine.Engine(client)
    ctx.obj['config'] = conf


@main_cli.command()
def reconfigure():
    """Force la re-saisie des informations de connexion à GLPI."""
    console.print("[bold yellow]Lancement de la reconfiguration...[/bold yellow]")
    config.prompt_for_config()


@main_cli.command(name="check-config")
@click.pass_context
def check_config_command(ctx):
    """Charge et affiche la configuration actuelle (sans le mot de passe)."""
    conf = ctx.obj['config']
    display_conf = {k: v for k, v in conf.items() if k != 'user_password'}
    console.print("[bold green]Configuration chargée avec succès :[/bold green]")
    rprint(display_conf) # rprint gère bien l'affichage des dictionnaires


@main_cli.command()
@click.pass_context
def login(ctx):
    """Initialise une session avec l'API GLPI."""
    client = ctx.obj['glpi_client']
    client.init_session()


@main_cli.command()
@click.pass_context
def logout(ctx):
    """Ferme la session GLPI active."""
    client = ctx.obj['glpi_client']
    client.kill_session()


# --- NOUVELLE COMMANDE ---
@main_cli.command()
@click.argument('device_name')
@click.pass_context
def find(ctx, device_name):
    """
    Recherche un équipement par son nom et affiche ses informations de base.
    
    Exemple: glpi-explorer find PC-1234
    """
    console.print(f"--- Lancement de la recherche pour [bold]'{device_name}'[/bold] ---")
    
    # On récupère le moteur depuis le contexte
    eng = ctx.obj['engine']
    
    # On appelle la méthode de notre moteur
    device = eng.find_device(device_name)
    
    if device:
        console.print("\n[bold green]Détails de l'équipement trouvé :[/bold green]")
        # rprint affiche joliment les dataclasses
        rprint(device)
    else:
        console.print(f"\n[bold red]Aucun résultat pour '{device_name}'.[/bold red]")