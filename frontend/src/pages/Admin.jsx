import { useEffect, useState } from 'react'
import { api } from '../api'
import { Navigation } from '../components/Navigation'

export function Admin() {
  const [empleados, setEmpleados] = useState([])
  const [turnos, setTurnos] = useState([])
  const [plantillas, setPlantillas] = useState([])
  const [detallesPlantilla, setDetallesPlantilla] = useState([])
  const [departamentos, setDepartamentos] = useState([])
  const [filtro, setFiltro] = useState('')
  const [filtroTurnos, setFiltroTurnos] = useState('')
  const [tab, setTab] = useState('empleados')
  const [form, setForm] = useState({ numero_empleado: '', nombre_completo: '', departamento_id: '', puesto: '' })
  const [turnoForm, setTurnoForm] = useState({ empleado_id: '', dia_semana: 0, hora_entrada: '08:00', hora_salida: '17:00', tolerancia: 15, tolerancia_entrada_previa: 15, tolerancia_salida_posterior: 15, tolerancia_salida_previa: 5, es_descanso: false, es_por_asistencia: false })
  const [plantillaForm, setPlantillaForm] = useState({ nombre: '', descripcion: '', es_rotativa: false, plantilla_semana_par_id: null, plantilla_semana_impar_id: null })
  const [plantillaSeleccionada, setPlantillaSeleccionada] = useState('')
  const [plantillaEfectiva, setPlantillaEfectiva] = useState(null)
  const [detallesTemporales, setDetallesTemporales] = useState({})
  const [editandoEmpleado, setEditandoEmpleado] = useState(null)
  const [editandoPlantilla, setEditandoPlantilla] = useState(null)
  const [message, setMessage] = useState('')
  const [usuariosSistema, setUsuariosSistema] = useState([])
  const [usuarioForm, setUsuarioForm] = useState({ username: '', password: '', rol_id: '', empleado_id: '' })
  const [editandoUsuario, setEditandoUsuario] = useState(null)
  const [supervisoresDepartamentos, setSupervisoresDepartamentos] = useState([])
  const [roles, setRoles] = useState([])
  const [ausencias, setAusencias] = useState([])
  const [filtroAusenciasFecha, setFiltroAusenciasFecha] = useState('')
  const [filtroAusenciasEmpleado, setFiltroAusenciasEmpleado] = useState('')
  const [reporteHoras, setReporteHoras] = useState([])
  const [reporteHorasExtra, setReporteHorasExtra] = useState([])
  const [reporteAsistencias, setReporteAsistencias] = useState([])
  const [visitas, setVisitas] = useState([])
  const [filtroVisitas, setFiltroVisitas] = useState('')
  const [filtroVisitasFechaInicio, setFiltroVisitasFechaInicio] = useState('')
  const [filtroVisitasFechaFin, setFiltroVisitasFechaFin] = useState('')
  const [filtroVisitasEmpleado, setFiltroVisitasEmpleado] = useState('')
  const [filtroCorreccionesEmpleado, setFiltroCorreccionesEmpleado] = useState('')
  const [filtroCorreccionesFecha, setFiltroCorreccionesFecha] = useState('')
  const [correccionesManuales, setCorreccionesManuales] = useState([])
  const [correccionForm, setCorreccionForm] = useState({ empleado_id: '', empleado_busqueda: '', fecha: '', tipo_correccion: 'Horas_Laboradas', minutos_agregados: 0, motivo: '' })
  const [horasExtraPendientes, setHorasExtraPendientes] = useState([])
  const [reporteSalidasTemporales, setReporteSalidasTemporales] = useState([])
  const [reporteForm, setReporteForm] = useState({ fecha_inicio: '', fecha_fin: '', empleado_id: '', corte_semanal: false })
  const [ausenciaForm, setAusenciaForm] = useState({ empleado_id: '', tipo_ausencia: 'Vacaciones', fecha_inicio: '', fecha_fin: '', pagada: true, porcentaje_aportacion: 100, motivo: '' })
  const [menuAbierto, setMenuAbierto] = useState(false)
  const rolUsuario = localStorage.getItem('rol')

  // Calcular semana actual (viernes a viernes) por default
  useEffect(() => {
    const hoy = new Date()
    const diaSemana = hoy.getDay() // 0 = domingo, 6 = sábado

    // Calcular días hasta el viernes más cercano (hacia atrás)
    // Si hoy es viernes (5), el inicio es hoy
    // Si hoy es sábado (6), el inicio es ayer (viernes)
    // Si hoy es domingo (0), el inicio es hace 2 días (viernes)
    // Si hoy es lunes (1), el inicio es hace 3 días (viernes)
    // Si hoy es martes (2), el inicio es hace 4 días (viernes)
    // Si hoy es miércoles (3), el inicio es hace 5 días (viernes)
    // Si hoy es jueves (4), el inicio es hace 6 días (viernes)
    let diasHastaViernes = (diaSemana + 2) % 7
    if (diasHastaViernes === 0) diasHastaViernes = 7

    const viernesPasado = new Date(hoy)
    viernesPasado.setDate(hoy.getDate() - diasHastaViernes)

    // El fin de la semana es el próximo viernes (6 días después del viernes pasado)
    const viernesProximo = new Date(viernesPasado)
    viernesProximo.setDate(viernesPasado.getDate() + 6)

    setReporteForm({
      fecha_inicio: viernesPasado.toISOString().split('T')[0],
      fecha_fin: viernesProximo.toISOString().split('T')[0],
      empleado_id: ''
    })
  }, [])
  const [subTabTurnos, setSubTabTurnos] = useState('turnos-individuales')
  const [subTabReportes, setSubTabReportes] = useState('horas-laboradas')
  const [nuevoDetalle, setNuevoDetalle] = useState({ dia: 0, entrada: '', salida: '', tolerancia: 15, tolerancia_entrada_previa: 15, tolerancia_salida_posterior: 15, tolerancia_salida_previa: 5, esDescanso: false, esPorAsistencia: false })
  const [turnosTemporales, setTurnosTemporales] = useState({})

  async function cargar() {
    try {
      const [empData, turnData, plantData, deptData, userData, supDeptData, rolesData] = await Promise.all([
        api.get('/admin/empleados'),
        api.get('/admin/turnos'),
        api.get('/admin/plantillas-turnos'),
        api.get('/admin/departamentos'),
        api.get('/admin/usuarios-sistema'),
        api.get('/admin/supervisores-departamentos'),
        api.get('/admin/roles')
      ])
      setEmpleados(empData.data)
      setTurnos(turnData.data)
      setPlantillas(plantData.data)
      setDepartamentos(deptData.data)
      setUsuariosSistema(userData.data)
      setSupervisoresDepartamentos(supDeptData.data)
      setRoles(rolesData.data)
      cargarAusencias()
      cargarVisitas()
      cargarHorasExtraPendientes()
      cargarCorreccionesManuales()
    } catch {}
  }

  async function cargarAusencias() {
    try {
      const params = {}
      if (filtroAusenciasFecha) params.fecha = filtroAusenciasFecha
      if (filtroAusenciasEmpleado) params.empleado_id = filtroAusenciasEmpleado
      const { data } = await api.get('/admin/ausencias', { params })
      setAusencias(data)
    } catch {}
  }

  async function cargarCorreccionesManuales() {
    try {
      const params = {}
      if (filtroCorreccionesFecha) params.fecha = filtroCorreccionesFecha
      const { data } = await api.get('/admin/correcciones-manuales', { params })
      // Filtrar por nombre o número de empleado en el frontend
      let filtradas = data
      if (filtroCorreccionesEmpleado) {
        const busqueda = filtroCorreccionesEmpleado.toLowerCase()
        filtradas = data.filter(c => {
          const emp = empleados.find(e => e.id === c.empleado_id)
          if (emp) {
            return emp.nombre_completo.toLowerCase().includes(busqueda) || 
                   emp.numero_empleado.toString().includes(busqueda)
          }
          return false
        })
      }
      setCorreccionesManuales(filtradas)
    } catch {}
  }

  async function crearCorreccionManual() {
    try {
      await api.post('/admin/correcciones-manuales', correccionForm)
      setMessage('✅ Corrección manual agregada')
      setCorreccionForm({ empleado_id: '', empleado_busqueda: '', fecha: '', tipo_correccion: 'Horas_Laboradas', minutos_agregados: 0, motivo: '' })
      cargarCorreccionesManuales()
    } catch {
      setMessage('❌ Error al agregar corrección manual')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarCorreccionManual(correccionId) {
    try {
      await api.delete(`/admin/correcciones-manuales/${correccionId}`)
      setMessage('✅ Corrección manual eliminada')
      cargarCorreccionesManuales()
    } catch {
      setMessage('❌ Error al eliminar corrección manual')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function cargarVisitas() {
    try {
      const params = {}
      if (filtroVisitasFechaInicio) params.fecha_inicio = filtroVisitasFechaInicio
      if (filtroVisitasFechaFin) params.fecha_fin = filtroVisitasFechaFin
      if (filtroVisitasEmpleado) params.empleado_id = filtroVisitasEmpleado
      const { data } = await api.get('/caseta/visitas', { params })
      setVisitas(data)
    } catch {}
  }

  async function cargarHorasExtraPendientes() {
    try {
      const params = {}
      if (filtroVisitasFechaInicio) params.fecha_inicio = filtroVisitasFechaInicio
      if (filtroVisitasFechaFin) params.fecha_fin = filtroVisitasFechaFin
      if (filtroVisitasEmpleado) params.empleado_id = filtroVisitasEmpleado
      const { data } = await api.get('/admin/bloques-horas-extra', { params })
      setHorasExtraPendientes(data)
    } catch (error) {
      console.error('Error al cargar bloques de horas extra:', error)
    }
  }

  async function actualizarVisita(visitaId, nuevoEstado, motivo = null) {
    try {
      await api.put(`/caseta/visitas/${visitaId}`, { 
        estado: nuevoEstado, 
        motivo: motivo 
      })
      setMessage('✅ Visita actualizada')
      cargarVisitas()
    } catch {
      setMessage('❌ Error al actualizar visita')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function actualizarDuracionVisita(visitaId, minutos) {
    try {
      await api.put(`/caseta/visitas/${visitaId}/duracion`, null, { params: { minutos } })
      setMessage('✅ Duración de visita actualizada')
      cargarVisitas()
    } catch {
      setMessage('❌ Error al actualizar duración de visita')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function modificarHorasExtra(asistenciaId, minutos) {
    try {
      await api.put(`/admin/asistencias/${asistenciaId}/modificar-horas-extra`, null, { params: { minutos } })
      setMessage('✅ Horas extra modificadas')
      cargarHorasExtraPendientes()
    } catch {
      setMessage('❌ Error al modificar horas extra')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function autorizarHorasExtra(asistenciaId) {
    try {
      await api.put(`/admin/asistencias/${asistenciaId}/autorizar-horas-extra`)
      setMessage('✅ Horas extra autorizadas')
      cargarHorasExtraPendientes()
    } catch {
      setMessage('❌ Error al autorizar horas extra')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function revocarAutorizacionRRHH(asistenciaId) {
    try {
      await api.put(`/admin/asistencias/${asistenciaId}/revocar-autorizacion-rrhh`)
      setMessage('✅ Autorización RRHH revocada')
      cargarHorasExtraPendientes()
    } catch {
      setMessage('❌ Error al revocar autorización RRHH')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function revocarValidacionSupervisor(asistenciaId) {
    try {
      await api.put(`/admin/asistencias/${asistenciaId}/revocar-validacion-supervisor`)
      setMessage('✅ Validación supervisor revocada')
      cargarHorasExtraPendientes()
    } catch {
      setMessage('❌ Error al revocar validación supervisor')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearEmpleado(event) {
    event.preventDefault()
    try {
      await api.post('/admin/empleados', { ...form, departamento_id: Number(form.departamento_id) })
      setMessage('✅ Colaborador creado')
      setForm({ numero_empleado: '', nombre_completo: '', departamento_id: 1, puesto: '' })
      cargar()
    } catch {
      setMessage('❌ Error al crear colaborador')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  function iniciarEdicionEmpleado(empleado) {
    setEditandoEmpleado(empleado.id)
    setForm({
      numero_empleado: empleado.numero_empleado,
      nombre_completo: empleado.nombre_completo,
      departamento_id: empleado.departamento_id,
      puesto: empleado.puesto
    })
  }

  async function actualizarEmpleado(event) {
    event.preventDefault()
    if (!editandoEmpleado) return
    try {
      await api.put(`/admin/empleados/${editandoEmpleado}`, { ...form, departamento_id: Number(form.departamento_id) })
      setMessage('✅ Colaborador actualizado')
      setEditandoEmpleado(null)
      setForm({ numero_empleado: '', nombre_completo: '', departamento_id: 1, puesto: '' })
      cargar()
    } catch {
      setMessage('❌ Error al actualizar colaborador')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  function cancelarEdicion() {
    setEditandoEmpleado(null)
    setForm({ numero_empleado: '', nombre_completo: '', departamento_id: 1, puesto: '' })
  }

  async function eliminarEmpleado(id) {
    if (!confirm('¿Estás seguro de eliminar este colaborador?')) return
    try {
      await api.delete(`/admin/empleados/${id}`)
      setMessage('✅ Colaborador eliminado')
      cargar()
    } catch {
      setMessage('❌ Error al eliminar colaborador')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function toggleActivoEmpleado(id, activoActual) {
    try {
      await api.put(`/admin/empleados/${id}/activo`, null, { params: { activo: !activoActual } })
      setMessage(`✅ Colaborador ${!activoActual ? 'activado' : 'desactivado'}`)
      cargar()
    } catch {
      setMessage('❌ Error al cambiar estado')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearUsuario(event) {
    event.preventDefault()
    try {
      await api.post('/admin/usuarios-sistema', null, {
        params: {
          username: usuarioForm.username,
          password: usuarioForm.password,
          rol_id: Number(usuarioForm.rol_id),
          empleado_id: usuarioForm.empleado_id ? Number(usuarioForm.empleado_id) : null
        }
      })
      setMessage('✅ Usuario creado')
      setUsuarioForm({ username: '', password: '', rol_id: '', empleado_id: '' })
      cargar()
    } catch {
      setMessage('❌ Error al crear usuario')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function actualizarUsuario(event) {
    event.preventDefault()
    try {
      await api.put(`/admin/usuarios-sistema/${editandoUsuario}`, null, {
        params: {
          username: usuarioForm.username,
          rol_id: Number(usuarioForm.rol_id),
          empleado_id: usuarioForm.empleado_id ? Number(usuarioForm.empleado_id) : null
        }
      })
      setMessage('✅ Usuario actualizado')
      setEditandoUsuario(null)
      setUsuarioForm({ username: '', password: '', rol_id: '', empleado_id: '' })
      cargar()
    } catch {
      setMessage('❌ Error al actualizar usuario')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarUsuario(id) {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return
    try {
      await api.delete(`/admin/usuarios-sistema/${id}`)
      setMessage('✅ Usuario eliminado')
      cargar()
    } catch {
      setMessage('❌ Error al eliminar usuario')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  function iniciarEdicionUsuario(usuario) {
    setEditandoUsuario(usuario.id)
    setUsuarioForm({
      username: usuario.username,
      password: '',
      rol_id: usuario.rol_id,
      empleado_id: usuario.empleado_id || ''
    })
  }

  function cancelarEdicionUsuario() {
    setEditandoUsuario(null)
    setUsuarioForm({ username: '', password: '', rol_id: '', empleado_id: '' })
  }

  async function toggleActivoUsuario(id, activoActual) {
    try {
      await api.put(`/admin/usuarios-sistema/${id}/activo`, null, { params: { activo: !activoActual } })
      setMessage(`✅ Usuario ${!activoActual ? 'activado' : 'desactivado'}`)
      cargar()
    } catch {
      setMessage('❌ Error al cambiar estado')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function asignarSupervisorDepartamento(usuarioId, departamentoId) {
    try {
      await api.post('/admin/supervisores-departamentos', null, { params: { usuario_id: usuarioId, departamento_id: departamentoId } })
      setMessage('✅ Supervisor asignado al departamento')
      cargar()
    } catch {
      setMessage('❌ Error al asignar supervisor')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarSupervisorDepartamento(relacionId) {
    try {
      await api.delete(`/admin/supervisores-departamentos/${relacionId}`)
      setMessage('✅ Relación eliminada')
      cargar()
    } catch {
      setMessage('❌ Error al eliminar relación')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearAusencia(event) {
    event.preventDefault()
    try {
      await api.post('/admin/ausencias', {
        ...ausenciaForm,
        empleado_id: Number(ausenciaForm.empleado_id),
        fecha_inicio: new Date(ausenciaForm.fecha_inicio).toISOString().split('T')[0],
        fecha_fin: new Date(ausenciaForm.fecha_fin).toISOString().split('T')[0],
        porcentaje_aportacion: Number(ausenciaForm.porcentaje_aportacion)
      })
      setMessage('✅ Ausencia creada')
      setAusenciaForm({ empleado_id: '', tipo_ausencia: 'Vacaciones', fecha_inicio: '', fecha_fin: '', pagada: true, porcentaje_aportacion: 100, motivo: '' })
      cargarAusencias()
    } catch {
      setMessage('❌ Error al crear ausencia')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function aprobarAusencia(ausenciaId) {
    try {
      await api.put(`/admin/ausencias/${ausenciaId}/aprobar`)
      setMessage('✅ Ausencia aprobada')
      cargarAusencias()
    } catch {
      setMessage('❌ Error al aprobar ausencia')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarAusencia(ausenciaId) {
    try {
      await api.delete(`/admin/ausencias/${ausenciaId}`)
      setMessage('✅ Ausencia eliminada')
      cargarAusencias()
    } catch {
      setMessage('❌ Error al eliminar ausencia')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function generarReporteHorasLaboradas(event) {
    event.preventDefault()
    try {
      const params = new URLSearchParams()
      params.append('fecha_inicio', reporteForm.fecha_inicio)
      params.append('fecha_fin', reporteForm.fecha_fin)
      if (reporteForm.empleado_id) params.append('empleado_id', reporteForm.empleado_id)
      if (reporteForm.corte_semanal) params.append('corte_semanal', 'true')
      
      const { data } = await api.get(`/admin/reportes/horas-laboradas?${params}`)
      setReporteHoras(data)
      setMessage(`✅ Reporte generado: ${data.length} registros`)
    } catch {
      setMessage('❌ Error al generar reporte')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function generarReporteHorasExtra(event) {
    event.preventDefault()
    try {
      const params = new URLSearchParams()
      params.append('fecha_inicio', reporteForm.fecha_inicio)
      params.append('fecha_fin', reporteForm.fecha_fin)
      if (reporteForm.empleado_id) params.append('empleado_id', reporteForm.empleado_id)
      if (reporteForm.corte_semanal) params.append('corte_semanal', 'true')

      const { data } = await api.get(`/admin/reportes/horas-extra?${params}`)
      setReporteHorasExtra(data)
      setMessage(`✅ Reporte generado: ${data.length} registros`)
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo generar el reporte'))
    }
  }

  async function generarReporteSalidasTemporales(event) {
    event.preventDefault()
    try {
      const params = new URLSearchParams()
      params.append('fecha_inicio', reporteForm.fecha_inicio)
      params.append('fecha_fin', reporteForm.fecha_fin)
      if (reporteForm.empleado_id) params.append('empleado_id', reporteForm.empleado_id)

      const { data } = await api.get(`/admin/reportes/salidas-temporales?${params}`)
      setReporteSalidasTemporales(data)
      setMessage(`✅ Reporte generado: ${data.length} registros`)
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo generar el reporte'))
    }
  }

  async function aprobarHoraExtra(asistencia_id) {
    try {
      await api.put(`/admin/incidencias/horas-extra/${asistencia_id}/aprobar-rrhh`)
      setReporteHorasExtra(reporteHorasExtra.map(r => r.id === asistencia_id ? { ...r, validado_rrhh: true } : r))
      setMessage('✅ Horas extra aprobadas por RRHH')
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo aprobar'))
    }
  }

  async function aprobarBloqueHorasExtraSupervisor(bloque_id) {
    try {
      await api.put(`/admin/bloques-horas-extra/${bloque_id}/aprobar-supervisor`)
      setReporteHorasExtra(reporteHorasExtra.map(r => r.bloque_id === bloque_id ? { ...r, validado_supervisor: true } : r))
      setMessage('✅ Bloque de horas extra aprobado por supervisor')
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo aprobar'))
    }
  }

  async function aprobarBloqueHorasExtraRRHH(bloque_id) {
    try {
      await api.put(`/admin/bloques-horas-extra/${bloque_id}/aprobar-rrhh`)
      setReporteHorasExtra(reporteHorasExtra.map(r => r.bloque_id === bloque_id ? { ...r, validado_rrhh: true, autorizado_completo: true } : r))
      setMessage('✅ Bloque de horas extra aprobado por RRHH')
      cargarHorasExtraPendientes()
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo aprobar'))
    }
  }

  async function rechazarBloqueHorasExtraRRHH(bloque_id) {
    try {
      await api.put(`/admin/bloques-horas-extra/${bloque_id}/rechazar-rrhh`)
      setHorasExtraPendientes(horasExtraPendientes.filter(h => h.id !== bloque_id))
      setMessage('❌ Bloque de horas extra rechazado por RRHH')
    } catch (err) {
      setMessage('❌ Error: ' + (err.response?.data?.detail || 'No se pudo rechazar'))
    }
  }

  async function actualizarMinutosBloqueHorasExtra(bloque_id, minutos) {
    try {
      await api.put(`/admin/bloques-horas-extra/${bloque_id}/actualizar-minutos`, null, { params: { minutos } })
      setMessage('✅ Minutos extra actualizados')
      cargarHorasExtraPendientes()
    } catch {
      setMessage('❌ Error al actualizar minutos extra')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function generarReporteAsistencias(event) {
    event.preventDefault()
    try {
      const params = new URLSearchParams()
      params.append('fecha_inicio', reporteForm.fecha_inicio)
      params.append('fecha_fin', reporteForm.fecha_fin)
      if (reporteForm.empleado_id) params.append('empleado_id', reporteForm.empleado_id)
      if (reporteForm.corte_semanal) params.append('corte_semanal', 'true')

      const { data } = await api.get(`/admin/reportes/asistencias?${params}`)
      setReporteAsistencias(data)
      setMessage(`✅ Reporte generado: ${data.length} registros`)
    } catch {
      setMessage('❌ Error al generar reporte')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function exportarExcel(tipo) {
    try {
      const params = new URLSearchParams()
      params.append('fecha_inicio', reporteForm.fecha_inicio)
      params.append('fecha_fin', reporteForm.fecha_fin)
      if (reporteForm.empleado_id) params.append('empleado_id', reporteForm.empleado_id)
      if (reporteForm.corte_semanal) params.append('corte_semanal', 'true')

      const endpoint = tipo === 'horas-laboradas' ? '/admin/reportes/horas-laboradas/excel' :
                       tipo === 'horas-extra' ? '/admin/reportes/horas-extra/excel' :
                       '/admin/reportes/asistencias/excel'

      const response = await api.get(`${endpoint}?${params}`, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `reporte_${tipo}_${reporteForm.fecha_inicio}_${reporteForm.fecha_fin}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setMessage('✅ Archivo Excel descargado')
    } catch {
      setMessage('❌ Error al exportar Excel')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearTurno(event) {
    event.preventDefault()
    try {
      await api.post('/admin/turnos', { 
        empleado_id: Number(turnoForm.empleado_id), 
        dia_semana: turnoForm.dia_semana,
        hora_entrada_oficial: turnoForm.hora_entrada,
        hora_salida_oficial: turnoForm.hora_salida,
        tolerancia_minutos: Number(turnoForm.tolerancia),
        tolerancia_entrada_previa_minutos: Number(turnoForm.tolerancia_entrada_previa),
        tolerancia_salida_posterior_minutos: Number(turnoForm.tolerancia_salida_posterior),
        tolerancia_salida_previa_minutos: Number(turnoForm.tolerancia_salida_previa),
        es_descanso: turnoForm.es_descanso,
        es_por_asistencia: turnoForm.es_por_asistencia
      })
      setMessage('✅ Turno creado')
      setTurnoForm({ empleado_id: '', dia_semana: 0, hora_entrada: '08:00', hora_salida: '17:00', tolerancia: 15, tolerancia_entrada_previa: 15, tolerancia_salida_posterior: 15, tolerancia_salida_previa: 5, es_descanso: false, es_por_asistencia: false })
      cargar()
    } catch {
      setMessage('❌ Error al crear turno')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function guardarTurno(diaSemana) {
    const turno = turnos.find(t => t.empleado_id === Number(turnoForm.empleado_id) && t.dia_semana === diaSemana)
    const temporal = turnosTemporales[diaSemana] || {}
    
    const horaEntrada = temporal.hora_entrada !== undefined ? temporal.hora_entrada : (turno?.hora_entrada_oficial || '')
    const horaSalida = temporal.hora_salida !== undefined ? temporal.hora_salida : (turno?.hora_salida_oficial || '')
    const tolerancia = temporal.tolerancia !== undefined ? temporal.tolerancia : (turno?.tolerancia_minutos || 15)
    const toleranciaEntradaPrevia = temporal.tolerancia_entrada_previa !== undefined ? temporal.tolerancia_entrada_previa : (turno?.tolerancia_entrada_previa_minutos || 15)
    const toleranciaSalidaPosterior = temporal.tolerancia_salida_posterior !== undefined ? temporal.tolerancia_salida_posterior : (turno?.tolerancia_salida_posterior_minutos || 15)
    const toleranciaSalidaPrevia = temporal.tolerancia_salida_previa !== undefined ? temporal.tolerancia_salida_previa : (turno?.tolerancia_salida_previa_minutos || 5)
    const esDescanso = temporal.es_descanso !== undefined ? temporal.es_descanso : (turno?.es_descanso || false)
    const esPorAsistencia = temporal.es_por_asistencia !== undefined ? temporal.es_por_asistencia : (turno?.es_por_asistencia || false)
    
    if (!esDescanso && !esPorAsistencia && (!horaEntrada || !horaSalida)) {
      setMessage('⚠️ Completa entrada y salida para días laborales')
      setTimeout(() => setMessage(''), 3000)
      return
    }
    
    try {
      const payload = {
        empleado_id: Number(turnoForm.empleado_id),
        dia_semana: diaSemana,
        hora_entrada_oficial: (esDescanso || esPorAsistencia) ? null : horaEntrada,
        hora_salida_oficial: (esDescanso || esPorAsistencia) ? null : horaSalida,
        tolerancia_minutos: tolerancia,
        tolerancia_entrada_previa_minutos: toleranciaEntradaPrevia,
        tolerancia_salida_posterior_minutos: toleranciaSalidaPosterior,
        tolerancia_salida_previa_minutos: toleranciaSalidaPrevia,
        es_descanso: esDescanso,
        es_por_asistencia: esPorAsistencia
      }
      
      if (turno?.id) {
        await api.put(`/admin/turnos/${turno.id}`, payload)
        setMessage('✅ Turno actualizado')
      } else {
        await api.post('/admin/turnos', payload)
        setMessage('✅ Turno guardado')
      }
      
      setTurnosTemporales(prev => {
        const nuevo = { ...prev }
        delete nuevo[diaSemana]
        return nuevo
      })
      cargar()
    } catch (error) {
      console.error('Error al guardar turno:', error)
      setMessage('❌ Error al guardar turno')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarTurno(turnoId) {
    try {
      await api.delete(`/admin/turnos/${turnoId}`)
      setMessage('✅ Turno eliminado')
      cargar()
    } catch {
      setMessage('❌ Error al eliminar turno')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearPlantilla() {
    if (!plantillaForm.nombre.trim()) return
    try {
      await api.post('/admin/plantillas-turnos', null, { params: plantillaForm })
      setMessage('✅ Plantilla creada')
      setPlantillaForm({ nombre: '', descripcion: '', es_rotativa: false, plantilla_semana_par_id: null, plantilla_semana_impar_id: null })
      cargar()
    } catch {
      setMessage('❌ Error al crear plantilla')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function actualizarPlantilla(id, nombre, descripcion, es_rotativa, plantilla_semana_par_id, plantilla_semana_impar_id) {
    try {
      await api.put(`/admin/plantillas-turnos/${id}`, null, { params: { nombre, descripcion, es_rotativa, plantilla_semana_par_id, plantilla_semana_impar_id } })
      setMessage('✅ Plantilla actualizada')
      cargar()
    } catch {
      setMessage('❌ Error al actualizar plantilla')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarPlantilla(id) {
    if (!confirm('¿Estás seguro de eliminar esta plantilla?')) return
    try {
      await api.delete(`/admin/plantillas-turnos/${id}`)
      setMessage('✅ Plantilla eliminada')
      setDetallesPlantilla([])
      cargar()
    } catch {
      setMessage('❌ Error al eliminar plantilla')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function actualizarDetallePlantilla(plantillaId, detalleId, horaEntrada, horaSalida, toleranciaEntradaPrevia, toleranciaEntradaDespues, toleranciaSalidaPrevia, toleranciaSalidaPosterior, esDescanso = false, esPorAsistencia = false) {
    try {
      await api.put(`/admin/plantillas-turnos/${plantillaId}/detalles/${detalleId}`, {
        hora_entrada: horaEntrada,
        hora_salida: horaSalida,
        tolerancia_entrada_previa_minutos: toleranciaEntradaPrevia,
        tolerancia_minutos: toleranciaEntradaDespues,
        tolerancia_salida_previa_minutos: toleranciaSalidaPrevia,
        tolerancia_salida_posterior_minutos: toleranciaSalidaPosterior,
        es_descanso: esDescanso,
        es_por_asistencia: esPorAsistencia
      })
      setMessage('✅ Detalle actualizado')
      await cargarDetallesPlantilla(plantillaId)
    } catch (error) {
      console.error('Error al actualizar detalle:', error)
      setMessage('❌ Error al actualizar detalle')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarDetallePlantilla(plantillaId, detalleId) {
    try {
      await api.delete(`/admin/plantillas-turnos/${plantillaId}/detalles/${detalleId}`)
      setMessage('✅ Detalle eliminado')
      cargarDetallesPlantilla(plantillaId)
    } catch {
      setMessage('❌ Error al eliminar detalle')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function agregarDetallePlantilla(plantillaId, diaSemana, horaEntrada, horaSalida, toleranciaEntradaPrevia, toleranciaEntradaDespues, toleranciaSalidaPrevia, toleranciaSalidaPosterior, esDescanso = false, esPorAsistencia = false) {
    try {
      await api.post(`/admin/plantillas-turnos/${plantillaId}/detalles`, {
        dia_semana: diaSemana,
        hora_entrada: horaEntrada,
        hora_salida: horaSalida,
        tolerancia_entrada_previa_minutos: toleranciaEntradaPrevia,
        tolerancia_minutos: toleranciaEntradaDespues,
        tolerancia_salida_previa_minutos: toleranciaSalidaPrevia,
        tolerancia_salida_posterior_minutos: toleranciaSalidaPosterior,
        es_descanso: esDescanso,
        es_por_asistencia: esPorAsistencia
      })
      setMessage('✅ Detalle agregado')
      await cargarDetallesPlantilla(plantillaId)
    } catch (error) {
      console.error('Error al agregar detalle:', error)
      setMessage('❌ Error al agregar detalle')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function cargarDetallesPlantilla(plantillaId) {
    try {
      const { data } = await api.get(`/admin/plantillas-turnos/${plantillaId}/detalles`)
      setDetallesPlantilla(data)
    } catch (error) {
      setMessage('❌ Error al cargar detalles')
      setTimeout(() => setMessage(''), 3000)
    }
  }

  async function cargarPlantillaEfectiva(empleadoId) {
    try {
      const { data } = await api.get(`/admin/empleados/${empleadoId}/plantilla-efectiva`)
      setPlantillaEfectiva(data)
      if (data.plantilla_efectiva) {
        cargarDetallesPlantilla(data.plantilla_efectiva.id)
      }
    } catch (error) {
      console.error('Error al cargar plantilla efectiva:', error)
    }
  }

  async function asignarPlantillaEmpleado(empleadoId, plantillaId) {
    try {
      await api.put(`/admin/empleados/${empleadoId}/plantilla-turno/${plantillaId}`)
      setMessage('✅ Plantilla asignada')
      await cargar()
    } catch {
      setMessage('❌ Error al asignar plantilla')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function romperPlantillaEmpleado(empleadoId) {
    if (!confirm('¿Estás seguro de romper la referencia a la plantilla y crear horario personal?')) return
    try {
      await api.post(`/admin/empleados/${empleadoId}/romper-plantilla`)
      setMessage('✅ Referencia a plantilla rota, horario personal creado')
      await cargar()
    } catch {
      setMessage('❌ Error al romper referencia a plantilla')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function crearDepartamento(nombre) {
    if (!nombre.trim()) return
    try {
      await api.post('/admin/departamentos', null, { params: { nombre } })
      setMessage('✅ Departamento creado')
      cargar()
    } catch {
      setMessage('❌ Error al crear departamento')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function actualizarDepartamento(id, nombre) {
    try {
      await api.put(`/admin/departamentos/${id}`, null, { params: { nombre } })
      setMessage('✅ Departamento actualizado')
      cargar()
    } catch {
      setMessage('❌ Error al actualizar departamento')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  async function eliminarDepartamento(id) {
    if (!confirm('¿Estás seguro de eliminar este departamento?')) return
    try {
      await api.delete(`/admin/departamentos/${id}`)
      setMessage('✅ Departamento eliminado')
      cargar()
    } catch (error) {
      setMessage('❌ Error: ' + (error.response?.data?.detail || 'No se puede eliminar departamento con colaboradores'))
    }
    setTimeout(() => setMessage(''), 3000)
  }

  useEffect(() => { cargar() }, [])

  const empleadosFiltrados = empleados.filter(e => 
    e.numero_empleado.toLowerCase().includes(filtro.toLowerCase()) ||
    e.nombre_completo.toLowerCase().includes(filtro.toLowerCase()) ||
    e.puesto.toLowerCase().includes(filtro.toLowerCase())
  )

  const diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

  return <main style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc', display: 'flex', flexDirection: 'column' }}>
    <Navigation />
    
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      <aside style={{ 
        width: menuAbierto ? '260px' : '60px', 
        background: 'rgba(15,23,42,0.95)', 
        borderRight: '1px solid #1e293b',
        padding: '1rem',
        transition: 'width 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        flexShrink: 0
      }}>
      <button 
        onClick={() => setMenuAbierto(!menuAbierto)}
        style={{ 
          padding: '0.75rem', 
          background: '#3b82f6', 
          border: 'none', 
          borderRadius: '0.5rem', 
          color: '#fff', 
          cursor: 'pointer', 
          fontSize: '1.25rem',
          marginBottom: '1rem'
        }}
      >
        {menuAbierto ? '◀' : '▶'}
      </button>
      
      {menuAbierto ? (
        <>
          <button className={tab === 'empleados' ? 'btn' : 'card'} onClick={() => setTab('empleados')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>👥 Colaboradores</button>
          <button className={tab === 'turnos' ? 'btn' : 'card'} onClick={() => setTab('turnos')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>📅 Turnos y Plantillas</button>
          <button className={tab === 'ausencias' ? 'btn' : 'card'} onClick={() => setTab('ausencias')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>🏖️ Ausencias</button>
          <button className={tab === 'visitas' ? 'btn' : 'card'} onClick={() => setTab('visitas')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>🚪 Visitas</button>
          <button className={tab === 'correcciones' ? 'btn' : 'card'} onClick={() => setTab('correcciones')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>✏️ Correcciones</button>
          <button className={tab === 'departamentos' ? 'btn' : 'card'} onClick={() => setTab('departamentos')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>🏢 Departamentos</button>
          <button className={tab === 'usuarios' ? 'btn' : 'card'} onClick={() => setTab('usuarios')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>🔐 Usuarios</button>
          <button className={tab === 'reportes' ? 'btn' : 'card'} onClick={() => setTab('reportes')} style={{ width: '100%', padding: '1rem', fontSize: '1rem', textAlign: 'left' }}>📊 Reportes</button>
        </>
      ) : (
        <>
          <button className={tab === 'empleados' ? 'btn' : 'card'} onClick={() => setTab('empleados')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>👥</button>
          <button className={tab === 'turnos' ? 'btn' : 'card'} onClick={() => setTab('turnos')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>📅</button>
          <button className={tab === 'ausencias' ? 'btn' : 'card'} onClick={() => setTab('ausencias')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🏖️</button>
          <button className={tab === 'visitas' ? 'btn' : 'card'} onClick={() => setTab('visitas')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🚪</button>
          <button className={tab === 'correcciones' ? 'btn' : 'card'} onClick={() => setTab('correcciones')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✏️</button>
          <button className={tab === 'departamentos' ? 'btn' : 'card'} onClick={() => setTab('departamentos')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🏢</button>
          <button className={tab === 'usuarios' ? 'btn' : 'card'} onClick={() => setTab('usuarios')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🔐</button>
          <button className={tab === 'reportes' ? 'btn' : 'card'} onClick={() => setTab('reportes')} style={{ width: '100%', padding: '0.75rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>📊</button>
        </>
      )}
    </aside>

    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', flex: 1, overflow: 'auto' }}>
      <section style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0 }}>Administración Operativa</h1>
          <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Gestión de colaboradores, turnos y departamentos</p>
        </div>
        <button className="btn" onClick={cargar} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>🔄 Actualizar</button>
      </section>

      {message && <div className="toast" style={{ background: message.includes('✅') ? 'rgba(5,150,105,0.95)' : message.includes('⚠️') ? 'rgba(234,179,8,0.95)' : 'rgba(220,38,38,0.95)', color: '#fff' }}>
        {message}
      </div>}

      {tab === 'empleados' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <form onSubmit={editandoEmpleado ? actualizarEmpleado : crearEmpleado} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <input className="input" placeholder="Número colaborador" value={form.numero_empleado} onChange={(e) => setForm({ ...form, numero_empleado: e.target.value })} required />
          <input className="input" placeholder="Nombre completo" value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} required />
          <select className="input" value={form.departamento_id} onChange={(e) => setForm({ ...form, departamento_id: e.target.value })} required>
            <option value="">Seleccionar departamento</option>
            {departamentos.map(d => <option key={d.id} value={d.id}>{d.nombre}</option>)}
          </select>
          <input className="input" placeholder="Puesto" value={form.puesto} onChange={(e) => setForm({ ...form, puesto: e.target.value })} required />
          <button className="btn">{editandoEmpleado ? '💾 Actualizar colaborador' : '➕ Crear colaborador'}</button>
          {editandoEmpleado && <button onClick={cancelarEdicion} style={{ padding: '0.75rem 1.5rem', background: '#64748b', border: 'none', borderRadius: '0.5rem', color: '#fff', cursor: 'pointer', fontWeight: 700 }}>❌ Cancelar</button>}
        </form>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input className="input" placeholder="🔍 Buscar por número, nombre o puesto..." value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ flex: 1 }} />
        </div>

        <section style={{ display: 'grid', gap: '0.75rem' }}>
          {empleadosFiltrados.length === 0 ? <p style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>No se encontraron colaboradores</p> : empleadosFiltrados.map((e) => <section key={e.id} className="panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 900, margin: 0 }}>{e.numero_empleado} - {e.nombre_completo}</h3>
              <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>{e.puesto} • Depto: {departamentos.find(d => d.id === e.departamento_id)?.nombre || 'Sin departamento'}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: (e.estado_actual === 'Adentro' || e.estado_actual === 'Laborando') ? 'rgba(5,150,105,0.1)' : e.estado_actual === 'Fuera' ? 'rgba(100,116,139,0.1)' : 'rgba(234,179,8,0.1)', padding: '0.5rem 1rem', borderRadius: '0.75rem' }}>
                <span style={{ fontSize: '1.25rem' }}>{(e.estado_actual === 'Adentro' || e.estado_actual === 'Laborando') ? '✅' : e.estado_actual === 'Fuera' ? '🚪' : '⏳'}</span>
                <span style={{ fontWeight: 700, color: (e.estado_actual === 'Adentro' || e.estado_actual === 'Laborando') ? '#059669' : e.estado_actual === 'Fuera' ? '#64748b' : '#eab308' }}>{e.estado_actual}</span>
              </div>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button onClick={() => iniciarEdicionEmpleado(e)} className="btn-sm btn-sm-blue">✏️ Editar</button>
                <button onClick={() => toggleActivoEmpleado(e.id, e.activo)} className={`btn-sm ${e.activo ? 'btn-sm-yellow' : 'btn-sm-green'}`}>{e.activo ? '🔒 Desactivar' : '✅ Activar'}</button>
                <button onClick={() => eliminarEmpleado(e.id)} className="btn-sm btn-sm-red">🗑️ Eliminar</button>
              </div>
            </div>
          </section>)}
        </section>
      </section>}

      {tab === 'turnos' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className={subTabTurnos === 'turnos-individuales' ? 'btn' : 'card'} onClick={() => setSubTabTurnos('turnos-individuales')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>📅 Turnos Individuales</button>
          <button className={subTabTurnos === 'plantillas' ? 'btn' : 'card'} onClick={() => setSubTabTurnos('plantillas')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>📋 Plantillas</button>
        </div>

        {subTabTurnos === 'turnos-individuales' && <div className="panel" style={{ padding: '1rem' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #3b82f6', borderRadius: '0.5rem', padding: '1rem', marginBottom: '1rem' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#3b82f6', fontSize: '0.9rem' }}>📋 Guía de Tolerancias</h4>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#94a3b8' }}>
              <li><strong>Tol. Entrada - Antes:</strong> Minutos antes del turno que se registran como visita (ej: 15 min antes = visita)</li>
              <li><strong>Tol. Entrada - Desp:</strong> Minutos después del turno que se consideran a tiempo (ej: 15 min después = entrada a tiempo)</li>
              <li><strong>Tol. Salida - Antes:</strong> Minutos antes de salir que se consideran a tiempo (ej: 5 min antes = salida a tiempo)</li>
              <li><strong>Tol. Salida - Desp:</strong> Minutos después de salir que generan horas extra (ej: 15 min después = horas extra)</li>
            </ul>
          </div>
          
          <input
            className="input"
            placeholder="🔍 Buscar colaborador por número o nombre..."
            value={filtroTurnos}
            onChange={(e) => setFiltroTurnos(e.target.value)}
            style={{ marginBottom: '1rem' }}
          />

          {!turnoForm.empleado_id ? (
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {empleados.filter(e =>
                String(e.numero_empleado).toLowerCase().includes(filtroTurnos.toLowerCase()) ||
                e.nombre_completo.toLowerCase().includes(filtroTurnos.toLowerCase())
              ).map(e => {
                const plantillaAsignada = e.plantilla_turno_id ? plantillas.find(p => p.id === e.plantilla_turno_id) : null
                return (
                <div
                  key={e.id}
                  onClick={() => setTurnoForm({ ...turnoForm, empleado_id: String(e.id) })}
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
                  <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>{e.puesto} • Depto: {departamentos.find(d => d.id === e.departamento_id)?.nombre || 'Sin departamento'}</p>
                  <p style={{ color: '#64748b', fontSize: '0.75rem', margin: '0.25rem 0 0' }}>📋 Plantilla: {plantillaAsignada ? plantillaAsignada.nombre : 'Personalizada'}</p>
                </div>
                )
              })}
            </div>
          ) : (() => {
            const empleado = empleados.find(e => e.id === Number(turnoForm.empleado_id))
            const plantillaAsignada = empleado?.plantilla_turno_id ? plantillas.find(p => p.id === empleado.plantilla_turno_id) : null
            
            // Cargar plantilla efectiva si el empleado tiene plantilla asignada
            if (empleado?.plantilla_turno_id && !plantillaEfectiva) {
              cargarPlantillaEfectiva(empleado.id)
            }
            
            return (
              <div>
                <button
                  onClick={() => {
                    setTurnoForm({ ...turnoForm, empleado_id: '' })
                    setTurnosTemporales({})
                    setPlantillaEfectiva(null)
                    setDetallesPlantilla([])
                  }}
                  className="btn-sm btn-sm-gray" style={{ marginBottom: '1rem' }}
                >
                  ← Volver a lista de empleados
                </button>
                <div style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #3b82f6', borderRadius: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 0.25rem 0', color: '#3b82f6' }}>{empleado?.numero_empleado} - {empleado?.nombre_completo}</h3>
                  <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: 0 }}>{empleado?.puesto} • Depto: {departamentos.find(d => d.id === empleado?.departamento_id)?.nombre || 'Sin departamento'}</p>
                </div>
                <div style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Plantilla de Turno</h4>
                  {plantillaEfectiva?.plantilla_efectiva ? (
                    <div>
                      {plantillaEfectiva.es_rotativa && (
                        <div style={{ marginBottom: '0.5rem', padding: '0.5rem', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '0.25rem', fontSize: '0.75rem', color: '#a855f7' }}>
                          🔄 Plantilla rotativa - Esta semana: {plantillaEfectiva.plantilla_efectiva.nombre}
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ color: '#059669', fontWeight: 700 }}>📋 {plantillaEfectiva.plantilla_efectiva.nombre}</span>
                        <button 
                          onClick={() => romperPlantillaEmpleado(Number(turnoForm.empleado_id))}
                          className="btn-sm btn-sm-yellow"
                        >
                          Romper referencia (crear horario personal)
                        </button>
                      </div>
                    </div>
                  ) : plantillaAsignada ? (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: '#059669', fontWeight: 700 }}>📋 {plantillaAsignada.nombre}</span>
                      <button 
                        onClick={() => romperPlantillaEmpleado(Number(turnoForm.empleado_id))}
                        className="btn-sm btn-sm-yellow"
                      >
                        Romper referencia (crear horario personal)
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <select 
                        className="input" 
                        style={{ flex: 1 }}
                        onChange={(e) => {
                          if (e.target.value) {
                            asignarPlantillaEmpleado(Number(turnoForm.empleado_id), Number(e.target.value))
                            e.target.value = ''
                          }
                        }}
                      >
                        <option value="">Seleccionar plantilla...</option>
                        {plantillas.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                      </select>
                    </div>
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
                            <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Por Asistencia</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detallesPlantilla.map(detalle => (
                            <tr key={detalle.id} style={{ borderBottom: '1px solid #1e293b' }}>
                              <td style={{ padding: '0.75rem' }}>{diasSemana[detalle.dia_semana]}</td>
                              <td style={{ padding: '0.75rem' }}>{detalle.hora_entrada_oficial || '-'}</td>
                              <td style={{ padding: '0.75rem' }}>{detalle.hora_salida_oficial || '-'}</td>
                              <td style={{ padding: '0.75rem' }}>{detalle.tolerancia_minutos} min</td>
                              <td style={{ padding: '0.75rem' }}>{detalle.es_descanso ? '🏖️ Descanso' : '💼 Laboral'}</td>
                              <td style={{ padding: '0.75rem' }}>{detalle.es_por_asistencia ? '✅ Sí' : '❌ No'}</td>
                            </tr>
                          ))}
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
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tol. Entrada</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tol. Salida</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Por Asistencia</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {diasSemana.map((dia, idx) => {
                          const turno = turnos.find(t => t.empleado_id === Number(turnoForm.empleado_id) && t.dia_semana === idx)
                          const temporal = turnosTemporales[idx] || {}
                          const valorEntrada = temporal.hora_entrada !== undefined ? temporal.hora_entrada : (turno?.hora_entrada_oficial || '')
                          const valorSalida = temporal.hora_salida !== undefined ? temporal.hora_salida : (turno?.hora_salida_oficial || '')
                          const valorTolerancia = temporal.tolerancia !== undefined ? temporal.tolerancia : (turno?.tolerancia_minutos || 15)
                          const valorToleranciaEntradaPrevia = temporal.tolerancia_entrada_previa !== undefined ? temporal.tolerancia_entrada_previa : (turno?.tolerancia_entrada_previa_minutos || 15)
                          const valorToleranciaSalidaPosterior = temporal.tolerancia_salida_posterior !== undefined ? temporal.tolerancia_salida_posterior : (turno?.tolerancia_salida_posterior_minutos || 15)
                          const valorToleranciaSalidaPrevia = temporal.tolerancia_salida_previa !== undefined ? temporal.tolerancia_salida_previa : (turno?.tolerancia_salida_previa_minutos || 5)
                          const valorDescanso = temporal.es_descanso !== undefined ? temporal.es_descanso : (turno?.es_descanso || false)
                          const valorPorAsistencia = temporal.es_por_asistencia !== undefined ? temporal.es_por_asistencia : (turno?.es_por_asistencia || false)
                          return (
                            <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                              <td style={{ padding: '0.75rem' }}>{dia}</td>
                              <td style={{ padding: '0.75rem' }}>
                                <input
                                  type="time"
                                  className="input"
                                  value={valorEntrada}
                                  onChange={(e) => {
                                    setTurnosTemporales({
                                      ...turnosTemporales,
                                      [idx]: { ...turnosTemporales[idx], hora_entrada: e.target.value }
                                    })
                                  }}
                                  disabled={valorDescanso}
                                  style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem' }}
                                />
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <input
                                  type="time"
                                  className="input"
                                  value={valorSalida}
                                  onChange={(e) => {
                                    setTurnosTemporales({
                                      ...turnosTemporales,
                                      [idx]: { ...turnosTemporales[idx], hora_salida: e.target.value }
                                    })
                                  }}
                                  disabled={valorDescanso}
                                  style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem' }}
                                />
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Antes</span>
                                    <input
                                      type="number"
                                      className="input"
                                      placeholder="15"
                                      value={valorToleranciaEntradaPrevia}
                                      onChange={(e) => {
                                        setTurnosTemporales({
                                          ...turnosTemporales,
                                          [idx]: { ...turnosTemporales[idx], tolerancia_entrada_previa: Number(e.target.value) }
                                        })
                                      }}
                                      style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                                    />
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Desp</span>
                                    <input
                                      type="number"
                                      className="input"
                                      placeholder="15"
                                      value={valorTolerancia}
                                      onChange={(e) => {
                                        setTurnosTemporales({
                                          ...turnosTemporales,
                                          [idx]: { ...turnosTemporales[idx], tolerancia: Number(e.target.value) }
                                        })
                                      }}
                                      style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                                    />
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                                  </div>
                                </div>
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Antes</span>
                                    <input
                                      type="number"
                                      className="input"
                                      placeholder="5"
                                      value={valorToleranciaSalidaPrevia}
                                      onChange={(e) => {
                                        setTurnosTemporales({
                                          ...turnosTemporales,
                                          [idx]: { ...turnosTemporales[idx], tolerancia_salida_previa: Number(e.target.value) }
                                        })
                                      }}
                                      style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                                    />
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Desp</span>
                                    <input
                                      type="number"
                                      className="input"
                                      placeholder="15"
                                      value={valorToleranciaSalidaPosterior}
                                      onChange={(e) => {
                                        setTurnosTemporales({
                                          ...turnosTemporales,
                                          [idx]: { ...turnosTemporales[idx], tolerancia_salida_posterior: Number(e.target.value) }
                                        })
                                      }}
                                      style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                                    />
                                    <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                                  </div>
                                </div>
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <input
                                    type="checkbox"
                                    checked={valorDescanso}
                                    onChange={(e) => {
                                      setTurnosTemporales({
                                        ...turnosTemporales,
                                        [idx]: { ...turnosTemporales[idx], es_descanso: e.target.checked }
                                      })
                                    }}
                                  />
                                  Descanso
                                </label>
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <input
                                    type="checkbox"
                                    checked={valorPorAsistencia}
                                    onChange={(e) => {
                                      setTurnosTemporales({
                                        ...turnosTemporales,
                                        [idx]: { ...turnosTemporales[idx], es_por_asistencia: e.target.checked }
                                      })
                                    }}
                                  />
                                  Por Asistencia
                                </label>
                              </td>
                              <td style={{ padding: '0.75rem' }}>
                                <button
                                  onClick={() => guardarTurno(idx)}
                                  className="btn-sm btn-sm-green"
                                >
                                  💾 Guardar
                                </button>
                                {turno?.id && (
                                  <button
                                    onClick={() => eliminarTurno(turno.id)}
                                    className="btn-sm btn-sm-red" style={{ marginLeft: '0.5rem' }}
                                  >
                                    🗑️
                                  </button>
                                )}
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
        </div>}

        {subTabTurnos === 'plantillas' && <div className="panel" style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Crear Nueva Plantilla</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <input
                  className="input"
                  placeholder="Nombre de la plantilla"
                  value={plantillaForm.nombre}
                  onChange={(e) => setPlantillaForm({ ...plantillaForm, nombre: e.target.value })}
                  style={{ flex: 1 }}
                />
                <input
                  className="input"
                  placeholder="Descripción (opcional)"
                  value={plantillaForm.descripcion}
                  onChange={(e) => setPlantillaForm({ ...plantillaForm, descripcion: e.target.value })}
                  style={{ flex: 1 }}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#e2e8f0' }}>
                  <input
                    type="checkbox"
                    checked={plantillaForm.es_rotativa || false}
                    onChange={(e) => setPlantillaForm({ ...plantillaForm, es_rotativa: e.target.checked })}
                  />
                  Plantilla rotativa (semana par/impar)
                </label>
              </div>
              {plantillaForm.es_rotativa && (
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <select
                    className="input"
                    value={plantillaForm.plantilla_semana_par_id || ''}
                    onChange={(e) => setPlantillaForm({ ...plantillaForm, plantilla_semana_par_id: e.target.value ? parseInt(e.target.value) : null })}
                    style={{ flex: 1 }}
                  >
                    <option value="">Plantilla semana par</option>
                    {plantillas.filter(p => p.id !== plantillaForm.id).map(p => (
                      <option key={p.id} value={p.id}>{p.nombre}</option>
                    ))}
                  </select>
                  <select
                    className="input"
                    value={plantillaForm.plantilla_semana_impar_id || ''}
                    onChange={(e) => setPlantillaForm({ ...plantillaForm, plantilla_semana_impar_id: e.target.value ? parseInt(e.target.value) : null })}
                    style={{ flex: 1 }}
                  >
                    <option value="">Plantilla semana impar</option>
                    {plantillas.filter(p => p.id !== plantillaForm.id).map(p => (
                      <option key={p.id} value={p.id}>{p.nombre}</option>
                    ))}
                  </select>
                </div>
              )}
              <button className="btn" onClick={crearPlantilla}>➕ Crear</button>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Plantillas Existentes</h3>
            {plantillas.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay plantillas creadas</p> : (
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {plantillas.map(p => (
                  <div key={p.id} style={{ padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>{p.nombre}</h4>
                      <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>{p.descripcion || 'Sin descripción'}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button
                        onClick={() => {
                          setPlantillaSeleccionada(p.id)
                          cargarDetallesPlantilla(p.id)
                        }}
                        className="btn-sm btn-sm-blue"
                      >
                        👁️ Ver Detalles
                      </button>
                      <button
                        onClick={() => eliminarPlantilla(p.id)}
                        className="btn-sm btn-sm-red"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {plantillaSeleccionada && (
            <div style={{ padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 0.25rem 0' }}>Detalles de Plantilla</h3>
                  {(() => {
                    const plantilla = plantillas.find(p => p.id === plantillaSeleccionada)
                    return plantilla ? (
                      <p style={{ color: '#3b82f6', fontSize: '0.875rem', margin: 0, fontWeight: 700 }}>📋 {plantilla.nombre} {plantilla.descripcion ? `- ${plantilla.descripcion}` : ''}</p>
                    ) : null
                  })()}
                </div>
                <button
                  onClick={() => {
                    setPlantillaSeleccionada('')
                    setDetallesPlantilla([])
                  }}
                  className="btn-sm btn-sm-gray"
                >
                  ✕ Cerrar
                </button>
              </div>

              <table className="table">
                <thead>
                  <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Día</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Entrada</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Salida</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tol. Entrada</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tol. Salida</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Descanso</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Por Asistencia</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {diasSemana.map((dia, idx) => {
                    const detalle = detallesPlantilla.find(d => d.dia_semana === idx)
                    const temporal = detallesTemporales[idx] || {}
                    const valorEntrada = temporal.hora_entrada !== undefined ? temporal.hora_entrada : (detalle?.hora_entrada_oficial || '')
                    const valorSalida = temporal.hora_salida !== undefined ? temporal.hora_salida : (detalle?.hora_salida_oficial || '')
                    const valorTolEntAntes = temporal.tolerancia_entrada_previa !== undefined ? temporal.tolerancia_entrada_previa : (detalle?.tolerancia_entrada_previa_minutos || 15)
                    const valorTolEntDesp = temporal.tolerancia_entrada_despues !== undefined ? temporal.tolerancia_entrada_despues : (detalle?.tolerancia_minutos || 15)
                    const valorTolSalAntes = temporal.tolerancia_salida_previa !== undefined ? temporal.tolerancia_salida_previa : (detalle?.tolerancia_salida_previa_minutos || 5)
                    const valorTolSalDesp = temporal.tolerancia_salida_posterior !== undefined ? temporal.tolerancia_salida_posterior : (detalle?.tolerancia_salida_posterior_minutos || 15)
                    const valorDescanso = temporal.es_descanso !== undefined ? temporal.es_descanso : (detalle?.es_descanso || false)
                    const valorPorAsistencia = temporal.es_por_asistencia !== undefined ? temporal.es_por_asistencia : (detalle?.es_por_asistencia || false)
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                        <td style={{ padding: '0.75rem' }}>{dia}</td>
                        <td style={{ padding: '0.75rem' }}>
                          <input
                            type="time"
                            className="input"
                            value={valorEntrada}
                            onChange={(e) => {
                              setDetallesTemporales({
                                ...detallesTemporales,
                                [idx]: { ...detallesTemporales[idx], hora_entrada: e.target.value }
                              })
                            }}
                            disabled={valorDescanso || valorPorAsistencia}
                            style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem' }}
                          />
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <input
                            type="time"
                            className="input"
                            value={valorSalida}
                            onChange={(e) => {
                              setDetallesTemporales({
                                ...detallesTemporales,
                                [idx]: { ...detallesTemporales[idx], hora_salida: e.target.value }
                              })
                            }}
                            disabled={valorDescanso || valorPorAsistencia}
                            style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem' }}
                          />
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Antes</span>
                              <input
                                type="number"
                                className="input"
                                placeholder="15"
                                value={valorTolEntAntes}
                                onChange={(e) => {
                                  setDetallesTemporales({
                                    ...detallesTemporales,
                                    [idx]: { ...detallesTemporales[idx], tolerancia_entrada_previa: Number(e.target.value) }
                                  })
                                }}
                                disabled={valorPorAsistencia}
                                style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                              />
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Desp</span>
                              <input
                                type="number"
                                className="input"
                                placeholder="15"
                                value={valorTolEntDesp}
                                onChange={(e) => {
                                  setDetallesTemporales({
                                    ...detallesTemporales,
                                    [idx]: { ...detallesTemporales[idx], tolerancia_entrada_despues: Number(e.target.value) }
                                  })
                                }}
                                disabled={valorPorAsistencia}
                                style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                              />
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Antes</span>
                              <input
                                type="number"
                                className="input"
                                placeholder="5"
                                value={valorTolSalAntes}
                                onChange={(e) => {
                                  setDetallesTemporales({
                                    ...detallesTemporales,
                                    [idx]: { ...detallesTemporales[idx], tolerancia_salida_previa: Number(e.target.value) }
                                  })
                                }}
                                disabled={valorPorAsistencia}
                                style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                              />
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8', width: '20px' }}>Desp</span>
                              <input
                                type="number"
                                className="input"
                                placeholder="15"
                                value={valorTolSalDesp}
                                onChange={(e) => {
                                  setDetallesTemporales({
                                    ...detallesTemporales,
                                    [idx]: { ...detallesTemporales[idx], tolerancia_salida_posterior: Number(e.target.value) }
                                  })
                                }}
                                disabled={valorPorAsistencia}
                                style={{ width: '45px', background: 'rgba(30,41,59,0.5)', border: '1px solid #1e293b', color: '#f8fafc', padding: '0.25rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}
                              />
                              <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>min</span>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input
                              type="checkbox"
                              checked={valorDescanso}
                              onChange={(e) => {
                                setDetallesTemporales({
                                  ...detallesTemporales,
                                  [idx]: { ...detallesTemporales[idx], es_descanso: e.target.checked }
                                })
                              }}
                              disabled={valorPorAsistencia}
                            />
                            Descanso
                          </label>
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input
                              type="checkbox"
                              checked={valorPorAsistencia}
                              onChange={(e) => {
                                setDetallesTemporales({
                                  ...detallesTemporales,
                                  [idx]: {
                                    ...detallesTemporales[idx],
                                    es_por_asistencia: e.target.checked,
                                    hora_entrada: e.target.checked ? '' : detallesTemporales[idx]?.hora_entrada,
                                    hora_salida: e.target.checked ? '' : detallesTemporales[idx]?.hora_salida
                                  }
                                })
                              }}
                              disabled={valorDescanso}
                            />
                            Por Asistencia
                          </label>
                        </td>
                        <td style={{ padding: '0.75rem' }}>
                          {detalle ? (
                            <>
                              <button
                                onClick={() => {
                                  actualizarDetallePlantilla(plantillaSeleccionada, detalle.id, valorEntrada, valorSalida, valorTolEntAntes, valorTolEntDesp, valorTolSalAntes, valorTolSalDesp, valorDescanso, valorPorAsistencia)
                                  setDetallesTemporales(prev => {
                                    const nuevo = { ...prev }
                                    delete nuevo[idx]
                                    return nuevo
                                  })
                                }}
                                className="btn-sm btn-sm-green"
                              >
                                💾
                              </button>
                              <button
                                onClick={() => eliminarDetallePlantilla(plantillaSeleccionada, detalle.id)}
                                className="btn-sm btn-sm-red" style={{ marginLeft: '0.5rem' }}
                              >
                                🗑️
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => {
                                agregarDetallePlantilla(plantillaSeleccionada, idx, valorEntrada, valorSalida, valorTolEntAntes, valorTolEntDesp, valorTolSalAntes, valorTolSalDesp, valorDescanso, valorPorAsistencia)
                                setDetallesTemporales(prev => {
                                  const nuevo = { ...prev }
                                  delete nuevo[idx]
                                  return nuevo
                                })
                              }}
                              className="btn-sm btn-sm-green"
                            >
                              ➕
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>}
      </section>}

      {tab === 'ausencias' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <form onSubmit={crearAusencia} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <select className="input" value={ausenciaForm.empleado_id} onChange={(e) => setAusenciaForm({ ...ausenciaForm, empleado_id: e.target.value })} required>
            <option value="">Seleccionar colaborador</option>
            {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
          </select>
          <select className="input" value={ausenciaForm.tipo_ausencia} onChange={(e) => setAusenciaForm({ ...ausenciaForm, tipo_ausencia: e.target.value })} required>
            <option value="Vacaciones">Vacaciones</option>
            <option value="Incapacidad">Incapacidad</option>
            <option value="Permiso">Permiso</option>
          </select>
          <input className="input" type="date" value={ausenciaForm.fecha_inicio} onChange={(e) => setAusenciaForm({ ...ausenciaForm, fecha_inicio: e.target.value })} required />
          <input className="input" type="date" value={ausenciaForm.fecha_fin} onChange={(e) => setAusenciaForm({ ...ausenciaForm, fecha_fin: e.target.value })} required />
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f8fafc' }}>
            <input type="checkbox" checked={ausenciaForm.pagada} onChange={(e) => setAusenciaForm({ ...ausenciaForm, pagada: e.target.checked })} />
            Pagada
          </label>
          {ausenciaForm.tipo_ausencia === 'Incapacidad' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label style={{ color: '#f8fafc', whiteSpace: 'nowrap' }}>% Aportación:</label>
              <input 
                className="input" 
                type="number" 
                min="0" 
                max="100" 
                value={ausenciaForm.porcentaje_aportacion} 
                onChange={(e) => setAusenciaForm({ ...ausenciaForm, porcentaje_aportacion: Math.min(100, Math.max(0, Number(e.target.value))) })} 
                required 
              />
            </div>
          )}
          <input className="input" placeholder="Motivo (opcional)" value={ausenciaForm.motivo} onChange={(e) => setAusenciaForm({ ...ausenciaForm, motivo: e.target.value })} />
          <button className="btn">➕ Crear Ausencia</button>
        </form>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Ausencias Registradas</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <input
              type="date"
              className="input"
              value={filtroAusenciasFecha}
              onChange={e => setFiltroAusenciasFecha(e.target.value)}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <select
              value={filtroAusenciasEmpleado}
              onChange={e => setFiltroAusenciasEmpleado(e.target.value)}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem', minWidth: '200px' }}
            >
              <option value="">Todos los colaboradores</option>
              {empleados.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.numero_empleado} - {emp.nombre_completo}</option>
              ))}
            </select>
            <button
              onClick={cargarAusencias}
              style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Filtrar
            </button>
            <button
              onClick={() => { setFiltroAusenciasFecha(''); setFiltroAusenciasEmpleado(''); cargarAusencias(); }}
              style={{ padding: '0.5rem 1rem', background: '#64748b', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Limpiar
            </button>
          </div>
          {ausencias.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay ausencias registradas</p> : (
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tipo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Inicio</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fin</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Pagada</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Motivo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {ausencias.map(a => {
                  const emp = empleados.find(e => e.id === a.empleado_id)
                  return (
                    <tr key={a.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? `${emp.numero_empleado} - ${emp.nombre_completo}` : 'N/A'}</td>
                      <td style={{ padding: '0.75rem' }}>{a.tipo_ausencia}</td>
                      <td style={{ padding: '0.75rem' }}>{a.fecha_inicio}</td>
                      <td style={{ padding: '0.75rem' }}>{a.fecha_fin}</td>
                      <td style={{ padding: '0.75rem' }}>{a.pagada ? '✅ Sí' : '❌ No'}</td>
                      <td style={{ padding: '0.75rem' }}>{a.motivo || '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{a.aprobado_rrhh ? '✅ Aprobado' : '⏳ Pendiente'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.25rem' }}>
                          {!a.aprobado_rrhh && <button onClick={() => aprobarAusencia(a.id)} className="btn-sm btn-sm-green">✅ Aprobar</button>}
                          <button onClick={() => eliminarAusencia(a.id)} className="btn-sm btn-sm-red">🗑️</button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>}

      {tab === 'visitas' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Autorización de Horas Extra</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <input
              type="date"
              value={filtroVisitasFechaInicio}
              onChange={e => setFiltroVisitasFechaInicio(e.target.value)}
              placeholder="Fecha inicio"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <input
              type="date"
              value={filtroVisitasFechaFin}
              onChange={e => setFiltroVisitasFechaFin(e.target.value)}
              placeholder="Fecha fin"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <select
              value={filtroVisitasEmpleado}
              onChange={e => setFiltroVisitasEmpleado(e.target.value)}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem', minWidth: '200px' }}
            >
              <option value="">Todos los colaboradores</option>
              {empleados.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.numero_empleado} - {emp.nombre_completo}</option>
              ))}
            </select>
            <button
              onClick={() => { cargarVisitas(); cargarHorasExtraPendientes(); }}
              style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Filtrar
            </button>
            <button
              onClick={() => { setFiltroVisitasFechaInicio(''); setFiltroVisitasFechaFin(''); setFiltroVisitasEmpleado(''); cargarVisitas(); cargarHorasExtraPendientes(); }}
              style={{ padding: '0.5rem 1rem', background: '#64748b', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Limpiar
            </button>
          </div>
          {horasExtraPendientes.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay horas extra pendientes de autorización</p> : (
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tipo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Horario</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Horas Extra</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Validado Supervisor</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {horasExtraPendientes.map(h => {
                  return (
                    <tr key={h.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{h.nombre_empleado} #{h.numero_empleado}</td>
                      <td style={{ padding: '0.75rem' }}>{h.fecha}</td>
                      <td style={{ padding: '0.75rem' }}>{h.tipo_bloque === 'ANTES_INICIO' ? 'Antes del turno' : 'Después del turno'}</td>
                      <td style={{ padding: '0.75rem', fontSize: '0.75rem' }}>
                        {new Date(h.hora_inicio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(h.hora_fin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <input
                          type="number"
                          value={h.minutos_extra}
                          onChange={e => actualizarMinutosBloqueHorasExtra(h.id, parseInt(e.target.value))}
                          style={{ width: '60px', padding: '0.25rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.25rem' }}
                        />
                        min
                      </td>
                      <td style={{ padding: '0.75rem' }}>{h.validado_supervisor ? '✅' : '❌'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                          {h.validado_supervisor && !h.validado_rrhh && (
                            <>
                              <button onClick={() => aprobarBloqueHorasExtraRRHH(h.id)} className="btn-sm btn-sm-green">✅ Autorizar RRHH</button>
                              <button onClick={() => rechazarBloqueHorasExtraRRHH(h.id)} className="btn-sm btn-sm-red">❌ Rechazar</button>
                            </>
                          )}
                          {h.validado_rrhh && (
                            <span style={{ fontSize: '0.75rem', color: '#22c55e' }}>✅ Autorizado</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Visitas (Entradas Fuera de Horario)</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <input
              type="date"
              value={filtroVisitasFechaInicio}
              onChange={e => setFiltroVisitasFechaInicio(e.target.value)}
              placeholder="Fecha inicio"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <input
              type="date"
              value={filtroVisitasFechaFin}
              onChange={e => setFiltroVisitasFechaFin(e.target.value)}
              placeholder="Fecha fin"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <select
              value={filtroVisitasEmpleado}
              onChange={e => setFiltroVisitasEmpleado(e.target.value)}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem', minWidth: '200px' }}
            >
              <option value="">Todos los colaboradores</option>
              {empleados.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.numero_empleado} - {emp.nombre_completo}</option>
              ))}
            </select>
            <button
              onClick={cargarVisitas}
              style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Filtrar
            </button>
            <button
              onClick={() => { setFiltroVisitasFechaInicio(''); setFiltroVisitasFechaFin(''); setFiltroVisitasEmpleado(''); cargarVisitas(); }}
              style={{ padding: '0.5rem 1rem', background: '#64748b', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Limpiar
            </button>
          </div>
          {visitas.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay visitas registradas</p> : (
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Hora Inicio</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Hora Fin</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Duración (min)</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Autorizado Por</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Motivo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {visitas.map(v => {
                  const emp = empleados.find(e => e.id === v.empleado_id)
                  return (
                    <tr key={v.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? `${emp.numero_empleado} - ${emp.nombre_completo}` : 'N/A'}</td>
                      <td style={{ padding: '0.75rem' }}>{v.hora_inicio ? new Date(v.hora_inicio).toLocaleString() : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{v.hora_fin ? new Date(v.hora_fin).toLocaleString() : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span>{v.minutos_duracion || 0} min</span>
                          <input 
                            type="number" 
                            defaultValue={v.minutos_duracion || 0}
                            style={{ width: '60px', padding: '0.25rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '0.25rem', color: '#fff' }}
                            onBlur={(e) => actualizarDuracionVisita(v.id, parseInt(e.target.value))}
                          />
                        </div>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: v.estado === 'Pagada' ? 'rgba(5,150,105,0.2)' : 
                                    v.estado === 'No_Pagada' ? 'rgba(239,68,68,0.2)' : 'rgba(234,179,8,0.2)',
                          color: v.estado === 'Pagada' ? '#059669' : 
                                 v.estado === 'No_Pagada' ? '#ef4444' : '#eab308'
                        }}>
                          {v.estado}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem' }}>{v.autorizado_por ? `Usuario #${v.autorizado_por}` : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{v.motivo || '-'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                          {v.estado === 'Pendiente' && (
                            <>
                              <button onClick={() => actualizarVisita(v.id, 'Pagada', 'Visita autorizada como pagada')} className="btn-sm btn-sm-green">✅ Pagada</button>
                              <button onClick={() => actualizarVisita(v.id, 'No_Pagada', 'Visita autorizada como no pagada')} className="btn-sm btn-sm-red">❌ No Pagada</button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>}

      {tab === 'correcciones' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Agregar Corrección Manual</h3>
          <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Buscar colaborador (nombre o número)"
                value={correccionForm.empleado_busqueda}
                onChange={e => setCorreccionForm({ ...correccionForm, empleado_busqueda: e.target.value })}
                style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem', width: '100%' }}
              />
              {correccionForm.empleado_busqueda && correccionForm.empleado_busqueda.length > 0 && (
                <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', maxHeight: '200px', overflowY: 'auto', zIndex: 10 }}>
                  {empleados
                    .filter(emp => 
                      emp.nombre_completo.toLowerCase().includes(correccionForm.empleado_busqueda.toLowerCase()) ||
                      emp.numero_empleado.toString().includes(correccionForm.empleado_busqueda)
                    )
                    .slice(0, 10)
                    .map(emp => (
                      <div
                        key={emp.id}
                        onClick={() => setCorreccionForm({ ...correccionForm, empleado_id: emp.id, empleado_busqueda: `${emp.numero_empleado} - ${emp.nombre_completo}` })}
                        style={{ padding: '0.5rem', cursor: 'pointer', borderBottom: '1px solid #334155' }}
                        onMouseEnter={e => e.target.style.background = '#334155'}
                        onMouseLeave={e => e.target.style.background = '#1e293b'}
                      >
                        {emp.numero_empleado} - {emp.nombre_completo}
                      </div>
                    ))}
                </div>
              )}
            </div>
            <input
              type="date"
              value={correccionForm.fecha}
              onChange={e => setCorreccionForm({ ...correccionForm, fecha: e.target.value })}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <select
              value={correccionForm.tipo_correccion}
              onChange={e => setCorreccionForm({ ...correccionForm, tipo_correccion: e.target.value })}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            >
              <option value="Horas_Laboradas">Horas Laboradas</option>
              <option value="Horas_Extra">Horas Extra</option>
              <option value="Incidencia">Incidencia</option>
              <option value="Permiso">Permiso</option>
            </select>
            <input
              type="number"
              step="0.01"
              value={correccionForm.minutos_agregados}
              onChange={e => setCorreccionForm({ ...correccionForm, minutos_agregados: parseFloat(e.target.value) || 0 })}
              placeholder="Minutos (ej: 30 para 30 min, -15 para restar 15 min)"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <input
              type="text"
              value={correccionForm.motivo}
              onChange={e => setCorreccionForm({ ...correccionForm, motivo: e.target.value })}
              placeholder="Motivo"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <button
              onClick={crearCorreccionManual}
              style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Agregar Corrección
            </button>
          </div>
        </div>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Historial de Correcciones Manuales</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Buscar colaborador (nombre o número)"
              value={filtroCorreccionesEmpleado}
              onChange={e => setFiltroCorreccionesEmpleado(e.target.value)}
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem', minWidth: '250px' }}
            />
            <input
              type="date"
              value={filtroCorreccionesFecha}
              onChange={e => setFiltroCorreccionesFecha(e.target.value)}
              placeholder="Fecha asignada"
              style={{ padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', borderRadius: '0.375rem' }}
            />
            <button
              onClick={cargarCorreccionesManuales}
              style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Filtrar
            </button>
            <button
              onClick={() => { setFiltroCorreccionesEmpleado(''); setFiltroCorreccionesFecha(''); cargarCorreccionesManuales(); }}
              style={{ padding: '0.5rem 1rem', background: '#64748b', color: '#f8fafc', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Limpiar
            </button>
          </div>
          {correccionesManuales.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay correcciones manuales registradas</p> : (
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha Asignada</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tipo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Minutos</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Motivo</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha Registro</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {correccionesManuales.map(c => {
                  const emp = empleados.find(e => e.id === c.empleado_id)
                  return (
                    <tr key={c.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? `${emp.numero_empleado} - ${emp.nombre_completo}` : 'N/A'}</td>
                      <td style={{ padding: '0.75rem' }}>{c.fecha}</td>
                      <td style={{ padding: '0.75rem' }}>{c.tipo_correccion}</td>
                      <td style={{ padding: '0.75rem' }}>{c.minutos_agregados > 0 ? `+${c.minutos_agregados}` : c.minutos_agregados}</td>
                      <td style={{ padding: '0.75rem' }}>{c.motivo}</td>
                      <td style={{ padding: '0.75rem' }}>{new Date(c.fecha_registro).toLocaleString()}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <button onClick={() => eliminarCorreccionManual(c.id)} className="btn-sm btn-sm-red">Eliminar</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>}

      {tab === 'departamentos' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Crear Nuevo Departamento</h3>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input 
              className="input" 
              placeholder="Nombre del departamento" 
              style={{ flex: 1 }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  crearDepartamento(e.target.value)
                  e.target.value = ''
                }
              }}
            />
            <button className="btn" onClick={(e) => {
              const input = e.target.previousElementSibling
              crearDepartamento(input.value)
              input.value = ''
            }}>➕ Crear</button>
          </div>
        </div>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Departamentos</h3>
          {departamentos.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay departamentos creados</p> : (
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {departamentos.map(d => (
                <div key={d.id} style={{ padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <input
                    className="input"
                    value={d.nombre}
                    style={{ flex: 1, background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '1rem' }}
                    onChange={(e) => actualizarDepartamento(d.id, e.target.value)}
                  />
                  <button
                    onClick={() => eliminarDepartamento(d.id)}
                    style={{ padding: '0.5rem 1rem', background: '#dc2626', border: 'none', borderRadius: '0.25rem', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', marginLeft: '0.5rem' }}
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>}

      {tab === 'usuarios' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <form onSubmit={editandoUsuario ? actualizarUsuario : crearUsuario} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <input className="input" placeholder="Usuario" value={usuarioForm.username} onChange={(e) => setUsuarioForm({ ...usuarioForm, username: e.target.value })} required />
          <input className="input" type="password" placeholder="Contraseña" value={usuarioForm.password} onChange={(e) => setUsuarioForm({ ...usuarioForm, password: e.target.value })} required={!editandoUsuario} />
          <select className="input" value={usuarioForm.rol_id} onChange={(e) => setUsuarioForm({ ...usuarioForm, rol_id: e.target.value })} required>
            <option value="">Seleccionar rol</option>
            {roles.filter(r => {
              // Filtrar roles según jerarquía: superusuario > admin > rrhh > supervisor
              if (rolUsuario === 'Superusuario') return true
              if (rolUsuario === 'Administrador') return r.nombre !== 'Superusuario'
              if (rolUsuario === 'RRHH') return r.nombre !== 'Superusuario' && r.nombre !== 'Administrador' && r.nombre !== 'RRHH'
              if (rolUsuario === 'Supervisor') return false
              return false
            }).map(r => <option key={r.id} value={r.id}>{r.nombre}</option>)}
          </select>
          <select className="input" value={usuarioForm.empleado_id} onChange={(e) => setUsuarioForm({ ...usuarioForm, empleado_id: e.target.value })}>
            <option value="">Sin empleado asociado</option>
            {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
          </select>
          <button className="btn" type="submit">{editandoUsuario ? 'Actualizar' : 'Crear'} Usuario</button>
          {editandoUsuario && <button className="btn" type="button" onClick={cancelarEdicionUsuario} style={{ background: '#64748b' }}>Cancelar</button>}
        </form>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Usuarios del Sistema</h3>
          {usuariosSistema.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay usuarios creados</p> : (
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {usuariosSistema.map(u => (
                <div key={u.id} style={{ padding: '1rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>{u.username}</h4>
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>
                      Rol: {u.rol} {u.empleado_nombre ? `• Empleado: ${u.empleado_nombre}` : ''} • {u.activo ? '✅ Activo' : '🔒 Inactivo'}
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button onClick={() => iniciarEdicionUsuario(u)} className="btn-sm btn-sm-blue">✏️ Editar</button>
                    <button onClick={() => toggleActivoUsuario(u.id, u.activo)} className={`btn-sm ${u.activo ? 'btn-sm-yellow' : 'btn-sm-green'}`}>{u.activo ? '🔒 Desactivar' : '✅ Activar'}</button>
                    <button onClick={() => eliminarUsuario(u.id)} className="btn-sm btn-sm-red">🗑️ Eliminar</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel" style={{ padding: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Asignar Supervisor a Departamento</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
            <select className="input" style={{ flex: 1 }} id="supervisor-select">
              <option value="">Seleccionar supervisor</option>
              {usuariosSistema.filter(u => u.rol === 'Supervisor').map(u => <option key={u.id} value={u.id}>{u.username}</option>)}
            </select>
            <select className="input" style={{ flex: 1 }} id="departamento-select">
              <option value="">Seleccionar departamento</option>
              {departamentos.map(d => <option key={d.id} value={d.id}>{d.nombre}</option>)}
            </select>
            <button className="btn" onClick={() => {
              const supervisorId = document.getElementById('supervisor-select').value
              const departamentoId = document.getElementById('departamento-select').value
              if (supervisorId && departamentoId) {
                asignarSupervisorDepartamento(Number(supervisorId), Number(departamentoId))
                document.getElementById('supervisor-select').value = ''
                document.getElementById('departamento-select').value = ''
              }
            }}>Asignar</button>
          </div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Relaciones Actuales</h4>
          {supervisoresDepartamentos.length === 0 ? <p style={{ color: '#94a3b8' }}>No hay relaciones asignadas</p> : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {supervisoresDepartamentos.map(r => (
                <div key={r.id} style={{ padding: '0.75rem', background: 'rgba(30,41,59,0.5)', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.875rem' }}>{r.usuario_nombre} → {r.departamento_nombre}</span>
                  <button onClick={() => eliminarSupervisorDepartamento(r.id)} style={{ padding: '0.25rem 0.5rem', background: '#dc2626', border: 'none', borderRadius: '0.25rem', color: '#fff', cursor: 'pointer', fontSize: '0.75rem' }}>Eliminar</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>}

      {tab === 'reportes' && <section style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className={subTabReportes === 'horas-laboradas' ? 'btn' : 'card'} onClick={() => setSubTabReportes('horas-laboradas')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>⏱️ Horas Laboradas</button>
          <button className={subTabReportes === 'horas-extra' ? 'btn' : 'card'} onClick={() => setSubTabReportes('horas-extra')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>⚡ Horas Extra</button>
          <button className={subTabReportes === 'salidas-temporales' ? 'btn' : 'card'} onClick={() => setSubTabReportes('salidas-temporales')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>🚪 Salidas Temporales</button>
          <button className={subTabReportes === 'asistencias' ? 'btn' : 'card'} onClick={() => setSubTabReportes('asistencias')} style={{ flex: 1, padding: '0.75rem', fontSize: '1rem' }}>✅ Asistencias</button>
        </div>

        {subTabReportes === 'horas-laboradas' && <section style={{ display: 'grid', gap: '1.5rem' }}>
          <form onSubmit={generarReporteHorasLaboradas} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
            <input className="input" type="date" value={reporteForm.fecha_inicio} onChange={(e) => setReporteForm({ ...reporteForm, fecha_inicio: e.target.value })} required />
            <input className="input" type="date" value={reporteForm.fecha_fin} onChange={(e) => setReporteForm({ ...reporteForm, fecha_fin: e.target.value })} required />
            <select className="input" value={reporteForm.empleado_id} onChange={(e) => setReporteForm({ ...reporteForm, empleado_id: e.target.value })}>
              <option value="">Todos los colaboradores</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#fff' }}>
              <input 
                type="checkbox" 
                checked={reporteForm.corte_semanal} 
                onChange={(e) => setReporteForm({ ...reporteForm, corte_semanal: e.target.checked })}
                style={{ width: '1rem', height: '1rem' }}
              />
              Corte semanal (Viernes 8am - Viernes 8am)
            </label>
            <button className="btn">📊 Generar Reporte</button>
            <button 
              type="button" 
              onClick={() => exportarExcel('horas-laboradas')}
              className="btn-green"
            >
              📥 Exportar Excel
            </button>
          </form>

          {reporteHoras.length > 0 && <div className="panel" style={{ padding: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Resultados: {reporteHoras.length} registros</h3>
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Entrada</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Salida</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Horas Laboradas</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Minutos Permiso</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Correcciones</th>
                </tr>
              </thead>
              <tbody>
                {reporteHoras.map((r, i) => {
                  const emp = empleados.find(e => e.id === r.empleado_id)
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? emp.nombre_completo : r.empleado_id}</td>
                      <td style={{ padding: '0.75rem' }}>{r.fecha}</td>
                      <td style={{ padding: '0.75rem' }}>{r.hora_entrada ? new Date(r.hora_entrada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{r.hora_salida ? new Date(r.hora_salida).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                      <td style={{ padding: '0.75rem', fontWeight: 700 }}>{r.horas_laboradas}h</td>
                      <td style={{ padding: '0.75rem', color: r.minutos_descanso > 0 ? '#eab308' : '#94a3b8' }}>{r.minutos_descanso || 0} min</td>
                      <td style={{ padding: '0.75rem' }}>{r.estado}</td>
                      <td style={{ padding: '0.75rem' }}>
                        {r.correcciones_manuales && r.correcciones_manuales.length > 0 ? (
                          <div style={{ fontSize: '0.75rem' }}>
                            {r.correcciones_manuales.map((c, idx) => (
                              <div key={idx} style={{ color: c.tipo === 'Permiso' ? '#eab308' : (c.minutos > 0 ? '#22c55e' : '#ef4444') }}>
                                {c.tipo}: {c.tipo === 'Permiso' ? c.minutos : (c.minutos > 0 ? '+' : '') + c.minutos} min
                              </div>
                            ))}
                          </div>
                        ) : '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>}
        </section>}

        {subTabReportes === 'horas-extra' && <section style={{ display: 'grid', gap: '1.5rem' }}>
          <form onSubmit={generarReporteHorasExtra} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
            <input className="input" type="date" value={reporteForm.fecha_inicio} onChange={(e) => setReporteForm({ ...reporteForm, fecha_inicio: e.target.value })} required />
            <input className="input" type="date" value={reporteForm.fecha_fin} onChange={(e) => setReporteForm({ ...reporteForm, fecha_fin: e.target.value })} required />
            <select className="input" value={reporteForm.empleado_id} onChange={(e) => setReporteForm({ ...reporteForm, empleado_id: e.target.value })}>
              <option value="">Todos los colaboradores</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#fff' }}>
              <input 
                type="checkbox" 
                checked={reporteForm.corte_semanal} 
                onChange={(e) => setReporteForm({ ...reporteForm, corte_semanal: e.target.checked })}
                style={{ width: '1rem', height: '1rem' }}
              />
              Corte semanal (Viernes 8am - Viernes 8am)
            </label>
            <button className="btn">📊 Generar Reporte</button>
            <button 
              type="button" 
              onClick={() => exportarExcel('horas-extra')}
              className="btn-green"
            >
              📥 Exportar Excel
            </button>
          </form>

          {reporteHorasExtra.length > 0 && <div className="panel" style={{ padding: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Resultados: {reporteHorasExtra.length} registros</h3>
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tipo Bloque</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Inicio - Fin</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Minutos</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Horas</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Supervisor</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>RRHH</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Correcciones</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {reporteHorasExtra.map((r, i) => {
                  const emp = empleados.find(e => e.id === r.empleado_id)
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? emp.nombre_completo : r.empleado_id}</td>
                      <td style={{ padding: '0.75rem' }}>{r.fecha}</td>
                      <td style={{ padding: '0.75rem' }}>{r.tipo}</td>
                      <td style={{ padding: '0.75rem', fontSize: '0.75rem' }}>
                        {new Date(r.hora_inicio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(r.hora_fin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td style={{ padding: '0.75rem' }}>{r.minutos_extra} min</td>
                      <td style={{ padding: '0.75rem', fontWeight: 700 }}>{r.horas_extra}h</td>
                      <td style={{ padding: '0.75rem' }}>{r.validado_supervisor ? '✅' : '❌'}</td>
                      <td style={{ padding: '0.75rem' }}>{r.validado_rrhh ? '✅' : '❌'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        {r.validado_rrhh ? (
                          <span style={{ color: '#22c55e', fontWeight: 700 }}>✅ Autorizado</span>
                        ) : (
                          <span style={{ color: '#eab308' }}>⏳ Pendiente</span>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {r.correcciones_manuales && r.correcciones_manuales.length > 0 ? (
                          <div style={{ fontSize: '0.75rem' }}>
                            {r.correcciones_manuales.map((c, idx) => (
                              <div key={idx} style={{ color: c.tipo === 'Permiso' ? '#eab308' : (c.minutos > 0 ? '#22c55e' : '#ef4444') }}>
                                {c.tipo}: {c.tipo === 'Permiso' ? c.minutos : (c.minutos > 0 ? '+' : '') + c.minutos} min
                              </div>
                            ))}
                          </div>
                        ) : '-'}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                          {!r.validado_supervisor && (
                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Esperando supervisor</span>
                          )}
                          {r.validado_supervisor && !r.validado_rrhh && (
                            <button onClick={() => aprobarBloqueHorasExtraRRHH(r.bloque_id)} className="btn-sm btn-sm-green">✓ Validar RRHH</button>
                          )}
                          {r.validado_supervisor && r.validado_rrhh && (
                            <span style={{ fontSize: '0.75rem', color: '#22c55e' }}>Completado</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>}
        </section>}

        {subTabReportes === 'salidas-temporales' && <section style={{ display: 'grid', gap: '1.5rem' }}>
          <form onSubmit={generarReporteSalidasTemporales} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
            <input className="input" type="date" value={reporteForm.fecha_inicio} onChange={(e) => setReporteForm({ ...reporteForm, fecha_inicio: e.target.value })} required />
            <input className="input" type="date" value={reporteForm.fecha_fin} onChange={(e) => setReporteForm({ ...reporteForm, fecha_fin: e.target.value })} required />
            <select className="input" value={reporteForm.empleado_id} onChange={(e) => setReporteForm({ ...reporteForm, empleado_id: e.target.value })}>
              <option value="">Todos los colaboradores</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
            <button className="btn">📊 Generar Reporte</button>
          </form>

          {reporteSalidasTemporales.length > 0 && <div className="panel" style={{ padding: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Resultados: {reporteSalidasTemporales.length} registros</h3>
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Tipo Salida</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Hora Salida</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Hora Regreso</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Duración (min)</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Minutos Descontados</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {reporteSalidasTemporales.map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '0.75rem' }}>{r.nombre_empleado} #{r.numero_empleado}</td>
                    <td style={{ padding: '0.75rem' }}>{r.tipo_salida}</td>
                    <td style={{ padding: '0.75rem' }}>{r.fecha_turno}</td>
                    <td style={{ padding: '0.75rem' }}>{r.hora_salida ? new Date(r.hora_salida).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{r.hora_regreso ? new Date(r.hora_regreso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700 }}>{r.duracion_minutos ? r.duracion_minutos + ' min' : '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{r.minutos_descontados} min</td>
                    <td style={{ padding: '0.75rem' }}>{r.estado_salida}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
        </section>}

        {subTabReportes === 'asistencias' && <section style={{ display: 'grid', gap: '1.5rem' }}>
          <form onSubmit={generarReporteAsistencias} className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
            <input className="input" type="date" value={reporteForm.fecha_inicio} onChange={(e) => setReporteForm({ ...reporteForm, fecha_inicio: e.target.value })} required />
            <input className="input" type="date" value={reporteForm.fecha_fin} onChange={(e) => setReporteForm({ ...reporteForm, fecha_fin: e.target.value })} required />
            <select className="input" value={reporteForm.empleado_id} onChange={(e) => setReporteForm({ ...reporteForm, empleado_id: e.target.value })}>
              <option value="">Todos los colaboradores</option>
              {empleados.map(e => <option key={e.id} value={e.id}>{e.numero_empleado} - {e.nombre_completo}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: '#fff' }}>
              <input 
                type="checkbox" 
                checked={reporteForm.corte_semanal} 
                onChange={(e) => setReporteForm({ ...reporteForm, corte_semanal: e.target.checked })}
                style={{ width: '1rem', height: '1rem' }}
              />
              Corte semanal (Viernes 8am - Viernes 8am)
            </label>
            <button className="btn">📊 Generar Reporte</button>
            <button 
              type="button" 
              onClick={() => exportarExcel('asistencias')}
              className="btn-green"
            >
              📥 Exportar Excel
            </button>
          </form>

          {reporteAsistencias.length > 0 && <div className="panel" style={{ padding: '1rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 900, margin: '0 0 1rem 0' }}>Resultados: {reporteAsistencias.length} registros</h3>
            <table className="table">
              <thead>
                <tr style={{ background: 'rgba(30,41,59,0.5)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Colaborador</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Fecha</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Entrada</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Salida</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Estado</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 900 }}>Correcciones</th>
                </tr>
              </thead>
              <tbody>
                {reporteAsistencias.map((r, i) => {
                  const emp = empleados.find(e => e.id === r.empleado_id)
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem' }}>{emp ? emp.nombre_completo : r.empleado_id}</td>
                      <td style={{ padding: '0.75rem' }}>{r.fecha}</td>
                      <td style={{ padding: '0.75rem' }}>{r.hora_entrada ? new Date(r.hora_entrada).toLocaleTimeString() : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{r.hora_salida ? new Date(r.hora_salida).toLocaleTimeString() : '-'}</td>
                      <td style={{ padding: '0.75rem' }}>{r.estado_registro || '-'}</td>
                      <td style={{ padding: '0.75rem' }}>
                        {r.correcciones_manuales && r.correcciones_manuales.length > 0 ? (
                          <div style={{ fontSize: '0.75rem' }}>
                            {r.correcciones_manuales.map((c, idx) => (
                              <div key={idx} style={{ color: c.tipo === 'Permiso' ? '#eab308' : (c.minutos > 0 ? '#22c55e' : '#ef4444') }}>
                                {c.tipo}: {c.tipo === 'Permiso' ? c.minutos : (c.minutos > 0 ? '+' : '') + c.minutos} min
                              </div>
                            ))}
                          </div>
                        ) : '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>}
        </section>}
      </section>}
    </div>
    </div>
  </main>
}
