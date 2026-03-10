"""
config.py — Configuración central de ElectroDispatch AI v2
Contiene: zonas, flota vehicular (15 unidades), reglas de seguridad,
          mapa de tiempos de respuesta y tipos de incidente.
"""
from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# ZONAS DEL SISTEMA (Estado Zulia)
# ─────────────────────────────────────────────────────────────────────────────

ZONAS: List[str] = [
    "Maracaibo", "San Francisco", "Cabimas", "Ciudad Ojeda",
    "La Cañada", "Machiques", "Santa Rita", "Bachaquero",
]

# Grid de posición para el mapa visual (fila, columna)
ZONA_GRID: Dict[str, tuple] = {
    "Santa Rita":    (0, 0), "Maracaibo":  (0, 1), "San Francisco": (0, 2),
    "Cabimas":       (1, 0), "Ciudad Ojeda": (1, 1), "La Cañada":    (1, 2),
    "Bachaquero":    (2, 0), "Machiques":    (2, 1),
}

# Color de badge por zona (para UI)
ZONA_COLOR: Dict[str, str] = {
    "Maracaibo": "#2196F3", "San Francisco": "#03A9F4", "Cabimas": "#00BCD4",
    "Ciudad Ojeda": "#009688", "La Cañada": "#4CAF50", "Machiques": "#8BC34A",
    "Santa Rita": "#FF9800", "Bachaquero": "#FF5722",
}

# ─────────────────────────────────────────────────────────────────────────────
# FLOTA VEHICULAR (15 unidades distribuidas en Zulia)
# ─────────────────────────────────────────────────────────────────────────────

FLOTA_INICIAL: List[Dict[str, Any]] = [
    {"id": "VH-001", "tipo": "Grúa",    "estado": "Disponible", "zona": "Maracaibo",      "chofer": "Carlos Mendoza",  "capacidad_ton": 10, "materiales": ["Transformador 250kVA", "Cable MT", "Aisladores", "EPP Completo"]},
    {"id": "VH-002", "tipo": "Canasta", "estado": "Disponible", "zona": "San Francisco",  "chofer": "Luis Herrera",    "capacidad_ton": 2,  "materiales": ["Cable BT", "Fusibles", "EPP Completo", "Linterna"]},
    {"id": "VH-003", "tipo": "Ligero",  "estado": "Ocupado",    "zona": "Maracaibo",      "chofer": "Pedro Ríos",      "capacidad_ton": 1,  "materiales": ["Herramientas básicas", "Medidores"]},
    {"id": "VH-004", "tipo": "Grúa",    "estado": "Disponible", "zona": "Cabimas",        "chofer": "Ramón Castro",    "capacidad_ton": 15, "materiales": ["Transformador 500kVA", "Cable MT", "Postes", "EPP Completo"]},
    {"id": "VH-005", "tipo": "Canasta", "estado": "Ocupado",    "zona": "Ciudad Ojeda",   "chofer": "Ana Gómez",       "capacidad_ton": 2,  "materiales": ["Cable BT", "EPP Completo"]},
    {"id": "VH-006", "tipo": "Ligero",  "estado": "Disponible", "zona": "Santa Rita",     "chofer": "Jorge Vásquez",   "capacidad_ton": 1,  "materiales": ["Herramientas básicas", "EPP Básico", "Medidores"]},
    {"id": "VH-007", "tipo": "Grúa",    "estado": "Disponible", "zona": "Maracaibo",      "chofer": "Martín Díaz",     "capacidad_ton": 12, "materiales": ["Transformador 250kVA", "Cable AT", "EPP Completo"]},
    {"id": "VH-008", "tipo": "Canasta", "estado": "Disponible", "zona": "La Cañada",      "chofer": "Sofía López",     "capacidad_ton": 3,  "materiales": ["Cable BT", "Fusibles", "EPP Completo"]},
    {"id": "VH-009", "tipo": "Ligero",  "estado": "Disponible", "zona": "Machiques",      "chofer": "Raúl Moreno",     "capacidad_ton": 1,  "materiales": ["Herramientas básicas", "Medidores", "EPP Básico"]},
    {"id": "VH-010", "tipo": "Grúa",    "estado": "Mantenimiento","zona": "Bachaquero",   "chofer": "Héctor Pinto",   "capacidad_ton": 20, "materiales": ["Transformador 1000kVA", "Cable MT", "Postes", "EPP Completo"]},
    {"id": "VH-011", "tipo": "Canasta", "estado": "Disponible", "zona": "San Francisco",  "chofer": "Clara Ruiz",      "capacidad_ton": 2,  "materiales": ["Cable BT", "Aisladores", "EPP Completo"]},
    {"id": "VH-012", "tipo": "Grúa",    "estado": "Disponible", "zona": "Machiques",      "chofer": "Ernesto Vega",    "capacidad_ton": 8,  "materiales": ["Cable MT", "Postes", "EPP Completo"]},
    {"id": "VH-013", "tipo": "Ligero",  "estado": "Ocupado",    "zona": "Cabimas",        "chofer": "Diana Flores",    "capacidad_ton": 1,  "materiales": ["Herramientas básicas", "Medidores"]},
    {"id": "VH-014", "tipo": "Canasta", "estado": "Disponible", "zona": "Ciudad Ojeda",   "chofer": "Álvaro Soto",     "capacidad_ton": 4,  "materiales": ["Cable AT", "Aisladores AT", "EPP Completo Clase 4"]},
    {"id": "VH-015", "tipo": "Ligero",  "estado": "Disponible", "zona": "Maracaibo",      "chofer": "Patricia Leal",   "capacidad_ton": 1,  "materiales": ["Herramientas básicas", "EPP Básico", "Laptop"]},
]

