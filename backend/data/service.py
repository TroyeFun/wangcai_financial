"""
统一数据服务层

封装所有数据访问，为 Agent 提供统一的数据接口
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from loguru import logger

from .providers.akshare import AkShareProvider
from .providers.finnhub import FinnhubProvider
from .providers.coingecko import CoinGeckoProvider
from .cache import CacheManager


class DataService:
    """统一数据服务"""
    
    def __init__(self, cache_manager: CacheManager, api_keys: Dict[str, str] = None):
        self.cache = cache_manager
        self.api_keys = api_keys or {}
        
        # 初始化数据提供者
        self.akshare = AkShareProvider()
        self.finnhub = FinnhubProvider(api_key=self.api_keys.get("finnhub", ""))
        self.coingecko = CoinGeckoProvider(api_key=self.api_keys.get("coingecko", ""))
        
        logger.info("数据服务初始化完成")
    
    def _market_to_provider(self, market: str) -> tuple:
        """根据市场类型返回对应的 Provider
        
        Returns:
            (provider, symbol_prefix)
        """
        if "A" in market or "沪深" in market or "上证" in market or "深证" in market:
            return self.akshare, ""
        elif "港" in market or "HK" in market:
            return self.akshare, ""
        elif "美" in market or "纳" in market or "SP" in market or "US" in market:
            return self.finnhub, "us_"
        elif "加密" in market or "BTC" in market or "ETH" in market:
            return self.coingecko, "crypto_"
        else:
            # 默认 A 股
            return self.akshare, ""
    
    async def get_market_data(self, symbol: str, market: str = "A 股", period: str = "daily") -> pd.DataFrame:
        """获取行情数据
        
        Args:
            symbol: 标的代码
            market: 市场类型
            period: 周期
            
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        provider, prefix = self._market_to_provider(market)
        
        # 先从缓存获取
        cache_key = f"{prefix}{symbol}"
        cached = await self.cache.get("market", cache_key)
        if cached is not None:
            logger.debug(f"从缓存获取行情数据：{cache_key}")
            return pd.DataFrame(cached)
        
        # 从 Provider 获取
        data = await provider.get_market_data(symbol, period)
        
        # 写入缓存
        if not data.empty:
            await self.cache.set("market", cache_key, data.to_dict(), self.cache.CACHE_TTL_DAY_K)
        
        return data
    
    async def get_macro_data(self, indicator: str, country: str = "CN") -> Dict[str, Any]:
        """获取宏观数据
        
        Args:
            indicator: 指标名称
            country: 国家
            
        Returns:
            宏观数据字典
        """
        # 先从缓存获取
        cache_key = f"{country}_{indicator}"
        cached = await self.cache.get("macro", cache_key)
        if cached is not None:
            logger.debug(f"从缓存获取宏观数据：{cache_key}")
            return cached
        
        # 从 AkShare 获取
        data = await self.akshare.get_macro_data(indicator, country)
        
        if not data.empty:
            result = data.to_dict()
            await self.cache.set("macro", cache_key, result, self.cache.CACHE_TTL_MACRO)
            return result
        
        return {}
    
    async def get_fund_flow(self, market: str = "A 股") -> Dict[str, Any]:
        """获取资金流向数据
        
        Args:
            market: 市场类型
            
        Returns:
            资金流向数据
        """
        # 先从缓存获取
        cache_key = "north" if "A" in market else "margin" if "两融" in market else market
        cached = await self.cache.get("fundflow", cache_key)
        if cached is not None:
            logger.debug(f"从缓存获取资金流向：{cache_key}")
            return cached
        
        # 从 Provider 获取
        data = await self.akshare.get_fund_flow(market)
        
        if not data.empty:
            result = data.to_dict()
            await self.cache.set("fundflow", cache_key, result, self.cache.CACHE_TTL_FUND_FLOW)
            return result
        
        return {}
    
    async def get_valuation(self, symbol: str, market: str = "A 股") -> Dict[str, Any]:
        """获取估值数据
        
        Args:
            symbol: 标的代码
            market: 市场类型
            
        Returns:
            估值数据
        """
        provider, prefix = self._market_to_provider(market)
        
        # 先从缓存获取
        cache_key = f"{prefix}valuation_{symbol}"
        cached = await self.cache.get("valuation", cache_key)
        if cached is not None:
            logger.debug(f"从缓存获取估值数据：{cache_key}")
            return cached
        
        # 从 Provider 获取
        data = await provider.get_valuation_data(symbol)
        
        if data:
            await self.cache.set("valuation", cache_key, data, self.cache.CACHE_TTL_FUND_FLOW)
        
        return data
    
    async def get_sentiment(self, market: str = "A 股") -> Dict[str, Any]:
        """获取市场情绪数据
        
        Args:
            market: 市场类型
            
        Returns:
            情绪数据
        """
        # 先从缓存获取
        cache_key = "cn" if "A" in market else "us" if "美" in market else "crypto"
        cached = await self.cache.get("sentiment", cache_key)
        if cached is not None:
            logger.debug(f"从缓存获取情绪数据：{cache_key}")
            return cached
        
        # 根据市场类型获取
        if "A" in market:
            data = await self.akshare.get_sentiment_data(market)
        elif "美" in market:
            data = await self.finnhub.get_sentiment_data(market)
        elif "加密" in market or "BTC" in market:
            data = await self.coingecko.get_sentiment_data(symbol="BTC")
        else:
            data = {}
        
        if data:
            await self.cache.set("sentiment", cache_key, data, self.cache.CACHE_TTL_SENTIMENT)
        
        return data
    
    async def get_index_components(self, index_name: str) -> List[str]:
        """获取指数成分股
        
        Args:
            index_name: 指数名称
            
        Returns:
            成分股代码列表
        """
        # 常见指数成分股映射
        index_map = {
            "沪深300": ["600519.SH", "600036.SH", "601318.SH", "000858.SZ", "601166.SH",
                       "600016.SH", "600030.SH", "601328.SH", "601088.SH", "600887.SH"],
            "上证50": ["600519.SH", "600036.SH", "601318.SH", "600016.SH", "601328.SH",
                      "600030.SH", "601088.SH", "601166.SH", "600050.SH", "601668.SH"],
        }
        
        return index_map.get(index_name, [])
    
    async def get_market_overview(self, market: str = "A 股") -> Dict[str, Any]:
        """获取市场概览（多个指标汇总）
        
        Args:
            market: 市场类型
            
        Returns:
            市场概览数据
        """
        provider, prefix = self._market_to_provider(market)
        
        overview = {
            "market": market,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
        
        # 获取主要指数
        if "A" in market:
            overview["indices"] = {}
            for symbol in ["000001.SH", "399001.SZ", "399006.SZ"]:
                data = await self.get_market_data(symbol, market)
                if not data.empty:
                    latest = data.iloc[-1]
                    overview["indices"][symbol] = {
                        "close": float(latest.get("close", 0)),
                        "change": float(latest.get("close", 0) - latest.get("open", 0)),
                    }
        
        # 获取资金流向
        overview["fund_flow"] = await self.get_fund_flow(market)
        
        # 获取情绪
        overview["sentiment"] = await self.get_sentiment(market)
        
        return overview
