from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


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
    user = db_session.query(User).filter_by(spotify_id=user_data['spotify_id']).first()

    if user:
        # Atualiza campos existentes
        user.display_name = user_data.get('display_name')
        user.avatar_url = user_data.get('avatar_url')
        user.access_token = user_data.get('access_token')
        user.refresh_token = user_data.get('refresh_token')
        user.token_expires_at = user_data.get('token_expires_at')
    else:
        # Cria novo usuário
        user = User(**user_data)
        db_session.add(user)

    db_session.commit()
    return user
