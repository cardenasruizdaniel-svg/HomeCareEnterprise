// ==========================================================
// HomeCare Enterprise - App Gerencial
// Dashboard ejecutivo de solo lectura, para dirección y
// gerencia -- separada de la app de campo (que usan los
// profesionales para sus visitas).
// ==========================================================

let perfil = null;
try {
  const guardado = localStorage.getItem("gerencial_perfil");
  if (guardado) perfil = JSON.parse(guardado);
} catch (error) {
  perfil = null;
}

function contenedor() {
  return document.getElementById("contenedor");
}

function titulo(texto, subtitulo = "") {
  document.getElementById("titulo-pantalla").textContent = texto;
  document.getElementById("subtitulo-pantalla").textContent = subtitulo;
}

function actualizarEstadoConexion() {
  const el = document.getElementById("estado-conexion");
  if (!el) return;
  if (!navigator.onLine) {
    el.textContent = "Sin conexión";
    el.className = "estado-conexion offline";
  } else {
    el.textContent = "En línea";
    el.className = "estado-conexion";
  }
}
window.addEventListener("online", actualizarEstadoConexion);
window.addEventListener("offline", actualizarEstadoConexion);

async function apiGet(ruta) {
  const respuesta = await fetch(ruta, { credentials: "same-origin" });
  if (respuesta.status === 401 || respuesta.status === 403) {
    const datosError = await respuesta.json().catch(() => ({}));
    throw { esAuth: true, mensaje: datosError.detail || "No tiene acceso." };
  }
  if (!respuesta.ok) throw new Error("Error al consultar el servidor.");
  return respuesta.json();
}

function formatoMoneda(valor) {
  return "$ " + Math.round(valor || 0).toLocaleString("es-CO");
}

// ==========================================================
// LOGIN
// ==========================================================

function renderLogin(mensajeError = "") {
  document.body.classList.remove("con-nav");
  const nav = document.getElementById("bottom-nav-fijo");
  if (nav) nav.remove();

  titulo("App Gerencial");
  contenedor().innerHTML = `
    <div style="text-align:center; padding:30px 10px 10px;">
      <img src="/static/img/logo_homecare.png" alt="HomeCare del Quindío" style="width:100px; height:100px; object-fit:contain; border-radius:20px; background:white; box-shadow:0 4px 16px rgba(0,0,0,0.12); padding:10px;">
      <h2 style="margin:16px 0 2px; color:var(--hc-navy);">
        <span style="color:var(--hc-teal-oscuro);">Home</span><span style="color:var(--hc-rosa);">Care</span>
      </h2>
      <p style="color:#6c757d; margin:0 0 6px; font-size:13px;">del Quindío I.P.S.</p>
      <p style="color:var(--hc-teal-oscuro); margin:0 0 20px; font-size:13px; font-weight:600;">App Gerencial — Dashboard Ejecutivo</p>
    </div>
    <div class="card">
      <h3>Iniciar sesión</h3>
      <p style="font-size:12px; color:#6c757d; margin-top:-4px;">Exclusivo para Administrador, Director Médico y Coordinador.</p>
      ${mensajeError ? `<div class="alerta-error">${mensajeError}</div>` : ""}
      <div class="form-group">
        <label>Usuario</label>
        <input type="text" id="login-usuario" autocomplete="username">
      </div>
      <div class="form-group">
        <label>Contraseña</label>
        <input type="password" id="login-password" autocomplete="current-password">
      </div>
      <button class="btn" id="btn-login">Ingresar</button>
    </div>`;

  document.getElementById("btn-login").addEventListener("click", async () => {
    const boton = document.getElementById("btn-login");
    boton.disabled = true;
    boton.textContent = "Ingresando...";

    try {
      const respuesta = await fetch("/api/gerencial/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          usuario: document.getElementById("login-usuario").value,
          password: document.getElementById("login-password").value,
        }),
      });

      const datos = await respuesta.json();

      if (!respuesta.ok) {
        renderLogin(datos.detail || "No se pudo iniciar sesión.");
        return;
      }

      perfil = datos.usuario;
      localStorage.setItem("gerencial_perfil", JSON.stringify(perfil));
      mostrarNav();
      renderDashboard();
    } catch (error) {
      renderLogin("No hay conexión. Intente de nuevo.");
    }
  });
}

