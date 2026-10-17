import os
from flask import Flask
from app.config import Config
from app.models import db, init_db

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
    
    # Register application routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Safe schema migration/init
    init_db(app)
    
    return app
