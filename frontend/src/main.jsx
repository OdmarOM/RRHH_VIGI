import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, Route, Routes, Navigate } from 'react-router-dom'
import { Shield, ScanLine, Users, ClipboardCheck, Activity, AlertTriangle, Truck, LogOut } from 'lucide-react'
import './styles.css'
import { Login } from './pages/Login.jsx'
import { ZebraCaseta } from './pages/ZebraCaseta.jsx'
import { Supervisor } from './pages/Supervisor.jsx'
import { Admin } from './pages/Admin.jsx'
import { Historial } from './pages/Historial.jsx'
import { api } from './api.js'

function ProtectedRoute({ children, allowedRoles = [] }) {
  const token = localStorage.getItem('token')
  const rol = localStorage.getItem('rol')
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles.length > 0 && !allowedRoles.includes(rol)) {
    return <Navigate to="/" replace />
  }
  
  return children
}

function Home() {
  const [metrics, setMetrics] = useState({ empleados_presentes: 0, incidencias: 0, fila_externa: 0 })
  const [loading, setLoading] = useState(true)
  const rol = localStorage.getItem('rol')

  useEffect(() => {
    async function loadMetrics() {
      try {
        const token = localStorage.getItem('token')
        
        // Cargar métricas según el rol
        if (rol === 'Vigilante' || rol === 'Superusuario') {
          const filaData = await api.get('/caseta/fila-externos').catch(() => ({ data: [] }))
          setMetrics({ fila_externa: filaData.data.length })
        } else if (rol === 'Supervisor' || rol === 'RRHH' || rol === 'Administrador') {
          const [empData, incData] = await Promise.all([
            api.get('/admin/empleados').catch(() => ({ data: [] })),
            api.get('/supervisor/incidencias').catch(() => ({ data: [] }))
          ])
          const presentes = empData.data.filter(e => e.estado_actual === 'Adentro').length
          setMetrics({ empleados_presentes: presentes, incidencias: incData.data.length })
        } else {
          // Superusuario ve todo
          const [empData, incData, filaData] = await Promise.all([
            api.get('/admin/empleados').catch(() => ({ data: [] })),
            api.get('/supervisor/incidencias').catch(() => ({ data: [] })),
            api.get('/caseta/fila-externos').catch(() => ({ data: [] }))
          ])
          const presentes = empData.data.filter(e => e.estado_actual === 'Adentro').length
          setMetrics({ empleados_presentes: presentes, incidencias: incData.data.length, fila_externa: filaData.data.length })
        }
      } catch {}
      setLoading(false)
    }
    loadMetrics()
  }, [rol])

  function logout() {
    localStorage.clear()
    window.location.reload()
  }

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc', padding: '1.5rem' }}>
    <section style={{ maxWidth: '72rem', margin: '0 auto', display: 'grid', gap: '1.5rem' }}>
      <div className="hero animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Shield size={56} strokeWidth={1.5} />
            <div>
              <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0, letterSpacing: '-0.02em' }}>Sistema RRHH y Vigilancia</h1>
              <p style={{ color: '#bfdbfe', marginTop: '0.5rem', fontSize: '1.125rem', maxWidth: '32rem' }}>SPA/PWA para caseta Zebra, supervisión y administración de planta industrial</p>
            </div>
          </div>
        </div>
        {rol && <button onClick={logout} className="btn" style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', background: 'linear-gradient(135deg, #dc2626, #b91c1c)' }}><LogOut size={20} /> Cerrar sesión</button>}
      </div>

      {!loading && <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }} className="animate-fade-in">
        {(rol === 'Supervisor' || rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && (
          <div className="panel" style={{ textAlign: 'center', padding: '1.5rem' }}>
            <Activity size={40} style={{ color: '#059669', marginBottom: '0.5rem' }} />
            <h3 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>{metrics.empleados_presentes}</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>Empleados presentes</p>
          </div>
        )}
        {(rol === 'Supervisor' || rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && (
          <div className="panel" style={{ textAlign: 'center', padding: '1.5rem' }}>
            <AlertTriangle size={40} style={{ color: '#eab308', marginBottom: '0.5rem' }} />
            <h3 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>{metrics.incidencias}</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>Incidencias pendientes</p>
          </div>
        )}
        {(rol === 'Vigilante' || rol === 'Superusuario') && (
          <div className="panel" style={{ textAlign: 'center', padding: '1.5rem' }}>
            <Truck size={40} style={{ color: '#3b82f6', marginBottom: '0.5rem' }} />
            <h3 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>{metrics.fila_externa}</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>Visitantes en fila</p>
          </div>
        )}
      </section>}

      <nav style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }} className="animate-fade-in">
        {!rol && <Link className="card" to="/login" style={{ animationDelay: '0.1s' }}><Shield size={28} /> Login</Link>}
        {(rol === 'Vigilante' || rol === 'Superusuario') && <Link className="card" to="/caseta" style={{ animationDelay: '0.2s' }}><ScanLine size={28} /> Caseta Zebra</Link>}
        {(rol === 'Supervisor' || rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && <Link className="card" to="/supervisor" style={{ animationDelay: '0.3s' }}><ClipboardCheck size={28} /> Supervisor</Link>}
        {(rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && <Link className="card" to="/admin" style={{ animationDelay: '0.4s' }}><Users size={28} /> Admin</Link>}
        {(rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && <Link className="card" to="/historial" style={{ animationDelay: '0.5s' }}><Activity size={28} /> Historial</Link>}
      </nav>

      <section className="panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
        <p style={{ color: '#64748b', fontSize: '0.875rem', margin: 0 }}>📱 Optimizado para terminales Zebra Android y escritorio • PWA instalable</p>
      </section>
    </section>
  </main>
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/caseta" element={<ProtectedRoute allowedRoles={['Vigilante', 'Superusuario']}><ZebraCaseta /></ProtectedRoute>} />
        <Route path="/supervisor" element={<ProtectedRoute allowedRoles={['Supervisor', 'RRHH', 'Administrador', 'Superusuario']}><Supervisor /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute allowedRoles={['RRHH', 'Administrador', 'Superusuario']}><Admin /></ProtectedRoute>} />
        <Route path="/historial" element={<ProtectedRoute allowedRoles={['RRHH', 'Administrador', 'Superusuario']}><Historial /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
