from app import app
from flask import render_template, redirect, url_for, request, session
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from app.etl import process_recent_tracks, generate_top_artists

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
REDIRECT_URI = os.getenv('REDIRECT_URI')
ENCODED_CLIENT = os.getenv('ENCODED_CLIENT')

@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')


@app.route('/login-spotify') # Esta será a rota que seu botão HTML vai chamar
def login_spotify():

    auth_url = (
        f"http://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={urllib.parse.quote(SPOTIFY_SCOPES)}" # Codifique os escopos também
    )
    # Redireciona o navegador do usuário para a URL de autorização do Spotify
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não recebido"

    # Prepare dados para o POST de troca do token
    token_url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": f"Basic {ENCODED_CLIENT}"
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        return f"Erro ao obter token: {response.text}"

    tokens = response.json()
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    access_token = session.get('access_token')

    if not access_token:
        return redirect(url_for('logout'))

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Dados do usuário
    profile_res = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if profile_res.status_code != 200:
        # DEBUG: mostrar código e resposta no log para entender o erro
        app.logger.error(f"Erro ao obter perfil Spotify: {profile_res.status_code} - {profile_res.text}")

        session.clear()
        # opcional: pode mostrar uma página de erro, mensagem, ou mesmo retornar profile_res.text
        return f"Erro ao obter perfil Spotify: {profile_res.status_code}", 400

    profile = profile_res.json()
    user_name = profile.get('display_name', 'Usuário')
    avatar_url = profile['images'][0]['url'] if profile.get('images') else None

    

    # Dados das músicas
    recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=50", headers=headers)
    recent_data = recent_res.json()['items']
    df = process_recent_tracks(recent_data)
    chart_html = generate_top_artists(df)

    return render_template("dash.html", user_name=user_name, avatar_url=avatar_url, chart_html=chart_html)
