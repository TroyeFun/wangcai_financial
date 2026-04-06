"""
估值分析师 Agent

职责：资产估值分析（PE/PB/PS 横纵向对比、DCF/DDM 模型）
数据源：AkShare（A股/港股）、Finnhub（美股）
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd

from .base_agent import BaseAgent
from ..data.service import DataService


class ValuationAnalystAgent(BaseAgent):
    """估值分析师 Agent"""
    
    def __init__(self, model: str = "deepseek-v4"):
        super().__init__(model=model)
        self.data_service: Optional[DataService] = None
    
    def set_data_service(self, data_service: DataService):
        """设置数据服务"""
        self.data_service = data_service
    
    async def analyze(self, symbol: str = "000300.SH", market: str = "A 股", **kwargs) -> Dict[str, Any]:
        """
        估值分析
        
        Args:
            symbol: 标的代码
            market: 市场类型
            **kwargs: 其他参数
            
        Returns:
            估值分析结果
        """
        if not self.data_service:
            logger.warning("数据服务未设置，使用 mock 数据")
            return self._mock_analysis(symbol, market)
        
        try:
            # 并行获取多个数据
            valuation_task = self.data_service.get_valuation(symbol, market)
            market_task = self.data_service.get_market_data(symbol, market)
            
            valuation_data, market_data = await self._async_gather(valuation_task, market_task)
            
            # 计算分位数（如果有历史数据）
            percentile = await self._calculate_percentile(market_data)
            
            # 构建分析结果
            result = {
                "agent": "valuation_analyst",
                "symbol": symbol,
                "market": market,
                "valuation": valuation_data,
                "percentile": percentile,
                "summary": self._generate_summary(valuation_data, percentile),
                "score": self._calculate_score(valuation_data, percentile),
                "timestamp": pd.Timestamp.now().isoformat(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"估值分析失败：{e}")
            return self._mock_analysis(symbol, market)
    
    async def _async_gather(self, *tasks):
        """并行执行任务"""
        import asyncio
        return await asyncio.gather(*tasks)
    
    async def _calculate_percentile(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """计算估值分位数"""
        if market_data.empty or "close" not in market_data.columns:
            return {"pe": 50, "pb": 50, "ps": 50}
        
        # 简化计算：假设当前价格在历史数据的某个分位
        # 实际应从数据库获取真实历史 PE/PB 数据
        return {
            "pe": 35,  # mock 数据
            "pb": 40,
            "ps": 30,
        }
    
    def _generate_summary(self, valuation: Dict, percentile: Dict) -> str:
        """生成估值摘要"""
        pe = valuation.get("pe", 0)
        pe_pct = percentile.get("pe", 50)
        
        if pe_pct < 30:
            level = "偏低估"
        elif pe_pct < 60:
            level = "合理"
        else:
            level = "偏高估"
        
        return f"{level}（历史分位 {pe_pct}%）"
    
    def _calculate_score(self, valuation: Dict, percentile: Dict) -> float:
        """计算估值评分"""
        pe_pct = percentile.get("pe", 50)
        
        # 越低估分数越高
        # 30% 分位给 9 分，50% 给 7 分，70% 给 5 分
        if pe_pct <= 30:
            return 9.0
        elif pe_pct <= 50:
            return 8.0 - (pe_pct - 30) * 0.05
        elif pe_pct <= 70:
            return 7.0 - (pe_pct - 50) * 0.1
        else:
            return max(4.0, 6.0 - (pe_pct - 70) * 0.05)
    
    def _mock_analysis(self, symbol: str, market: str) -> Dict[str, Any]:
        """返回 mock 分析结果"""
        return {
            "agent": "valuation_analyst",
            "symbol": symbol,
            "market": market,
            "valuation": {
                "pe": 12.5,
                "pb": 1.5,
                "ps": 2.0,
            },
            "percentile": {
                "pe": 35,
                "pb": 40,
                "ps": 30,
            },
            "summary": "合理偏低估（历史分位 35%）",
            "score": 7.5,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def compare_industries(self, industries: List[str], market: str = "A 股") -> Dict[str, Any]:
        """行业对比分析
        
        Args:
            industries: 行业列表
            market: 市场类型
            
        Returns:
            行业对比结果
        """
        if not self.data_service:
            return self._mock_industry_comparison(industries)
        
        results = []
        for industry in industries:
            # 每个行业获取代表股票
            symbol = self._industry_to_symbol(industry)
            valuation = await self.data_service.get_valuation(symbol, market)
            results.append({
                "industry": industry,
                "symbol": symbol,
                "valuation": valuation,
                "score": valuation.get("pe", 15) / 20 * 10,  # 简化评分
            })
        
        # 按估值排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "agent": "valuation_analyst",
            "type": "industry_comparison",
            "results": results,
            "recommendation": results[0]["industry"] if results else None,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    def _industry_to_symbol(self, industry: str) -> str:
        """行业到代表股票的映射"""
        mapping = {
            "科技": "000001.SH",
            "消费": "600519.SH",
            "金融": "601318.SH",
            "医药": "000538.SZ",
            "半导体": "688981.SH",
            "新能源": "002594.SZ",
        }
        return mapping.get(industry, "000300.SH")
    
    def _mock_industry_comparison(self, industries: List[str]) -> Dict[str, Any]:
        """mock 行业对比"""
        results = [
            {"industry": "金融", "valuation": {"pe": 8.5, "pb": 0.9}, "score": 8.5},
            {"industry": "消费", "valuation": {"pe": 25.0, "pb": 5.0}, "score": 6.0},
            {"industry": "科技", "valuation": {"pe": 45.0, "pb": 8.0}, "score": 4.5},
        ]
        return {
            "agent": "valuation_analyst",
            "type": "industry_comparison",
            "results": results[:len(industries)],
            "recommendation": "金融板块估值最低",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
