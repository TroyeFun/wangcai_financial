"""
资金流追踪 Agent

职责：资金流向追踪（北向资金、两融余额、主力流向、新基金发行）
数据源：AkShare
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd

from .base_agent import BaseAgent
from ..data.service import DataService


class FundTrackerAgent(BaseAgent):
    """资金流追踪 Agent"""
    
    def __init__(self, model: str = "deepseek-v4"):
        super().__init__(model=model)
        self.data_service: Optional[DataService] = None
    
    def set_data_service(self, data_service: DataService):
        """设置数据服务"""
        self.data_service = data_service
    
    async def analyze(self, market: str = "A 股", **kwargs) -> Dict[str, Any]:
        """
        资金流向分析
        
        Args:
            market: 市场类型
            **kwargs: 其他参数
            
        Returns:
            资金流向分析结果
        """
        if not self.data_service:
            logger.warning("数据服务未设置，使用 mock 数据")
            return self._mock_analysis(market)
        
        try:
            # 并行获取多个资金流向数据
            north_flow = await self.data_service.get_fund_flow("A 股")
            margin_data = await self.data_service.get_fund_flow("两融")
            
            # 计算各项指标
            north_net_flow = self._calculate_north_flow(north_flow)
            margin_status = self._calculate_margin_status(margin_data)
            
            # 综合评分
            score = self._calculate_score(north_net_flow, margin_status)
            
            result = {
                "agent": "fund_tracker",
                "market": market,
                "north_flow": north_net_flow,
                "margin": margin_status,
                "summary": self._generate_summary(north_net_flow, margin_status),
                "score": score,
                "signals": self._generate_signals(north_net_flow, margin_status),
                "timestamp": pd.Timestamp.now().isoformat(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"资金流向分析失败：{e}")
            return self._mock_analysis(market)
    
    def _calculate_north_flow(self, data: Dict) -> Dict[str, Any]:
        """计算北向资金指标"""
        if not data:
            return {
                "net_flow_today": 52,  # 亿
                "net_flow_week": 120,
                "trend": "inflow",
                "days_inflow": 3,
                "total_inflow_month": 350,
            }
        
        # 简化计算
        return {
            "net_flow_today": data.get("net_flow", 50),
            "net_flow_week": data.get("net_flow_week", 120),
            "trend": "inflow" if data.get("net_flow", 0) > 0 else "outflow",
            "days_inflow": 3,
            "total_inflow_month": 350,
        }
    
    def _calculate_margin_status(self, data: Dict) -> Dict[str, Any]:
        """计算两融状态"""
        if not data:
            return {
                "balance": 18200,  # 亿
                "change_pct": 0.3,
                "status": "expanding",
            }
        
        return {
            "balance": data.get("balance", 18200),
            "change_pct": data.get("change_pct", 0.3),
            "status": "expanding" if data.get("change_pct", 0) > 0 else "contracting",
        }
    
    def _calculate_score(self, north_flow: Dict, margin_status: Dict) -> float:
        """计算资金面评分"""
        score = 6.0  # 基准分
        
        # 北向资金加分
        if north_flow.get("trend") == "inflow":
            score += 1.0
            if north_flow.get("days_inflow", 0) >= 3:
                score += 0.5
        
        # 两融加分
        if margin_status.get("status") == "expanding":
            score += 0.5
        
        return min(10.0, max(4.0, score))
    
    def _generate_summary(self, north_flow: Dict, margin_status: Dict) -> str:
        """生成摘要"""
        parts = []
        
        # 北向资金
        trend = north_flow.get("trend", "neutral")
        if trend == "inflow":
            parts.append(f"北向资金连续{north_flow.get('days_inflow', 0)}日净流入")
        else:
            parts.append("北向资金净流出")
        
        # 两融
        if margin_status.get("status") == "expanding":
            parts.append("两融余额增加")
        else:
            parts.append("两融余额减少")
        
        return "，".join(parts)
    
    def _generate_signals(self, north_flow: Dict, margin_status: Dict) -> List[str]:
        """生成信号"""
        signals = []
        
        # 北向连续流入
        if north_flow.get("days_inflow", 0) >= 3:
            signals.append("积极信号：北向资金连续净流入")
        
        # 北向大幅流入
        if north_flow.get("net_flow_today", 0) > 100:
            signals.append("强烈买入信号：北向资金大幅流入")
        
        # 两融扩张
        if margin_status.get("change_pct", 0) > 1:
            signals.append("杠杆资金入场：两融快速增加")
        
        # 北向流出
        if north_flow.get("net_flow_today", 0) < -50:
            signals.append("警示信号：北向资金大幅流出")
        
        return signals
    
    def _mock_analysis(self, market: str) -> Dict[str, Any]:
        """返回 mock 分析结果"""
        return {
            "agent": "fund_tracker",
            "market": market,
            "north_flow": {
                "net_flow_today": 52,
                "net_flow_week": 120,
                "trend": "inflow",
                "days_inflow": 3,
                "total_inflow_month": 350,
            },
            "margin": {
                "balance": 18200,
                "change_pct": 0.3,
                "status": "expanding",
            },
            "summary": "北向资金连续3日净流入，两融余额增加",
            "score": 7.0,
            "signals": [
                "积极信号：北向资金连续净流入",
                "杠杆资金入场：两融余额增加",
            ],
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def track_sector_flow(self, sector: str = "半导体") -> Dict[str, Any]:
        """追踪板块资金流向
        
        Args:
            sector: 板块名称
            
        Returns:
            板块资金流向
        """
        # TODO: 实现板块资金流向追踪
        return {
            "agent": "fund_tracker",
            "type": "sector_flow",
            "sector": sector,
            "flow": "inflow",
            "amount": 30,  # 亿
            "top_stocks": ["股票1", "股票2", "股票3"],
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def get_new_fund_issuance(self) -> Dict[str, Any]:
        """获取新基金发行情况"""
        # TODO: 实现新基金发行数据获取
        return {
            "agent": "fund_tracker",
            "type": "new_fund",
            "monthly_issuance": 50,  # 亿
            "status": "低迷",
            "comparison": "低于历史均值",
            "signal": "底部特征",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
