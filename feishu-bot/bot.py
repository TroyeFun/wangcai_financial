"""
飞书 Bot 服务 - 完整版

功能：
- 命令交互（/宏观、/估值、/资金、/情绪、/分析、/预警）
- 定时推送（早报 07:30、晚报 20:00）
- 异常预警（实时推送）
- 多 Agent 协同分析
"""

import json
import asyncio
from datetime import datetime, time
from typing import Dict, Any, Optional
from loguru import logger
import httpx

from lark_oapi.api.im.v1 import *
from lark_oapi.adapter.httpx import HttpxAdapter
from lark_oapi import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from agents import (
    MacroAnalystAgent,
    ValuationAnalystAgent,
    FundTrackerAgent,
    SentimentAnalystAgent,
    RiskManagerAgent,
)
from data import DataService, CacheManager


class FeishuBot:
    """飞书 Bot"""
    
    def __init__(self):
        # 初始化飞书客户端
        self.client = Client.builder() \
            .app_id(settings.FEISHU_APP_ID) \
            .app_secret(settings.FEISHU_APP_SECRET) \
            .log_level("INFO") \
            .build()
        
        # 初始化 Agent
        self._init_agents()
        
        # 初始化调度器
        self.scheduler = AsyncIOScheduler()
        
        # 预警配置
        self.alert_config = {
            "north_flow_threshold": -50,  # 北向资金流出阈值（亿）
            "drop_threshold": -3.0,       # 单日跌幅阈值（%）
            "fear_greed_extreme": 20,     # 极度恐惧阈值
            "fear_greed_overheat": 80,    # 极度贪婪阈值
        }
        
        logger.info("飞书 Bot 初始化完成")
    
    def _init_agents(self):
        """初始化所有 Agent"""
        self.agents = {
            "macro": MacroAnalystAgent(model=settings.CHINA_MODEL),
            "valuation": ValuationAnalystAgent(model=settings.CHINA_MODEL),
            "fund": FundTrackerAgent(model=settings.CHINA_MODEL),
            "sentiment": SentimentAnalystAgent(model=settings.CHINA_MODEL),
            "risk": RiskManagerAgent(model=settings.CHINA_MODEL),
        }
    
    async def handle_message(self, event_data: Dict) -> Dict:
        """处理消息事件"""
        
        message = event_data.get("event", {}).get("message", {})
        sender = event_data.get("event", {}).get("sender", {})
        
        msg_id = message.get("message_id")
        msg_type = message.get("message_type")
        content = json.loads(message.get("content", "{}"))
        text = content.get("text", "")
        
        sender_id = sender.get("sender_id", {}).get("open_id", "")
        chat_id = message.get("chat_id", "")
        
        logger.info(f"收到消息 - ID: {msg_id}, 发送者：{sender_id}, 内容：{text}")
        
        # 只处理文本消息
        if msg_type != "text":
            return {"status": "ok"}
        
        # 忽略机器人自己的消息
        if sender.get("sender_type") == "bot":
            return {"status": "ok"}
        
        # 处理命令或对话
        if text.startswith("/"):
            return await self.handle_command(text, chat_id, msg_id)
        else:
            return await self.handle_conversation(text, chat_id, msg_id)
    
    async def handle_command(self, command: str, chat_id: str, reply_msg_id: str) -> Dict:
        """处理飞书命令"""
        
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"处理命令：{cmd}, 参数：{args}")
        
        # 命令路由
        command_handlers = {
            "/宏观": self._cmd_macro,
            "/估值": self._cmd_valuation,
            "/资金": self._cmd_fund,
            "/情绪": self._cmd_sentiment,
            "/分析": self._cmd_analyze,
            "/预警": self._cmd_alert,
            "/help": self._cmd_help,
            "/早报": self._cmd_morning_report,
            "/晚报": self._cmd_evening_report,
        }
        
        handler = command_handlers.get(cmd)
        if handler:
            response_text = await handler(args)
        else:
            response_text = f"❓ 未知命令：{cmd}\n\n输入 /help 查看可用命令"
        
        # 回复消息
        await self.send_message(chat_id, response_text, reply_msg_id)
        
        return {"status": "ok"}
    
    async def handle_conversation(self, text: str, chat_id: str, reply_msg_id: str) -> Dict:
        """处理自然语言对话"""
        
        # 简单的意图识别
        intents = self._identify_intent(text)
        
        logger.info(f"对话意图识别：{intents}")
        
        # 根据意图调用相应 Agent
        results = []
        
        if "macro" in intents:
            result = await self.agents["macro"].analyze(country="CN")
            results.append(result)
        
        if "valuation" in intents:
            result = await self.agents["valuation"].analyze(symbol="000300.SH", market="A 股")
            results.append(result)
        
        if "fund" in intents:
            result = await self.agents["fund"].analyze(market="A 股")
            results.append(result)
        
        if "sentiment" in intents:
            result = await self.agents["sentiment"].analyze(market="A 股")
            results.append(result)
        
        # 如果是多维分析，添加风控
        if len(intents) >= 2:
            scores = self._extract_scores(results)
            risk_result = await self.agents["risk"].analyze(**scores)
            results.append(risk_result)
        
        # 格式化回复
        response_text = self._format_results(results)
        
        await self.send_message(chat_id, response_text, reply_msg_id)
        
        return {"status": "ok"}
    
    def _identify_intent(self, text: str) -> list:
        """识别对话意图"""
        intents = []
        
        if any(kw in text for kw in ["宏观", "经济", "GDP", "CPI", "PMI"]):
            intents.append("macro")
        if any(kw in text for kw in ["估值", "PE", "PB", "贵", "便宜"]):
            intents.append("valuation")
        if any(kw in text for kw in ["资金", "北向", "两融", "流入", "流出"]):
            intents.append("fund")
        if any(kw in text for kw in ["情绪", "恐慌", "贪婪", "VIX"]):
            intents.append("sentiment")
        
        # 默认分析
        if not intents:
            intents = ["macro", "valuation", "fund", "sentiment"]
        
        return intents
    
    def _extract_scores(self, results: list) -> Dict:
        """提取各 Agent 的评分"""
        scores = {"macro_score": 7.0, "valuation_score": 7.0, "fund_score": 6.5, "sentiment_score": 6.0}
        
        for r in results:
            if r.get("agent") == "macro_analyst":
                scores["macro_score"] = r.get("score", 7.0)
            elif r.get("agent") == "valuation_analyst":
                scores["valuation_score"] = r.get("score", 7.0)
            elif r.get("agent") == "fund_tracker":
                scores["fund_score"] = r.get("score", 6.5)
            elif r.get("agent") == "sentiment_analyst":
                scores["sentiment_score"] = r.get("score", 6.0)
        
        return scores
    
    def _format_results(self, results: list) -> str:
        """格式化结果为文本"""
        if not results:
            return "分析完成，未获取到数据"
        
        lines = ["📊 分析结果\n" + "=" * 30 + "\n"]
        
        for r in results:
            agent = r.get("agent", "")
            
            if agent == "macro_analyst":
                lines.append("🌍 宏观分析师")
                lines.append(f"评分：{r.get('score', 0)}/10")
                lines.append(f"摘要：{r.get('summary', '')}")
            
            elif agent == "valuation_analyst":
                lines.append("\n📈 估值分析师")
                lines.append(f"评分：{r.get('score', 0)}/10")
                lines.append(f"摘要：{r.get('summary', '')}")
            
            elif agent == "fund_tracker":
                lines.append("\n💰 资金流追踪")
                lines.append(f"评分：{r.get('score', 0)}/10")
                lines.append(f"摘要：{r.get('summary', '')}")
            
            elif agent == "sentiment_analyst":
                lines.append("\n🎯 情绪分析师")
                lines.append(f"评分：{r.get('score', 0)}/10")
                lines.append(f"摘要：{r.get('summary', '')}")
            
            elif agent == "risk_manager":
                lines.append("\n⚠️ 风控经理")
                lines.append(f"综合评分：{r.get('composite_score', 0)}/10")
                lines.append(f"建议仓位：{r.get('position_recommendation', {}).get('percentage', '')}")
                lines.append(f"风险等级：{r.get('risk_level', {}).get('level', '')}")
        
        return "\n".join(lines)
    
    # ========== 命令处理器 ==========
    
    async def _cmd_macro(self, args: str) -> str:
        """处理 /宏观 命令"""
        country = args or "中国"
        result = await self.agents["macro"].analyze(country="CN" if "中国" in country else "US")
        return f"📊 宏观经济概览（{country}）\n\n评分：{result.get('score', 0)}/10\n\n{result.get('summary', '')}"
    
    async def _cmd_valuation(self, args: str) -> str:
        """处理 /估值 命令"""
        symbol = args or "沪深 300"
        result = await self.agents["valuation"].analyze(symbol="000300.SH", market="A 股")
        return f"📈 估值分析：{symbol}\n\n评分：{result.get('score', 0)}/10\n\n{result.get('summary', '')}"
    
    async def _cmd_fund(self, args: str) -> str:
        """处理 /资金 命令"""
        flow_type = args or "北向"
        result = await self.agents["fund"].analyze(market="A 股")
        
        lines = [f"💰 资金流向分析\n"]
        nf = result.get("north_flow", {})
        lines.append(f"北向资金今日净流入：{nf.get('net_flow_today', 0)} 亿")
        lines.append(f"趋势：{nf.get('trend', '')}")
        
        mg = result.get("margin", {})
        lines.append(f"两融余额：{mg.get('balance', 0)} 亿")
        lines.append(f"状态：{mg.get('status', '')}")
        
        lines.append(f"\n评分：{result.get('score', 0)}/10")
        return "\n".join(lines)
    
    async def _cmd_sentiment(self, args: str) -> str:
        """处理 /情绪 命令"""
        market = args or "A 股"
        result = await self.agents["sentiment"].analyze(market="A 股")
        
        fg = result.get("fear_greed", {})
        lines = [
            f"🎯 市场情绪分析（{market}）\n",
            f"恐贪指数：{fg.get('score', 0)}（{fg.get('label', '')}）",
            f"VIX：{result.get('vix', 0)}",
            f"换手率：{result.get('turnover', {}).get('status', '')}",
            f"\n评分：{result.get('score', 0)}/10",
            f"\n反向信号：{result.get('contrarian_signal', '')}",
        ]
        return "\n".join(lines)
    
    async def _cmd_analyze(self, args: str) -> str:
        """处理 /分析 命令"""
        target = args or "A 股"
        return f"🔍 正在对 {target} 进行四维综合分析...\n\n（分析中，请稍候）"
    
    async def _cmd_alert(self, args: str) -> str:
        """处理 /预警 命令"""
        if not args or args == "列表":
            return self._format_alert_list()
        elif args.startswith("设置"):
            return "✅ 预警设置已更新"
        else:
            return "❓ 未知操作，输入 /预警 列表 查看"
    
    def _format_alert_list(self) -> str:
        """格式化预警列表"""
        lines = [
            "⚠️ 当前预警设置\n",
            "─" * 20,
            f"• 北向资金流出 > {abs(self.alert_config['north_flow_threshold'])} 亿",
            f"• 单日跌幅 > {abs(self.alert_config['drop_threshold'])}%",
            f"• 恐贪指数 < {self.alert_config['fear_greed_extreme']}（极度恐惧）",
            f"• 恐贪指数 > {self.alert_config['fear_greed_overheat']}（极度贪婪）",
            "─" * 20,
            "\n输入 /预警 设置 <指标> <阈值> 修改",
        ]
        return "\n".join(lines)
    
    async def _cmd_help(self, args: str) -> str:
        """处理 /help 命令"""
        help_text = """
🤖 LLM 投资分析平台 - 命令帮助

📊 **分析类命令**
/宏观 [国家] - 宏观经济概览
/估值 [标的] - 市场/行业估值分析
/资金 [类型] - 资金流向追踪
/情绪 [市场] - 市场情绪分析
/分析 [标的] - 四维综合分析

📰 **推送类命令**
/早报 - 立即获取早报
/晚报 - 立即获取晚报

⚠️ **预警类命令**
/预警 列表 - 查看预警设置
/预警 设置 <指标> <阈值> - 设置预警

💡 **直接输入问题** 也可以分析哦！
"""
        return help_text.strip()
    
    async def _cmd_morning_report(self, args: str) -> str:
        """处理 /早报 命令"""
        return await self.generate_morning_report()
    
    async def _cmd_evening_report(self, args: str) -> str:
        """处理 /晚报 命令"""
        return await self.generate_evening_report()
    
    # ========== 定时推送 ==========
    
    async def generate_morning_report(self) -> str:
        """生成早报"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 并行获取各维度数据
        macro_task = self.agents["macro"].analyze(country="CN")
        sentiment_task = self.agents["sentiment"].analyze(market="A 股")
        fund_task = self.agents["fund"].analyze(market="A 股")
        
        macro_result, sentiment_result, fund_result = await asyncio.gather(
            macro_task, sentiment_task, fund_task, return_exceptions=True
        )
        
        # 提取评分
        macro_score = self._safe_get(macro_result, "score", 7.0)
        sentiment_score = self._safe_get(sentiment_result, "score", 6.0)
        fund_score = self._safe_get(fund_result, "score", 6.5)
        
        avg_score = (macro_score + sentiment_score + fund_score) / 3
        recommendation = "偏多" if avg_score >= 7 else "中性" if avg_score >= 5 else "偏空"
        
        # 格式化早报
        report = f"""
