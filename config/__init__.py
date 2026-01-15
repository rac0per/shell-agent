import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    MODEL_SERVER_HOST = os.getenv("MODEL_SERVER_HOST", "127.0.0.1")
    MODEL_SERVER_PORT = int(os.getenv("MODEL_SERVER_PORT", 8000))
    MODEL_PATH = os.getenv("MODEL_PATH", "./models/qwen-7b")
    DB_PATH = os.getenv("DB_PATH", "./data/memory.db")
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", 256))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))
    TOP_P = float(os.getenv("TOP_P", 0.9))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    DB_PATH = "./data/test_memory.db"
    DEBUG = True

def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv("ENV", "development")
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)
