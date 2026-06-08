import { useEffect, useState } from 'react'
import { api } from '../api'
import { Navigation } from '../components/Navigation'

export function Historial() {
  const [historial, setHistorial] = useState([])
  const [historialExternos, setHistorialExternos] = useState([])
  const [empleados, setEmpleados] = useState([])
  const [fechaInicio, setFechaInicio] = useState('')
  const [fechaFin, setFechaFin] = useState('')
  const [empleadoId, setEmpleadoId] = useState('')
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('colaboradores')

  useEffect(() => {
    cargarEmpleados()
    cargarHistorial()
    cargarHistorialExternos()
  }, [])

  async function cargarEmpleados() {
    try {
      const { data } = await api.get('/admin/empleados')
      setEmpleados(data)
    } catch {}
  }

  async function cargarHistorial() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (fechaInicio) params.append('fecha_inicio', fechaInicio)
      if (fechaFin) params.append('fecha_fin', fechaFin)
      if (empleadoId) params.append('empleado_id', empleadoId)
      const { data } = await api.get(`/caseta/historial?${params.toString()}`)
      setHistorial(data)
    } catch {}
    setLoading(false)
  }

  async function cargarHistorialExternos() {
    try {
      const params = new URLSearchParams()
      if (fechaInicio) params.append('fecha_inicio', fechaInicio)
      if (fechaFin) params.append('fecha_fin', fechaFin)
      const { data } = await api.get(`/caseta/historial-externos?${params.toString()}`)
      setHistorialExternos(data)
    } catch {}
  }

  function aplicarFiltros() {
    cargarHistorial()
  }

  function limpiarFiltros() {
    setFechaInicio('')
    setFechaFin('')
    setEmpleadoId('')
    setTimeout(() => {
      cargarHistorial()
      cargarHistorialExternos()
    }, 0)
  }

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc' }}>
    <Navigation />
    <div style={{ padding: '1.5rem' }}>
    <section style={{ maxWidth: '80rem', margin: '0 auto', display: 'grid', gap: '1.5rem' }}>
      <div className="hero animate-fade-in">
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0 }}>📊 Historial de Accesos</h1>
        <p style={{ color: '#bfdbfe', marginTop: '0.5rem', fontSize: '1.125rem' }}>Registro de entradas y salidas de colaboradores</p>
      </div>

      <section className="panel" style={{ padding: '1.5rem', display: 'grid', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            onClick={() => setTab('colaboradores')}
            style={{ 
              padding: '0.75rem 1.5rem', 
              background: tab === 'colaboradores' ? 'linear-gradient(135deg, #3b82f6, #2563eb)' : '#1e293b', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#fff', 
              cursor: 'pointer', 
              fontWeight: 700 
            }}
          >
            👥 Colaboradores
          </button>
          <button 
            onClick={() => setTab('externos')}
            style={{ 
              padding: '0.75rem 1.5rem', 
              background: tab === 'externos' ? 'linear-gradient(135deg, #3b82f6, #2563eb)' : '#1e293b', 
              border: 'none', 
              borderRadius: '0.5rem', 
              color: '#fff', 
              cursor: 'pointer', 
              fontWeight: 700 
            }}
          >
            🚚 Externos
          </button>
        </div>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 900, margin: 0 }}>Filtros</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Fecha inicio</label>
            <input 
              className="input" 
              type="date" 
              value={fechaInicio} 
              onChange={(e) => setFechaInicio(e.target.value)} 
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Fecha fin</label>
            <input 
              className="input" 
              type="date" 
              value={fechaFin} 
              onChange={(e) => setFechaFin(e.target.value)} 
            />
          </div>
          {tab === 'colaboradores' && <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Colaborador (opcional)</label>
            <select 
              className="input" 
              value={empleadoId} 
              onChange={(e) => setEmpleadoId(e.target.value)}
            >
              <option value="">Todos los colaboradores</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
          </div>}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={aplicarFiltros} disabled={loading}>
            {loading ? 'Cargando...' : '🔍 Filtrar'}
          </button>
          <button onClick={limpiarFiltros} style={{ padding: '0.75rem 1.5rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer', fontWeight: 700 }}>
            🗑️ Limpiar
          </button>
        </div>
      </section>

      <section className="panel" style={{ padding: '1.5rem', display: 'grid', gap: '1rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 900, margin: 0 }}>
          Resultados ({tab === 'colaboradores' ? historial.length : historialExternos.length})
        </h2>
        
        {tab === 'colaboradores' && !loading && historial.length > 0 && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.75rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#3b82f6' }}>{historial.length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Total Registros</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#059669' }}>{historial.filter(h => h.estado_registro === 'Normal').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Asistencias Normales</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#eab308' }}>{historial.filter(h => h.estado_registro === 'Incidencia').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Incidencias</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#f97316' }}>{historial.reduce((sum, h) => sum + (h.minutos_extra_calculados || 0), 0)}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Minutos Extras Totales</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#ef4444' }}>{(historial.reduce((sum, h) => sum + (h.minutos_extra_calculados || 0), 0) / 60).toFixed(1)}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Horas Extras Totales</div>
          </div>
        </div>}

        {tab === 'externos' && !loading && historialExternos.length > 0 && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.75rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#3b82f6' }}>{historialExternos.length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Total Visitas</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#059669' }}>{historialExternos.filter(e => e.estado_fila === 'Adentro_Verde').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Adentro</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#eab308' }}>{historialExternos.filter(e => e.estado_fila === 'Retirado').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Retirados</div>
          </div>
        </div>}

        {loading ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Cargando...</p> : 
        tab === 'colaboradores' && historial.length === 0 ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Sin registros de colaboradores</p> :
        tab === 'externos' && historialExternos.length === 0 ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Sin registros de externos</p> :
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {tab === 'colaboradores' && historial.map((h) => (
            <div key={h.id} style={{ 
              padding: '1.25rem', 
              borderRadius: '0.75rem', 
              background: 'linear-gradient(135deg, #1e293b, #0f172a)', 
              border: '1px solid #334155',
              display: 'grid', 
              gap: '0.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 900, margin: 0 }}>{h.nombre_empleado}</h3>
                  <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>#{h.numero_empleado} • {h.puesto} • {h.departamento}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ 
                    padding: '0.25rem 0.75rem', 
                    borderRadius: '0.5rem', 
                    fontSize: '0.75rem', 
                    fontWeight: 700,
                    background: h.estado_registro === 'Normal' ? 'rgba(5,150,105,0.2)' : h.estado_registro === 'Incidencia' ? 'rgba(234,179,8,0.2)' : 'rgba(100,116,139,0.2)',
                    color: h.estado_registro === 'Normal' ? '#059669' : h.estado_registro === 'Incidencia' ? '#eab308' : '#94a3b8'
                  }}>
                    {h.estado_registro}
                  </span>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div>
                  <span style={{ color: '#64748b' }}>📅 Fecha:</span> {h.fecha_turno}
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>🕐 Entrada:</span> {h.hora_entrada_real ? new Date(h.hora_entrada_real).toLocaleTimeString() : '-'}
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>🕕 Salida:</span> {h.hora_salida_real ? new Date(h.hora_salida_real).toLocaleTimeString() : '-'}
                </div>
                {h.minutos_extra_calculados > 0 && <div>
                  <span style={{ color: '#64748b' }}>⏱️ Extra:</span> {h.minutos_extra_calculados} min
                </div>}
              </div>
            </div>
          ))}
          {tab === 'externos' && historialExternos.map((e) => (
            <div key={e.id} style={{ 
              padding: '1.25rem', 
              borderRadius: '0.75rem', 
              background: 'linear-gradient(135deg, #1e293b, #0f172a)', 
              border: '1px solid #334155',
              display: 'grid', 
              gap: '0.5rem' 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 900, margin: 0 }}>{e.nombre_empresa}</h3>
                  <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>{e.tipo_visitante}</p>
                  {(e.chofer || e.placa) && <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0.25rem 0 0' }}>
                    {e.chofer && <span>👤 {e.chofer}</span>}
                    {e.chofer && e.placa && <span> • </span>}
                    {e.placa && <span>🚗 {e.placa}</span>}
                  </p>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ 
                    padding: '0.25rem 0.75rem', 
                    borderRadius: '0.5rem', 
                    fontSize: '0.75rem', 
                    fontWeight: 700,
                    background: e.estado_fila === 'Adentro_Verde' ? 'rgba(5,150,105,0.2)' : e.estado_fila === 'Retirado' ? 'rgba(100,116,139,0.2)' : 'rgba(234,179,8,0.2)',
                    color: e.estado_fila === 'Adentro_Verde' ? '#059669' : e.estado_fila === 'Retirado' ? '#94a3b8' : '#eab308'
                  }}>
                    {e.estado_fila === 'Adentro_Verde' ? 'Adentro' : e.estado_fila === 'Retirado' ? 'Retirado' : 'En Espera'}
                  </span>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div>
                  <span style={{ color: '#64748b' }}>🕐 Llegada:</span> {new Date(e.hora_llegada).toLocaleString()}
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>🕕 Salida:</span> {e.hora_salida ? new Date(e.hora_salida).toLocaleString() : '-'}
                </div>
                {e.anden_asignado && <div>
                  <span style={{ color: '#64748b' }}>📍 Andén:</span> {e.anden_asignado}
                </div>}
              </div>
            </div>
          ))}
        </div>}
      </section>
    </section>
    </div>
  </main>
}