// ==========================================================
// NAVEGACIÓN INFERIOR
// ==========================================================

function mostrarNav() {
  document.body.classList.add("con-nav");
  if (document.getElementById("bottom-nav-fijo")) return;

  const nav = document.createElement("div");
  nav.className = "bottom-nav";
  nav.id = "bottom-nav-fijo";
  nav.innerHTML = `
    <button data-vista="dashboard"><span class="icono">📊</span>Dashboard</button>
    <button data-vista="cartera"><span class="icono">💳</span>Cartera</button>
    <button data-vista="inventario"><span class="icono">📦</span>Inventario</button>
    <button data-vista="perfil"><span class="icono">👤</span>Perfil</button>
  `;
  document.body.appendChild(nav);

  nav.querySelectorAll("button").forEach((boton) => {
    boton.addEventListener("click", () => {
      nav.querySelectorAll("button").forEach((b) => b.classList.remove("activo"));
      boton.classList.add("activo");
      const vista = boton.dataset.vista;
      if (vista === "dashboard") renderDashboard();
      else if (vista === "cartera") renderCartera();
      else if (vista === "inventario") renderInventario();
      else if (vista === "perfil") renderPerfil();
    });
  });
}

function marcarNavActivo(vista) {
  const nav = document.getElementById("bottom-nav-fijo");
  if (!nav) return;
  nav.querySelectorAll("button").forEach((b) => b.classList.toggle("activo", b.dataset.vista === vista));
}

// ==========================================================
// DASHBOARD EJECUTIVO
// ==========================================================

let graficoProduccion = null;

