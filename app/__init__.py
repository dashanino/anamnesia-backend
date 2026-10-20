from flask import Flask

from config import Config
from app.extensions import db, migrate, jwt
from flask_cors import CORS
# Importar rutas
from app.routes.tavus_route import tavus_bp
from app.routes.caso_clinico_routes import caso_clinico_bp


def create_app():
    app = Flask(__name__)

    app.json.ensure_ascii = False
    app.config.from_object(Config)
    CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:4200"]
        }
    }
)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Registrar rutas de Tavus
    app.register_blueprint(
        tavus_bp,
        url_prefix='/api'
    )

    # Registrar rutas de casos clínicos
    app.register_blueprint(
        caso_clinico_bp,
        url_prefix='/api/casos'
    )

    return app