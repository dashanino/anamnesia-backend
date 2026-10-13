from flask import Flask


from config import Config
from app.extensions import db, migrate, jwt

def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    
    
    return app