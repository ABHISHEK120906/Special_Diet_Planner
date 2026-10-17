import os
from flask import Flask
from flask_login import LoginManager
from app.config import Config
from app.models import db, User, init_db

login_manager = LoginManager()


def create_app(config_class=Config):
    # Absolute pathing for robust static/template discovery across local and Vercel serverless lambdas
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    app.config.from_object(config_class)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Safe schema migration/init
    init_db(app)

    return app
