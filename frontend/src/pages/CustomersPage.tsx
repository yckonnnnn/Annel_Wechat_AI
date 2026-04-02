import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface CustomerSummary {
  external_userid: string
  name: string
  avatar: string
  corp_name: string
  message_count: number
  last_updated: number
}

interface CustomerListResponse {
  data: { count: number; customers: CustomerSummary[] }
}

function formatTime(ts: number): string {
  if (!ts) return '-'
  const d = new Date(ts * 1000)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const AVATAR_COLORS = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
const avatarColor = (id: string) => AVATAR_COLORS[id.charCodeAt(id.length - 1) % AVATAR_COLORS.length]

export default function CustomersPage() {
  const navigate = useNavigate()
  const [customers, setCustomers] = useState<CustomerSummary[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    const qs = search ? `?search=${encodeURIComponent(search)}` : ''
    api
      .get<CustomerListResponse>(`/api/customers${qs}`)
      .then((res) => setCustomers(res.data.customers))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [search])

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>客户管理</h2>
          <p style={{ fontSize: 14, color: '#6b7280' }}>{customers.length} 位客户</p>
        </div>
      </div>

      {/* 搜索框 */}
      <div style={{ position: 'relative', marginBottom: 20, maxWidth: 400 }}>
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2"
          style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
        >
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          type="text"
          placeholder="搜索客户姓名或 ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', padding: '10px 14px 10px 40px',
            background: '#fff',
            border: '1.5px solid #e5e7eb',
            borderRadius: 10, fontSize: 14, outline: 'none',
            boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          }}
        />
      </div>

      {error && (
        <div style={{ marginBottom: 16, padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 10, color: '#ef4444', fontSize: 14 }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af', fontSize: 14 }}>加载中...</div>
      ) : customers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9ca3af', fontSize: 14 }}>
          {search ? '没有匹配的客户' : '暂无客户对话记录'}
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e5e7eb', overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
          {customers.map((c, i) => (
            <button
              key={c.external_userid}
              onClick={() => navigate(`/customers/${c.external_userid}`)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center',
                padding: '14px 20px',
                background: 'transparent',
                border: 'none',
                borderBottom: i < customers.length - 1 ? '1px solid #f3f4f6' : 'none',
                cursor: 'pointer', textAlign: 'left',
                transition: 'background 0.12s',
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = '#f9fafb')}
              onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              {c.avatar ? (
                <img src={c.avatar} alt={c.name}
                  style={{ width: 42, height: 42, borderRadius: '50%', flexShrink: 0, objectFit: 'cover' }} />
              ) : (
                <div style={{
                  width: 42, height: 42, borderRadius: '50%', flexShrink: 0,
                  background: avatarColor(c.external_userid),
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 15, fontWeight: 600,
                }}>
                  {(c.name || c.external_userid).slice(0, 1)}
                </div>
              )}
              <div style={{ marginLeft: 14, flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: '#111827', whiteSpace: 'nowrap' }}>
                    {c.name || c.external_userid}
                  </p>
                  {c.corp_name && (
                    <span style={{ fontSize: 11, color: '#6b7280', background: '#f3f4f6', padding: '1px 7px', borderRadius: 10, whiteSpace: 'nowrap', flexShrink: 0 }}>
                      {c.corp_name}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 12, color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.external_userid} · {c.message_count} 条消息
                </p>
              </div>
              <span style={{ fontSize: 12, color: '#9ca3af', flexShrink: 0, marginLeft: 12 }}>
                {formatTime(c.last_updated)}
              </span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="2" style={{ marginLeft: 8, flexShrink: 0 }}>
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
