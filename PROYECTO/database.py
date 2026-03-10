"""
database.py — Capa de datos SQLite para ElectroDispatch AI v3
Tabla compartida entre la app Streamlit y el bot de Telegram.

Tablas:
  flota              — Vehículos: CRUD completo
  incidentes         — Historial de Órdenes de Trabajo
  reportes_telegram  — Mensajes y fotos del bot
  alertas            — Alertas de seguridad activas
  inventario_taller  — Control de stock del taller
"""
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from config import FLOTA_INICIAL, DB_PATH


class SQLiteManager:
    """
    Gestiona todas las operaciones de base de datos del sistema.
    Usa SQLite como backend local — no requiere servidor externo.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        """Crea una conexión con row_factory para dict-like access."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ─────────────────────────────────────────────────────────────────────────
    # INICIALIZACIÓN
    # ─────────────────────────────────────────────────────────────────────────

    def init_db(self):
        """Crea todas las tablas si no existen y puebla la flota inicial."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS flota (
                    id           TEXT PRIMARY KEY,
                    tipo         TEXT NOT NULL,
                    estado       TEXT NOT NULL DEFAULT 'Disponible',
                    zona         TEXT NOT NULL,
                    chofer       TEXT NOT NULL,
                    capacidad_ton REAL NOT NULL DEFAULT 1,
                    materiales   TEXT,
                    updated_at   TEXT
                );

                CREATE TABLE IF NOT EXISTS incidentes (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_ot         TEXT UNIQUE,
                    descripcion       TEXT,
                    tipo_incidente    TEXT,
                    zona              TEXT,
                    clima             TEXT,
                    vehiculo_asignado TEXT,
                    chofer            TEXT,
                    eta_min           INTEGER,
                    nivel_riesgo      TEXT,
                    veredicto         TEXT,
                    advertencias      TEXT,
                    epp_requerido     TEXT,
                    texto_ot          TEXT,
                    fuente            TEXT DEFAULT 'web',
                    created_at        TEXT
                );

                CREATE TABLE IF NOT EXISTS reportes_telegram (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id       TEXT,
                    username      TEXT,
                    nombre        TEXT,
                    tipo          TEXT,
                    contenido     TEXT,
                    foto_bytes    BLOB,
                    foto_filename TEXT,
                    procesado     INTEGER DEFAULT 0,
                    created_at    TEXT
                );

                CREATE TABLE IF NOT EXISTS alertas (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo       TEXT,
                    mensaje    TEXT,
                    zona       TEXT,
                    nivel      TEXT DEFAULT 'MEDIO',
                    activa     INTEGER DEFAULT 1,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS inventario_taller (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria    TEXT NOT NULL DEFAULT 'General',
                    item         TEXT NOT NULL,
                    cantidad     REAL NOT NULL DEFAULT 0,
                    unidad       TEXT NOT NULL DEFAULT 'unidades',
                    minimo_stock REAL NOT NULL DEFAULT 0,
                    ubicacion    TEXT DEFAULT '',
                    notas        TEXT DEFAULT '',
                    updated_at   TEXT
                );
            """)
            conn.commit()
            # Poblar inventario inicial si está vacío
            cnt_inv = conn.execute("SELECT COUNT(*) FROM inventario_taller").fetchone()[0]
            if cnt_inv == 0:
                self._poblar_inventario_inicial(conn)
            # Poblar flota si está vacía
            count = conn.execute("SELECT COUNT(*) FROM flota").fetchone()[0]
            if count == 0:
                self._poblar_flota_inicial(conn)

    def _poblar_flota_inicial(self, conn: sqlite3.Connection):
        """Inserta los vehículos del mock data si la tabla está vacía."""
        now = datetime.now().isoformat()
        for v in FLOTA_INICIAL:
            conn.execute(
                """INSERT OR IGNORE INTO flota
                   (id, tipo, estado, zona, chofer, capacidad_ton, materiales, updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    v["id"], v["tipo"], v["estado"], v["zona"], v["chofer"],
                    v["capacidad_ton"], json.dumps(v["materiales"]), now,
                )
            )
        conn.commit()

    def _poblar_inventario_inicial(self, conn: sqlite3.Connection):
        """Stock inicial del taller."""
        now = datetime.now().isoformat()
        items = [
            # (categoria, item, cantidad, unidad, minimo_stock, ubicacion)
            ("EPP","Casco seguridad eléctrico",20,"unidades",5,"Estante A1"),
            ("EPP","Guantes dieléctricos Clase 4",15,"pares",4,"Estante A2"),
            ("EPP","Botas dieléctricas",10,"pares",3,"Estante A3"),
            ("EPP","Arnés de seguridad",8,"unidades",2,"Estante A4"),
            ("EPP","Careta facial arco",6,"unidades",2,"Estante A5"),
            ("EPP","Chaleco reflectante AR",12,"unidades",4,"Estante A6"),
            ("EPP","Traje ignífugo Cat.2",5,"unidades",2,"Estante A7"),
            ("Materiales Eléctricos","Cable 12AWG THHN",500,"metros",100,"Bodega B1"),
            ("Materiales Eléctricos","Cable 10AWG THHN",300,"metros",80,"Bodega B1"),
            ("Materiales Eléctricos","Breaker 1P 20A",25,"unidades",5,"Bodega B2"),
            ("Materiales Eléctricos","Breaker 3P 100A",8,"unidades",2,"Bodega B2"),
            ("Materiales Eléctricos","Cinta aislante 3M",40,"rollos",10,"Bodega B3"),
            ("Materiales Eléctricos","Conector tipo cuña",100,"unidades",20,"Bodega B3"),
            ("Materiales Eléctricos","Terminal preaislado",200,"unidades",50,"Bodega B4"),
            ("Herramientas","Alicate universal",10,"unidades",3,"Herramientero C1"),
            ("Herramientas","Voltímetro digital",6,"unidades",2,"Herramientero C1"),
            ("Herramientas","Detector de tensión",8,"unidades",2,"Herramientero C2"),
            ("Herramientas","Pinza amperimétrica",5,"unidades",2,"Herramientero C2"),
            ("Herramientas","Llave de perico",12,"unidades",3,"Herramientero C3"),
            ("Repuestos","Fusible cuchilla 60A",30,"unidades",8,"Bodega D1"),
            ("Repuestos","Fusible NH 100A",20,"unidades",5,"Bodega D1"),
            ("Repuestos","Pararrayos 15kV",4,"unidades",1,"Bodega D2"),
            ("Consumibles","Lubricante dieléctrico",10,"frascos",3,"Bodega E1"),
            ("Consumibles","Bridas plásticas",500,"unidades",100,"Bodega E2"),
            ("Consumibles","Señales viales",15,"unidades",4,"Bodega E3"),
        ]
        conn.executemany(
            "INSERT INTO inventario_taller (categoria,item,cantidad,unidad,minimo_stock,ubicacion,updated_at) VALUES (?,?,?,?,?,?,?)",
            [(i[0],i[1],i[2],i[3],i[4],i[5],now) for i in items]
        )
        conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # FLOTA — CRUD COMPLETO
    # ─────────────────────────────────────────────────────────────────────────

    def get_flota(self) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM flota ORDER BY id").fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_flota_disponible(self) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM flota WHERE estado = 'Disponible' ORDER BY zona"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update_estado_vehiculo(self, vehiculo_id: str, nuevo_estado: str):
        """Actualiza el estado operativo de un vehículo."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE flota SET estado = ?, updated_at = ? WHERE id = ?",
                (nuevo_estado, datetime.now().isoformat(), vehiculo_id)
            )
            conn.commit()

    def update_vehiculo(self, vehiculo_id: str, campos: Dict[str, Any]):
        """Actualiza campos arbitrarios de un vehículo."""
        campos["updated_at"] = datetime.now().isoformat()
        sets = ", ".join(f"{k} = ?" for k in campos)
        vals = list(campos.values()) + [vehiculo_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE flota SET {sets} WHERE id = ?", vals)
            conn.commit()

    def agregar_vehiculo(self, datos: Dict[str, Any]) -> bool:
        """Agrega un vehículo nuevo. Retorna False si el ID ya existe."""
        now = datetime.now().isoformat()
        try:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO flota (id,tipo,estado,zona,chofer,capacidad_ton,materiales,updated_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (datos["id"], datos["tipo"], datos.get("estado","Disponible"),
                     datos["zona"], datos["chofer"], datos.get("capacidad_ton",1),
                     json.dumps(datos.get("materiales",[])), now)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_vehiculo(self, vehiculo_id: str):
        """Elimina un vehículo de la flota permanentemente."""
        with self._connect() as conn:
            conn.execute("DELETE FROM flota WHERE id = ?", (vehiculo_id,))
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # INCIDENTES / ÓRDENES DE TRABAJO
    # ─────────────────────────────────────────────────────────────────────────

    def agregar_incidente(self, datos: Dict[str, Any]) -> int:
        """Persiste una OT en la base de datos. Retorna el ID insertado."""
        datos["created_at"] = datos.get("created_at", datetime.now().isoformat())
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO incidentes
                   (numero_ot, descripcion, tipo_incidente, zona, clima,
                    vehiculo_asignado, chofer, eta_min, nivel_riesgo, veredicto,
                    advertencias, epp_requerido, texto_ot, fuente, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    datos.get("numero_ot"),
                    datos.get("descripcion"),
                    datos.get("tipo_incidente"),
                    datos.get("zona"),
                    datos.get("clima"),
                    datos.get("vehiculo_asignado"),
                    datos.get("chofer"),
                    datos.get("eta_min"),
                    datos.get("nivel_riesgo"),
                    datos.get("veredicto"),
                    json.dumps(datos.get("advertencias", [])),
                    json.dumps(datos.get("epp_requerido", [])),
                    datos.get("texto_ot"),
                    datos.get("fuente", "web"),
                    datos["created_at"],
                )
            )
            conn.commit()
            return cur.lastrowid

    def get_incidentes(self, limit: int = 50) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM incidentes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def eliminar_incidente(self, incidente_id: int):
        """Elimina un incidente/OT específico."""
        with self._connect() as conn:
            conn.execute("DELETE FROM incidentes WHERE id = ?", (incidente_id,))
            conn.commit()

    def vaciar_actividades(self):
        """Elimina todos los registros de la tabla incidentes."""
        with self._connect() as conn:
            conn.execute("DELETE FROM incidentes")
            conn.commit()

    def get_incidentes_hoy(self) -> List[Dict]:
        hoy = datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM incidentes WHERE created_at LIKE ? ORDER BY id DESC",
                (f"{hoy}%",)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_estadisticas(self) -> Dict[str, Any]:
        """Retorna estadísticas globales para el dashboard."""
        with self._connect() as conn:
            total_ot        = conn.execute("SELECT COUNT(*) FROM incidentes").fetchone()[0]
            ot_hoy          = len(self.get_incidentes_hoy())
            disponibles     = conn.execute("SELECT COUNT(*) FROM flota WHERE estado='Disponible'").fetchone()[0]
            ocupados        = conn.execute("SELECT COUNT(*) FROM flota WHERE estado='Ocupado'").fetchone()[0]
            mantenimiento   = conn.execute("SELECT COUNT(*) FROM flota WHERE estado='Mantenimiento'").fetchone()[0]
            total_flota     = conn.execute("SELECT COUNT(*) FROM flota").fetchone()[0]
            alertas_activas = conn.execute("SELECT COUNT(*) FROM alertas WHERE activa=1").fetchone()[0]
            reportes_tg     = conn.execute("SELECT COUNT(*) FROM reportes_telegram").fetchone()[0]
            nuevos_tg       = conn.execute("SELECT COUNT(*) FROM reportes_telegram WHERE procesado=0").fetchone()[0]
            stock_bajo      = conn.execute(
                "SELECT COUNT(*) FROM inventario_taller WHERE cantidad <= minimo_stock AND minimo_stock > 0"
            ).fetchone()[0]

            por_zona = conn.execute(
                "SELECT zona, COUNT(*) as total FROM incidentes GROUP BY zona ORDER BY total DESC"
            ).fetchall()
            por_riesgo = conn.execute(
                "SELECT nivel_riesgo, COUNT(*) as total FROM incidentes GROUP BY nivel_riesgo"
            ).fetchall()

        return {
            "total_ot": total_ot,
            "ot_hoy": ot_hoy,
            "disponibles": disponibles,
            "ocupados": ocupados,
            "mantenimiento": mantenimiento,
            "total_flota": total_flota,
            "alertas_activas": alertas_activas,
            "reportes_telegram": reportes_tg,
            "nuevos_telegram": nuevos_tg,
            "stock_bajo": stock_bajo,
            "por_zona": [dict(r) for r in por_zona],
            "por_riesgo": [dict(r) for r in por_riesgo],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # REPORTES TELEGRAM
    # ─────────────────────────────────────────────────────────────────────────

    def agregar_reporte_telegram(
        self, chat_id: str, username: str, nombre: str,
        tipo: str, contenido: str,
        foto_bytes: Optional[bytes] = None,
        foto_filename: Optional[str] = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO reportes_telegram
                   (chat_id, username, nombre, tipo, contenido, foto_bytes, foto_filename, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    chat_id, username, nombre, tipo, contenido,
                    foto_bytes, foto_filename,
                    datetime.now().isoformat(),
                )
            )
            conn.commit()
            return cur.lastrowid

    def get_reportes_telegram(self, limit: int = 30) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM reportes_telegram ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_dict(r, excluir_blob=False) for r in rows]

    def marcar_procesado(self, reporte_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE reportes_telegram SET procesado = 1 WHERE id = ?", (reporte_id,)
            )
            conn.commit()

    def eliminar_reporte_telegram(self, reporte_id: int):
        """Elimina permanentemente un reporte de la tabla reportes_telegram."""
        with self._connect() as conn:
            conn.execute("DELETE FROM reportes_telegram WHERE id = ?", (reporte_id,))
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # ALERTAS
    # ─────────────────────────────────────────────────────────────────────────

    def agregar_alerta(self, tipo: str, mensaje: str, zona: str, nivel: str = "MEDIO") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO alertas (tipo, mensaje, zona, nivel, created_at) VALUES (?,?,?,?,?)",
                (tipo, mensaje, zona, nivel, datetime.now().isoformat())
            )
            conn.commit()
            return cur.lastrowid

    def get_alertas_activas(self) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM alertas WHERE activa=1 ORDER BY id DESC LIMIT 20"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def cerrar_alerta(self, alerta_id: int):
        with self._connect() as conn:
            conn.execute("UPDATE alertas SET activa = 0 WHERE id = ?", (alerta_id,))
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # INVENTARIO TALLER — CRUD COMPLETO
    # ─────────────────────────────────────────────────────────────────────────

    def get_inventario(self, categoria: Optional[str] = None) -> List[Dict]:
        """Retorna todo el inventario, opcionalmente filtrado por categoría."""
        with self._connect() as conn:
            if categoria and categoria != "Todas":
                rows = conn.execute(
                    "SELECT * FROM inventario_taller WHERE categoria=? ORDER BY categoria, item",
                    (categoria,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM inventario_taller ORDER BY categoria, item"
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_categorias_inventario(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT categoria FROM inventario_taller ORDER BY categoria"
            ).fetchall()
            return [r[0] for r in rows]

    def get_items_bajo_stock(self) -> List[Dict]:
        """Items cuya cantidad <= minimo_stock (solo donde minimo > 0)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM inventario_taller WHERE cantidad <= minimo_stock AND minimo_stock > 0 ORDER BY categoria"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def agregar_item_inventario(self, datos: Dict[str, Any]) -> int:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO inventario_taller
                   (categoria, item, cantidad, unidad, minimo_stock, ubicacion, notas, updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (datos.get("categoria","General"), datos["item"],
                 datos.get("cantidad",0), datos.get("unidad","unidades"),
                 datos.get("minimo_stock",0), datos.get("ubicacion",""),
                 datos.get("notas",""), now)
            )
            conn.commit()
            return cur.lastrowid

    def update_item_inventario(self, item_id: int, datos: Dict[str, Any]):
        datos["updated_at"] = datetime.now().isoformat()
        sets = ", ".join(f"{k} = ?" for k in datos)
        vals = list(datos.values()) + [item_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE inventario_taller SET {sets} WHERE id = ?", vals)
            conn.commit()

    def eliminar_item_inventario(self, item_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM inventario_taller WHERE id = ?", (item_id,))
            conn.commit()

    def ajustar_cantidad(self, item_id: int, delta: float):
        """Suma/resta delta a la cantidad actual (entrada/salida de stock)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE inventario_taller SET cantidad = MAX(0, cantidad + ?), updated_at = ? WHERE id = ?",
                (delta, datetime.now().isoformat(), item_id)
            )
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────────────────────────────

    def _row_to_dict(self, row: sqlite3.Row, excluir_blob: bool = True) -> Dict:
        d = dict(row)
        if excluir_blob and "foto_bytes" in d:
            d.pop("foto_bytes", None)
        return d


# Instancia global (singleton) — usada por app.py y telegram_bot.py
db = SQLiteManager()
