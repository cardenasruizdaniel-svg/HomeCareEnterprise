# Manual de Conexión del Chatbot de WhatsApp — HomeCare Enterprise

**Para quién es este manual:** el Administrador de la IPS, para dejar el chatbot de WhatsApp funcionando de verdad (no en modo simulado).

**Dónde se configura en el sistema:** Menú lateral → **Chatbot WhatsApp** (`/configuracion-whatsapp`). Solo lo ven el Administrador y el perfil Asistencial.

---

## Antes de empezar: qué necesita tener

1. Una cuenta de **Facebook Business Manager** (gratuita).
2. Un número de celular **que no esté ya usado en una cuenta de WhatsApp normal** (no puede ser el mismo número con el que alguien ya chatea desde la app de WhatsApp del celular — WhatsApp Business API necesita un número dedicado).
3. Su sistema debe estar publicado en internet con una dirección **https://** — si ya lo tiene en Render (`https://homecareenterprise.onrender.com` o el dominio que hayan configurado), esto ya lo cumple.

---

## PASO 1 — Crear la cuenta de WhatsApp Business Platform

1. Entre a [business.facebook.com](https://business.facebook.com) e inicie sesión (o cree la cuenta de la IPS si no la tiene).
2. En el menú, busque **"WhatsApp"** → **"Empezar"** (o entre directamente a [developers.facebook.com](https://developers.facebook.com), cree una App nueva, tipo **"Business"**, y agréguele el producto **"WhatsApp"**).
3. Siga el asistente: le va a pedir verificar la IPS como negocio (nombre legal, NIT, dirección) — use los mismos datos que ya tiene en **Configuración de la Empresa** dentro del sistema.
4. Cuando le pida el número de teléfono, registre el número dedicado para el chatbot (puede ser una línea nueva, o una que la IPS ya tenga pero no use para WhatsApp personal).

---

## PASO 2 — Conseguir el Token de Acceso y el ID del número

1. Dentro del panel de desarrolladores de Meta, vaya a su App → **WhatsApp** → **Configuración de la API**.
2. Ahí va a ver:
   - **Token de acceso temporal** (dura 24 horas — sirve para probar, pero para producción real necesita generar uno **permanente**, ver Paso 4).
   - **ID del número de teléfono** (un número largo, ej: `109876543210987`).
3. Copie ambos datos.

---

## PASO 3 — Conectar el sistema con esos datos

1. En el sistema, entre a **Chatbot WhatsApp** (menú lateral).
2. Marque la casilla **"Chatbot habilitado"**.
3. Pegue el **Token de acceso** y el **ID del número de teléfono** en los campos correspondientes.
4. Copie el **Token de verificación del webhook** que el sistema ya generó solo (aparece en un campo de texto, ya viene lleno) — lo va a necesitar en el siguiente paso.
5. Guarde.

---

## PASO 4 — Registrar el Webhook en Meta (para que el chatbot pueda RECIBIR mensajes)

1. En el panel de desarrolladores de Meta, dentro de su App → **WhatsApp** → **Configuración**, busque la sección **"Webhook"**.
2. Haga clic en **"Editar"** y llene:
   - **URL de retorno de llamada (Callback URL):**
     ```
     https://[su-dominio]/webhook/whatsapp
     ```
     (reemplace `[su-dominio]` por el dominio real donde está publicado el sistema — ej: `homecareenterprise.onrender.com`)
   - **Token de verificación:** pegue exactamente el mismo token que copió en el Paso 3.
3. Haga clic en **"Verificar y guardar"** — Meta le va a hacer una petición automática al sistema; si el token coincide, queda verificado con un ✅.
4. Justo debajo, en **"Campos del Webhook"**, active la casilla **"messages"** (para que le lleguen los mensajes entrantes de los pacientes).

---

## PASO 5 — Generar un Token de Acceso PERMANENTE (para producción real)

El token que copió en el Paso 2 caduca en 24 horas — sirve solo para probar. Para que el chatbot siga funcionando sin que se caiga cada día:

1. En Meta Business Manager, vaya a **Configuración del negocio** → **Usuarios del sistema**.
2. Cree un "Usuario del sistema" nuevo (o use uno existente), con rol de **Administrador**.
3. Genere un **token de acceso** para ese usuario del sistema, asignándole permisos sobre `whatsapp_business_messaging` y `whatsapp_business_management`, con vigencia de **"Nunca expira"**.
4. Reemplace el token temporal por este token permanente en la pantalla de **Chatbot WhatsApp** del sistema (Paso 3, campo "Token de acceso").

---

## PASO 6 — Probar

1. Desde su propio celular (o el de alguien que ya sea paciente registrado en el sistema, con el celular correcto en su ficha), escríbale un mensaje al número de WhatsApp que configuró — cualquier cosa, ej. "hola".
2. Debe recibir el menú automático con las 5 opciones.
3. Si no le llega nada, revise:
   - Que el webhook haya quedado verificado (✅ en el panel de Meta).
   - Que la casilla "messages" esté activada en los campos del webhook.
   - Que "Chatbot habilitado" esté marcado en la pantalla de configuración del sistema.
   - Que el número desde el que escribe esté guardado exactamente en el campo "Celular" de algún paciente (con o sin el +57, el sistema lo reconoce de las dos formas).

---

## Preguntas frecuentes

**¿El chatbot puede mandar mensajes a cualquier persona, o solo a quien escriba primero?**
Por las reglas de WhatsApp Business API, para mensajes que el sistema envía por su cuenta (como una orden médica o la confirmación de una cita), no hay problema. Para que el chatbot RESPONDA preguntas, la persona debe escribirle primero.

**¿Cuánto cuesta?**
Meta cobra por conversación después de cierto número de mensajes gratuitos al mes (varía según el país y el volumen). Revise los precios actuales en el panel de Meta Business — esto no lo administra ni lo cobra el sistema, es directamente con Meta.

**¿Quién en la IPS puede ver/cambiar esta configuración?**
Solo el Administrador y las personas con el perfil **Asistencial** — se puede ajustar quién más tiene acceso desde **Roles y Permisos**, activando o desactivando el módulo "Chatbot de WhatsApp" para cualquier perfil.
