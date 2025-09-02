"""
Configuration loader for Spotify Display
Loads settings from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Spotify API settings
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') 
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080')
    
    # Flask settings
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Application settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 2))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        missing = []
        
        if not cls.SPOTIFY_CLIENT_ID:
            missing.append('SPOTIFY_CLIENT_ID')
        if not cls.SPOTIFY_CLIENT_SECRET:
            missing.append('SPOTIFY_CLIENT_SECRET')
            
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

def load_config():
    """Load and validate configuration"""
    config = Config()
    config.validate()
    return config