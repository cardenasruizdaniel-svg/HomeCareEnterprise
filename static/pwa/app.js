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

async function intentarSincronizar(esManual = false) {
  if (sincronizando) {
    return { ok: false, motivo: "ya_en_progreso" };
  }

  // navigator.onLine solo dice si hay una antena de red prendida
  // (wifi/datos), NO si de verdad hay internet funcionando -- en
  // zonas con señal débil puede decir "true" sin que en realidad
  // haya conexión, o quedarse en "false" por un momento aunque sí
  // haya señal. Para el intento AUTOMÁTICO se respeta como una
  // primera señal rápida (para no gastar batería/datos intentando
  // en vano), pero el botón "Sincronizar ahora" siempre intenta
  // de verdad -- si en realidad no hay internet, el propio envío
  // fallará y lo dirá claramente.
  if (!esManual && !navigator.onLine) return { ok: false, motivo: "sin_señal" };

  sincronizando = true;
  actualizarEstadoConexion(await contarPendientes(), "sincronizando");

  let resultadoFinal = { ok: true, enviados: 0 };

  try {
    const pendientes = await leerTodoDeStore("cola_offline");

    if (pendientes.length === 0) {
      actualizarEstadoConexion(0);
      return { ok: true, enviados: 0, sinPendientes: true };
    }

    const cuerpo = {
      acciones: pendientes.map((a) => ({ id: a.id, tipo: a.tipo, payload: a.payload })),
    };

    // Límite de tiempo: si la conexión está muy lenta o se
    // cuelga, después de 25 segundos se cancela el intento en
    // vez de quedarse esperando indefinidamente (lo cual
    // bloqueaba cualquier otro intento de sincronizar mientras
    // tanto, automático o manual).
    const controlador = new AbortController();
    const limiteTiempo = setTimeout(() => controlador.abort(), 25000);

    let respuesta;
    try {
      respuesta = await fetch("/api/movil/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(cuerpo),
        signal: controlador.signal,
      });
    } finally {
      clearTimeout(limiteTiempo);
    }

    if (!respuesta.ok) throw new Error("El servidor rechazó la sincronización.");

    const datos = await respuesta.json();
    let enviadosOk = 0;

    for (const resultado of datos.resultados) {
      if (resultado.ok) {
        await borrarDeStore("cola_offline", resultado.id);
        enviadosOk++;

        const geocerca = resultado.resultado && resultado.resultado.geocerca;
        if (geocerca && geocerca.verificable !== undefined) {
          mostrarAvisoGeocerca(geocerca);
        }
      } else {
        // Una accion que el servidor rechazo (ej. verificacion
        // facial que no coincide, o el turno ya se habia
        // cerrado) NUNCA va a funcionar con los mismos datos
        // por mas veces que se reintente -- asi que se avisa
        // claramente y se saca de la cola, en vez de quedar
        // reintentando en silencio para siempre sin que la
        // persona se entere de que algo no se guardo.
        await borrarDeStore("cola_offline", resultado.id);
        alert(
          "⚠ Una acción no se pudo guardar y no se va a reintentar sola:\n\n" +
          (resultado.error || "Error desconocido del servidor.") +
          "\n\nSi era un registro de ingreso/salida, vuelva a intentarlo desde la pantalla de la visita."
        );
      }
    }

    resultadoFinal = { ok: true, enviados: enviadosOk, total: pendientes.length };
  } catch (error) {
    const esTimeout = error.name === "AbortError";
    console.warn("No se pudo sincronizar todavía:", error.message);
    resultadoFinal = {
      ok: false,
      motivo: esTimeout ? "tiempo_agotado" : "error_conexion",
      mensaje: esTimeout
        ? "La conexión está muy lenta y se canceló el intento después de 25 segundos. Se reintentará solo."
        : "No se pudo conectar con el servidor. Se reintentará solo cuando haya señal.",
    };
  } finally {
    sincronizando = false;
    actualizarContadorPendientes();
  }

  return resultadoFinal;
}

window.addEventListener("online", () => intentarSincronizar());
setInterval(() => intentarSincronizar(), 15000);

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

function actualizarEstadoConexion(pendientes, estadoEspecial) {
  const el = document.getElementById("estado-conexion");
  if (!el) return;

  if (estadoEspecial === "sincronizando") {
    el.textContent = "⏳ Enviando...";
    el.className = "estado-conexion pendiente";
  } else if (!navigator.onLine) {
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

// ==========================================================
// VISOR DE REPORTES DENTRO DE LA APP
//
// Antes, "imprimir" abría una pestaña nueva del navegador,
// lo que hacia que el usuario sintiera que "se salio" de la
// app. Esto en cambio muestra el reporte en una ventana
// superpuesta DENTRO de la misma app (un iframe a pantalla
// completa con boton de cerrar e imprimir), sin navegar a
// ningun lado ni abrir nada por fuera.
// ==========================================================

function abrirReporteEnApp(url) {
  const overlay = document.createElement("div");
  overlay.id = "overlay-reporte-app";
  overlay.style.cssText = "position:fixed; inset:0; background:#fff; z-index:9999; display:flex; flex-direction:column;";
  overlay.innerHTML = `
    <div style="display:flex; gap:8px; padding:10px; background:#0d6efd; flex-shrink:0;">
      <button id="btn-cerrar-reporte-app" style="background:#fff; color:#0d6efd; border:none; border-radius:6px; padding:8px 14px; font-weight:bold;">← Volver a la app</button>
      <button id="btn-imprimir-reporte-app" style="background:#198754; color:#fff; border:none; border-radius:6px; padding:8px 14px; font-weight:bold;">🖨️ Imprimir</button>
    </div>
    <iframe id="iframe-reporte-app" src="${url}" style="flex:1; border:none; width:100%;"></iframe>
  `;
  document.body.appendChild(overlay);

  document.getElementById("btn-cerrar-reporte-app").addEventListener("click", () => overlay.remove());
  document.getElementById("btn-imprimir-reporte-app").addEventListener("click", () => {
    const iframe = document.getElementById("iframe-reporte-app");
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
  });
}
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
    <div style="text-align:center; padding:30px 10px 10px;">
      <img src="/static/img/logo_homecare.png" alt="HomeCare del Quindío" style="width:110px; height:110px; object-fit:contain; border-radius:20px; background:white; box-shadow:0 4px 16px rgba(0,0,0,0.12); padding:10px;">
      <h2 style="margin:16px 0 2px; color:var(--hc-navy);">
        <span style="color:var(--hc-teal-oscuro);">Home</span><span style="color:var(--hc-rosa);">Care</span>
      </h2>
      <p style="color:#6c757d; margin:0 0 20px; font-size:13px;">del Quindío I.P.S. — App de Campo</p>
    </div>
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

      if (perfilDatos.tiene_foto_enrolamiento === false) {
        renderEnrolamientoFacial();
      } else {
        irA("agenda");
        reanudarMonitoreoSiHayTurnoAbierto();
        iniciarRecordatoriosDeTurno();
      }
    } catch (error) {
      errorEl.innerHTML = `<div class="alerta alerta-danger">No hay conexión. Debe iniciar sesión la primera vez con internet.</div>`;
    }
  });
}

// ==========================================================
// ENROLAMIENTO FACIAL EN EL PRIMER INGRESO A LA APP
//
// Si el profesional todavia no tiene una foto de enrolamiento
// guardada, se le pide tomarse una ANTES de dejarlo continuar
// -- esa foto queda registrada como su foto de enrolamiento, y
// desde ese momento se usa para verificar que sea la misma
// persona cada vez que registre un ingreso/salida de visita.
// Esto es EXCLUSIVO de la app (en la web, el enrolamiento lo
// hace el administrador desde la ficha del profesional).
// ==========================================================

