"""
情绪分析师 Agent

职责：市场情绪分析（恐贪指数、VIX、舆情分析、换手率）
数据源：AkShare、Finnhub、Web 搜索
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd

from .base_agent import BaseAgent
from ..data.service import DataService


class SentimentAnalystAgent(BaseAgent):
    """情绪分析师 Agent"""
    
    def __init__(self, model: str = "deepseek-v4"):
        super().__init__(model=model)
        self.data_service: Optional[DataService] = None
    
    def set_data_service(self, data_service: DataService):
        """设置数据服务"""
        self.data_service = data_service
    
    async def analyze(self, market: str = "A 股", **kwargs) -> Dict[str, Any]:
        """
        市场情绪分析
        
        Args:
            market: 市场类型
            **kwargs: 其他参数
            
        Returns:
            情绪分析结果
        """
        if not self.data_service:
            logger.warning("数据服务未设置，使用 mock 数据")
            return self._mock_analysis(market)
        
        try:
            # 并行获取多个情绪指标
            sentiment_data = await self.data_service.get_sentiment(market)
            market_data = await self.data_service.get_market_data("000001.SH", market)
            
            # 计算各项指标
            fear_greed = self._calculate_fear_greed(sentiment_data)
            vix = sentiment_data.get("vix", 18)
            turnover = self._calculate_turnover(market_data)
            
            # 综合评分
            score = self._calculate_score(fear_greed, vix, turnover)
            
            result = {
                "agent": "sentiment_analyst",
                "market": market,
                "fear_greed": fear_greed,
                "vix": vix,
                "turnover": turnover,
                "summary": self._generate_summary(fear_greed, vix, turnover),
                "score": score,
                "signals": self._generate_signals(fear_greed, vix, turnover),
                "contrarian_signal": self._contrarian_signal(fear_greed),
                "timestamp": pd.Timestamp.now().isoformat(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"情绪分析失败：{e}")
            return self._mock_analysis(market)
    
    def _calculate_fear_greed(self, data: Dict) -> Dict[str, Any]:
        """计算恐贪指数"""
        # 简化计算
        score = data.get("fear_greed_index", 45)
        
        if score >= 75:
            label = "极度贪婪"
            color = "red"
        elif score >= 60:
            label = "贪婪"
            color = "orange"
        elif score >= 45:
            label = "中性"
            color = "yellow"
        elif score >= 25:
            label = "恐惧"
            color = "lightgreen"
        else:
            label = "极度恐惧"
            color = "green"
        
        return {
            "score": score,
            "label": label,
            "color": color,
        }
    
    def _calculate_turnover(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """计算换手率"""
        if market_data.empty:
            return {
                "rate": 1.2,  # %
                "status": "偏低",
                "comparison": "低于历史均值",
            }
        
        # 简化计算
        return {
            "rate": 1.5,
            "status": "偏低",
            "comparison": "市场参与度不高",
        }
    
    def _calculate_score(self, fear_greed: Dict, vix: float, turnover: Dict) -> float:
        """计算情绪评分"""
        score = 6.0  # 基准分
        
        # 恐贪指数调整（恐惧时加分，贪婪时减分）
        fg_score = fear_greed.get("score", 50)
        if fg_score < 30:
            score += 1.0  # 极度恐惧，反向做多信号
        elif fg_score < 45:
            score += 0.5  # 恐惧
        elif fg_score > 70:
            score -= 1.0  # 极度贪婪，风险信号
        
        # VIX 调整
        if vix < 15:
            score += 0.5  # 低波动，市场乐观
        elif vix > 25:
            score -= 0.5  # 高波动，市场紧张
        
        # 换手率调整
        if turnover.get("status") == "偏低":
            score += 0.3  # 低换手，非过热信号
        
        return min(10.0, max(4.0, score))
    
    def _generate_summary(self, fear_greed: Dict, vix: float, turnover: Dict) -> str:
        """生成摘要"""
        parts = []
        
        # 恐贪
        parts.append(f"恐贪指数 {fear_greed.get('score', 0)}（{fear_greed.get('label', '中性')}）")
        
        # VIX
        if vix:
            parts.append(f"VIX {vix}")
        
        # 换手率
        if turnover.get("status"):
            parts.append(f"换手率{turnover.get('status')}")
        
        return "，".join(parts)
    
    def _generate_signals(self, fear_greed: Dict, vix: float, turnover: Dict) -> List[str]:
        """生成信号"""
        signals = []
        fg_score = fear_greed.get("score", 50)
        
        # 恐贪信号
        if fg_score < 30:
            signals.append("反向做多信号：市场极度恐惧")
        elif fg_score < 45:
            signals.append("潜在机会：市场偏恐惧")
        elif fg_score > 70:
            signals.append("风险警示：市场极度贪婪")
        
        # VIX 信号
        if vix and vix > 30:
            signals.append("波动率飙升：市场恐慌")
        elif vix and vix < 15:
            signals.append("低波动环境：市场平静")
        
        # 换手率信号
        if turnover.get("status") == "偏低":
            signals.append("市场参与度低，非过热信号")
        elif turnover.get("status") == "偏高":
            signals.append("换手率升高，关注短期波动")
        
        return signals
    
    def _contrarian_signal(self, fear_greed: Dict) -> str:
        """反向交易信号"""
        score = fear_greed.get("score", 50)
        
        if score < 25:
            return "强烈买入信号：市场极度恐惧，通常是底部"
        elif score < 40:
            return "买入信号：市场恐惧，可能是买入机会"
        elif score > 75:
            return "卖出信号：市场极度贪婪，可能接近顶部"
        elif score > 60:
            return "谨慎信号：市场贪婪，考虑获利了结"
        else:
            return "中性信号：等待明确方向"
    
    def _mock_analysis(self, market: str) -> Dict[str, Any]:
        """返回 mock 分析结果"""
        return {
            "agent": "sentiment_analyst",
            "market": market,
            "fear_greed": {
                "score": 45,
                "label": "中性",
                "color": "yellow",
            },
            "vix": 18.5,
            "turnover": {
                "rate": 1.2,
                "status": "偏低",
                "comparison": "低于历史均值",
            },
            "summary": "恐贪指数 45（中性），VIX 18.5，换手率偏低",
            "score": 6.0,
            "signals": [
                "市场参与度低，非过热信号",
            ],
            "contrarian_signal": "中性信号：等待明确方向",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def analyze_sector_sentiment(self, sector: str = "科技") -> Dict[str, Any]:
        """分析板块情绪
        
        Args:
            sector: 板块名称
            
        Returns:
            板块情绪分析
        """
        # TODO: 实现板块情绪分析
        return {
            "agent": "sentiment_analyst",
            "type": "sector_sentiment",
            "sector": sector,
            "hot_index": 65,  # 热度指数 0-100
            "status": "偏热",
            "recommendation": "注意短期风险",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def get_sentiment_news(self, keyword: str = "A股") -> List[Dict[str, Any]]:
        """获取舆情新闻
        
        Args:
            keyword: 关键词
            
        Returns:
            新闻列表
        """
        # TODO: 实现舆情新闻获取
        return [
            {
                "title": "某机构看好A股后市",
                "sentiment": "positive",
                "source": "财经媒体",
                "time": "2小时前",
            },
            {
                "title": "市场资金面趋紧",
                "sentiment": "negative",
                "source": "券商研报",
                "time": "5小时前",
            },
        ]
