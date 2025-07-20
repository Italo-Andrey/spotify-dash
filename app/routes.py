from app import app
from flask import render_template, redirect, url_for, request, session
from dotenv import load_dotenv
import base64
import os
import requests
import urllib.parse
from app.etl import (
    process_recent_tracks,
    generate_top_artists,
    generate_hourly_distribution,
    generate_top_tracks
)


load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SPOTIFY_SCOPES = 'user-read-private user-read-recently-played'
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://127.0.0.1:5000/callback')


@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')


@app.route('/login-spotify') #Esta será a rota que o botão HTML vai chamar
def login_spotify():

    auth_url = (
        f"http://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={urllib.parse.quote(SPOTIFY_SCOPES)}"
    )
    # Redireciona o navegador do usuário para a URL de autorização do Spotify
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não recebido"

    #Prepare dados para o POST de troca do token
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
        return f"Erro ao obter perfil Spotify: {profile_res.status_code}", 400

    profile = profile_res.json()
    user_name = profile.get('display_name', 'Usuário')
    avatar_url = profile['images'][0]['url'] if profile.get('images') else None

    

    # Dados das músicas
    recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=50", headers=headers)
    recent_data = recent_res.json()['items']
    df = process_recent_tracks(recent_data)
    
    chart_html_artists = generate_top_artists(df)
    chart_html_hourly = generate_hourly_distribution(df)
    chart_html_tracks = generate_top_tracks(df)

    return render_template(
        "dash.html",
        user_name=user_name,
        avatar_url=avatar_url,
        chart_html_artists=chart_html_artists,
        chart_html_hourly=chart_html_hourly,
        chart_html_tracks=chart_html_tracks
    )
