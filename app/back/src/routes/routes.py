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
from app.back.src.models.models import create_or_update_user, get_user_by_spotify_id, add_tracks_for_user, get_tracks_dataframe_for_user
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
        # Troca o código pelos tokens
        tokens = exchange_code_for_token(code)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_in = tokens["expires_in"]

        # Busca dados do perfil do Spotify
        user_data = get_user_data(access_token)

        # Calcula data de expiração
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Enriquecer o dicionário user_data com informações do token
        user_data.update({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": expires_at
        })

        # Cria ou atualiza o usuário
        user = create_or_update_user(user_data=user_data, db_session=db.session)

        # Cria sessão local
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

    # Dados do perfil
    user = get_user_by_spotify_id(spotify_user_id, db.session)
    if not user:
        return redirect(url_for('routes.logout'))

    user_name = user.display_name
    avatar_url = user.avatar_url
    access_token = user.access_token

    # Atualiza as músicas recentes do usuário
    recent_data = get_recent_tracks(access_token)
    if recent_data:
        df = process_recent_tracks(recent_data)
        if not df.empty:
            tracks_list = df.to_dict(orient="records")
            # Aqui usamos a função normalmente com commit=True (default)
            inserted_count = add_tracks_for_user(
                user.id,
                tracks_list,
                db.session,
                commit=True,
                bulk=False
            )
            current_app.logger.info(f"{inserted_count} novas faixas inseridas para {user_name}.")
        else:
            current_app.logger.info(f"Nenhuma música nova retornada para {user_name}.")
    else:
        current_app.logger.warning(f"API do Spotify não retornou dados para {user_name}.")

    # Dataframe para gerar os gráficos
    df_all = get_tracks_dataframe_for_user(user.id, db.session)

    chart_html_artists = generate_top_artists(df_all)
    chart_html_hourly = generate_hourly_distribution(df_all)
    chart_html_tracks = generate_top_tracks(df_all)

    return render_template(
        "dash.html",
        user_name=user_name,
        avatar_url=avatar_url,
        chart_html_artists=chart_html_artists,
        chart_html_hourly=chart_html_hourly,
        chart_html_tracks=chart_html_tracks
    )
