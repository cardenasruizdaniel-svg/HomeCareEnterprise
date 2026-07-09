# Facturación Electrónica de Copagos

Marco normativo vigente: Resolución 000227 de 2025 (que unificó y
consolidó la Resolución 000165 de 2023 y sus modificatorias, incluida
la Resolución 000202 de 2025). Estructura de datos: UBL 2.1.

## Qué implementa HomeCare Enterprise hoy

1. **Copagos** (`/copagos/{paciente_id}`): se registra cuánto debe
   pagar un paciente por una atención (copago o cuota moderadora), y
   se marca cuándo y cómo lo pagó (efectivo, transferencia, tarjeta,
   PSE).
2. **Factura Electrónica de Venta (FEV)**: al marcar un copago como
   pagado, el sistema puede generar automáticamente:
   - El **XML en estructura UBL 2.1** (`services/facturacion_service.py`,
     `core/facturacion/xml_builder.py`), con los mismos bloques que
     exige el Anexo Técnico de la DIAN (`Invoice`, `AccountingSupplierParty`,
     `AccountingCustomerParty`, `InvoiceLine`, `TaxTotal`,
     `LegalMonetaryTotal`).
   - La **representación gráfica en PDF**, que se envía automáticamente
     al paciente por correo (reutilizando el mismo mecanismo de envío
     de las órdenes médicas).
3. Los servicios de salud domiciliarios están **excluidos de IVA**
   (Estatuto Tributario, artículo 476), por lo que el sistema calcula
   `valor_iva = 0` en todas las facturas de copago.

## Qué NO hace (y por qué)

**El CUFE que genera el sistema es una referencia local (hash SHA-384),
no el CUFE oficial de la DIAN.** El CUFE real solo lo puede calcular
un facturador **habilitado**, porque su fórmula exige una "clave
técnica" que la DIAN asigna de forma privada a cada facturador durante
el proceso de habilitación. Sin esa clave, es matemáticamente
imposible calcular el CUFE real — no es una limitación del código,
es una limitación de diseño del propio sistema de la DIAN (a propósito,
para que nadie pueda facturar en nombre de otro).

Para que estas facturas sean válidas fiscalmente, la IPS debe:

1. **Habilitarse como facturador electrónico** ante la DIAN (trámite
   en el RUT, actualizando la responsabilidad correspondiente).
2. Obtener un **certificado de firma digital** vigente.
3. Usar el **software gratuito de la DIAN** (viable si el volumen de
   copagos es bajo) o contratar un **proveedor tecnológico habilitado**
   (Alegra, Siigo, Factus, World Office, Helisa, entre otros) que se
   encargue de la transmisión, validación y devolución del CUFE oficial.
4. Configurar en la DIAN el **prefijo y rango de numeración** autorizado
   (actualmente el sistema numera internamente con el prefijo `FEV`,
   que debe reemplazarse por el que la DIAN autorice).

Ninguno de estos pasos depende del software: son trámites y decisiones
administrativas de la IPS. Este sistema deja el documento armado en el
formato correcto para que, cuando la IPS elija su proveedor
tecnológico, la integración solo requiera conectar la transmisión —
no rediseñar la captura de datos de copagos.

## Recomendación práctica

Mientras se define el proveedor tecnológico, estas facturas sirven
como **comprobante interno** del cobro del copago (con PDF real
entregable al paciente), pero **no reemplazan** la factura de venta
válida fiscalmente. Una vez la IPS esté habilitada, sustituir
`calcular_cufe_local()` en `core/facturacion/xml_builder.py` por la
llamada al proveedor tecnológico elegido.
