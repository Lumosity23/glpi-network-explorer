import click
from rich.console import Console

# On importe maintenant nos deux modules
from . import config
from . import glpi_client

console = Console()

# Le décorateur @click.pass_context permet de passer un objet partagé
# entre les commandes. Nous l'utiliserons pour partager notre client GLPI
# initialisé, afin de ne pas avoir à le recréer pour chaque commande.
@click.group()
@click.pass_context
def main_cli(ctx):
    """
    GLPI Network Explorer
    
    Un outil en ligne de commande pour explorer et tracer votre réseau via l'API GLPI.
    """
    # ctx.obj est un dictionnaire que l'on peut utiliser pour stocker
    # des objets partagés.
    ctx.obj = {}
    
    # On charge la config au démarrage.
    # Si elle n'existe pas, elle sera demandée à l'utilisateur.
    conf = config.get_or_create_config()
    
    # On stocke le client GLPI dans le contexte pour le réutiliser
    ctx.obj['glpi_client'] = glpi_client.GLPIClient(conf)
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
    # On ne veut jamais afficher le mot de passe !
    display_conf = {k: v for k, v in conf.items() if k != 'user_password'}
    
    console.print("[bold green]Configuration chargée avec succès :[/bold green]")
    console.print(display_conf)


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