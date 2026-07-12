"""
HomeCare Enterprise - Verificación facial de ingreso/salida

Compara la foto de ingreso/salida contra la foto de
"enrolamiento" del profesional (tomada una vez, al crear o
editar su ficha), para confirmar que quien está marcando la
visita es de verdad esa persona -- y no otra usando su usuario.

Funciona 100% local (sin internet ni servicios en la nube),
con OpenCV:
- Detección de rostro: Haar Cascade (viene incluido con OpenCV).
- Comparación: LBPH (Local Binary Pattern Histogram), un
  algoritmo clásico de reconocimiento facial que no necesita
  modelos descargados de internet -- se "entrena" al vuelo con
  la propia foto de enrolamiento.

HONESTIDAD SOBRE LA PRECISIÓN: este es un método razonable
para detectar una suplantación evidente (otra persona
completamente distinta), pero NO tiene la precisión de un
sistema de reconocimiento facial con redes neuronales
profundas (por ejemplo, los que usan las apps de los bancos).
Cambios grandes de luz, ángulo, o el paso de los años entre la
foto de enrolamiento y la verificación pueden afectar el
resultado. El umbral de sensibilidad (UMBRAL_COINCIDENCIA) se
puede ajustar según la experiencia real de uso.
"""

import base64
from io import BytesIO

import cv2
import numpy as np

# Se exige un 80% de similitud para aceptar la foto (ajustable
# aquí si, con el uso real, resulta demasiado estricto o
# demasiado permisivo). LBPH da un valor de "distancia" (más
# bajo = más parecido); se convierte a un porcentaje de
# similitud para que sea más fácil de entender e interpretar.
PORCENTAJE_MINIMO_SIMILITUD = 80

_detector_rostros = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def _decodificar_imagen(imagen_base64: str):
    """Convierte un data-URI base64 (como los que manda la app) a una imagen de OpenCV."""
    if not imagen_base64:
        return None
    try:
        if "," in imagen_base64:
            imagen_base64 = imagen_base64.split(",", 1)[1]
        datos = base64.b64decode(imagen_base64)
        arreglo = np.frombuffer(datos, dtype=np.uint8)
        imagen = cv2.imdecode(arreglo, cv2.IMREAD_COLOR)
        return imagen
    except Exception:
        return None


