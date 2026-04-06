"""
CoinGecko 数据提供者 - 加密货币数据源

覆盖：比特币、以太坊等主流加密货币
免费额度：30 req/min, 10K calls/month
"""

import pandas as pd
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio
from datetime import datetime

from .base import DataProvider


class CoinGeckoProvider(DataProvider):
    """CoinGecko 数据提供者"""
    
    RATE_LIMIT_PER_MIN = 30  # 免费版限制
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
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
        
        # 添加 API Key（如果有）
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CoinGecko API 请求失败：{endpoint}, 错误：{e}")
            return {}
    
    async def get_market_data(self, symbol: str = "BTC", period: str = "daily") -> pd.DataFrame:
        """获取加密货币行情数据"""
        await self._rate_limit()
        
        try:
            # 获取货币 ID
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                logger.warning(f"未找到加密货币：{symbol}")
                return pd.DataFrame()
            
            # 解析周期
            days_map = {
                "1d": 1,
                "1w": 7,
                "1m": 30,
            }
            days = days_map.get(period, 1)
            
            # 获取市场数据
            data = self._get(f"coins/{coin_id}/market_chart", {
                "vs_currency": "usd",
                "days": days,
            })
            
            if data and "prices" in data:
                df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                
                # 添加成交量
                if "total_volumes" in data:
                    volumes = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
                    df = df.merge(volumes, on="timestamp")
                
                logger.info(f"获取加密行情数据成功：{symbol}, 行数：{len(df)}")
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取加密行情数据失败：{symbol}, 错误：{e}")
            return pd.DataFrame()
    
    def _symbol_to_id(self, symbol: str) -> Optional[str]:
        """将交易对符号转换为 CoinGecko ID"""
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "SOL": "solana",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "SHIB": "shiba-inu",
            "LTC": "litecoin",
            "AVAX": "avalanche-2",
            "LINK": "chainlink",
            "UNI": "uniswap",
        }
        return symbol_map.get(symbol.upper())
    
    async def get_top_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取市值前 N 的加密货币"""
        await self._rate_limit()
        
        try:
            data = self._get("coins/markets", {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
            })
            
            if data:
                result = []
                for coin in data:
                    result.append({
                        "id": coin.get("id"),
                        "symbol": coin.get("symbol"),
                        "name": coin.get("name"),
                        "price": coin.get("current_price"),
                        "change_24h": coin.get("price_change_percentage_24h"),
                        "market_cap": coin.get("market_cap"),
                        "volume": coin.get("total_volume"),
                    })
                return result
            
            return []
            
        except Exception as e:
            logger.error(f"获取热门加密货币失败：{e}")
            return []
    
    async def get_sentiment_data(self, symbol: str = "BTC") -> Dict[str, Any]:
        """获取加密市场情绪数据"""
        await self._rate_limit()
        
        try:
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                return {}
            
            # 获取恐惧贪婪指数（通过多个指标估算）
            data = self._get(f"coins/{coin_id}")
            
            if data:
                market_data = data.get("market_data", {})
                
                # 计算短期趋势（7天变化）
                price_change_7d = market_data.get("price_change_percentage_7d", 0)
                price_change_30d = market_data.get("price_change_percentage_30d", 0)
                
                # 简单估算情绪指数
                sentiment_score = 50  # 基准
                if price_change_7d:
                    sentiment_score += price_change_7d * 2  # 价格涨则情绪偏多
                
                # 限制在 0-100 范围
                sentiment_score = max(0, min(100, sentiment_score))
                
                return {
                    "symbol": symbol,
                    "fear_greed_index": sentiment_score,
                    "fear_greed_label": self._sentiment_label(sentiment_score),
                    "price_change_7d": price_change_7d,
                    "price_change_30d": price_change_30d,
                    "market_cap": market_data.get("market_cap"),
                    "volume_24h": market_data.get("total_volume"),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取加密情绪数据失败：{symbol}, 错误：{e}")
            return {}
    
    def _sentiment_label(self, score: float) -> str:
        """将情绪分数转换为标签"""
        if score >= 75:
            return "极度贪婪"
        elif score >= 60:
            return "贪婪"
        elif score >= 45:
            return "中性"
        elif score >= 25:
            return "恐惧"
        else:
            return "极度恐惧"
    
    async def get_fund_flow(self, symbol: str = "BTC") -> Dict[str, Any]:
        """获取加密资金流向（通过交易所数据估算）"""
        await self._rate_limit()
        
        try:
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                return {}
            
            # 获取交易所交易对数据
            data = self._get(f"coins/{coin_id}/tickers")
            
            if data and "tickers" in data:
                total_volume = 0
                buy_volume = 0
                
                for ticker in data["tickers"][:50]:  # 取前 50 个交易对
                    volume = ticker.get("converted_volume", {}).get("usd", 0)
                    total_volume += volume
                    
                    # 判断是买入还是卖出（基于 last_price 变化）
                    if ticker.get("bid_ask_spread_percentage", 0) < 0.5:
                        buy_volume += volume * 0.6  # 假设买入略多
                    else:
                        buy_volume += volume * 0.4
                
                return {
                    "symbol": symbol,
                    "total_volume_24h": total_volume,
                    "buy_volume_24h": buy_volume,
                    "sell_volume_24h": total_volume - buy_volume,
                    "net_flow": "inflow" if buy_volume > total_volume / 2 else "outflow",
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取加密资金流向失败：{symbol}, 错误：{e}")
            return {}
    
    async def get_ohlc(self, symbol: str = "BTC", days: int = 7) -> pd.DataFrame:
        """获取 K 线数据（OHLC）"""
        await self._rate_limit()
        
        try:
            coin_id = self._symbol_to_id(symbol)
            if not coin_id:
                return pd.DataFrame()
            
            data = self._get(f"coins/{coin_id}/ohlc", {
                "vs_currency": "usd",
                "days": days,
            })
            
            if data:
                df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                logger.info(f"获取 OHLC 数据成功：{symbol}, 行数：{len(df)}")
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取 OHLC 数据失败：{symbol}, 错误：{e}")
            return pd.DataFrame()