function renderEnrolamientoFacial() {
  mostrarNav(false);
  titulo("Enrolamiento facial");

  contenedor().innerHTML = `
    <div class="card">
      <h3>📸 Registre su rostro</h3>
      <p class="text-muted small">
        Es la primera vez que ingresa a la app. Antes de continuar, tómese una foto de su rostro —
        esta quedará guardada como su foto de referencia, y se usará para confirmar que es usted quien
        registra el ingreso y la salida de cada visita. Ubique su rostro dentro del círculo, con buena luz.
      </p>

      <div id="camara-enrolamiento-app-contenedor" style="position:relative; max-width:100%; margin-bottom:10px;">
        <video id="video-enrolamiento-app" autoplay playsinline style="width:100%; border-radius:8px; background:#000;"></video>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:62%; aspect-ratio:1/1.25; border:4px solid #00c2b8; border-radius:50%; pointer-events:none; box-shadow:0 0 0 2000px rgba(0,0,0,0.35);"></div>
      </div>
      <canvas id="canvas-enrolamiento-app" style="display:none;"></canvas>

      <button class="btn btn-primary w-100" id="btn-tomar-foto-enrolamiento-app">📸 Tomar foto</button>

      <img id="preview-enrolamiento-app" style="max-width:100%; max-height:220px; display:none; border-radius:8px;" class="mb-2 mt-2">
      <div id="estado-enrolamiento-app" class="small text-muted mb-2"></div>
      <button class="btn btn-primary w-100" id="btn-confirmar-enrolamiento-app" style="display:none;">✔ Guardar y continuar</button>
      <button class="btn btn-secondary w-100 mt-2" id="btn-repetir-enrolamiento-app" style="display:none;">↺ Repetir foto</button>
    </div>`;

  let fotoEnrolamientoCapturada = null;
  let flujoCamaraEnrolamientoApp = null;

  async function iniciarCamaraEnrolamientoApp() {
    try {
      flujoCamaraEnrolamientoApp = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
      document.getElementById("video-enrolamiento-app").srcObject = flujoCamaraEnrolamientoApp;
    } catch (error) {
      document.getElementById("estado-enrolamiento-app").innerHTML =
        `<span style="color:#c71c22;">No se pudo acceder a la cámara: ${error.message}. Debe permitir el acceso a la cámara para poder usar la app.</span>`;
    }
  }

  function detenerCamaraEnrolamientoApp() {
    if (flujoCamaraEnrolamientoApp) {
      flujoCamaraEnrolamientoApp.getTracks().forEach((pista) => pista.stop());
      flujoCamaraEnrolamientoApp = null;
    }
  }

  iniciarCamaraEnrolamientoApp();

  document.getElementById("btn-tomar-foto-enrolamiento-app").addEventListener("click", () => {
    const video = document.getElementById("video-enrolamiento-app");
    const lienzo = document.getElementById("canvas-enrolamiento-app");
    lienzo.width = video.videoWidth;
    lienzo.height = video.videoHeight;
    lienzo.getContext("2d").drawImage(video, 0, 0);
    fotoEnrolamientoCapturada = lienzo.toDataURL("image/jpeg", 0.9);

    const vista = document.getElementById("preview-enrolamiento-app");
    vista.src = fotoEnrolamientoCapturada;
    vista.style.display = "block";

    detenerCamaraEnrolamientoApp();
    document.getElementById("camara-enrolamiento-app-contenedor").style.display = "none";
    document.getElementById("btn-tomar-foto-enrolamiento-app").style.display = "none";
    document.getElementById("btn-confirmar-enrolamiento-app").style.display = "block";
    document.getElementById("btn-repetir-enrolamiento-app").style.display = "block";
  });

  document.getElementById("btn-repetir-enrolamiento-app").addEventListener("click", () => {
    fotoEnrolamientoCapturada = null;
    document.getElementById("preview-enrolamiento-app").style.display = "none";
    document.getElementById("camara-enrolamiento-app-contenedor").style.display = "block";
    document.getElementById("btn-tomar-foto-enrolamiento-app").style.display = "block";
    document.getElementById("btn-confirmar-enrolamiento-app").style.display = "none";
    document.getElementById("btn-repetir-enrolamiento-app").style.display = "none";
    document.getElementById("estado-enrolamiento-app").textContent = "";
    iniciarCamaraEnrolamientoApp();
  });

  document.getElementById("btn-confirmar-enrolamiento-app").addEventListener("click", async () => {
    const estadoEl = document.getElementById("estado-enrolamiento-app");
    const botonConfirmar = document.getElementById("btn-confirmar-enrolamiento-app");
    botonConfirmar.disabled = true;
    estadoEl.textContent = "Guardando...";

    try {
      const respuesta = await fetch("/api/movil/enrolamiento-facial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ foto_base64: fotoEnrolamientoCapturada }),
      });

      if (!respuesta.ok) {
        const datosError = await respuesta.json().catch(() => ({}));
        estadoEl.innerHTML = `<span style="color:#c71c22;">${datosError.detail || "No se pudo guardar la foto."}</span>`;
        botonConfirmar.disabled = false;
        return;
      }

      alert("Foto de enrolamiento guardada correctamente. Ya puede usar la app normalmente.");
      irA("agenda");
      reanudarMonitoreoSiHayTurnoAbierto();
      iniciarRecordatoriosDeTurno();
    } catch (error) {
      estadoEl.innerHTML = `<span style="color:#c71c22;">Sin conexión — necesita internet para guardar su foto de enrolamiento la primera vez.</span>`;
      botonConfirmar.disabled = false;
    }
  });
}

// ---------------- AGENDA ----------------

let vistaAgendaActual = "dia";
let fechaReferenciaAgenda = new Date();

function _formatoFechaISO(fecha) {
  return fecha.toISOString().slice(0, 10);
}

function _rangoDeVista(vista, fechaRef) {
  const inicio = new Date(fechaRef);
  const fin = new Date(fechaRef);

  if (vista === "dia") {
    // inicio y fin ya son el mismo dia
  } else if (vista === "semana") {
    const diaSemana = inicio.getDay(); // 0=domingo
    const offsetLunes = diaSemana === 0 ? -6 : 1 - diaSemana;
    inicio.setDate(inicio.getDate() + offsetLunes);
    fin.setTime(inicio.getTime());
    fin.setDate(fin.getDate() + 6);
  } else if (vista === "mes") {
    inicio.setDate(1);
    fin.setMonth(fin.getMonth() + 1);
    fin.setDate(0);
  }

  return { inicio: _formatoFechaISO(inicio), fin: _formatoFechaISO(fin) };
}

