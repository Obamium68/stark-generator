"""
Flask application factory
"""
from flask import Flask
from app.config import Config


def create_app(config_class=Config):
    """
    Application factory pattern
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app