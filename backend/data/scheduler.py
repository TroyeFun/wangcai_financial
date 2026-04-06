"""
数据采集调度器

负责定时采集各市场数据，更新缓存
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from typing import Dict, Any, List
import asyncio

from .providers.akshare import AkShareProvider
from .providers.finnhub import FinnhubProvider
from .providers.coingecko import CoinGeckoProvider
from .cache import CacheManager


class DataScheduler:
    """数据采集调度器"""
    
    def __init__(self, cache_manager: CacheManager, api_keys: Dict[str, str] = None):
        self.scheduler = AsyncIOScheduler()
        self.cache = cache_manager
        self.api_keys = api_keys or {}
        
        # 初始化数据提供者
        self.akshare = AkShareProvider()
        self.finnhub = FinnhubProvider(api_key=self.api_keys.get("finnhub", ""))
        self.coingecko = CoinGeckoProvider(api_key=self.api_keys.get("coingecko", ""))
        
        logger.info("数据调度器初始化完成")
    
    def setup_jobs(self):
        """配置定时任务"""
        
        # ========== A 股数据采集 ==========
        
        # 每日收盘后采集A股数据（15:30 后）
        self.scheduler.add_job(
            self.collect_a_stock_data,
            CronTrigger(hour=15, minute=35, day_of_week="mon-fri"),
            id="collect_a_stock_daily",
            name="A股每日数据采集",
            replace_existing=True,
        )
        
        # 盘中每小时更新资金流向
        self.scheduler.add_job(
            self.collect_fund_flow,
            IntervalTrigger(hours=1, start_date="09:30:00", end_date="15:00:00"),
            id="collect_fund_flow_hourly",
            name="资金流向每小时更新",
            replace_existing=True,
        )
        
        # ========== 美股数据采集 ==========
        
        # 美股收盘后采集（次日 05:00，对应美东时间 16:00）
        self.scheduler.add_job(
            self.collect_us_stock_data,
            CronTrigger(hour=5, minute=0),
            id="collect_us_stock_daily",
            name="美股每日数据采集",
            replace_existing=True,
        )
        
        # ========== 加密货币数据采集 ==========
        
        # 每小时采集加密数据
        self.scheduler.add_job(
            self.collect_crypto_data,
            IntervalTrigger(hours=1),
            id="collect_crypto_hourly",
            name="加密货币每小时更新",
            replace_existing=True,
        )
        
        # ========== 宏观数据采集 ==========
        
        # 每周一采集宏观数据
        self.scheduler.add_job(
            self.collect_macro_data,
            CronTrigger(day_of_week="mon", hour=8, minute=0),
            id="collect_macro_weekly",
            name="宏观数据每周采集",
            replace_existing=True,
        )
        
        # ========== 情绪数据采集 ==========
        
        # 每 30 分钟更新市场情绪
        self.scheduler.add_job(
            self.collect_sentiment_data,
            IntervalTrigger(minutes=30),
            id="collect_sentiment_halfhourly",
            name="情绪数据每30分钟更新",
            replace_existing=True,
        )
        
        logger.info("定时任务配置完成")
    
    async def collect_a_stock_data(self):
        """采集A股数据"""
        logger.info("开始采集A股数据...")
        
        symbols = ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH"]  # 沪深主要指数
        
        for symbol in symbols:
            try:
                data = await self.akshare.get_market_data(symbol, period="daily")
                if not data.empty:
                    await self.cache.set(
                        "market",
                        symbol,
                        data.to_dict(),
                        self.cache.CACHE_TTL_DAY_K
                    )
                    logger.info(f"A股数据采集成功：{symbol}")
            except Exception as e:
                logger.error(f"A股数据采集失败：{symbol}, 错误：{e}")
        
        logger.info("A股数据采集完成")
    
    async def collect_fund_flow(self):
        """采集资金流向数据"""
        logger.info("开始采集资金流向...")
        
        try:
            # 北向资金
            north_flow = await self.akshare.get_fund_flow("A 股")
            if not north_flow.empty:
                await self.cache.set(
                    "fundflow",
                    "north",
                    north_flow.to_dict(),
                    self.cache.CACHE_TTL_FUND_FLOW
                )
            
            # 两融数据
            margin_data = await self.akshare.get_fund_flow("两融")
            if not margin_data.empty:
                await self.cache.set(
                    "fundflow",
                    "margin",
                    margin_data.to_dict(),
                    self.cache.CACHE_TTL_FUND_FLOW
                )
            
            logger.info("资金流向采集完成")
            
        except Exception as e:
            logger.error(f"资金流向采集失败：{e}")
    
    async def collect_us_stock_data(self):
        """采集美股数据"""
        logger.info("开始采集美股数据...")
        
        symbols = ["SPY", "QQQ", "DIA"]  # SP500, Nasdaq, Dow Jones ETF
        
        for symbol in symbols:
            try:
                data = await self.finnhub.get_market_data(symbol, period="daily")
                if not data.empty:
                    await self.cache.set(
                        "market",
                        f"us_{symbol}",
                        data.to_dict(),
                        self.cache.CACHE_TTL_DAY_K
                    )
                    logger.info(f"美股数据采集成功：{symbol}")
            except Exception as e:
                logger.error(f"美股数据采集失败：{symbol}, 错误：{e}")
        
        logger.info("美股数据采集完成")
    
    async def collect_crypto_data(self):
        """采集加密货币数据"""
        logger.info("开始采集加密货币数据...")
        
        symbols = ["BTC", "ETH", "BNB"]
        
        for symbol in symbols:
            try:
                data = await self.coingecko.get_market_data(symbol, period="daily")
                if not data.empty:
                    await self.cache.set(
                        "market",
                        f"crypto_{symbol}",
                        data.to_dict(),
                        self.cache.CACHE_TTL_DAY_K
                    )
                    
                    # 同时采集情绪数据
                    sentiment = await self.coingecko.get_sentiment_data(symbol)
                    if sentiment:
                        await self.cache.set(
                            "sentiment",
                            f"crypto_{symbol}",
                            sentiment,
                            self.cache.CACHE_TTL_SENTIMENT
                        )
                    
                    logger.info(f"加密数据采集成功：{symbol}")
            except Exception as e:
                logger.error(f"加密数据采集失败：{symbol}, 错误：{e}")
        
        logger.info("加密货币数据采集完成")
    
    async def collect_macro_data(self):
        """采集宏观经济数据"""
        logger.info("开始采集宏观数据...")
        
        indicators = ["GDP", "CPI", "PMI", "M2"]
        
        for indicator in indicators:
            try:
                data = await self.akshare.get_macro_data(indicator, "CN")
                if not data.empty:
                    await self.cache.set(
                        "macro",
                        indicator,
                        data.to_dict(),
                        self.cache.CACHE_TTL_MACRO
                    )
                    logger.info(f"宏观数据采集成功：{indicator}")
            except Exception as e:
                logger.error(f"宏观数据采集失败：{indicator}, 错误：{e}")
        
        logger.info("宏观数据采集完成")
    
    async def collect_sentiment_data(self):
        """采集市场情绪数据"""
        logger.info("开始采集情绪数据...")
        
        try:
            # A股情绪
            cn_sentiment = await self.akshare.get_sentiment_data("A 股")
            await self.cache.set(
                "sentiment",
                "cn",
                cn_sentiment,
                self.cache.CACHE_TTL_SENTIMENT
            )
            
            # 美股 VIX
            us_sentiment = await self.finnhub.get_sentiment_data("US")
            await self.cache.set(
                "sentiment",
                "us",
                us_sentiment,
                self.cache.CACHE_TTL_SENTIMENT
            )
            
            logger.info("情绪数据采集完成")
            
        except Exception as e:
            logger.error(f"情绪数据采集失败：{e}")
    
    async def run_now(self):
        """手动触发立即采集"""
        logger.info("手动触发数据采集...")
        
        tasks = [
            self.collect_a_stock_data(),
            self.collect_fund_flow(),
            self.collect_us_stock_data(),
            self.collect_crypto_data(),
            self.collect_macro_data(),
            self.collect_sentiment_data(),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("手动采集完成")
    
    def start(self):
        """启动调度器"""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("数据调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("数据调度器已停止")