async function renderDashboard() {
  marcarNavActivo("dashboard");
  titulo("Dashboard Ejecutivo", perfil ? `${perfil.nombre} · ${perfil.rol}` : "");
  contenedor().innerHTML = `<div class="spinner-centro">Cargando indicadores...</div>`;

  let datos;
  try {
    datos = await apiGet("/api/gerencial/dashboard");
  } catch (error) {
    if (error.esAuth) { cerrarSesionForzado(error.mensaje); return; }
    contenedor().innerHTML = `<div class="alerta-error">No se pudo cargar el dashboard. Verifique su conexión.</div>
      <button class="btn btn-secondary" onclick="renderDashboard()">Reintentar</button>`;
    return;
  }

  const g = datos.gerencial;
  const op = datos.operativo;

  const iconoTendencia = g.tendencia_facturacion.icono === "arrow-up" ? "▲" : g.tendencia_facturacion.icono === "arrow-down" ? "▼" : "—";
  const claseTendencia = g.tendencia_facturacion.color === "success" ? "tendencia-up" : g.tendencia_facturacion.color === "danger" ? "tendencia-down" : "";

  contenedor().innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card teal">
        <div class="kpi-label">💰 Facturado este mes</div>
        <div class="kpi-valor">${formatoMoneda(g.facturado_mes)}</div>
        <div class="kpi-detalle ${claseTendencia}">${iconoTendencia} ${g.tendencia_facturacion.valor}% vs mes anterior</div>
      </div>
      <div class="kpi-card rosa">
        <div class="kpi-label">📋 Cartera pendiente</div>
        <div class="kpi-valor">${formatoMoneda(g.cartera_pendiente)}</div>
        <div class="kpi-detalle">${g.facturas_pendientes} factura(s)</div>
      </div>
      <div class="kpi-card navy">
        <div class="kpi-label">📦 Valor inventario</div>
        <div class="kpi-valor">${formatoMoneda(g.valor_inventario)}</div>
        <div class="kpi-detalle">Compras del mes: ${formatoMoneda(g.compras_mes)}</div>
      </div>
      <div class="kpi-card light">
        <div class="kpi-label">✅ Cumplimiento agenda</div>
        <div class="kpi-valor">${g.porcentaje_cumplimiento}%</div>
        <div class="kpi-detalle">${g.visitas_completadas_mes} de ${g.visitas_mes} visita(s)</div>
      </div>
    </div>

    <div class="card mt-2" style="margin-top:12px;">
      <h3>👥 Operación general</h3>
      <div class="kpi-grid">
        <div class="kpi-card light"><div class="kpi-label">Pacientes activos</div><div class="kpi-valor">${g.pacientes_activos}</div></div>
        <div class="kpi-card light"><div class="kpi-label">Profesionales activos</div><div class="kpi-valor">${g.profesionales_activos}</div></div>
      </div>
    </div>

    ${(g.insumos_stock_bajo > 0 || g.lotes_vencidos > 0 || g.lotes_por_vencer > 0) ? `
    <div class="card">
      <h3>⚠ Alertas</h3>
      ${g.insumos_stock_bajo > 0 ? `<div class="alerta-item danger">📦 ${g.insumos_stock_bajo} insumo(s) con stock bajo</div>` : ""}
      ${g.lotes_vencidos > 0 ? `<div class="alerta-item danger">☠ ${g.lotes_vencidos} lote(s) vencido(s)</div>` : ""}
      ${g.lotes_por_vencer > 0 ? `<div class="alerta-item warning">⏰ ${g.lotes_por_vencer} lote(s) por vencer</div>` : ""}
    </div>` : ""}

    <div class="card">
      <h3>📈 Producción mensual</h3>
      <div class="grafico-contenedor"><canvas id="canvas-produccion"></canvas></div>
    </div>

    <div class="card">
      <h3>🗓 Programados hoy (${op.visitas_hoy_total})</h3>
      ${(!op.visitas_hoy || op.visitas_hoy.length === 0) ? `<p class="muted">Sin visitas programadas hoy.</p>` :
        op.visitas_hoy.map((v) => `
          <div class="lista-item">
            <strong>${v.hora_inicio || ""}</strong> — ${v.paciente || "Paciente sin nombre"}
            <span class="badge ${v.estado === 'Completada' ? 'badge-success' : v.estado === 'En Curso' ? 'badge-info' : 'badge-danger'}" style="float:right;">${v.estado || ""}</span>
            <br><span class="muted">${v.servicio || ""} · Con: ${v.profesional || "Sin asignar"}</span>
          </div>`).join("")}
    </div>

    <div class="card">
      <h3>🚶 En visita ahora (${op.en_visita_ahora.length})</h3>
      ${op.en_visita_ahora.length === 0 ? `<p class="muted">Nadie está en visita en este momento.</p>` :
        op.en_visita_ahora.map((v) => `
          <div class="lista-item">
            <strong>${v.paciente || "Paciente sin nombre"}</strong>
            <br><span class="muted">Con: ${v.profesional || "Sin asignar"} · Ingresó: ${v.hora_real_inicio || ""} · ${v.servicio || ""}</span>
          </div>`).join("")}
    </div>

    <div class="card">
      <h3>✅ Finalizaron hoy (${op.finalizaron_hoy.length})</h3>
      ${op.finalizaron_hoy.length === 0 ? `<p class="muted">Nadie ha finalizado visitas todavía hoy.</p>` :
        op.finalizaron_hoy.map((v) => `
          <div class="lista-item">
            <strong>${v.paciente || "Paciente sin nombre"}</strong>
            <br><span class="muted">Con: ${v.profesional || "Sin asignar"} · ${v.hora_real_inicio || ""} a ${v.hora_real_fin || ""}</span>
          </div>`).join("")}
    </div>

    ${op.total_servicios_sin_programar > 0 ? `
    <div class="card">
      <h3>🗓 Servicios sin programar (${op.total_servicios_sin_programar})</h3>
      ${op.servicios_sin_programar.map((s) => `
        <div class="lista-item">
          <strong>${s.paciente || "Paciente sin nombre"}</strong>
          <span class="badge badge-danger" style="float:right;">${s.pendientes}/${s.total_visitas}</span>
          <br><span class="muted">${s.tipo_servicio || ""}${s.subtipo ? " - " + s.subtipo : ""} · Desde ${s.fecha_inicio}</span>
        </div>`).join("")}
    </div>` : ""}
  `;

  const ctx = document.getElementById("canvas-produccion");
  if (ctx && datos.grafico_produccion) {
    if (graficoProduccion) graficoProduccion.destroy();
    graficoProduccion = new Chart(ctx, {
      type: "bar",
      data: {
        labels: datos.grafico_produccion.labels,
        datasets: [{ label: "Visitas", data: datos.grafico_produccion.values, backgroundColor: "#00c2b8" }],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
    });
  }
}

// ==========================================================
// CARTERA
// ==========================================================

async function renderCartera() {
  marcarNavActivo("cartera");
  titulo("Cartera Pendiente");
  contenedor().innerHTML = `<div class="spinner-centro">Cargando...</div>`;

  let filas;
  try {
    filas = await apiGet("/api/gerencial/cartera");
  } catch (error) {
    if (error.esAuth) { cerrarSesionForzado(error.mensaje); return; }
    contenedor().innerHTML = `<div class="alerta-error">No se pudo cargar la cartera.</div>`;
    return;
  }

  contenedor().innerHTML = `
    <div class="card">
      <h3>💳 Facturas pendientes de cobro</h3>
      ${filas.length === 0 ? `<p class="muted">No hay cartera pendiente. 🎉</p>` :
        filas.map((f) => `
          <div class="lista-item">
            <strong>${f.primer_nombre || ""} ${f.primer_apellido || ""}</strong>
            <span class="badge badge-danger" style="float:right;">${formatoMoneda(f.valor_total)}</span>
            <br><span class="muted">${f.prefijo || ""}${f.numero || ""} · ${(f.fecha_emision || "").slice(0,10)} · ${f.estado || ""}</span>
          </div>`).join("")}
    </div>`;
}

// ==========================================================
// INVENTARIO (resumen)
// ==========================================================

async function renderInventario() {
  marcarNavActivo("inventario");
  titulo("Inventario");
  contenedor().innerHTML = `<div class="spinner-centro">Cargando...</div>`;

  let datos;
  try {
    datos = await apiGet("/api/gerencial/inventario-resumen");
  } catch (error) {
    if (error.esAuth) { cerrarSesionForzado(error.mensaje); return; }
    contenedor().innerHTML = `<div class="alerta-error">No se pudo cargar el inventario.</div>`;
    return;
  }

  contenedor().innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card teal"><div class="kpi-label">Valor total</div><div class="kpi-valor">${formatoMoneda(datos.total_valorizado)}</div></div>
      <div class="kpi-card light"><div class="kpi-label">Insumos activos</div><div class="kpi-valor">${datos.total_insumos}</div></div>
    </div>
    <div class="card">
      <h3>⚠ Insumos con stock bajo (${datos.total_stock_bajo})</h3>
      ${datos.insumos_stock_bajo.length === 0 ? `<p class="muted">Todo el inventario está en niveles normales.</p>` :
        datos.insumos_stock_bajo.map((i) => `
          <div class="lista-item">
            <strong>${i.nombre}</strong>
            <span class="badge badge-danger" style="float:right;">${i.stock_actual} / mín. ${i.stock_minimo}</span>
          </div>`).join("")}
    </div>`;
}

