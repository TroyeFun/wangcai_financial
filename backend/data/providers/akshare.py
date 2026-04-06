"""
AkShare 数据提供者 - MVP 主力数据源

覆盖：A 股、港股、期货、基金、债券、黄金、中国宏观数据
完全免费，限流约 3 秒/请求
"""

import pandas as pd
import akshare as ak
from typing import Dict, Any, Optional
from loguru import logger
import asyncio

from .base import DataProvider


class AkShareProvider(DataProvider):
    """AkShare 数据提供者"""
    
    RATE_LIMIT = 3.0  # 秒/请求
    
    def __init__(self):
        self._last_request_time = 0
    
    async def _rate_limit(self):
        """限流控制"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT:
            await asyncio.sleep(self.RATE_LIMIT - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def get_macro_data(self, indicator: str, country: str = "CN") -> pd.DataFrame:
        """获取中国宏观经济数据"""
        await self._rate_limit()
        
        try:
            if country != "CN":
                # AkShare 主要覆盖中国数据
                logger.warning(f"AkShare 不支持 {country} 宏观数据，返回空 DataFrame")
                return pd.DataFrame()
            
            # 根据指标类型获取数据
            if indicator.upper() == "GDP":
                df = ak.macro_china_gdp_year()
            elif indicator.upper() == "CPI":
                df = ak.macro_china_cpi_year()
            elif indicator.upper() == "PMI":
                df = ak.macro_china_pmi_year()
            elif indicator.upper() == "M2":
                df = ak.macro_china_money_supply_year()
            elif indicator.upper() == "利率":
                df = ak.macro_china_loan_prime_rate()
            elif indicator.upper() == "汇率":
                df = ak.macro_china_usd_rmb()
            else:
                logger.warning(f"未知的宏观指标：{indicator}")
                return pd.DataFrame()
            
            logger.info(f"获取宏观数据成功：{indicator}, 行数：{len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取宏观数据失败：{indicator}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_market_data(self, symbol: str, period: str = "daily") -> pd.DataFrame:
        """获取 A 股/港股行情数据"""
        await self._rate_limit()
        
        try:
            # 解析标的代码
            if "." in symbol:
                # 格式：000001.SH, 600519.SH 等
                code, exchange = symbol.split(".")
                if exchange in ["SH", "SZ"]:
                    df = ak.stock_zh_a_hist(symbol=symbol, period=period, adjust="qfq")
                elif exchange == "HK":
                    df = ak.stock_hk_daily(symbol=code, adjust="qfq")
                else:
                    logger.warning(f"不支持的交易所：{exchange}")
                    return pd.DataFrame()
            else:
                # 默认 A 股
                df = ak.stock_zh_a_hist(symbol=symbol, period=period, adjust="qfq")
            
            logger.info(f"获取行情数据成功：{symbol}, 行数：{len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取行情数据失败：{symbol}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_fund_flow(self, market: str = "A 股") -> pd.DataFrame:
        """获取资金流向数据"""
        await self._rate_limit()
        
        try:
            if market == "A 股":
                # 北向资金
                df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            elif market == "港股":
                # 南向资金
                df = ak.stock_hsgt_south_net_flow_in_em(symbol="南下")
            elif market == "两融":
                # 融资融券
                df = ak.stock_margin_sse()
            else:
                logger.warning(f"未知的资金流向市场：{market}")
                return pd.DataFrame()
            
            logger.info(f"获取资金流向数据成功：{market}, 行数：{len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败：{market}, 错误：{e}")
            return pd.DataFrame()
    
    async def get_valuation_data(self, symbol: str) -> Dict[str, Any]:
        """获取估值数据"""
        await self._rate_limit()
        
        try:
            # 获取指数估值
            if "指数" in symbol or symbol.startswith("000") or symbol.startswith("399"):
                df = ak.index_value_hist_funddb(symbol=symbol)
                if len(df) > 0:
                    latest = df.iloc[-1]
                    return {
                        "pe": float(latest.get("pe", 0)),
                        "pb": float(latest.get("pb", 0)),
                        "ps": float(latest.get("ps", 0)),
                        "pe_percentile": float(latest.get("pe_percentile", 0)),
                        "pb_percentile": float(latest.get("pb_percentile", 0)),
                    }
            
            # 个股估值
            df = ak.stock_a_lg_indicator(symbol=symbol)
            if len(df) > 0:
                latest = df.iloc[-1]
                return {
                    "pe": float(latest.get("pe", 0)),
                    "pb": float(latest.get("pb", 0)),
                    "ps": float(latest.get("ps_ttm", 0)),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取估值数据失败：{symbol}, 错误：{e}")
            return {}
    
    async def get_sentiment_data(self, market: str = "A 股") -> Dict[str, Any]:
        """获取情绪数据（简化版）"""
        await self._rate_limit()
        
        try:
            # 这里可以扩展：龙虎榜、涨停板、换手率等
            # MVP 先返回基础数据
            return {
                "turnover_rate": 0,
                "limit_up_count": 0,
                "limit_down_count": 0,
                "dragon_tiger_list": [],
            }
            
        except Exception as e:
            logger.error(f"获取情绪数据失败：{market}, 错误：{e}")
            return {}
