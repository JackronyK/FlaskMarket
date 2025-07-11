from flask import Flask
from config import Config
from extensions import db, migrate
from datetime import timedelta
from admins import admins_bp
from users import users_bp
from main import main_bp
import os




def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.permanent_session_lifetime = timedelta(minutes=10)

    # initialize the app
    db.init_app(app)
    migrate.init_app(app, db)


    # Creating the upload folder if not  exists
    upload_path = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_path, exist_ok=True)


    # Register the Blueprints
    app.register_blueprint(admins_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(main_bp)

    # Importing models for db creation
    with app.app_context():
        from main import models as main_models
        from admins import models as admin_models
        from users import  models as users_models

    return app

app = create_app()