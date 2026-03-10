"""
agents.py — ElectroDispatch AI v3 — Agentes Mejorados
======================================================
Agente P0: PriorityClassifier     — Clasifica urgencia 1-4 por palabras clave
Agente P1: LogisticsManager       — Asignación óptima con scoring multi-factor
Agente P2: SafetyGuardian         — Validación EPP + nuevas reglas (arco, espacio, escalera)
Agente P3: AdminBot               — OT estructurada + PDF
Extra:     ZoneCoverageAnalyzer   — Analiza cobertura y sugiere pre-posicionamiento
"""
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from fpdf import FPDF

from config import REGLAS_SEGURIDAD, TIEMPO_RESPUESTA, TIPO_POR_INCIDENTE
from database import SQLiteManager


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO ESTÁNDAR DE AGENTE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Encapsula el output estandarizado de cualquier agente."""
    success: bool
    datos: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE P0: CLASIFICADOR DE PRIORIDAD
# ─────────────────────────────────────────────────────────────────────────────

class PriorityClassifier:
    """
    Agente P0 — Clasificador de Prioridad.

    Analiza palabras clave en la descripción e infiere el nivel de urgencia
    del incidente (1=CRÍTICA → 4=BAJA). Determina el tiempo máximo de respuesta.
    Este agente corre PRIMERO en el pipeline para que todo el proceso conozca
    la urgencia desde el inicio.
    """

    NIVELES = {
        1: {"nivel": "CRÍTICA",  "color": "#F43F5E", "emoji": "🔴", "tiempo_max": 10},
        2: {"nivel": "ALTA",     "color": "#F59E0B", "emoji": "🟠", "tiempo_max": 25},
        3: {"nivel": "MEDIA",    "color": "#4E90D3", "emoji": "🟡", "tiempo_max": 60},
        4: {"nivel": "BAJA",     "color": "#10B981", "emoji": "🟢", "tiempo_max": 180},
    }

    KW = {
        1: ["personas atrapadas", "heridos", "muertos", "electrocutado", "electrocucion",
            "incendio", "explosion", "explosión", "fuego", "cables vía pública caídos",
            "sin luz hospital", "sin luz semaforo", "derrumbe", "cable energizado tocan"],
        2: ["transformador", "subestacion", "subestación", "media tension", "alta tension",
            "explotado", "quemado", "arco electrico", "cortocircuito", "sin electricidad",
            "apagon grande", "barrio sin luz"],
        4: ["revision", "revisión", "inspeccion", "inspección", "medidor", "lectura",
            "mantenimiento preventivo", "rutinario", "rutina"],
    }

    def run(self, descripcion: str, tipo_incidente: str = "") -> AgentResult:
        desc = (descripcion + " " + tipo_incidente).lower()
        logs = ["Clasificando nivel de prioridad del incidente..."]
        nivel = 3  # Default MEDIA

        kw_detectadas = []
        for n in [1, 2, 4]:
            for kw in self.KW[n]:
                if kw in desc:
                    kw_detectadas.append(kw)
                    if n < nivel or nivel == 3:
                        nivel = n
                    break

        info = self.NIVELES[nivel]
        if kw_detectadas:
            logs.append(f"Palabras clave detectadas: {', '.join(kw_detectadas[:4])}")
        else:
            logs.append("Sin palabras clave especiales → prioridad MEDIA por defecto")

        logs.append(f"Prioridad asignada: {info['emoji']} NIVEL {nivel} — {info['nivel']}")
        logs.append(f"Tiempo máximo de respuesta para este nivel: {info['tiempo_max']} minutos")

        alerta_extra = ""
        if nivel == 1:
            alerta_extra = "⚠️ ACTIVAR PROTOCOLO DE EMERGENCIA — Notificar supervisor de turno inmediatamente."
            logs.append(alerta_extra)

        return AgentResult(
            success=True,
            datos={
                "numero": nivel,
                "nivel": info["nivel"],
                "color": info["color"],
                "emoji": info["emoji"],
                "tiempo_max_min": info["tiempo_max"],
                "alerta_extra": alerta_extra,
            },
            logs=logs,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE P1: COORDINADOR LOGÍSTICO (SCORING MULTI-FACTOR)
# ─────────────────────────────────────────────────────────────────────────────

class LogisticsManager:
    """
    Agente P1 — Coordinador Logístico v3.

    Mejora respecto a v2: scoring multi-factor en lugar de solo ordenar por ETA.
    Pondera: coincidencia de tipo (50 pts), ETA (0–40 pts), capacidad (10 pts).
    Lee flota disponible en tiempo real de SQLite.
    """

    def __init__(self, db: SQLiteManager):
        self.db = db

    def _inferir_tipo(self, descripcion: str) -> str:
        desc_lower = descripcion.lower()
        for palabra, tipo in TIPO_POR_INCIDENTE.items():
            if palabra in desc_lower:
                return tipo
        return "Grúa"

    def _eta(self, zona_v: str, zona_i: str) -> int:
        try:
            return TIEMPO_RESPUESTA[zona_v][zona_i]
        except KeyError:
            return 90

    def _score(self, v: Dict, tipo_req: str, zona_i: str) -> int:
        """Score: tipo (50), ETA (40), capacidad (10)."""
        score = 0
        # Tipo
        if v["tipo"] == tipo_req:
            score += 50
        elif tipo_req == "Grúa" and v["tipo"] == "Canasta":
            score += 20
        elif tipo_req == "Canasta" and v["tipo"] == "Grúa":
            score += 15
        # ETA
        eta = self._eta(v["zona"], zona_i)
        score += max(0, 40 - eta // 2)
        # Capacidad
        if v.get("capacidad_ton", 0) >= 5:
            score += 10
        elif v.get("capacidad_ton", 0) >= 2:
            score += 5
        return score

    def run(self, descripcion: str, zona_incidente: str, tipo_incidente: str = "",
            prioridad_num: int = 3) -> AgentResult:
        logs = []
        logs.append(f"Analizando solicitud: «{descripcion[:80]}»")
        logs.append(f"Zona objetivo: {zona_incidente} | Prioridad: {prioridad_num}")

        tipo_req = self._inferir_tipo(descripcion + " " + tipo_incidente)
        logs.append(f"Tipo de vehículo requerido: {tipo_req}")

        import json
        flota = self.db.get_flota()
        disponibles = [v for v in flota if v["estado"] == "Disponible"]
        logs.append(f"Unidades disponibles: {len(disponibles)} de {len(flota)} en flota")

        if not disponibles:
            return AgentResult(
                success=False, logs=logs,
                error="❌ Sin recursos: No hay vehículos disponibles en la flota.",
            )

        # Scoring multi-factor
        scored = [(self._score(v, tipo_req, zona_incidente), v) for v in disponibles]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, sel = scored[0]
        eta = self._eta(sel["zona"], zona_incidente)

        logs.append(f"Candidatos evaluados: {len(scored)} — Top score: {best_score}/100")
        logs.append(f"Seleccionado: {sel['id']} ({sel['tipo']}) · Score {best_score}/100")
        logs.append(f"Origen: Zona {sel['zona']} → Destino: {zona_incidente} → ETA {eta} min")
        logs.append(f"Chofer: {sel['chofer']} | Capacidad: {sel.get('capacidad_ton',1)}t")

        # Advertir si no hay del tipo ideal
        if sel["tipo"] != tipo_req:
            logs.append(f"⚠️ Sin {tipo_req} disponibles — usando {sel['tipo']} como alternativa")

        mats = json.loads(sel["materiales"]) if isinstance(sel.get("materiales"), str) else sel.get("materiales", [])

        # Alerta ETA vs tiempo max prioridad
        from config import ZONAS
        tiempos_max = {1: 10, 2: 25, 3: 60, 4: 180}
        t_max = tiempos_max.get(prioridad_num, 60)
        if eta > t_max:
            logs.append(f"⚠️ ETA ({eta} min) supera el tiempo máximo para esta prioridad ({t_max} min)")

        return AgentResult(
            success=True,
            datos={
                "id_vehiculo": sel["id"],
                "tipo_vehiculo": sel["tipo"],
                "chofer": sel["chofer"],
                "zona_origen": sel["zona"],
                "zona_destino": zona_incidente,
                "tiempo_estimado_min": eta,
                "score_asignacion": best_score,
                "materiales_disponibles": mats,
                "descripcion_incidente": descripcion,
                "tipo_requerido": tipo_req,
                "eta_ok": eta <= t_max,
            },
            logs=logs,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE P2: OFICIAL DE SEGURIDAD (REGLAS EXTENDIDAS)
# ─────────────────────────────────────────────────────────────────────────────

class SafetyGuardian:
    """
    Agente P2 — Oficial de Seguridad v3.

    Nuevas reglas respecto a v2:
    - Arco eléctrico (arc flash): distancias y EPP especial
    - Espacio confinado: mínimo 3 trabajadores, ventilación
    - Trabajo en escalera: requiere vigía
    - Zona industrial: coordinación con jefe de planta
    """

    def __init__(self):
        self.nombre = "SafetyGuardian"

    def _hora_nocturna(self) -> bool:
        h = datetime.now().hour
        return h < 6 or h >= 18

    def _es_altura(self, tipo: str) -> bool:
        return tipo in ("Grúa", "Canasta")

    def _chequear(self, desc: str, zona: str, tipo: str, clima: str) -> List[Dict]:
        """Evalúa todas las condiciones y retorna lista de violaciones detectadas."""
        desc_l = desc.lower()
        violations = []

        # 1. Lluvia + trabajo en altura
        if clima in ("Lluvioso", "Tormenta") and self._es_altura(tipo):
            violations.append({
                "regla": "Lluvia + Altura",
                "nivel": "ALTO",
                "msg": "LLUVIA ACTIVA: Trabajo en altura restringido. Requiere autorización de Supervisor y arnés doble.",
                "epp": ["Arnés doble", "Casco con barbuquejo", "Botas dieléctricas", "Guantes aislantes Clase 2"],
            })

        # 2. Alta / Media Tensión
        palabras_at = ["transformador","alta tension","alta tensión","media tension","media tensión",
                       "subestacion","subestación","mt ","at ","kv","línea energizada"]
        if any(p in desc_l for p in palabras_at):
            violations.append({
                "regla": "Alta Tensión",
                "nivel": "CRITICO",
                "msg": "ALTA TENSION: Mínimo 2 técnicos certificados. Verificar distancias de seguridad. Corte previo obligatorio.",
                "epp": ["Guantes dieléctricos Clase 4","Careta facial Clase 4","Ropa ignífuga Cat.2","Detector de tensión"],
            })

        # 3. Arco eléctrico
        if any(p in desc_l for p in ["arco electrico","arco eléctrico","cortocircuito","flash","arc"]):
            violations.append({
                "regla": "Riesgo de Arco Eléctrico",
                "nivel": "CRITICO",
                "msg": "RIESGO DE ARCO: Mantener distancia límite de 1.5m. Usar PPE de arco Cat.4 (40+ cal/cm²).",
                "epp": ["Traje de arco Cat.4 (40 cal/cm²)","Escudo de cara arco","Guantes Clase 00 sobre Clase 4"],
            })

        # 4. Trabajo nocturno
        if self._hora_nocturna():
            violations.append({
                "regla": "Trabajo Nocturno",
                "nivel": "MEDIO",
                "msg": "TRABAJO NOCTURNO: Iluminación mínima 500 lux. Acompañante de seguridad obligatorio.",
                "epp": ["Chaleco reflectante","Linterna de cabeza (3000 lm)","Señalización nocturna"],
            })

        # 5. Zona vial
        if any(p in desc_l for p in ["calle","avenida","av.","via ","vía ","carretera","autopista","interseccion"]):
            violations.append({
                "regla": "Zona Vial",
                "nivel": "ALTO",
                "msg": "ZONA VIAL: Señalizar 50 m. Coordinación con tránsito. Vías de escape definidas.",
                "epp": ["Conos de señalización","Vallas metálicas","Chaleco AR alta visibilidad"],
            })

        # 6. Zona Industrial
        if zona.lower() == "industrial":
            violations.append({
                "regla": "Zona Industrial",
                "nivel": "ALTO",
                "msg": "ZONA INDUSTRIAL: Coordinación obligatoria con Jefe de Planta. Equipo de rescate en sitio.",
                "epp": ["Protectores auditivos","Gafas de seguridad", "Casco industrial Clase E"],
            })

        # 7. Espacio confinado
        if any(p in desc_l for p in ["bóveda","boveda","pozo","subterranea","subterráneo","alcantarilla","cámara subterránea"]):
            violations.append({
                "regla": "Espacio Confinado",
                "nivel": "CRITICO",
                "msg": "ESPACIO CONFINADO: Mínimo 3 trabajadores (1 vigía). Prueba de atmósfera antes de entrar. Ventilación forzada.",
                "epp": ["Detector de gases 4-en-1","Arnés de rescate","Trípode de rescate","Equipo de respiración"],
            })

        # 8. Tormenta eléctrica
        if clima == "Tormenta":
            violations.append({
                "regla": "Tormenta Eléctrica",
                "nivel": "CRITICO",
                "msg": "TORMENTA: Trabajo exterior suspendido hasta estabilización. Si hay actividad eléctrica, evacuar zona.",
                "epp": ["Radio meteorológico","Refugio temporal","Calzado aislante"],
            })

        return violations

    def run(self, asignacion: Dict[str, Any], clima: str, descripcion: str, zona: str) -> AgentResult:
        logs = ["Iniciando evaluación de seguridad..."]
        tipo = asignacion.get("tipo_vehiculo", "")

        violations = self._chequear(descripcion, zona, tipo, clima)
        n = len(violations)

        # EPP base + acumulado de violaciones
        epp = ["Casco de seguridad eléctrico", "Botas de seguridad dieléctricas",
               "Guantes de trabajo", "Lentes de seguridad", "Extintor en vehículo"]
        advertencias = []

        for v in violations:
            logs.append(f"REGLA ACTIVA [{v['nivel']}]: {v['regla']}")
            advertencias.append(v["msg"])
            epp.extend(v["epp"])

        epp = list(dict.fromkeys(epp))  # Dedup preservando orden

        # Nivel de riesgo global (el más alto detectado)
        niveles_orden = {"CRITICO": 4, "ALTO": 3, "MEDIO": 2, "BAJO": 1}
        if violations:
            nivel_max = max(violations, key=lambda x: niveles_orden.get(x["nivel"], 0))
            nivel_riesgo = nivel_max["nivel"]
        else:
            nivel_riesgo = "BAJO"

        if n == 0:
            veredicto = "APROBADO"
            logs.append("✅ Sin violaciones detectadas. Orden APROBADA.")
        else:
            veredicto = "APROBADO_CON_ADVERTENCIAS"
            logs.append(f"⚠️ {n} regla(s) activa(s) — Nivel {nivel_riesgo}. Supervisión obligatoria.")

        logs.append(f"EPP total requerido: {len(epp)} ítems")
        logs.append(f"Veredicto final: {veredicto}")

        return AgentResult(
            success=True,
            datos={
                "veredicto": veredicto,
                "nivel_riesgo": nivel_riesgo,
                "advertencias": advertencias,
                "epp_requerido": epp,
                "clima_evaluado": clima,
                "reglas_activadas": [v["regla"] for v in violations],
                "num_violaciones": n,
            },
            logs=logs,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE P3: ADMINISTRATIVO / REPORTES
# ─────────────────────────────────────────────────────────────────────────────

class AdminBot:
    """Agente P3 — Genera la OT numerada en texto y PDF descargable."""

    @staticmethod
    def generar_numero_ot() -> str:
        return f"OT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    def run(self, descripcion: str, tipo_incidente: str, zona: str,
            asignacion: Dict, validacion: Dict, prioridad: Dict) -> AgentResult:
        logs = ["Generando Orden de Trabajo oficial..."]
        numero_ot = self.generar_numero_ot()
        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        nivel_riesgo = validacion.get("nivel_riesgo", "N/D")
        veredicto    = validacion.get("veredicto", "N/D")
        advertencias = validacion.get("advertencias", [])
        epp          = validacion.get("epp_requerido", [])
        pri          = prioridad.get("nivel", "MEDIA")
        pri_emoji    = prioridad.get("emoji", "")
        pri_tmax     = prioridad.get("tiempo_max_min", "N/D")

        logs.append(f"N° OT: {numero_ot}")
        logs.append(f"Prioridad: {pri_emoji} {pri} | Riesgo: {nivel_riesgo}")

        sep = "=" * 62
        texto = f"""
{sep}
         ORDEN DE TRABAJO — ElectroDispatch AI v3
{sep}
N. OT        : {numero_ot}
Fecha/Hora   : {fecha_hora}
Prioridad    : {pri_emoji} {pri} (respuesta max: {pri_tmax} min)
{sep}

