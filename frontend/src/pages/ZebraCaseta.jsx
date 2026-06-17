import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { Navigation } from '../components/Navigation'

export function ZebraCaseta() {
  const [gafete, setGafete] = useState('')
  const [empleadoEscaneado, setEmpleadoEscaneado] = useState(null)
  const [error, setError] = useState(null)
  const [mensaje, setMensaje] = useState(null)
  const [externos, setExternos] = useState([])
  const [observaciones, setObservaciones] = useState([])
  const [modalAnden, setModalAnden] = useState({ visible: false, id: null })
  const [modalExterno, setModalExterno] = useState({ visible: false, tipo: 'Externo', nombre: '', chofer: '', placa: '', fotos: [] })
  const [modalConfirmacionSalida, setModalConfirmacionSalida] = useState({ visible: false, id: null, nombre: '' })
  const [modalEvidencia, setModalEvidencia] = useState({ visible: false, externoId: null, fotos: [] })
  const [creandoExterno, setCreandoExterno] = useState(false)
  const inputRef = useRef(null)

  const OBSERVACIONES_OPCIONES = ['Sin Uniforme', 'Sin Gafete', 'EPP Incompleto', 'Otro']

  useEffect(() => { inputRef.current?.focus(); cargarExternos() }, [])

  async function escanear(valor = gafete) {
    if (!valor.trim()) return
    setError(null)
    setEmpleadoEscaneado(null)
    setObservaciones([])
    try {
      const { data } = await api.post(`/caseta/escanear/${encodeURIComponent(valor.trim())}`)
      setEmpleadoEscaneado(data)
      setGafete('')
      inputRef.current?.focus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al escanear')
      setGafete('')
      inputRef.current?.focus()
    }
  }

  async function confirmarEntrada() {
    if (!empleadoEscaneado) return
    try {
      const { data } = await api.post('/caseta/entrada', { 
        empleado_id: empleadoEscaneado.empleado_id, 
        observaciones 
      })
      if (data.estado_registro === 'INCIDENCIA') {
        setMensaje(data.mensaje)
        setTimeout(() => setMensaje(null), 5000)
      } else if (data.estado_registro === 'VISITA_DESCANSO') {
        setMensaje('🏖️ Entrada registrada como VISITA (ausencia programada activa)')
        setTimeout(() => setMensaje(null), 5000)
      } else {
        setMensaje('✅ Entrada registrada correctamente')
        setTimeout(() => setMensaje(null), 3000)
      }
      setEmpleadoEscaneado(null)
      setObservaciones([])
      cargarExternos()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al confirmar entrada')
    }
  }

  function cancelarEscaneo() {
    setEmpleadoEscaneado(null)
    setObservaciones([])
    setGafete('')
    inputRef.current?.focus()
  }

  function toggleObservacion(obs) {
    setObservaciones(prev => 
      prev.includes(obs) ? prev.filter(o => o !== obs) : [...prev, obs]
    )
  }

  async function cargarExternos() {
    try {
      const { data } = await api.get('/caseta/fila-externos')
      setExternos(data)
    } catch {}
  }

  function abrirModalExterno() {
    setModalExterno({ visible: true, tipo: 'Externo', nombre: '', chofer: '', placa: '', fotos: [] })
  }

  function abrirModalEvidencia(externoId) {
    setModalEvidencia({ visible: true, externoId, fotos: [] })
  }

  async function agregarEvidenciaExterno() {
    if (!modalEvidencia.externoId) return
    try {
      const formData = new FormData()
      modalEvidencia.fotos.forEach((foto) => {
        formData.append('fotos', foto)
      })
      
      await api.post(`/caseta/fila-externos/${modalEvidencia.externoId}/agregar-evidencias`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setModalEvidencia({ visible: false, externoId: null, fotos: [] })
      cargarExternos()
    } catch (err) {
      console.error('Error al agregar evidencia:', err)
    }
  }

  async function crearExterno() {
    if (!modalExterno.nombre.trim() || creandoExterno) return
    setCreandoExterno(true)
    try {
      const formData = new FormData()
      formData.append('tipo_visitante', modalExterno.tipo)
      formData.append('nombre_empresa', modalExterno.nombre)
      if (modalExterno.chofer) formData.append('chofer', modalExterno.chofer)
      if (modalExterno.placa) formData.append('placa', modalExterno.placa)
      
      // Agregar fotos si existen
      modalExterno.fotos.forEach((foto, index) => {
        formData.append(`fotos`, foto)
      })
      
      await api.post('/caseta/fila-externos', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setModalExterno({ visible: false, tipo: 'Externo', nombre: '', chofer: '', placa: '', fotos: [] })
      cargarExternos()
    } catch (err) {
      console.error('Error al crear externo:', err)
    } finally {
      setCreandoExterno(false)
    }
  }

  function abrirModalAnden(id) {
    setModalAnden({ visible: true, id, anden: '' })
  }

  async function asignarAnden() {
    if (!modalAnden.anden.trim()) return
    try {
      await api.post(`/caseta/fila-externos/${modalAnden.id}/asignar`, { anden_asignado: modalAnden.anden })
      setModalAnden({ visible: false, id: null, anden: '' })
      cargarExternos()
    } catch {}
  }

  async function marcarSalidaExterno(id) {
    // Ya no marca la salida directamente, ahora abre modal de confirmación
    const externo = externos.find(e => e.id === id)
    if (externo) {
      setModalConfirmacionSalida({ visible: true, id, nombre: externo.nombre_empresa })
    }
  }

  async function confirmarSalidaExterno() {
    try {
      await api.put(`/caseta/fila-externos/${modalConfirmacionSalida.id}/salida`)
      setModalConfirmacionSalida({ visible: false, id: null, nombre: '' })
      cargarExternos()
    } catch {}
  }

  async function marcarEntradaDirecta(id) {
    try {
      await api.put(`/caseta/fila-externos/${id}/entrada-directa`)
      cargarExternos()
    } catch {}
  }

  async function salidaTemporal(tipo) {
    if (!empleadoEscaneado) return
    try {
      await api.post('/caseta/salida-temporal', { 
        empleado_id: empleadoEscaneado.empleado_id, 
        tipo_salida: tipo 
      })
      setEmpleadoEscaneado(null)
      cargarExternos()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar salida')
    }
  }

  async function salidaFinal() {
    if (!empleadoEscaneado) return
    try {
      await api.post(`/caseta/salida-final/${empleadoEscaneado.empleado_id}`)
      setEmpleadoEscaneado(null)
      cargarExternos()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar salida final')
    }
  }

  async function reingresarSalidaTemporal() {
    if (!empleadoEscaneado) return
    try {
      await api.post('/caseta/regreso-salida-temporal', { 
        empleado_id: empleadoEscaneado.empleado_id
      })
      setEmpleadoEscaneado(null)
      cargarExternos()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar reingreso')
    }
  }

  const estadoColor = empleadoEscaneado?.estado_empleado === 'Laborando' ? '#059669' : empleadoEscaneado?.estado_empleado === 'En_Espera_Pase' ? '#eab308' : empleadoEscaneado?.estado_empleado === 'Salida_Temporal' ? '#f97316' : empleadoEscaneado?.estado_empleado === 'Fuera' ? '#64748b' : '#f97316'
  const estadoBg = empleadoEscaneado?.estado_empleado === 'Laborando' ? 'rgba(5,150,105,0.1)' : empleadoEscaneado?.estado_empleado === 'En_Espera_Pase' ? 'rgba(234,179,8,0.1)' : empleadoEscaneado?.estado_empleado === 'Salida_Temporal' ? 'rgba(249,115,22,0.1)' : 'rgba(100,116,139,0.1)'

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc' }}>
    <Navigation />
    <div style={{ padding: '1rem', display: 'grid', gap: '1rem' }}>
    <section style={{ borderRadius: '1.5rem', background: 'linear-gradient(135deg, #1d4ed8, #2563eb)', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0 }}>Caseta Zebra</h1>
        <p style={{ color: '#bfdbfe', marginTop: '0.5rem', fontSize: '1rem' }}>Escáner físico: al recibir Enter se envía automáticamente</p>
      </div>
      <div style={{ fontSize: '3rem' }}>🏢</div>
    </section>

    <div style={{ display: 'grid', gap: '1rem' }}>
      <input ref={inputRef} className="input" style={{ fontSize: '2rem', padding: '1.5rem', textAlign: 'center', letterSpacing: '0.5em' }} value={gafete} onChange={(e) => setGafete(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') escanear() }} placeholder="ESCANEAR GAFETE" autoFocus disabled={!!empleadoEscaneado} />
      <button className="btn" style={{ fontSize: '2rem', padding: '2rem', fontWeight: 900 }} onClick={() => escanear()} disabled={!!empleadoEscaneado}>📷 REGISTRAR ESCANEO</button>
    </div>

    {error && <section className="panel" style={{ background: 'linear-gradient(145deg, #7f1d1d, #991b1b)', border: '2px solid #dc2626', padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span style={{ fontSize: '2rem' }}>⚠️</span>
        <div>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Error</h3>
          <p style={{ fontSize: '1.125rem', margin: '0.25rem 0 0' }}>{error}</p>
        </div>
      </div>
    </section>}

    {mensaje && <section className="panel" style={{ background: mensaje.includes('✅') ? 'linear-gradient(145deg, #065f46, #047857)' : 'linear-gradient(145deg, #713f12, #92400e)', border: `2px solid ${mensaje.includes('✅') ? '#059669' : '#eab308'}`, padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span style={{ fontSize: '2rem' }}>{mensaje.includes('✅') ? '✅' : '⚠️'}</span>
        <div>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>{mensaje.includes('✅') ? 'Éxito' : 'Atención'}</h3>
          <p style={{ fontSize: '1.125rem', margin: '0.25rem 0 0' }}>{mensaje}</p>
        </div>
      </div>
    </section>}

    {empleadoEscaneado && <section className="panel" style={{ background: estadoBg, border: `2px solid ${estadoColor}`, padding: '1.5rem', display: 'grid', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0, color: estadoColor }}>{empleadoEscaneado.nombre_completo}</h3>
          <p style={{ fontSize: '1.125rem', margin: '0.25rem 0 0' }}>#{empleadoEscaneado.numero_empleado} • {empleadoEscaneado.puesto}</p>
          <p style={{ fontSize: '1rem', color: '#94a3b8', margin: '0.25rem 0 0' }}>Estado: {empleadoEscaneado.estado_empleado} • {empleadoEscaneado.estado_registro === 'VISITA_DESCANSO' ? 'Visita' : empleadoEscaneado.estado_registro}</p>
          {empleadoEscaneado.horario && (
            <p style={{ fontSize: '1rem', margin: '0.25rem 0 0', color: empleadoEscaneado.fuera_horario ? '#dc2626' : '#059669', fontWeight: 700 }}>
              🕐 Hora entrada oficial: {empleadoEscaneado.horario.hora_entrada_oficial} (tolerancia: {empleadoEscaneado.horario.tolerancia_minutos} min)
            </p>
          )}
        </div>
        <div style={{ fontSize: '3rem' }}>{empleadoEscaneado.estado_empleado === 'Laborando' ? '✅' : empleadoEscaneado.estado_empleado === 'En_Espera_Pase' ? '⏳' : '🚪'}</div>
      </div>

      {empleadoEscaneado.pase_espera_expira && <div style={{ padding: '1rem', background: 'rgba(234,179,8,0.2)', borderRadius: '0.75rem', border: '1px solid #eab308' }}>
        <p style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>⏰ Pase expira: {new Date(empleadoEscaneado.pase_espera_expira).toLocaleTimeString()}</p>
      </div>}

      {empleadoEscaneado.fuera_horario && !empleadoEscaneado.ausencias_programadas?.length && <div style={{ padding: '1rem', background: 'rgba(234,179,8,0.2)', borderRadius: '0.75rem', border: '1px solid #eab308' }}>
        <p style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>⚠️ Fuera de horario</p>
        {empleadoEscaneado.horario && <p style={{ fontSize: '0.875rem', margin: '0.25rem 0 0', color: '#94a3b8' }}>Entrada oficial: {empleadoEscaneado.horario.hora_entrada_oficial} (tolerancia: {empleadoEscaneado.horario.tolerancia_minutos} min)</p>}
      </div>}

      {empleadoEscaneado.ausencias_programadas && empleadoEscaneado.ausencias_programadas.length > 0 && <div style={{ padding: '1rem', background: 'rgba(220,38,38,0.2)', borderRadius: '0.75rem', border: '1px solid #dc2626' }}>
        <p style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>🏖️ {empleadoEscaneado.ausencias_programadas[0].tipo}</p>
        {empleadoEscaneado.ausencias_programadas.map((ausencia, idx) => (
          <div key={idx} style={{ marginTop: '0.5rem' }}>
            <p style={{ fontSize: '0.875rem', margin: '0.25rem 0 0', color: '#94a3b8' }}>
              Del {new Date(ausencia.fecha_inicio).toLocaleDateString()} al {new Date(ausencia.fecha_fin).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>}

      {empleadoEscaneado.estado_empleado !== 'Laborando' && empleadoEscaneado.estado_empleado !== 'Salida_Temporal' && <>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.75rem 0' }}>Observaciones (opcional):</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {OBSERVACIONES_OPCIONES.map(obs => (
              <button
                key={obs}
                onClick={() => toggleObservacion(obs)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  border: '2px solid',
                  borderColor: observaciones.includes(obs) ? '#3b82f6' : '#475569',
                  background: observaciones.includes(obs) ? 'rgba(59,130,246,0.2)' : 'transparent',
                  color: '#f8fafc',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {observaciones.includes(obs) ? '✓ ' : ''}{obs}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn-green" onClick={confirmarEntrada} style={{ flex: 1, padding: '1.5rem', fontSize: '1.25rem', fontWeight: 900 }}>✅ INGRESAR</button>
          <button onClick={cancelarEscaneo} style={{ flex: 1, padding: '1.5rem', fontSize: '1.25rem', fontWeight: 900, background: 'linear-gradient(135deg, #dc2626, #b91c1c)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>❌ CANCELAR</button>
        </div>
      </>}

      {empleadoEscaneado.estado_empleado === 'Salida_Temporal' && <div style={{ display: 'flex', gap: '1rem' }}>
        <button onClick={reingresarSalidaTemporal} style={{ flex: 1, padding: '1.5rem', fontSize: '1.25rem', fontWeight: 900, background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>✅ REINGRESAR</button>
        <button onClick={cancelarEscaneo} style={{ flex: 1, padding: '1.5rem', fontSize: '1.25rem', fontWeight: 900, background: 'linear-gradient(135deg, #dc2626, #b91c1c)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>❌ CANCELAR</button>
      </div>}

      {empleadoEscaneado.estado_empleado === 'Laborando' && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
        <button onClick={() => salidaTemporal('Mandado_Trabajo')} style={{ padding: '1.25rem', fontSize: '1rem', fontWeight: 900, background: 'linear-gradient(135deg, #3b82f6, #2563eb)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>🚗 Mandado</button>
        <button onClick={() => salidaTemporal('Comer')} style={{ padding: '1.25rem', fontSize: '1rem', fontWeight: 900, background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>🍽️ Comer</button>
        <button onClick={() => salidaTemporal('Permiso_Personal')} style={{ padding: '1.25rem', fontSize: '1rem', fontWeight: 900, background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>👤 Permiso Personal</button>
        <button onClick={salidaFinal} style={{ padding: '1.25rem', fontSize: '1rem', fontWeight: 900, background: 'linear-gradient(135deg, #6366f1, #4f46e5)', border: 'none', borderRadius: '0.75rem', color: '#fff', cursor: 'pointer' }}>🏁 Fin de Turno</button>
      </div>}
    </section>}

    <section className="panel" style={{ display: 'grid', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>🚚 Fila virtual</h2>
        <button className="btn-green" onClick={abrirModalExterno} style={{ fontSize: '1.125rem', padding: '0.75rem 1.5rem' }}>+ Agregar externo</button>
      </div>
      {externos.length === 0 ? <p style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>Sin visitantes en fila</p> : externos.map((x) => {
        const requiereAnden = x.tipo_visitante === 'Cliente' || x.tipo_visitante === 'Externo'
        return <div key={x.id} style={{ borderRadius: '1rem', padding: '1.25rem', background: x.estado_fila === 'Adentro_Verde' ? 'linear-gradient(135deg, #059669, #047857)' : 'linear-gradient(135deg, #eab308, #ca8a04)', color: x.estado_fila === 'Adentro_Verde' ? '#fff' : '#020617', display: 'grid', gap: '0.5rem' }}>
        <div 
          onClick={() => {
            if (x.estado_fila === 'Espera_Amarillo') {
              if (requiereAnden) {
                abrirModalAnden(x.id)
              } else {
                marcarEntradaDirecta(x.id)
              }
            } else {
              marcarSalidaExterno(x.id)
            }
          }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', cursor: 'pointer' }}
        >
          <div style={{ display: 'grid', gap: '0.25rem', flex: 1 }}>
            <div style={{ fontSize: '1.25rem' }}>{x.nombre_empresa}</div>
            <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>{x.tipo_visitante.replace('_', ' ')}</div>
            {(x.chofer || x.placa) && <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>
              {x.chofer && <span>👤 {x.chofer}</span>}
              {x.chofer && x.placa && <span> • </span>}
              {x.placa && <span>🚗 {x.placa}</span>}
            </div>}
            <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>
              🕐 Llegada: {new Date(x.hora_llegada).toLocaleTimeString()}
              {x.hora_entrada_almacen && <span> • Entrada almacén: {new Date(x.hora_entrada_almacen).toLocaleTimeString()}</span>}
              {x.hora_salida && <span> • Salida: {new Date(x.hora_salida).toLocaleTimeString()}</span>}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {x.estado_fila === 'Adentro_Verde' ? <span>✅ {requiereAnden ? x.anden_asignado : 'Adentro'}</span> : <span>⏳ Espera</span>}
            <span style={{ fontSize: '1.5rem' }}>{x.estado_fila === 'Adentro_Verde' ? '🟢' : '🟡'}</span>
          </div>
        </div>
        {x.estado_fila === 'Espera_Amarillo' && (
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button 
              onClick={(e) => { e.stopPropagation(); abrirModalEvidencia(x.id) }}
              style={{ 
                width: '4rem',
                height: '4rem',
                borderRadius: '50%',
                fontSize: '2rem',
                fontWeight: 700, 
                background: 'rgba(59, 130, 246, 0.95)', 
                border: '3px solid #3b82f6', 
                color: '#fff', 
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                transition: 'transform 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
              onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
              title="Agregar evidencia fotográfica"
            >
              📸
            </button>
          </div>
        )}
      </div>})}
    </section>

    {modalAnden.visible && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="panel" style={{ padding: '2rem', minWidth: '300px' }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Asignar Andén</h3>
        <input className="input" placeholder="Número de andén" value={modalAnden.anden} onChange={(e) => setModalAnden({ ...modalAnden, anden: e.target.value })} style={{ marginBottom: '1rem' }} />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn-green" onClick={asignarAnden} style={{ flex: 1 }}>Asignar</button>
          <button onClick={() => setModalAnden({ visible: false, id: null, anden: '' })} style={{ flex: 1, padding: '0.75rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer' }}>Cancelar</button>
        </div>
      </div>
    </div>}

    {modalExterno.visible && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="panel" style={{ padding: '2rem', minWidth: '350px', display: 'grid', gap: '1rem' }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Registrar Visitante</h3>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Tipo de visitante *</label>
          <select className="input" value={modalExterno.tipo} onChange={(e) => setModalExterno({ ...modalExterno, tipo: e.target.value })}>
            <option value="Externo">Externo</option>
            <option value="Proveedor_Servicio">Proveedor de Servicio</option>
            <option value="Cliente">Cliente</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {modalExterno.tipo === 'Cliente' ? 'Nombre del cliente *' : 'Nombre de la empresa *'}
          </label>
          <input 
            className="input" 
            placeholder={modalExterno.tipo === 'Cliente' ? 'Cliente' : 'Empresa'} 
            value={modalExterno.nombre} 
            onChange={(e) => setModalExterno({ ...modalExterno, nombre: e.target.value })} 
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Nombre del chofer (opcional)</label>
          <input className="input" placeholder="Chofer" value={modalExterno.chofer} onChange={(e) => setModalExterno({ ...modalExterno, chofer: e.target.value })} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Placa del vehículo (opcional)</label>
          <input className="input" placeholder="Placa" value={modalExterno.placa} onChange={(e) => setModalExterno({ ...modalExterno, placa: e.target.value })} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Evidencias fotográficas (opcional)</label>
          <input 
            type="file" 
            accept="image/*" 
            multiple 
            onChange={(e) => setModalExterno({ ...modalExterno, fotos: Array.from(e.target.files) })}
            style={{ marginBottom: '0.5rem' }}
          />
          {modalExterno.fotos.length > 0 && (
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{modalExterno.fotos.length} foto(s) seleccionada(s)</p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn-green" onClick={crearExterno} disabled={creandoExterno} style={{ flex: 1, opacity: creandoExterno ? 0.5 : 1 }}>{creandoExterno ? 'Registrando...' : 'Registrar'}</button>
          <button onClick={() => setModalExterno({ visible: false, tipo: 'Externo', nombre: '', chofer: '', placa: '', fotos: [] })} style={{ flex: 1, padding: '0.75rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer' }}>Cancelar</button>
        </div>
      </div>
    </div>}

    {modalConfirmacionSalida.visible && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="panel" style={{ padding: '2rem', minWidth: '350px', display: 'grid', gap: '1rem' }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Confirmar Salida</h3>
        <p style={{ fontSize: '1rem', margin: 0 }}>¿Estás seguro de que <strong>{modalConfirmacionSalida.nombre}</strong> está saliendo de las instalaciones?</p>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={confirmarSalidaExterno} style={{ flex: 1, padding: '0.75rem', background: '#ef4444', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer', fontWeight: 700 }}>Confirmar Salida</button>
          <button onClick={() => setModalConfirmacionSalida({ visible: false, id: null, nombre: '' })} style={{ flex: 1, padding: '0.75rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer' }}>Cancelar</button>
        </div>
      </div>
    </div>}

    {modalEvidencia.visible && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="panel" style={{ padding: '2rem', minWidth: '350px', display: 'grid', gap: '1rem' }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 900, margin: 0 }}>Agregar Evidencia Fotográfica</h3>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>Fotos</label>
          <input 
            type="file" 
            accept="image/*" 
            multiple 
            onChange={(e) => setModalEvidencia({ ...modalEvidencia, fotos: Array.from(e.target.files) })}
            style={{ marginBottom: '0.5rem' }}
          />
          {modalEvidencia.fotos.length > 0 && (
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{modalEvidencia.fotos.length} foto(s) seleccionada(s)</p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn-green" onClick={agregarEvidenciaExterno} style={{ flex: 1 }}>Agregar</button>
          <button onClick={() => setModalEvidencia({ visible: false, externoId: null, fotos: [] })} style={{ flex: 1, padding: '0.75rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer' }}>Cancelar</button>
        </div>
      </div>
    </div>}
    </div>
  </main>
}