def _extraer_rostro(imagen_base64: str, tamano=(200, 200)):
    """
    Detecta el rostro más grande de la foto, lo recorta, y le
    aplica una máscara ovalada -- así, las esquinas (que suelen
    tener fondo, pared, ropa, cabello) quedan en un gris neutro
    parejo en vez de información real, y la comparación se
    concentra en el óvalo central del rostro (ojos, nariz,
    boca, mejillas), no en lo que rodea a la persona.
    Devuelve None si no se detecta ningún rostro.
    """
    imagen = _decodificar_imagen(imagen_base64)
    if imagen is None:
        return None

    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    rostros = _detector_rostros.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    if len(rostros) == 0:
        return None

    # Si detecta varios rostros en la foto, se usa el más
    # grande (el más cercano a la cámara -- lo más probable es
    # que sea la persona que está tomando la foto).
    x, y, w, h = max(rostros, key=lambda r: r[2] * r[3])

    # Se reduce un poco el recuadro detectado (10% en cada
    # lado) para acercarse más a la cara y alejarse del pelo,
    # las orejas y el fondo que Haar Cascade suele incluir.
    margen_x, margen_y = int(w * 0.08), int(h * 0.08)
    x2, y2 = max(0, x + margen_x), max(0, y + margen_y)
    w2, h2 = max(1, w - 2 * margen_x), max(1, h - 2 * margen_y)

    rostro_recortado = gris[y2:y2 + h2, x2:x2 + w2]
    rostro_redimensionado = cv2.resize(rostro_recortado, tamano)

    # Máscara ovalada: todo lo que quede FUERA del óvalo
    # central (esquinas -- fondo, cabello, orejas) se vuelve un
    # gris parejo, para que no afecte la comparación. Lo de
    # ADENTRO del óvalo (el rostro en sí) queda intacto.
    mascara = np.zeros(tamano, dtype=np.uint8)
    centro = (tamano[0] // 2, tamano[1] // 2)
    ejes = (int(tamano[0] * 0.42), int(tamano[1] * 0.48))
    cv2.ellipse(mascara, centro, ejes, 0, 0, 360, 255, -1)

    rostro_con_fondo_neutro = np.full(tamano, 127, dtype=np.uint8)
    rostro_con_fondo_neutro[mascara == 255] = rostro_redimensionado[mascara == 255]

    return rostro_con_fondo_neutro


def diagnostico_disponibilidad() -> dict:
    """
    Revisa si OpenCV (con el módulo de reconocimiento facial)
    está realmente instalado y funcionando en este servidor.
    Úsela para confirmar por qué la verificación facial no
    está bloqueando nada -- si esto devuelve "disponible: False",
    la causa es que falta instalar la librería, no un error de
    programación.
    """
    try:
        import cv2
        if not hasattr(cv2, "face"):
            return {
                "disponible": False,
                "motivo": "Está instalado 'opencv-python' pero NO 'opencv-contrib-python' "
                          "(el módulo cv2.face con el reconocimiento facial solo viene en la versión 'contrib').",
            }
        cv2.face.LBPHFaceRecognizer_create()
        ruta_cascada = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        import os
        if not os.path.exists(ruta_cascada):
            return {"disponible": False, "motivo": "No se encontró el archivo de detección de rostros de OpenCV."}
        return {"disponible": True, "motivo": "OpenCV con reconocimiento facial está instalado y funcionando correctamente."}
    except ImportError as error:
        return {
            "disponible": False,
            "motivo": f"OpenCV no está instalado en este servidor ({error}). "
                      "Ejecute: pip install opencv-contrib-python --break-system-packages "
                      "(o sin ese modificador en Windows) y reinicie el programa.",
        }
    except Exception as error:
        return {"disponible": False, "motivo": f"Error inesperado al verificar OpenCV: {error}"}


def comparar_rostros(foto_enrolamiento_base64: str, foto_nueva_base64: str) -> dict:
    """
    Compara la foto tomada en el ingreso/salida contra la foto
    de enrolamiento del profesional.

    Devuelve:
    - {"verificado": True}  -> el profesional no tiene foto de
      enrolamiento registrada (no aplica la verificación para
      él todavía), o el rostro sí coincide.
    - {"verificado": False, "motivo": "..."} -> BLOQUEA el
      registro en cualquiera de estos casos: no se detectó un
      rostro claro en la foto de enrolamiento (hay que
      corregirla desde la ficha del profesional), no se
      detectó un rostro claro en la foto nueva (hay que volver
      a tomarla, de frente y con buena luz), o sí se detectaron
      ambos rostros pero NO coinciden.

    IMPORTANTE: si el profesional SÍ tiene foto de enrolamiento
    registrada, la verificación es OBLIGATORIA -- no se deja
    pasar una foto que no muestre claramente un rostro, para
    evitar que alguien registre el ingreso con una foto de
    cualquier otra cosa.
    """

    if not foto_enrolamiento_base64:
        return {"verificado": True, "motivo": "Este profesional no tiene foto de enrolamiento registrada."}

    rostro_enrolado = _extraer_rostro(foto_enrolamiento_base64)
    if rostro_enrolado is None:
        return {
            "verificado": False,
            "motivo": "La foto de enrolamiento de este profesional no tiene un rostro detectable. "
                      "Un administrador debe actualizarla desde la ficha del profesional en la web.",
        }

    rostro_nuevo = _extraer_rostro(foto_nueva_base64)
    if rostro_nuevo is None:
        return {
            "verificado": False,
            "motivo": "No se detectó un rostro claro en la foto tomada. Tome la foto de frente, "
                      "con buena luz, mostrando su rostro completo (sin gafas oscuras ni gorra).",
        }

    reconocedor = cv2.face.LBPHFaceRecognizer_create()
    reconocedor.train([rostro_enrolado], np.array([1]))

    _etiqueta, confianza = reconocedor.predict(rostro_nuevo)
    similitud_porcentaje = max(0.0, 100.0 - confianza)

    if similitud_porcentaje < PORCENTAJE_MINIMO_SIMILITUD:
        return {
            "verificado": False,
            "motivo": f"El rostro de la foto no coincide con el registrado para este profesional "
                      f"(similitud: {similitud_porcentaje:.0f}%, se requiere al menos {PORCENTAJE_MINIMO_SIMILITUD}%).",
            "similitud_porcentaje": round(similitud_porcentaje, 1),
        }

    return {"verificado": True, "similitud_porcentaje": round(similitud_porcentaje, 1)}