1. DATOS DEL INCIDENTE
   Tipo         : {tipo_incidente}
   Descripcion  : {descripcion}
   Zona         : {zona}
   Clima        : {validacion.get('clima_evaluado','N/D')}

2. ASIGNACION DE RECURSOS
   Vehiculo ID  : {asignacion.get('id_vehiculo','N/D')}
   Tipo         : {asignacion.get('tipo_vehiculo','N/D')}
   Chofer       : {asignacion.get('chofer','N/D')}
   Zona Origen  : {asignacion.get('zona_origen','N/D')}
   ETA          : {asignacion.get('tiempo_estimado_min','?')} minutos
   Score Asig.  : {asignacion.get('score_asignacion','?')}/100
   Materiales   : {', '.join(asignacion.get('materiales_disponibles',[])[:5])}

3. VALIDACION DE SEGURIDAD
   Veredicto    : {veredicto}
   Nivel Riesgo : {nivel_riesgo}
   Reglas act.  : {', '.join(validacion.get('reglas_activadas',['Ninguna']))}
"""
        if advertencias:
            texto += "\n   ADVERTENCIAS OBLIGATORIAS:\n"
            for i, adv in enumerate(advertencias, 1):
                texto += f"   [{i}] {adv}\n"

        texto += "\n4. EPP REQUERIDO (Equipo de Proteccion Personal)\n"
        for item in epp:
            texto += f"   + {item}\n"

        texto += f"""
