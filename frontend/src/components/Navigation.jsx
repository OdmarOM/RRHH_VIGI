import { Link } from 'react-router-dom'
import { LogOut, Shield, ScanLine, ClipboardCheck, Users, Activity, Home } from 'lucide-react'

export function Navigation() {
  const rol = localStorage.getItem('rol')

  function logout() {
    localStorage.clear()
    window.location.href = '/'
  }

  return (
    <nav style={{ 
      background: 'linear-gradient(135deg, #1e293b, #0f172a)', 
      padding: '1rem 1.5rem', 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      borderBottom: '1px solid #334155',
      width: '100%',
      boxSizing: 'border-box'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Shield size={24} style={{ color: '#3b82f6' }} />
        <span style={{ fontWeight: 700, fontSize: '1.125rem' }}>Sistema RRHH</span>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <Link 
          to="/home" 
          style={{ 
            padding: '0.5rem 1rem', 
            background: 'transparent', 
            border: 'none', 
            borderRadius: '0.5rem', 
            color: '#94a3b8', 
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.875rem',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'rgba(59, 130, 246, 0.1)'
            e.target.style.color = '#3b82f6'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'transparent'
            e.target.style.color = '#94a3b8'
          }}
        >
          <Home size={18} /> Menú
        </Link>

        {(rol === 'Vigilante' || rol === 'Superusuario') && (
          <Link 
            to="/caseta" 
            style={{ 
              padding: '0.5rem 1rem', 
              background: 'transparent', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#94a3b8', 
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)'
              e.target.style.color = '#3b82f6'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'transparent'
              e.target.style.color = '#94a3b8'
            }}
          >
            <ScanLine size={18} /> Caseta
          </Link>
        )}

        {(rol === 'Supervisor' || rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && (
          <Link 
            to="/supervisor" 
            style={{ 
              padding: '0.5rem 1rem', 
              background: 'transparent', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#94a3b8', 
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)'
              e.target.style.color = '#3b82f6'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'transparent'
              e.target.style.color = '#94a3b8'
            }}
          >
            <ClipboardCheck size={18} /> Supervisor
          </Link>
        )}

        {(rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && (
          <Link 
            to="/admin" 
            style={{ 
              padding: '0.5rem 1rem', 
              background: 'transparent', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#94a3b8', 
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)'
              e.target.style.color = '#3b82f6'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'transparent'
              e.target.style.color = '#94a3b8'
            }}
          >
            <Users size={18} /> Admin
          </Link>
        )}

        {(rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario') && (
          <Link 
            to="/historial" 
            style={{ 
              padding: '0.5rem 1rem', 
              background: 'transparent', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#94a3b8', 
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(59, 130, 246, 0.1)'
              e.target.style.color = '#3b82f6'
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'transparent'
              e.target.style.color = '#94a3b8'
            }}
          >
            <Activity size={18} /> Historial
          </Link>
        )}

        <button 
          onClick={logout}
          style={{ 
            padding: '0.5rem 1rem', 
            background: 'linear-gradient(135deg, #dc2626, #b91c1c)', 
            border: 'none', 
            borderRadius: '0.5rem', 
            color: '#fff', 
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.875rem',
            cursor: 'pointer',
            fontWeight: 600,
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)'
            e.target.style.transform = 'translateY(-1px)'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)'
            e.target.style.transform = 'translateY(0)'
          }}
        >
          <LogOut size={18} /> Cerrar Sesión
        </button>
      </div>
    </nav>
  )
}