# ─────────────────────────────────────────────────────────────────────────────
# INVENTARIO DE ALMACÉN
# ─────────────────────────────────────────────────────────────────────────────

INVENTARIO_ALMACEN: List[Dict[str, Any]] = [
    {"item": "Transformador 250kVA",  "cantidad": 3,    "unidad": "unidades"},
    {"item": "Transformador 500kVA",  "cantidad": 1,    "unidad": "unidades"},
    {"item": "Transformador 1000kVA", "cantidad": 1,    "unidad": "unidades"},
    {"item": "Cable MT 33kV",         "cantidad": 500,  "unidad": "metros"},
    {"item": "Cable BT",              "cantidad": 1200, "unidad": "metros"},
    {"item": "Cable AT 115kV",        "cantidad": 200,  "unidad": "metros"},
    {"item": "Aisladores de línea",   "cantidad": 120,  "unidad": "unidades"},
    {"item": "Fusibles AT",           "cantidad": 80,   "unidad": "unidades"},
    {"item": "EPP Completo (kit)",    "cantidad": 15,   "kits":   "kits"},
    {"item": "Postes de concreto 12m","cantidad": 10,   "unidad": "unidades"},
    {"item": "Guantes dieléctricos",  "cantidad": 40,   "unidad": "pares"},
    {"item": "Arnés de seguridad",    "cantidad": 20,   "unidad": "unidades"},
]

# ─────────────────────────────────────────────────────────────────────────────
# TIEMPO DE RESPUESTA ENTRE ZONAS (minutos) — Estado Zulia
# ─────────────────────────────────────────────────────────────────────────────

TIEMPO_RESPUESTA: Dict[str, Dict[str, int]] = {
    "Maracaibo":      {"Maracaibo": 10, "San Francisco": 15, "Santa Rita": 30, "Cabimas": 45, "Ciudad Ojeda": 65, "La Cañada": 35, "Machiques": 90, "Bachaquero": 85},
    "San Francisco":  {"Maracaibo": 15, "San Francisco": 10, "Santa Rita": 35, "Cabimas": 50, "Ciudad Ojeda": 70, "La Cañada": 20, "Machiques": 85, "Bachaquero": 90},
    "Cabimas":       {"Maracaibo": 45, "San Francisco": 50, "Santa Rita": 20, "Cabimas": 10, "Ciudad Ojeda": 25, "La Cañada": 60, "Machiques": 120, "Bachaquero": 40},
    "Ciudad Ojeda":  {"Maracaibo": 65, "San Francisco": 70, "Santa Rita": 40, "Cabimas": 25, "Ciudad Ojeda": 10, "La Cañada": 80, "Machiques": 140, "Bachaquero": 20},
    "La Cañada":     {"Maracaibo": 35, "San Francisco": 20, "Santa Rita": 55, "Cabimas": 60, "Ciudad Ojeda": 80, "La Cañada": 10, "Machiques": 70, "Bachaquero": 100},
    "Machiques":     {"Maracaibo": 90, "San Francisco": 85, "Santa Rita": 120, "Cabimas": 120, "Ciudad Ojeda": 140, "La Cañada": 70, "Machiques": 10, "Bachaquero": 150},
    "Santa Rita":    {"Maracaibo": 30, "San Francisco": 35, "Santa Rita": 10, "Cabimas": 20, "Ciudad Ojeda": 40, "La Cañada": 55, "Machiques": 120, "Bachaquero": 60},
    "Bachaquero":    {"Maracaibo": 85, "San Francisco": 90, "Santa Rita": 60, "Cabimas": 40, "Ciudad Ojeda": 20, "La Cañada": 100, "Machiques": 150, "Bachaquero": 10},
}

# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE SEGURIDAD
# ─────────────────────────────────────────────────────────────────────────────

REGLAS_SEGURIDAD: Dict[str, Any] = {
    "lluvia_altura": {
        "condicion": "Lluvia + trabajo en altura (Grúa/Canasta)",
        "accion": "ADVERTENCIA",
        "mensaje": "LLUVIA ACTIVA: Trabajo en altura restringido. Requiere autorización de Supervisor de Seguridad y uso de arnés doble.",
        "epp_adicional": ["Arnés doble de seguridad", "Casco con barbuquejo", "Botas dieléctricas", "Guantes aislantes clase 2"],
    },
    "alta_tension": {
        "condicion": "Transformador / Alta Tensión / Media Tensión",
        "accion": "OBLIGATORIO",
        "mensaje": "ALTA TENSION: Se requieren minimo 2 tecnicos certificados. Verificar distancias de seguridad minimas.",
        "epp_adicional": ["Guantes dieléctricos clase 4", "Careta facial", "Ropa ignífuga", "Detector de tensión"],
    },
    "trabajo_nocturno": {
        "condicion": "Hora fuera de rango 06:00–18:00",
        "accion": "ADVERTENCIA",
        "mensaje": "TRABAJO NOCTURNO: Requiere iluminacion artificial minima de 500 lux y acompanante de seguridad.",
        "epp_adicional": ["Chaleco reflectante", "Linterna de cabeza", "Señalización nocturna"],
    },
    "zona_vial": {
        "condicion": "Trabajo en vía pública",
        "accion": "OBLIGATORIO",
        "mensaje": "ZONA VIAL: Señalizar area de trabajo en un radio de 50 m. Coordinacion con transito obligatoria.",
        "epp_adicional": ["Conos de señalización", "Vallas metálicas", "Chaleco reflectante alta visibilidad"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# MAPA DE TIPO DE VEHÍCULO POR PALABRAS CLAVE EN EL INCIDENTE
# ─────────────────────────────────────────────────────────────────────────────

TIPO_POR_INCIDENTE: Dict[str, str] = {
    "transformador": "Grúa",
    "poste":         "Grúa",
    "reemplazo":     "Grúa",
    "grua":          "Grúa",
    "cable":         "Canasta",
    "linea":         "Canasta",
    "altura":        "Canasta",
    "canasta":       "Canasta",
    "medicion":      "Ligero",
    "revision":      "Ligero",
    "inspeccion":    "Ligero",
    "lectura":       "Ligero",
}

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE INCIDENTE PREDEFINIDOS
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_INCIDENTE: List[str] = [
    "Transformador averiado / explotado",
    "Corte de cable de Media Tensión",
    "Corte de cable de Baja Tensión",
    "Poste caído o inclinado",
    "Cortocircuito en red MT",
    "Falla en subestación",
    "Medidor dañado / falso contacto",
    "Revisión preventiva de línea",
    "Inspección de zona industrial",
    "Emergencia — reporte Telegram",
    "Otro (describir abajo)",
]

# Configuración de la app
APP_NAME = "ElectroDispatch AI"
APP_VERSION = "3.1.0"
BOT_USERNAME = "@tetranutabot"
import os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "electrodispatch.db")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")


