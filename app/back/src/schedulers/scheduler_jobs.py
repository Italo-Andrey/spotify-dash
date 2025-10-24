from app import db
from app.back.src.models.models import User, add_tracks_for_user
from app.back.src.auth.user_auth import refresh_access_token
from app.back.src.auth.spotify_data import get_recent_tracks
from app.back.src.reuse.etl import process_recent_tracks



def refresh_user_tokens(app):
    """
    Job 1: Atualiza tokens de todos os usuários (sem buscar músicas) com commit em lote
    """
    from app import db

    with app.app_context():
        app.logger.info("🔑 Iniciando job de refresh dos tokens...")

        users = User.query.all()
        if not users:
            app.logger.warning("Nenhum usuário encontrado no banco.")
            return

        updated_count = 0

        for user in users:
            try:
                if not user.refresh_token:
                    app.logger.warning(f"Usuário {user.spotify_id} sem refresh_token.")
                    continue

                tokens = refresh_access_token(user.refresh_token)
                user.access_token = tokens['access_token']
                user.refresh_token = tokens.get('refresh_token', user.refresh_token)
                updated_count += 1

                app.logger.info(f"Token preparado para {user.display_name or user.spotify_id}")

            except Exception as e:
                app.logger.error(f"Erro ao atualizar token do usuário {user.spotify_id}: {e}")

        # Commit único para todos os updates
        if updated_count:
            db.session.commit()
            app.logger.info(f"Commit realizado para {updated_count} usuários.")

        app.logger.info("🏁 Job de refresh de tokens finalizado.")



def update_tracks_data(app):
    """
    Job 2: Busca músicas recentes (usando tokens válidos) e faz commit único em lote.
    """

    with app.app_context():
        app.logger.info("🎵 Iniciando job de atualização das músicas recentes...")

        users = User.query.all()
        if not users:
            app.logger.warning("Nenhum usuário encontrado no banco.")
            return

        total_inserted = 0

        try:
            for user in users:
                if not user.access_token:
                    app.logger.warning(f"Usuário {user.spotify_id} sem access_token válido.")
                    continue

                recent_data = get_recent_tracks(user.access_token)
                if not recent_data:
                    app.logger.warning(f"Nenhum dado retornado para o usuário {user.spotify_id}.")
                    continue

                df = process_recent_tracks(recent_data)
                if df.empty:
                    app.logger.info(f"Nenhuma música nova encontrada para {user.display_name or user.spotify_id}.")
                    continue

                tracks_list = df.to_dict(orient="records")

                inserted_count = add_tracks_for_user(
                    user_id=user.id,
                    tracks=tracks_list,
                    db_session=db.session,
                    commit=False,  # Desliga commit interno
                    bulk=True       # Usa inserção em lote
                )

                total_inserted += inserted_count
                app.logger.info(f"{inserted_count} novas músicas preparadas para {user.display_name or user.spotify_id}")

            
            if total_inserted > 0:
                app.logger.info(f"🏁 Commit realizado com sucesso ({total_inserted} músicas inseridas).")
            else:
                app.logger.info("Nenhuma nova música para inserir.")

        except Exception as e:
            app.logger.error(f"Erro durante o job de atualização: {e}", exc_info=True)

        app.logger.info("🏁 Job de atualização das músicas finalizado.")

