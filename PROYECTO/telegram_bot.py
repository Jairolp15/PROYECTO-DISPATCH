"""
telegram_bot.py — Bot de Telegram para ElectroDispatch AI v3.1 (Zulia)
Bot: @tetranutabot

Funcionalidades:
   /start        — Bienvenida e instrucciones
   /estado       — Resumen COMPLETO de flota en tiempo real
   /stock        — Ver ítems con bajo stock en taller
   /buscar <item> — Buscar disponibilidad de material
   /info         — Información del sistema y cobertura
   /ayuda        — Lista de comandos
   /ot <desc> | <zona> — Crear OT directamente (Ej: /ot Falla | Maracaibo)

Ejecutar en terminal separada:
   python telegram_bot.py
"""
import asyncio
import io
import logging
import os
import sys

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)

# Agregar el directorio del proyecto al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import SQLiteManager
from agents import ejecutar_pipeline

from config import TELEGRAM_TOKEN as TOKEN
if not TOKEN:
    print("ERROR: TELEGRAM_TOKEN no encontrado en .env a través de config.py")
    sys.exit(1)

# Usuarios autorizados (dejar vacío para permitir todos)
USUARIOS_AUTORIZADOS: list = []  # Ej: ["123456789", "987654321"]

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ElectroBot")

db = SQLiteManager()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _esta_autorizado(update: Update) -> bool:
    if not USUARIOS_AUTORIZADOS:
        return True
    return str(update.effective_user.id) in USUARIOS_AUTORIZADOS

def _nombre_usuario(update: Update) -> str:
    u = update.effective_user
    return u.full_name or u.username or str(u.id)

def _resumen_flota() -> str:
    """Genera un resumen detallado de toda la flota."""
    flota = db.get_flota()
    disponibles = [v for v in flota if v["estado"] == "Disponible"]
    ocupados    = [v for v in flota if v["estado"] == "Ocupado"]
    mant        = [v for v in flota if v["estado"] == "Mantenimiento"]

    lineas = [
        "🚛 *Estado Global de la Flota — Zulia AI*\n",
        f"✅ *Disponibles* : {len(disponibles)}",
        f"🔴 *Ocupados*    : {len(ocupados)}",
        f"🔧 *Mant.*       : {len(mant)}",
        f"📊 *Total*       : {len(flota)}\n",
        "📍 *Distribución por Zona:*",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    for v in flota:
        emoji = "🟢" if v['estado']=="Disponible" else "🔴" if v['estado']=="Ocupado" else "🔧"
        lineas.append(f"{emoji} `{v['id']}` — {v['zona']} — {v['tipo']}")
        # Agregar botón de cambio de estado en el resumen no es fácil sin un teclado por vehículo,
        # así que usaremos una lista con botones abajo o un comando de gestión.

    return "\n".join(lineas)

def _get_botones_gestion_flota():
    """Genera botones para seleccionar un vehículo y cambiar su estado."""
    db_local = SQLiteManager()
    flota = db_local.get_flota()
    btns = []
    for v in flota:
        btns.append([InlineKeyboardButton(f"🔧 Gestionar {v['id']} ({v['estado']})", callback_data=f"gest_v_{v['id']}")])
    btns.append([InlineKeyboardButton("⬅️ Volver", callback_data="ayuda")])
    return InlineKeyboardMarkup(btns)

async def _show_inventory_page(query, page: int):
    """Muestra una página del inventario con controles de entrada/salida."""
    logger.info(f"Bot: Mostrando página de inventario {page}")
    db_local = SQLiteManager()
    items = db_local.get_inventario()
    
    if not items:
        logger.warning("Bot: Inventario vacío al intentar mostrar página.")
        await query.edit_message_text("📭 El inventario está vacío.", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="ayuda")]]))
        return

    per_page = 5
    total_pages = (len(items) - 1) // per_page + 1
    page = max(0, min(page, total_pages - 1))
    
    start = page * per_page
    end = start + per_page
    batch = items[start:end]
    
    texto = [
        f"📦 *Inventario (Pág {page+1}/{total_pages})*\n",
        "_Usa los botones para +/- 1 unidad:_"
    ]
    
    btns = []
    for it in batch:
        m = "🔴" if it["cantidad"] <= it["minimo_stock"] else "🟢"
        texto.append(f"{m} `{it['item']}`: {it['cantidad']} {it['unidad']}")
        btns.append([
            InlineKeyboardButton(f"➕ {it['item'][:12]}", callback_data=f"inv_mov_ent_{it['id']}"),
            InlineKeyboardButton(f"➖ {it['item'][:12]}", callback_data=f"inv_mov_sal_{it['id']}")
        ])
    
    # Navegación
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Ant", callback_data=f"inv_page_{page-1}"))
    if page < total_pages - 1: nav.append(InlineKeyboardButton("Sig ➡️", callback_data=f"inv_page_{page+1}"))
    if nav: btns.append(nav)
    
    btns.append([InlineKeyboardButton("⬅️ Volver al Menú", callback_data="ayuda")])
    
    await query.edit_message_text("\n".join(texto), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(btns))

# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS DE COMANDOS
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida con botones de acción rápida."""
    nombre = _nombre_usuario(update)
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚛 Ver Estado de Flota", callback_data="estado")],
        [InlineKeyboardButton("📦 Ver Inventario Taller", callback_data="inventario")],
        [InlineKeyboardButton("📋 Ayuda / Comandos",   callback_data="ayuda")],
    ])
    texto = (
        f"⚡ *Bienvenido a ElectroDispatch AI*, {nombre}!\n\n"
        "Soy el asistente de despacho eléctrico. Puedo ayudarte a:\n\n"
        "📸 *Enviar fotos* de incidentes — se cargan automáticamente en el panel de control\n"
        "📝 *Enviar texto* describiendo un incidente\n"
        "🔧 `/ot <descripcion> | <zona>` — Crear Orden de Trabajo\n"
        "📊 `/estado` — Ver disponibilidad de flota\n"
        "❓ `/ayuda` — Lista de comandos\n\n"
        "_Panel web: corre la app Streamlit en tu PC_"
    )
    await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=teclado)


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado de la flota en tiempo real (teclado interactivo)."""
    logger.info(f"Bot: Comando /estado por {update.effective_user.full_name}")
    await update.message.reply_text(
        f"{_resumen_flota()}\n\n_Selecciona para gestionar:_ ",
        parse_mode="Markdown",
        reply_markup=_get_botones_gestion_flota()
    )


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📋 *Comandos de ElectroDispatch:*\n\n"
        "⚡ *Operaciones:*\n"
        "`/estado` — Estado detallado de flota\n"
        "`/ot desc | zona` — Crear Orden de Trabajo\n"
        "   _Ej: /ot Falla transformador | Cabimas_\n\n"
        "📦 *Inventario:*\n"
        "`/stock` — Ver materiales críticos\n"
        "`/buscar <nombre>` — Buscar material específico\n\n"
        "❓ *Otros:*\n"
        "`/info` — Info del sistema\n"
        "`/start` — Menú principal\n\n"
        "📸 *Reportes:* Envía fotos o texto directamente para reportar incidentes."
    )
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚛 Ver Flota", callback_data="estado")],
        [InlineKeyboardButton("📦 Ver Stock", callback_data="stock")],
    ])
    await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=teclado)


