import requests
from rich.console import Console

# On importe les fonctions de notre module de configuration
from . import config

console = Console()

class GLPIClient:
    """
    Un client pour interagir avec l'API REST de GLPI.
    Gère l'authentification et les requêtes.
    """
    def __init__(self, conf: dict):
        # On s'assure que l'URL se termine bien par un slash
        self.api_url = conf['glpi_url'].rstrip('/') + '/'
        self.app_token = conf['app_token']
        self.session_token = conf.get('session_token') # Peut être None au début

        # On garde une copie de la config pour la mettre à jour
        self._config_data = conf

    def _get_headers(self) -> dict:
        """Construit les headers HTTP nécessaires pour les requêtes."""
        if not self.session_token:
            # Pour l'initSession, on n'a besoin que de l'App-Token
            return {
                'Content-Type': 'application/json',
                'App-Token': self.app_token
            }
        
        # Pour toutes les autres requêtes, on inclut le Session-Token
        return {
            'Content-Type': 'application/json',
            'App-Token': self.app_token,
            'Session-Token': self.session_token
        }

    def init_session(self) -> bool:
        """
        Initialise une nouvelle session avec l'API GLPI et récupère un session_token.
        Met à jour la configuration locale avec le nouveau token.
        """
        console.print(f"Tentative d'ouverture de session sur {self.api_url}...")
        
        # Le endpoint pour l'authentification
        endpoint = "initSession"
        url = self.api_url + endpoint

        # --- DÉBUT DE LA CORRECTION ---
        # L'API GLPI attend les clés "login" et "password", et non "user_login"
        auth_payload = {
            "login": self._config_data['user_login'],
            "password": self._config_data['user_password']
        }
        # --- FIN DE LA CORRECTION ---
        
        try:
            # On utilise les headers sans session_token pour cette requête spécifique
            headers_for_auth = {
                'Content-Type': 'application/json',
                'App-Token': self.app_token
            }
            # L'API GLPI v10+ a changé la méthode pour GET. On essaie POST puis GET.
            # On va d'abord tenter avec POST, qui est plus commun pour le login.
            response = requests.post(url, headers=headers_for_auth, json=auth_payload, timeout=10)
            
            # Si POST échoue avec une erreur de méthode non autorisée (405), on tente GET
            # C'est une des subtilités de GLPI v10.
            if response.status_code == 405:
                console.print("[yellow]POST non autorisé, tentative avec GET...[/yellow]")
                headers_for_auth_get = headers_for_auth.copy()
                headers_for_auth_get.update({
                    "login": self._config_data['user_login'],
                    "password": self._config_data['user_password']
                })
                response = requests.get(url, headers=headers_for_auth_get, timeout=10)


            # Lève une exception si le statut est une erreur (4xx ou 5xx)
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data.get('session_token')
            
            if not self.session_token:
                console.print("[bold red]Erreur: session_token non reçu de GLPI.[/bold red]")
                return False
            
            # On met à jour le token dans notre config et on la sauvegarde
            self._config_data['session_token'] = self.session_token
            config.save_config(self._config_data)

            console.print("[bold green]Session ouverte avec succès ![/bold green]")
            return True

        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Erreur de connexion à l'API GLPI: {e}[/bold red]")
            if e.response is not None:
                console.print(f"[red]Détail de l'erreur GLPI: {e.response.text}[/red]")
            return False

    def kill_session(self) -> bool:
        """Ferme la session active sur GLPI."""
        if not self.session_token:
            console.print("[yellow]Aucune session active à fermer.[/yellow]")
            return True
            
        console.print("Fermeture de la session GLPI...")
        endpoint = "killSession"
        url = self.api_url + endpoint

        try:
            response = requests.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()

            # On nettoie le token dans notre config
            self._config_data['session_token'] = None
            self.session_token = None
            config.save_config(self._config_data)

            console.print("[bold green]Session fermée avec succès.[/bold green]")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Erreur lors de la fermeture de la session: {e}[/bold red]")
            return False