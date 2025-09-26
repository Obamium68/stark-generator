"""
Application configuration
"""
import os


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JSON_SORT_KEYS = False
    
    MAX_QUERIES = int(os.environ.get('MAX_QUERIES', 100))
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 360))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}