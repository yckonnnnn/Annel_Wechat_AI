import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Customer {
  external_userid: string
  name: string
  avatar: string
  corp_name: string
}

interface CustomerListResponse {
  data: { count: number; customers: Customer[] }
}

interface ScheduledTask {
  id: string
  sender: string
  content: string
  cron: Record<string, string>
  external_userids: string[] | null
}

interface ScheduleListResponse {
  data: ScheduledTask[]
}

type RepeatType = 'daily' | 'weekdays' | 'weekends' | 'weekly'

const REPEAT_OPTIONS: { value: RepeatType; label: string }[] = [
  { value: 'daily', label: '每天' },
  { value: 'weekdays', label: '工作日（周一至周五）' },
  { value: 'weekends', label: '周末（周六日）' },
  { value: 'weekly', label: '每周指定一天' },
]

const WEEKDAY_OPTIONS = [
  { value: 'mon', label: '周一' }, { value: 'tue', label: '周二' },
  { value: 'wed', label: '周三' }, { value: 'thu', label: '周四' },
  { value: 'fri', label: '周五' }, { value: 'sat', label: '周六' },
  { value: 'sun', label: '周日' },
]

function buildCron(repeat: RepeatType, weekday: string, hour: string, minute: string) {
  const base = { hour, minute }
  if (repeat === 'weekdays') return { ...base, day_of_week: 'mon-fri' }
  if (repeat === 'weekends') return { ...base, day_of_week: 'sat,sun' }
  if (repeat === 'weekly') return { ...base, day_of_week: weekday }
  return base
}

function describeCron(cron: Record<string, string>): string {
  const h = cron.hour?.padStart(2, '0') ?? '?'
  const m = cron.minute?.padStart(2, '0') ?? '00'
  const dow = cron.day_of_week
  if (!dow) return `每天 ${h}:${m}`
  if (dow === 'mon-fri') return `工作日 ${h}:${m}`
  if (dow === 'sat,sun') return `周末 ${h}:${m}`
  const found = WEEKDAY_OPTIONS.find((d) => d.value === dow)
  return `每${found?.label ?? dow} ${h}:${m}`
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb',
  borderRadius: 8, fontSize: 14, outline: 'none', boxSizing: 'border-box',
}
const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 13, color: '#374151', fontWeight: 500, marginBottom: 6,
}

// ─── Customer Multi-Select ────────────────────────────────────────────────────

