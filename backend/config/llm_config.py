"""
LLM 配置模块

支持多模型路由，包括：
- AIHubMix（国内聚合平台，推荐）
- OpenAI
- Azure OpenAI
- Anthropic
- DeepSeek 官方
"""

import os
import litellm
from loguru import logger
from typing import Dict, Optional

from .settings import settings


class LLMConfig:
    """LLM 配置管理器"""
    
    # 模型路由配置
    MODEL_ROUTES = {
        # 中国市场 - 使用 DeepSeek
        "deepseek-v4": "deepseek/deepseek-chat-v3",
        "deepseek-r1": "deepseek/deepseek-reasoner",
        
        # 美国市场 - 使用 GPT-4o
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        
        # 通用 - 兼容模式
        "default": "deepseek/deepseek-chat-v3",
    }
    
    # 模型别名
    ALIASES = {
        # DeepSeek 系列
        "deepseek-v4": "deepseek/deepseek-chat-v3",
        "deepseek-chat": "deepseek/deepseek-chat-v3",
        "deepseek-coder": "deepseek/deepseek-coder-v2",
        "deepseek-r1": "deepseek/deepseek-reasoner",
        "deepseek-reasoner": "deepseek/deepseek-reasoner",
        
        # GPT 系列
        "gpt-4o": "gpt-4o",
        "gpt-4": "gpt-4",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-3.5": "gpt-3.5-turbo",
        
        # Claude 系列
        "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-opus": "claude-3-opus",
        
        # 国内模型
        "qwen-plus": "qwen/qwen-plus",
        "qwen-max": "qwen/qwen-max",
        "yi-large": "yi/yi-large",
        "glm-4": "zhipuai/glm-4",
        "moonshot-v1-8k": "moonshot/moonshot-v1-8k",
    }
    
    def __init__(self):
        self._configured = False
        self._setup_providers()
    
    def _setup_providers(self):
        """配置 LLM 提供商"""
        try:
            # ========== AIHubMix 配置（推荐国内用户）==========
            if settings.AIHUBMIX_API_KEY:
                # AIHubMix 端点
                litellm.base_url = settings.AIHUBMIX_BASE_URL or "https://api.aihubmix.com/v1"
                
                # 设置 API Key
                os.environ["AIHUBMIX_API_KEY"] = settings.AIHUBMIX_API_KEY
                
                # 特别配置：禁用严格模式（某些模型需要）
                os.environ["LITELLM_ALLOW_STRICT_MODE"] = "false"
                
                logger.info(f"✅ AIHubMix 已配置，端点：{litellm.base_url}")
                self._configured = True
            
            # ========== DeepSeek 官方配置 ==========
            elif settings.DEEPSEEK_API_KEY:
                os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY
                logger.info("✅ DeepSeek 官方已配置")
                self._configured = True
            
            # ========== OpenAI 配置 ==========
            elif settings.OPENAI_API_KEY:
                os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
                logger.info("✅ OpenAI 已配置")
                self._configured = True
            
            # ========== Azure OpenAI 配置 ==========
            if settings.AZURE_API_KEY and settings.AZURE_BASE_URL:
                litellm.base_url = settings.AZURE_BASE_URL
                os.environ["AZURE_API_KEY"] = settings.AZURE_API_KEY
                os.environ["API_VERSION"] = settings.AZURE_API_VERSION or "2024-02-01"
                logger.info("✅ Azure OpenAI 已配置")
                self._configured = True
            
            # 设置超时
            litellm.max_retries = 3
            litellm.request_timeout = 120  # 2分钟超时
            
            logger.info("LLM 配置完成")
            
        except Exception as e:
            logger.error(f"LLM 配置失败：{e}")
    
    def get_model(self, model_key: str) -> str:
        """获取实际模型名称
        
        Args:
            model_key: 模型键（可以是别名）
            
        Returns:
            完整的模型标识符
        """
        # 如果是完整标识符（包含/），直接返回
        if "/" in model_key:
            return model_key
        
        # 查找别名
        if model_key in self.ALIASES:
            return self.ALIASES[model_key]
        
        # 查找路由
        if model_key in self.MODEL_ROUTES:
            return self.MODEL_ROUTES[model_key]
        
        # 默认返回原值
        return model_key
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self._configured


# 全局 LLM 配置实例
llm_config = LLMConfig()


def call_llm(
    model: str,
    messages: list,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    **kwargs
) -> dict:
    """调用 LLM 的统一接口
    
    Args:
        model: 模型名称（支持别名）
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        **kwargs: 其他参数
        
    Returns:
        LLM 响应
    """
    # 解析实际模型
    actual_model = llm_config.get_model(model)
    
    try:
        response = litellm.completion(
            model=actual_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        logger.info(f"LLM 调用成功，模型：{actual_model}，tokens：{response.usage.total_tokens}")
        return response
        
    except Exception as e:
        logger.error(f"LLM 调用失败：{e}")
        
        # 尝试降级
        if "deepseek" in actual_model:
            logger.info("尝试使用 gpt-4o-mini 降级...")
            try:
                response = litellm.completion(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                logger.info("降级成功")
                return response
            except Exception as e2:
                logger.error(f"降级也失败：{e2}")
        
        raise e


def get_available_models() -> list:
    """获取可用的模型列表"""
    return list(llm_config.ALIASES.keys())
