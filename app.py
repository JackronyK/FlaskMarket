from flask import Flask
from config import Config
from extensions import db, migrate, mail
from datetime import timedelta
from admins import admins_bp
from users import users_bp
from main import main_bp
from orders import orders_bp
import os
import logging

# logging configuration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Create the Flask application
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.logger.setLevel(logging.DEBUG)
    app.permanent_session_lifetime = timedelta(minutes=10)

    # initialize the app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)


    # Creating the upload folder if not  exists
    upload_path = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_path, exist_ok=True)


    # Register the Blueprints
    app.register_blueprint(admins_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(orders_bp)

    # Importing models for db creation
    with app.app_context():
        from main import models as main_models
        from admins import models as admin_models
        from users import  models as users_models
        from orders import models as order_models

    return app

app = create_app()