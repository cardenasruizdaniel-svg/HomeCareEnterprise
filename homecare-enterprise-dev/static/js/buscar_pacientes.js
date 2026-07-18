/* HomeCare Enterprise - Busqueda de pacientes en el modal
   Envuelto en una funcion inmediata (IIFE) para que nunca
   falle aunque el script se cargue mas de una vez en la
   misma pagina (evita el error "Identifier ya declarado"). */

(function () {

    const txtBuscar = document.getElementById("buscarPaciente");

    if (txtBuscar) {

        txtBuscar.addEventListener("keyup", async () => {

            const texto = txtBuscar.value;

            if (texto.length < 2) {
                return;
            }

            const respuesta = await fetch(
                "/api/pacientes?buscar_texto=" + encodeURIComponent(texto)
            );

            const datos = await respuesta.json();

            const tabla = document.getElementById("tablaPacientes");
            tabla.innerHTML = "";

            if (datos.length === 0) {
                tabla.innerHTML = `
                <tr><td colspan="5" class="text-center text-muted py-3">
                    No se encontraron pacientes con ese criterio.
                </td></tr>`;
                return;
            }

            datos.forEach((p) => {
                tabla.innerHTML += `
                <tr>
                    <td>${p.documento}</td>
                    <td>${p.nombre}</td>
                    <td>${p.eps || ""}</td>
                    <td>${p.ciudad || ""}</td>
                    <td>
                        <button
                            class="btn btn-success btn-sm"
                            onclick='seleccionarPaciente(${JSON.stringify(p)})'>
                            Seleccionar
                        </button>
                    </td>
                </tr>`;
            });
        });
    }

    window.seleccionarPaciente = function (p) {

        document.getElementById("paciente_id").value = p.id;
        document.getElementById("paciente_documento").value = p.documento;
        document.getElementById("paciente_nombre").value = p.nombre;
        document.getElementById("paciente_eps").value = p.eps || "";
        document.getElementById("paciente_ciudad").value = p.ciudad || "";
        document.getElementById("paciente_direccion").value = p.direccion || "";
        document.getElementById("paciente_telefono").value = p.telefono || "";

        const campoEdad = document.getElementById("paciente_edad");
        if (campoEdad) campoEdad.value = (p.edad !== null && p.edad !== undefined) ? p.edad : "";

        const campoSexo = document.getElementById("paciente_sexo");
        if (campoSexo) campoSexo.value = p.sexo || "";

        const instanciaModal = bootstrap.Modal.getInstance(
            document.getElementById("modalPaciente")
        );

        if (instanciaModal) {
            instanciaModal.hide();
        }
    };

})();
