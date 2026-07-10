/* =========================================================
   HomeCare Enterprise - App de Campo (PWA offline-first)

   Arquitectura:
   - IndexedDB guarda: (a) la agenda y las fichas de paciente
     que ya se consultaron (para verlas sin internet), y
     (b) una "cola_offline" con cada acción que el
     profesional registra (ingreso, salida, signos vitales,
     medicamento administrado, evolución, orden médica).
   - Cuando hay conexión, la cola se sincroniza contra
     POST /api/movil/sync en un solo lote. Cada item exitoso
     se borra de la cola; los que fallan se quedan para
     reintentar.
   - La sesión (cookie) se comparte con el sitio web: el
     profesional inicia sesión una vez estando en línea.
   ========================================================= */

const DB_NOMBRE = "homecare_app";
const DB_VERSION = 2;

let db = null;
let perfil = JSON.parse(localStorage.getItem("homecare_perfil") || "null");
let vistaActual = "login";

// ==========================================================
// INDEXEDDB
// ==========================================================

function abrirDB() {
  return new Promise((resolve, reject) => {
    const solicitud = indexedDB.open(DB_NOMBRE, DB_VERSION);

    solicitud.onupgradeneeded = (evento) => {
      const base = evento.target.result;

      if (!base.objectStoreNames.contains("agenda_cache")) {
        base.createObjectStore("agenda_cache", { keyPath: "id" });
      }
      if (!base.objectStoreNames.contains("pacientes_cache")) {
        base.createObjectStore("pacientes_cache", { keyPath: "paciente_id" });
      }
      if (!base.objectStoreNames.contains("cola_offline")) {
        base.createObjectStore("cola_offline", { keyPath: "id" });
      }
      if (!base.objectStoreNames.contains("plantillas_cache")) {
        base.createObjectStore("plantillas_cache", { keyPath: "id" });
      }
    };

    solicitud.onsuccess = (evento) => resolve(evento.target.result);
    solicitud.onerror = (evento) => reject(evento.target.error);
  });
}

function guardarEnStore(nombreStore, valor) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nombreStore, "readwrite");
    tx.objectStore(nombreStore).put(valor);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function leerDeStore(nombreStore, clave) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nombreStore, "readonly");
    const solicitud = tx.objectStore(nombreStore).get(clave);
    solicitud.onsuccess = () => resolve(solicitud.result || null);
    solicitud.onerror = () => reject(solicitud.error);
  });
}

function leerTodoDeStore(nombreStore) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nombreStore, "readonly");
    const solicitud = tx.objectStore(nombreStore).getAll();
    solicitud.onsuccess = () => resolve(solicitud.result || []);
    solicitud.onerror = () => reject(solicitud.error);
  });
}

function borrarDeStore(nombreStore, clave) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nombreStore, "readwrite");
    tx.objectStore(nombreStore).delete(clave);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function limpiarStore(nombreStore) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(nombreStore, "readwrite");
    tx.objectStore(nombreStore).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

// Borra TODO lo que se guardó en el celular sobre pacientes,
// agenda y plantillas de la sesión de la persona que estaba
// usando la app -- necesario al cerrar sesión, para que si
// otro profesional entra despues en el MISMO celular/tablet
// (algo comun en atencion domiciliaria, donde varios
// comparten un mismo dispositivo) no seguir viendo pacientes,
// historias clinicas ni citas de la persona anterior.
// La cola de sincronizacion pendiente (cola_offline) SI se
// conserva a proposito, para no perder informacion que
// todavia no ha llegado al servidor.
async function limpiarDatosDeSesion() {
  try {
    await limpiarStore("agenda_cache");
    await limpiarStore("pacientes_cache");
    await limpiarStore("plantillas_cache");
  } catch (error) {
    console.error("No se pudo limpiar la caché local:", error);
  }
}

// ==========================================================
// COLA OFFLINE (acciones pendientes de sincronizar)
// ==========================================================

function generarId() {
  return "acc-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
}

async function encolarAccion(tipo, payload) {
  const accion = {
    id: generarId(),
    tipo,
    payload,
    creado_en: new Date().toISOString(),
    intentos: 0,
  };
  await guardarEnStore("cola_offline", accion);
  actualizarContadorPendientes();
  intentarSincronizar();
  return accion;
}

async function contarPendientes() {
  const todas = await leerTodoDeStore("cola_offline");
  return todas.length;
}

async function actualizarContadorPendientes() {
  const total = await contarPendientes();
  const el = document.querySelector('[data-vista="pendientes"] .icono');
  if (el) el.textContent = total > 0 ? "📤" + total : "📤";
  actualizarEstadoConexion(total);
}

// ==========================================================
// SINCRONIZACIÓN
// ==========================================================

let sincronizando = false;

async function intentarSincronizar() {
  if (sincronizando || !navigator.onLine) return;

  sincronizando = true;

  try {
    const pendientes = await leerTodoDeStore("cola_offline");

    if (pendientes.length === 0) {
      sincronizando = false;
      actualizarEstadoConexion(0);
      return;
    }

    const cuerpo = {
      acciones: pendientes.map((a) => ({ id: a.id, tipo: a.tipo, payload: a.payload })),
    };

    const respuesta = await fetch("/api/movil/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(cuerpo),
    });

    if (!respuesta.ok) throw new Error("El servidor rechazó la sincronización.");

    const datos = await respuesta.json();

    for (const resultado of datos.resultados) {
      if (resultado.ok) {
        await borrarDeStore("cola_offline", resultado.id);

        const geocerca = resultado.resultado && resultado.resultado.geocerca;
        if (geocerca && geocerca.verificable !== undefined) {
          mostrarAvisoGeocerca(geocerca);
        }
      }
      // los que fallan se quedan en la cola para reintentar
      // (por ejemplo, si el servidor devolvió un error puntual)
    }
  } catch (error) {
    console.warn("No se pudo sincronizar todavía:", error.message);
  } finally {
    sincronizando = false;
    actualizarContadorPendientes();
  }
}

window.addEventListener("online", intentarSincronizar);
setInterval(intentarSincronizar, 20000);

// ==========================================================
// ESTADO DE CONEXIÓN (indicador visual)
// ==========================================================

function mostrarAvisoGeocerca(geocerca) {
  if (!geocerca.verificable) {
    return; // no se pudo verificar (sin permiso de ubicacion o paciente sin coordenadas), no molestar con esto
  }
  if (geocerca.dentro_del_rango) {
    // ubicacion correcta: aviso discreto, no bloquea nada
    console.log("Ubicación verificada:", geocerca.mensaje);
  } else {
    alert("⚠ " + geocerca.mensaje);
  }
}

function actualizarEstadoConexion(pendientes) {
  const el = document.getElementById("estado-conexion");
  if (!el) return;

  if (!navigator.onLine) {
    el.textContent = "Sin conexión";
    el.className = "estado-conexion offline";
  } else if (pendientes > 0) {
    el.textContent = pendientes + " por enviar";
    el.className = "estado-conexion pendiente";
  } else {
    el.textContent = "En línea";
    el.className = "estado-conexion";
  }
}

window.addEventListener("offline", () => actualizarEstadoConexion(0));
window.addEventListener("online", () => actualizarEstadoConexion(0));

// ==========================================================
// LLAMADAS A LA API (con respaldo en caché)
// ==========================================================

async function apiGet(url) {
  const respuesta = await fetch(url, { credentials: "same-origin" });
  if (!respuesta.ok) throw new Error("Error de red");
  return respuesta.json();
}

async function obtenerAgenda(fechaInicio, fechaFin) {
  try {
    const datos = await apiGet(
      `/api/movil/agenda/${perfil.profesional_id}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`
    );
    for (const visita of datos.visitas) await guardarEnStore("agenda_cache", visita);
    return datos.visitas;
  } catch (error) {
    return await leerTodoDeStore("agenda_cache");
  }
}

async function obtenerFichaPaciente(pacienteId) {
  try {
    const datos = await apiGet(`/api/movil/paciente/${pacienteId}`);
    datos.paciente_id = pacienteId;
    await guardarEnStore("pacientes_cache", datos);
    return datos;
  } catch (error) {
    return await leerDeStore("pacientes_cache", pacienteId);
  }
}

// ==========================================================
// GEOLOCALIZACIÓN
// ==========================================================

function obtenerUbicacion() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ lat: null, lon: null });
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => resolve({ lat: null, lon: null }),
      { timeout: 5000 }
    );
  });
}

// ==========================================================
// RECORDATORIOS DE ABRIR/CERRAR TURNO (10 minutos antes)
//
// Revisa cada minuto, mientras la app este abierta, si hay
// alguna visita a punto de empezar (sin ingreso marcado) o a
// punto de terminar (con ingreso pero sin salida), y avisa
// con una notificacion del navegador 10 minutos antes.
// ==========================================================

const _yaAvisados = new Set();

