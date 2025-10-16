from app import app
import requests

def get_recent_tracks(access_token: str):

    headers = {"Authorization": f"Bearer {access_token}"}

    # músicas recentes
    recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=50", headers=headers)
    recent_data = recent_res.json()['items']

    return recent_data



def get_user_data(access_token: str) -> dict:
    """
    Retorna informações básicas do perfil do usuário Spotify.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if profile_res.status_code != 200:
        raise Exception(f"Erro ao obter perfil Spotify: {profile_res.status_code} - {profile_res.text}")

    profile = profile_res.json()
    return {
        "spotify_user_id": profile.get("id"),
        "display_name": profile.get("display_name", "Usuário"),
        "profile_image_url": profile["images"][0]["url"] if profile.get("images") else None,
    }
