"""Script de verificacion rapida del pipeline v2."""
import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, r'c:\Users\Usuario\Downloads\PROYECTO')

import unittest.mock as mock
sys.modules['streamlit'] = mock.MagicMock()

print("Importando config...")
from config import ZONAS, FLOTA_INICIAL
print(f"  Zonas: {len(ZONAS)} - Flota inicial: {len(FLOTA_INICIAL)}")

print("Importando database...")
from database import SQLiteManager
db = SQLiteManager()
stats = db.get_estadisticas()
print(f"  Flota en DB: {stats['total_flota']} vehiculos, Disponibles: {stats['disponibles']}")

print("Importando agents...")
from agents import ejecutar_pipeline

print("Ejecutando pipeline completo...")
r = ejecutar_pipeline(
    descripcion='Transformador explotado en Avenida Principal, cables MT caidos',
    tipo_incidente='Transformador averiado / explotado',
    zona='Norte',
    clima='Lluvioso',
    db=db,
    fuente='test',
)

if r['exito']:
    a1 = r['agente1'].datos
    a2 = r['agente2'].datos
    a3 = r['agente3'].datos
    print(f"  EXITO!")
    print(f"  Vehiculo: {a1['id_vehiculo']} ({a1['tipo_vehiculo']})")
    print(f"  Chofer  : {a1['chofer']} - ETA: {a1['tiempo_estimado_min']} min")
    print(f"  Riesgo  : {a2['nivel_riesgo']} - Veredicto: {a2['veredicto']}")
    print(f"  OT      : {a3['numero_ot']}")

    bot = r['admin_bot']
    pdf = bot.generar_pdf(a3['texto_ot'], a3['numero_ot'])
    sz = len(pdf) if pdf else 0
    hdr = pdf[:4] if pdf else b'VACIO'
    print(f"  PDF     : {sz} bytes - Header: {hdr}")
    print()
    print("=== TODAS LAS VERIFICACIONES PASARON ===")
else:
    print("FALLO:", r)