function _minutosHasta(fechaHoraTexto) {
  const objetivo = new Date(fechaHoraTexto.replace(" ", "T"));
  return (objetivo.getTime() - Date.now()) / 60000;
}

function _mostrarRecordatorio(titulo, cuerpo) {
  if (typeof Notification !== "undefined" && Notification.permission === "granted") {
    new Notification(titulo, { body: cuerpo, icon: "/app/icons/icon-192.png" });
  } else {
    // Si no hay permiso de notificaciones del sistema, al menos se avisa dentro de la app
    console.log(`[Recordatorio] ${titulo}: ${cuerpo}`);
  }
}

async function _revisarRecordatoriosDeTurno() {
  try {
    const todas = await leerTodoDeStore("agenda_cache");
    const hoyISO = new Date().toISOString().slice(0, 10);

    todas
      .filter((v) => v.fecha === hoyISO)
      .forEach((v) => {
        const nombrePaciente = [v.primer_nombre, v.primer_apellido].filter(Boolean).join(" ");

        // Recordatorio de ABRIR turno
        if (!v.hora_real_inicio && v.hora_inicio) {
          const minutos = _minutosHasta(`${v.fecha} ${v.hora_inicio}:00`);
          const clave = `abrir-${v.id}`;
          if (minutos > 0 && minutos <= 10 && !_yaAvisados.has(clave)) {
            _yaAvisados.add(clave);
            _mostrarRecordatorio(
              "⏰ Recuerde abrir turno",
              `Su visita a ${nombrePaciente} empieza en ${Math.round(minutos)} minutos. No olvide registrar el ingreso.`
            );
          }
        }

        // Recordatorio de CERRAR turno
        if (v.hora_real_inicio && !v.hora_real_fin && v.hora_fin) {
          const minutos = _minutosHasta(`${v.fecha} ${v.hora_fin}:00`);
          const clave = `cerrar-${v.id}`;
          if (minutos > 0 && minutos <= 10 && !_yaAvisados.has(clave)) {
            _yaAvisados.add(clave);
            _mostrarRecordatorio(
              "⏰ Recuerde cerrar turno",
              `Su turno con ${nombrePaciente} termina en ${Math.round(minutos)} minutos. No olvide registrar la salida.`
            );
          }
        }
      });
  } catch (error) {
    // sin cache todavia, no hay nada que revisar
  }
}

function iniciarRecordatoriosDeTurno() {
  if (typeof Notification !== "undefined" && Notification.permission === "default") {
    Notification.requestPermission();
  }
  _revisarRecordatoriosDeTurno();
  setInterval(_revisarRecordatoriosDeTurno, 60000); // cada minuto
}

// ==========================================================
// MONITOREO DEL TURNO ACTIVO
//
// Mientras el usuario tiene una visita con ingreso marcado
// pero sin salida (turno "abierto"), esto: 1) avisa con un
// mensaje del navegador si intenta cerrar la pestaña/app sin
// haber cerrado el turno, y 2) vigila su ubicacion cada cierto
// tiempo -- si se aleja demasiado del domicilio del paciente,
// cierra el turno automaticamente (registra la salida sola).
// ==========================================================

let _idVigilanciaUbicacion = null;
let _visitaEnMonitoreo = null;
const MARGEN_SALIDA_AUTOMATICA = 1.5; // 50% mas del radio normal, para no cerrar por un rebote del GPS

function _avisoAntesDeCerrar(evento) {
  evento.preventDefault();
  evento.returnValue = "Tiene un turno abierto. No cierre la aplicación hasta registrar la salida.";
  return evento.returnValue;
}

function iniciarMonitoreoTurno(visita) {
  detenerMonitoreoTurno(); // por si ya habia uno corriendo, para no duplicar

  _visitaEnMonitoreo = visita;
  window.addEventListener("beforeunload", _avisoAntesDeCerrar);

  if (!navigator.geolocation || visita.lat_paciente == null || visita.lon_paciente == null) {
    return; // sin geolocalizacion o sin coordenadas del paciente, no se puede vigilar
  }

  _idVigilanciaUbicacion = navigator.geolocation.watchPosition(
    async (posicion) => {
      const distancia = calcularDistanciaMetros(
        posicion.coords.latitude, posicion.coords.longitude,
        _visitaEnMonitoreo.lat_paciente, _visitaEnMonitoreo.lon_paciente
      );
      const limite = (_visitaEnMonitoreo.radio_geocerca_metros || 150) * MARGEN_SALIDA_AUTOMATICA;

      if (distancia !== null && distancia > limite) {
        await _cerrarTurnoAutomaticamente(_visitaEnMonitoreo, posicion.coords.latitude, posicion.coords.longitude);
      }
    },
    () => {}, // si falla una lectura puntual del GPS, se ignora y se sigue vigilando
    { enableHighAccuracy: true, maximumAge: 30000, timeout: 20000 }
  );
}

function detenerMonitoreoTurno() {
  if (_idVigilanciaUbicacion !== null) {
    navigator.geolocation.clearWatch(_idVigilanciaUbicacion);
    _idVigilanciaUbicacion = null;
  }
  window.removeEventListener("beforeunload", _avisoAntesDeCerrar);
  _visitaEnMonitoreo = null;
}

async function _cerrarTurnoAutomaticamente(visita, lat, lon) {
  detenerMonitoreoTurno();

  await encolarAccion("salida", {
    visita_id: visita.id, lat: lat, lon: lon,
    foto_base64: null, marca_tiempo_offline: new Date().toISOString(),
    motivo: "Cierre automático: el profesional se alejó del domicilio del paciente.",
  });

  visita.hora_real_fin = new Date().toISOString().replace("T", " ").slice(0, 19);
  await guardarEnStore("agenda_cache", visita);

  alert(
    "⚠ Se detectó que se alejó del domicilio del paciente, así que el sistema cerró " +
    "el turno automáticamente. Si esto fue un error, contacte a la oficina."
  );

  if (document.getElementById("titulo-pantalla")) {
    renderDetalleVisita(visita.id);
  }
}

// Si la app se cierra y se vuelve a abrir mientras un turno
// seguia abierto (ingreso marcado, salida sin marcar), esto
// retoma la vigilancia automaticamente al cargar la agenda.
async function reanudarMonitoreoSiHayTurnoAbierto() {
  try {
    const todas = await leerTodoDeStore("agenda_cache");
    const abierta = todas.find((v) => v.hora_real_inicio && !v.hora_real_fin);
    if (abierta) iniciarMonitoreoTurno(abierta);
  } catch (error) {
    // sin cache todavia, no hay nada que reanudar
  }
}

// ==========================================================
// RENDERIZADO DE PANTALLAS
// ==========================================================

const contenedor = () => document.getElementById("contenedor");
const titulo = (t) => (document.getElementById("titulo-pantalla").textContent = t);

function mostrarNav(mostrar) {
  document.getElementById("nav-inferior").classList.toggle("oculto", !mostrar);
}

async function irA(vista, parametro) {
  vistaActual = vista;
  document.querySelectorAll(".bottom-nav button").forEach((b) => {
    b.classList.toggle("activo", b.dataset.vista === vista);
  });

  if (vista === "agenda") return renderAgenda();
  if (vista === "pacientes") return renderBusquedaPacientes();
  if (vista === "pendientes") return renderPendientes();
  if (vista === "perfil") return renderPerfil();
  if (vista === "detalle_visita") return renderDetalleVisita(parametro);
  if (vista === "ficha_paciente") return renderFichaPaciente(parametro);
}

// ---------------- LOGIN ----------------

function renderLogin() {
  mostrarNav(false);
  titulo("HomeCare - Ingreso");
  contenedor().innerHTML = `
    <div class="card">
      <h3>Iniciar sesión</h3>
      <div id="login-error"></div>
      <div class="form-group">
        <label>Usuario</label>
        <input type="text" id="login-usuario" autocomplete="username">
      </div>
      <div class="form-group">
        <label>Contraseña</label>
        <input type="password" id="login-password" autocomplete="current-password">
      </div>
      <button class="btn btn-primary w-100" id="btn-login">Ingresar</button>
      <p class="mt-2" style="font-size:12px;color:#6c757d">
        Debe iniciar sesión una vez con internet. Después, la app funciona sin conexión.
      </p>
    </div>`;

  document.getElementById("btn-login").addEventListener("click", async () => {
    const usuario = document.getElementById("login-usuario").value.trim();
    const password = document.getElementById("login-password").value;
    const errorEl = document.getElementById("login-error");
    errorEl.innerHTML = "";

    try {
      const respuesta = await fetch("/api/movil/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ usuario, password }),
      });

      if (!respuesta.ok) {
        errorEl.innerHTML = `<div class="alerta alerta-danger">Usuario o contraseña incorrectos.</div>`;
        return;
      }

      const datosLogin = await respuesta.json();
      const perfilDatos = await apiGet("/api/movil/perfil");

      // Se limpia cualquier dato guardado de una sesion anterior
      // ANTES de guardar el perfil nuevo -- asi, si este celular
      // lo uso otra persona antes (comun quando se comparte un
      // mismo dispositivo entre varios profesionales), no queda
      // nada de esa sesion anterior mezclado con la nueva.
      await limpiarDatosDeSesion();

      perfil = {
        usuario_id: datosLogin.usuario.id,
        nombre: datosLogin.usuario.nombre,
        rol: datosLogin.usuario.rol,
        profesional_id: perfilDatos.profesional_id,
      };
      localStorage.setItem("homecare_perfil", JSON.stringify(perfil));

      mostrarNav(true);
      irA("agenda");
      reanudarMonitoreoSiHayTurnoAbierto();
      iniciarRecordatoriosDeTurno();
    } catch (error) {
      errorEl.innerHTML = `<div class="alerta alerta-danger">No hay conexión. Debe iniciar sesión la primera vez con internet.</div>`;
    }
  });
}