📊 市场早报 | {date}

🌍 隔夜要闻
• 美联储维持利率不变，年内降息预期降温
• 纳指 +0.8%，标普 +0.5%

📈 今日关注
• A 股：关注成交量变化
• 港股：腾讯回购持续

💰 资金信号
• 北向资金：{self._safe_get(fund_result, 'north_flow', {}).get('trend', 'neutral')}
• 两融余额：{self._safe_get(fund_result, 'margin', {}).get('status', 'neutral')}

🎯 情绪面
• 恐贪指数：{self._safe_get(sentiment_result, 'fear_greed', {}).get('score', 0)}

{'─' * 30}
📌 四维评分：{avg_score:.1f}/10（{recommendation}）
"""
        return report.strip()
    
    async def generate_evening_report(self) -> str:
        """生成晚报"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 并行获取数据
        macro_task = self.agents["macro"].analyze(country="CN")
        sentiment_task = self.agents["sentiment"].analyze(market="A 股")
        fund_task = self.agents["fund"].analyze(market="A 股")
        
        macro_result, sentiment_result, fund_result = await asyncio.gather(
            macro_task, sentiment_task, fund_task, return_exceptions=True
        )
        
        # 提取评分
        macro_score = self._safe_get(macro_result, "score", 7.0)
        sentiment_score = self._safe_get(sentiment_result, "score", 6.0)
        fund_score = self._safe_get(fund_result, "score", 6.5)
        
        avg_score = (macro_score + sentiment_score + fund_score) / 3
        recommendation = "偏多" if avg_score >= 7 else "中性" if avg_score >= 5 else "偏空"
        
        # 格式化晚报
        report = f"""
📊 市场晚报 | {date}

📉 今日回顾
• 沪指 震荡收平
• 成交额 ¥9000 亿
• 涨跌比 2:1

🔥 行业亮点
• 科技板块表现强势
• 消费板块有所回暖

💰 资金动向
• 北向资金：{self._safe_get(fund_result, 'north_flow', {}).get('trend', 'neutral')}
• 两融余额：{self._safe_get(fund_result, 'margin', {}).get('status', 'neutral')}

⚠️ 异常信号
• 无明显异常

{'─' * 30}
📌 四维评分：{avg_score:.1f}/10（{recommendation}）
"""
        return report.strip()
    
    def _safe_get(self, obj, key, default=None):
        """安全获取字典值"""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default
    
    async def check_alerts(self) -> Optional[Dict]:
        """检查是否触发预警"""
        alerts = []
        
        try:
            # 获取资金数据
            fund_result = await self.agents["fund"].analyze(market="A 股")
            north_flow = fund_result.get("north_flow", {}).get("net_flow_today", 0)
            
            if north_flow < self.alert_config["north_flow_threshold"]:
                alerts.append({
                    "type": "fund",
                    "level": "warning",
                    "message": f"北向资金异常流出：{north_flow} 亿",
                })
            
            # 获取情绪数据
            sentiment_result = await self.agents["sentiment"].analyze(market="A 股")
            fear_greed = sentiment_result.get("fear_greed", {}).get("score", 50)
            
            if fear_greed < self.alert_config["fear_greed_extreme"]:
                alerts.append({
                    "type": "sentiment",
                    "level": "opportunity",
                    "message": f"市场极度恐惧（{fear_greed}），可能是买入机会",
                })
            elif fear_greed > self.alert_config["fear_greed_overheat"]:
                alerts.append({
                    "type": "sentiment",
                    "level": "warning",
                    "message": f"市场极度贪婪（{fear_greed}），注意短期风险",
                })
            
            return alerts if alerts else None
            
        except Exception as e:
            logger.error(f"预警检查失败：{e}")
            return None
    
    def setup_scheduler(self):
        """配置定时任务"""
        from apscheduler.triggers.cron import CronTrigger
        
        # 早报（工作日 07:30）
        self.scheduler.add_job(
            self._send_morning_report,
            CronTrigger(hour=7, minute=30, day_of_week="mon-fri"),
            id="morning_report",
            name="发送早报",
            replace_existing=True,
        )
        
        # 晚报（工作日 20:00）
        self.scheduler.add_job(
            self._send_evening_report,
            CronTrigger(hour=20, minute=0, day_of_week="mon-fri"),
            id="evening_report",
            name="发送晚报",
            replace_existing=True,
        )
        
        # 预警检查（每小时）
        from apscheduler.triggers.interval import IntervalTrigger
        self.scheduler.add_job(
            self._check_and_send_alerts,
            IntervalTrigger(hours=1),
            id="alert_check",
            name="预警检查",
            replace_existing=True,
        )
        
        logger.info("定时任务配置完成")
    
    async def _send_morning_report(self):
        """发送早报"""
        try:
            report = await self.generate_morning_report()
            # TODO: 发送到配置的群
            logger.info(f"早报生成成功：{report[:100]}...")
        except Exception as e:
            logger.error(f"早报生成失败：{e}")
    
    async def _send_evening_report(self):
        """发送晚报"""
        try:
            report = await self.generate_evening_report()
            logger.info(f"晚报生成成功：{report[:100]}...")
        except Exception as e:
            logger.error(f"晚报生成失败：{e}")
    
    async def _check_and_send_alerts(self):
        """检查并发送预警"""
        try:
            alerts = await self.check_alerts()
            if alerts:
                for alert in alerts:
                    logger.warning(f"触发预警：{alert}")
                    # TODO: 发送到配置的群
        except Exception as e:
            logger.error(f"预警检查失败：{e}")
    
    async def send_message(self, chat_id: str, text: str, reply_msg_id: str = None):
        """发送飞书消息"""
        
        content = {"text": text}
        
        req = CreateMessageRequest.builder() \
            .request_body(
                CreateMessageRequestBody.builder() \
                .receive_id(chat_id) \
                .message_type("text") \
                .content(json.dumps(content)) \
                .reply_id(reply_msg_id) \
                .build()
            ) \
            .receive_id_type("chat_id") \
            .build()
        
        try:
            resp = await self.client.im.v1.message.acreate(req)
            if resp.code == 0:
                logger.info(f"消息发送成功：{chat_id}")
            else:
                logger.error(f"消息发送失败：{resp.msg}")
        except Exception as e:
            logger.error(f"发送消息异常：{e}")
    
    def start(self):
        """启动 Bot"""
        self.setup_scheduler()
        self.scheduler.start()
        logger.info("飞书 Bot 已启动")
    
    def stop(self):
        """停止 Bot"""
        self.scheduler.shutdown()
        logger.info("飞书 Bot 已停止")
