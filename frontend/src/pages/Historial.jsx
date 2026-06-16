import { useEffect, useState } from 'react'
import { api } from '../api'
import { Navigation } from '../components/Navigation'

export function Historial() {
  const [eventos, setEventos] = useState([])
  const [historialExternos, setHistorialExternos] = useState([])
  const [empleados, setEmpleados] = useState([])
  const [fechaInicio, setFechaInicio] = useState('')
  const [fechaFin, setFechaFin] = useState('')
  const [empleadoId, setEmpleadoId] = useState('')
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('colaboradores')
  const [evidenciasExternos, setEvidenciasExternos] = useState({})

  useEffect(() => {
    cargarEmpleados()
    cargarHistorialExternos()
  }, [])

  async function cargarEmpleados() {
    try {
      const { data } = await api.get('/admin/empleados')
      setEmpleados(data)
    } catch {}
  }

  async function cargarEventos() {
    if (!empleadoId) {
      setEventos([])
      return
    }
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (fechaInicio) params.append('fecha_inicio', fechaInicio)
      if (fechaFin) params.append('fecha_fin', fechaFin)
      const { data } = await api.get(`/caseta/eventos/${empleadoId}?${params.toString()}`)
      setEventos(data)
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
      
      // Cargar evidencias para cada externo
      const evidencias = {}
      for (const externo of data) {
        try {
          const { data: evData } = await api.get(`/caseta/fila-externos/${externo.id}/evidencias`)
          if (evData.length > 0) {
            evidencias[externo.id] = evData
          }
        } catch {}
      }
      setEvidenciasExternos(evidencias)
    } catch {}
  }

  function aplicarFiltros() {
    cargarEventos()
  }

  function limpiarFiltros() {
    setFechaInicio('')
    setFechaFin('')
    setEmpleadoId('')
    setEventos([])
  }

  useEffect(() => {
    cargarEventos()
  }, [empleadoId])

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc' }}>
    <Navigation />
    <div style={{ padding: '1.5rem' }}>
    <section style={{ maxWidth: '80rem', margin: '0 auto', display: 'grid', gap: '1.5rem' }}>
      <div className="hero animate-fade-in">
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0 }}>📊 Historial de Accesos</h1>
        <p style={{ color: '#bfdbfe', marginTop: '0.5rem', fontSize: '1.125rem' }}>Registro de entradas y salidas de colaboradores</p>
      </div>

      <section className="panel" style={{ padding: '1.5rem', display: 'grid', gap: '1rem' }}>
        <div className="tabs">
          <button className={`tab${tab === 'colaboradores' ? ' active' : ''}`} onClick={() => setTab('colaboradores')}>👥 Colaboradores</button>
          <button className={`tab${tab === 'externos' ? ' active' : ''}`} onClick={() => setTab('externos')}>🚚 Externos</button>
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
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Colaborador *</label>
            <select 
              className="input" 
              value={empleadoId} 
              onChange={(e) => setEmpleadoId(e.target.value)}
              required
            >
              <option value="">Seleccionar colaborador...</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
          </div>}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={aplicarFiltros} disabled={loading}>
            {loading ? 'Cargando...' : '🔍 Filtrar'}
          </button>
          <button onClick={limpiarFiltros} className="btn-sm btn-sm-gray" style={{ fontSize: '1rem', padding: '0.7rem 1.25rem' }}>
            🗑️ Limpiar
          </button>
        </div>
      </section>

      <section className="panel" style={{ padding: '1.5rem', display: 'grid', gap: '1rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 900, margin: 0 }}>
          Resultados ({tab === 'colaboradores' ? eventos.length : historialExternos.length})
        </h2>
        
        {tab === 'colaboradores' && !loading && eventos.length > 0 && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.75rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#3b82f6' }}>{eventos.length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Total Eventos</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#059669' }}>{eventos.filter(e => e.tipo_evento === 'Entrada').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Entradas</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#ef4444' }}>{eventos.filter(e => e.tipo_evento === 'Salida').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Salidas</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#eab308' }}>{eventos.filter(e => e.tipo_evento === 'Salida_Temporal').length}</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Salidas Temporales</div>
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
        tab === 'colaboradores' && !empleadoId ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Selecciona un colaborador para ver su historial de eventos</p> :
        tab === 'colaboradores' && eventos.length === 0 ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Sin eventos para este colaborador</p> :
        tab === 'externos' && historialExternos.length === 0 ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Sin registros de externos</p> :
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {tab === 'colaboradores' && eventos.map((e) => (
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
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 900, margin: 0 }}>{e.tipo_evento.replace('_', ' ')}</h3>
                  <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>{e.observaciones || ''}</p>
                  {e.observaciones && e.observaciones.includes('retardo') && <span style={{ 
                    padding: '0.25rem 0.5rem', 
                    borderRadius: '0.25rem', 
                    fontSize: '0.75rem', 
                    fontWeight: 700,
                    background: 'rgba(239,68,68,0.2)',
                    color: '#ef4444'
                  }}>
                    ⚠️ A destiempo
                  </span>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ 
                    padding: '0.25rem 0.75rem', 
                    borderRadius: '0.5rem', 
                    fontSize: '0.75rem', 
                    fontWeight: 700,
                    background: e.tipo_evento === 'Entrada' ? 'rgba(5,150,105,0.2)' : e.tipo_evento === 'Salida' ? 'rgba(239,68,68,0.2)' : 'rgba(234,179,8,0.2)',
                    color: e.tipo_evento === 'Entrada' ? '#059669' : e.tipo_evento === 'Salida' ? '#ef4444' : '#eab308'
                  }}>
                    {e.tipo_evento}
                  </span>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div>
                  <span style={{ color: '#64748b' }}>🕐 Fecha:</span> {new Date(e.fecha_evento).toLocaleString()}
                </div>
                {e.tipo_salida && <div>
                  <span style={{ color: '#64748b' }}>📋 Tipo Salida:</span> {e.tipo_salida}
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
                {e.latitud && e.longitud && <div>
                  <span style={{ color: '#64748b' }}>📍 Ubicación:</span> <a href={`https://maps.google.com/?q=${e.latitud},${e.longitud}`} target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6', textDecoration: 'none' }}>Ver en mapa</a>
                </div>}
              </div>
              {evidenciasExternos[e.id] && evidenciasExternos[e.id].length > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                  <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 0.5rem 0' }}>📸 Evidencias fotográficas:</p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {evidenciasExternos[e.id].map((ev) => (
                      <a
                        key={ev.id}
                        href={`${api.defaults.baseURL}/caseta/fila-externos/${e.id}/evidencias/${ev.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.5rem',
                          background: 'rgba(59, 130, 246, 0.2)',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          color: '#3b82f6',
                          textDecoration: 'none'
                        }}
                      >
                        📷 Foto {new Date(ev.fecha_captura).toLocaleString()}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>}
      </section>
    </section>
    </div>
  </main>
}
