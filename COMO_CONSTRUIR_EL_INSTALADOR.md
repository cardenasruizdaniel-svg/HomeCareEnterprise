# Cómo construir el instalador de HomeCare Enterprise para Windows

Esta guía es para hacerlo **una sola vez** (o cada vez que se quiera generar una versión nueva del instalador). El resultado final es un archivo `.exe` que cualquier persona puede instalar con doble clic, sin necesitar Python ni nada técnico — igual que instalar Office.

**Tiempo estimado:** 20-40 minutos la primera vez (la mayoría es esperando que se instalen cosas).

---

## Lo que se necesita antes de empezar

1. Un computador con **Windows 10 u 11** (64 bits).
2. Conexión a internet (para descargar Python y las dependencias — después de armado, el instalador final funciona sin internet).
3. Unos **3 GB libres** en disco durante el proceso (el resultado final es más liviano, pero durante la construcción se necesita espacio de sobra).

---

## Paso 1 — Instalar Python

1. Ir a [python.org/downloads](https://www.python.org/downloads/) y descargar **Python 3.11 o 3.12** (evitar la 3.13 por ahora, algunas librerías tardan en dar soporte).
2. Al instalar, **muy importante:** marcar la casilla que dice **"Add python.exe to PATH"** antes de darle a Instalar.
3. Para confirmar que quedó bien instalado, abrir el **Símbolo del sistema (CMD)** y escribir:
   ```
   python --version
   ```
   Debe mostrar algo como `Python 3.11.x`.

---

## Paso 2 — Copiar el proyecto a la carpeta de trabajo

1. Descomprimir el ZIP del proyecto (`homecare-enterprise-dev.zip`) en una carpeta fácil de encontrar, por ejemplo:
   ```
   C:\HomeCareBuild\
   ```
2. Abrir el Símbolo del sistema **dentro de esa carpeta** (se puede hacer rápido escribiendo `cmd` en la barra de direcciones del Explorador de Windows, estando parado en esa carpeta, y presionando Enter).

---

## Paso 3 — Instalar las dependencias del proyecto

Dentro de la carpeta del proyecto, ejecutar:

```
pip install -r requirements.txt
pip install pyinstaller
```

Esto se demora varios minutos (especialmente por las librerías de reconocimiento facial).

> **Si algo falla aquí:** el archivo `requirements.txt` tiene versiones específicas de cada librería. Si alguna versión ya no está disponible el día que se haga esto, el mensaje de error dice claramente cuál — se puede quitar el número de versión de esa línea específica (dejando solo el nombre) e intentar de nuevo, o preguntarme y lo resolvemos juntos.

---

## Paso 4 — Generar el programa (con PyInstaller)

Todavía dentro de la carpeta del proyecto:

```
pyinstaller homecare.spec
```

Esto tarda varios minutos. Al terminar, va a quedar una carpeta nueva:

```
dist\HomeCare Enterprise\
```

**Antes de seguir, hay que probar que funcione:** entrar a esa carpeta y hacer doble clic en `HomeCare Enterprise.exe`. Debe abrirse una ventana negra (de estado del servidor) y, unos segundos después, el navegador solo con la pantalla de inicio de sesión de HomeCare. Si eso funciona, se puede continuar. Si no abre nada o da error, revisar el mensaje en la ventana negra y avisarme para ayudar a diagnosticarlo.

---

## Paso 5 — Instalar Inno Setup (el programa que arma el instalador visual)

1. Descargar gratis de [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php) (la versión normal, "innosetup-X.X.X.exe").
2. Instalarlo con las opciones de siempre (Siguiente, Siguiente, Instalar).

---

## Paso 6 — Generar el instalador final

1. Abrir el archivo `instalador.iss` (que está en la carpeta del proyecto) — con doble clic debería abrirse directamente en Inno Setup.
2. Dentro de Inno Setup, presionar **Compilar** (o el ícono de play verde, o `Ctrl+F9`).
3. Al terminar, va a quedar el instalador final en:
   ```
   Salida\HomeCare_Enterprise_Instalador.exe
   ```

**Ese archivo es el que se comparte e instala en cualquier computador.**

---

## Cómo lo ve la persona que lo instala

1. Doble clic en `HomeCare_Enterprise_Instalador.exe`.
2. Windows puede preguntar "¿Permitir que esta app haga cambios?" — se acepta (es normal para cualquier instalador).
3. Aparece el asistente: Bienvenida → elegir si quiere ícono en el Escritorio → elegir si quiere que abra solo al encender el computador → Instalar.
4. Al terminar, si dejó marcada la opción, se abre solo.
5. De ahí en adelante, doble clic en el ícono del Escritorio (o del menú de Inicio) abre el sistema completo, ya listo para usar, sin necesitar internet ni Render.

---

## Dónde quedan guardados los datos

La base de datos, los documentos subidos, y las copias de seguridad **no se guardan dentro del programa** (para que no se pierdan al instalar una actualización) — quedan en:

```
%LOCALAPPDATA%\HomeCareEnterprise\
```

(que normalmente es algo como `C:\Users\NombreDeUsuario\AppData\Local\HomeCareEnterprise\`)

Esa carpeta conviene incluirla en las copias de seguridad periódicas del computador.

---

## Para generar una versión nueva más adelante

Cuando yo les entregue una actualización del código:

1. Reemplazar los archivos del proyecto en `C:\HomeCareBuild\` por los nuevos.
2. Repetir solo los **Pasos 4 y 6** (no hace falta repetir la instalación de Python ni de las dependencias, a menos que aparezca una librería nueva).
3. El instalador nuevo va a actualizar el programa, mientras que los datos (pacientes, historias clínicas, etc.) se mantienen intactos en la carpeta de AppData.

---

## Preguntas frecuentes

**¿El instalador funciona sin internet una vez instalado?**
Sí — todo lo que necesita (Python, las librerías, el propio sistema) ya queda incluido dentro del programa instalado. Solo se necesita internet para las funciones que explícitamente lo requieren (enviar WhatsApp, correo, etc.).

**¿Se puede instalar en varios computadores de la IPS?**
Sí, el mismo instalador sirve para cualquier computador con Windows. Cada instalación tiene su PROPIA base de datos local (no se comparten datos entre computadores a menos que se configure algo adicional para eso).

**¿Qué tan pesado queda el instalador?**
Por las librerías de reconocimiento facial (OpenCV), es normal que quede en el rango de 300-500 MB. Es más grande que un instalador típico, pero es esperable para lo que incluye.
