function buscarCIE10(){

    let texto = document.getElementById("buscarCIE10").value;

    fetch("/api/cie10?buscar=" + texto)

    .then(response => response.json())

    .then(datos=>{

        let html="";

        datos.forEach(item=>{

            html += `

            <tr>

                <td>

                    <strong>${item.codigo}</strong>

                </td>

                <td>

                    ${item.descripcion}

                </td>

                <td>

                    <button

                        class="btn btn-success btn-sm"

                        onclick="seleccionarCIE10(

                            '${item.codigo}',

                            '${item.descripcion}'

                        )">

                        Seleccionar

                    </button>

                </td>

            </tr>

            `;

        });

        document.getElementById("resultadoCIE10").innerHTML = html;

    });

}

function seleccionarCIE10(

    codigo,

    descripcion

){

    document.getElementById("codigo_cie10").value = codigo;

    document.getElementById("diagnostico").value = descripcion;

    bootstrap.Modal.getInstance(

        document.getElementById("modalBusquedaCIE10")

    ).hide();

}