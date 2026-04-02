import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  {
    to: '/dashboard', label: '仪表盘',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
      </svg>
    ),
  },
  {
    to: '/customers', label: '客户管理',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
  {
    to: '/proactive', label: '主动关怀',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 15.1a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 4.27h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 11.9a16 16 0 0 0 6.29 6.29l1.5-1.5a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
      </svg>
    ),
  },
  {
    to: '/faq', label: 'FAQ 知识库',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"/>
      </svg>
    ),
  },
  {
    to: '/settings', label: '系统设置',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
  },
]

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen" style={{ background: '#f0f2f5' }}>
      {/* 深色侧边栏 */}
      <aside
        className="flex flex-col"
        style={{
          width: 220,
          background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          flexShrink: 0,
        }}
      >
        {/* Logo 区 */}
        <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 34, height: 34, borderRadius: 10,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z"/>
              </svg>
            </div>
            <div>
              <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, lineHeight: 1.2 }}>企微客服</p>
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>管理系统</p>
            </div>
          </div>
        </div>

        {/* 导航 */}
        <nav style={{ flex: 1, padding: '12px 10px' }}>
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                borderRadius: 10,
                marginBottom: 2,
                color: isActive ? '#fff' : 'rgba(255,255,255,0.5)',
                background: isActive ? 'rgba(99,102,241,0.25)' : 'transparent',
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: isActive ? 500 : 400,
                transition: 'all 0.15s',
                borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
              })}
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </nav>

        {/* 用户区 */}
        <div style={{ padding: '16px 14px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          {user && (
            <div style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 12, fontWeight: 600, flexShrink: 0,
                }}
              >
                {user.name.slice(0, 1)}
              </div>
              <div style={{ minWidth: 0 }}>
                <p style={{ color: '#fff', fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.name}
                </p>
                <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11 }}>{user.role}</p>
              </div>
            </div>
          )}
          <button
            onClick={logout}
            style={{
              width: '100%', padding: '8px 12px',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8, color: 'rgba(255,255,255,0.5)',
              fontSize: 13, cursor: 'pointer', textAlign: 'left',
              transition: 'all 0.15s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(239,68,68,0.15)'
              e.currentTarget.style.color = '#f87171'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
              e.currentTarget.style.color = 'rgba(255,255,255,0.5)'
            }}
          >
            退出登录
          </button>
        </div>
      </aside>

      {/* 主内容 */}
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  )
}
