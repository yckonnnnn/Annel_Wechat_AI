import { useAuth } from '../contexts/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  const infoRows = [
    { label: '用户 ID', value: user?.userid ?? '-' },
    { label: '姓名', value: user?.name ?? '-' },
    { label: '角色', value: user?.role === 'superadmin' ? '超级管理员' : user?.role === 'admin' ? '管理员' : '员工' },
  ]

  const systemRows = [
    { label: '企业 ID（CorpID）', value: 'ww3a42a0c7158120be' },
    { label: '应用 AgentID', value: '1000023' },
    { label: '回调地址', value: 'https://www.hairclub.com.cn/callback' },
    { label: '域名', value: 'www.hairclub.com.cn' },
  ]

  return (
    <div style={{ padding: 32 }}>
      {/* 头部 */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 }}>系统设置</h2>
        <p style={{ fontSize: 14, color: '#6b7280' }}>查看系统配置与当前账号信息</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, maxWidth: 900 }}>
        {/* 当前账号 */}
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: 16,
          padding: 24,
          boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 18,
            }}>
              👤
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#1f2937', margin: 0 }}>当前账号</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {infoRows.map(({ label, value }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: '#6b7280' }}>{label}</span>
                <span style={{
                  fontSize: 13, fontWeight: 500, color: '#1f2937',
                  background: '#f3f4f6', padding: '4px 10px', borderRadius: 6,
                }}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 企业微信配置 */}
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: 16,
          padding: 24,
          boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #07c160, #06ad56)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 18,
            }}>
              ⚙️
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#1f2937', margin: 0 }}>企业微信配置</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {systemRows.map(({ label, value }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                <span style={{ fontSize: 13, color: '#6b7280', flexShrink: 0 }}>{label}</span>
                <span style={{
                  fontSize: 12, fontWeight: 500, color: '#374151',
                  background: '#f3f4f6', padding: '4px 8px', borderRadius: 6,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  maxWidth: 200,
                }}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 服务状态 */}
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: 16,
          padding: 24,
          boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
          gridColumn: '1 / -1',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 18,
            }}>
              🔧
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#1f2937', margin: 0 }}>服务状态</h3>
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            {[
              { name: 'API 服务', status: '运行中', color: '#10b981' },
              { name: '企微回调', status: '已配置', color: '#10b981' },
              { name: 'SSL 证书', status: '有效', color: '#10b981' },
              { name: 'AI 助手', status: '已接入', color: '#10b981' },
            ].map(({ name, status, color }) => (
              <div key={name} style={{
                flex: 1, padding: '14px 16px',
                background: `${color}0d`,
                border: `1px solid ${color}33`,
                borderRadius: 10,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <span style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>{name}</span>
                <span style={{ fontSize: 12, color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block' }} />
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
