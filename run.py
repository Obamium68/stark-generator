"""
Application entry point
"""
import os
from app import create_app
from app.config import config
from flask_cors import CORS


config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])
CORS(app, origins=os.environ.get('CORS_ORIGIN'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )