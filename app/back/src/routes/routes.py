from flask import Blueprint, render_template, redirect, url_for, request, session, current_app
from app import db
from app.back.src.auth.user_auth import get_spotify_auth_url, exchange_code_for_token
from app.back.src.auth.spotify_data import get_recent_tracks, get_user_data
from app.back.src.reuse.etl import (
    process_recent_tracks,
    generate_top_artists,
    generate_hourly_distribution,
    generate_top_tracks
)
from app.back.src.models.models import create_or_update_user, get_user_by_spotify_id, add_tracks_for_user
from datetime import datetime, timedelta

routes = Blueprint("routes", __name__)

@routes.route('/')
@routes.route('/index')
def index():
    return render_template('index.html')


@routes.route('/login-spotify')
def login_spotify():
    # redireciona o usuário para o Spotify
    return redirect(get_spotify_auth_url())


@routes.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código de autorização não recebido", 400

    try:
        # 1️⃣ Troca o código pelos tokens
        tokens = exchange_code_for_token(code)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_in = tokens["expires_in"]

        # 2️⃣ Busca dados do perfil do Spotify
        user_data = get_user_data(access_token)

        # 3️⃣ Calcula data de expiração
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # 4️⃣ Enriquecer o dicionário user_data com informações do token
        user_data.update({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": expires_at
        })

        # 5️⃣ Cria ou atualiza o usuário
        user = create_or_update_user(user_data=user_data, db_session=db.session)

        # 6️⃣ Cria sessão local
        session["spotify_user_id"] = user.spotify_id
        session["access_token"] = access_token

        return redirect(url_for("routes.dashboard"))

    except Exception as e:
        current_app.logger.error(f"Erro no callback: {e}")
        return f"Erro durante autenticação: {str(e)}", 400



@routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.index'))


@routes.route('/dashboard')
def dashboard():

    access_token = session.get('access_token')
    spotify_user_id = session.get('spotify_user_id')
    if not access_token:
        return redirect(url_for('routes.logout'))

    # dados do perfil
    user = get_user_by_spotify_id(spotify_user_id, db.session)

    if not user:
        return redirect(url_for('routes.logout'))

    user_name = user.display_name
    avatar_url = user.avatar_url
    access_token = user.access_token

    # músicas recentes
    recent_data = get_recent_tracks(access_token)
    df = process_recent_tracks(recent_data)
    tracks_list = df.to_dict(orient='records')
    add_tracks_for_user(user.id, tracks_list, db.session)

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
