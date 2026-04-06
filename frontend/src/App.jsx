import { useState } from 'react'
import axios from 'axios'

// Mock 数据
const mockAnalysisResults = {
    '宏观': {
        agent: 'macro_analyst',
        score: 7.2,
        data: {
            'GDP': '5.2% (+0.3%)',
            'CPI': '1.8% (-0.2%)',
            'PMI': '51.2 (+0.5)',
            '利率': '3.45% (-0.1%)',
        },
        analysis: '宏观经济整体稳定，PMI 连续 3 个月处于扩张区间（51.2），显示制造业景气度回升。CPI 温和（1.8%），货币政策空间充足。信用周期处于扩张早期，对股市形成支撑。',
    },
    '估值': {
        agent: 'valuation_analyst',
        score: 7.5,
        data: {
            '沪深 300 PE': '12.1x',
            '历史分位': '35%',
            '美股 SP500 PE': '22x',
            '行业对比': '科技 60% / 金融 15%',
        },
        analysis: '沪深 300 PE 12.1x，处于近 5 年 35% 分位，估值合理偏低。相比美股（SP500 PE 22x）有显著折价。行业分化明显：科技板块略贵（60% 分位），金融板块便宜（15% 分位）。',
    },
    '资金': {
        agent: 'fund_tracker',
        score: 6.5,
        data: {
            '北向资金': '+¥120 亿/周',
            '两融余额': '¥1.82 万亿',
            '新基金发行': '低迷',
            '主力流向': '半导体+新能源',
        },
        analysis: '北向资金连续 3 日净流入，本周累计 ¥120 亿，释放积极信号。两融余额环比 +2%，杠杆资金开始入场。新基金发行仍低迷，符合底部特征。',
    },
    '情绪': {
        agent: 'sentiment_analyst',
        score: 6.0,
        data: {
            '恐贪指数': '45（中性）',
            'VIX': '18.5（低位）',
            '换手率': '偏低',
            '市场热度': '低（非过热）',
        },
        analysis: '恐贪指数 45（中性区域），VIX 处于低位（18.5），市场波动率不高。换手率偏低，社交媒体讨论度低，非过热信号。',
    },
}

// 雷达图数据
const radarData = [
    { subject: '基本面', A: 7.2, fullMark: 10 },
    { subject: '估值', A: 7.5, fullMark: 10 },
    { subject: '资金', A: 6.5, fullMark: 10 },
    { subject: '情绪', A: 6.0, fullMark: 10 },
]

