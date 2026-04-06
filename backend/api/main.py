"""
FastAPI 主应用入口 - 完整版

集成所有功能：
- 多 Agent 协同分析
- 个性化配置
- 历史分析记录
- 向量检索
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Dict, Any, List, Optional
import asyncio

from config.settings import settings
from router.intent import identify_intent, extract_entities
from agents import (
    MacroAnalystAgent,
    ValuationAnalystAgent,
    FundTrackerAgent,
    SentimentAnalystAgent,
    RiskManagerAgent,
)
from agents.coordinator import AgentCoordinator
from data import DataService, CacheManager
from services import preferences_manager, analysis_memory


# 初始化应用
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务
data_service: DataService = None
agent_coordinator: AgentCoordinator = None


@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logger.info(f"应用启动：{settings.APP_NAME}")
    logger.info(f"版本：1.0.0")
    logger.info(f"环境：{settings.APP_ENV}")
    
    # 初始化数据服务
    global data_service, agent_coordinator
    cache_manager = CacheManager(settings.REDIS_URL)
    data_service = DataService(
        cache_manager,
        api_keys={
            "finnhub": settings.FINNHUB_API_KEY or "",
            "coingecko": settings.COINGECKO_API_KEY or "",
        }
    )
    
    # 初始化 Agent 协调器
    agent_coordinator = AgentCoordinator()
    
    logger.info("所有服务初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    logger.info("应用关闭")


# ========== 基础接口 ==========

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "phase": "Phase 3 完成",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "data": data_service is not None,
            "coordinator": agent_coordinator is not None,
            "memory": analysis_memory is not None,
        }
    }


# ========== 分析接口 ==========

@app.post("/api/analyze")
async def analyze(
    query: str,
    user_id: str = Query(default="default", description="用户 ID"),
    save: bool = Query(default=True, description="是否保存到历史"),
) -> Dict[str, Any]:
    """
    分析接口
    
    Args:
        query: 用户查询文本
        user_id: 用户 ID（用于个性化配置）
        save: 是否保存到历史记录
        
    Returns:
        分析结果
    """
    try:
        # 意图识别
        intents = identify_intent(query)
        entities = extract_entities(query)
        
        logger.info(f"查询：{query}, 意图：{intents}")
        
        # 检查是否是综合分析
        if len(intents) >= 3 or "全面" in query or "适合买" in query:
            # 使用协调器进行综合分析
            result = await agent_coordinator.comprehensive_analysis(
                target=entities.get("market", "A 股"),
                market=entities.get("market", "A 股"),
            )
        else:
            # 使用单个 Agent
            result = await _single_agent_analysis(intents, entities)
        
        # 保存到历史
        if save:
            analysis_memory.add_analysis(
                query=query,
                response=result,
                metadata={
                    "market": entities.get("market", "A 股"),
                    "user_id": user_id,
                }
            )
        
        return {
            "query": query,
            "user_id": user_id,
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _single_agent_analysis(intents: List[str], entities: Dict) -> Dict[str, Any]:
    """单个 Agent 分析"""
    results = []
    
    if "macro_analyst" in intents:
        agent = MacroAnalystAgent(model=settings.CHINA_MODEL)
        result = await agent.analyze(country="CN")
        results.append(result)
    
    if "valuation_analyst" in intents:
        agent = ValuationAnalystAgent(model=settings.CHINA_MODEL)
        result = await agent.analyze(symbol="000300.SH", market="A 股")
        results.append(result)
    
    if "fund_tracker" in intents:
        agent = FundTrackerAgent(model=settings.CHINA_MODEL)
        result = await agent.analyze(market="A 股")
        results.append(result)
    
    if "sentiment_analyst" in intents:
        agent = SentimentAnalystAgent(model=settings.CHINA_MODEL)
        result = await agent.analyze(market="A 股")
        results.append(result)
    
    return {"results": results}


# ========== 市场接口 ==========

@app.get("/api/market/{market}")
async def get_market_overview(market: str = "A 股") -> Dict[str, Any]:
    """获取市场概览"""
    try:
        if not data_service:
            raise HTTPException(status_code=503, detail="数据服务未初始化")
        
        overview = await data_service.get_market_overview(market)
        return overview
        
    except Exception as e:
        logger.error(f"获取市场概览失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/{market}")
async def get_sentiment(market: str = "A 股") -> Dict[str, Any]:
    """获取市场情绪"""
    try:
        if not data_service:
            raise HTTPException(status_code=503, detail="数据服务未初始化")
        
        sentiment = await data_service.get_sentiment(market)
        return sentiment
        
    except Exception as e:
        logger.error(f"获取情绪数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 个性化配置接口 ==========

@app.get("/api/preferences/{user_id}")
async def get_preferences(user_id: str) -> Dict[str, Any]:
    """获取用户偏好"""
    prefs = preferences_manager.get_preferences(user_id)
    return prefs.model_dump()


@app.post("/api/preferences/{user_id}")
async def update_preferences(user_id: str, prefs: Dict) -> Dict[str, Any]:
    """更新用户偏好"""
    from services.preferences import UserPreferences
    
    try:
        user_prefs = UserPreferences(user_id=user_id, **prefs)
        preferences_manager.update_preferences(user_id, user_prefs)
        return {"status": "ok", "message": "偏好已更新"}
    except Exception as e:
        logger.error(f"更新偏好失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preferences/{user_id}/markets")
async def update_markets(user_id: str, markets: List[str]) -> Dict[str, Any]:
    """更新关注市场"""
    success = preferences_manager.update_market(user_id, markets)
    if success:
        return {"status": "ok", "markets": markets}
    raise HTTPException(status_code=500, detail="更新失败")


# ========== 历史记录接口 ==========

@app.get("/api/history")
async def get_history(
    limit: int = Query(default=10, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """获取分析历史"""
    return analysis_memory.get_recent(limit)


@app.get("/api/history/search")
async def search_history(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(default=5, ge=1, le=20),
    market: str = Query(default=None, description="市场过滤"),
) -> List[Dict[str, Any]]:
    """搜索相似分析"""
    return analysis_memory.search_similar(query, limit, market)


@app.get("/api/history/stats")
async def get_history_stats() -> Dict[str, Any]:
    """获取历史统计"""
    return analysis_memory.get_statistics()


# ========== 预警接口 ==========

@app.get("/api/alerts/check")
async def check_alerts() -> Dict[str, Any]:
    """手动触发预警检查"""
    try:
        from feishu_bot.bot import FeishuBot
        
        bot = FeishuBot()
        alerts = await bot.check_alerts()
        
        return {
            "checked_at": "now",
            "alerts": alerts or [],
        }
    except Exception as e:
        logger.error(f"预警检查失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/morning")
async def get_morning_report() -> Dict[str, Any]:
    """获取早报"""
    try:
        from feishu_bot.bot import FeishuBot
        
        bot = FeishuBot()
        report = await bot.generate_morning_report()
        
        return {
            "type": "morning",
            "report": report,
        }
    except Exception as e:
        logger.error(f"生成早报失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/evening")
async def get_evening_report() -> Dict[str, Any]:
    """获取晚报"""
    try:
        from feishu_bot.bot import FeishuBot
        
        bot = FeishuBot()
        report = await bot.generate_evening_report()
        
        return {
            "type": "evening",
            "report": report,
        }
    except Exception as e:
        logger.error(f"生成晚报失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 系统信息 ==========

@app.get("/api/models")
async def get_available_models() -> Dict[str, Any]:
    """获取可用模型"""
    return {
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek V3", "type": "chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek R1", "type": "reasoning"},
            {"id": "gpt-4o", "name": "GPT-4o", "type": "chat"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "chat"},
        ],
        "default": settings.DEFAULT_MODEL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
