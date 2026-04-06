"""
宏观分析师 Agent

职责：宏观经济分析（GDP/CPI/PMI、利率汇率、政策解读）
数据源：AkShare（中国）、Finnhub（美国）
"""

from typing import Dict, Any
from loguru import logger

from .base_agent import BaseAgent


class MacroAnalystAgent(BaseAgent):
    """宏观分析师 Agent"""
    
    def __init__(self, model: str = "deepseek-v4"):
        super().__init__(model=model)
    
    async def analyze(self, country: str = "CN", indicators: list = None) -> Dict[str, Any]:
        """
        宏观经济分析
        
        Args:
            country: 国家/地区（CN/US）
            indicators: 指标列表（GDP/CPI/PMI 等）
            
        Returns:
            分析结果字典
        """
        # TODO: 从数据层获取实际数据
        # MVP 先返回示例结构
        mock_data = {
            "country": country,
            "indicators": indicators or ["GDP", "CPI", "PMI"],
            "data": {
                "GDP": {"value": 5.2, "yoy": 0.3, "trend": "stable"},
                "CPI": {"value": 1.8, "yoy": -0.2, "trend": "down"},
                "PMI": {"value": 51.2, "yoy": 0.5, "trend": "up"},
            },
            "summary": "宏观经济整体稳定，PMI 连续处于扩张区间，CPI 温和",
            "score": 7.0,  # 宏观环境评分（0-10）
        }
        
        # 构建 ROLES Prompt
        system_prompt = """你是一位专业的宏观经济分析师，具有 CFA 三级持证人的分析能力。
所有结论必须有数据支撑，使用"数据显示..."而非"我认为..."。"""
        
        evidence_str = "\n".join([f"- {k}: {v}" for k, v in mock_data["data"].items()])
        prompt = self._build_roles_prompt(
            role="宏观经济分析师",
            objective=f"分析{country}当前宏观环境",
            limits="只使用提供的数据，不编造数值",
            evidence=evidence_str,
            safeguards="给出置信度评估，标注数据来源和时间"
        )
        
        # 调用 LLM 生成分析
        # analysis_text = self._call_llm(prompt, system_prompt)
        analysis_text = mock_data["summary"]  # MVP 先用 mock
        
        return {
            "agent": "macro_analyst",
            "country": country,
            "score": mock_data["score"],
            "data": mock_data["data"],
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat(),
        }
