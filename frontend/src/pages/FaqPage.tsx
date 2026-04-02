import { useState } from 'react'

interface FaqItem {
  id: number
  question: string
  answer: string
  category: string
}

const SAMPLE_FAQS: FaqItem[] = [
  { id: 1, question: '门店地址在哪里？', answer: '我们位于市中心XX路XX号，欢迎预约到店体验。', category: '门店信息' },
  { id: 2, question: '营业时间是？', answer: '周一至周日 10:00 - 21:00，法定节假日正常营业。', category: '门店信息' },
  { id: 3, question: '如何预约服务？', answer: '可通过企业微信直接联系顾问预约，或拨打门店电话。', category: '预约服务' },
]

const CATEGORY_COLORS: Record<string, string> = {
  '门店信息': '#6366f1',
  '预约服务': '#10b981',
  '价格咨询': '#f59e0b',
  '售后服务': '#ef4444',
  '其他': '#6b7280',
}

export default function FaqPage() {
  const [faqs, setFaqs] = useState<FaqItem[]>(SAMPLE_FAQS)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [category, setCategory] = useState('门店信息')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const filtered = faqs.filter(
    (f) =>
      f.question.includes(search) ||
      f.answer.includes(search) ||
      f.category.includes(search)
  )

  const handleAdd = () => {
    if (!question.trim() || !answer.trim()) return
    setFaqs([...faqs, { id: Date.now(), question: question.trim(), answer: answer.trim(), category }])
    setQuestion('')
    setAnswer('')
    setShowForm(false)
  }

  const handleDelete = (id: number) => {
    if (!confirm('确认删除该条目？')) return
    setFaqs(faqs.filter((f) => f.id !== id))
  }

  return (
    <div style={{ padding: 32 }}>
      {/* 头部 */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>FAQ 知识库</h2>
          <p style={{ fontSize: 14, color: '#6b7280' }}>管理常见问题，提升客服回复效率</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: '10px 20px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none',
            borderRadius: 10,
            color: '#fff',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {showForm ? '取消' : '+ 新增条目'}
        </button>
      </div>

      {/* 新增表单 */}
      {showForm && (
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: 16,
          padding: 24,
          marginBottom: 20,
          boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
        }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#374151', marginBottom: 16 }}>新增 FAQ 条目</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, color: '#374151', fontWeight: 500, marginBottom: 6 }}>问题</label>
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="输入常见问题..."
                style={{
                  width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb',
                  borderRadius: 8, fontSize: 14, outline: 'none', boxSizing: 'border-box',
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, color: '#374151', fontWeight: 500, marginBottom: 6 }}>分类</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb',
                  borderRadius: 8, fontSize: 14, outline: 'none', background: '#fff', boxSizing: 'border-box',
                }}
              >
                {['门店信息', '预约服务', '价格咨询', '售后服务', '其他'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, color: '#374151', fontWeight: 500, marginBottom: 6 }}>回答</label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={3}
              placeholder="输入标准回答..."
              style={{
                width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb',
                borderRadius: 8, fontSize: 14, outline: 'none', resize: 'none', boxSizing: 'border-box',
              }}
            />
          </div>
          <button
            onClick={handleAdd}
            style={{
              padding: '10px 24px', background: '#6366f1', border: 'none',
              borderRadius: 8, color: '#fff', fontSize: 14, fontWeight: 500, cursor: 'pointer',
            }}
          >
            保存
          </button>
        </div>
      )}

      {/* 搜索 */}
      <div style={{ position: 'relative', marginBottom: 20 }}>
        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af', fontSize: 16 }}>🔍</span>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索问题、回答或分类..."
          style={{
            width: '100%', padding: '10px 12px 10px 38px', border: '1px solid #e5e7eb',
            borderRadius: 10, fontSize: 14, outline: 'none', background: '#fff', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* 统计 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <span style={{ fontSize: 13, color: '#6b7280', background: '#f3f4f6', padding: '4px 12px', borderRadius: 20 }}>
          共 {faqs.length} 条
        </span>
        {search && (
          <span style={{ fontSize: 13, color: '#6366f1', background: '#eef2ff', padding: '4px 12px', borderRadius: 20 }}>
            搜索到 {filtered.length} 条
          </span>
        )}
      </div>

      {/* FAQ 列表 */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af', fontSize: 14 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
          暂无匹配的 FAQ 条目
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map((faq) => (
            <div
              key={faq.id}
              style={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: 12,
                overflow: 'hidden',
                boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
              }}
            >
              <div
                onClick={() => setExpandedId(expandedId === faq.id ? null : faq.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '14px 18px', cursor: 'pointer',
                }}
              >
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                  background: `${CATEGORY_COLORS[faq.category] ?? '#6b7280'}18`,
                  color: CATEGORY_COLORS[faq.category] ?? '#6b7280',
                  flexShrink: 0,
                }}>
                  {faq.category}
                </span>
                <p style={{ flex: 1, fontSize: 14, fontWeight: 500, color: '#1f2937', margin: 0 }}>
                  {faq.question}
                </p>
                <span style={{ color: '#9ca3af', fontSize: 12, flexShrink: 0 }}>
                  {expandedId === faq.id ? '▲' : '▼'}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(faq.id) }}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: '#ef4444', fontSize: 13, flexShrink: 0,
                  }}
                >
                  删除
                </button>
              </div>
              {expandedId === faq.id && (
                <div style={{
                  padding: '12px 18px 16px',
                  borderTop: '1px solid #f3f4f6',
                  background: '#fafafa',
                  fontSize: 14, color: '#374151', lineHeight: 1.6,
                }}>
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
