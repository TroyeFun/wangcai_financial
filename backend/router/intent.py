"""
对话路由层 - 意图识别

根据用户输入识别分析意图，分发到对应的 Agent
"""

import re
from typing import Optional, List, Dict
from loguru import logger


# 意图路由配置
INTENT_ROUTES = {
    "macro_analyst": [
        r"宏观", r"GDP", r"CPI", r"PMI", r"利率", r"降息", r"加息", r"政策", r"经济",
        r"通胀", r"失业", r"货币", r"央行", r"财政",
    ],
    "valuation_analyst": [
        r"估值", r"PE", r"PB", r"PS", r"DCF", r"DDM", r"贵不贵", r"便宜", 
        r"高估", r"低估", r"合理", r"分位", r"市盈率", r"市净率",
    ],
    "fund_tracker": [
        r"资金", r"北向", r"南向", r"两融", r"主力", r"流入", r"流出", 
        r"融资", r"融券", r"外资", r"内资",
    ],
    "sentiment_analyst": [
        r"情绪", r"恐慌", r"贪婪", r"VIX", r"舆情", r"散户", r"热度",
        r"恐贪", r"换手", r"成交量",
    ],
    "sector_analyst": [
        r"行业", r"板块", r"轮动", r"景气", r"产业链", r"赛道",
        r"半导体", r"新能源", r"消费", r"科技", r"金融",
    ],
    "risk_manager": [
        r"风险", r"回撤", r"仓位", r"对冲", r"止损", r"相关性",
        r"VaR", r"波动", r"夏普",
    ],
}

# 多维分析触发规则
MULTI_AGENT_TRIGGERS = [
    r"现在适合买", r"能不能买", r"该不该卖", r"适合入场",
    r"全面分析", r"综合判断", r"四维分析", r"整体怎么看",
]


def identify_intent(user_input: str) -> List[str]:
    """识别用户意图
    
    Args:
        user_input: 用户输入文本
        
    Returns:
        匹配的 Agent 列表
    """
    matched_agents = []
    
    # 检查是否触发多维分析
    for pattern in MULTI_AGENT_TRIGGERS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.info("触发多维分析意图")
            return ["macro_analyst", "valuation_analyst", "fund_tracker", 
                    "sentiment_analyst", "sector_analyst", "risk_manager"]
    
    # 单维度意图识别
    for agent, patterns in INTENT_ROUTES.items():
        for pattern in patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                if agent not in matched_agents:
                    matched_agents.append(agent)
                break
    
    if not matched_agents:
        logger.warning(f"未识别到明确意图：{user_input}")
        return ["macro_analyst"]  # 默认返回宏观分析
    
    logger.info(f"识别意图：{matched_agents}")
    return matched_agents


def extract_entities(user_input: str) -> Dict[str, str]:
    """从用户输入中提取实体（市场、标的等）
    
    Args:
        user_input: 用户输入文本
        
    Returns:
        实体字典
    """
    entities = {}
    
    # 市场识别
    if any(kw in user_input for kw in ["A 股", "沪深", "上证", "深证"]):
        entities["market"] = "A 股"
    elif any(kw in user_input for kw in ["港股", "恒生", "国企指数"]):
        entities["market"] = "港股"
    elif any(kw in user_input for kw in ["美股", "纳指", "标普", "道指"]):
        entities["market"] = "美股"
    elif any(kw in user_input for kw in ["BTC", "比特币", "加密"]):
        entities["market"] = "加密货币"
    
    # 具体标的识别（简化版）
    # 可以扩展：正则匹配股票代码、指数名称等
    
    return entities