5. INSTRUCCIONES OPERATIVAS
   - Confirmar llegada al sitio por radio con despachador.
   - Fotografiar el area antes Y despues de la intervencion.
   - Reportar hallazgos adicionales via bot Telegram @tetranutabot.
   - Registrar hora inicio/fin de trabajo en esta orden.
   - Completar Acta de Trabajo y firmar al finalizar.

6. FIRMA Y CONFORMIDAD
   DESPACHADOR: ___________________  TECNICO: ____________________
   SUPERVISOR:  ___________________  HORA CIERRE: ________________

{sep}
"""
        logs.append("Orden de Trabajo generada exitosamente.")
        return AgentResult(
            success=True,
            datos={"numero_ot": numero_ot, "fecha_hora": fecha_hora, "texto_ot": texto},
            logs=logs,
        )

    def generar_pdf(self, texto_ot: str, numero_ot: str, prioridad_num: int = 3) -> Optional[bytes]:
        """Exporta la OT a PDF en memoria. Libre de emojis/unicode."""

        def _lp(t: str) -> str:
            return re.sub(r'[^\x00-\xFF]', '', t)

        colores_prioridad = {1: (180,20,40), 2: (180,100,10), 3: (30,100,190), 4: (15,140,90)}
        color_pri = colores_prioridad.get(prioridad_num, (30,100,190))

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Encabezado
            pdf.set_fill_color(5, 10, 20)
            pdf.rect(0, 0, 210, 34, "F")
            pdf.set_fill_color(*color_pri)
            pdf.rect(0, 31, 210, 3, "F")
            pdf.set_text_color(233, 184, 74)
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_y(8)
            pdf.cell(0, 10, "ELECTRODISPATCH AI", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(160, 190, 220)
            pdf.cell(0, 7, "Sistema Multi-Agente de Despacho Electrico  |  v3.0  |  Bot: @tetranutabot",
                     align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)

            # Título
            pdf.set_text_color(5, 10, 20)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 9, f"ORDEN DE TRABAJO  {_lp(numero_ot)}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*color_pri)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Cuerpo
            pdf.set_font("Courier", "", 9)
            pdf.set_text_color(30, 35, 45)

            for linea in texto_ot.splitlines():
                lc = _lp(linea)
                ls = lc.strip()
                if ls and ls[0].isdigit() and ". " in ls[:3]:
                    pdf.ln(2)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_fill_color(235, 240, 255)
                    pdf.set_x(10)
                    pdf.cell(190, 7, f"  {ls}", fill=True, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Courier", "", 9)
                elif ls.startswith("="):
                    pdf.set_draw_color(60, 80, 120)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(2)
                else:
                    safe = lc.encode("latin-1", errors="replace").decode("latin-1")
                    pdf.set_x(10)
                    pdf.multi_cell(190, 5, safe)

            # Pie
            pdf.set_y(-18)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(140, 150, 160)
            pdf.cell(0, 5,
                f"Generado por ElectroDispatch AI v3  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  @tetranutabot",
                align="C")

            return bytes(pdf.output())
        except Exception as e:
            print(f"[AdminBot] Error PDF: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISIS DE COBERTURA DE ZONAS (self-improvement)
# ─────────────────────────────────────────────────────────────────────────────

class ZoneCoverageAnalyzer:
    """
    Analiza la distribución de la flota disponible vs la demanda histórica
    de incidentes por zona. Genera recomendaciones de pre-posicionamiento.
    """

    def analizar(self, db: SQLiteManager) -> Dict[str, Any]:
        flota = db.get_flota()
        incidentes = db.get_incidentes(limit=100)

        # Disponibles por zona
        cobertura = {}
        for v in flota:
            z = v["zona"]
            if z not in cobertura:
                cobertura[z] = {"disponibles": 0, "total": 0, "incidentes": 0}
            cobertura[z]["total"] += 1
            if v["estado"] == "Disponible":
                cobertura[z]["disponibles"] += 1

        # Incidentes por zona
        for inc in incidentes:
            z = inc.get("zona", "")
            if z in cobertura:
                cobertura[z]["incidentes"] += 1

        # Score de cobertura: disponibles / (incidentes + 1) — mayor = mejor
        recomendaciones = []
        for zona, info in cobertura.items():
            score = info["disponibles"] / (info["incidentes"] + 1)
            info["score"] = round(score, 2)
            if score < 0.3 and info["incidentes"] > 0:
                recomendaciones.append(
                    f"⚠️ {zona}: baja cobertura ({info['disponibles']} disp. / {info['incidentes']} incid.) "
                    f"— considerar re-posicionar vehículo desde zona adyacente."
                )

        zonas_criticas = [z for z, i in cobertura.items() if i.get("score", 1) < 0.3]

        return {
            "cobertura": cobertura,
            "recomendaciones": recomendaciones,
            "zonas_criticas": zonas_criticas,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL (P0→P1→P2→P3)
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_pipeline(
    descripcion: str,
    tipo_incidente: str,
    zona: str,
    clima: str,
    db: SQLiteManager,
    fuente: str = "web",
) -> Dict[str, Any]:
    """
    Orquesta: PriorityClassifier → LogisticsManager → SafetyGuardian → AdminBot.
    Persiste la OT en SQLite y retorna todos los resultados.
    """
    res: Dict[str, Any] = {
        "exito": False,
        "agente0": None, "agente1": None,
        "agente2": None, "agente3": None,
    }

    # P0 — Prioridad
    a0 = PriorityClassifier()
    r0 = a0.run(descripcion, tipo_incidente)
    res["agente0"] = r0

    # P1 — Logística
    a1 = LogisticsManager(db=db)
    r1 = a1.run(descripcion, zona, tipo_incidente, r0.datos.get("numero", 3))
    res["agente1"] = r1
    if not r1.success:
        return res

    # P2 — Seguridad
    a2 = SafetyGuardian()
    r2 = a2.run(r1.datos, clima, descripcion, zona)
    res["agente2"] = r2

    # P3 — AdminBot
    a3 = AdminBot()
    r3 = a3.run(descripcion, tipo_incidente, zona, r1.datos, r2.datos, r0.datos)
    res["agente3"] = r3
    res["admin_bot"] = a3
    res["exito"] = True

    # Persistir en BD
    try:
        db.agregar_incidente({
            "numero_ot":         r3.datos["numero_ot"],
            "descripcion":       descripcion,
            "tipo_incidente":    tipo_incidente,
            "zona":              zona,
            "clima":             clima,
            "vehiculo_asignado": r1.datos["id_vehiculo"],
            "chofer":            r1.datos["chofer"],
            "eta_min":           r1.datos["tiempo_estimado_min"],
            "nivel_riesgo":      r2.datos["nivel_riesgo"],
            "veredicto":         r2.datos["veredicto"],
            "advertencias":      r2.datos["advertencias"],
            "epp_requerido":     r2.datos["epp_requerido"],
            "texto_ot":          r3.datos["texto_ot"],
            "fuente":            fuente,
        })
        if r2.datos["nivel_riesgo"] in ("CRITICO", "ALTO"):
            db.agregar_alerta(
                tipo="Despacho de riesgo elevado",
                mensaje=f"OT {r3.datos['numero_ot']} — {zona} — {r2.datos['nivel_riesgo']}",
                zona=zona,
                nivel=r2.datos["nivel_riesgo"],
            )
    except Exception as e:
        print(f"[Pipeline] Error persistiendo: {e}")

    return res