// ---------------- AGENDA ----------------

async function renderAgenda() {
  titulo("Mi Agenda");
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  const hoy = new Date().toISOString().slice(0, 10);
  const visitas = await obtenerAgenda(hoy, hoy);

  if (!visitas.length) {
    contenedor().innerHTML = `<div class="alerta alerta-info">No tiene visitas asignadas hoy.</div>`;
    return;
  }

  contenedor().innerHTML = visitas
    .map((v) => {
      const nombrePaciente = [v.primer_nombre, v.primer_apellido].filter(Boolean).join(" ");
      let estadoBadge = "badge-secondary";
      if (v.hora_real_fin) estadoBadge = "badge-success";
      else if (v.hora_real_inicio) estadoBadge = "badge-warning";

      return `
      <div class="card" onclick="irA('detalle_visita', ${v.id})">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3>${nombrePaciente}</h3>
          <span class="badge ${estadoBadge}">${v.hora_real_fin ? "Completada" : v.hora_real_inicio ? "En curso" : "Pendiente"}</span>
        </div>
        <small>${v.hora_inicio} · ${v.servicio}</small><br>
        <small>${v.direccion || ""} ${v.barrio || ""}</small>
      </div>`;
    })
    .join("");
}

// ---------------- DETALLE DE VISITA ----------------

async function renderDetalleVisita(visitaId) {
  titulo("Visita");
  const todas = await leerTodoDeStore("agenda_cache");
  const visita = todas.find((v) => v.id === visitaId);

  if (!visita) {
    contenedor().innerHTML = `<div class="alerta alerta-danger">No se encontró la visita.</div>`;
    return;
  }

  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  const yaFinalizada = !!visita.hora_real_fin;

  if (yaFinalizada) {
    // La visita ya se completó: pantalla BLOQUEADA, solo se
    // puede consultar/imprimir el reporte o (si hace falta)
    // registrar una corrección, nunca volver a marcar
    // ingreso/salida ni editar lo ya guardado.
    contenedor().innerHTML = `
      <div class="card">
        <h3>${nombrePaciente}</h3>
        <small>${visita.servicio} · ${visita.hora_inicio} - ${visita.hora_fin}</small><br>
        <small>${visita.direccion || ""} ${visita.barrio || ""}, ${visita.municipio || ""}</small>
        <div class="alerta alerta-success mt-2">
          ✔ Visita finalizada — Ingreso: ${visita.hora_real_inicio ? visita.hora_real_inicio.slice(11, 16) : "—"},
          Salida: ${visita.hora_real_fin.slice(11, 16)}
        </div>
      </div>
      <button class="btn btn-primary btn-block" id="btn-ver-reporte">📄 Ver / imprimir reporte de esta visita</button>
      <button class="btn btn-secondary btn-block" onclick="irAFichaPacienteDesdeVisita(${visita.paciente_id}, ${visita.id})">
        🧑‍⚕️ Ver historia clínica y alergias
      </button>
      <button class="btn btn-secondary btn-block" onclick="irA('agenda')">← Volver a la agenda</button>
    `;
    document.getElementById("btn-ver-reporte").addEventListener("click", () => renderVerReporte(visita));
    return;
  }

  if (!visita.hora_real_inicio) {
    // Todavia NO se ha registrado el ingreso a labores: la
    // pantalla queda BLOQUEADA, solo se puede marcar el
    // ingreso (con foto + ubicacion). El resto de opciones
    // (historia clinica, evolucion, signos, firmar planilla,
    // etc.) se habilitan recien despues de entrar.
    contenedor().innerHTML = `
      <div class="card">
        <h3>${nombrePaciente}</h3>
        <small>${visita.servicio} · ${visita.hora_inicio} - ${visita.hora_fin}</small><br>
        <small>${visita.direccion || ""} ${visita.barrio || ""}, ${visita.municipio || ""}</small>
        <div class="alerta alerta-info mt-2">
          🔒 Para ver la historia clínica y registrar cualquier información de este paciente,
          primero debe registrar su ingreso a labores (con foto y ubicación).
        </div>
      </div>
      <button class="btn btn-primary btn-block" id="btn-ingreso">▶ Registrar ingreso a labores</button>
      <button class="btn btn-secondary btn-block" onclick="irA('agenda')">← Volver a la agenda</button>
    `;
    document.getElementById("btn-ingreso").addEventListener("click", () => renderCapturaFotoIngreso(visita, "ingreso"));
    return;
  }

  contenedor().innerHTML = `
    <div class="card">
      <h3>${nombrePaciente}</h3>
      <small>${visita.servicio} · ${visita.hora_inicio} - ${visita.hora_fin}</small><br>
      <small>${visita.direccion || ""} ${visita.barrio || ""}, ${visita.municipio || ""}</small>
      <p class="mt-2">
        Ingreso real: <strong>${visita.hora_real_inicio ? visita.hora_real_inicio.slice(11, 16) : "— pendiente —"}</strong><br>
        Salida real: <strong>${visita.hora_real_fin ? visita.hora_real_fin.slice(11, 16) : "— pendiente —"}</strong>
      </p>
    </div>

    <button class="btn btn-success btn-block" id="btn-salida" ${visita.hora_real_fin ? "disabled" : ""}>
      ⏹ Finalizar labores
    </button>
    <button class="btn btn-secondary btn-block" onclick="irAFichaPacienteDesdeVisita(${visita.paciente_id}, ${visita.id})">
      🧑‍⚕️ Ver historia clínica y alergias
    </button>
    ${esPerfilCuidador() ? "" : `
    <button class="btn btn-secondary btn-block" id="btn-signos">🌡️ Registrar signos vitales</button>
    <button class="btn btn-secondary btn-block" id="btn-medicamento">💊 Registrar medicamento administrado</button>
    `}
    <button class="btn btn-secondary btn-block" id="btn-evolucion">${esPerfilCuidador() ? "📋 Registro Informe de Cuidador" : "📝 Registrar evolución"}</button>
    ${esPerfilCuidador() ? "" : `
    <button class="btn btn-secondary btn-block" id="btn-laboratorio">🧪 Resultados de laboratorio</button>
    <button class="btn btn-secondary btn-block" id="btn-ordenes">📋 Órdenes Médicas</button>
    <button class="btn btn-secondary btn-block" id="btn-ultima-nota-medica">🩺 Última Nota Médica</button>
    <button class="btn btn-secondary btn-block" id="btn-programa-atencion">📑 Programa de Atención</button>
    `}
    ${visita.planilla_id && visita.planilla_estado !== "Firmada" ? `
    <button class="btn btn-primary btn-block" id="btn-firmar-planilla">✍️ Firmar planilla de visita</button>
    ` : ""}
    ${esPerfilCuidador() ? "" : `
    ${!visita.ubicacion_confirmada || esPerfilAdministrativo() ? `
    <button class="btn btn-secondary btn-block" id="btn-actualizar-ubicacion-paciente">
      📍 ${visita.ubicacion_confirmada ? "Corregir" : "Registrar"} ubicación exacta del paciente
    </button>
    ` : `
    <div class="alerta alerta-info">📍 La ubicación de este paciente ya fue registrada en la visita de valoración inicial.</div>
    `}
    `}
    <button class="btn btn-secondary btn-block" onclick="irA('agenda')">← Volver a la agenda</button>
  `;

  if (visita.planilla_id && visita.planilla_estado !== "Firmada") {
    document.getElementById("btn-firmar-planilla").addEventListener("click", () => renderFirmarPlanilla(visita));
  }
  const botonUbicacion = document.getElementById("btn-actualizar-ubicacion-paciente");
  if (botonUbicacion) {
  botonUbicacion.addEventListener("click", async () => {
    const ubicacion = await obtenerUbicacion();
    if (ubicacion.lat === null) {
      alert("No se pudo obtener la ubicación. Verifique el permiso de ubicación.");
      return;
    }
    await encolarAccion("actualizar_ubicacion_paciente", {
      paciente_id: visita.paciente_id, lat: ubicacion.lat, lon: ubicacion.lon,
    });
    alert("Ubicación del paciente guardada. Se sincronizará cuando haya conexión.");
  });
  }

  document.getElementById("btn-salida").addEventListener("click", () => renderCapturaFotoIngreso(visita, "salida"));

  document.getElementById("btn-evolucion").addEventListener("click", () => renderFormularioEvolucion(visita));
  if (!esPerfilCuidador()) {
    document.getElementById("btn-signos").addEventListener("click", () => renderFormularioSignos(visita));
    document.getElementById("btn-medicamento").addEventListener("click", () => renderFormularioMedicamento(visita));
    document.getElementById("btn-laboratorio").addEventListener("click", () => renderLaboratorio(visita));
    document.getElementById("btn-ordenes").addEventListener("click", () => renderOrdenMedica(visita));
    document.getElementById("btn-ultima-nota-medica").addEventListener("click", () => renderUltimaNotaMedica(visita));
    document.getElementById("btn-programa-atencion").addEventListener("click", () => renderProgramaAtencion(visita));
  }
}