// ==========================================================
// PERFIL
// ==========================================================

function renderPerfil() {
  marcarNavActivo("perfil");
  titulo("Mi Perfil");
  contenedor().innerHTML = `
    <div class="card">
      <h3>${perfil.nombre}</h3>
      <small>${perfil.rol} · ${perfil.usuario}</small>
    </div>
    <button class="btn btn-danger" id="btn-logout">Cerrar sesión</button>
  `;
  document.getElementById("btn-logout").addEventListener("click", async () => {
    await fetch("/api/gerencial/logout", { method: "POST", credentials: "same-origin" });
    localStorage.removeItem("gerencial_perfil");
    perfil = null;
    document.body.classList.remove("con-nav");
    const nav = document.getElementById("bottom-nav-fijo");
    if (nav) nav.remove();
    renderLogin();
  });
}

function cerrarSesionForzado(mensaje) {
  localStorage.removeItem("gerencial_perfil");
  perfil = null;
  document.body.classList.remove("con-nav");
  const nav = document.getElementById("bottom-nav-fijo");
  if (nav) nav.remove();
  renderLogin(mensaje);
}

// ==========================================================
// ARRANQUE
// ==========================================================

async function iniciar() {
  actualizarEstadoConexion();

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/gerencial/sw.js").catch(console.error);
  }

  if (perfil) {
    mostrarNav();
    renderDashboard();
  } else {
    renderLogin();
  }
}

iniciar();
