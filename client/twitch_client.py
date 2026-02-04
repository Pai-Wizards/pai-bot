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

    def get_user(self, login_or_id: str) -> Optional[Dict[str, Optional[str]]]:
        token = self.get_app_access_token()
        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id or "",
        }

        login_or_id = str(login_or_id).strip()
        # extrai username se for uma URL do twitch
        if "twitch.tv" in login_or_id:
            try:
                login_or_id = login_or_id.rstrip("/").split("/")[-1]
            except Exception:
                pass

        params = {}
        if login_or_id.isdigit():
            params["id"] = login_or_id
        else:
            params["login"] = login_or_id.lower()

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
            "id": user.get("id"),
            "login": user.get("login"),
            "display_name": user.get("display_name"),
            "description": user.get("description"),  # ADICIONADO
        }

    def subscribe_eventsub(self, broadcaster_user_id: str, callback_url: str, secret: Optional[str] = None) -> Dict:
        """
        Cria uma subscription EventSub (stream.online) para o broadcaster_user_id.
        Em caso de subscription já existente (409) retorna um objeto indicando isso ao invés de lançar.
        """
        token = self.get_app_access_token()
        url = "https://api.twitch.tv/helix/eventsub/subscriptions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id or "",
            "Content-Type": "application/json",
        }
        body = {
            "type": "stream.online",
            "version": "1",
            "condition": {"broadcaster_user_id": str(broadcaster_user_id)},
            "transport": {
                "method": "webhook",
                "callback": callback_url,
                "secret": secret or ""
            }
        }

        resp = requests.post(url, headers=headers, json=body, timeout=10)

        # Trata caso onde já existe subscription (409) sem lançar
        if resp.status_code == 409:
            try:
                detail = resp.json()
            except Exception:
                detail = {"message": resp.text}
            return {"status": "exists", "detail": detail}

        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Falha ao criar EventSub: {resp.status_code} {resp.text}")
        try:
            return {"status": "created", "detail": resp.json()}
        except Exception:
            return {"status": "created", "detail": {}}

    def list_eventsub_subscriptions(self) -> Dict[str, list]:
        """
        Retorna dict com keys: 'total' e 'data' (lista de subscriptions).
        Itera paginação (cursor 'after') para retornar todas as subscriptions.
        Lança RuntimeError em caso de erro HTTP.
        """
        token = self.get_app_access_token()
        url = "https://api.twitch.tv/helix/eventsub/subscriptions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id or "",
        }

        all_items = []
        params = {}
        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                raise RuntimeError(f"Falha ao listar EventSub: {resp.status_code} {resp.text}")
            data = resp.json()
            items = data.get("data", [])
            all_items.extend(items)

            pagination = data.get("pagination", {}) or {}
            cursor = pagination.get("cursor")
            if cursor:
                params["after"] = cursor
                continue
            break

        return {"total": len(all_items), "data": all_items}
