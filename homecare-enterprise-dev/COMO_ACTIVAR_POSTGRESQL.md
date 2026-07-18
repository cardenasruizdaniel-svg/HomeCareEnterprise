# Cómo activar PostgreSQL en Render

El sistema ya está preparado para usar PostgreSQL — detecta solo si debe usarlo, según una variable de entorno. **No hay que tocar ni una línea de código para activarlo.**

---

## Cómo funciona (para entender qué va a pasar)

- Si la variable de entorno `DATABASE_URL` **no existe**, el sistema sigue usando SQLite exactamente igual que hasta ahora (nada cambia).
- Si `DATABASE_URL` **sí existe** y empieza con `postgres://` o `postgresql://` (que es justo el formato que entrega Render automáticamente), el sistema usa PostgreSQL en su lugar — sin ningún otro ajuste.

---

## Paso 1 — Crear la base de datos PostgreSQL en Render

1. Entrar a [render.com](https://render.com) → **New** → **PostgreSQL**.
2. Ponerle un nombre (ej: `homecare-db`).
3. Elegir la región (idealmente la misma región donde está el servicio web, para que la conexión sea más rápida).
4. Elegir el plan — para empezar, el plan gratuito o el más básico de pago sirve perfectamente; se puede subir de plan después sin perder nada.
5. Crear.

Render tarda uno o dos minutos en aprovisionarla.

---

## Paso 2 — Conectar la base de datos al servicio web

1. Entrar al servicio web de HomeCare Enterprise en Render.
2. Ir a **Environment** (Variables de entorno).
3. Render, si la base de datos y el servicio web están en la misma cuenta, generalmente ofrece conectarlos automáticamente y crear la variable `DATABASE_URL` sola. Si no aparece sola:
   - Ir a la base de datos creada → copiar el **"Internal Database URL"** (la interna, no la externa — es más rápida y no sale a internet).
   - Volver al servicio web → Environment → **Add Environment Variable**.
   - Nombre: `DATABASE_URL`
   - Valor: pegar la URL copiada.
4. Guardar los cambios — Render va a reiniciar el servicio automáticamente.

---

## Paso 3 — Confirmar que arrancó bien

Al reiniciar, el sistema va a:
1. Detectar la variable `DATABASE_URL`.
2. Conectarse a PostgreSQL en vez de SQLite.
3. Crear todas las tablas automáticamente (el mismo proceso que ya corre siempre al iniciar).
4. Sembrar los catálogos de referencia igual que en cualquier instalación nueva.

Para confirmar que todo quedó bien:
- Entrar al sistema con el usuario administrador por defecto.
- Si el login funciona y el Dashboard carga sin errores, la base de datos PostgreSQL ya está funcionando.
- En los logs de Render (pestaña "Logs" del servicio web), no debería aparecer ningún error relacionado con `psycopg2` o `DATABASE_URL`.

---

## Importante: esto es información de prueba, así que se empieza limpio

Como confirmamos que todavía no hay pacientes reales cargados, no hace falta migrar ningún dato — el sistema simplemente arranca en PostgreSQL con todo limpio (igual que una instalación nueva), y desde ahí ya se puede empezar a cargar información real de una vez, directamente en la base de datos robusta.

---

## Copias de seguridad (ya con PostgreSQL)

Render hace copias de seguridad automáticas diarias de las bases de datos PostgreSQL administradas (según el plan elegido, con distinta cantidad de días de retención) — esto ya es un salto grande de seguridad comparado con SQLite, donde había que acordarse de copiar el archivo manualmente.

---

## Si algo sale mal

Si por algún motivo la conexión a PostgreSQL fallara al arrancar, basta con **quitar la variable `DATABASE_URL`** del servicio web en Render, y el sistema vuelve a funcionar con SQLite de inmediato, sin perder nada de lo demás — es un interruptor de ida y vuelta, no un cambio de un solo sentido.
