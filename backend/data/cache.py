"""
缓存管理模块

使用 Redis 缓存高频数据，减少 API 调用
"""

import json
import redis
from typing import Any, Optional
from loguru import logger
from datetime import timedelta


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        logger.info("缓存管理器初始化成功")
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        return f"investment:{prefix}:{identifier}"
    
    async def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """获取缓存数据"""
        try:
            key = self._make_key(prefix, identifier)
            data = self.redis.get(key)
            if data:
                logger.debug(f"缓存命中：{key}")
                return json.loads(data)
            logger.debug(f"缓存未命中：{key}")
            return None
        except Exception as e:
            logger.error(f"获取缓存失败：{e}")
            return None
    
    async def set(self, prefix: str, identifier: str, data: Any, ttl: int) -> bool:
        """设置缓存数据
        
        Args:
            prefix: 键前缀
            identifier: 唯一标识
            data: 数据（会自动序列化）
            ttl: 过期时间（秒）
        """
        try:
            key = self._make_key(prefix, identifier)
            serialized = json.dumps(data, default=str)  # 处理 datetime 等类型
            self.redis.setex(key, timedelta(seconds=ttl), serialized)
            logger.debug(f"缓存已设置：{key}, TTL={ttl}s")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败：{e}")
            return False
    
    async def delete(self, prefix: str, identifier: str) -> bool:
        """删除缓存"""
        try:
            key = self._make_key(prefix, identifier)
            self.redis.delete(key)
            logger.debug(f"缓存已删除：{key}")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败：{e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """批量删除匹配模式的缓存"""
        try:
            keys = self.redis.keys(self._make_key(pattern, "*"))
            if keys:
                self.redis.delete(*keys)
                logger.info(f"批量删除缓存：{len(keys)} 个键")
            return True
        except Exception as e:
            logger.error(f"批量删除缓存失败：{e}")
            return False


# 缓存前缀常量
CACHE_PREFIX = {
    "MARKET_DATA": "market",      # 行情数据
    "MACRO_DATA": "macro",        # 宏观数据
    "FUND_FLOW": "fundflow",      # 资金流向
    "VALUATION": "valuation",     # 估值数据
    "SENTIMENT": "sentiment",     # 情绪数据
    "ANALYSIS": "analysis",       # 分析报告
}
