import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface CustomerListResponse {
  data: { count: number; customers: { last_updated: number; message_count: number }[] }
}

const CARD_STYLES = [
  { bg: 'linear-gradient(135deg, #6366f1, #8b5cf6)', icon: '👥' },
  { bg: 'linear-gradient(135deg, #0ea5e9, #38bdf8)', icon: '💬' },
  { bg: 'linear-gradient(135deg, #10b981, #34d399)', icon: '📣' },
]

export default function DashboardPage() {
  const navigate = useNavigate()
  const [totalCustomers, setTotalCustomers] = useState<number | null>(null)
  const [totalMessages, setTotalMessages] = useState<number | null>(null)
  const [todayActive, setTodayActive] = useState<number | null>(null)

  useEffect(() => {
    api
      .get<CustomerListResponse>('/api/customers')
      .then((res) => {
        const customers = res.data.customers
        setTotalCustomers(customers.length)
        setTotalMessages(customers.reduce((sum, c) => sum + (c.message_count || 0), 0))
        const todayStart = new Date().setHours(0, 0, 0, 0) / 1000
        setTodayActive(customers.filter((c) => c.last_updated >= todayStart).length)
      })
      .catch(() => {
        setTotalCustomers(0)
        setTotalMessages(0)
        setTodayActive(0)
      })
  }, [])

  const stats = [
    { label: '客户总数', value: totalCustomers, sub: '有对话记录' },
    { label: '消息总量', value: totalMessages, sub: '所有会话消息' },
    { label: '今日活跃', value: todayActive, sub: '今日有新消息' },
  ]

  return (
    <div style={{ padding: 32 }}>
      {/* 头部 */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>仪表盘</h2>
        <p style={{ fontSize: 14, color: '#6b7280' }}>
          {new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-6" style={{ marginBottom: 28 }}>
        {stats.map(({ label, value, sub }, i) => (
          <div
            key={label}
            style={{
              borderRadius: 16,
              background: CARD_STYLES[i].bg,
              padding: '24px 24px',
              color: '#fff',
              boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 12 }}>{CARD_STYLES[i].icon}</div>
            <p style={{ fontSize: 36, fontWeight: 700, lineHeight: 1, marginBottom: 6 }}>
              {value === null ? '…' : value}
            </p>
            <p style={{ fontSize: 14, fontWeight: 500, opacity: 0.9, marginBottom: 2 }}>{label}</p>
            <p style={{ fontSize: 12, opacity: 0.6 }}>{sub}</p>
            <div
              style={{
                position: 'absolute', right: -20, bottom: -20,
                width: 100, height: 100, borderRadius: '50%',
                background: 'rgba(255,255,255,0.1)',
              }}
            />
          </div>
        ))}
      </div>

      {/* 快捷入口 */}
      <div style={{ marginBottom: 8 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: '#374151', marginBottom: 14 }}>快捷操作</h3>
        <div style={{ display: 'flex', gap: 12 }}>
          {[
            { label: '查看客户列表', to: '/customers', color: '#6366f1', icon: '👥' },
            { label: '立即发送关怀', to: '/proactive', color: '#10b981', icon: '📣' },
          ].map(({ label, to, color, icon }) => (
            <button
              key={to}
              onClick={() => navigate(to)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '12px 20px',
                background: '#fff',
                border: `1.5px solid ${color}22`,
                borderRadius: 12,
                cursor: 'pointer',
                fontSize: 14,
                color: color,
                fontWeight: 500,
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                transition: 'all 0.15s',
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = `${color}0d`)}
              onMouseOut={(e) => (e.currentTarget.style.background = '#fff')}
            >
              <span style={{ fontSize: 18 }}>{icon}</span>
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
