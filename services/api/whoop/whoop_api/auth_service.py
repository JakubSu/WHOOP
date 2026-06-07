from __future__ import annotations

from urllib.parse import urlencode

from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import WhoopToken
from whoop.whoop_api.parsers import parse_token_response


WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class AuthService:
    def __init__(
        self,
        *,
        client: BaseWhoopClient,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: str,
    ) -> None:
        self.client = client
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes

    def build_authorization_url(self, *, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": self.scopes,
                "state": state,
            }
        )
        return f"{WHOOP_AUTH_URL}?{query}"

    def exchange_code(self, code: str) -> WhoopToken:
        payload = self.client.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        return parse_token_response(payload)

    def refresh_token(self, refresh_token: str) -> WhoopToken:
        payload = self.client.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        return parse_token_response(payload, refresh_token=refresh_token)

    def revoke_user_access(self, access_token: str) -> None:
        BaseWhoopClient(access_token=access_token, session=self.client.session, timeout=self.client.timeout).delete(
            "/v2/user/access"
        )
