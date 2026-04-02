import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

interface Message {
  timestamp: number
  from: 'user' | 'system'
  type: string
  content: string
  extra?: Record<string, unknown>
}

interface CustomerDetail {
  external_userid: string
  name: string
  avatar: string
  gender: number
  corp_name: string
  position: string
  conversation_summary: {
    message_count: number
    last_updated: number
    first_message_time: number
  } | null
}

interface DetailResponse {
  data: CustomerDetail
}

interface MessagesResponse {
  data: { messages: Message[] }
}

function formatDateTime(ts: number): string {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function CustomerDetailPage() {
  const { external_userid } = useParams<{ external_userid: string }>()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<CustomerDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!external_userid) return
    Promise.all([
      api.get<DetailResponse>(`/api/customers/${external_userid}`),
      api.get<MessagesResponse>(`/api/customers/${external_userid}/messages?limit=100`),
    ])
      .then(([detailRes, msgsRes]) => {
        setDetail(detailRes.data)
        setMessages(msgsRes.data.messages)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [external_userid])

  useEffect(() => {
    bottomRef.current?.scrollIntoView()
  }, [messages])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400 text-sm">加载中...</div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-500 text-sm">{error}</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-sm text-blue-600 hover:underline">
          ← 返回
        </button>
      </div>
    )
  }

  const avatarColors = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6']
  const avatarBg = avatarColors[(external_userid?.charCodeAt(external_userid.length - 1) ?? 0) % avatarColors.length]
  const displayName = detail?.name || external_userid || ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 顶部栏 */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        padding: '20px 24px',
        flexShrink: 0,
      }}>
        {/* 返回按钮 */}
        <button
          onClick={() => navigate('/customers')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: 8, padding: '5px 12px', color: 'rgba(255,255,255,0.7)',
            fontSize: 13, cursor: 'pointer', marginBottom: 16,
          }}
        >
          ← 返回客户列表
        </button>

        {/* 客户信息主区 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {detail?.avatar ? (
            <img src={detail.avatar} alt={displayName}
              style={{ width: 56, height: 56, borderRadius: '50%', objectFit: 'cover', border: '2px solid rgba(255,255,255,0.2)', flexShrink: 0 }} />
          ) : (
            <div style={{
              width: 56, height: 56, borderRadius: '50%', flexShrink: 0,
              background: avatarBg,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 22, fontWeight: 700,
              border: '2px solid rgba(255,255,255,0.2)',
            }}>
              {displayName.slice(0, 1)}
            </div>
          )}

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: 0 }}>{displayName}</h3>
              {detail?.gender === 1 && <span style={{ fontSize: 12, background: 'rgba(99,102,241,0.4)', color: '#a5b4fc', padding: '2px 8px', borderRadius: 6 }}>男</span>}
              {detail?.gender === 2 && <span style={{ fontSize: 12, background: 'rgba(236,72,153,0.3)', color: '#f9a8d4', padding: '2px 8px', borderRadius: 6 }}>女</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {detail?.corp_name && (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
                  🏢 {detail.corp_name}
                </span>
              )}
              {detail?.corp_name && detail?.position && (
                <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>·</span>
              )}
              {detail?.position && (
                <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
                  {detail.position}
                </span>
              )}
              {!detail?.corp_name && !detail?.position && (
                <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>{external_userid}</span>
              )}
            </div>
          </div>

          {/* 消息统计 */}
          {detail?.conversation_summary && (
            <div style={{
              background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 10, padding: '10px 16px', textAlign: 'center', flexShrink: 0,
            }}>
              <p style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: 0 }}>
                {detail.conversation_summary.message_count}
              </p>
              <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', margin: '2px 0 0' }}>条消息</p>
            </div>
          )}
        </div>
      </div>

      {/* 对话区域 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', background: '#f0f2f5', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: 14, padding: '60px 0' }}>暂无对话记录</div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: msg.from === 'user' ? 'flex-start' : 'flex-end' }}>
              <div style={{ maxWidth: '60%' }}>
                <div style={{
                  padding: '10px 14px',
                  borderRadius: msg.from === 'user' ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
                  fontSize: 14, lineHeight: 1.55,
                  background: msg.from === 'user' ? '#fff' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: msg.from === 'user' ? '#1f2937' : '#fff',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                }}>
                  {msg.type === 'image' ? (
                    <span style={{ fontStyle: 'italic', opacity: 0.7, fontSize: 13 }}>[图片]</span>
                  ) : msg.type === 'event' ? (
                    <span style={{ fontStyle: 'italic', opacity: 0.7, fontSize: 13 }}>[{msg.content}]</span>
                  ) : msg.content}
                </div>
                <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 4, textAlign: msg.from === 'user' ? 'left' : 'right' }}>
                  {formatDateTime(msg.timestamp)}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
