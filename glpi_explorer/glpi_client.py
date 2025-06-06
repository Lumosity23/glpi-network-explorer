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
        
        endpoint = "initSession"
        url = self.api_url + endpoint

        auth_payload = {
            "login": self._config_data['user_login'],
            "password": self._config_data['user_password']
        }
        
        try:
            headers_for_auth = {
                'Content-Type': 'application/json',
                'App-Token': self.app_token
            }
            response = requests.post(url, headers=headers_for_auth, json=auth_payload, timeout=10)
            
            if response.status_code == 405:
                console.print("[yellow]POST non autorisé, tentative avec GET...[/yellow]")
                headers_for_auth_get = headers_for_auth.copy()
                headers_for_auth_get.update({
                    "login": self._config_data['user_login'],
                    "password": self._config_data['user_password']
                })
                response = requests.get(url, headers=headers_for_auth_get, timeout=10)

            response.raise_for_status()
            
            data = response.json()
            self.session_token = data.get('session_token')
            
            if not self.session_token:
                console.print("[bold red]Erreur: session_token non reçu de GLPI.[/bold red]")
                return False
            
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

            self._config_data['session_token'] = None
            self.session_token = None
            config.save_config(self._config_data)

            console.print("[bold green]Session fermée avec succès.[/bold green]")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Erreur lors de la fermeture de la session: {e}[/bold red]")
            return False

    # --- NOUVELLE MÉTHODE --- (EN FAIT, C'EST LA VERSION CORRIGÉE)
    def search_by_name(self, item_name: str) -> dict | None:
        """
        Recherche un équipement par son nom exact dans plusieurs types d'items GLPI.
        
        Args:
            item_name: Le nom exact de l'équipement à rechercher.

        Returns:
            Le premier item trouvé sous forme de dictionnaire, ou None si non trouvé.
        """
        if not self.session_token:
            console.print("[bold red]Erreur: Aucune session active. Veuillez vous connecter d'abord.[/bold red]")
            return None

        item_types_to_search = ['Computer', 'NetworkEquipment', 'PassiveDevice', 'Cable']
        
        console.print(f"Recherche de '{item_name}' dans GLPI...")
        
        for item_type in item_types_to_search:
            url = self.api_url + item_type
            
            # --- DÉBUT DE LA CORRECTION ---
            # Utilisation de la syntaxe de recherche simplifiée, plus fiable.
            # search[<champ>] est souvent mieux interprété par GLPI.
            params = {
                f'search[name]': item_name,
                'forcedisplay[0]': 'itemtype'
            }
            # --- FIN DE LA CORRECTION ---
            
            try:
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data:
                    # --- DÉBUT DE LA VÉRIFICATION SUPPLÉMENTAIRE ---
                    # L'API peut retourner tous les items si le filtre échoue.
                    # On doit donc vérifier manuellement que le résultat est correct.
                    for item in data:
                        if item.get('name') == item_name:
                            # On a trouvé la correspondance exacte !
                            console.print(f"[green]'{item_name}' trouvé (type: {item_type}).[/green]")
                            if 'itemtype' not in item:
                                item['itemtype'] = item_type
                            return item
                    # Si on sort de la boucle, c'est que l'API a retourné des résultats
                    # mais aucun ne correspond exactement. On continue la recherche.
                    
                # Si data est vide ou si aucun item ne correspondait, la recherche dans ce type d'objet a échoué.

            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Erreur lors de la recherche dans {item_type}: {e}[/bold red]")
                return None
        
        console.print(f"[yellow]Aucun équipement nommé '{item_name}' n'a été trouvé.[/yellow]")
        return None