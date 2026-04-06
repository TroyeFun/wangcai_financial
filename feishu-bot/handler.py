"""
飞书 Bot 服务

处理飞书消息事件，支持命令交互和定时推送
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import hashlib
import base64
import json
import hmac
import os
from typing import Dict, Any

from lark_oapi.api.im.v1 import *
from lark_oapi.const import *
from lark_oapi.client import Client


app = FastAPI(title="Investment Analysis Feishu Bot")

# 配置
APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

# 初始化飞书客户端
client = Client.builder() \
    .app_id(APP_ID) \
    .app_secret(APP_SECRET) \
    .log_level("INFO") \
    .build()


def verify_signature(timestamp: str, nonce: str, signature: str, body: str) -> bool:
    """验证飞书请求签名"""
    if not VERIFICATION_TOKEN:
        return True
    
    sign_str = timestamp + nonce + VERIFICATION_TOKEN + body
    signature_computed = base64.b64encode(
        hmac.new(sign_str.encode(), digestmod=hashlib.sha256).digest()
    ).decode()
    
    return signature == signature_computed


@app.post("/feishu/event")
async def feishu_event(request: Request):
    """处理飞书事件（包括 URL 验证和消息接收）"""
    
    body = await request.body()
    headers = request.headers
    
    # 获取验证参数
    timestamp = headers.get("X-Lark-Request-Timestamp", "")
    nonce = headers.get("X-Lark-Request-Nonce", "")
    signature = headers.get("X-Lark-Signature", "")
    
    # 验证签名
    if not verify_signature(timestamp, nonce, signature, body.decode()):
        logger.warning("签名验证失败")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 解析请求体
    try:
        data = json.loads(body)
    except Exception as e:
        logger.error(f"解析请求体失败：{e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # URL 验证（飞书首次配置时需要）
    if data.get("type") == "url_verification":
        challenge = data.get("challenge", "")
        logger.info(f"URL 验证挑战：{challenge}")
        return {"challenge": challenge}
    
    # 处理消息事件
    if data.get("header", {}).get("event_type") == "im.message.receive_v1":
        return await handle_message(data)
    
    # 其他事件
    logger.info(f"收到其他事件：{data.get('header', {}).get('event_type')}")
    return JSONResponse({"status": "ok"})


async def handle_message(event_data: Dict[str, Any]) -> JSONResponse:
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
        return JSONResponse({"status": "ok"})
    
    # 忽略机器人自己的消息
    if sender.get("sender_type") == "bot":
        return JSONResponse({"status": "ok"})
    
    # 处理命令
    if text.startswith("/"):
        return await handle_command(text, chat_id, msg_id)
    
    # 普通对话，调用分析接口
    return await analyze_and_reply(text, chat_id, msg_id)


async def handle_command(command: str, chat_id: str, reply_msg_id: str) -> JSONResponse:
    """处理飞书命令"""
    
    parts = command.strip().split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    logger.info(f"处理命令：{cmd}, 参数：{args}")
    
    # 命令路由
    command_handlers = {
        "/宏观": handle_macro_command,
        "/估值": handle_valuation_command,
        "/资金": handle_fundflow_command,
        "/情绪": handle_sentiment_command,
        "/分析": handle_analyze_command,
        "/预警": handle_warning_command,
        "/help": handle_help_command,
    }
    
    handler = command_handlers.get(cmd)
    if handler:
        response_text = await handler(args)
    else:
        response_text = f"❓ 未知命令：{cmd}\n\n输入 /help 查看可用命令"
    
    # 回复消息
    await send_message(chat_id, response_text, reply_msg_id)
    
    return JSONResponse({"status": "ok"})


async def handle_macro_command(args: list) -> str:
    """处理 /宏观 命令"""
    country = args[0] if args else "中国"
    return f"📊 宏观经济概览（{country}）\n\n正在获取数据，请稍候..."


async def handle_valuation_command(args: list) -> str:
    """处理 /估值 命令"""
    symbol = " ".join(args) if args else "沪深 300"
    return f"📈 估值分析：{symbol}\n\n正在计算估值分位..."


async def handle_fundflow_command(args: list) -> str:
    """处理 /资金 命令"""
    flow_type = args[0] if args else "北向"
    return f"💰 资金流向：{flow_type}\n\n正在获取最新数据..."


async def handle_sentiment_command(args: list) -> str:
    """处理 /情绪 命令"""
    market = args[0] if args else "A 股"
    return f"🎯 市场情绪：{market}\n\n正在分析情绪指标..."


async def handle_analyze_command(args: list) -> str:
    """处理 /分析 命令"""
    target = " ".join(args) if args else "A 股"
    return f"🔍 四维综合分析：{target}\n\n正在调用多个 Agent 进行分析..."


async def handle_warning_command(args: list) -> str:
    """处理 /预警 命令"""
    if not args or args[0] == "列表":
        return "⚠️ 当前预警设置\n\n· 北向资金异常流出 > ¥50 亿\n· 单日跌幅 > 3%\n\n输入 /预警 设置 <指标> <阈值> 修改"
    elif args[0] == "设置":
        return "✅ 预警设置已更新"
    else:
        return "❓ 未知操作，输入 /预警 列表 查看当前设置"


async def handle_help_command(args: list) -> str:
    """处理 /help 命令"""
    help_text = """
🤖 LLM 投资分析平台 - 命令帮助

**分析类命令：**
/宏观 [国家] - 宏观经济概览
/估值 [标的] - 市场/行业估值分析
/资金 [类型] - 资金流向追踪
/情绪 [市场] - 市场情绪分析
/分析 [标的] - 四维综合分析

**预警类命令：**
/预警 列表 - 查看预警设置
/预警 设置 <指标> <阈值> - 设置预警

**其他：**
/help - 显示此帮助信息

**示例：**
/宏观 中国
/估值 沪深 300
/分析 A 股 现在适合买入吗？

直接输入自然语言问题也可以哦～
"""
    return help_text.strip()


async def analyze_and_reply(text: str, chat_id: str, reply_msg_id: str):
    """调用后端分析接口并回复"""
    
    # TODO: 调用后端 API 进行分析
    # 这里先返回示例响应
    response_text = f"""
🦞 收到你的问题：{text}

正在调用 AI Agent 进行分析...
（MVP 版本，完整功能开发中）
"""
    
    await send_message(chat_id, response_text, reply_msg_id)
    
    return JSONResponse({"status": "ok"})


async def send_message(chat_id: str, text: str, reply_msg_id: str = None):
    """发送飞书消息"""
    
    content = {
        "text": text
    }
    
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
        resp = await client.im.v1.message.acreate(req)
        if resp.code == 0:
            logger.info(f"消息发送成功：{chat_id}")
        else:
            logger.error(f"消息发送失败：{resp.msg}")
    except Exception as e:
        logger.error(f"发送消息异常：{e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
