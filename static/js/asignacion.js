/*
==========================================================
HomeCare Enterprise
Motor Inteligente de Asignación
Sprint 3.4
==========================================================
*/

class AsignacionUI {

    constructor() {

        this.api = "/asignacion";

        this.inicializar();

    }

    inicializar() {

        this.configurarEventos();

        this.cargarIndicadores();

    }

    //======================================================
    // EVENTOS
    //======================================================

    configurarEventos() {

        const btn = document.getElementById("btnAsignarTodo");

        if (btn) {

            btn.addEventListener("click", () => {

                this.ejecutarMotor();

            });

        }

        document.querySelectorAll(".btnAsignar")

        .forEach(boton => {

            boton.addEventListener("click", e => {

                this.asignarVisita(

                    e.currentTarget.dataset.id

                );

            });

        });

    }

    //======================================================
    // INDICADORES
    //======================================================

    async cargarIndicadores() {

        try {

            const response = await fetch(

                `${this.api}/indicadores`

            );

            const datos = await response.json();

            this.actualizarIndicadores(datos);

        }

        catch(error){

            console.error(error);

        }

    }

    actualizarIndicadores(datos){

        this.valor(

            "kpiPendientes",

            datos.visitas_pendientes

        );

        this.valor(

            "kpiProfesionales",

            datos.profesionales_disponibles

        );

    }

    valor(id,valor){

        const control=document.getElementById(id);

        if(control){

            control.innerText=valor;

        }

    }

    //======================================================
    // MOTOR AUTOMÁTICO
    //======================================================

    async ejecutarMotor(){

        const salida=document.getElementById(

            "resultadoMotor"

        );

        salida.innerHTML="Ejecutando...";

        try{

            const response=await fetch(

                `${this.api}/ejecutar`,

                {

                    method:"POST"

                }

            );

            const datos=await response.json();

            salida.textContent=JSON.stringify(

                datos,

                null,

                4

            );

            this.valor(

                "kpiAsignadas",

                datos.total

            );

            this.cargarIndicadores();

        }

        catch(error){

            salida.innerHTML=

                error.toString();

        }

    }

    //======================================================
    // UNA VISITA
    //======================================================

    async asignarVisita(id){

        try{

            const response=await fetch(

                `${this.api}/${id}`,

                {

                    method:"POST"

                }

            );

            const datos=await response.json();

            alert(

                "Profesional seleccionado: "

                +

                datos.profesional_id

            );

            location.reload();

        }

        catch(error){

            alert(error);

        }

    }

}

document.addEventListener(

    "DOMContentLoaded",

    ()=>{

        new AsignacionUI();

    }

);