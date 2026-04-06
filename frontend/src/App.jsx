import { useState } from 'react'
import axios from 'axios'

// Mock 数据 - 用于演示
const mockAnalysisResults = {
  '宏观': {
    agent: 'macro_analyst',
    score: 7.2,
    data: {
      'GDP': { value: '5.2%', yoy: '+0.3%', trend: 'stable' },
      'CPI': { value: '1.8%', yoy: '-0.2%', trend: 'down' },
      'PMI': { value: '51.2', yoy: '+0.5', trend: 'up' },
      '利率': { value: '3.45%', yoy: '-0.1%', trend: 'stable' },
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
      '行业对比': '科技 60% 分位（偏贵），金融 15% 分位（便宜）',
    },
    analysis: '沪深 300 PE 12.1x，处于近 5 年 35% 分位，估值合理偏低。相比美股（SP500 PE 22x）有显著折价。行业分化明显：科技板块略贵（60% 分位），金融板块便宜（15% 分位）。',
  },
  '资金': {
    agent: 'fund_tracker',
    score: 6.5,
    data: {
      '北向资金': '本周净流入 ¥120 亿',
      '两融余额': '¥1.82 万亿（+0.3%）',
      '新基金发行': '低迷（底部特征）',
      '主力流向': '半导体 + 新能源获加仓',
    },
    analysis: '北向资金连续 3 日净流入，本周累计 ¥120 亿，释放积极信号。两融余额环比 +2%，杠杆资金开始入场。新基金发行仍低迷，符合底部特征。',
  },
  '情绪': {
    agent: 'sentiment_analyst',
    score: 6.0,
    data: {
      '恐贪指数': '45（偏恐惧）',
      'VIX': '18.5（低位）',
      '换手率': '偏低',
      '社交媒体热度': '低（非过热）',
    },
    analysis: '恐贪指数 45（偏恐惧区域），通常是反向做多信号。VIX 处于低位（18.5），市场波动率不高。换手率偏低，社交媒体讨论度低，显示市场参与度不高，非过热信号。',
  },
}

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('all')

  const analyzeQuery = (text) => {
    // 简单的意图识别
    let intents = []
    if (text.includes('宏观') || text.includes('经济') || text.includes('GDP') || text.includes('CPI')) {
      intents.push('宏观')
    }
    if (text.includes('估值') || text.includes('PE') || text.includes('贵') || text.includes('便宜')) {
      intents.push('估值')
    }
    if (text.includes('资金') || text.includes('北向') || text.includes('两融')) {
      intents.push('资金')
    }
    if (text.includes('情绪') || text.includes('恐慌') || text.includes('贪婪')) {
      intents.push('情绪')
    }
    
    // 默认触发全部
    if (intents.length === 0 || text.includes('全面') || text.includes('适合买') || text.includes('适合卖')) {
      intents = ['宏观', '估值', '资金', '情绪']
    }
    
    return intents
  }

  const handleAnalyze = async () => {
    if (!query.trim()) return
    
    setLoading(true)
    
    // 模拟 API 调用延迟
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const intents = analyzeQuery(query)
    const results = intents.map(key => ({
      ...mockAnalysisResults[key],
      title: key,
    }))
    
    // 计算综合评分
    const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length
    
    setResult({
      query,
      intents,
      results,
      compositeScore: avgScore.toFixed(1),
      recommendation: avgScore >= 7 ? '偏多' : avgScore >= 5 ? '中性' : '偏空',
    })
    
    setLoading(false)
  }

  const quickExamples = [
    '现在适合买入 A 股吗？',
    '分析一下当前宏观环境',
    '沪深 300 估值如何？',
    '北向资金最近流向',
  ]

  const filteredResults = activeTab === 'all' 
    ? result?.results 
    : result?.results.filter(r => r.title === activeTab)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-5xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🦞 LLM 投资分析平台
          </h1>
          <p className="text-gray-600">
            AI 驱动的四维投资分析系统 · 模拟机构级分析流程
          </p>
        </div>

        {/* 输入区域 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            💬 请输入你的问题
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="例如：现在适合买入 A 股吗？ / 分析一下当前宏观环境"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium text-lg"
            >
              {loading ? '🤖 分析中...' : '✨ 分析'}
            </button>
          </div>
        </div>

        {/* 结果展示 */}
        {result && (
          <div className="space-y-6">
            {/* 综合评分卡片 */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">📊 四维综合评分</h2>
                  <p className="text-blue-100">基于宏观、估值、资金、情绪四个维度</p>
                </div>
                <div className="text-right">
                  <div className="text-5xl font-bold mb-2">{result.compositeScore}/10</div>
                  <div className={`text-xl font-medium px-4 py-2 rounded-full ${
                    result.recommendation === '偏多' ? 'bg-green-400' :
                    result.recommendation === '中性' ? 'bg-yellow-400' : 'bg-red-400'
                  }`}>
                    {result.recommendation}
                  </div>
                </div>
              </div>
            </div>

            {/* Tab 切换 */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap ${
                  activeTab === 'all' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                全部
              </button>
              {['宏观', '估值', '资金', '情绪'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap ${
                    activeTab === tab 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Agent 分析卡片 */}
            {filteredResults?.map((r, idx) => (
              <div key={idx} className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">
                      {r.title === '宏观' ? '🌍' :
                       r.title === '估值' ? '📈' :
                       r.title === '资金' ? '💰' : '🎯'}
                    </span>
                    <h3 className="text-xl font-semibold text-gray-900">
                      {r.title === '宏观' ? '宏观分析师' :
                       r.title === '估值' ? '估值分析师' :
                       r.title === '资金' ? '资金流追踪' : '情绪分析师'}
                    </h3>
                  </div>
                  <span className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-full font-medium">
                    评分：{r.score}/10
                  </span>
                </div>

                {/* 数据展示 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {Object.entries(r.data).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">{key}</div>
                      <div className="text-sm font-medium text-gray-900">{value}</div>
                    </div>
                  ))}
                </div>

                {/* 分析文字 */}
                <p className="text-gray-700 leading-relaxed">{r.analysis}</p>
              </div>
            ))}

            {/* 风控建议 */}
            {activeTab === 'all' && (
              <div className="bg-amber-50 border-l-4 border-amber-400 rounded-lg p-6">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div>
                    <h3 className="font-semibold text-amber-900 mb-2">风控经理建议</h3>
                    <ul className="text-amber-800 space-y-1">
                      <li>• 建议仓位：{result.compositeScore >= 7 ? '60-70%（标准仓位）' : result.compositeScore >= 5 ? '40-50%（轻仓）' : '20-30%（观望）'}</li>
                      <li>• 重点关注：科技 + 消费板块（基本面改善 + 估值合理）</li>
                      <li>• 风险提示：关注美联储议息会议，可能引发短期波动</li>
                      <li>• 策略：分批建仓，避免一次性重仓</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 快捷示例 */}
        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-500 mb-3">🚀 快捷示例（点击试试）</h3>
          <div className="flex flex-wrap gap-2">
            {quickExamples.map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="px-4 py-2 text-sm bg-white hover:bg-blue-50 border border-gray-200 rounded-full transition-colors text-gray-700"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {/* 页脚 */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>MVP 版本 · Week 1 开发完成</p>
          <p className="mt-1">设计文档：<a href="https://www.feishu.cn/docx/R5KXdLd1doGKKdxMXJ4cJIhynbd" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">查看</a></p>
        </div>
      </div>
    </div>
  )
}

export default App
