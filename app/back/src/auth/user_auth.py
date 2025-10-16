import os
import base64
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()


CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
REDIRECT_URI = os.getenv('REDIRECT_URI')



def get_spotify_auth_url():
    """
    Gera a URL para o usuário autorizar o app via OAuth.
    """
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={urllib.parse.quote(SPOTIFY_SCOPES)}"
    )
    return auth_url



def exchange_code_for_token(code):
    """
    Recebe o 'code' retornado pelo Spotify e troca por tokens de acesso e refresh.
    """
    token_url = "https://accounts.spotify.com/api/token"
    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_creds}"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erro ao obter token: {response.text}")

    return response.json()



def refresh_access_token(refresh_token: str) -> dict:
    """
    Usa o refresh_token do usuário para solicitar um novo access_token.
    Retorna um dicionário com os novos tokens e tempo de expiração.
    """
    token_url = "https://accounts.spotify.com/api/token"
    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode()).decode()

    headers = {"Authorization": f"Basic {encoded_creds}"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Erro ao renovar token: {response.text}")

    tokens = response.json()
    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token", refresh_token),
        "expires_in": tokens.get("expires_in")
    }
