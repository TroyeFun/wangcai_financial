"""
风控经理 Agent

职责：风险管理（VaR 计算、最大回撤、仓位建议、相关性分析）
整合其他 Agent 的数据，给出综合风控建议
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd

from .base_agent import BaseAgent


class RiskManagerAgent(BaseAgent):
    """风控经理 Agent"""
    
    def __init__(self, model: str = "deepseek-v4"):
        super().__init__(model=model)
    
    async def analyze(self, 
                     macro_score: float = 7.0,
                     valuation_score: float = 7.5,
                     fund_score: float = 6.5,
                     sentiment_score: float = 6.0,
                     **kwargs) -> Dict[str, Any]:
        """
        综合风控分析
        
        Args:
            macro_score: 宏观评分
            valuation_score: 估值评分
            fund_score: 资金评分
            sentiment_score: 情绪评分
            
        Returns:
            风控分析结果
        """
        # 四维权重（根据设计文档）
        weights = {
            "macro": 0.40,      # 基本面
            "valuation": 0.40,  # 估值
            "fund": 0.10,       # 资金
            "sentiment": 0.10,  # 情绪
        }
        
        # 计算综合评分
        composite_score = (
            macro_score * weights["macro"] +
            valuation_score * weights["valuation"] +
            fund_score * weights["fund"] +
            sentiment_score * weights["sentiment"]
        )
        
        # 计算仓位建议
        position = self._calculate_position(composite_score)
        
        # 风险评估
        risk_level = self._assess_risk(composite_score)
        
        # 生成建议
        suggestions = self._generate_suggestions(
            composite_score, position, risk_level,
            macro_score, valuation_score, fund_score, sentiment_score
        )
        
        # 生成警告
        warnings = self._generate_warnings(
            composite_score, sentiment_score
        )
        
        result = {
            "agent": "risk_manager",
            "composite_score": round(composite_score, 1),
            "position_recommendation": position,
            "risk_level": risk_level,
            "weights": weights,
            "suggestions": suggestions,
            "warnings": warnings,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
        
        return result
    
    def _calculate_position(self, composite_score: float) -> Dict[str, Any]:
        """计算仓位建议"""
        if composite_score >= 8.0:
            return {
                "level": "重仓",
                "percentage": "70-80%",
                "description": "强烈看多，可适当加仓",
            }
        elif composite_score >= 7.0:
            return {
                "level": "标准仓位",
                "percentage": "60-70%",
                "description": "积极看多，保持标准仓位",
            }
        elif composite_score >= 6.0:
            return {
                "level": "轻仓",
                "percentage": "40-50%",
                "description": "中性偏多，控制仓位",
            }
        elif composite_score >= 5.0:
            return {
                "level": "观望",
                "percentage": "20-30%",
                "description": "中性，等待机会",
            }
        else:
            return {
                "level": "清仓",
                "percentage": "0-10%",
                "description": "谨慎，减仓或清仓",
            }
    
    def _assess_risk(self, composite_score: float) -> Dict[str, Any]:
        """评估风险等级"""
        if composite_score >= 7.5:
            return {
                "level": "低风险",
                "value": 1,
                "description": "市场环境良好，风险可控",
            }
        elif composite_score >= 6.0:
            return {
                "level": "中等风险",
                "value": 2,
                "description": "市场中性，保持警惕",
            }
        elif composite_score >= 5.0:
            return {
                "level": "较高风险",
                "value": 3,
                "description": "市场偏弱，控制仓位",
            }
        else:
            return {
                "level": "高风险",
                "value": 4,
                "description": "市场走弱，建议减仓",
            }
    
    def _generate_suggestions(self, 
                              composite_score: float,
                              position: Dict,
                              risk_level: Dict,
                              macro_score: float,
                              valuation_score: float,
                              fund_score: float,
                              sentiment_score: float) -> List[str]:
        """生成建议"""
        suggestions = []
        
        # 仓位建议
        suggestions.append(f"建议仓位：{position['percentage']}（{position['level']}）")
        
        # 各维度建议
        if valuation_score < 6:
            suggestions.append("估值偏高，关注估值修复风险")
        
        if sentiment_score < 5:
            suggestions.append("市场情绪偏弱，注意短期波动")
        
        if fund_score < 6:
            suggestions.append("资金面偏弱，跟踪北向资金动向")
        
        # 具体板块建议
        if composite_score >= 7:
            suggestions.append("重点关注：科技 + 消费板块")
        elif composite_score >= 6:
            suggestions.append("重点关注：低估值防御性板块")
        
        # 策略建议
        if composite_score >= 7:
            suggestions.append("策略：分批建仓，减少择时风险")
        else:
            suggestions.append("策略：观望为主，等待明确信号")
        
        return suggestions
    
    def _generate_warnings(self, composite_score: float, sentiment_score: float) -> List[str]:
        """生成警告"""
        warnings = []
        
        if sentiment_score > 75:
            warnings.append("⚠️ 警告：市场情绪过热，可能接近短期顶部")
        
        if sentiment_score < 25:
            warnings.append("⚠️ 警告：市场情绪极度恐慌，可能存在机会")
        
        if composite_score < 5:
            warnings.append("⚠️ 警告：综合评分偏低，控制风险为主")
        
        # 其他风险提示
        warnings.append("⚠️ 关注：美联储议息会议，可能引发全球波动")
        warnings.append("⚠️ 关注：地缘政治风险，可能影响市场")
        
        return warnings
    
    async def calculate_var(self, 
                            portfolio_value: float = 1000000,
                            confidence: float = 0.95,
                            period: int = 1) -> Dict[str, Any]:
        """
        计算 VaR（Value at Risk）
        
        Args:
            portfolio_value: 组合价值
            confidence: 置信度
            period: 持有期（天）
            
        Returns:
            VaR 结果
        """
        # 简化计算（假设日波动率 2%）
        daily_volatility = 0.02
        
        # Z-score for 95% confidence
        z_score = 1.645
        
        # Calculate VaR
        var = portfolio_value * daily_volatility * z_score * (period ** 0.5)
        
        return {
            "agent": "risk_manager",
            "type": "var_calculation",
            "portfolio_value": portfolio_value,
            "confidence": confidence,
            "period_days": period,
            "var_absolute": round(var, 2),
            "var_percentage": round(var / portfolio_value * 100, 2),
            "interpretation": f"在 {confidence*100}% 置信度下，{period} 天内最大损失约为 {var/10000:.1f} 万元",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def analyze_drawdown(self,
                               current_value: float = 1000000,
                               peak_value: float = 1100000) -> Dict[str, Any]:
        """
        分析最大回撤
        
        Args:
            current_value: 当前价值
            peak_value: 历史最高价值
            
        Returns:
            回撤分析结果
        """
        drawdown = (peak_value - current_value) / peak_value * 100
        
        if drawdown < 5:
            status = "正常回撤"
        elif drawdown < 10:
            status = "中等回撤"
        elif drawdown < 20:
            status = "较大回撤"
        else:
            status = "严重回撤"
        
        return {
            "agent": "risk_manager",
            "type": "drawdown_analysis",
            "current_value": current_value,
            "peak_value": peak_value,
            "drawdown_percentage": round(drawdown, 2),
            "status": status,
            "recommendation": "适当止损或定投摊薄成本" if drawdown > 5 else "继续持有",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    async def correlation_analysis(self,
                                   assets: List[str] = None) -> Dict[str, Any]:
        """
        相关性分析
        
        Args:
            assets: 资产列表
            
        Returns:
            相关性矩阵
        """
        if assets is None:
            assets = ["沪深300", "创业板", "纳斯达克", "黄金", "债券"]
        
        # Mock 相关性矩阵
        correlations = {
            "沪深300": {"创业板": 0.85, "纳斯达克": 0.45, "黄金": -0.10, "债券": 0.20},
            "创业板": {"沪深300": 0.85, "纳斯达克": 0.50, "黄金": -0.05, "债券": 0.10},
            "纳斯达克": {"沪深300": 0.45, "创业板": 0.50, "黄金": 0.15, "债券": -0.20},
            "黄金": {"沪深300": -0.10, "创业板": -0.05, "纳斯达克": 0.15, "债券": 0.30},
            "债券": {"沪深300": 0.20, "创业板": 0.10, "纳斯达克": -0.20, "黄金": 0.30},
        }
        
        return {
            "agent": "risk_manager",
            "type": "correlation_analysis",
            "assets": assets,
            "correlations": correlations,
            "recommendation": "建议股债配置，降低组合波动",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
