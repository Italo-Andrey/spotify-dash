from app import app
from flask import render_template, redirect, url_for, request, session
from app.back.src.auth.user_auth import get_spotify_auth_url, exchange_code_for_token
import requests
from app.back.src.reuse.etl import (
    process_recent_tracks,
    generate_top_artists,
    generate_hourly_distribution,
    generate_top_tracks
)
from app.back.src.auth.spotify_data import get_recent_tracks, get_user_data
from datetime import datetime, timedelta
from app.back.src.models.models import create_or_update_user


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login-spotify')
def login_spotify():
    # redireciona o usuário para o Spotify
    return redirect(get_spotify_auth_url())


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não recebido", 400

    try:
        tokens = exchange_code_for_token(code)  # retorna dict
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_in = tokens["expires_in"]

        # Pega dados do perfil
        user_data = get_user_data(access_token)

        # Calcula data de expiração
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Cria ou atualiza usuário no banco
        user = create_or_update_user(
            db_session=db.session,  # ou conexão psycopg2
            spotify_user_id=user_data["spotify_user_id"],
            display_name=user_data["display_name"],
            profile_image_url=user_data["profile_image_url"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at
        )

        # Cria sessão local
        session["user_id"] = user.id
        session["spotify_user_id"] = user.spotify_user_id

        return redirect(url_for("dashboard"))

    except Exception as e:
        app.logger.error(f"Erro no callback: {e}")
        return f"Erro durante autenticação: {str(e)}", 400



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('logout'))

    # dados do perfil
    user_name, avatar_url = get_user_data(access_token, session)

    # músicas recentes
    recent_data = get_recent_tracks(access_token)

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
