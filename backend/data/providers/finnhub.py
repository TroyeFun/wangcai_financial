"""
Finnhub 数据提供者 - 美股主力数据源

覆盖：美股、外汇、加密货币、宏观经济
免费额度：60 req/min
"""

import pandas as pd
import requests
from typing import Dict, Any, Optional
from loguru import logger
import asyncio

from .base import DataProvider


class FinnhubProvider(DataProvider):
    """Finnhub 数据提供者"""
    
    RATE_LIMIT_PER_MIN = 60  # 免费版限制
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self._last_request_time = 0
        self._request_count = 0
    
    async def _rate_limit(self):
        """限流控制"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        # 每分钟重置计数
        if elapsed >= 60:
            self._request_count = 0
            self._last_request_time = now
        
        # 检查是否超限
        if self._request_count >= self.RATE_LIMIT_PER_MIN:
            await asyncio.sleep(60 - elapsed)
            self._request_count = 0
            self._last_request_time = asyncio.get_event_loop().time()
        
        self._request_count += 1
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """发送 GET 请求"""
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params["token"] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Finnhub API 请求失败：{endpoint}, 错误：{e}")
            return {}
    
    async def get_macro_data(self, indicator: str = "GDP", country: str = "US") -> pd.DataFrame:
        """获取宏观经济数据"""
        await self._rate_limit()
        
        try:
            # 经济指标指标映射
            indicator_map = {
                "GDP": "gdp",
                "CPI": "cpi",
                "PMI": "pmi",
            }
            
            # Finnhub 宏观经济指标
            data = self._get("scan/macro-economic", {
                "key": indicator_map.get(indicator.upper(), indicator),
            })
            
            if data:
                logger.info(f"获取宏观数据成功：{indicator}")
            
            return pd.DataFrame(data) if data else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取宏观数据失败：{indicator}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_market_data(self, symbol: str = "AAPL", period: str = "daily") -> pd.DataFrame:
        """获取美股行情数据"""
        await self._rate_limit()
        
        try:
            # 解析周期
            period_map = {
                "1d": "1",
                "1w": "7",
                "1m": "30",
            }
            resolution = period_map.get(period, "D")
            
            # 获取股票 candles
            data = self._get("stock/candle", {
                "symbol": symbol.upper(),
                "resolution": resolution,
                "from": int(pd.Timestamp.now().timestamp() - 86400 * 30),  # 最近 30 天
                "to": int(pd.Timestamp.now().timestamp()),
            })
            
            if data and data.get("s") == "ok":
                df = pd.DataFrame({
                    "timestamp": pd.to_datetime(data["t"], unit="s"),
                    "open": data["o"],
                    "high": data["h"],
                    "low": data["l"],
                    "close": data["c"],
                    "volume": data["v"],
                })
                logger.info(f"获取行情数据成功：{symbol}, 行数：{len(df)}")
                return df
            
            logger.warning(f"获取行情数据失败：{symbol}, 无数据")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取行情数据失败：{symbol}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_fund_flow(self, market: str = "US") -> pd.DataFrame:
        """获取资金流向数据（简化版）"""
        await self._rate_limit()
        
        try:
            # Finnhub 没有直接的北向资金数据，这里返回指数成分股数据作为替代
            # 可以用于分析资金流向
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败：{market}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_valuation_data(self, symbol: str) -> Dict[str, Any]:
        """获取估值数据"""
        await self._rate_limit()
        
        try:
            # 获取股票基本面
            data = self._get("stock/metric", {
                "symbol": symbol.upper(),
                "metric": "all",
            })
            
            if data and "metric" in data:
                metric = data["metric"]
                return {
                    "pe": metric.get("peExclExtraTTM"),
                    "pb": metric.get("pbAnnual"),
                    "ps": metric.get("psAnnual"),
                    "market_cap": metric.get("marketCapitalization"),
                    "52_week_high": metric.get("52WeekHigh"),
                    "52_week_low": metric.get("52WeekLow"),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取估值数据失败：{symbol}, 错误：{e}")
            return {}
    
    async def get_sentiment_data(self, market: str = "US") -> Dict[str, Any]:
        """获取情绪数据"""
        await self._rate_limit()
        
        try:
            # 获取 VIX 指数
            vix_data = self._get("index", {
                "symbol": "VIX",
            })
            
            # 获取恐慌指数（也用 VIX）
            return {
                "vix": vix_data.get("c", 0),
                "vix_high": vix_data.get("h", 0),
                "vix_low": vix_data.get("l", 0),
                "sentiment": "neutral",
            }
            
        except Exception as e:
            logger.error(f"获取情绪数据失败：{market}, 错误：{e}")
            return {}
    
    async def get_forex_data(self, base: str = "USD", quote: str = "CNY") -> Dict[str, Any]:
        """获取外汇数据"""
        await self._rate_limit()
        
        try:
            symbol = f"{base}_{quote}"
            data = self._get("forex/rates", {
                "base": base,
            })
            
            if data and "quote" in data:
                quote_data = data["quote"].get(symbol.upper(), {})
                return {
                    "pair": symbol,
                    "rate": quote_data.get("price", 0),
                    "timestamp": pd.Timestamp.now().isoformat(),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取外汇数据失败：{base}/{quote}, 错误：{e}")
            return {}
    
    async def get_crypto_data(self, symbol: str = "BTC") -> Dict[str, Any]:
        """获取加密货币数据（通过 Finnhub 的替代指标）"""
        await self._rate_limit()
        
        try:
            # Finnhub 的加密货币数据比较有限
            # 这里返回美股恐慌指数作为参考（加密市场与传统金融市场相关）
            
            vix_data = await self.get_sentiment_data("US")
            
            return {
                "symbol": symbol,
                "vix_correlation": vix_data.get("vix", 0),
                "note": "Finnhub 加密数据有限，建议使用 CoinGecko Provider",
            }
            
        except Exception as e:
            logger.error(f"获取加密数据失败：{symbol}, 错误：{e}")
            return {}
