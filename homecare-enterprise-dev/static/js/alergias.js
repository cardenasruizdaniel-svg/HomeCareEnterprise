const txtBuscarAlergia = document.getElementById("buscarAlergia");

if (txtBuscarAlergia) {

    txtBuscarAlergia.addEventListener("keyup", function () {

        const texto = this.value.toLowerCase();

        const filas = document.querySelectorAll("#tablaAlergias tbody tr");

        filas.forEach(fila => {

            const contenido = fila.innerText.toLowerCase();

            fila.style.display = contenido.includes(texto) ? "" : "none";

        });

    });

}