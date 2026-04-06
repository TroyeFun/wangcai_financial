"""
飞书 Bot 启动脚本

Usage:
    python run.py                    # 启动 Bot
    python run.py --morning-report   # 生成并打印早报
    python run.py --evening-report   # 生成并打印晚报
    python run.py --test            # 测试模式（不发送消息）
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_bot.bot import FeishuBot


async def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        bot = FeishuBot()
        
        if cmd == "--morning-report":
            report = await bot.generate_morning_report()
            print(report)
        
        elif cmd == "--evening-report":
            report = await bot.generate_evening_report()
            print(report)
        
        elif cmd == "--test":
            print("🧪 测试模式")
            print("-" * 30)
            
            # 测试各 Agent
            print("🌍 测试宏观分析师...")
            result = await bot.agents["macro"].analyze(country="CN")
            print(f"  评分：{result.get('score', 0)}/10")
            
            print("📈 测试估值分析师...")
            result = await bot.agents["valuation"].analyze(symbol="000300.SH", market="A 股")
            print(f"  评分：{result.get('score', 0)}/10")
            
            print("💰 测试资金流追踪...")
            result = await bot.agents["fund"].analyze(market="A 股")
            print(f"  评分：{result.get('score', 0)}/10")
            
            print("🎯 测试情绪分析师...")
            result = await bot.agents["sentiment"].analyze(market="A 股")
            print(f"  评分：{result.get('score', 0)}/10")
            
            print("⚠️ 测试风控经理...")
            result = await bot.agents["risk"].analyze()
            print(f"  综合评分：{result.get('composite_score', 0)}/10")
            
            print("-" * 30)
            print("✅ 测试完成！")
        
        elif cmd == "--alerts":
            print("🔍 检查预警...")
            alerts = await bot.check_alerts()
            if alerts:
                for alert in alerts:
                    print(f"  ⚠️ {alert}")
            else:
                print("  ✅ 无预警")
        
        else:
            print(f"未知命令：{cmd}")
            print("可用命令：--morning-report, --evening-report, --test, --alerts")
    
    else:
        # 启动 Bot
        print("🚀 启动飞书 Bot...")
        bot = FeishuBot()
        bot.start()
        
        try:
            # 保持运行
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("\n👋 Bot 停止")
            bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
