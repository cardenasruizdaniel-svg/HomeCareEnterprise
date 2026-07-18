"""
=========================================================
HomeCare Enterprise
Lote inicial ILUSTRATIVO de medicamentos frecuentes en
atencion domiciliaria (SIN codigo CUM real, a proposito).

ADVERTENCIA IMPORTANTE: a diferencia del catalogo DIVIPOLA
(descargado directamente de la fuente oficial del DANE), NO
se incluyen aqui numeros de CUM reales porque no tenemos
forma de verificarlos contra el registro vigente del INVIMA
en este momento. Inventar un numero con formato de CUM real
seria peligroso: alguien podria confundirlo con un codigo
valido y reportarlo en un RIPS real. Por eso el "codigo" de
cada fila es un marcador "PENDIENTE-CUM-NNN" que el sistema
resalta en rojo hasta que se reemplace por el CUM oficial,
consultado en:
https://consultaregistro.invima.gov.co/Consultas/consultas/consreg_encabcum.jsp

El CUM lo administra el INVIMA y tiene decenas de miles de
registros (uno por cada presentacion comercial de cada
medicamento), actualizado permanentemente. Para cargar el
listado oficial completo, usar CUMRepository.importar_csv().

Cada tupla: (codigo, nombre, principio_activo, concentracion, forma_farmaceutica)
=========================================================
"""

CUM_FRECUENTES = [
    ("PENDIENTE-CUM-001", "Acetaminofén 500mg tableta", "Acetaminofén", "500mg", "Tableta"),
    ("PENDIENTE-CUM-002", "Ibuprofeno 400mg tableta", "Ibuprofeno", "400mg", "Tableta"),
    ("PENDIENTE-CUM-003", "Losartán potásico 50mg tableta", "Losartán potásico", "50mg", "Tableta"),
    ("PENDIENTE-CUM-004", "Metformina clorhidrato 850mg tableta", "Metformina clorhidrato", "850mg", "Tableta"),
    ("PENDIENTE-CUM-005", "Omeprazol 20mg cápsula", "Omeprazol", "20mg", "Cápsula"),
    ("PENDIENTE-CUM-006", "Amoxicilina 500mg cápsula", "Amoxicilina", "500mg", "Cápsula"),
    ("PENDIENTE-CUM-007", "Enalapril maleato 20mg tableta", "Enalapril maleato", "20mg", "Tableta"),
    ("PENDIENTE-CUM-008", "Ácido acetilsalicílico 100mg tableta", "Ácido acetilsalicílico", "100mg", "Tableta"),
    ("PENDIENTE-CUM-009", "Furosemida 40mg tableta", "Furosemida", "40mg", "Tableta"),
    ("PENDIENTE-CUM-010", "Insulina NPH 100 UI/mL suspensión inyectable", "Insulina isófana humana (NPH)", "100 UI/mL", "Suspensión inyectable"),
]
