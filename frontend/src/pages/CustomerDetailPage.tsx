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

  return (
    <div className="flex flex-col h-full">
      {/* 顶部栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4 shrink-0">
        <button onClick={() => navigate('/customers')} className="text-gray-400 hover:text-gray-600 text-sm">
          ← 返回
        </button>
        <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium text-xs shrink-0">
          {external_userid?.slice(-2).toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-800">
            {detail?.name || external_userid}
          </p>
          <p className="text-xs text-gray-400">
            {[detail?.corp_name, detail?.position].filter(Boolean).join(' · ') || external_userid}
          </p>
        </div>
        {detail?.conversation_summary && (
          <span className="ml-auto text-xs text-gray-400">
            共 {detail.conversation_summary.message_count} 条消息
          </span>
        )}
      </div>

      {/* 对话区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 text-sm py-16">暂无对话记录</div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.from === 'user' ? 'justify-start' : 'justify-end'}`}
            >
              <div className="max-w-sm">
                <div
                  className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.from === 'user'
                      ? 'bg-white text-gray-800 rounded-tl-sm shadow-sm'
                      : 'bg-blue-600 text-white rounded-tr-sm'
                  }`}
                >
                  {msg.type === 'image' ? (
                    <span className="italic text-xs opacity-70">[图片]</span>
                  ) : msg.type === 'event' ? (
                    <span className="italic text-xs opacity-70">[{msg.content}]</span>
                  ) : (
                    msg.content
                  )}
                </div>
                <p
                  className={`text-xs text-gray-300 mt-1 ${
                    msg.from === 'user' ? 'text-left' : 'text-right'
                  }`}
                >
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
