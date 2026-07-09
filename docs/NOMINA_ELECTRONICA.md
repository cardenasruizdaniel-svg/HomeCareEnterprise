# Nómina Electrónica (Documento Soporte de Pago de Nómina - DSNE)

Marco normativo vigente: Resolución 000013 de 2021 (Anexo Técnico de
Nómina Electrónica), hoy recopilada en el **Anexo T.5.4** de la
Resolución 000227 de 2025. A diferencia de la factura de venta, **la
DIAN no ofrece herramienta gratuita para nómina electrónica** — se
requiere software propio validado o un proveedor tecnológico
habilitado.

## Qué implementa HomeCare Enterprise hoy

Al generar una nómina formal (`/nomina` → "Generar nómina de este
periodo"), el botón **"Generar documentos soporte"** crea, para cada
profesional incluido, un **DSNE en XML** (`services/nomina_electronica_service.py`,
`core/nomina_electronica/xml_builder.py`) con las secciones que exige
el Anexo Técnico:

- Encabezado y periodo de nómina.
- Datos del empleador (NIT, razón social) y del trabajador.
- **Devengados**: básico, auxilio de transporte (cuando aplica según
  el tope legal), horas extra y recargos nocturnos/dominicales (para
  los profesionales contratados por horas, tomados del mismo motor de
  cálculo legal usado en la nómina interna).
- **Deducciones**: salud y pensión (4% + 4%), aplicables a los
  contratos de término fijo/indefinido con salario mensual.
- Comprobante total (devengado, deducciones, neto a pagar).

Estos valores son exactamente los mismos que ya calculó el módulo de
Nómina — el DSNE no repite ni reinterpreta cálculos, solo los expone
en el formato que exige la DIAN.

## Qué NO hace (y por qué)

**El CUNE (Código Único de Nómina Electrónica) es una referencia local,
no el CUNE oficial.** Igual que el CUFE de facturación, su cálculo
real requiere una clave técnica que la DIAN asigna únicamente durante
el proceso de habilitación — es una limitación de diseño del sistema
de la DIAN, no del software.

Para transmitir nómina electrónica real, la IPS debe:

1. Tener el **RUT actualizado** con la responsabilidad de nómina
   electrónica activa.
2. Contar con **firma digital** vigente.
3. Elegir un **proveedor tecnológico habilitado** (Siigo, Alegra,
   World Office, Helisa, entre otros) o desarrollar la transmisión
   directa siguiendo las especificaciones técnicas de la DIAN — la
   DIAN no ofrece una herramienta propia gratuita para este documento.
4. Transmitir dentro de los primeros 10 días del mes siguiente al
   periodo pagado (Resolución 000013 de 2021, artículo 8).

## Nota sobre contratos de prestación de servicios

El Documento Soporte de Nómina Electrónica aplica a relaciones
**laborales** (término fijo, indefinido, obra/labor). Los profesionales
contratados por **prestación de servicios** (incluidos muchos
contratos "por horas" en el sector salud) generalmente no generan
DSNE sino su propia **factura de venta o documento equivalente**
como independientes — verifique con su asesor contable cuál aplica a
cada tipo de vínculo antes de transmitir.
