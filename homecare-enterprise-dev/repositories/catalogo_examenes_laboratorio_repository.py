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

    # ---------------- HEMATOLOGÍA (ampliación) ----------------
    "Velocidad de Sedimentación Globular (VSG)": {
        "categoria": "Hematología",
        "parametros": [("VSG", "mm/h", 0, 20)],
    },
    "Reticulocitos": {
        "categoria": "Hematología",
        "parametros": [("Reticulocitos", "%", 0.5, 2.5)],
    },
    "Frotis de Sangre Periférica": {
        "categoria": "Hematología",
        "parametros": [
            ("Morfología de glóbulos rojos", "", None, None),
            ("Morfología de glóbulos blancos", "", None, None),
            ("Morfología de plaquetas", "", None, None),
        ],
    },
    "Ferritina": {
        "categoria": "Hematología",
        "parametros": [("Ferritina", "ng/mL", 15, 150)],
    },
    "Hierro sérico y transferrina": {
        "categoria": "Hematología",
        "parametros": [
            ("Hierro sérico", "µg/dL", 50, 170),
            ("Transferrina", "mg/dL", 200, 360),
            ("Saturación de transferrina", "%", 20, 50),
        ],
    },

    # ---------------- QUÍMICA SANGUÍNEA (ampliación) ----------------
    "Proteínas totales y albúmina": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Proteínas totales", "g/dL", 6.4, 8.3),
            ("Albúmina", "g/dL", 3.5, 5.0),
            ("Globulinas", "g/dL", 2.0, 3.5),
        ],
    },
    "Calcio, fósforo y magnesio": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Calcio sérico", "mg/dL", 8.5, 10.5),
            ("Fósforo", "mg/dL", 2.5, 4.5),
            ("Magnesio", "mg/dL", 1.7, 2.2),
        ],
    },
    "Bilirrubinas (total, directa, indirecta)": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Bilirrubina total", "mg/dL", 0.3, 1.2),
            ("Bilirrubina directa", "mg/dL", 0.0, 0.3),
            ("Bilirrubina indirecta", "mg/dL", 0.2, 0.9),
        ],
    },
    "Gamma GT (GGT)": {
        "categoria": "Química Sanguínea",
        "parametros": [("Gamma GT", "U/L", 8, 61)],
    },
    "Amilasa y lipasa": {
        "categoria": "Química Sanguínea",
        "parametros": [
            ("Amilasa", "U/L", 28, 100),
            ("Lipasa", "U/L", 13, 60),
        ],
    },
    "Deshidrogenasa láctica (LDH)": {
        "categoria": "Química Sanguínea",
        "parametros": [("LDH", "U/L", 140, 280)],
    },
    "Creatinquinasa (CK total)": {
        "categoria": "Química Sanguínea",
        "parametros": [("CK total", "U/L", 30, 200)],
    },

    # ---------------- PERFIL CARDÍACO ----------------
    "Perfil cardíaco (Troponina + CK-MB)": {
        "categoria": "Cardiología",
        "parametros": [
            ("Troponina I", "ng/mL", 0, 0.04),
            ("CK-MB", "ng/mL", 0, 5),
        ],
    },
    "Péptido Natriurético (NT-proBNP)": {
        "categoria": "Cardiología",
        "parametros": [("NT-proBNP", "pg/mL", 0, 125)],
    },

    # ---------------- GASES Y ELECTROLITOS ----------------
    "Gases arteriales": {
        "categoria": "Gases Arteriales",
        "parametros": [
            ("pH arterial", "", 7.35, 7.45),
            ("PaO2", "mmHg", 80, 100),
            ("PaCO2", "mmHg", 35, 45),
            ("HCO3", "mEq/L", 22, 26),
            ("Saturación de O2", "%", 95, 100),
        ],
    },
    "Calcio iónico": {
        "categoria": "Gases Arteriales",
        "parametros": [("Calcio iónico", "mmol/L", 1.1, 1.3)],
    },

    # ---------------- ENDOCRINOLOGÍA (ampliación) ----------------
    "Insulina basal": {
        "categoria": "Endocrinología",
        "parametros": [("Insulina basal", "µU/mL", 2.6, 24.9)],
    },
    "Cortisol": {
        "categoria": "Endocrinología",
        "parametros": [("Cortisol AM", "µg/dL", 6.2, 19.4)],
    },
    "Testosterona": {
        "categoria": "Endocrinología",
        "parametros": [("Testosterona total", "ng/dL", 280, 1100)],
    },
    "Perfil tiroideo completo (TSH, T3, T4)": {
        "categoria": "Endocrinología",
        "parametros": [
            ("TSH", "µUI/mL", 0.4, 4.0),
            ("T4 libre", "ng/dL", 0.8, 1.8),
            ("T3 total", "ng/dL", 80, 200),
        ],
    },
    "Vitamina D (25-OH)": {
        "categoria": "Endocrinología",
        "parametros": [("25-OH Vitamina D", "ng/mL", 30, 100)],
    },
    "Vitamina B12 y ácido fólico": {
        "categoria": "Endocrinología",
        "parametros": [
            ("Vitamina B12", "pg/mL", 200, 900),
            ("Ácido fólico", "ng/mL", 3, 20),
        ],
    },
    "Paratohormona (PTH)": {
        "categoria": "Endocrinología",
        "parametros": [("PTH", "pg/mL", 15, 65)],
    },

    # ---------------- SEROLOGÍA / INFECCIOSAS ----------------
    "VIH (prueba de tamizaje)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [("VIH Ac/Ag", "", None, None)],
    },
    "VDRL / RPR (sífilis)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [("VDRL", "", None, None)],
    },
    "Hepatitis B (HBsAg)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [("Antígeno de superficie Hepatitis B", "", None, None)],
    },
    "Hepatitis C (Anti-HCV)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [("Anticuerpos Hepatitis C", "", None, None)],
    },
    "Prueba rápida de Dengue (NS1/IgM/IgG)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [
            ("Antígeno NS1", "", None, None),
            ("IgM Dengue", "", None, None),
            ("IgG Dengue", "", None, None),
        ],
    },
    "Toxoplasma (IgG/IgM)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [
            ("Toxoplasma IgG", "UI/mL", 0, 3),
            ("Toxoplasma IgM", "", None, None),
        ],
    },
    "Widal (fiebre tifoidea)": {
        "categoria": "Serología / Infecciosas",
        "parametros": [("Widal O", "", None, None), ("Widal H", "", None, None)],
    },

    # ---------------- MICROBIOLOGÍA / CULTIVOS ----------------
    "Urocultivo": {
        "categoria": "Microbiología",
        "parametros": [
            ("Recuento de colonias", "UFC/mL", 0, 10000),
            ("Microorganismo aislado", "", None, None),
        ],
    },
    "Coprocultivo": {
        "categoria": "Microbiología",
        "parametros": [("Microorganismo aislado", "", None, None)],
    },
    "Hemocultivo": {
        "categoria": "Microbiología",
        "parametros": [("Resultado", "", None, None)],
    },
    "Cultivo de secreción de herida": {
        "categoria": "Microbiología",
        "parametros": [("Microorganismo aislado", "", None, None), ("Antibiograma", "", None, None)],
    },
    "KOH / Frotis directo": {
        "categoria": "Microbiología",
        "parametros": [("Resultado", "", None, None)],
    },

    # ---------------- COPROLÓGICO ----------------
    "Coprológico (parasitológico de heces)": {
        "categoria": "Coprológico",
        "parametros": [
            ("Aspecto", "", None, None),
            ("Sangre oculta", "", None, None),
            ("Parásitos", "", None, None),
            ("Leucocitos fecales", "por campo", 0, 5),
        ],
    },
    "Sangre oculta en heces": {
        "categoria": "Coprológico",
        "parametros": [("Sangre oculta", "", None, None)],
    },

    # ---------------- MARCADORES TUMORALES ----------------
    "Antígeno Prostático Específico (PSA)": {
        "categoria": "Marcadores Tumorales",
        "parametros": [("PSA total", "ng/mL", 0, 4)],
    },
    "CA 125": {
        "categoria": "Marcadores Tumorales",
        "parametros": [("CA 125", "U/mL", 0, 35)],
    },
    "Antígeno Carcinoembrionario (CEA)": {
        "categoria": "Marcadores Tumorales",
        "parametros": [("CEA", "ng/mL", 0, 5)],
    },
    "Alfafetoproteína (AFP)": {
        "categoria": "Marcadores Tumorales",
        "parametros": [("AFP", "ng/mL", 0, 10)],
    },
}


def sembrar_si_vacio():
    """
    Siembra los exámenes que todavía no existan en el catálogo
    -- así, si se agregan exámenes nuevos en una actualización
    del programa, las instalaciones que ya tenían el catálogo
    sembrado también reciben los nuevos (sin duplicar los que
    ya existían).
    """
    for nombre_examen, datos in EXAMENES_PRECARGADOS.items():
        ya_existe = consultar_escalar(
            "SELECT COUNT(*) FROM catalogo_examenes_laboratorio WHERE nombre_examen=?", (nombre_examen,)
        )
        if ya_existe:
            continue

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