async def cmd_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ot <descripcion> | <zona>
    Crea una OT directamente desde Telegram usando el pipeline de agentes.
    """
    if not _esta_autorizado(update):
        await update.message.reply_text("⛔ No autorizado.")
        return

    texto_raw = " ".join(context.args)
    if "|" not in texto_raw:
        await update.message.reply_text(
            "⚠️ Formato: `/ot descripcion | zona`\n"
            "Ejemplo: `/ot Transformador averiado | Norte`",
            parse_mode="Markdown"
        )
        return

    partes = texto_raw.split("|", 1)
    descripcion = partes[0].strip()
    zona = partes[1].strip() if len(partes) > 1 else "Centro"

    # Validar zona
    from config import ZONAS
    if zona not in ZONAS:
        zona = "Centro"

    await update.message.reply_text(f"⚙️ Procesando OT para *{zona}*...", parse_mode="Markdown")

    resultado = ejecutar_pipeline(
        descripcion=descripcion,
        tipo_incidente="Emergencia — reporte Telegram",
        zona=zona,
        clima="Soleado",
        db=db,
        fuente="telegram",
    )

    if not resultado["exito"]:
        err = resultado["agente1"].error if resultado["agente1"] else "Error desconocido"
        await update.message.reply_text(f"❌ {err}")
        return

    a1 = resultado["agente1"].datos
    a2 = resultado["agente2"].datos
    a3 = resultado["agente3"].datos

    respuesta = (
        f"✅ *Orden de Trabajo Generada*\n\n"
        f"📋 N° OT       : `{a3['numero_ot']}`\n"
        f"🚛 Vehículo    : {a1['id_vehiculo']} ({a1['tipo_vehiculo']})\n"
        f"👤 Chofer      : {a1['chofer']}\n"
        f"⏱️ ETA         : {a1['tiempo_estimado_min']} minutos\n"
        f"🛡️ Riesgo      : *{a2['nivel_riesgo']}*\n"
        f"📍 Zona        : {zona}\n\n"
        f"_Gestión finalizada por el Pipeline de Agentes._"
    )
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Ver en Dashboard", url="http://localhost:8501")],
        [InlineKeyboardButton("🔄 Nueva OT", callback_data="ayuda")],
    ])
    await update.message.reply_text(respuesta, parse_mode="Markdown", reply_markup=teclado)

async def cmd_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ítems con stock bajo."""
    bajo = db.get_items_bajo_stock()
    if not bajo:
        await update.message.reply_text("✅ *Todo en orden.* No hay ítems con bajo stock.", parse_mode="Markdown")
        return
    
    lineas = ["⚠️ *Alerta de Inventario (Bajo Stock):*\n"]
    for it in bajo[:10]:
        lineas.append(f"• `{it['item']}`: {it['cantidad']} {it['unidad']} (Min: {it['minimo_stock']})")
    
    if len(bajo) > 10:
        lineas.append(f"\n_... y {len(bajo)-10} ítems más._")
    
    teclado = InlineKeyboardMarkup([[InlineKeyboardButton("📦 Ver Todo el Inventario", callback_data="buscar_todo")]])
    await update.message.reply_text("\n".join(lineas), parse_mode="Markdown", reply_markup=teclado)

async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca un ítem en el inventario."""
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("🔎 Uso: `/buscar <nombre_del_material>`", parse_mode="Markdown")
        return

    items = db.get_inventario()
    resultados = [i for i in items if query.lower() in i["item"].lower()]
    
    if not resultados:
        await update.message.reply_text(f"❌ No se encontró nada parecido a '*{query}*'.", parse_mode="Markdown")
        return
    
    texto = [f"🔎 *Resultados para '{query}':*\n"]
    for it in resultados[:8]:
        estado = "🔴" if it['cantidad'] <= it['minimo_stock'] else "🟢"
        texto.append(f"{estado} *{it['item']}* — {it['cantidad']} {it['unidad']}\n   📍 {it.get('ubicacion','Taller')}")

    await update.message.reply_text("\n".join(texto), parse_mode="Markdown")

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import ZONAS, APP_VERSION
    stats = db.get_estadisticas()
    texto = (
        f"⚡ *ElectroDispatch AI v{APP_VERSION}*\n"
        f"📍 *Región:* Estado Zulia, Venezuela\n\n"
        f"📈 *Actividad:* {stats['total_ot']} OTs totales\n"
        f"🚛 *Flota:* {stats['total_flota']} unidades activas\n"
        f"🏢 *Zonas:* {', '.join(ZONAS[:5])}...\n\n"
        f"_Sistema multi-agente operando en tiempo real._"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS DE MENSAJES
# ─────────────────────────────────────────────────────────────────────────────

async def handle_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe una foto (posiblemente con pie de foto), la descarga y
    la persiste en la tabla reportes_telegram de SQLite.
    """
    u = update.effective_user
    caption = update.message.caption or "Sin descripcion"

    # Descargar la foto en máxima resolución
    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    foto_bytes = buf.getvalue()
    foto_filename = f"foto_{photo.file_id[:12]}.jpg"

    reporte_id = db.agregar_reporte_telegram(
        chat_id=str(u.id),
        username=u.username or "",
        nombre=u.full_name or str(u.id),
        tipo="foto",
        contenido=caption,
        foto_bytes=foto_bytes,
        foto_filename=foto_filename,
    )

    logger.info(f"Foto recibida de {u.full_name} (reporte #{reporte_id})")

    await update.message.reply_text(
        f"📸 Foto recibida y registrada (ID #{reporte_id})\n"
        f"_Ya puedes verla en el panel web → Central Telegram_",
        parse_mode="Markdown"
    )


