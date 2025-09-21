import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv(".env.local")

class Config:
    # LiveKit Configuration
    LIVEKIT_API_KEY: Optional[str] = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET: Optional[str] = os.getenv("LIVEKIT_API_SECRET")
    LIVEKIT_URL: Optional[str] = os.getenv("LIVEKIT_URL")
    
    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Deepgram Configuration
    DEEPGRAM_API_KEY: Optional[str] = os.getenv("DEEPGRAM_API_KEY")
    
    # Cartesia Configuration
    CARTESIA_API_KEY: Optional[str] = os.getenv("CARTESIA_API_KEY")
    
    @classmethod
    def validate_livekit_config(cls) -> bool:
        """Validate that all required LiveKit configuration is present"""
        required_vars = [cls.LIVEKIT_API_KEY, cls.LIVEKIT_API_SECRET, cls.LIVEKIT_URL]
        return all(required_vars)
    
    @classmethod
    def validate_database_config(cls) -> bool:
        """Validate that database configuration is present"""
        return cls.DATABASE_URL is not None
    
    @classmethod
    def get_missing_livekit_vars(cls) -> list[str]:
        """Get list of missing LiveKit environment variables"""
        missing = []
        if not cls.LIVEKIT_API_KEY:
            missing.append("LIVEKIT_API_KEY")
        if not cls.LIVEKIT_API_SECRET:
            missing.append("LIVEKIT_API_SECRET")
        if not cls.LIVEKIT_URL:
            missing.append("LIVEKIT_URL")
        return missing
    
    @classmethod
    def get_all_missing_vars(cls) -> list[str]:
        """Get list of all missing required environment variables"""
        missing = cls.get_missing_livekit_vars()
        if not cls.DATABASE_URL:
            missing.append("DATABASE_URL")
        return missing

config = Config()

LIVEKIT_API_KEY = config.LIVEKIT_API_KEY
LIVEKIT_API_SECRET = config.LIVEKIT_API_SECRET
LIVEKIT_URL = config.LIVEKIT_URL
DATABASE_URL = config.DATABASE_URL 