function App() {
    const [query, setQuery] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState('all')

    const analyzeQuery = (text) => {
        let intents = []
        if (text.includes('宏观') || text.includes('经济')) intents.push('宏观')
        if (text.includes('估值') || text.includes('PE')) intents.push('估值')
        if (text.includes('资金') || text.includes('北向')) intents.push('资金')
        if (text.includes('情绪') || text.includes('恐慌')) intents.push('情绪')
        if (intents.length === 0 || text.includes('全面') || text.includes('适合买')) {
            intents = ['宏观', '估值', '资金', '情绪']
        }
        return intents
    }

    const handleAnalyze = async () => {
        if (!query.trim()) return
        setLoading(true)
        await new Promise(r => setTimeout(r, 1500))
        const intents = analyzeQuery(query)
        const results = intents.map(key => ({...mockAnalysisResults[key], title: key}))
        const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length
        const compositeScore = avgScore.toFixed(1)
        const recommendation = avgScore >= 7 ? '偏多' : avgScore >= 5 ? '中性' : '偏空'
        const position = avgScore >= 7 ? '60-70%' : avgScore >= 5 ? '40-50%' : '20-30%'
        const positionLevel = avgScore >= 7 ? '标准仓位' : avgScore >= 5 ? '轻仓' : '观望'
        setResult({ query, intents, results, compositeScore, recommendation, position, positionLevel })
        setLoading(false)
    }

    const filteredResults = activeTab === 'all' ? result?.results : result?.results?.filter(r => r.title === activeTab)

    const icons = { '宏观': '🌍', '估值': '📈', '资金': '💰', '情绪': '🎯' }
    const names = { '宏观': '宏观分析师', '估值': '估值分析师', '资金': '资金流追踪', '情绪': '情绪分析师' }

    // 渲染评分仪表盘
    const renderGauge = (score) => {
        const rotation = (score / 10) * 180 - 90
        const color = score >= 7 ? '#22c55e' : score >= 5 ? '#eab308' : '#ef4444'
        return `
            <svg viewBox="0 0 100 60" class="w-32 h-24">
                <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#e5e7eb" stroke-width="8" stroke-linecap="round"/>
                <path d="M 10 50 A 40 40 0 0 1 ${50 + 40 * Math.cos((rotation - 90) * Math.PI / 180)} ${50 + 40 * Math.sin((rotation - 90) * Math.PI / 180)}" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"/>
                <text x="50" y="50" text-anchor="middle" class="text-xl font-bold" fill="${color}">${score}</text>
            </svg>
        `
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-8">
            <div className="max-w-6xl mx-auto">
                {/* 标题 */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">🦞 LLM 投资分析平台</h1>
                    <p className="text-blue-300">AI 驱动的四维投资分析系统 · 模拟机构级分析流程</p>
                </div>

                {/* 输入区域 */}
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-8 border border-white/20">
                    <div className="flex gap-4">
                        <input type="text" value={query} onChange={e => setQuery(e.target.value)}
                            onKeyPress={e => e.key === 'Enter' && handleAnalyze()}
                            placeholder="输入问题，如：现在适合买入 A 股吗？"
                            className="flex-1 px-5 py-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"/>
                        <button onClick={handleAnalyze} disabled={loading}
                            className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-bold hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 transition-all">
                            {loading ? '🤖 分析中...' : '✨ 分析'}
                        </button>
                    </div>
                </div>

                {result && (
                    <div className="space-y-6">
                        {/* 综合评分卡片 */}
                        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-2xl">
                            <div className="grid md:grid-cols-3 gap-8">
                                <div className="text-center">
                                    <h2 className="text-lg text-white/80 mb-4">四维综合评分</h2>
                                    <div className="text-6xl font-bold mb-2">{result.compositeScore}</div>
                                    <div className="text-2xl">/ 10</div>
                                </div>
                                <div className="text-center">
                                    <h2 className="text-lg text-white/80 mb-4">市场判断</h2>
                                    <div className={`text-4xl font-bold px-6 py-3 rounded-xl inline-block ${result.recommendation === '偏多' ? 'bg-green-500' : result.recommendation === '中性' ? 'bg-yellow-500' : 'bg-red-500'}`}>
                                        {result.recommendation}
                                    </div>
                                </div>
                                <div className="text-center">
                                    <h2 className="text-lg text-white/80 mb-4">建议仓位</h2>
                                    <div className="text-4xl font-bold mb-2">{result.position}</div>
                                    <div className="text-xl text-white/80">{result.positionLevel}</div>
                                </div>
                            </div>
                        </div>

                        {/* 雷达图 + 评分条 */}
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* 四维评分条 */}
                            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                                <h3 className="text-xl font-bold text-white mb-6">📊 四维评分</h3>
                                <div className="space-y-4">
                                    {result.results.map(r => (
                                        <div key={r.title} className="flex items-center gap-4">
                                            <span className="text-2xl">{icons[r.title]}</span>
                                            <span className="w-20 text-white font-medium">{r.title}</span>
                                            <div className="flex-1 bg-gray-700 rounded-full h-4 overflow-hidden">
                                                <div className="h-full rounded-full transition-all duration-1000" 
                                                    style={{width: `${r.score * 10}%`, backgroundColor: r.score >= 7 ? '#22c55e' : r.score >= 5 ? '#eab308' : '#ef4444'}}></div>
                                            </div>
                                            <span className="w-12 text-right text-white font-bold">{r.score}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* 风控建议 */}
                            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                                <h3 className="text-xl font-bold text-white mb-6">⚠️ 风控建议</h3>
                                <ul className="space-y-3 text-white/90">
                                    <li className="flex items-start gap-3">
                                        <span className="text-yellow-400">•</span>
                                        <span>重点关注：科技 + 消费板块（基本面改善 + 估值合理）</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="text-yellow-400">•</span>
                                        <span>策略：分批建仓，减少择时风险</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="text-red-400">⚠️</span>
                                        <span>关注：美联储议息会议，可能引发全球波动</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="text-red-400">⚠️</span>
                                        <span>关注：地缘政治风险，可能影响市场</span>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        {/* Tab 切换 */}
                        <div className="flex gap-2">
                            <button onClick={() => setActiveTab('all')} className={`px-4 py-2 rounded-lg font-medium ${activeTab === 'all' ? 'bg-blue-500 text-white' : 'bg-white/10 text-white/70 hover:bg-white/20'}`}>全部</button>
                            {['宏观', '估值', '资金', '情绪'].map(tab => (
                                <button key={tab} onClick={() => setTab(tab)} className={`px-4 py-2 rounded-lg font-medium ${activeTab === tab ? 'bg-blue-500 text-white' : 'bg-white/10 text-white/70 hover:bg-white/20'}`}>{tab}</button>
                            ))}
                        </div>

                        {/* Agent 分析卡片 */}
                        {filteredResults?.map((r, idx) => (
                            <div key={idx} className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className="text-3xl">{icons[r.title]}</span>
                                        <h3 className="text-xl font-bold text-white">{names[r.title]}</h3>
                                    </div>
                                    <span className="px-4 py-2 bg-green-500/20 text-green-400 rounded-full font-bold">评分：{r.score}/10</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                                    {Object.entries(r.data).map(([k, v]) => (
                                        <div key={k} className="bg-white/5 rounded-xl p-3">
                                            <div className="text-xs text-white/50 mb-1">{k}</div>
                                            <div className="text-white font-medium">{v}</div>
                                        </div>
                                    ))}
                                </div>
                                <p className="text-white/80 leading-relaxed">{r.analysis}</p>
                            </div>
                        ))}
                    </div>
                )}

                {/* 快捷示例 */}
                <div className="mt-8">
                    <h3 className="text-sm font-medium text-white/50 mb-3">🚀 快捷示例</h3>
                    <div className="flex flex-wrap gap-2">
                        {['现在适合买入 A 股吗？', '分析一下当前宏观环境', '沪深 300 估值如何？', '北向资金最近流向'].map(q => (
                            <button key={q} onClick={() => setQuery(q)} className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 text-white/70 rounded-full transition-colors">{q}</button>
                        ))}
                    </div>
                </div>

                {/* 页脚 */}
                <div className="mt-12 text-center text-sm text-white/40">
                    <p>MVP 版本 · Phase 1 Week 4 · 已完成 12 周中的 3 周</p>
                </div>
            </div>
        </div>
    )
}

export default App
