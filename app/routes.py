from app import app
from flask import render_template, redirect, url_for
from dotenv import load_dotenv
import os
import requests
import urllib.parse

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
REDIRECT_URI = os.getenv('REDIRECT_URI')

@app.route('/')
@app.route('/index')
def index():
    # Não vamos mais montar a URL do Spotify aqui, apenas o link para nossa rota de login
    # O HTML terá um link simples para '/login-spotify'
    return render_template('index.html')

@app.route('/login-spotify') # Esta será a rota que seu botão HTML vai chamar
def login_spotify():
    # Constrói a URL completa de autorização do Spotify no backend
    # É CRUCIAL codificar a REDIRECT_URI para evitar problemas de URL

    auth_url = (
        f"http://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={urllib.parse.quote(SPOTIFY_SCOPES)}" # Codifique os escopos também
    )
    # Redireciona o navegador do usuário para a URL de autorização do Spotify
    return redirect(auth_url)

@app.route('/callback') # Rota para onde o Spotify vai redirecionar após a autorização
def callback():
    code = requests.args.get('code') # Obtém o código de autorização da URL
    if code:
        # Aqui você faria a requisição POST para o Spotify para trocar o 'code'
        # por um 'access_token' e 'refresh_token'.
        # Isso envolveria usar o CLIENT_ID e o CLIENT_SECRET.
        return f"Autorização bem-sucedida! Código recebido: {code}. Agora troque-o por um token de acesso!"
    else:
        error = requests.args.get('error')
        return f"Erro na autorização: {error or 'Usuário negou o acesso.'}"