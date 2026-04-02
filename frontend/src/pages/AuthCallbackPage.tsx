import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { setToken } from '../lib/auth'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const called = useRef(false)

  useEffect(() => {
    if (called.current) return
    called.current = true

    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')

    if (!code) {
      navigate('/login', { replace: true })
      return
    }

    fetch(`/api/auth/callback?code=${code}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.access_token) {
          setToken(data.access_token)
          navigate('/dashboard', { replace: true })
        } else {
          navigate('/login', { replace: true })
        }
      })
      .catch(() => navigate('/login', { replace: true }))
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <span className="text-gray-400 text-sm">登录中，请稍候...</span>
    </div>
  )
}
