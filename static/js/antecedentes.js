const filtro=document.getElementById("buscarAntecedente");

if(filtro){

filtro.addEventListener("keyup",function(){

let texto=this.value.toLowerCase();

let filas=document.querySelectorAll("#tablaAntecedentes tbody tr");

filas.forEach(f=>{

let contenido=f.innerText.toLowerCase();

f.style.display=contenido.includes(texto)?"":"none";

});

});

}