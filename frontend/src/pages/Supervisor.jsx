import { useEffect, useState } from 'react'
import { api } from '../api'
import { Navigation } from '../components/Navigation'

export function Supervisor() {
  const [items, setItems] = useState([])
  const [empleados, setEmpleados] = useState([])
  const [turnos, setTurnos] = useState([])
  const [plantillas, setPlantillas] = useState([])
  const [detallesPlantilla, setDetallesPlantilla] = useState([])
  const [horasExtra, setHorasExtra] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('incidencias')
  const [turnoForm, setTurnoForm] = useState({ empleado_id: '' })
  const [filtroEmpleados, setFiltroEmpleados] = useState('')

  async function cargar() {
    setLoading(true)
    try {
      const [incData, empData, turnData, plantData, heData] = await Promise.all([
        api.get('/supervisor/incidencias'),
        api.get('/supervisor/empleados'),
        api.get('/supervisor/turnos'),
        api.get('/supervisor/plantillas-turnos'),
        api.get('/supervisor/incidencias/horas-extra')
      ])
      setItems(incData.data)
      setEmpleados(empData.data)
      setTurnos(turnData.data)
      setPlantillas(plantData.data)
      setHorasExtra(heData.data)
    } catch {}
    setLoading(false)
  }

  async function aprobar(id) {
    try {
      await api.post(`/supervisor/aprobar-pase/${id}`)
      setMessage('✅ Pase aprobado correctamente')
      cargar()
    } catch (error) {
      setMessage(error.response?.data?.detail ?? '❌ No se pudo aprobar')
      cargar()
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function validarHoraExtra(bloqueId) {
    try {
      await api.put(`/supervisor/incidencias/horas-extra/bloque/${bloqueId}/validar`)
      setMessage('✅ Bloque de horas extra validado')
      cargar()
    } catch (error) {
      setMessage('❌ Error: ' + (error.response?.data?.detail || 'No se pudo validar'))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function guardarTurno(diaSemana) {
    const turno = turnos.find(t => t.empleado_id === Number(turnoForm.empleado_id) && t.dia_semana === diaSemana)
    if (!turno) {
      setMessage('⚠️ No hay turno para guardar')
      setTimeout(() => setMessage(''), 3000)
      return
    }
    try {
      if (turno.id) {
        await api.put(`/supervisor/turnos/${turno.id}`, { es_descanso: turno.es_descanso })
      } else {
        await api.post('/supervisor/turnos', { 
          empleado_id: turno.empleado_id, 
          dia_semana: turno.dia_semana, 
          es_descanso: turno.es_descanso,
          hora_entrada_oficial: turno.hora_entrada_oficial,
          hora_salida_oficial: turno.hora_salida_oficial,
          tolerancia_minutos: turno.tolerancia_minutos
        })
      }
      setMessage('✅ Turno guardado')
      cargar()
    } catch {
      setMessage('❌ Error al guardar turno')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarTurno(turnoId) {
    try {
      await api.delete(`/supervisor/turnos/${turnoId}`)
      setMessage('✅ Turno eliminado')
      cargar()
    } catch {
      setMessage('❌ Error al eliminar turno')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function cargarDetallesPlantilla(plantillaId) {
    try {
      const { data } = await api.get(`/supervisor/plantillas-turnos/${plantillaId}/detalles`)
      setDetallesPlantilla(data)
    } catch (error) {
      console.error('Error al cargar detalles:', error)
      setMessage('❌ Error al cargar detalles')
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function romperPlantilla(empleadoId) {
    if (!confirm('¿Estás seguro de romper la plantilla de este colaborador? Podrás editar los horarios individualmente.')) return
    try {
      await api.put(`/supervisor/empleados/${empleadoId}/romper-plantilla`)
      setMessage('✅ Plantilla rota correctamente')
      cargar()
    } catch (error) {
      setMessage('❌ Error: ' + (error.response?.data?.detail || 'No se pudo romper la plantilla'))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  useEffect(() => { cargar() }, [])

  const diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

  const getUrgencia = (expira) => {
    if (!expira) return { color: '#64748b', label: 'Sin fecha', icon: '⏳' }
    const minutos = (new Date(expira) - new Date()) / 60000
    if (minutos <= 0) return { color: '#dc2626', label: 'Expirado', icon: '🚨' }
    if (minutos <= 5) return { color: '#ef4444', label: `${Math.floor(minutos)} min`, icon: '🔴' }
    if (minutos <= 15) return { color: '#f97316', label: `${Math.floor(minutos)} min`, icon: '🟠' }
    return { color: '#eab308', label: `${Math.floor(minutos)} min`, icon: '🟡' }
  }

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc' }}>
    <Navigation />
    <div style={{ padding: '1.5rem', display: 'grid', gap: '1.5rem', alignContent: 'start' }}>
    <section style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0 }}>Panel Supervisor</h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Aprobación de pases y gestión de turnos</p>
      </div>
      <button className="btn" onClick={cargar} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>🔄 Actualizar</button>
    </section>

    <div className="tabs">
      <button className={`tab${tab === 'incidencias' ? ' active' : ''}`} onClick={() => setTab('incidencias')}>📋 Pases de Retardo</button>
      <button className={`tab${tab === 'horas-extra' ? ' active' : ''}`} onClick={() => setTab('horas-extra')}>⏰ Horas Extra</button>
      <button className={`tab${tab === 'turnos' ? ' active' : ''}`} onClick={() => setTab('turnos')}>📅 Turnos</button>
    </div>

    {message && <div className="toast" style={{ background: message.includes('✅') ? 'rgba(5,150,105,0.95)' : message.includes('⚠️') ? 'rgba(234,179,8,0.95)' : 'rgba(220,38,38,0.95)', color: '#fff' }}>
      {message}
    </div>}

    {tab === 'incidencias' && (loading ? <p style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>Cargando incidencias...</p> : items.length === 0 ? <section className="panel" style={{ textAlign: 'center', padding: '3rem' }}>
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Sin pases de retardo pendientes</h2>
      <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Todos los pases están al día</p>
    </section> : <section style={{ display: 'grid', gap: '1rem' }}>
      {items.sort((a, b) => new Date(a.pase_espera_expira) - new Date(b.pase_espera_expira)).map((x) => {
        const urgencia = getUrgencia(x.pase_espera_expira)
        return <section key={x.id} className="panel" style={{ border: `2px solid ${urgencia.color}`, padding: '1.5rem', display: 'grid', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: 0 }}>{x.nombre_empleado || 'Colaborador #' + x.empleado_id}</h3>
              <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>#{x.numero_empleado} • Asistencia #{x.id}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: `${urgencia.color}20`, padding: '0.5rem 1rem', borderRadius: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>{urgencia.icon}</span>
              <span style={{ fontWeight: 700, color: urgencia.color }}>{urgencia.label}</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>Expira: {new Date(x.pase_espera_expira).toLocaleString()}</p>
              <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>Estado: {x.estado_registro}</p>
            </div>
            <button className="btn-green" onClick={() => aprobar(x.id)} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>✅ Aprobar pase</button>
          </div>
        </section>
      })}
    </section>)}

    {tab === 'horas-extra' && (loading ? <p style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>Cargando horas extra...</p> : horasExtra.length === 0 ? <section className="panel" style={{ textAlign: 'center', padding: '3rem' }}>
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Sin horas extra pendientes</h2>
      <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Todas las horas extra están validadas</p>
    </section> : <section style={{ display: 'grid', gap: '1rem' }}>
      {horasExtra.map((x) => (
        <section key={x.bloque_id} className="panel" style={{ border: '2px solid #f97316', padding: '1.5rem', display: 'grid', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: 0 }}>{x.nombre_empleado} #{x.numero_empleado}</h3>
              <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>Bloque: {x.tipo_bloque === 'ANTES_INICIO' ? 'Antes del turno' : 'Después del turno'}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(249,115,22,0.2)', padding: '0.5rem 1rem', borderRadius: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>⏰</span>
              <span style={{ fontWeight: 700, color: '#f97316' }}>{Math.floor(x.minutos_extra / 60)}h {x.minutos_extra % 60}m</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>Fecha: {new Date(x.fecha_turno).toLocaleDateString()}</p>
              <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>
                Horario: {new Date(x.hora_inicio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(x.hora_fin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            <button className="btn-green" onClick={() => validarHoraExtra(x.bloque_id)} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>✅ Validar bloque</button>
          </div>
        </section>
      ))}
    </section>)}

    {tab === 'turnos' && <section style={{ display: 'grid', gap: '1.5rem' }}>
      <div className="panel" style={{ padding: '1rem' }}>
        {!turnoForm.empleado_id ? (
          <>
            <input
              className="input"
              placeholder="🔍 Buscar colaborador por número o nombre..."
              value={filtroEmpleados}
              onChange={(e) => setFiltroEmpleados(e.target.value)}
              style={{ marginBottom: '1rem' }}
            />
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {empleados.filter(e =>
                String(e.numero_empleado).toLowerCase().includes(filtroEmpleados.toLowerCase()) ||
                e.nombre_completo.toLowerCase().includes(filtroEmpleados.toLowerCase())
              ).map(e => (
                <div
                  key={e.id}
                  onClick={() => {
                    setTurnoForm({ ...turnoForm, empleado_id: String(e.id) })
                    cargar()
                  }}
                  style={{
                    padding: '1rem',
                    background: 'rgba(30,41,59,0.5)',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    border: '1px solid transparent'
                  }}
                  onMouseEnter={(el) => {
                    el.target.style.background = 'rgba(59, 130, 246, 0.2)'
                    el.target.style.borderColor = '#3b82f6'
                  }}
                  onMouseLeave={(el) => {
                    el.target.style.background = 'rgba(30,41,59,0.5)'
                    el.target.style.borderColor = 'transparent'
                  }}
                >
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 900, margin: 0 }}>{e.numero_empleado} - {e.nombre_completo}</h3>
                  <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>{e.puesto}</p>
                </div>
              ))}
            </div>
          </>
        ) : (() => {
          const empleado = empleados.find(e => e.id === Number(turnoForm.empleado_id))
          const plantillaAsignada = empleado?.plantilla_turno_id ? plantillas.find(p => p.id === empleado.plantilla_turno_id) : null
          
          // Cargar detalles de la plantilla si el empleado tiene una asignada
          if (plantillaAsignada && (detallesPlantilla.length === 0 || detallesPlantilla[0]?.plantilla_id !== plantillaAsignada.id)) {
            cargarDetallesPlantilla(plantillaAsignada.id)
          }
          
          return (
            <div>
              <button
                onClick={() => setTurnoForm({ ...turnoForm, empleado_id: '' })}
                className="btn-sm btn-sm-gray" style={{ marginBottom: '1rem' }}
              >
                ← Volver a lista de colaboradores
              </button>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: '0 0 1rem 0' }}>{empleado?.numero_empleado} - {empleado?.nombre_completo}</h3>
              <div style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Plantilla de Turno</h4>
                {plantillaAsignada ? (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: '#059669', fontWeight: 700 }}>📋 {plantillaAsignada.nombre}</span>
                    <button
                      onClick={() => romperPlantilla(empleado.id)}
                      className="btn-sm btn-sm-yellow"
                    >
                      Romper plantilla
                    </button>
                  </div>
                ) : (
                  <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Sin plantilla asignada (edición individual)</span>
                )}
              </div>
              <div style={{ overflowX: 'auto' }}>
                {plantillaAsignada ? (
                  <>
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1rem' }}>
                      Este colaborador usa la plantilla "{plantillaAsignada.nombre}". Los horarios se muestran en modo solo lectura.
                    </p>
                    <table className="table">
                      <thead>
                        <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Día</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Entrada</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Salida</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tolerancia</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const detallesPlantillaEmpleado = detallesPlantilla.filter(d => d.plantilla_id === plantillaAsignada.id)
                          return diasSemana.map((dia, i) => {
                            const detalle = detallesPlantillaEmpleado.find(d => d.dia_semana === i)
                            return (
                              <tr key={i} style={{ borderBottom: '1px solid #1e293b', background: detalle?.es_descanso ? 'rgba(234,179,8,0.1)' : 'transparent' }}>
                                <td style={{ padding: '0.75rem', fontWeight: 700 }}>{dia}</td>
                                <td style={{ padding: '0.75rem', color: detalle?.es_descanso ? '#64748b' : '#f8fafc' }}>
                                  {detalle?.es_descanso ? 'Descanso' : (detalle?.hora_entrada_oficial || '-')}
                                </td>
                                <td style={{ padding: '0.75rem', color: detalle?.es_descanso ? '#64748b' : '#f8fafc' }}>
                                  {detalle?.es_descanso ? 'Descanso' : (detalle?.hora_salida_oficial || '-')}
                                </td>
                                <td style={{ padding: '0.75rem', color: '#f8fafc' }}>
                                  {detalle?.tolerancia_minutos || '-'}
                                </td>
                                <td style={{ padding: '0.75rem' }}>
                                  {detalle?.es_descanso ? (
                                    <span style={{ color: '#eab308', fontSize: '0.75rem' }}>🏖️ Descanso</span>
                                  ) : (
                                    <span style={{ color: '#059669', fontSize: '0.75rem' }}>✅ Laboral</span>
                                  )}
                                </td>
                              </tr>
                            )
                          })
                        })()}
                      </tbody>
                    </table>
                  </>
                ) : (
                  <table className="table">
                    <thead>
                      <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Día</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Entrada</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Salida</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tolerancia</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Descanso</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Por Asistencia</th>
                        <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {diasSemana.map((dia, i) => {
                        const turno = turnos.find(t => t.empleado_id === Number(turnoForm.empleado_id) && t.dia_semana === i)
                        return (
                          <tr key={i} style={{ borderBottom: '1px solid #1e293b', background: turno?.es_descanso ? 'rgba(234,179,8,0.1)' : 'transparent' }}>
                            <td style={{ padding: '0.75rem', fontWeight: 700 }}>{dia}</td>
                            <td style={{ padding: '0.75rem' }}>
                              <input 
                                className="input" 
                                type="time" 
                                value={turno?.hora_entrada_oficial || ''} 
                                disabled
                                style={{ padding: '0.25rem', background: 'rgba(30,41,59,0.3)' }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                              <input 
                                className="input" 
                                type="time" 
                                value={turno?.hora_salida_oficial || ''} 
                                disabled
                                style={{ padding: '0.25rem', background: 'rgba(30,41,59,0.3)' }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                              <input 
                                className="input" 
                                type="number" 
                                value={turno?.tolerancia_minutos || 15} 
                                disabled
                                style={{ padding: '0.25rem', width: '80px', background: 'rgba(30,41,59,0.3)' }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                              <input 
                                type="checkbox" 
                                checked={turno?.es_descanso || false}
                                onChange={(e) => {
                                  const newTurnos = [...turnos]
                                  const existingIndex = newTurnos.findIndex(t => t.empleado_id === Number(turnoForm.empleado_id) && t.dia_semana === i)
                                  if (existingIndex >= 0) {
                                    newTurnos[existingIndex] = { ...newTurnos[existingIndex], es_descanso: e.target.checked }
                                  } else {
                                    newTurnos.push({ empleado_id: Number(turnoForm.empleado_id), dia_semana: i, hora_entrada_oficial: '', hora_salida_oficial: '', tolerancia_minutos: 15, es_descanso: e.target.checked })
                                  }
                                  setTurnos(newTurnos)
                                }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                              {turno?.es_por_asistencia ? '✅ Sí' : '❌ No'}
                            </td>
                            <td style={{ padding: '0.75rem' }}>
                              {turno && turno.id ? (
                                <button
                                  onClick={() => guardarTurno(i)}
                                  className="btn-sm btn-sm-green"
                                >
                                  Guardar
                                </button>
                              ) : null}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )
        })()}
      </div>
    </section>}
    </div>
  </main>
}
