/*
=========================================================
HomeCare Enterprise
Diseñador Universal
Sprint 3 - Entrega 30
=========================================================
*/

async function cargarComponentes() {

    const lista = document.getElementById("lista-componentes");

    if (!lista) return;

    lista.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary"></div>
            <p class="mt-2">Cargando componentes...</p>
        </div>
    `;

    try {

        const respuesta = await fetch("/plantillas/api/componentes");

        if (!respuesta.ok) {
            throw new Error("Error cargando componentes");
        }

        const componentes = await respuesta.json();

        lista.innerHTML = "";

        if (componentes.length === 0) {

            lista.innerHTML = `
                <div class="alert alert-warning">
                    No existen componentes registrados.
                </div>
            `;

            return;

        }

        componentes.forEach(function(componente){

            lista.innerHTML += `

                <div
                    class="card shadow-sm mb-2 componente-item"
                    draggable="true"
                    data-codigo="${componente.codigo}">

                    <div class="card-body p-2">

                        <i class="bi ${componente.icono}"></i>

                        <strong>

                            ${componente.nombre}

                        </strong>

                        <br>

                        <small class="text-muted">

                            ${componente.categoria}

                        </small>

                    </div>

                </div>

            `;

        });

        inicializarDragDrop();

    }

    catch(error){

        console.error(error);

        lista.innerHTML = `

            <div class="alert alert-danger">

                Error cargando componentes

            </div>

        `;

    }

}

document.addEventListener(

    "DOMContentLoaded",

    function(){

        cargarComponentes();

    }

);

// ======================================================
// DRAG & DROP
// ======================================================

let componenteArrastrado = null;

function inicializarDragDrop() {

    console.clear();

    const items = document.querySelectorAll(".componente-item");

    console.log("Componentes encontrados:", items.length);

    items.forEach(function(item){

        console.log("Registrando:", item.dataset.codigo);

        item.addEventListener("dragstart", function(e){

            console.log("Drag:", this.dataset.codigo);

            componenteArrastrado = {

                codigo: this.dataset.codigo,

                nombre: this.innerText.trim()

            };

        });

    });

    const canvas = document.getElementById("canvas");

    if(!canvas){

        console.error("No existe el canvas");

        return;

    }

    console.log("Canvas encontrado");

    canvas.addEventListener("dragover", function(e){

        e.preventDefault();

    });

    canvas.addEventListener("drop", function(e){

        e.preventDefault();

        console.log("DROP");

        agregarComponente();

    });

}

// =====================================================
// FORMULARIO EN MEMORIA
// =====================================================

let formulario = {

    id: null,

    nombre: "",

    componentes: []

};

let contadorComponentes = 1;

// ======================================================
// AGREGAR COMPONENTE
// ======================================================

function agregarComponente(){

    if(!componenteArrastrado){

        return;

    }

    const mensaje=document.getElementById("mensaje-vacio");

    if(mensaje){

        mensaje.remove();

    }

    const canvas=document.getElementById("canvas");

    const tarjeta=document.createElement("div");

    tarjeta.className="card shadow-sm mb-3";

    tarjeta.innerHTML=`

        <div class="card-body">

            <strong>

                ${componenteArrastrado.nombre}

            </strong>

            <hr>

            <input

                class="form-control"

                placeholder="Vista previa del componente">

        </div>

    `;

    const componenteJSON = {

    id: "cmp_" + contadorComponentes,

    tipo: componenteArrastrado.codigo,

    nombre: componenteArrastrado.nombre,

    label: componenteArrastrado.nombre,

    requerido: false,

    placeholder: "",

    visible: true,

    orden: contadorComponentes,

    configuracion: {}

};

formulario.componentes.push(componenteJSON);

contadorComponentes++;

console.log(formulario);

    canvas.appendChild(tarjeta);

}