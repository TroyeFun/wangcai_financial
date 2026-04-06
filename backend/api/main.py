"""
FastAPI 主应用入口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Dict, Any

from config.settings import settings
from router.intent import identify_intent, extract_entities
from agents.macro_analyst import MacroAnalystAgent


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


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"应用启动：{settings.APP_NAME}")
    logger.info(f"环境：{settings.APP_ENV}")
    logger.info(f"默认模型：{settings.DEFAULT_MODEL}")


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
        "version": "0.1.0",
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
        
        if "macro_analyst" in intents:
            agent = MacroAnalystAgent(model=settings.CHINA_MODEL)
            country = "CN" if entities.get("market") == "A 股" else "US"
            result = await agent.analyze(country=country)
            results.append(result)
        
        # TODO: 扩展其他 Agent
        
        return {
            "query": query,
            "intents": intents,
            "entities": entities,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