function CustomerMultiSelect({
  customers,
  selected,
  onChange,
}: {
  customers: Customer[]
  selected: string[]           // external_userid[]
  onChange: (ids: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const wrapRef = useRef<HTMLDivElement>(null)

  // 点击外部关闭
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const filtered = customers.filter((c) =>
    c.name.includes(search) || c.external_userid.includes(search) || c.corp_name.includes(search)
  )

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])
  }

  const selectedCustomers = customers.filter((c) => selected.includes(c.external_userid))

  return (
    <div ref={wrapRef} style={{ position: 'relative' }}>
      <label style={labelStyle}>
        指定客户
        <span style={{ fontWeight: 400, color: '#9ca3af', marginLeft: 4 }}>（不选 = 发送给该员工所有客户）</span>
      </label>

      {/* 触发框 */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          minHeight: 42, padding: '6px 12px', border: `1.5px solid ${open ? '#6366f1' : '#e5e7eb'}`,
          borderRadius: 8, cursor: 'pointer', background: '#fff', boxSizing: 'border-box',
          display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center',
          transition: 'border-color 0.15s',
        }}
      >
        {selectedCustomers.length === 0 ? (
          <span style={{ color: '#9ca3af', fontSize: 14 }}>点击选择客户...</span>
        ) : (
          selectedCustomers.map((c) => (
            <span
              key={c.external_userid}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                background: '#eef2ff', color: '#6366f1', borderRadius: 6,
                fontSize: 13, padding: '2px 8px', fontWeight: 500,
              }}
            >
              {c.name}
              <span
                onClick={(e) => { e.stopPropagation(); toggle(c.external_userid) }}
                style={{ cursor: 'pointer', opacity: 0.6, marginLeft: 2, lineHeight: 1 }}
              >×</span>
            </span>
          ))
        )}
        <span style={{ marginLeft: 'auto', color: '#9ca3af', fontSize: 12 }}>{open ? '▲' : '▼'}</span>
      </div>

      {/* 下拉面板 */}
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0, zIndex: 100,
          background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)', overflow: 'hidden',
        }}>
          {/* 搜索 */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid #f3f4f6' }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索客户姓名..."
              onClick={(e) => e.stopPropagation()}
              style={{ ...inputStyle, padding: '7px 10px', border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13 }}
              autoFocus
            />
          </div>

          {/* 全选/清空 */}
          {customers.length > 0 && (
            <div style={{ display: 'flex', gap: 8, padding: '6px 12px', borderBottom: '1px solid #f3f4f6' }}>
              <button onClick={() => onChange(customers.map((c) => c.external_userid))}
                style={{ fontSize: 12, color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                全选
              </button>
              <span style={{ color: '#e5e7eb' }}>|</span>
              <button onClick={() => onChange([])}
                style={{ fontSize: 12, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                清空
              </button>
              <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9ca3af' }}>
                已选 {selected.length}/{customers.length}
              </span>
            </div>
          )}

          {/* 客户列表 */}
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {filtered.length === 0 ? (
              <div style={{ padding: '20px 0', textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>无匹配客户</div>
            ) : (
              filtered.map((c) => {
                const isSelected = selected.includes(c.external_userid)
                return (
                  <div
                    key={c.external_userid}
                    onClick={() => toggle(c.external_userid)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                      cursor: 'pointer', background: isSelected ? '#f5f3ff' : 'transparent',
                      transition: 'background 0.1s',
                    }}
                    onMouseOver={(e) => { if (!isSelected) e.currentTarget.style.background = '#f9fafb' }}
                    onMouseOut={(e) => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
                  >
                    {/* 勾选框 */}
                    <div style={{
                      width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                      border: isSelected ? 'none' : '1.5px solid #d1d5db',
                      background: isSelected ? '#6366f1' : 'transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {isSelected && <span style={{ color: '#fff', fontSize: 12, lineHeight: 1 }}>✓</span>}
                    </div>
                    {/* 头像 */}
                    {c.avatar ? (
                      <img src={c.avatar} alt={c.name} style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
                    ) : (
                      <div style={{
                        width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                        background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: 13, fontWeight: 600,
                      }}>
                        {c.name.slice(0, 1)}
                      </div>
                    )}
                    {/* 名字 */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 14, fontWeight: 500, color: '#111827', margin: 0 }}>{c.name}</p>
                      {c.corp_name && <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>{c.corp_name}</p>}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── SendNowTab ───────────────────────────────────────────────────────────────

function SendNowTab({ defaultSender, customers }: { defaultSender: string; customers: Customer[] }) {
  const [sender, setSender] = useState(defaultSender)
  const [content, setContent] = useState('')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [status, setStatus] = useState<'idle' | 'sending' | 'ok' | 'error'>('idle')
  const [msg, setMsg] = useState('')

  const handleSend = () => {
    if (!sender.trim() || !content.trim()) {
      setStatus('error'); setMsg('发送人和消息内容不能为空'); return
    }
    setStatus('sending'); setMsg('')
    api
      .post('/api/proactive', {
        sender: sender.trim(),
        content: content.trim(),
        external_userids: selectedIds.length > 0 ? selectedIds : null,
      })
      .then(() => { setStatus('ok'); setMsg('发送成功！'); setContent(''); setSelectedIds([]) })
      .catch((e: Error) => { setStatus('error'); setMsg(e.message) })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 560 }}>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={labelStyle}>发送人（企微员工 userid）</label>
            <input value={sender} onChange={(e) => setSender(e.target.value)} placeholder="例：zhangsan" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>消息内容</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={4}
              placeholder="输入要发送的消息..." style={{ ...inputStyle, resize: 'none' }} />
          </div>
          <CustomerMultiSelect customers={customers} selected={selectedIds} onChange={setSelectedIds} />
        </div>

        {msg && <p style={{ fontSize: 14, color: status === 'ok' ? '#10b981' : '#ef4444', marginTop: 12 }}>{msg}</p>}

        <button onClick={handleSend} disabled={status === 'sending'}
          style={{
            marginTop: 16, padding: '11px 28px',
            background: status === 'sending' ? '#6b7280' : 'linear-gradient(135deg, #07c160, #06ad56)',
            border: 'none', borderRadius: 10, color: '#fff', fontSize: 14, fontWeight: 600,
            cursor: status === 'sending' ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 12px rgba(7,193,96,0.3)',
          }}>
          {status === 'sending' ? '发送中...' : '立即发送'}
        </button>
      </div>
    </div>
  )
}

// ─── ScheduleTab ─────────────────────────────────────────────────────────────

function ScheduleTab({ defaultSender, customers }: { defaultSender: string; customers: Customer[] }) {
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [sender, setSender] = useState(defaultSender)
  const [content, setContent] = useState('')
  const [repeat, setRepeat] = useState<RepeatType>('daily')
  const [weekday, setWeekday] = useState('mon')
  const [hour, setHour] = useState('8')
  const [minute, setMinute] = useState('0')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')

  const loadTasks = () => {
    api.get<ScheduleListResponse>('/api/proactive/schedule')
      .then((res) => setTasks(res.data))
      .catch(() => setTasks([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadTasks() }, [])

  const handleCreate = () => {
    if (!sender.trim() || !content.trim()) { setFormError('发送人和内容不能为空'); return }
    setSubmitting(true); setFormError('')
    const cron = buildCron(repeat, weekday, hour, minute)
    api.post('/api/proactive/schedule', {
      task_id: `task_${Date.now()}`,
      sender: sender.trim(),
      content: content.trim(),
      cron,
      external_userids: selectedIds.length > 0 ? selectedIds : null,
    })
      .then(() => { setShowForm(false); setContent(''); setSelectedIds([]); loadTasks() })
      .catch((e: Error) => setFormError(e.message))
      .finally(() => setSubmitting(false))
  }

  const handleDelete = (id: string) => {
    if (!confirm('确认删除该定时任务？')) return
    api.delete(`/api/proactive/schedule/${id}`).then(() => loadTasks()).catch(() => {})
  }

  // 根据 external_userid 反查名字
  const resolveNames = (ids: string[] | null) => {
    if (!ids) return '全部客户'
    return ids.map((id) => customers.find((c) => c.external_userid === id)?.name || id).join('、')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 680 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ fontSize: 14, color: '#6b7280' }}>{tasks.length} 个定时任务</p>
        <button onClick={() => setShowForm(!showForm)}
          style={{
            padding: '9px 18px', background: showForm ? '#f3f4f6' : '#6366f1',
            border: 'none', borderRadius: 8, color: showForm ? '#374151' : '#fff',
            fontSize: 14, fontWeight: 500, cursor: 'pointer',
          }}>
          {showForm ? '取消' : '+ 新建任务'}
        </button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.05)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#374151', marginBottom: 16 }}>新建定时任务</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={labelStyle}>发送人（userid）</label>
              <input value={sender} onChange={(e) => setSender(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>重复规则</label>
              <select value={repeat} onChange={(e) => setRepeat(e.target.value as RepeatType)}
                style={{ ...inputStyle, background: '#fff' }}>
                {REPEAT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', marginBottom: 16 }}>
            {repeat === 'weekly' && (
              <div>
                <label style={labelStyle}>星期</label>
                <select value={weekday} onChange={(e) => setWeekday(e.target.value)}
                  style={{ padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, outline: 'none', background: '#fff' }}>
                  {WEEKDAY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            )}
            <div>
              <label style={labelStyle}>时</label>
              <input type="number" min={0} max={23} value={hour} onChange={(e) => setHour(e.target.value)}
                style={{ width: 70, padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, outline: 'none' }} />
            </div>
            <div>
              <label style={labelStyle}>分</label>
              <input type="number" min={0} max={59} value={minute} onChange={(e) => setMinute(e.target.value)}
                style={{ width: 70, padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, outline: 'none' }} />
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>消息内容</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={3}
              style={{ ...inputStyle, resize: 'none' }} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <CustomerMultiSelect customers={customers} selected={selectedIds} onChange={setSelectedIds} />
          </div>
          {formError && <p style={{ fontSize: 13, color: '#ef4444', marginBottom: 12 }}>{formError}</p>}
          <button onClick={handleCreate} disabled={submitting}
            style={{
              padding: '10px 24px', background: '#6366f1', border: 'none',
              borderRadius: 8, color: '#fff', fontSize: 14, fontWeight: 500,
              cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.6 : 1,
            }}>
            {submitting ? '创建中...' : '创建任务'}
          </button>
        </div>
      )}

      {loading ? (
        <p style={{ fontSize: 14, color: '#9ca3af' }}>加载中...</p>
      ) : tasks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', background: '#fff', borderRadius: 16, border: '1px solid #e5e7eb', color: '#9ca3af', fontSize: 14 }}>
          <div style={{ fontSize: 36, marginBottom: 10 }}>⏰</div>暂无定时任务
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
          {tasks.map((t, i) => (
            <div key={t.id} style={{
              display: 'flex', alignItems: 'flex-start', gap: 16, padding: '16px 20px',
              borderTop: i > 0 ? '1px solid #f3f4f6' : 'none',
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 12, background: '#eef2ff', color: '#6366f1', padding: '3px 8px', borderRadius: 6, fontWeight: 600 }}>
                    {describeCron(t.cron)}
                  </span>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>发送人：{t.sender}</span>
                </div>
                <p style={{ fontSize: 14, color: '#374151', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.content}</p>
                <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>
                  客户：{resolveNames(t.external_userids)}
                </p>
              </div>
              <button onClick={() => handleDelete(t.id)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: 13, flexShrink: 0 }}>
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Tab = 'send' | 'schedule'

export default function ProactivePage() {
  const { user } = useAuth()
  const [tab, setTab] = useState<Tab>('send')
  const [customers, setCustomers] = useState<Customer[]>([])
  const defaultSender = user?.userid ?? ''

  useEffect(() => {
    api.get<CustomerListResponse>('/api/customers')
      .then((res) => setCustomers(res.data.customers))
      .catch(() => {})
  }, [])

  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>主动关怀</h2>
        <p style={{ fontSize: 14, color: '#6b7280' }}>向客户主动发送消息或创建定时任务</p>
      </div>

      <div style={{ display: 'flex', gap: 4, background: '#f3f4f6', borderRadius: 10, padding: 4, width: 'fit-content', marginBottom: 28 }}>
        {([['send', '立即发送'], ['schedule', '定时任务']] as [Tab, string][]).map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 14,
            background: tab === key ? '#fff' : 'transparent',
            color: tab === key ? '#1f2937' : '#6b7280',
            fontWeight: tab === key ? 600 : 400,
            boxShadow: tab === key ? '0 1px 4px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s',
          }}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'send'
        ? <SendNowTab defaultSender={defaultSender} customers={customers} />
        : <ScheduleTab defaultSender={defaultSender} customers={customers} />}
    </div>
  )
}
