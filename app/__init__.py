from flask import Flask
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from app.back.src.routes import routes
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()


db = SQLAlchemy()  # cria a instância do banco
migrate = Migrate()  # controle de migrações

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco e migrações
db.init_app(app)
migrate.init_app(app, db)

scheduler = BackgroundScheduler()
scheduler.start()