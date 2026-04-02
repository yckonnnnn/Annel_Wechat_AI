import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { isLoggedIn } from '../lib/auth'

export default function LoginPage() {
  const navigate = useNavigate()

  useEffect(() => {
    if (isLoggedIn()) navigate('/dashboard', { replace: true })
  }, [navigate])

  const handleLogin = () => {
    const redirectUri = `${window.location.origin}/auth/callback`
    fetch(`/api/auth/wecom-login-url?redirect_uri=${encodeURIComponent(redirectUri)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.url) window.location.href = data.url
      })
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)' }}
    >
      {/* 背景装饰圆 */}
      <div
        style={{
          position: 'fixed', top: '-20%', right: '-10%',
          width: 500, height: 500, borderRadius: '50%',
          background: 'rgba(99,102,241,0.15)', pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'fixed', bottom: '-15%', left: '-8%',
          width: 400, height: 400, borderRadius: '50%',
          background: 'rgba(16,185,129,0.1)', pointerEvents: 'none',
        }}
      />

      <div
        className="relative w-full max-w-sm mx-4"
        style={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 20,
          padding: '48px 40px',
        }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            style={{
              width: 56, height: 56, borderRadius: 16,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 16,
              boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white" opacity="0.9"/>
              <circle cx="8" cy="11" r="1.5" fill="rgba(99,102,241,0.8)"/>
              <circle cx="12" cy="11" r="1.5" fill="rgba(99,102,241,0.8)"/>
              <circle cx="16" cy="11" r="1.5" fill="rgba(99,102,241,0.8)"/>
            </svg>
          </div>
          <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>
            企微客服管理
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>
            使用企业微信账号安全登录
          </p>
        </div>

        {/* 登录按钮 */}
        <button
          onClick={handleLogin}
          className="w-full"
          style={{
            padding: '14px 0',
            background: 'linear-gradient(135deg, #07c160, #06ad56)',
            border: 'none',
            borderRadius: 12,
            color: '#fff',
            fontSize: 15,
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(7,193,96,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            transition: 'opacity 0.15s',
          }}
          onMouseOver={(e) => (e.currentTarget.style.opacity = '0.9')}
          onMouseOut={(e) => (e.currentTarget.style.opacity = '1')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M18.403 5.633A8.919 8.919 0 0 0 12.053 3c-4.948 0-8.976 4.027-8.976 8.977 0 1.582.413 3.126 1.198 4.488L3 21.116l4.759-1.249a8.981 8.981 0 0 0 4.29 1.093h.004c4.947 0 8.975-4.027 8.975-8.977a8.926 8.926 0 0 0-2.625-6.35"/>
          </svg>
          企业微信扫码登录
        </button>

        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, textAlign: 'center', marginTop: 20 }}>
          仅限企业内部成员使用
        </p>
      </div>
    </div>
  )
}
