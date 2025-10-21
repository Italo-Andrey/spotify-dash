from flask import Flask
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar extensões (sem app ainda)
db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler()

def create_app():

    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "front/src/templates")
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "front/src/static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.secret_key = os.getenv('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    scheduler.start()

    # Importa rotas dentro do contexto da função
    from app.back.src.routes.routes import routes as routes_blueprint
    app.register_blueprint(routes_blueprint)

    return app