async function renderAgenda() {
  titulo("Mi Agenda");
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  const { inicio, fin } = _rangoDeVista(vistaAgendaActual, fechaReferenciaAgenda);
  const visitas = await obtenerAgenda(inicio, fin);

  const etiquetaPeriodo = vistaAgendaActual === "dia"
    ? new Date(fechaReferenciaAgenda).toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" })
    : `${inicio} — ${fin}`;

  let html = `
    <div class="card">
      <div style="display:flex; gap:4px; margin-bottom:8px;">
        <button class="btn ${vistaAgendaActual === "dia" ? "btn-primary" : "btn-secondary"}" style="flex:1;" id="btn-vista-dia">Día</button>
        <button class="btn ${vistaAgendaActual === "semana" ? "btn-primary" : "btn-secondary"}" style="flex:1;" id="btn-vista-semana">Semana</button>
        <button class="btn ${vistaAgendaActual === "mes" ? "btn-primary" : "btn-secondary"}" style="flex:1;" id="btn-vista-mes">Mes</button>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <button class="btn btn-secondary" id="btn-periodo-anterior">←</button>
        <strong style="text-transform:capitalize;">${etiquetaPeriodo}</strong>
        <button class="btn btn-secondary" id="btn-periodo-siguiente">→</button>
      </div>
    </div>
  `;

  if (!visitas.length) {
    html += `<div class="alerta alerta-info">No tiene visitas asignadas en este periodo.</div>`;
  } else if (vistaAgendaActual === "dia") {
    html += visitas.map((v) => _tarjetaVisitaAgenda(v)).join("");
  } else {
    // Semana o mes: agrupar por fecha, para ver dia a dia
    const porFecha = {};
    visitas.forEach((v) => {
      porFecha[v.fecha] = porFecha[v.fecha] || [];
      porFecha[v.fecha].push(v);
    });
    Object.keys(porFecha).sort().forEach((fecha) => {
      const fechaLegible = new Date(fecha + "T00:00:00").toLocaleDateString("es-CO", { weekday: "short", day: "numeric", month: "short" });
      html += `<h5 class="mt-2" style="text-transform:capitalize;">${fechaLegible}</h5>`;
      html += porFecha[fecha].map((v) => _tarjetaVisitaAgenda(v)).join("");
    });
  }

  contenedor().innerHTML = html;

  document.getElementById("btn-vista-dia").addEventListener("click", () => { vistaAgendaActual = "dia"; renderAgenda(); });
  document.getElementById("btn-vista-semana").addEventListener("click", () => { vistaAgendaActual = "semana"; renderAgenda(); });
  document.getElementById("btn-vista-mes").addEventListener("click", () => { vistaAgendaActual = "mes"; renderAgenda(); });

  document.getElementById("btn-periodo-anterior").addEventListener("click", () => {
    _moverPeriodo(-1);
    renderAgenda();
  });
  document.getElementById("btn-periodo-siguiente").addEventListener("click", () => {
    _moverPeriodo(1);
    renderAgenda();
  });
}

function _moverPeriodo(direccion) {
  const nueva = new Date(fechaReferenciaAgenda);
  if (vistaAgendaActual === "dia") nueva.setDate(nueva.getDate() + direccion);
  else if (vistaAgendaActual === "semana") nueva.setDate(nueva.getDate() + direccion * 7);
  else if (vistaAgendaActual === "mes") nueva.setMonth(nueva.getMonth() + direccion);
  fechaReferenciaAgenda = nueva;
}

function _tarjetaVisitaAgenda(v) {
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

    ${esPerfilCuidador() ? "" : `
    ${!visita.ubicacion_confirmada ? `
    <button class="btn btn-secondary btn-block" id="btn-actualizar-ubicacion-paciente">
      📍 Registrar ubicación exacta del paciente
    </button>
    ` : `
    <div class="alerta alerta-info">📍 La ubicación de este paciente ya fue registrada. Para volver a tomarla, un administrador debe borrarla primero desde la ficha del paciente en la web.</div>
    `}
    `}

    <button class="btn btn-secondary btn-block" onclick="irAFichaPacienteDesdeVisita(${visita.paciente_id}, ${visita.id})">
      🧑‍⚕️ Ver historia clínica y alergias
    </button>

    ${esPerfilCuidador() ? "" : `
    <button class="btn btn-secondary btn-block" id="btn-signos">🌡️ Signos Vitales y Tallas</button>
    <button class="btn btn-secondary btn-block" id="btn-laboratorio">🧪 Resultados de laboratorio</button>
    <button class="btn btn-secondary btn-block" id="btn-examen-fisico">🩻 Examen Físico</button>
    <button class="btn btn-secondary btn-block" id="btn-alergias">⚠️ Alergias</button>
    <button class="btn btn-secondary btn-block" id="btn-antecedentes">📖 Antecedentes</button>
    `}

    <button class="btn btn-secondary btn-block" id="btn-evolucion">${esPerfilCuidador() ? "📋 Registro Informe de Cuidador" : "📝 Registrar evolución"}</button>

    ${esPerfilCuidador() ? "" : `
    ${esPerfilConOrdenes() ? `<button class="btn btn-secondary btn-block" id="btn-ordenes">📋 Órdenes Médicas</button>` : ""}
    <button class="btn btn-secondary btn-block" id="btn-programa-atencion">📑 Programa de Atención</button>
    <button class="btn btn-secondary btn-block" id="btn-ultima-nota-medica">🩺 Última Nota Médica</button>
    <button class="btn btn-secondary btn-block" id="btn-recomendaciones">📝 Recomendaciones</button>
    ${esPerfilConMedicamentos() ? `<button class="btn btn-secondary btn-block" id="btn-medicamento">💊 Registrar medicamento administrado</button>` : ""}
    `}

    ${visita.planilla_id && visita.planilla_estado !== "Firmada" ? `
    <button class="btn btn-primary btn-block" id="btn-firmar-planilla">✍️ Firmar planilla de visita</button>
    ` : ""}

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
    const botonMedicamento = document.getElementById("btn-medicamento");
    if (botonMedicamento) botonMedicamento.addEventListener("click", () => renderFormularioMedicamento(visita));
    document.getElementById("btn-laboratorio").addEventListener("click", () => renderLaboratorio(visita));
    const botonOrdenes = document.getElementById("btn-ordenes");
    if (botonOrdenes) botonOrdenes.addEventListener("click", () => renderOrdenMedica(visita));
    document.getElementById("btn-ultima-nota-medica").addEventListener("click", () => renderUltimaNotaMedica(visita));
    document.getElementById("btn-programa-atencion").addEventListener("click", () => renderProgramaAtencion(visita));
    document.getElementById("btn-alergias").addEventListener("click", () => renderAlergias(visita));
    document.getElementById("btn-antecedentes").addEventListener("click", () => renderAntecedentes(visita));
    document.getElementById("btn-examen-fisico").addEventListener("click", () => renderExamenFisico(visita));
    document.getElementById("btn-recomendaciones").addEventListener("click", () => renderRecomendaciones(visita));
  }
}

