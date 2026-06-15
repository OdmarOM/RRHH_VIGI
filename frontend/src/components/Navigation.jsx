import { Link, useLocation } from 'react-router-dom'
import { LogOut, Shield, ScanLine, ClipboardCheck, Users, Activity, Home } from 'lucide-react'

export function Navigation() {
  const rol = localStorage.getItem('rol')
  const { pathname } = useLocation()

  function logout() {
    localStorage.clear()
    window.location.href = '/'
  }

  const esAdmin = rol === 'RRHH' || rol === 'Administrador' || rol === 'Superusuario'
  const esSupervisor = rol === 'Supervisor' || esAdmin
  const esVigilante = rol === 'Vigilante' || rol === 'Superusuario'

  const links = [
    { to: '/home', label: 'Menú', icon: Home, show: true },
    { to: '/caseta', label: 'Caseta', icon: ScanLine, show: esVigilante },
    { to: '/supervisor', label: 'Supervisor', icon: ClipboardCheck, show: esSupervisor },
    { to: '/admin', label: 'Admin', icon: Users, show: esAdmin },
    { to: '/historial', label: 'Historial', icon: Activity, show: esAdmin },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Shield size={24} style={{ color: '#3b82f6' }} />
        <span>Sistema RRHH</span>
      </div>

      <div className="navbar-links">
        {links.filter(l => l.show).map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className={`nav-link${pathname === to ? ' active' : ''}`}
          >
            <Icon size={18} /> {label}
          </Link>
        ))}

        <button onClick={logout} className="nav-link nav-link-danger">
          <LogOut size={18} /> Cerrar Sesión
        </button>
      </div>
    </nav>
  )
}
