"""
HomeCare Enterprise - Zonas de la ciudad

Catálogo simple de zonas geográficas de referencia, para
poder agrupar a los pacientes por sector de la ciudad y
programar las visitas de un mismo día en la misma zona
(mucho más eficiente que cruzar la ciudad de un lado a otro).
"""

ZONAS_CIUDAD = [
    "Norte",
    "Sur",
    "Oriente",
    "Occidente",
    "Centro",
    "Nororiente",
    "Noroccidente",
    "Suroriente",
    "Suroccidente",
    "Cordilleranos",  # antes "Zona Rural" -- pacientes que se visitan una sola vez al mes
]

# Zonas que NO se visitan cada vez que se arma la ruta del día
# siguiente, sino con una periodicidad propia -- por ahora solo
# "Cordilleranos", que se visita una vez al mes.
ZONAS_CON_PERIODICIDAD_PROPIA = {
    "Cordilleranos": 30,  # días entre una visita y la siguiente
}
