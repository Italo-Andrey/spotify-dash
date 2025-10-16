import time
from flask import session
from app import app
from app.back.src.auth.user_auth import refresh_access_token
from app.back.src.auth.spotify_data import get_recent_tracks
from app.back.src.reuse.etl import process_recent_tracks
import os

# Exemplo: salvar localmente (você pode adaptar pra banco ou S3)
DATA_PATH = "data/recent_tracks.parquet"

def update_user_data():
    with app.app_context():
        app.logger.info("Iniciando job de atualização de dados do usuário...")

        # ⚠️ Aqui, você precisa saber de quem é o refresh_token
        # Em produção, o ideal seria armazenar os tokens num banco.
        refresh_token = session.get('refresh_token')
        if not refresh_token:
            app.logger.warning("Nenhum usuário autenticado na sessão. Job cancelado.")
            return

        try:
            access_token, new_refresh_token = refresh_access_token(refresh_token)
            session['access_token'] = access_token
            session['refresh_token'] = new_refresh_token

            recent_data = get_recent_tracks(access_token)
            df = process_recent_tracks(recent_data)

            # Salva sem duplicar
            if os.path.exists(DATA_PATH):
                import pandas as pd
                old_df = pd.read_parquet(DATA_PATH)
                combined_df = (
                    pd.concat([old_df, df])
                    .drop_duplicates(subset=["track_id", "played_at"], keep="last")
                )
                combined_df.to_parquet(DATA_PATH, index=False)
            else:
                df.to_parquet(DATA_PATH, index=False)

            app.logger.info("Atualização concluída com sucesso.")

        except Exception as e:
            app.logger.error(f"Erro no scheduler: {e}")
