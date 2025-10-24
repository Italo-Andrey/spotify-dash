from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from sqlalchemy import and_
from pandas import DataFrame


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(255))
    avatar_url = db.Column(db.String(500))
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamento com tracks
    tracks = db.relationship('Track', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.display_name or self.spotify_id}>'



class Track(db.Model):
    __tablename__ = 'tracks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    track_name = db.Column(db.String(255))
    artist_name = db.Column(db.String(255))
    played_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Track {self.track_name} - {self.artist_name}>'



def create_or_update_user(user_data, db_session):
    user = db_session.query(User).filter_by(spotify_id=user_data['spotify_user_id']).first()

    if user:
        # Atualiza campos existentes
        user.display_name = user_data.get('display_name')
        user.avatar_url = user_data.get('profile_image_url')
        user.access_token = user_data.get('access_token')
        user.refresh_token = user_data.get('refresh_token')
        user.token_expires_at = user_data.get('token_expires_at')
    else:
        # Cria novo usuário
        user = User(
            spotify_id=user_data['spotify_user_id'],
            display_name=user_data.get('display_name'),
            avatar_url=user_data.get('profile_image_url'),
            access_token=user_data.get('access_token'),
            refresh_token=user_data.get('refresh_token'),
            token_expires_at=user_data.get('token_expires_at'),
        )
        db_session.add(user)

    db_session.commit()
    return user



def get_user_by_spotify_id(spotify_id, db_session):
    """Retorna o objeto User do banco pelo spotify_id."""
    return db_session.query(User).filter_by(spotify_id=spotify_id).first()



def add_tracks_for_user(user_id, tracks, db_session, commit=True, bulk=True):
    """
    Adiciona faixas para um usuário, comparando apenas as 50 últimas músicas do banco.
    Garante consistência de timezone e evita duplicidades.
    """

    # 1️⃣ Busca as 50 últimas músicas já salvas no banco
    existing = (
        db_session.query(Track.played_at)
        .filter(Track.user_id == user_id)
        .order_by(Track.played_at.desc())
        .limit(50)
        .all()
    )

    # Converte para datetime "naive" (sem timezone)
    existing_played = {row[0].replace(tzinfo=None) for row in existing}

    # 2️⃣ Ordena as músicas recentes por played_at e pega as últimas 50
    tracks = sorted(tracks, key=lambda x: x['played_at'], reverse=True)[:50]

    new_tracks = []
    for t in tracks:
        # Converte para datetime nativo Python sem timezone
        played_at = (
            t['played_at'].to_pydatetime().replace(tzinfo=None)
            if hasattr(t['played_at'], 'to_pydatetime')
            else pd.to_datetime(t['played_at']).to_pydatetime().replace(tzinfo=None)
        )

        # Só insere se ainda não existir
        if played_at not in existing_played:
            new_tracks.append(
                Track(
                    user_id=user_id,
                    track_name=t['Músicas'],
                    artist_name=t['Artistas'],
                    played_at=played_at,
                )
            )

    # 3️⃣ Caso não haja novos registros, encerra
    if not new_tracks:
        return 0

    # 4️⃣ Inserção (bulk ou não)
    if bulk:
        db_session.bulk_save_objects(new_tracks)
    else:
        db_session.add_all(new_tracks)

    # 5️⃣ Commit opcional
    if commit:
        db_session.commit()

    return len(new_tracks)








def get_tracks_dataframe_for_user(user_id, db_session):
    """Retorna um DataFrame com todas as faixas do usuário."""

    tracks = db_session.query(Track).filter(Track.user_id == user_id).all()
    if not tracks:
        return DataFrame(columns=['Músicas', 'Artistas', 'played_at'])

    data = [{
        'Músicas': t.track_name,
        'Artistas': t.artist_name,
        'played_at': t.played_at
    } for t in tracks]

    return DataFrame(data)