"""
Application entry point
"""
import os
from app import create_app
from app.config import config

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )