from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any


class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    RATE_LIMIT: float = 1.0  # 秒/请求
    
    @abstractmethod
    async def get_macro_data(self, indicator: str, country: str) -> pd.DataFrame:
        """获取宏观经济数据
        
        Args:
            indicator: 指标名称（GDP/CPI/PMI 等）
            country: 国家/地区（CN/US 等）
            
        Returns:
            DataFrame 包含历史数据
        """
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str, period: str) -> pd.DataFrame:
        """获取行情数据
        
        Args:
            symbol: 标的代码（如 000001.SH, AAPL 等）
            period: 周期（1d/1w/1m 等）
            
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        pass
    
    @abstractmethod
    async def get_fund_flow(self, market: str) -> pd.DataFrame:
        """获取资金流向数据
        
        Args:
            market: 市场（A 股/港股/美股等）
            
        Returns:
            DataFrame 包含资金流向数据
        """
        pass
    
    async def get_valuation_data(self, symbol: str) -> Dict[str, Any]:
        """获取估值数据
        
        Args:
            symbol: 标的代码
            
        Returns:
            字典包含 PE/PB/PS 等估值指标
        """
        raise NotImplementedError
    
    async def get_sentiment_data(self, market: str) -> Dict[str, Any]:
        """获取情绪数据
        
        Args:
            market: 市场
            
        Returns:
            字典包含情绪指标
        """
        raise NotImplementedError
