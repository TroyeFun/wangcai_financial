"""
FastAPI 主应用入口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Dict, Any
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
from data import DataService, CacheManager


# 初始化应用
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS 配置（前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据服务（延迟初始化）
data_service: DataService = None


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"应用启动：{settings.APP_NAME}")
    logger.info(f"环境：{settings.APP_ENV}")
    logger.info(f"默认模型：{settings.DEFAULT_MODEL}")
    
    # 初始化数据服务
    global data_service
    cache_manager = CacheManager(settings.REDIS_URL)
    data_service = DataService(
        cache_manager,
        api_keys={
            "finnhub": settings.FINNHUB_API_KEY or "",
            "coingecko": settings.COINGECKO_API_KEY or "",
        }
    )
    logger.info("数据服务初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("应用关闭")


@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "0.3.0",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.post("/api/analyze")
async def analyze(query: str) -> Dict[str, Any]:
    """
    分析接口
    
    Args:
        query: 用户查询文本
        
    Returns:
        分析结果
    """
    try:
        # 意图识别
        intents = identify_intent(query)
        entities = extract_entities(query)
        
        logger.info(f"查询：{query}, 意图：{intents}, 实体：{entities}")
        
        # 根据意图分发到对应 Agent
        results = []
        
        # 并行执行多个 Agent
        tasks = []
        agent_names = []
        
        if "macro_analyst" in intents:
            agent = MacroAnalystAgent(model=settings.CHINA_MODEL)
            country = "CN" if entities.get("market") in ["A 股", "沪深", "上证", "深证"] else "US"
            tasks.append(agent.analyze(country=country))
            agent_names.append("macro_analyst")
        
        if "valuation_analyst" in intents:
            agent = ValuationAnalystAgent(model=settings.CHINA_MODEL)
            if data_service:
                agent.set_data_service(data_service)
            symbol = entities.get("symbol", "000300.SH")
            tasks.append(agent.analyze(symbol=symbol, market=entities.get("market", "A 股")))
            agent_names.append("valuation_analyst")
        
        if "fund_tracker" in intents:
            agent = FundTrackerAgent(model=settings.CHINA_MODEL)
            if data_service:
                agent.set_data_service(data_service)
            tasks.append(agent.analyze(market=entities.get("market", "A 股")))
            agent_names.append("fund_tracker")
        
        if "sentiment_analyst" in intents:
            agent = SentimentAnalystAgent(model=settings.CHINA_MODEL)
            if data_service:
                agent.set_data_service(data_service)
            tasks.append(agent.analyze(market=entities.get("market", "A 股")))
            agent_names.append("sentiment_analyst")
        
        # 执行所有任务
        if tasks:
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent_names[i]} 执行失败：{result}")
                else:
                    results.append(result)
        
        # 如果是多维分析，添加风控建议
        if len(intents) >= 3:
            risk_agent = RiskManagerAgent(model=settings.CHINA_MODEL)
            
            # 收集各维度评分
            scores = {"macro": 7.0, "valuation": 7.0, "fund": 6.5, "sentiment": 6.0}
            for r in results:
                if r.get("agent") == "macro_analyst":
                    scores["macro"] = r.get("score", 7.0)
                elif r.get("agent") == "valuation_analyst":
                    scores["valuation"] = r.get("score", 7.0)
                elif r.get("agent") == "fund_tracker":
                    scores["fund"] = r.get("score", 6.5)
                elif r.get("agent") == "sentiment_analyst":
                    scores["sentiment"] = r.get("score", 6.0)
            
            risk_result = await risk_agent.analyze(**scores)
            results.append(risk_result)
        
        return {
            "query": query,
            "intents": intents,
            "entities": entities,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/{market}")
async def get_market_overview(market: str = "A 股") -> Dict[str, Any]:
    """获取市场概览"""
    try:
        if not data_service:
            return {"error": "数据服务未初始化"}
        
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
            return {"error": "数据服务未初始化"}
        
        sentiment = await data_service.get_sentiment(market)
        return sentiment
        
    except Exception as e:
        logger.error(f"获取情绪数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