function renderFormularioSignos(visita) {
  contenedor().innerHTML = `
    <div class="card">
      <h3>Signos Vitales y Tallas</h3>
      <div class="form-group"><label>Peso (kg)</label><input type="number" step="0.1" id="sv-peso"></div>
      <div class="form-group"><label>Talla (metros, ej: 1.70 — también acepta cm, ej: 170)</label><input type="number" step="0.01" id="sv-talla" placeholder="1.70"></div>
      <div class="form-group"><label>IMC (calculado)</label><input type="text" id="sv-imc" readonly style="background:#f0f0f0;"></div>
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

  function calcularImcMovil() {
    const peso = parseFloat(document.getElementById("sv-peso").value);
    let talla = parseFloat(document.getElementById("sv-talla").value);
    // Si escriben la talla en centímetros (ej. 170) en vez de
    // metros (1.70), se detecta y se convierte solo -- es muy
    // común escribirla así por costumbre.
    if (talla > 3) talla = talla / 100;
    if (peso > 0 && talla > 0) {
      document.getElementById("sv-imc").value = (peso / (talla * talla)).toFixed(2);
    } else {
      document.getElementById("sv-imc").value = "";
    }
  }
  document.getElementById("sv-peso").addEventListener("input", calcularImcMovil);
  document.getElementById("sv-talla").addEventListener("input", calcularImcMovil);

  document.getElementById("btn-guardar-signos").addEventListener("click", async () => {
    const datos = {
      peso: parseFloat(document.getElementById("sv-peso").value) || null,
      talla: (() => {
        let t = parseFloat(document.getElementById("sv-talla").value);
        if (!t) return null;
        return t > 3 ? t / 100 : t; // normaliza a metros si la escribieron en centímetros
      })(),
      imc: parseFloat(document.getElementById("sv-imc").value) || null,
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

    alert("Signos vitales y tallas guardados. Se enviarán al servidor automáticamente.");
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
      <div class="form-group"><label>Tipo de examen (elija del catálogo, o escriba uno personalizado abajo)</label>
        <select id="lab-catalogo-examen">
          <option value="">-- Personalizado --</option>
        </select>
      </div>
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

  function agregarFilaItemMovil(valoresIniciales) {
    valoresIniciales = valoresIniciales || {};
    const fila = document.createElement("div");
    fila.className = "fila-item-lab-movil";
    fila.style.cssText = "border:1px solid #dee2e6; border-radius:6px; padding:8px; margin-bottom:8px;";
    fila.innerHTML = `
      <input type="text" class="campo-nombre-parametro" placeholder="Parámetro (ej: Glóbulos rojos)" style="margin-bottom:4px;" value="${valoresIniciales.nombre_parametro || ''}">
      <div style="display:flex; gap:4px;">
        <input type="text" class="campo-valor-obtenido" placeholder="Valor" style="flex:1;">
        <input type="text" class="campo-unidad" placeholder="Unidad" style="flex:1;" value="${valoresIniciales.unidad || ''}">
      </div>
      <div style="display:flex; gap:4px; margin-top:4px;">
        <input type="number" step="any" class="campo-rango-min" placeholder="Rango mín." style="flex:1;" value="${valoresIniciales.rango_min ?? ''}">
        <input type="number" step="any" class="campo-rango-max" placeholder="Rango máx." style="flex:1;" value="${valoresIniciales.rango_max ?? ''}">
      </div>
      <button type="button" class="btn btn-secondary btn-quitar-item-movil" style="margin-top:4px; width:100%;">Quitar</button>
    `;
    document.getElementById("lab-items-contenedor").appendChild(fila);
    fila.querySelector(".btn-quitar-item-movil").addEventListener("click", () => fila.remove());
  }

  document.getElementById("btn-agregar-item-lab").addEventListener("click", agregarFilaItemMovil);
  agregarFilaItemMovil();

  // Cargar el catalogo de examenes para el desplegable, agrupado por categoría
  let catalogoExamenesLab = [];
  try {
    catalogoExamenesLab = await apiGet("/api/movil/laboratorios/catalogo");
    const selectCatalogo = document.getElementById("lab-catalogo-examen");

    const categorias = {};
    catalogoExamenesLab.forEach((e) => {
      const cat = e.categoria || "Otros";
      categorias[cat] = categorias[cat] || [];
      categorias[cat].push(e);
    });

    let opcionesHtml = '<option value="">-- Personalizado --</option>';
    Object.keys(categorias).sort().forEach((categoria) => {
      opcionesHtml += `<optgroup label="${categoria}">`;
      categorias[categoria].forEach((e) => {
        opcionesHtml += `<option value="${e.id}">${e.nombre_examen}</option>`;
      });
      opcionesHtml += `</optgroup>`;
    });
    selectCatalogo.innerHTML = opcionesHtml;

    selectCatalogo.addEventListener("change", () => {
      const examenId = selectCatalogo.value;
      if (!examenId) return;
      const examen = catalogoExamenesLab.find((e) => String(e.id) === examenId);
      document.getElementById("lab-examen").value = examen.nombre_examen;
      document.getElementById("lab-items-contenedor").innerHTML = "";
      examen.parametros.forEach((p) => agregarFilaItemMovil(p));
    });
  } catch (error) {
    // sin conexion, se sigue pudiendo diligenciar de forma personalizada
  }

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
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  // Si el paciente YA tiene un programa asignado, no se deja
  // volver a asignar/editar desde la app -- cualquier cambio
  // se hace desde la web, para mantener el control de quién
  // modifica el programa y cuándo.
  let programaExistente = null;
  try {
    programaExistente = await apiGet(`/api/movil/paciente/${visita.paciente_id}/programa-atencion`);
  } catch (error) {
    programaExistente = null;
  }

  if (programaExistente) {
    contenedor().innerHTML = `
      <div class="card">
        <h3>📑 Programa de Atención</h3>
        <small>${nombrePaciente}</small>
        <div class="alerta alerta-info" style="margin-top:10px;">
          Este paciente ya tiene un programa asignado. Para modificarlo, hágalo desde la página web.
        </div>
        <p style="margin-top:10px;"><strong>Programa:</strong> ${programaExistente.programa_nombre}</p>
        ${programaExistente.tipo ? `<p><strong>Tipo:</strong> ${programaExistente.tipo}${programaExistente.subtipo ? " - " + programaExistente.subtipo : ""}</p>` : ""}
        ${programaExistente.profesional ? `<p><strong>Asignado por:</strong> ${programaExistente.profesional}</p>` : ""}
        ${programaExistente.fecha_inicio ? `<p><strong>Fecha de inicio:</strong> ${programaExistente.fecha_inicio}</p>` : ""}
        ${programaExistente.motivo ? `<p><strong>Motivo:</strong> ${programaExistente.motivo}</p>` : ""}
      </div>
      <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
    `;
    return;
  }

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

async function renderProgramarMiAgenda() {
  titulo("Programar Mi Agenda");
  contenedor().innerHTML = `<p class="text-center">Cargando sesiones...</p>`;

  let sesiones = [];
  try {
    sesiones = await apiGet("/api/movil/mi-agenda-programable");
  } catch (error) {
    contenedor().innerHTML = `<div class="alerta alerta-danger">No se pudo cargar. Necesita conexión para esta pantalla.</div>
      <button class="btn btn-secondary btn-block" onclick="renderPerfil()">← Volver</button>`;
    return;
  }

  let html = `<div class="card"><h3>📅 Programar Mi Agenda</h3><small>Sesiones pendientes o ya programadas de sus pacientes asignados.</small></div>`;

  if (sesiones.length === 0) {
    html += `<div class="alerta alerta-info">No tiene sesiones pendientes ni programadas por ahora.</div>`;
  } else {
    sesiones.forEach((s) => {
      const nombrePaciente = [s.primer_nombre, s.primer_apellido].filter(Boolean).join(" ");
      const yaProgramada = !!s.programacion_id;
      html += `
        <div class="card" style="${yaProgramada ? 'border-left:4px solid #0d6efd;' : 'border-left:4px solid #dd5600;'}">
          <strong>${nombrePaciente}</strong> — ${s.tipo_servicio}${s.subtipo ? " - " + s.subtipo : ""}<br>
          <small>${s.direccion || ""}, ${s.municipio || ""}</small><br>
          ${yaProgramada
            ? `<span class="badge" style="background:#0d6efd; color:white;">Programada: ${s.fecha_programada} ${s.hora_programada || ""}</span>`
            : `<span class="badge" style="background:#dd5600; color:white;">Pendiente de programar</span>`}

          <div style="display:flex; gap:4px; margin-top:8px;">
            <input type="date" class="campo-fecha-pa" data-planilla="${s.planilla_id}" style="flex:1;" value="${yaProgramada ? s.fecha_programada : ''}">
            <input type="time" class="campo-hora-pa" data-planilla="${s.planilla_id}" style="flex:1;" value="${yaProgramada ? s.hora_programada : ''}">
          </div>
          <button type="button" class="btn ${yaProgramada ? 'btn-secondary' : 'btn-success'} w-100 btn-guardar-pa" style="margin-top:6px;"
                  data-planilla="${s.planilla_id}" data-paciente="${s.paciente_id}">
            ${yaProgramada ? "🔄 Reprogramar" : "✅ Programar"}
          </button>
        </div>
      `;
    });
  }

  html += `<button class="btn btn-secondary btn-block" onclick="renderPerfil()">← Volver</button>`;
  contenedor().innerHTML = html;

  document.querySelectorAll(".btn-guardar-pa").forEach((boton) => {
    boton.addEventListener("click", async () => {
      const planillaId = boton.dataset.planilla;
      const pacienteId = boton.dataset.paciente;
      const fecha = document.querySelector(`.campo-fecha-pa[data-planilla="${planillaId}"]`).value;
      const hora = document.querySelector(`.campo-hora-pa[data-planilla="${planillaId}"]`).value;

      if (!fecha) {
        alert("Debe indicar la fecha.");
        return;
      }

      await encolarAccion("programar_visita_movil", {
        planilla_id: planillaId,
        paciente_id: pacienteId,
        fecha: fecha,
        hora_inicio: hora || "08:00",
        hora_fin: hora ? sumarUnaHora(hora) : "09:00",
        profesional_id: perfil.profesional_id,
      });

      alert("Guardado. Se sincronizará cuando haya conexión.");
      renderProgramarMiAgenda();
    });
  });
}

function sumarUnaHora(horaTexto) {
  const [horas, minutos] = horaTexto.split(":").map(Number);
  const total = (horas + 1) % 24;
  return `${String(total).padStart(2, "0")}:${String(minutos).padStart(2, "0")}`;
}

async function renderAlergias(visita) {
  titulo("Alergias");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  let datos = { alergias: [], tipos: [], severidades: [] };
  try { datos = await apiGet(`/api/movil/paciente/${visita.paciente_id}/alergias`); } catch (e) {}

  const nombresTipo = { MED: "Medicamentos", ALI: "Alimentos", LAT: "Látex", CON: "Contraste", PIC: "Picaduras", AMB: "Ambientales", OTR: "Otros" };

  let html = `<div class="card"><h3>⚠️ Alergias</h3><small>${nombrePaciente}</small></div>`;

  if (datos.alergias.length === 0) {
    html += `<div class="alerta alerta-info">Sin alergias registradas.</div>`;
  } else {
    datos.alergias.forEach((a) => {
      html += `<div class="card" style="border-left:4px solid #c71c22;"><strong>${nombresTipo[a.tipo] || a.tipo}: ${a.alergeno}</strong><br>
        <small>Severidad: ${a.severidad} · ${a.estado}</small>
        ${a.reaccion ? `<p style="margin-top:6px; color:#c71c22; font-weight:bold;">⚠️ Le puede producir: ${a.reaccion}</p>` : `<p style="margin-top:6px; color:#888;">No se registró qué le produce.</p>`}</div>`;
    });
  }

  html += `
    <div class="card">
      <h5>Registrar nueva alergia</h5>
      <div class="form-group"><label>Tipo</label>
        <select id="al-tipo">${datos.tipos.map(t => `<option value="${t}">${nombresTipo[t] || t}</option>`).join("")}</select>
      </div>
      <div class="form-group"><label>Alérgeno</label><input type="text" id="al-alergeno" placeholder="Ej: Penicilina"></div>
      <div class="form-group"><label>Severidad</label>
        <select id="al-severidad">${datos.severidades.map(s => `<option value="${s}">${s}</option>`).join("")}</select>
      </div>
      <div class="form-group"><label>¿Qué le puede producir? (reacción)</label><textarea id="al-reaccion" rows="2" placeholder="Ej: Urticaria, dificultad para respirar, hinchazón..."></textarea></div>
      <button class="btn btn-success w-100" id="btn-guardar-alergia">Guardar</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  contenedor().innerHTML = html;

  document.getElementById("btn-guardar-alergia").addEventListener("click", async () => {
    const alergeno = document.getElementById("al-alergeno").value.trim();
    if (!alergeno) { alert("Debe indicar el alérgeno."); return; }
    await encolarAccion("crear_alergia", {
      paciente_id: visita.paciente_id, tipo: document.getElementById("al-tipo").value,
      alergeno: alergeno, severidad: document.getElementById("al-severidad").value,
      reaccion: document.getElementById("al-reaccion").value, estado: "Activa",
    });
    alert("Alergia guardada. Se sincronizará cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

async function renderAntecedentes(visita) {
  titulo("Antecedentes");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  contenedor().innerHTML = `<p class="text-center">Cargando...</p>`;

  let datos = { antecedentes: [], tipos: [] };
  try { datos = await apiGet(`/api/movil/paciente/${visita.paciente_id}/antecedentes`); } catch (e) {}

  const nombresTipo = { AP: "Personales", AF: "Familiares", AQ: "Quirúrgicos", AH: "Hospitalizaciones", AL: "Alergias", HT: "Hábitos", GO: "Gineco-Obstétricos", OC: "Ocupacionales", FA: "Farmacológicos" };

  let html = `<div class="card"><h3>📖 Antecedentes</h3><small>${nombrePaciente}</small></div>`;

  if (datos.antecedentes.length === 0) {
    html += `<div class="alerta alerta-info">Sin antecedentes registrados.</div>`;
  } else {
    datos.antecedentes.forEach((a) => {
      html += `<div class="card"><strong>${nombresTipo[a.tipo] || a.tipo}</strong><p style="margin-top:6px;">${a.descripcion}</p></div>`;
    });
  }

  html += `
    <div class="card">
      <h5>Registrar nuevo antecedente</h5>
      <div class="form-group"><label>Tipo</label>
        <select id="an-tipo">${datos.tipos.map(t => `<option value="${t}">${nombresTipo[t] || t}</option>`).join("")}</select>
      </div>
      <div class="form-group"><label>Descripción</label><textarea id="an-descripcion" rows="3"></textarea></div>
      <button class="btn btn-success w-100" id="btn-guardar-antecedente">Guardar</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  contenedor().innerHTML = html;

  document.getElementById("btn-guardar-antecedente").addEventListener("click", async () => {
    const descripcion = document.getElementById("an-descripcion").value.trim();
    if (!descripcion) { alert("Debe indicar la descripción."); return; }
    await encolarAccion("crear_antecedente", {
      paciente_id: visita.paciente_id, tipo: document.getElementById("an-tipo").value,
      descripcion: descripcion,
    });
    alert("Antecedente guardado. Se sincronizará cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

function renderExamenFisico(visita) {
  titulo("Examen Físico");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  const sistemas = ["cabeza", "cara", "boca", "cuello", "torax", "abdomen", "extremidades", "vascular", "neurologico", "columna"];

  contenedor().innerHTML = `
    <div class="card">
      <h3>🩻 Examen Físico por Sistemas</h3>
      <small>${nombrePaciente}</small>
      <div class="form-group" style="margin-top:10px;"><label>Tipo de profesional</label><input type="text" id="ef-tipo-profesional" placeholder="Ej: Medicina General, Enfermería"></div>
      ${sistemas.map(s => `<div class="form-group"><label style="text-transform:capitalize;">${s}</label><textarea id="ef-${s}" rows="2" placeholder="Ej: NORMAL"></textarea></div>`).join("")}
      <button class="btn btn-success w-100" id="btn-guardar-examen-fisico">Guardar examen físico</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  document.getElementById("btn-guardar-examen-fisico").addEventListener("click", async () => {
    const valores = {};
    sistemas.forEach((s) => { valores[s] = document.getElementById(`ef-${s}`).value; });

    await encolarAccion("crear_examen_fisico", {
      paciente_id: visita.paciente_id, programacion_id: visita.id, profesional_id: perfil.profesional_id,
      tipo_profesional: document.getElementById("ef-tipo-profesional").value, valores: valores,
    });

    alert("Examen físico guardado. Se sincronizará cuando haya conexión.");
    irA("detalle_visita", visita.id);
  });
}

async function renderRecomendaciones(visita) {
  titulo("Recomendaciones");
  const nombrePaciente = [visita.primer_nombre, visita.primer_apellido].filter(Boolean).join(" ");
  const tiposConsulta = ["PRIMERA VEZ", "CONTROL", "CONFIRMADO NUEVO", "CONFIRMADO REPETIDO", "PRESUNTIVO"];

  let diagnosticosPaciente = [];
  try {
    diagnosticosPaciente = await apiGet(`/api/movil/paciente/${visita.paciente_id}/diagnosticos`);
  } catch (error) {
    diagnosticosPaciente = [];
  }

  let recomendacionesExistentes = [];
  try {
    recomendacionesExistentes = await apiGet(`/api/movil/paciente/${visita.paciente_id}/recomendaciones`);
  } catch (error) {
    recomendacionesExistentes = [];
  }

  let htmlExistentes = `<div class="card"><h3>📝 Recomendaciones / Plan Médico</h3><small>${nombrePaciente}</small></div>`;

  if (recomendacionesExistentes.length === 0) {
    htmlExistentes += `<div class="alerta alerta-info">Este paciente todavía no tiene recomendaciones/plan médico registrado.</div>`;
  } else {
    htmlExistentes += `<h5 style="margin-top:10px;">Ya registradas</h5>`;
    recomendacionesExistentes.forEach((r) => {
      htmlExistentes += `
        <div class="card">
          <strong>${r.diagnostico_ppal_nombre || ""} ${r.diagnostico_ppal_codigo ? "(" + r.diagnostico_ppal_codigo + ")" : ""}</strong><br>
          <small>${r.profesional || ""} · ${r.tipo_consulta || ""} · ${r.fecha_creacion || ""}</small>
          ${r.diagnostico_rel1_nombre ? `<p style="margin-top:4px; margin-bottom:0;">Relacionado 1: ${r.diagnostico_rel1_nombre}</p>` : ""}
          ${r.diagnostico_rel2_nombre ? `<p style="margin-bottom:0;">Relacionado 2: ${r.diagnostico_rel2_nombre}</p>` : ""}
          ${r.diagnostico_rel3_nombre ? `<p style="margin-bottom:0;">Relacionado 3: ${r.diagnostico_rel3_nombre}</p>` : ""}
          <div style="margin-top:6px;">
            ${r.incapacidad ? `<span class="badge" style="background:#dd5600;color:white;">Incapacidad</span>` : ""}
            ${r.nota_aclaratoria ? `<span class="badge" style="background:#0d6efd;color:white;">Nota aclaratoria</span>` : ""}
            ${r.orden_medicamentos ? `<span class="badge" style="background:#0fb9ae;color:white;">Orden medicamentos</span>` : ""}
            ${r.orden_procedimientos ? `<span class="badge" style="background:#6c757d;color:white;">Orden procedimientos</span>` : ""}
          </div>
          ${r.recomendaciones_texto ? `<p style="margin-top:6px; margin-bottom:0;">${r.recomendaciones_texto}</p>` : ""}
        </div>
      `;
    });
  }

  contenedor().innerHTML = htmlExistentes + `<h5 style="margin-top:16px;">Agregar nueva</h5>`;

  const contenedorFormulario = document.createElement("div");
  contenedor().appendChild(contenedorFormulario);
  contenedorFormulario.innerHTML = `
    <div class="card">
      <label style="font-weight:bold; margin-top:10px; display:block;">Diagnóstico principal</label>
      <select id="reco-ppal-select">
        <option value="">-- Seleccione --</option>
        ${diagnosticosPaciente.map((d) => `<option value="${d.codigo}" data-nombre="${d.nombre}">${d.codigo} - ${d.nombre}</option>`).join("")}
        <option value="NA" data-nombre="No aplica">No aplica</option>
        <option value="__buscar__">Otro (buscar en el catálogo CIE-10)...</option>
      </select>
      <div id="reco-buscar-ppal-contenedor" style="display:none; margin-top:6px;">
        <input type="text" id="reco-buscar-ppal" placeholder="Buscar por código o nombre (CIE-10)...">
        <div id="reco-resultados-ppal" style="max-height:150px; overflow-y:auto;"></div>
      </div>
      <input type="hidden" id="reco-ppal-codigo"><input type="hidden" id="reco-ppal-nombre">

      ${[1, 2, 3].map(n => `
      <label style="font-weight:bold; margin-top:10px; display:block;">Diagnóstico relacionado ${n} (opcional)</label>
      <input type="text" id="reco-buscar-rel${n}" placeholder="Buscar por código o nombre (CIE-10)...">
      <div id="reco-resultados-rel${n}" style="max-height:150px; overflow-y:auto;"></div>
      <input type="hidden" id="reco-rel${n}-codigo"><input type="hidden" id="reco-rel${n}-nombre">
      `).join("")}

      <div class="form-group"><label>Tipo de consulta</label>
        <select id="reco-tipo-consulta">${tiposConsulta.map(t => `<option value="${t}">${t}</option>`).join("")}</select>
      </div>

      <label><input type="checkbox" id="reco-incapacidad"> Incapacidad</label><br>
      <label><input type="checkbox" id="reco-nota-aclaratoria"> Nota aclaratoria</label><br>
      <label><input type="checkbox" id="reco-orden-medicamentos"> Orden de medicamentos</label><br>
      <label><input type="checkbox" id="reco-orden-procedimientos"> Orden de procedimientos</label>

      <div class="form-group" style="margin-top:10px;"><label>Recomendaciones / plan</label><textarea id="reco-texto" rows="3"></textarea></div>
      <button class="btn btn-success w-100" id="btn-guardar-recomendacion">Guardar</button>
    </div>
    <button class="btn btn-secondary btn-block" onclick="irA('detalle_visita', ${visita.id})">← Volver</button>
  `;

  function habilitarBusquedaCie10(sufijo) {
    const campo = document.getElementById(`reco-buscar-${sufijo}`);
    const resultados = document.getElementById(`reco-resultados-${sufijo}`);
    const campoCodigo = document.getElementById(`reco-${sufijo}-codigo`);
    const campoNombre = document.getElementById(`reco-${sufijo}-nombre`);

    let temporizador;
    campo.addEventListener("input", () => {
      clearTimeout(temporizador);
      campoCodigo.value = ""; campoNombre.value = "";
      const texto = campo.value.trim();
      if (texto.length < 2) { resultados.innerHTML = ""; return; }
      temporizador = setTimeout(async () => {
        const resp = await fetch(`/api/cie10?buscar=${encodeURIComponent(texto)}`);
        const datos = await resp.json();
        resultados.innerHTML = datos.slice(0, 10).map(d =>
          `<div class="card" style="padding:6px; margin:4px 0; cursor:pointer;" data-codigo="${d.codigo}" data-descripcion="${d.descripcion}">${d.codigo} - ${d.descripcion}</div>`
        ).join("");
        resultados.querySelectorAll("[data-codigo]").forEach((el) => {
          el.addEventListener("click", () => {
            campo.value = `${el.dataset.codigo} - ${el.dataset.descripcion}`;
            campoCodigo.value = el.dataset.codigo;
            campoNombre.value = el.dataset.descripcion;
            resultados.innerHTML = "";
          });
        });
      }, 300);
    });
  }

  ["ppal", "rel1", "rel2", "rel3"].forEach(habilitarBusquedaCie10);

  document.getElementById("reco-ppal-select").addEventListener("change", (evento) => {
    const opcion = evento.target.selectedOptions[0];
    const contenedorBusqueda = document.getElementById("reco-buscar-ppal-contenedor");

    if (evento.target.value === "__buscar__") {
      contenedorBusqueda.style.display = "block";
      document.getElementById("reco-ppal-codigo").value = "";
      document.getElementById("reco-ppal-nombre").value = "";
    } else {
      contenedorBusqueda.style.display = "none";
      document.getElementById("reco-ppal-codigo").value = evento.target.value;
      document.getElementById("reco-ppal-nombre").value = opcion ? opcion.dataset.nombre || "" : "";
    }
  });

  document.getElementById("btn-guardar-recomendacion").addEventListener("click", async () => {
    const codigoPpal = document.getElementById("reco-ppal-codigo").value;
    if (!codigoPpal) { alert("Debe seleccionar el diagnóstico principal de la lista de resultados."); return; }

    await encolarAccion("crear_recomendacion", {
      paciente_id: visita.paciente_id, programacion_id: visita.id, profesional_id: perfil.profesional_id,
      datos: {
        diagnostico_ppal_codigo: codigoPpal, diagnostico_ppal_nombre: document.getElementById("reco-ppal-nombre").value,
        diagnostico_rel1_codigo: document.getElementById("reco-rel1-codigo").value, diagnostico_rel1_nombre: document.getElementById("reco-rel1-nombre").value,
        diagnostico_rel2_codigo: document.getElementById("reco-rel2-codigo").value, diagnostico_rel2_nombre: document.getElementById("reco-rel2-nombre").value,
        diagnostico_rel3_codigo: document.getElementById("reco-rel3-codigo").value, diagnostico_rel3_nombre: document.getElementById("reco-rel3-nombre").value,
        tipo_consulta: document.getElementById("reco-tipo-consulta").value,
        incapacidad: document.getElementById("reco-incapacidad").checked,
        nota_aclaratoria: document.getElementById("reco-nota-aclaratoria").checked,
        orden_medicamentos: document.getElementById("reco-orden-medicamentos").checked,
        orden_procedimientos: document.getElementById("reco-orden-procedimientos").checked,
        recomendaciones_texto: document.getElementById("reco-texto").value,
      },
    });

    alert("Recomendación guardada. Se sincronizará cuando haya conexión.");
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

// Solo los roles que en la web tienen permiso de "ordenes"
// (médico y profesionales de terapias) pueden generar Órdenes
// Médicas desde la app -- enfermería y cuidadores no, para que
// sea consistente con lo que ya se restringe en la web.
function esPerfilConOrdenes() {
  const rol = (perfil && perfil.rol || "").toLowerCase();
  const rolesConOrdenes = ["médico", "medico", "director médico", "fisioterapeuta",
    "terapeuta respiratorio", "psicólogo", "psicologo", "salud ocupacional", "terapeuta", "nutricionista",
    "administrador", "coordinador"];
  return rolesConOrdenes.some((r) => rol.includes(r));
}

// Solo los roles que en la web tienen permiso de "medicamentos"
// (médico, enfermería, coordinación) pueden registrar
// medicamentos administrados desde la app.
// Solo los profesionales de terapias (fisioterapia, terapia
// respiratoria, psicología, salud ocupacional, terapeuta,
// nutrición) pueden organizar su propia agenda desde la app --
// los demás roles (médico, enfermería, cuidador, coordinación)
// dependen de que se la programen desde la oficina.
function esPerfilTerapeuta() {
  const rol = (perfil && perfil.rol || "").toLowerCase();
  const rolesTerapeutas = ["fisioterapeuta", "terapeuta respiratorio", "psicólogo", "psicologo",
    "salud ocupacional", "terapeuta", "nutricionista"];
  return rolesTerapeutas.some((r) => rol.includes(r));
}

function esPerfilConMedicamentos() {
  const rol = (perfil && perfil.rol || "").toLowerCase();
  const rolesConMedicamentos = ["médico", "medico", "director médico", "enfermer", "coordinador", "administrador"];
  return rolesConMedicamentos.some((r) => rol.includes(r));
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
          <button class="btn btn-secondary btn-block mt-1" onclick="abrirReporteEnApp('/historia-clinica/informe/${i.id}/imprimir')">
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

// Dibuja, sobre la foto tomada, la latitud/longitud y la
// fecha/hora exacta en que se tomó -- para que la ubicación
// quede como prueba VISIBLE directamente en la imagen, y no
// solo como un dato aparte en la base de datos.
function agregarMarcaDeAguaUbicacion(fotoBase64, lat, lon) {
  return new Promise((resolve) => {
    const imagen = new Image();
    imagen.onload = () => {
      const lienzo = document.createElement("canvas");
      lienzo.width = imagen.width;
      lienzo.height = imagen.height;
      const contexto = lienzo.getContext("2d");
      contexto.drawImage(imagen, 0, 0);

      const texto1 = `📍 Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`;
      const texto2 = new Date().toLocaleString("es-CO");
      const tamanoFuente = Math.max(14, Math.round(imagen.width / 40));
      const alturaFranja = tamanoFuente * 2 + 24;

      contexto.fillStyle = "rgba(0, 0, 0, 0.55)";
      contexto.fillRect(0, imagen.height - alturaFranja, imagen.width, alturaFranja);

      contexto.fillStyle = "#ffffff";
      contexto.font = `bold ${tamanoFuente}px Arial`;
      contexto.textBaseline = "top";
      contexto.fillText(texto1, 12, imagen.height - alturaFranja + 8);
      contexto.font = `${tamanoFuente - 2}px Arial`;
      contexto.fillText(texto2, 12, imagen.height - alturaFranja + tamanoFuente + 14);

      resolve(lienzo.toDataURL("image/jpeg", 0.85));
    };
    imagen.onerror = () => resolve(fotoBase64); // si algo falla, se manda la foto original sin marca
    imagen.src = fotoBase64;
  });
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
      <p class="text-muted small">Ubique su rostro dentro del círculo y tome la foto, para corroborar que usted se encuentra en el lugar (junto con la ubicación GPS).</p>

      <div id="camara-ingreso-contenedor" style="position:relative; max-width:100%; margin-bottom:10px;">
        <video id="video-camara-ingreso" autoplay playsinline style="width:100%; border-radius:8px; background:#000;"></video>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:62%; aspect-ratio:1/1.25; border:4px solid #0fb9ae; border-radius:50%; pointer-events:none; box-shadow:0 0 0 2000px rgba(0,0,0,0.35);"></div>
      </div>
      <canvas id="canvas-captura-ingreso" style="display:none;"></canvas>

      <button class="btn btn-primary w-100" id="btn-tomar-foto-ingreso">📸 Tomar foto</button>

      <img id="foto-ingreso-preview" style="max-width:100%; max-height:200px; display:none;" class="mb-2 mt-2">
      <div id="foto-ingreso-estado" class="small text-muted mb-2"></div>
      <button class="btn btn-primary w-100" id="btn-confirmar-foto-ingreso" style="display:none;">✔ Confirmar</button>
      <button class="btn btn-secondary w-100 mt-2" id="btn-repetir-foto-ingreso" style="display:none;">↺ Repetir foto</button>
      <button class="btn btn-secondary w-100 mt-2" onclick="detenerCamaraIngreso(); irA('detalle_visita', ${visita.id})">Cancelar</button>
    </div>`;

  let fotoCapturada = null;
  let flujoCamaraIngreso = null;

  async function iniciarCamaraIngreso() {
    try {
      flujoCamaraIngreso = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
      document.getElementById("video-camara-ingreso").srcObject = flujoCamaraIngreso;
    } catch (error) {
      document.getElementById("foto-ingreso-estado").innerHTML =
        `<span style="color:#c71c22;">No se pudo acceder a la cámara: ${error.message}</span>`;
    }
  }

  window.detenerCamaraIngreso = () => {
    if (flujoCamaraIngreso) {
      flujoCamaraIngreso.getTracks().forEach((pista) => pista.stop());
      flujoCamaraIngreso = null;
    }
  };

  iniciarCamaraIngreso();

  document.getElementById("btn-tomar-foto-ingreso").addEventListener("click", () => {
    const video = document.getElementById("video-camara-ingreso");
    const lienzo = document.getElementById("canvas-captura-ingreso");
    lienzo.width = video.videoWidth;
    lienzo.height = video.videoHeight;
    lienzo.getContext("2d").drawImage(video, 0, 0);
    fotoCapturada = lienzo.toDataURL("image/jpeg", 0.9);

    const vista = document.getElementById("foto-ingreso-preview");
    vista.src = fotoCapturada;
    vista.style.display = "block";

    detenerCamaraIngreso();
    document.getElementById("camara-ingreso-contenedor").style.display = "none";
    document.getElementById("btn-tomar-foto-ingreso").style.display = "none";
    document.getElementById("btn-confirmar-foto-ingreso").style.display = "block";
    document.getElementById("btn-repetir-foto-ingreso").style.display = "block";
  });

  document.getElementById("btn-repetir-foto-ingreso").addEventListener("click", () => {
    fotoCapturada = null;
    document.getElementById("foto-ingreso-preview").style.display = "none";
    document.getElementById("camara-ingreso-contenedor").style.display = "block";
    document.getElementById("btn-tomar-foto-ingreso").style.display = "block";
    document.getElementById("btn-confirmar-foto-ingreso").style.display = "none";
    document.getElementById("btn-repetir-foto-ingreso").style.display = "none";
    iniciarCamaraIngreso();
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

    document.getElementById("foto-ingreso-estado").textContent = "Verificando su identidad...";

    // Verificación facial INMEDIATA: si hay conexión en este
    // momento, se valida el rostro contra la foto de
    // enrolamiento ANTES de dejar avanzar -- si no coincide,
    // aquí mismo se detiene, no se llega a registrar nada.
    // Si NO hay conexión justo ahora, se sigue el camino de
    // siempre (se encola, y se valida contra la misma foto de
    // enrolamiento del servidor en cuanto haya señal).
    try {
      const respuestaVerificacion = await fetch("/api/movil/verificar-rostro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ visita_id: visita.id, foto_base64: fotoCapturada }),
      });

      if (respuestaVerificacion.ok) {
        const resultadoVerificacion = await respuestaVerificacion.json();
        if (!resultadoVerificacion.verificado) {
          document.getElementById("foto-ingreso-estado").innerHTML =
            `<span style="color:#c71c22; font-weight:bold;">
              ⚠ No se pudo ${accion === "ingreso" ? "registrar el ingreso" : "finalizar la visita"}: ${resultadoVerificacion.motivo}
            </span>`;
          return; // se detiene aquí -- no se registra nada
        }
      }
      // Si respuestaVerificacion no fue "ok" por algún otro motivo del servidor,
      // se sigue adelante y quedará pendiente de verificar cuando sincronice.
    } catch (error) {
      // Sin conexión en este momento -- se sigue el camino offline de siempre.
    }

    document.getElementById("foto-ingreso-estado").textContent = "Marcando la ubicación sobre la foto...";
    const fotoConMarcaDeAgua = await agregarMarcaDeAguaUbicacion(fotoCapturada, ubicacion.lat, ubicacion.lon);

    await encolarAccion(accion, {
      visita_id: visita.id, lat: ubicacion.lat, lon: ubicacion.lon,
      foto_base64: fotoConMarcaDeAgua, marca_tiempo_offline: new Date().toISOString(),
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

  document.getElementById("btn-sync-ahora").addEventListener("click", async (evento) => {
    const boton = evento.target;
    const textoOriginal = boton.textContent;
    boton.disabled = true;
    boton.textContent = "⏳ Sincronizando...";

    const resultado = await intentarSincronizar(true); // true = intento manual, no espera a navigator.onLine

    boton.disabled = false;
    boton.textContent = textoOriginal;

    if (resultado.motivo === "ya_en_progreso") {
      alert("Ya hay una sincronización en curso, espere un momento y vuelva a intentar.");
    } else if (resultado.sinPendientes) {
      alert("No había nada pendiente por enviar.");
    } else if (resultado.ok) {
      alert(`✔ Se enviaron ${resultado.enviados} de ${resultado.total} elemento(s) pendientes.`);
    } else {
      alert("⚠ " + (resultado.mensaje || "No se pudo sincronizar."));
    }

    renderPendientes();
  });

  const lista = document.getElementById("lista-pendientes");

  if (pendientes.length === 0) {
    lista.innerHTML = `<div class="alerta alerta-success">Todo está sincronizado. No hay nada pendiente.</div>`;
    return;
  }

  lista.innerHTML = pendientes
    .map(
      (a) => {
        const minutosEsperando = Math.floor((Date.now() - new Date(a.creado_en).getTime()) / 60000);
        const llevaRato = minutosEsperando >= 5;
        return `
      <div class="card" style="${llevaRato ? 'border-left:4px solid #dd9d00;' : ''}">
        <strong>${etiquetas[a.tipo] || a.tipo}</strong><br>
        <small>Registrado: ${new Date(a.creado_en).toLocaleString()} (${minutosEsperando < 1 ? "hace un momento" : "hace " + minutosEsperando + " min"})</small>
        ${llevaRato ? `<br><small style="color:#dd9d00;">⚠ Lleva un rato esperando — revise su conexión y use "Sincronizar ahora"</small>` : ""}
      </div>`;
      }
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
    ${esPerfilTerapeuta() ? `<button class="btn btn-primary btn-block" id="btn-programar-mi-agenda">📅 Programar Mi Agenda</button>` : ""}
    <button class="btn btn-danger btn-block" id="btn-logout">Cerrar sesión</button>
  `;

  const botonProgramarAgenda = document.getElementById("btn-programar-mi-agenda");
  if (botonProgramarAgenda) botonProgramarAgenda.addEventListener("click", () => renderProgramarMiAgenda());

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
    // Cada vez que se abre la app (no solo al escribir usuario y
    // contraseña), se revisa si el profesional YA tiene foto de
    // enrolamiento -- si por cualquier motivo no la tiene (no
    // se alcanzó a tomar antes, se reinició la base de datos,
    // un administrador se la borró, etc.), se le pide tomarla
    // ANTES de dejarlo continuar. Si no hay conexión para
    // consultarlo, se deja pasar normal (no se bloquea el
    // trabajo en campo por no poder verificarlo en ese momento).
    let debePedirEnrolamiento = false;
    try {
      const perfilActualizado = await apiGet("/api/movil/perfil");
      debePedirEnrolamiento = perfilActualizado.tiene_foto_enrolamiento === false;
    } catch (error) {
      debePedirEnrolamiento = false;
    }

    if (debePedirEnrolamiento) {
      renderEnrolamientoFacial();
    } else {
      mostrarNav(true);
      irA("agenda");
      reanudarMonitoreoSiHayTurnoAbierto();
      iniciarRecordatoriosDeTurno();
    }
  } else {
    renderLogin();
  }

  intentarSincronizar();
}

iniciar();
