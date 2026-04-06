from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # ========== 应用配置 ==========
    APP_NAME: str = "LLM Investment Analysis Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ========== 数据库配置 ==========
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/investment_db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # ========== LLM 配置 ==========
    # 优先使用 AIHubMix（国内聚合平台，推荐）
    AIHUBMIX_API_KEY: Optional[str] = None
    AIHUBMIX_BASE_URL: Optional[str] = None  # 默认: https://api.aihubmix.com/v1
    
    # 备选：DeepSeek 官方
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    
    # 备选：OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # 备选：Azure OpenAI
    AZURE_API_KEY: Optional[str] = None
    AZURE_BASE_URL: Optional[str] = None
    AZURE_API_VERSION: Optional[str] = "2024-02-01"
    
    # 模型路由（使用 AIHubMix 时填模型别名即可）
    DEFAULT_MODEL: str = "deepseek-chat"  # 默认模型
    CHINA_MODEL: str = "deepseek-chat"   # 中国市场模型
    US_MODEL: str = "gpt-4o"           # 美国市场模型
    REASONING_MODEL: str = "deepseek-reasoner"  # 推理模型
    
    # ========== 飞书 Bot 配置 ==========
    FEISHU_APP_ID: Optional[str] = None
    FEISHU_APP_SECRET: Optional[str] = None
    FEISHU_VERIFICATION_TOKEN: Optional[str] = None
    FEISHU_BOT_PORT: int = 8001
    
    # ========== 数据源配置 ==========
    AKSHARE_RATE_LIMIT: float = 3.0  # 秒/请求
    FINNHUB_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    
    # ========== 缓存配置（秒） ==========
    CACHE_TTL_DAY_K: int = 86400      # 日K线 24小时
    CACHE_TTL_MACRO: int = 604800     # 宏观指标 7天
    CACHE_TTL_FUND_FLOW: int = 14400  # 资金流向 4小时
    CACHE_TTL_SENTIMENT: int = 3600   # 情绪指标 1小时
    CACHE_TTL_NEWS: int = 1800        # 新闻 30分钟
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
