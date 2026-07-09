/*
==========================================================
HOMECARE IPS ENTERPRISE
Expediente Clínico
==========================================================
*/

let pacienteId = null;
let moduloActual = "resumen";


/*=========================================================
INICIALIZAR
=========================================================*/

function inicializarExpediente(idPaciente){

    pacienteId = idPaciente;

    const ultimoModulo = localStorage.getItem("modulo_clinico");

    if(ultimoModulo){

        cargarModulo(ultimoModulo);

    }else{

        cargarModulo("resumen");

    }

}


/*=========================================================
CARGAR MODULO
=========================================================*/

async function cargarModulo(modulo){

    moduloActual = modulo;

    localStorage.setItem(

        "modulo_clinico",

        modulo

    );

    activarMenu(modulo);

    cambiarTitulo(modulo);

    mostrarSpinner();

    try{

        const respuesta = await fetch(

            `/pacientes/${pacienteId}/modulo/${modulo}`

        );

        if(!respuesta.ok){

            throw new Error(

                "No fue posible cargar el módulo."

            );

        }

        const html = await respuesta.text();

        document.getElementById(

            "contenidoModulo"

        ).innerHTML = html;

    }

    catch(error){

        document.getElementById(

            "contenidoModulo"

        ).innerHTML = `

        <div class="alert alert-danger">

            <h5>

                Error

            </h5>

            ${error.message}

        </div>

        `;

    }

}


/*=========================================================
SPINNER
=========================================================*/

function mostrarSpinner(){

    document.getElementById(

        "contenidoModulo"

    ).innerHTML = `

    <div class="text-center p-5">

        <div

            class="spinner-border text-primary"

            role="status">

        </div>

        <br><br>

        Cargando información...

    </div>

    `;

}


/*=========================================================
TITULO
=========================================================*/

function cambiarTitulo(modulo){

    let titulo = modulo;

    titulo = titulo.replace("_"," ");

    titulo = titulo.charAt(0).toUpperCase()

        + titulo.slice(1);

    document.getElementById(

        "tituloModulo"

    ).innerHTML = titulo;

}


/*=========================================================
MENU ACTIVO
=========================================================*/

function activarMenu(modulo){

    document

        .querySelectorAll(

            ".menu-clinico"

        )

        .forEach(item=>{

            item.classList.remove("active");

        });

    const boton = document.getElementById(

        "menu-"+modulo

    );

    if(boton){

        boton.classList.add(

            "active"

        );

    }

}


/*=========================================================
RECARGAR
=========================================================*/

function recargarModulo(){

    cargarModulo(

        moduloActual

    );

}


/*=========================================================
SIGUIENTE MODULO
=========================================================*/

function siguienteModulo(){

    const lista=[

        "resumen",

        "diagnosticos",

        "antecedentes",

        "alergias",

        "medicamentos",

        "signos",

        "evoluciones",

        "procedimientos",

        "examenes",

        "imagenes",

        "documentos",

        "visitas",

        "programacion",

        "facturacion",

        "auditoria"

    ];

    let indice = lista.indexOf(

        moduloActual

    );

    indice++;

    if(indice>=lista.length){

        indice=0;

    }

    cargarModulo(

        lista[indice]

    );

}


/*=========================================================
MODULO ANTERIOR
=========================================================*/

function moduloAnterior(){

    const lista=[

        "resumen",

        "diagnosticos",

        "antecedentes",

        "alergias",

        "medicamentos",

        "signos",

        "evoluciones",

        "procedimientos",

        "examenes",

        "imagenes",

        "documentos",

        "visitas",

        "programacion",

        "facturacion",

        "auditoria"

    ];

    let indice = lista.indexOf(

        moduloActual

    );

    indice--;

    if(indice<0){

        indice=lista.length-1;

    }

    cargarModulo(

        lista[indice]

    );

}