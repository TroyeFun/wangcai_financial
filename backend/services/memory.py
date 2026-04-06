"""
历史分析向量检索

使用 ChromaDB 存储和检索历史分析报告
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB 未安装，向量检索功能不可用")


class AnalysisMemory:
    """分析历史记忆"""
    
    def __init__(self, persist_dir: str = "./data/chroma"):
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            self._init_chroma()
        else:
            # 使用简单的内存存储
            self._memory_store: List[Dict] = []
            logger.info("使用内存存储代替 ChromaDB")
    
    def _init_chroma(self):
        """初始化 ChromaDB"""
        try:
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_dir,
                anonymized_telemetry=False,
            ))
            
            # 创建或获取集合
            self.collection = self.client.get_or_create_collection(
                name="analysis_history",
                metadata={"description": "投资分析历史记录"}
            )
            
            logger.info("ChromaDB 初始化成功")
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败：{e}")
            self.client = None
            self.collection = None
    
    def add_analysis(self, 
                   query: str, 
                   response: Dict[str, Any],
                   metadata: Dict[str, Any] = None) -> bool:
        """
        添加分析记录
        
        Args:
            query: 用户查询
            response: 分析响应
            metadata: 额外元数据（如市场、时间等）
        """
        record = {
            "id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        if self.collection:
            try:
                # 添加到 ChromaDB
                self.collection.add(
                    documents=[json.dumps({"query": query, "response": response})],
                    ids=[record["id"]],
                    metadatas=[{
                        "timestamp": record["timestamp"],
                        "market": metadata.get("market", "unknown") if metadata else "unknown",
                    }]
                )
                logger.info(f"分析记录已添加：{record['id']}")
                return True
            except Exception as e:
                logger.error(f"添加分析记录失败：{e}")
                return False
        else:
            # 内存存储
            self._memory_store.append(record)
            logger.info(f"分析记录已添加（内存）：{record['id']}")
            return True
    
    def search_similar(self, 
                      query: str, 
                      limit: int = 5,
                      market: str = None) -> List[Dict[str, Any]]:
        """
        搜索相似分析
        
        Args:
            query: 搜索查询
            limit: 返回数量
            market: 市场过滤
        """
        if self.collection:
            try:
                # ChromaDB 向量搜索
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where={"market": market} if market else None,
                )
                
                # 解析结果
                similar = []
                if results and results.get("documents"):
                    for i, doc in enumerate(results["documents"][0]):
                        similar.append({
                            "id": results["ids"][0][i],
                            "score": results.get("distances", [[]])[0][i] if results.get("distances") else 1.0,
                            "data": json.loads(doc),
                            "timestamp": results["metadatas"][0][i].get("timestamp") if results.get("metadatas") else None,
                        })
                
                return similar
                
            except Exception as e:
                logger.error(f"搜索失败：{e}")
                return []
        else:
            # 简单文本匹配
            return self._simple_search(query, limit)
    
    def _simple_search(self, query: str, limit: int = 5) -> List[Dict]:
        """简单的文本搜索（备选）"""
        keywords = set(query.lower().split())
        
        scored = []
        for record in self._memory_store:
            score = 0
            query_lower = record["query"].lower()
            for kw in keywords:
                if kw in query_lower:
                    score += 1
            
            if score > 0:
                scored.append({
                    "id": record["id"],
                    "score": score,
                    "data": {"query": record["query"], "response": record["response"]},
                    "timestamp": record["timestamp"],
                })
        
        # 按分数排序
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的分析记录"""
        if self.collection:
            try:
                results = self.collection.get(limit=limit)
                
                records = []
                if results and results.get("documents"):
                    for i, doc in enumerate(results["documents"]):
                        records.append({
                            "id": results["ids"][i],
                            "data": json.loads(doc),
                            "timestamp": results["metadatas"][i].get("timestamp") if results.get("metadatas") else None,
                        })
                
                return records
            except Exception as e:
                logger.error(f"获取最近记录失败：{e}")
                return []
        else:
            return self._memory_store[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = 0
        markets = {}
        
        if self.collection:
            try:
                total = self.collection.count()
                
                # 获取所有记录的市场分布
                results = self.collection.get()
                if results and results.get("metadatas"):
                    for meta in results["metadatas"]:
                        market = meta.get("market", "unknown")
                        markets[market] = markets.get(market, 0) + 1
            except Exception as e:
                logger.error(f"获取统计失败：{e}")
        else:
            total = len(self._memory_store)
            for record in self._memory_store:
                market = record.get("metadata", {}).get("market", "unknown")
                markets[market] = markets.get(market, 0) + 1
        
        return {
            "total_analyses": total,
            "market_distribution": markets,
            "memory_type": "chromadb" if self.collection else "memory",
        }


# 全局实例
analysis_memory = AnalysisMemory()
