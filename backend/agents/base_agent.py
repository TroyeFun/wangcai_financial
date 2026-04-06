"""
AI Agent 基类

所有分析 Agent 都继承此基类，实现统一的调用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger
import litellm
from datetime import datetime


class BaseAgent(ABC):
    """AI Agent 基类"""
    
    def __init__(self, model: str = "deepseek-v4", temperature: float = 0.0):
        """
        Args:
            model: 使用的 LLM 模型
            temperature: 温度参数（金融分析强制为 0）
        """
        self.model = model
        self.temperature = temperature
        self.name = self.__class__.__name__
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """调用 LLM
        
        使用 LiteLLM 统一接口，支持多模型路由
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            
            content = response.choices[0].message.content
            logger.info(f"{self.name} LLM 调用成功，tokens: {response.usage.total_tokens}")
            return content
            
        except Exception as e:
            logger.error(f"{self.name} LLM 调用失败：{e}")
            return f"分析失败：{str(e)}"
    
    @abstractmethod
    async def analyze(self, **kwargs) -> Dict[str, Any]:
        """执行分析
        
        子类必须实现此方法
        """
        pass
    
    def _build_roles_prompt(self, role: str, objective: str, limits: str, 
                           evidence: str, safeguards: str) -> str:
        """构建 ROLES Prompt 框架
        
        Role-Objective-Limits-Evidence-Safeguards 结构化 Prompt
        """
        return f"""
Role: {role}

Objective: {objective}

Limits: {limits}

Evidence:
{evidence}

Safeguards: {safeguards}

请基于以上信息进行分析，确保所有结论都有数据支撑。
"""
