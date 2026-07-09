/*
==========================================================
HomeCare Enterprise
Sprint 3.3
Centro de Despacho Inteligente
==========================================================
*/

class DespachoUI {

    constructor() {

        this.baseURL = "/despacho";

        this.inicializar();

    }

    async inicializar() {

        await this.cargarDashboard();

        this.configurarEventos();

        this.actualizacionAutomatica();

    }

    configurarEventos() {

        const btnActualizar = document.getElementById("btnActualizar");

        if (btnActualizar) {

            btnActualizar.addEventListener("click", () => {

                this.cargarDashboard();

            });

        }

        const btnActualizarTablero = document.getElementById("btnActualizarTablero");

        if (btnActualizarTablero) {

            btnActualizarTablero.addEventListener("click", () => {

                this.cargarDashboard();

            });

        }

        const buscar = document.getElementById("buscarDespacho");

        if (buscar) {

            buscar.addEventListener("keyup", () => {

                this.filtrarTabla(buscar.value);

            });

        }

    }

    async cargarDashboard() {

        try {

            const response = await fetch(`${this.baseURL}/`);

            const data = await response.json();

            this.actualizarKPIs(data.indicadores || {});

            this.cargarTabla(data.pendientes || []);

            this.cargarCola(data.pendientes || []);

        }

        catch (error) {

            console.error(error);

        }

    }

    actualizarKPIs(datos) {

        this.setValor("kpiPendientes", datos.pendientes);

        this.setValor("kpiRuta", datos.en_ruta);

        this.setValor("kpiAtencion", datos.atendiendo);

        this.setValor("kpiFinalizadas", datos.finalizados);

        this.setValor("kpiProfesionales", datos.profesionales);

    }

    setValor(id, valor) {

        const control = document.getElementById(id);

        if (control) {

            control.innerText = valor ?? 0;

        }

    }

    cargarTabla(lista) {

        const tbody = document.getElementById("tablaDespacho") ||
                      document.getElementById("tablaOperativa") ||
                      document.getElementById("tablaProfesional");

        if (!tbody) return;

        tbody.innerHTML = "";

        lista.forEach(item => {

            tbody.innerHTML += `

                <tr>

                    <td>${item.hora_inicio ?? ""}</td>

                    <td>${item.paciente ?? item.paciente_id}</td>

                    <td>${item.profesional ?? item.profesional_id}</td>

                    <td>${item.municipio ?? ""}</td>

                    <td>

                        <span class="estado estado-${(item.estado || "").toLowerCase()}">

                            ${item.estado}

                        </span>

                    </td>

                    <td>${item.prioridad ?? ""}</td>

                    <td>

                        <button class="btn btn-sm btn-success"

                            onclick="despachoUI.enRuta(${item.id})">

                            Ruta

                        </button>

                        <button class="btn btn-sm btn-primary"

                            onclick="despachoUI.finalizar(${item.id})">

                            Finalizar

                        </button>

                    </td>

                </tr>

            `;

        });

    }

    cargarCola(lista) {

        const cola = document.getElementById("colaDespacho");

        if (!cola) return;

        cola.innerHTML = "";

        lista.forEach(item => {

            cola.innerHTML += `

                <div class="list-group-item prioridad-${(item.prioridad || "media").toLowerCase()}">

                    <strong>${item.paciente ?? item.paciente_id}</strong>

                    <br>

                    ${item.direccion ?? ""}

                </div>

            `;

        });

    }

    filtrarTabla(texto) {

        texto = texto.toLowerCase();

        document.querySelectorAll("tbody tr").forEach(fila => {

            fila.style.display = fila.innerText.toLowerCase().includes(texto)

                ? ""

                : "none";

        });

    }

    async enRuta(id) {

        await fetch(`${this.baseURL}/${id}/en-ruta`, {

            method: "PUT"

        });

        this.cargarDashboard();

    }

    async finalizar(id) {

        await fetch(`${this.baseURL}/${id}/finalizar`, {

            method: "PUT"

        });

        this.cargarDashboard();

    }

    actualizacionAutomatica() {

        setInterval(() => {

            this.cargarDashboard();

        }, 60000);

    }

}

const despachoUI = new DespachoUI();