function renderFormularioSignos(visita) {
  contenedor().innerHTML = `
    <div class="card">
      <h3>Signos vitales</h3>
      <div class="form-group"><label>Temperatura (°C)</label><input type="number" step="0.1" id="sv-temp"></div>
      <div class="form-group"><label>Presión sistólica</label><input type="number" id="sv-sis"></div>
      <div class="form-group"><label>Presión diastólica</label><input type="number" id="sv-dia"></div>
      <div class="form-group"><label>Frecuencia cardíaca</label><input type="number" id="sv-fc"></div>
      <div class="form-group"><label>Frecuencia respiratoria</label><input type="number" id="sv-fr"></div>
      <div class="form-group"><label>Saturación O2 (%)</label><input type="number" id="sv-sat"></div>
      <div class="form-group"><label>Glucemia</label><input type="number" id="sv-gluc"></div>
      <div class="form-group"><label>Dolor (0-10)</label><input type="number" min="0" max="10" id="sv-dolor"></div>
      <div class="form-group"><label>Observaciones</label><textarea id="sv-obs" rows="2"></textarea></div>
      <button class="btn btn-success w-100" id="btn-guardar-signos">Guardar</button>
      <button class="btn btn-secondary w-100 mt-2" onclick="irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  document.getElementById("btn-guardar-signos").addEventListener("click", async () => {
    const datos = {
      temperatura: parseFloat(document.getElementById("sv-temp").value) || null,
      presion_sistolica: parseInt(document.getElementById("sv-sis").value) || null,
      presion_diastolica: parseInt(document.getElementById("sv-dia").value) || null,
      frecuencia_cardiaca: parseInt(document.getElementById("sv-fc").value) || null,
      frecuencia_respiratoria: parseInt(document.getElementById("sv-fr").value) || null,
      saturacion_oxigeno: parseInt(document.getElementById("sv-sat").value) || null,
      glucemia: parseFloat(document.getElementById("sv-gluc").value) || null,
      dolor: parseInt(document.getElementById("sv-dolor").value) || null,
      observaciones: document.getElementById("sv-obs").value,
    };

    await encolarAccion("signos_vitales", {
      paciente_id: visita.paciente_id,
      profesional: perfil.nombre,
      datos,
    });

    alert("Signos vitales guardados. Se enviarán al servidor automáticamente.");
    irA("detalle_visita", visita.id);
  });
}

function renderFormularioMedicamento(visita) {
  contenedor().innerHTML = `
    <div class="card">
      <h3>Medicamento administrado</h3>
      <div class="form-group"><label>Nombre del medicamento</label><input type="text" id="med-nombre"></div>
      <div class="form-group"><label>Dosis</label><input type="text" id="med-dosis" placeholder="Ej: 500mg"></div>
      <div class="form-group"><label>Vía</label>
        <select id="med-via">
          <option>Oral</option><option>Intramuscular</option><option>Intravenosa</option>
          <option>Subcutánea</option><option>Tópica</option><option>Otra</option>
        </select>
      </div>
      <div class="form-group"><label>Observaciones</label><textarea id="med-obs" rows="2"></textarea></div>
      <button class="btn btn-success w-100" id="btn-guardar-med">Guardar</button>
      <button class="btn btn-secondary w-100 mt-2" onclick="irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  document.getElementById("btn-guardar-med").addEventListener("click", async () => {
    await encolarAccion("medicamento_administrado", {
      medicamento_id: null,
      paciente_id: visita.paciente_id,
      profesional: perfil.nombre,
      dosis: document.getElementById("med-dosis").value,
      via: document.getElementById("med-via").value,
      observaciones: (document.getElementById("med-nombre").value + " — " + document.getElementById("med-obs").value),
      estado: "Administrado",
    });

    alert("Medicamento registrado. Se enviará al servidor automáticamente.");
    irA("detalle_visita", visita.id);
  });
}

const TIPOS_NOTA_MOVIL = [
  { rol: "Médico", nombre: "Nota Médica" },
  { rol: "Enfermero", nombre: "Nota de Enfermería" },
  { rol: "Cuidador", nombre: "Nota de Cuidador" },
  { rol: "Aplicador", nombre: "Nota de Aplicador" },
  { rol: "Curaciones", nombre: "Nota de Curaciones" },
  { rol: "Terapeuta", nombre: "Nota de Terapia" },
];