async def handle_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe un mensaje de texto y lo guarda como reporte de incidente.
    Ignora mensajes que son comandos.
    """
    texto = update.message.text
    if texto.startswith("/"):
        return  # Ignorar comandos no reconocidos

    u = update.effective_user
    reporte_id = db.agregar_reporte_telegram(
        chat_id=str(u.id),
        username=u.username or "",
        nombre=u.full_name or str(u.id),
        tipo="texto",
        contenido=texto,
    )

    logger.info(f"Texto de {u.full_name}: {texto[:60]}")

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Ver en panel web", url="http://localhost:8502")],
    ])
    await update.message.reply_text(
        f"📝 Reporte registrado (#{reporte_id})\n"
        f"_Visible en panel web → Central Telegram_\n\n"
        f"Para crear una OT directamente usa:\n`/ot {texto[:40]}... | Zona`",
        parse_mode="Markdown",
        reply_markup=teclado,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK QUERIES (botones inline)
# ─────────────────────────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.info(f"Bot: Callback recibido: {query.data} de {update.effective_user.full_name}")
    await query.answer()
    if query.data == "estado":
        await query.edit_message_text(f"{_resumen_flota()}\n\n_Selecciona para cambiar estado:_ ", 
                                     parse_mode="Markdown", reply_markup=_get_botones_gestion_flota())
    elif query.data.startswith("gest_v_"):
        vid = query.data.replace("gest_v_", "")
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Disponible", callback_data=f"set_est_{vid}_Disponible")],
            [InlineKeyboardButton("🔴 Ocupado", callback_data=f"set_est_{vid}_Ocupado")],
            [InlineKeyboardButton("🔧 Mantenimiento", callback_data=f"set_est_{vid}_Mantenimiento")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="estado")]
        ])
        await query.edit_message_text(f"🚜 *Gestionar:* `{vid}`\nSelecciona el nuevo estado:", 
                                     parse_mode="Markdown", reply_markup=btns)
    elif query.data.startswith("set_est_"):
        _, _, vid, nest = query.data.split("_")
        db.update_estado_vehiculo(vid, nest)
        await query.edit_message_text(f"✅ Estado de `{vid}` actualizado a *{nest}*.", 
                                     parse_mode="Markdown", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver a Flota", callback_data="estado")]]))
    elif query.data == "inventario":
        # Mostrar resumen de inventario con paginación
        await _show_inventory_page(query, 0)
    elif query.data.startswith("inv_page_"):
        page = int(query.data.replace("inv_page_", ""))
        await _show_inventory_page(query, page)
    elif query.data.startswith("inv_mov_"):
        # inv_mov_ent_1 or inv_mov_sal_1
        _, _, type, iid = query.data.split("_")
        delta = 1 if type == "ent" else -1
        db.ajustar_cantidad(int(iid), delta)
        # Volver a mostrar la página (necesitamos saber qué página era, por ahora refrescamos)
        await query.answer(f"{'✅ Entrada' if delta>0 else '🚨 Salida'} registrada (+1)")
        await _show_inventory_page(query, 0) 
    elif query.data == "ayuda_buscar":
        await query.edit_message_text("🔎 Para buscar un material, usa el comando:\n\n`/buscar <nombre>`\n\n_Ejemplo: /buscar cable_", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="inventario")]]))
    elif query.data == "ayuda":
        await cmd_ayuda(update, context)
    elif query.data == "stock":
        await cmd_stock(update, context)
    elif query.data == "buscar_todo":
        await update.callback_query.message.reply_text("💡 Usa `/buscar <nombre>` para encontrar materiales específicos.")


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLER
# ─────────────────────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error en update: {context.error}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  ElectroDispatch AI — Bot de Telegram @tetranutabot")
    print("=" * 55)
    print(f"  DB: {db.db_path}")
    print("  Iniciando polling... (Ctrl+C para detener)")
    print("=" * 55)

    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("ayuda",  cmd_ayuda))
    app.add_handler(CommandHandler("ot",     cmd_ot))
    app.add_handler(CommandHandler("stock",  cmd_stock))
    app.add_handler(CommandHandler("buscar", cmd_buscar))
    app.add_handler(CommandHandler("info",   cmd_info))

    # Fotos y texto
    app.add_handler(MessageHandler(filters.PHOTO,   handle_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_texto))

    # Callbacks de botones
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Error handler
    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
