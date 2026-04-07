from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Finance Dashboard API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    
    DATABASE_URL: str = "sqlite:///./finance.db"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()