function renderFormularioEvolucion(visita, opciones) {
  opciones = opciones || {};
  const esCuidador = esPerfilCuidador();

  contenedor().innerHTML = `
    <div class="card">
      <h3>${esCuidador ? "Registro Informe de Cuidador" : "Registrar en la Historia Clínica"}</h3>
      <div class="form-group" style="display:${esCuidador ? "none" : "block"};">
        <label>¿Qué tipo de formato va a diligenciar?</label>
        <select id="ev-tipo-nota">
          <option value="">-- Seleccione --</option>
          ${TIPOS_NOTA_MOVIL.map(t => `<option value="${t.rol}" data-nombre="${t.nombre}">${t.nombre}</option>`).join("")}
        </select>
      </div>
      <div id="ev-contenedor-resto" style="display:${esCuidador ? "block" : "none"};">
        <div class="form-group">
          <label>Plantilla predefinida (opcional)</label>
          <select id="ev-plantilla">
            <option value="">-- Escribir libremente --</option>
          </select>
        </div>
        ${esCuidador ? "" : `
        <div class="form-group">
          <label><input type="checkbox" id="ev-es-aclaratoria" ${opciones.forzarAclaratoriaDe ? "checked" : ""}>
            Esta nota es una ACLARACIÓN de un informe anterior (por un error)</label>
          <small style="display:block;color:#6c757d;">Solo disponible para médicos y profesionales de la salud.</small>
        </div>
        <div class="form-group" id="ev-contenedor-informe" style="display:${opciones.forzarAclaratoriaDe ? "block" : "none"};">
          <label>¿A qué informe corrige?</label>
          <select id="ev-informe-a-corregir">
            <option value="">-- Cargando informes... --</option>
          </select>
        </div>
        `}
        ${esCuidador && opciones.forzarNuevoInforme ? `
        <div class="alerta alerta-info">
          Los cuidadores registran un informe nuevo (no se reemplaza el anterior; ambos quedan guardados en la historia clínica).
        </div>` : ""}
        <div class="form-group"><label>Nota</label><textarea id="ev-nota" rows="6" placeholder="Estado del paciente, novedades, recomendaciones..."></textarea></div>
        <button class="btn btn-success w-100" id="btn-guardar-ev">Guardar</button>
      </div>
      <button class="btn btn-secondary w-100 mt-2" onclick="irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  let rolNotaElegido = "";
  let nombreNotaElegida = "";

  if (esCuidador) {
    rolNotaElegido = "Cuidador";
    nombreNotaElegida = "Nota de Cuidador";
    cargarPlantillasMovil();
  }

  async function cargarInformesParaAclarar(preseleccionar) {
    try {
      const respuesta = await fetch(`/api/movil/paciente/${visita.paciente_id}/informes`);
      const informes = await respuesta.json();
      const selector = document.getElementById("ev-informe-a-corregir");
      selector.innerHTML = informes.map((i) =>
        `<option value="${i.consecutivo}">N.° ${i.consecutivo} — ${i.fecha} — ${(i.nota || "").substring(0, 40)}...</option>`
      ).join("") || `<option value="">Sin informes previos</option>`;
      if (preseleccionar) selector.value = String(preseleccionar);
    } catch (error) {
      document.getElementById("ev-informe-a-corregir").innerHTML = `<option value="">No se pudo cargar (sin conexión)</option>`;
    }
  }

  document.getElementById("ev-tipo-nota").addEventListener("change", (e) => {
    if (!e.target.value) {
      document.getElementById("ev-contenedor-resto").style.display = "none";
      return;
    }
    rolNotaElegido = e.target.value;
    nombreNotaElegida = e.target.selectedOptions[0].dataset.nombre;
    document.getElementById("ev-contenedor-resto").style.display = "block";
    cargarPlantillasMovil();
    if (opciones.forzarAclaratoriaDe) cargarInformesParaAclarar(opciones.forzarAclaratoriaDe);
  });

  if (!esCuidador) {
    document.getElementById("ev-es-aclaratoria").addEventListener("change", async (e) => {
      const contenedorInforme = document.getElementById("ev-contenedor-informe");
      contenedorInforme.style.display = e.target.checked ? "block" : "none";
      if (e.target.checked) cargarInformesParaAclarar();
    });
  }

  // Cargar las plantillas del tipo de nota elegido: si hay
  // conexion, se descargan y se guardan en cache; si no hay
  // conexion, se usan las que quedaron guardadas la ultima vez.
  async function cargarPlantillasMovil() {
    const selector = document.getElementById("ev-plantilla");
    selector.innerHTML = '<option value="">-- Escribir libremente --</option>';
    let plantillas = [];

    try {
      const respuesta = await fetch(`/plantillas-visita/api/mis-plantillas?rol=${encodeURIComponent(rolNotaElegido)}`);
      plantillas = await respuesta.json();

      // Actualizar la cache local para poder usarlas sin conexion despues
      for (const p of plantillas) {
        await guardarEnStore("plantillas_cache", p);
      }
    } catch (error) {
      // Sin conexion: usar lo que haya quedado guardado la ultima vez, filtrando por el rol elegido
      const todas = await leerTodoDeStore("plantillas_cache");
      plantillas = todas.filter((p) => p.rol_destinatario === rolNotaElegido || p.rol_destinatario === "Todos");
    }

    plantillas.forEach((p) => {
      const opcion = document.createElement("option");
      opcion.value = p.contenido;
      opcion.textContent = `${p.nombre} (${p.rol_destinatario || "Todos"})`;
      selector.appendChild(opcion);
    });

    selector.addEventListener("change", () => {
      if (selector.value) {
        const textarea = document.getElementById("ev-nota");
        textarea.value += (textarea.value ? "\n" : "") + selector.value;
        selector.value = "";
      }
    });
  }

  document.getElementById("btn-guardar-ev").addEventListener("click", async () => {
    // Los cuidadores nunca pueden registrar nota aclaratoria:
    // para ellos, siempre es un informe nuevo.
    const esAclaratoria = !esCuidador && document.getElementById("ev-es-aclaratoria").checked;
    const informeACorregir = esAclaratoria ? document.getElementById("ev-informe-a-corregir").value : null;

    if (esAclaratoria && !informeACorregir) {
      alert("Debe indicar a qué informe corresponde la nota aclaratoria.");
      return;
    }

    const ubicacion = await obtenerUbicacion();
    await encolarAccion("evolucion", {
      paciente_id: visita.paciente_id,
      programacion_id: visita.id,
      profesional_id: perfil.profesional_id,
      tipo_profesional: nombreNotaElegida || perfil.rol,
      nota: document.getElementById("ev-nota").value,
      lat: ubicacion.lat,
      lon: ubicacion.lon,
      tipo_registro: esAclaratoria ? "NOTA_ACLARATORIA" : "INFORME",
      nota_aclaratoria_de: esAclaratoria ? parseInt(informeACorregir) : null,
    });

    alert(esAclaratoria ? "Nota aclaratoria guardada. Se enviará al servidor automáticamente." : "Informe guardado. Se enviará al servidor automáticamente.");
    irA("detalle_visita", visita.id);
  });
}

function renderFirmarPlanilla(visita) {
  contenedor().innerHTML = `
    <div class="card">
      <h3>Firmar planilla de visita</h3>
      <div class="form-group">
        <label>¿Quién firma?</label>
        <select id="pl-firmante">
          <option value="Paciente">El paciente</option>
          <option value="Acompañante">Un acompañante</option>
        </select>
      </div>
      <div class="form-group" id="pl-contenedor-acompanante" style="display:none;">
        <label>Nombre del acompañante</label>
        <input type="text" id="pl-nombre-acompanante">
      </div>
      <label>Firma (dibuje con el dedo)</label>
      <canvas id="pl-lienzo" width="600" height="200" style="width:100%; height:180px; background:#f1f1f1; border:1px solid #ccc; touch-action:none;"></canvas>
      <button class="btn btn-secondary w-100 mt-2" id="pl-btn-limpiar">Borrar firma</button>
      <div class="form-group mt-3">
        <label>Foto de la visita</label>
        <input type="file" accept="image/*" capture="environment" id="pl-foto">
      </div>
      <button class="btn btn-success w-100 mt-3" id="pl-btn-guardar">✔ Confirmar visita</button>
      <button class="btn btn-secondary w-100 mt-2" onclick="irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  document.getElementById("pl-firmante").addEventListener("change", (e) => {
    document.getElementById("pl-contenedor-acompanante").style.display =
      e.target.value === "Acompañante" ? "block" : "none";
  });

  const lienzo = document.getElementById("pl-lienzo");
  const contexto = lienzo.getContext("2d");
  let dibujando = false;

  function posicion(evento) {
    const rect = lienzo.getBoundingClientRect();
    const escalaX = lienzo.width / rect.width;
    const escalaY = lienzo.height / rect.height;
    const punto = evento.touches ? evento.touches[0] : evento;
    return { x: (punto.clientX - rect.left) * escalaX, y: (punto.clientY - rect.top) * escalaY };
  }

  lienzo.addEventListener("touchstart", (e) => {
    dibujando = true;
    const p = posicion(e);
    contexto.beginPath();
    contexto.moveTo(p.x, p.y);
    e.preventDefault();
  });
  lienzo.addEventListener("touchmove", (e) => {
    if (!dibujando) return;
    const p = posicion(e);
    contexto.lineTo(p.x, p.y);
    contexto.stroke();
    e.preventDefault();
  });
  lienzo.addEventListener("touchend", () => (dibujando = false));
  lienzo.addEventListener("mousedown", (e) => { dibujando = true; const p = posicion(e); contexto.beginPath(); contexto.moveTo(p.x, p.y); });
  lienzo.addEventListener("mousemove", (e) => { if (!dibujando) return; const p = posicion(e); contexto.lineTo(p.x, p.y); contexto.stroke(); });
  lienzo.addEventListener("mouseup", () => (dibujando = false));

  document.getElementById("pl-btn-limpiar").addEventListener("click", () => {
    contexto.clearRect(0, 0, lienzo.width, lienzo.height);
  });

  document.getElementById("pl-btn-guardar").addEventListener("click", async () => {
    const firmaBase64 = lienzo.toDataURL("image/png");
    const archivoFoto = document.getElementById("pl-foto").files[0];

    const fotoBase64 = await new Promise((resolve) => {
      if (!archivoFoto) return resolve(null);
      const lector = new FileReader();
      lector.onload = () => resolve(lector.result);
      lector.readAsDataURL(archivoFoto);
    });

    const ubicacion = await obtenerUbicacion();

    await encolarAccion("firmar_planilla", {
      planilla_id: visita.planilla_id,
      firmante: document.getElementById("pl-firmante").value,
      nombre_acompanante: document.getElementById("pl-nombre-acompanante").value,
      firma_base64: firmaBase64,
      foto_base64: fotoBase64,
      lat: ubicacion.lat,
      lon: ubicacion.lon,
      marca_tiempo_offline: new Date().toISOString(),
    });

    visita.planilla_estado = "Firmada";
    await guardarEnStore("agenda_cache", visita);

    alert("Visita confirmada. La firma se enviará al servidor automáticamente cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

async function renderLaboratorio(visita) {
  titulo("Laboratorio Clínico");
  contenedor().innerHTML = `<p class="text-center">Cargando resultados...</p>`;

  let resultados = [];
  try {
    resultados = await apiGet(`/api/movil/paciente/${visita.paciente_id}/laboratorios`);
  } catch (error) {
    resultados = [];
  }

  let html = `<div class="card"><h3>🧪 Laboratorio Clínico</h3></div>`;

  if (resultados.length > 0) {
    html += `<h5 class="mt-2">Resultados ya registrados</h5>`;
    resultados.forEach((r) => {
      html += `
        <div class="card">
          <strong>${r.nombre_examen}</strong><br>
          <small>${r.laboratorio_realizo || ""} · ${r.fecha_resultado || r.fecha_creacion}</small>`;
      if (r.items && r.items.length > 0) {
        html += `<table style="width:100%; font-size:13px; margin-top:6px;">`;
        r.items.forEach((i) => {
          const colores = { Alto: "#c71c22", Bajo: "#dd5600", Normal: "#73a839" };
          const color = colores[i.interpretacion] || "#6c757d";
          html += `<tr>
            <td>${i.nombre_parametro}</td>
            <td>${i.valor_obtenido || ""} ${i.unidad || ""}</td>
            <td>${i.interpretacion ? `<span style="color:${color}; font-weight:bold;">${i.interpretacion}</span>` : ""}</td>
          </tr>`;
        });
        html += `</table>`;
      }
      if (r.resultado_texto) html += `<p style="margin-top:6px;">${r.resultado_texto}</p>`;
      if (r.foto_resultado_base64) html += `<img src="${r.foto_resultado_base64}" style="max-width:100%; max-height:200px;">`;
      html += `</div>`;
    });
  } else {
    html += `<div class="alerta alerta-info">Sin resultados registrados todavía para este paciente.</div>`;
  }

  html += `
    <div class="card">
      <h5>Registrar nuevo resultado</h5>
      <div class="form-group"><label>Examen</label><input type="text" id="lab-examen" placeholder="Ej: Hemograma completo"></div>
      <div class="form-group"><label>Laboratorio que lo realizó</label><input type="text" id="lab-laboratorio"></div>
      <div class="form-group"><label>Fecha del resultado</label><input type="date" id="lab-fecha"></div>

      <label style="font-weight:bold; margin-top:10px; display:block;">Parámetros medidos</label>
      <div id="lab-items-contenedor"></div>
      <button type="button" class="btn btn-secondary w-100" id="btn-agregar-item-lab" style="margin-bottom:10px;">+ Agregar parámetro</button>

      <div class="form-group"><label>Observaciones generales</label><textarea id="lab-texto" rows="3"></textarea></div>
      <div class="form-group">
        <label>Foto del resultado (para constancia)</label>
        <input type="file" accept="image/*" capture="environment" id="lab-foto-input">
      </div>
      <img id="lab-foto-preview" style="max-width:100%; max-height:200px; display:none;" class="mb-2">
      <button class="btn btn-success w-100" id="btn-guardar-laboratorio">Guardar resultado</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  contenedor().innerHTML = html;

  function agregarFilaItemMovil() {
    const fila = document.createElement("div");
    fila.className = "fila-item-lab-movil";
    fila.style.cssText = "border:1px solid #dee2e6; border-radius:6px; padding:8px; margin-bottom:8px;";
    fila.innerHTML = `
      <input type="text" class="campo-nombre-parametro" placeholder="Parámetro (ej: Glóbulos rojos)" style="margin-bottom:4px;">
      <div style="display:flex; gap:4px;">
        <input type="text" class="campo-valor-obtenido" placeholder="Valor" style="flex:1;">
        <input type="text" class="campo-unidad" placeholder="Unidad" style="flex:1;">
      </div>
      <div style="display:flex; gap:4px; margin-top:4px;">
        <input type="number" step="any" class="campo-rango-min" placeholder="Rango mín." style="flex:1;">
        <input type="number" step="any" class="campo-rango-max" placeholder="Rango máx." style="flex:1;">
      </div>
      <button type="button" class="btn btn-secondary btn-quitar-item-movil" style="margin-top:4px; width:100%;">Quitar</button>
    `;
    document.getElementById("lab-items-contenedor").appendChild(fila);
    fila.querySelector(".btn-quitar-item-movil").addEventListener("click", () => fila.remove());
  }

  document.getElementById("btn-agregar-item-lab").addEventListener("click", agregarFilaItemMovil);
  agregarFilaItemMovil();

  let fotoCapturada = null;
  document.getElementById("lab-foto-input").addEventListener("change", (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => {
      fotoCapturada = lector.result;
      const vista = document.getElementById("lab-foto-preview");
      vista.src = lector.result;
      vista.style.display = "block";
    };
    lector.readAsDataURL(archivo);
  });

  document.getElementById("btn-guardar-laboratorio").addEventListener("click", async () => {
    const examen = document.getElementById("lab-examen").value;
    if (!examen) {
      alert("Debe indicar el nombre del examen.");
      return;
    }

    const items = [];
    document.querySelectorAll(".fila-item-lab-movil").forEach((fila) => {
      const nombre = fila.querySelector(".campo-nombre-parametro").value.trim();
      if (!nombre) return;
      items.push({
        nombre_parametro: nombre,
        valor_obtenido: fila.querySelector(".campo-valor-obtenido").value.trim(),
        unidad: fila.querySelector(".campo-unidad").value.trim(),
        rango_min: fila.querySelector(".campo-rango-min").value || null,
        rango_max: fila.querySelector(".campo-rango-max").value || null,
      });
    });

    await encolarAccion("resultado_laboratorio", {
      paciente_id: visita.paciente_id,
      nombre_examen: examen,
      laboratorio_realizo: document.getElementById("lab-laboratorio").value,
      fecha_resultado: document.getElementById("lab-fecha").value,
      resultado_texto: document.getElementById("lab-texto").value,
      foto_resultado_base64: fotoCapturada,
      profesional_id: perfil.profesional_id,
      items: items,
    });

    alert("Resultado de laboratorio guardado. Se sincronizará cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

function renderOrdenMedica(visita) {
  titulo("Órdenes Médicas");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");

  contenedor().innerHTML = `
    <div class="card">
      <h3>📋 Nueva orden médica</h3>
      <small>${nombrePaciente}</small>
      <div class="form-group">
        <label>Tipo de orden</label>
        <select id="orden-tipo">
          <option value="Medicamento">Medicamento</option>
          <option value="Examen">Examen</option>
          <option value="Remisión">Remisión</option>
          <option value="Procedimiento">Procedimiento</option>
          <option value="Otro">Otro</option>
        </select>
      </div>
      <div class="form-group"><label>Descripción de la orden</label><textarea id="orden-descripcion" rows="5" placeholder="Ej: Acetaminofén 500mg cada 8 horas por 5 días"></textarea></div>
      <div class="form-group"><label>Código CUPS (opcional)</label><input type="text" id="orden-cups"></div>
      <div class="alerta alerta-info">Al guardar, la orden se envía automáticamente al paciente por WhatsApp/correo, igual que desde la oficina.</div>
      <button class="btn btn-success w-100" id="btn-guardar-orden">Guardar y enviar</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  document.getElementById("btn-guardar-orden").addEventListener("click", async () => {
    const descripcion = document.getElementById("orden-descripcion").value.trim();
    if (!descripcion) {
      alert("Debe describir la orden médica.");
      return;
    }

    await encolarAccion("crear_orden_medica", {
      paciente_id: visita.paciente_id,
      profesional_id: perfil.profesional_id,
      tipo_orden: document.getElementById("orden-tipo").value,
      descripcion: descripcion,
      codigo_cups: document.getElementById("orden-cups").value,
    });

    alert("Orden médica guardada. Se enviará al paciente cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

async function renderUltimaNotaMedica(visita) {
  titulo("Última Nota Médica");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");

  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  let nota = null;
  try {
    nota = await apiGet(`/api/movil/paciente/${visita.paciente_id}/ultima-nota-medica`);
  } catch (error) {
    nota = null;
  }

  contenedor().innerHTML = `
    <div class="card">
      <h3>🩺 Última Nota Médica</h3>
      <small>${nombrePaciente}</small>
      ${nota ? `
      <div style="margin-top:10px;">
        <strong>Informe N.° ${nota.consecutivo}</strong> · <small>${nota.fecha}</small>
        <p style="margin-top:8px;">${nota.nota}</p>
        <small style="color:#6c757d;">${nota.profesional || ""}${nota.registro_profesional ? " — R.M. " + nota.registro_profesional : ""}</small>
      </div>
      ` : `
      <div class="alerta alerta-info" style="margin-top:10px;">Este paciente todavía no tiene ninguna nota médica registrada.</div>
      `}
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;
}

async function renderProgramaAtencion(visita) {
  titulo("Programa de Atención");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  contenedor().innerHTML = `<p class="text-center">Cargando catálogo...</p>`;

  let catalogo = { programas: [], actividades: [] };
  try {
    catalogo = await apiGet("/api/movil/programa-atencion/catalogo");
  } catch (error) {
    contenedor().innerHTML = `<div class="alerta alerta-danger">No se pudo cargar el catálogo. Necesita conexión para esta pantalla.</div>
      <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>`;
    return;
  }

  let html = `
    <div class="card">
      <h3>📑 Programa de Atención</h3>
      <small>${nombrePaciente}</small>

      <div class="form-group" style="margin-top:10px;">
        <label>Programa</label>
        <select id="pa-programa">
          <option value="">-- Seleccione --</option>
          ${catalogo.programas.map(p => `<option value="${p.id}">${p.nombre}</option>`).join("")}
        </select>
      </div>
      <div class="form-group"><label>Motivo / diagnóstico de ingreso al programa</label><textarea id="pa-motivo" rows="2"></textarea></div>

      <label style="font-weight:bold; margin-top:10px; display:block;">Servicios / actividades a asignar</label>
      <div id="pa-items-contenedor"></div>
      <button type="button" class="btn btn-secondary w-100" id="btn-agregar-actividad-pa" style="margin-bottom:10px;">+ Agregar actividad</button>

      <button class="btn btn-success w-100" id="btn-guardar-programa">Guardar programa y actividades</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  contenedor().innerHTML = html;

  function agregarFilaActividad() {
    const fila = document.createElement("div");
    fila.className = "fila-actividad-pa";
    fila.style.cssText = "border:1px solid #dee2e6; border-radius:6px; padding:8px; margin-bottom:8px;";
    fila.innerHTML = `
      <select class="campo-actividad">
        <option value="">-- Actividad --</option>
        ${catalogo.actividades.map(a => `<option value="${a.id}" data-nombre="${a.nombre}">${a.nombre}</option>`).join("")}
      </select>
      <div style="display:flex; gap:4px; margin-top:4px;">
        <input type="number" class="campo-sesiones" placeholder="N.° sesiones" style="flex:1;">
        <input type="date" class="campo-fecha-inicio" style="flex:1;">
      </div>
      <select class="campo-frecuencia" style="margin-top:4px;">
        <option value="Diaria">Diaria</option>
        <option value="Interdiaria">Interdiaria</option>
        <option value="1 vez por semana">1 vez por semana</option>
        <option value="2 veces por semana">2 veces por semana</option>
        <option value="3 veces por semana">3 veces por semana</option>
        <option value="Cada 8 días">Cada 8 días</option>
        <option value="Cada 15 días">Cada 15 días</option>
        <option value="1 vez al mes">1 vez al mes</option>
      </select>
      <button type="button" class="btn btn-secondary btn-quitar-actividad-pa" style="margin-top:4px; width:100%;">Quitar</button>
    `;
    document.getElementById("pa-items-contenedor").appendChild(fila);
    fila.querySelector(".btn-quitar-actividad-pa").addEventListener("click", () => fila.remove());
  }

  document.getElementById("btn-agregar-actividad-pa").addEventListener("click", agregarFilaActividad);
  agregarFilaActividad();

  document.getElementById("btn-guardar-programa").addEventListener("click", async () => {
    const programaId = document.getElementById("pa-programa").value;
    if (!programaId) {
      alert("Debe seleccionar el programa de atención.");
      return;
    }

    const actividades = [];
    document.querySelectorAll(".fila-actividad-pa").forEach((fila) => {
      const select = fila.querySelector(".campo-actividad");
      const actividadId = select.value;
      if (!actividadId) return;
      actividades.push({
        actividad_id: actividadId,
        nombre_actividad: select.selectedOptions[0].dataset.nombre,
        numero_sesiones: fila.querySelector(".campo-sesiones").value || null,
        fecha_inicio: fila.querySelector(".campo-fecha-inicio").value || new Date().toISOString().slice(0, 10),
        frecuencia: fila.querySelector(".campo-frecuencia").value,
        profesional_id: perfil.profesional_id,
      });
    });

    if (actividades.length === 0) {
      alert("Debe agregar al menos una actividad/servicio.");
      return;
    }

    await encolarAccion("asignar_programa_atencion", {
      paciente_id: visita.paciente_id,
      programa_id: programaId,
      profesional_id: perfil.profesional_id,
      motivo: document.getElementById("pa-motivo").value,
      actividades: actividades,
    });

    alert("Programa y actividades guardados. Se sincronizarán cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

function esPerfilCuidador() {
  return !!(perfil && perfil.rol && perfil.rol.toLowerCase().includes("cuidador"));
}

function esPerfilAdministrativo() {
  const rol = (perfil && perfil.rol || "").toLowerCase();
  return rol.includes("administrativo") || rol.includes("administrador") || rol.includes("coordinador");
}

async function renderVerReporte(visita) {
  titulo("Reporte de la visita");
  contenedor().innerHTML = `<p class="text-center">Cargando reporte...</p>`;

  let informes = [];
  try {
    informes = await apiGet(`/api/movil/visita/${visita.id}/informes`);
  } catch (error) {
    contenedor().innerHTML = `
      <div class="alerta alerta-danger">No se pudo cargar el reporte (necesita conexión a internet para verlo).</div>
      <button class="btn btn-secondary btn-block mt-2" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
    `;
    return;
  }

  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  const esCuidador = esPerfilCuidador();

  let html = `
    <div class="card">
      <h3>Reporte — ${nombrePaciente}</h3>
      <small>${visita.servicio} · ${visita.fecha}</small>
    </div>
  `;

  if (informes.length === 0) {
    html += `<div class="alerta alerta-info">Todavía no se ha registrado ningún informe para esta visita.</div>`;
  } else {
    informes.forEach((i) => {
      const esAclaratoria = i.tipo_registro === "NOTA_ACLARATORIA";
      html += `
        <div class="card" style="${esAclaratoria ? 'border-left:4px solid #dc3545;' : ''}">
          <strong>${esAclaratoria ? "Nota aclaratoria" : "Informe"} N.° ${i.consecutivo}</strong>
          ${i.nota_aclaratoria_de ? `<span style="color:#dc3545"> (corrige el informe N.° ${i.nota_aclaratoria_de})</span>` : ""}
          <br><small>${i.tipo_profesional || ""} · ${i.profesional || ""} · ${i.fecha}</small>
          <p style="margin-top:8px;">${i.nota}</p>
          ${i.firma_profesional_base64 ? `<img src="${i.firma_profesional_base64}" style="max-height:60px;background:white;border:1px solid #dee2e6;">` : ""}
          <button class="btn btn-secondary btn-block mt-1" onclick="window.open('/historia-clinica/informe/${i.id}/imprimir', '_blank')">
            🖨️ Imprimir este informe (con datos completos del paciente)
          </button>
        </div>
      `;
    });
  }

  html += `<button class="btn btn-primary btn-block mt-2" onclick="window.print()">🖨️ Imprimir reporte</button>`;

  if (informes.length > 0) {
    const ultimoInforme = informes.filter((i) => i.tipo_registro === "INFORME").slice(-1)[0];
    if (ultimoInforme) {
      if (esCuidador) {
        html += `<button class="btn btn-secondary btn-block mt-2" id="btn-corregir-reporte">
          ✏️ El informe no quedó bien — registrar uno nuevo
        </button>`;
      } else {
        html += `<button class="btn btn-secondary btn-block mt-2" id="btn-corregir-reporte">
          ✏️ El informe no quedó bien — hacer nota aclaratoria
        </button>`;
      }
    }
  }

  html += `<button class="btn btn-secondary btn-block mt-2" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>`;

  contenedor().innerHTML = html;

  const botonCorregir = document.getElementById("btn-corregir-reporte");
  if (botonCorregir) {
    const ultimoInforme = informes.filter((i) => i.tipo_registro === "INFORME").slice(-1)[0];
    botonCorregir.addEventListener("click", () => {
      if (esCuidador) {
        // Los cuidadores no manejan notas aclaratorias: para
        // ellos, corregir es simplemente registrar un informe
        // nuevo (no reemplaza el anterior, ambos quedan en la
        // historia clínica).
        renderFormularioEvolucion(visita, { forzarNuevoInforme: true });
      } else {
        // Médicos y profesionales de la salud sí usan la nota
        // aclaratoria formal, indicando a qué informe corrige.
        renderFormularioEvolucion(visita, { forzarAclaratoriaDe: ultimoInforme.consecutivo });
      }
    });
  }
}

function calcularDistanciaMetros(lat1, lon1, lat2, lon2) {
  if (lat1 == null || lon1 == null || lat2 == null || lon2 == null) return null;
  const R = 6371000; // radio de la Tierra en metros
  const rad = (g) => (g * Math.PI) / 180;
  const dLat = rad(lat2 - lat1);
  const dLon = rad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function renderCapturaFotoIngreso(visita, accion) {
  const titulo = accion === "ingreso" ? "Registrar ingreso" : "Finalizar labores";

  contenedor().innerHTML = `
    <div class="card">
      <h3>${titulo}</h3>
      <p class="text-muted small">Tome una foto en el domicilio del paciente para corroborar que usted se encuentra en el lugar (junto con la ubicación GPS).</p>
      <div class="form-group">
        <label>Foto</label>
        <input type="file" accept="image/*" capture="environment" id="foto-ingreso-input">
      </div>
      <img id="foto-ingreso-preview" style="max-width:100%; max-height:200px; display:none;" class="mb-2">
      <div id="foto-ingreso-estado" class="small text-muted mb-2"></div>
      <button class="btn btn-primary w-100" id="btn-confirmar-foto-ingreso">✔ Confirmar</button>
      <button class="btn btn-secondary w-100 mt-2" onclick="irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  let fotoCapturada = null;

  document.getElementById("foto-ingreso-input").addEventListener("change", (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => {
      fotoCapturada = lector.result;
      const vista = document.getElementById("foto-ingreso-preview");
      vista.src = lector.result;
      vista.style.display = "block";
    };
    lector.readAsDataURL(archivo);
  });

  document.getElementById("btn-confirmar-foto-ingreso").addEventListener("click", async () => {
    if (!fotoCapturada) {
      alert("Debe tomar o seleccionar una foto para continuar.");
      return;
    }

    document.getElementById("foto-ingreso-estado").textContent = "Obteniendo ubicación...";
    const ubicacion = await obtenerUbicacion();

    if (ubicacion.lat === null) {
      alert("No se pudo obtener su ubicación GPS. Active el permiso de ubicación e intente de nuevo.");
      document.getElementById("foto-ingreso-estado").textContent = "";
      return;
    }

    // Validacion OBLIGATORIA: si el paciente ya tiene una
    // ubicacion registrada, el celular debe estar dentro del
    // radio de su geocerca para poder marcar ingreso/salida.
    // Se calcula aqui mismo en el celular (no depende de
    // internet) comparando contra las coordenadas que ya
    // trae guardadas la agenda.
    if (visita.lat_paciente != null && visita.lon_paciente != null) {
      const distancia = calcularDistanciaMetros(ubicacion.lat, ubicacion.lon, visita.lat_paciente, visita.lon_paciente);
      const radioPermitido = visita.radio_geocerca_metros || 150;

      if (distancia !== null && distancia > radioPermitido) {
        document.getElementById("foto-ingreso-estado").innerHTML =
          `<span style="color:#c71c22; font-weight:bold;">
            ⚠ No puede ${accion === "ingreso" ? "ingresar" : "finalizar"} porque no está en la ubicación del paciente
            (está a ${Math.round(distancia)} metros; el máximo permitido es ${radioPermitido} metros).
          </span>`;
        return;
      }
    }

    await encolarAccion(accion, {
      visita_id: visita.id, lat: ubicacion.lat, lon: ubicacion.lon,
      foto_base64: fotoCapturada, marca_tiempo_offline: new Date().toISOString(),
    });

    if (accion === "ingreso") {
      visita.hora_real_inicio = new Date().toISOString().replace("T", " ").slice(0, 19);
      iniciarMonitoreoTurno(visita);
    } else {
      visita.hora_real_fin = new Date().toISOString().replace("T", " ").slice(0, 19);
      detenerMonitoreoTurno();
    }
    await guardarEnStore("agenda_cache", visita);

    alert("Registrado correctamente. Se sincronizará cuando haya conexión.");
    renderDetalleVisita(visita.id);
  });
}

// ---------------- FICHA DEL PACIENTE ----------------

let _origenFichaPaciente = null;

function irAFichaPacienteDesdeVisita(pacienteId, visitaId) {
  _origenFichaPaciente = visitaId;
  irA("ficha_paciente", pacienteId);
}

async function renderFichaPaciente(pacienteId) {
  titulo("Historia Clínica");
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  const ficha = await obtenerFichaPaciente(pacienteId);

  if (!ficha || !ficha.paciente) {
    contenedor().innerHTML = `<div class="alerta alerta-danger">Sin datos guardados de este paciente (necesita internet la primera vez).</div>`;
    return;
  }

  const p = ficha.paciente;
  const nombre = [p.primer_nombre, p.segundo_nombre, p.primer_apellido, p.segundo_apellido].filter(Boolean).join(" ");

  let alergiasHtml = `<div class="alerta alerta-success">Sin alergias activas registradas.</div>`;
  if (ficha.alergias && ficha.alergias.length) {
    alergiasHtml = `<div class="alerta alerta-danger"><strong>⚠ Alergias:</strong><br>` +
      ficha.alergias.map((a) => `${a.alergeno} (${a.severidad})`).join("<br>") + `</div>`;
  }

  let medicamentosHtml = "";
  if (ficha.medicamentos_activos && ficha.medicamentos_activos.length) {
    medicamentosHtml = `<div class="card"><h3>💊 Medicamentos activos</h3>` +
      ficha.medicamentos_activos.map((m) => `<div>${m.nombre} — ${m.dosis || ""} ${m.frecuencia || ""}</div>`).join("") +
      `</div>`;
  }

  let diagnosticosHtml = "";
  if (ficha.diagnosticos && ficha.diagnosticos.length) {
    diagnosticosHtml = `<div class="card"><h3>Diagnósticos</h3>` +
      ficha.diagnosticos.map((d) => `<div>${d.codigo_cie10} - ${d.diagnostico}</div>`).join("") +
      `</div>`;
  }

  contenedor().innerHTML = `
    <div class="card">
      <h3>${nombre}</h3>
      <small>${p.tipo_documento} ${p.documento} · ${p.eps || ""}</small>
    </div>
    ${alergiasHtml}
    ${medicamentosHtml}
    ${diagnosticosHtml}
    <button class="btn btn-secondary btn-block mt-2" onclick="volverDeFichaPaciente(${pacienteId})">← Volver</button>
  `;
}

function volverDeFichaPaciente(pacienteId) {
  if (_origenFichaPaciente) {
    const visitaId = _origenFichaPaciente;
    _origenFichaPaciente = null;
    irA("detalle_visita", visitaId);
  } else {
    irA("agenda");
  }
}

// ---------------- BÚSQUEDA DE PACIENTES ----------------

async function renderBusquedaPacientes() {
  titulo("Pacientes");
  contenedor().innerHTML = `
    <div class="card">
      <p style="font-size:13px;color:#6c757d">
        Se muestran los pacientes de las visitas ya cargadas en la agenda.
        Abra la agenda con internet para actualizar la lista.
      </p>
    </div>
    <div id="lista-pacientes"></div>`;

  const visitas = await leerTodoDeStore("agenda_cache");
  const vistos = new Map();
  visitas.forEach((v) => {
    if (!vistos.has(v.paciente_id)) {
      vistos.set(v.paciente_id, [v.primer_nombre, v.primer_apellido].filter(Boolean).join(" "));
    }
  });

  const lista = document.getElementById("lista-pacientes");
  if (vistos.size === 0) {
    lista.innerHTML = `<div class="alerta alerta-info">No hay pacientes en caché todavía.</div>`;
    return;
  }

  lista.innerHTML = Array.from(vistos.entries())
    .map(([id, nombre]) => `<div class="card" onclick="irA('ficha_paciente', ${id})"><strong>${nombre}</strong></div>`)
    .join("");
}

// ---------------- PENDIENTES POR ENVIAR ----------------

async function renderPendientes() {
  titulo("Por enviar al servidor");
  const pendientes = await leerTodoDeStore("cola_offline");

  const etiquetas = {
    ingreso: "Ingreso a labores",
    salida: "Finalización de labores",
    signos_vitales: "Signos vitales",
    medicamento_administrado: "Medicamento administrado",
    evolucion: "Nota de evolución",
    orden_medica: "Orden médica",
  };

  contenedor().innerHTML = `
    <button class="btn btn-primary btn-block" id="btn-sync-ahora">🔄 Sincronizar ahora</button>
    <div id="lista-pendientes" class="mt-2"></div>`;

  document.getElementById("btn-sync-ahora").addEventListener("click", async () => {
    await intentarSincronizar();
    renderPendientes();
  });

  const lista = document.getElementById("lista-pendientes");

  if (pendientes.length === 0) {
    lista.innerHTML = `<div class="alerta alerta-success">Todo está sincronizado. No hay nada pendiente.</div>`;
    return;
  }

  lista.innerHTML = pendientes
    .map(
      (a) => `
      <div class="card">
        <strong>${etiquetas[a.tipo] || a.tipo}</strong><br>
        <small>Registrado: ${new Date(a.creado_en).toLocaleString()}</small>
      </div>`
    )
    .join("");
}

// ---------------- PERFIL ----------------

function renderPerfil() {
  titulo("Mi Perfil");
  contenedor().innerHTML = `
    <div class="card">
      <h3>${perfil.nombre}</h3>
      <small>${perfil.rol}</small>
    </div>
    <button class="btn btn-danger btn-block" id="btn-logout">Cerrar sesión</button>
  `;

  document.getElementById("btn-logout").addEventListener("click", async () => {
    if (!confirm("¿Cerrar sesión? Los datos pendientes de enviar se conservarán.")) return;
    try {
      await fetch("/api/movil/logout", { method: "POST", credentials: "same-origin" });
    } catch (e) {}
    await limpiarDatosDeSesion();
    localStorage.removeItem("homecare_perfil");
    perfil = null;
    mostrarNav(false);
    renderLogin();
  });
}

// ==========================================================
// NAVEGACIÓN INFERIOR
// ==========================================================

document.querySelectorAll(".bottom-nav button").forEach((boton) => {
  boton.addEventListener("click", () => irA(boton.dataset.vista));
});

// ==========================================================
// ARRANQUE
// ==========================================================

async function iniciar() {
  db = await abrirDB();
  actualizarEstadoConexion(await contarPendientes());

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/app/sw.js").catch(console.error);
  }

  if (perfil && perfil.profesional_id) {
    mostrarNav(true);
    irA("agenda");
    reanudarMonitoreoSiHayTurnoAbierto();
    iniciarRecordatoriosDeTurno();
  } else {
    renderLogin();
  }

  intentarSincronizar();
}

iniciar();
