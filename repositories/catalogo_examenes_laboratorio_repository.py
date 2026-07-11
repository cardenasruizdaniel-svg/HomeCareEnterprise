"""
HomeCare Enterprise - Catálogo de Exámenes de Laboratorio

Trae precargados los exámenes más solicitados en atención
domiciliaria, cada uno con sus parámetros y rangos de
referencia estándar (valores habituales de laboratorio
clínico en Colombia, en adultos) -- para que al registrar un
resultado solo haya que escribir el valor obtenido de cada
parámetro, no armar la lista completa a mano cada vez.

IMPORTANTE: los rangos de referencia pueden variar levemente
entre laboratorios (según el equipo/método que usen) -- estos
son los rangos de referencia generales más usados. Si el
laboratorio que atiende a la IPS maneja rangos distintos,
se pueden ajustar aquí mismo o al momento de registrar el
resultado.
"""

from database.database import consultar_escalar, consultar_todos, ejecutar

EXAMENES_PRECARGADOS = {
    "Hemograma completo": {
        "categoria": "Hematología",
        "parametros": [
            ("Glóbulos rojos", "mill/mm3", 4.5, 5.9),
            ("Hemoglobina", "g/dL", 13.5, 17.5),
            ("Hematocrito", "%", 41, 53),
            ("VCM (volumen corpuscular medio)", "fL", 80, 100),
            ("HCM (hemoglobina corpuscular media)", "pg", 27, 33),
            ("CHCM", "g/dL", 32, 36),
            ("Glóbulos blancos", "/mm3", 4500, 11000),
            ("Neutrófilos", "%", 40, 70),
            ("Linfocitos", "%", 20, 45),
            ("Monocitos", "%", 2, 10),
            ("Eosinófilos", "%", 0, 6),
            ("Plaquetas", "/mm3", 150000, 450000),
        ],
    },
    "Parcial de orina": {
        "categoria": "Uroanálisis",
        "parametros": [
            ("Color", "", None, None),
            ("Aspecto", "", None, None),
            ("pH", "", 5, 8),
            ("Densidad", "", 1.005, 1.030),
            ("Proteínas", "mg/dL", 0, 0),
            ("Glucosa", "mg/dL", 0, 0),
            ("Cetonas", "mg/dL", 0, 0),
            ("Nitritos", "", None, None),
            ("Leucocitos (sedimento)", "por campo", 0, 5),
            ("Hematíes (sedimento)", "por campo", 0, 3),
            ("Bacterias", "", None, None),
        ],
    },
    "Glicemia en ayunas": {
        "categoria": "Química Sanguínea",
        "parametros": [("Glucosa en ayunas", "mg/dL", 70, 100)],
    },
    "Hemoglobina glicosilada (HbA1c)": {
        "categoria": "Química Sanguínea",
        "parametros": [("Hemoglobina glicosilada A1c", "%", 4, 5.6)],
    },
    "Perfil lipídico": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Colesterol total", "mg/dL", 0, 200),
            ("Colesterol HDL", "mg/dL", 40, 60),
            ("Colesterol LDL", "mg/dL", 0, 130),
            ("Triglicéridos", "mg/dL", 0, 150),
        ],
    },
    "Perfil renal": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Creatinina", "mg/dL", 0.6, 1.3),
            ("BUN (nitrógeno ureico)", "mg/dL", 7, 20),
            ("Ácido úrico", "mg/dL", 3.4, 7.0),
        ],
    },
    "Perfil hepático": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("ALT (TGP)", "U/L", 7, 56),
            ("AST (TGO)", "U/L", 10, 40),
            ("Bilirrubina total", "mg/dL", 0.3, 1.2),
            ("Fosfatasa alcalina", "U/L", 44, 147),
        ],
    },
    "Electrolitos séricos": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Sodio", "mEq/L", 135, 145),
            ("Potasio", "mEq/L", 3.5, 5.1),
            ("Cloro", "mEq/L", 98, 107),
        ],
    },
    "Perfil tiroideo (TSH + T4 libre)": {
        "categoria": "Endocrinología",
        "parametros": [
            ("TSH", "µUI/mL", 0.4, 4.0),
            ("T4 libre", "ng/dL", 0.8, 1.8),
        ],
    },
    "Pruebas de coagulación (PT/PTT/INR)": {
        "categoria": "Coagulación",
        "parametros": [
            ("Tiempo de protrombina (PT)", "seg", 11, 13.5),
            ("INR", "", 0.8, 1.2),
            ("Tiempo parcial de tromboplastina (PTT)", "seg", 25, 35),
        ],
    },
    "PCR (proteína C reactiva)": {
        "categoria": "Inmunología",
        "parametros": [("PCR", "mg/L", 0, 10)],
    },
}


def sembrar_si_vacio():
    total = consultar_escalar("SELECT COUNT(*) FROM catalogo_examenes_laboratorio") or 0
    if total > 0:
        return

    for nombre_examen, datos in EXAMENES_PRECARGADOS.items():
        examen_id = ejecutar(
            "INSERT INTO catalogo_examenes_laboratorio(nombre_examen, categoria) VALUES (?, ?)",
            (nombre_examen, datos["categoria"]),
        )
        for orden, (nombre_parametro, unidad, rango_min, rango_max) in enumerate(datos["parametros"]):
            ejecutar(
                """
                INSERT INTO catalogo_parametros_laboratorio(
                    examen_id, nombre_parametro, unidad, rango_min, rango_max, orden
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (examen_id, nombre_parametro, unidad, rango_min, rango_max, orden),
            )


def listar_examenes():
    return consultar_todos(
        "SELECT * FROM catalogo_examenes_laboratorio WHERE activo=1 ORDER BY categoria, nombre_examen"
    )


def listar_parametros_de_examen(examen_id: int):
    return consultar_todos(
        "SELECT * FROM catalogo_parametros_laboratorio WHERE examen_id=? ORDER BY orden",
        (examen_id,),
    )


def crear_examen(nombre_examen: str, categoria: str, parametros: list) -> int:
    examen_id = ejecutar(
        "INSERT INTO catalogo_examenes_laboratorio(nombre_examen, categoria) VALUES (?, ?)",
        (nombre_examen, categoria or ""),
    )
    for orden, p in enumerate(parametros):
        ejecutar(
            """
            INSERT INTO catalogo_parametros_laboratorio(
                examen_id, nombre_parametro, unidad, rango_min, rango_max, orden
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (examen_id, p["nombre_parametro"], p.get("unidad", ""), p.get("rango_min"), p.get("rango_max"), orden),
        )
    return examen_id


def desactivar_examen(examen_id: int):
    ejecutar("UPDATE catalogo_examenes_laboratorio SET activo=0 WHERE id=?", (examen_id,))
