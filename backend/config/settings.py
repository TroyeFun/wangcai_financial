from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "LLM Investment Analysis Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/investment_db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # LLM 配置
    DEEPSEEK_V4_API_KEY: Optional[str] = None
    DEEPSEEK_R1_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # 模型路由
    DEFAULT_MODEL: str = "deepseek-v4"
    CHINA_MODEL: str = "deepseek-v4"
    US_MODEL: str = "gpt-4o"
    REASONING_MODEL: str = "deepseek-r1"
    
    # 飞书 Bot 配置
    FEISHU_APP_ID: Optional[str] = None
    FEISHU_APP_SECRET: Optional[str] = None
    FEISHU_VERIFICATION_TOKEN: Optional[str] = None
    FEISHU_BOT_PORT: int = 8001
    
    # 数据源配置
    AKSHARE_RATE_LIMIT: float = 3.0
    FINNHUB_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    
    # 缓存配置（秒）
    CACHE_TTL_DAY_K: int = 86400
    CACHE_TTL_MACRO: int = 604800
    CACHE_TTL_FUND_FLOW: int = 14400
    CACHE_TTL_SENTIMENT: int = 3600
    CACHE_TTL_NEWS: int = 1800
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
