// ==============================
// Sidebar Inteligente
// ==============================

const sidebar = document.querySelector(".sidebar");
const main = document.querySelector(".main");
const btnSidebar = document.getElementById("btnSidebar");

// Restaurar estado guardado
if(localStorage.getItem("sidebar") === "cerrado"){

    sidebar.classList.add("collapsed");
    main.classList.add("expanded");

}

if(btnSidebar){

    btnSidebar.addEventListener("click",()=>{

        sidebar.classList.toggle("collapsed");

        main.classList.toggle("expanded");

        if(sidebar.classList.contains("collapsed")){

            localStorage.setItem("sidebar","cerrado");

        }else{

            localStorage.setItem("sidebar","abierto");

        }

    });

}

// ==============================
// Menú Activo
// ==============================

document.querySelectorAll(".menu a").forEach(link=>{

    if(link.href===window.location.href){

        link.classList.add("active");

    }

});