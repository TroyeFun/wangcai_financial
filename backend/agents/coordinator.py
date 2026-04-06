"""
多 Agent 协调器

负责协调多个 Agent 协同工作，处理复杂分析任务
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from agents import (
    MacroAnalystAgent,
    ValuationAnalystAgent,
    FundTrackerAgent,
    SentimentAnalystAgent,
    RiskManagerAgent,
)
from config.settings import settings


class AgentCoordinator:
    """多 Agent 协调器"""
    
    def __init__(self):
        # 初始化所有 Agent
        self.agents = {
            "macro": MacroAnalystAgent(model=settings.CHINA_MODEL),
            "valuation": ValuationAnalystAgent(model=settings.CHINA_MODEL),
            "fund": FundTrackerAgent(model=settings.CHINA_MODEL),
            "sentiment": SentimentAnalystAgent(model=settings.CHINA_MODEL),
            "risk": RiskManagerAgent(model=settings.CHINA_MODEL),
        }
        
        logger.info("Agent 协调器初始化完成")
    
    async def comprehensive_analysis(self, target: str = "A 股", market: str = "A 股") -> Dict[str, Any]:
        """
        四维综合分析
        
        并行调用所有 Agent，然后由风控 Manager 汇总
        """
        logger.info(f"开始四维综合分析：{target}")
        
        # 并行执行所有 Agent
        tasks = {
            "macro": self.agents["macro"].analyze(country="CN"),
            "valuation": self.agents["valuation"].analyze(symbol="000300.SH", market=market),
            "fund": self.agents["fund"].analyze(market=market),
            "sentiment": self.agents["sentiment"].analyze(market=market),
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 整理结果
        analysis_results = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Agent {key} 执行失败：{result}")
                analysis_results[key] = {"error": str(result)}
            else:
                analysis_results[key] = result
        
        # 调用风控 Manager 汇总
        scores = self._extract_scores(analysis_results)
        risk_result = await self.agents["risk"].analyze(**scores)
        analysis_results["risk"] = risk_result
        
        # 计算综合评分
        composite_score = sum(scores.values()) / len(scores)
        
        return {
            "target": target,
            "market": market,
            "analysis_results": analysis_results,
            "scores": scores,
            "composite_score": composite_score,
            "recommendation": self._generate_recommendation(composite_score, analysis_results),
        }
    
    async def quick_analysis(self, query: str, market: str = "A 股") -> Dict[str, Any]:
        """
        快速分析
        
        根据问题类型选择性调用 Agent
        """
        # 识别问题类型
        query_type = self._classify_query(query)
        
        logger.info(f"快速分析 - 类型：{query_type}")
        
        # 根据类型选择 Agent
        agent_map = {
            "macro": ["macro"],
            "valuation": ["valuation"],
            "fund": ["fund"],
            "sentiment": ["sentiment"],
            "all": ["macro", "valuation", "fund", "sentiment", "risk"],
            "risk": ["macro", "valuation", "fund", "sentiment", "risk"],
        }
        
        selected_agents = agent_map.get(query_type, ["macro"])
        
        # 执行选中的 Agent
        tasks = []
        for agent_key in selected_agents:
            if agent_key == "macro":
                tasks.append(self.agents["macro"].analyze(country="CN"))
            elif agent_key == "valuation":
                tasks.append(self.agents["valuation"].analyze(symbol="000300.SH", market=market))
            elif agent_key == "fund":
                tasks.append(self.agents["fund"].analyze(market=market))
            elif agent_key == "sentiment":
                tasks.append(self.agents["sentiment"].analyze(market=market))
            elif agent_key == "risk":
                # 需要先获取其他评分
                pass
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "query": query,
            "query_type": query_type,
            "results": results,
        }
    
    def _classify_query(self, query: str) -> str:
        """分类问题类型"""
        query_lower = query.lower()
        
        # 关键词匹配
        if any(kw in query_lower for kw in ["宏观", "经济", "gdp", "cpi", "pmi", "利率"]):
            return "macro"
        
        if any(kw in query_lower for kw in ["估值", "pe", "pb", "贵", "便宜", "分位"]):
            return "valuation"
        
        if any(kw in query_lower for kw in ["资金", "北向", "两融", "流入", "流出"]):
            return "fund"
        
        if any(kw in query_lower for kw in ["情绪", "恐慌", "贪婪", "vix"]):
            return "sentiment"
        
        if any(kw in query_lower for kw in ["风险", "回撤", "仓位", "止损"]):
            return "risk"
        
        # 默认四维分析
        if any(kw in query_lower for kw in ["适合买", "适合卖", "全面", "分析", "现在"]):
            return "all"
        
        return "macro"
    
    def _extract_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        """提取评分"""
        scores = {
            "macro_score": 7.0,
            "valuation_score": 7.0,
            "fund_score": 6.5,
            "sentiment_score": 6.0,
        }
        
        if "macro" in results and isinstance(results["macro"], dict):
            scores["macro_score"] = results["macro"].get("score", 7.0)
        
        if "valuation" in results and isinstance(results["valuation"], dict):
            scores["valuation_score"] = results["valuation"].get("score", 7.0)
        
        if "fund" in results and isinstance(results["fund"], dict):
            scores["fund_score"] = results["fund"].get("score", 6.5)
        
        if "sentiment" in results and isinstance(results["sentiment"], dict):
            scores["sentiment_score"] = results["sentiment"].get("score", 6.0)
        
        return scores
    
    def _generate_recommendation(self, composite_score: float, results: Dict) -> Dict[str, Any]:
        """生成投资建议"""
        if composite_score >= 8:
            level = "强烈看多"
            position = "70-80%"
            action = "可适当加仓，分批建仓"
        elif composite_score >= 7:
            level = "积极看多"
            position = "60-70%"
            action = "保持标准仓位，逢低加仓"
        elif composite_score >= 6:
            level = "中性偏多"
            position = "50-60%"
            action = "控制仓位，等待机会"
        elif composite_score >= 5:
            level = "中性"
            position = "30-40%"
            action = "观望为主，减少操作"
        else:
            level = "谨慎"
            position = "20%以下"
            action = "减仓或清仓，等待底部信号"
        
        return {
            "level": level,
            "position": position,
            "action": action,
            "composite_score": composite_score,
        }


# 全局协调器实例
agent_coordinator = AgentCoordinator()
