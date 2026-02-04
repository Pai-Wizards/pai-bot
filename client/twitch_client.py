import time
import requests
from typing import Optional, Dict

class TwitchClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def get_app_access_token(self) -> str:
        """
        Gera (ou retorna cache) do token de acesso de app (client credentials).
        Exige que client_id e client_secret estejam definidos na instância.
        Retorna o access_token em caso de sucesso; lança RuntimeError em erro.
        """
        if not self.client_id or not self.client_secret:
            raise RuntimeError("client_id e client_secret precisam ser configurados")

        if self._token and time.time() < self._token_expires_at:
            return self._token

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        resp = requests.post(url, params=params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Falha ao obter token Twitch: {resp.status_code} {resp.text}")

        data = resp.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)

        if not access_token:
            raise RuntimeError(f"Resposta inesperada ao obter token: {data}")

        self._token = access_token
        self._token_expires_at = time.time() + int(expires_in) - 30
        return self._token

    def get_user_images(self, login: str) -> Optional[Dict[str, Optional[str]]]:
        """
        Busca profile_image_url e offline_image_url para o login informado.
        Retorna dict { 'profile_image_url': str|None, 'offline_image_url': str|None } ou None se usuário não encontrado.
        Pode lançar RuntimeError em caso de falha na requisição.
        """
        token = self.get_app_access_token()
        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id or "",
        }
        params = {"login": login}

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Falha ao buscar usuário Twitch: {resp.status_code} {resp.text}")

        data = resp.json()
        items = data.get("data", [])
        if not items:
            return None

        user = items[0]
        return {
            "profile_image_url": user.get("profile_image_url"),
            "offline_image_url": user.get("offline_image_url"),
        }
