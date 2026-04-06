"""
个性化配置管理

管理用户的投资偏好和通知设置
"""

from typing import Dict, Any, List, Optional
from datetime import time
from pydantic import BaseModel
from loguru import logger


class UserPreferences(BaseModel):
    """用户偏好配置"""
    
    # 基本信息
    user_id: str
    user_name: str = ""
    
    # 关注市场
    markets: List[str] = ["A 股"]  # A 股、港股、美股、加密
    
    # 关注板块
    sectors: List[str] = []  # 科技、消费、金融等
    
    # 风险偏好
    risk_level: str = "medium"  # low, medium, high
    
    # 推送设置
    enable_morning_report: bool = True
    enable_evening_report: bool = True
    enable_alerts: bool = True
    
    # 推送时间
    morning_report_time: str = "07:30"
    evening_report_time: str = "20:00"
    
    # 预警阈值
    alert_thresholds: Dict[str, float] = {
        "north_flow": -50,  # 北向资金流出阈值（亿）
        "drop_threshold": -3.0,  # 单日跌幅阈值（%）
        "fear_greed_low": 20,  # 极度恐惧
        "fear_greed_high": 80,  # 极度贪婪
    }
    
    # 仓位建议偏好
    position_preference: str = "standard"  # conservative, standard, aggressive
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "user_name": "张三",
                "markets": ["A 股", "港股"],
                "sectors": ["科技", "消费"],
                "risk_level": "medium",
                "enable_morning_report": True,
                "enable_evening_report": True,
                "enable_alerts": True,
            }
        }


class PreferencesManager:
    """用户偏好管理器"""
    
    def __init__(self):
        # 内存存储（生产环境应该用数据库）
        self._preferences: Dict[str, UserPreferences] = {}
        self._default_preferences = UserPreferences(
            user_id="default",
            user_name="默认用户",
        )
        logger.info("偏好管理器初始化完成")
    
    def get_preferences(self, user_id: str) -> UserPreferences:
        """获取用户偏好"""
        return self._preferences.get(user_id, self._default_preferences)
    
    def update_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """更新用户偏好"""
        try:
            self._preferences[user_id] = preferences
            logger.info(f"用户 {user_id} 偏好已更新")
            return True
        except Exception as e:
            logger.error(f"更新偏好失败：{e}")
            return False
    
    def update_market(self, user_id: str, markets: List[str]) -> bool:
        """更新关注市场"""
        prefs = self.get_preferences(user_id)
        prefs.markets = markets
        return self.update_preferences(user_id, prefs)
    
    def update_alert_threshold(self, user_id: str, key: str, value: float) -> bool:
        """更新预警阈值"""
        prefs = self.get_preferences(user_id)
        prefs.alert_thresholds[key] = value
        return self.update_preferences(user_id, prefs)
    
    def enable_report(self, user_id: str, report_type: str, enabled: bool) -> bool:
        """开关推送"""
        prefs = self.get_preferences(user_id)
        if report_type == "morning":
            prefs.enable_morning_report = enabled
        elif report_type == "evening":
            prefs.enable_evening_report = enabled
        elif report_type == "alert":
            prefs.enable_alerts = enabled
        return self.update_preferences(user_id, prefs)
    
    def get_position_recommendation(self, user_id: str, base_position: str) -> str:
        """根据风险偏好调整仓位建议"""
        prefs = self.get_preferences(user_id)
        
        if prefs.position_preference == "conservative":
            # 保守型：降低 20%
            return f"{int(base_position.rstrip('%').rstrip('0-9')) * 0.8}-{int(base_position.split('-')[1].rstrip('%')) * 0.8}%"
        elif prefs.position_preference == "aggressive":
            # 激进型：提高 20%
            parts = base_position.split("-")
            low = int(parts[0].rstrip("%"))
            high = int(parts[1].rstrip("%"))
            return f"{min(100, int(low * 1.2))}-{min(100, int(high * 1.2))}%"
        else:
            return base_position


# 全局偏好管理器
preferences_manager = PreferencesManager()
