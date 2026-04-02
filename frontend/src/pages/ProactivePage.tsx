import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

// ─── 类型 ────────────────────────────────────────────────────────────────────

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

// ─── Cron 辅助 ───────────────────────────────────────────────────────────────

type RepeatType = 'daily' | 'weekdays' | 'weekends' | 'weekly'

const REPEAT_OPTIONS: { value: RepeatType; label: string }[] = [
  { value: 'daily', label: '每天' },
  { value: 'weekdays', label: '工作日（周一至周五）' },
  { value: 'weekends', label: '周末（周六日）' },
  { value: 'weekly', label: '每周指定一天' },
]

const WEEKDAY_OPTIONS = [
  { value: 'mon', label: '周一' },
  { value: 'tue', label: '周二' },
  { value: 'wed', label: '周三' },
  { value: 'thu', label: '周四' },
  { value: 'fri', label: '周五' },
  { value: 'sat', label: '周六' },
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

// ─── 子组件：立即发送 Tab ─────────────────────────────────────────────────────

function SendNowTab({ defaultSender }: { defaultSender: string }) {
  const [sender, setSender] = useState(defaultSender)
  const [content, setContent] = useState('')
  const [targets, setTargets] = useState('')     // 逗号分隔的 external_userid，空 = 全部
  const [status, setStatus] = useState<'idle' | 'sending' | 'ok' | 'error'>('idle')
  const [msg, setMsg] = useState('')

  const handleSend = () => {
    if (!sender.trim() || !content.trim()) {
      setStatus('error')
      setMsg('发送人和消息内容不能为空')
      return
    }
    setStatus('sending')
    setMsg('')
    const external_userids = targets.trim()
      ? targets.split(',').map((s) => s.trim()).filter(Boolean)
      : null
    api
      .post('/api/proactive', { sender: sender.trim(), content: content.trim(), external_userids })
      .then(() => {
        setStatus('ok')
        setMsg('发送成功！')
        setContent('')
        setTargets('')
      })
      .catch((e: Error) => {
        setStatus('error')
        setMsg(e.message)
      })
  }

  return (
    <div className="space-y-5 max-w-lg">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">发送人（企微员工 userid）</label>
        <input
          value={sender}
          onChange={(e) => setSender(e.target.value)}
          placeholder="例：zhangsan"
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">消息内容</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          placeholder="输入要发送的消息..."
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          指定客户（留空 = 该员工所有客户）
        </label>
        <input
          value={targets}
          onChange={(e) => setTargets(e.target.value)}
          placeholder="external_userid1, external_userid2, ..."
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
        <p className="text-xs text-gray-400 mt-1">多个 ID 用英文逗号分隔</p>
      </div>

      {msg && (
        <p className={`text-sm ${status === 'ok' ? 'text-green-600' : 'text-red-500'}`}>{msg}</p>
      )}

      <button
        onClick={handleSend}
        disabled={status === 'sending'}
        className="px-6 py-2.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
      >
        {status === 'sending' ? '发送中...' : '立即发送'}
      </button>
    </div>
  )
}

// ─── 子组件：定时任务 Tab ─────────────────────────────────────────────────────

function ScheduleTab({ defaultSender }: { defaultSender: string }) {
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // 表单状态
  const [sender, setSender] = useState(defaultSender)
  const [content, setContent] = useState('')
  const [repeat, setRepeat] = useState<RepeatType>('daily')
  const [weekday, setWeekday] = useState('mon')
  const [hour, setHour] = useState('8')
  const [minute, setMinute] = useState('0')
  const [targets, setTargets] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')

  const loadTasks = () => {
    api
      .get<ScheduleListResponse>('/api/proactive/schedule')
      .then((res) => setTasks(res.data))
      .catch(() => setTasks([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const handleCreate = () => {
    if (!sender.trim() || !content.trim()) {
      setFormError('发送人和内容不能为空')
      return
    }
    setSubmitting(true)
    setFormError('')
    const cron = buildCron(repeat, weekday, hour, minute)
    const task_id = `task_${Date.now()}`
    const external_userids = targets.trim()
      ? targets.split(',').map((s) => s.trim()).filter(Boolean)
      : null
    api
      .post('/api/proactive/schedule', { task_id, sender: sender.trim(), content: content.trim(), cron, external_userids })
      .then(() => {
        setShowForm(false)
        setContent('')
        setTargets('')
        loadTasks()
      })
      .catch((e: Error) => setFormError(e.message))
      .finally(() => setSubmitting(false))
  }

  const handleDelete = (id: string) => {
    if (!confirm('确认删除该定时任务？')) return
    api.delete(`/api/proactive/schedule/${id}`).then(() => loadTasks()).catch(() => {})
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{tasks.length} 个定时任务</p>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? '取消' : '+ 新建任务'}
        </button>
      </div>

      {/* 新建表单 */}
      {showForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">新建定时任务</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">发送人（userid）</label>
              <input
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">重复规则</label>
              <select
                value={repeat}
                onChange={(e) => setRepeat(e.target.value as RepeatType)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none bg-white"
              >
                {REPEAT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-3 items-end">
            {repeat === 'weekly' && (
              <div>
                <label className="block text-xs text-gray-600 mb-1">星期</label>
                <select
                  value={weekday}
                  onChange={(e) => setWeekday(e.target.value)}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none bg-white"
                >
                  {WEEKDAY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-xs text-gray-600 mb-1">时</label>
              <input
                type="number"
                min={0}
                max={23}
                value={hour}
                onChange={(e) => setHour(e.target.value)}
                className="w-16 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">分</label>
              <input
                type="number"
                min={0}
                max={59}
                value={minute}
                onChange={(e) => setMinute(e.target.value)}
                className="w-16 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-600 mb-1">消息内容</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">指定客户（留空 = 全部）</label>
            <input
              value={targets}
              onChange={(e) => setTargets(e.target.value)}
              placeholder="external_userid1, external_userid2, ..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <button
            onClick={handleCreate}
            disabled={submitting}
            className="px-5 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? '创建中...' : '创建任务'}
          </button>
        </div>
      )}

      {/* 任务列表 */}
      {loading ? (
        <p className="text-sm text-gray-400">加载中...</p>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm bg-white rounded-xl border border-gray-100">
          暂无定时任务
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
          {tasks.map((t) => (
            <div key={t.id} className="flex items-start px-5 py-4 gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                    {describeCron(t.cron)}
                  </span>
                  <span className="text-xs text-gray-400">发送人：{t.sender}</span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-2">{t.content}</p>
                {t.external_userids && (
                  <p className="text-xs text-gray-400 mt-1">
                    指定 {t.external_userids.length} 位客户
                  </p>
                )}
              </div>
              <button
                onClick={() => handleDelete(t.id)}
                className="text-xs text-red-400 hover:text-red-600 transition-colors shrink-0 mt-1"
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── 主页面 ───────────────────────────────────────────────────────────────────

type Tab = 'send' | 'schedule'

export default function ProactivePage() {
  const { user } = useAuth()
  const [tab, setTab] = useState<Tab>('send')
  const defaultSender = user?.userid ?? ''

  return (
    <div className="p-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">主动关怀</h2>

      {/* Tab 切换 */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit mb-8">
        {([['send', '立即发送'], ['schedule', '定时任务']] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-5 py-2 text-sm rounded-md transition-colors ${
              tab === key
                ? 'bg-white text-gray-800 font-medium shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'send' ? (
        <SendNowTab defaultSender={defaultSender} />
      ) : (
        <ScheduleTab defaultSender={defaultSender} />
      )}
    </div>
  )
}
