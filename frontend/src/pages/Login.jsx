import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [remember, setRemember] = useState(false)

  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedRol = localStorage.getItem('rol')
    if (savedToken && savedRol) {
      setMessage('Sesión activa detectada, redirigiendo...')
      setTimeout(() => {
        if (savedRol === 'Vigilante') navigate('/caseta')
        else if (savedRol === 'Supervisor') navigate('/supervisor')
        else if (savedRol === 'RRHH' || savedRol === 'Administrador' || savedRol === 'Superusuario') navigate('/admin')
        else navigate('/')
      }, 1000)
    }
  }, [navigate])

  async function submit(event) {
    event.preventDefault()
    if (!username.trim() || !password.trim()) {
      setMessage('⚠️ Completa todos los campos')
      return
    }
    setLoading(true)
    setMessage('')
    try {
      const { data } = await api.post('/auth/login', { username, password })
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('rol', data.rol)
      if (remember) {
        localStorage.setItem('remember', 'true')
      }
      setMessage('✅ Sesión iniciada correctamente')
      setTimeout(() => {
        if (data.rol === 'Vigilante') navigate('/caseta')
        else if (data.rol === 'Supervisor') navigate('/supervisor')
        else if (data.rol === 'RRHH' || data.rol === 'Administrador' || data.rol === 'Superusuario') navigate('/admin')
        else navigate('/')
      }, 1000)
    } catch (err) {
      setMessage('❌ Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc', padding: '1.5rem', display: 'grid', placeItems: 'center' }}>
    <form onSubmit={submit} className="panel" style={{ width: '100%', maxWidth: '28rem', display: 'grid', gap: '1.5rem' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🔐</div>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 900, margin: 0 }}>Acceso al Sistema</h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Sistema RRHH y Vigilancia</p>
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem', color: '#94a3b8' }}>Usuario</label>
          <input className="input" placeholder="Ingresa tu usuario" value={username} onChange={(e) => setUsername(e.target.value)} disabled={loading} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem', color: '#94a3b8' }}>Contraseña</label>
          <input className="input" placeholder="Ingresa tu contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <input type="checkbox" id="remember" checked={remember} onChange={(e) => setRemember(e.target.checked)} style={{ width: '1.25rem', height: '1.25rem' }} />
        <label htmlFor="remember" style={{ fontSize: '0.875rem', color: '#94a3b8', cursor: 'pointer' }}>Recordar sesión</label>
      </div>

      <button className="btn" disabled={loading} style={{ opacity: loading ? 0.5 : 1 }}>
        {loading ? '⏳ Iniciando...' : '🚀 Iniciar sesión'}
      </button>

      {message && <section style={{ padding: '1rem', borderRadius: '0.75rem', background: message.includes('✅') ? 'rgba(5,150,105,0.1)' : message.includes('⚠️') ? 'rgba(234,179,8,0.1)' : 'rgba(220,38,38,0.1)', border: `1px solid ${message.includes('✅') ? '#059669' : message.includes('⚠️') ? '#eab308' : '#dc2626'}`, textAlign: 'center' }}>
        <p style={{ fontSize: '0.875rem', fontWeight: 700, margin: 0 }}>{message}</p>
      </section>}

      <div style={{ textAlign: 'center', paddingTop: '1rem', borderTop: '1px solid #1e293b' }}>
        <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>Usuarios de prueba: super/super123, vigilante/vigilante123</p>
      </div>
    </form>
  </main>
}
