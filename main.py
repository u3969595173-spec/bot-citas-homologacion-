# -*- coding: utf-8 -*-
"""
Bot de Telegram para Citas de Homologación
Sistema de monitoreo y auto-reserva de citas
"""

import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime

# Configurar OpenSSL para permitir renegociación legacy
os.environ['OPENSSL_CONF'] = os.path.join(os.path.dirname(__file__), 'openssl.cnf')

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from monitor import CitasMonitor
from user_data import UserDataManager
from health_server import start_health_server
from daily_heartbeat import daily_heartbeat
from queue_manager import CitasQueue
from auto_fill import auto_fill_appointment
from commands_extra import pausar_command, reanudar_command, test_command, stats_command, cola_command, confirmar_cita_command, cancelar_cola_command

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estado global
monitor = None
usuarios_activos = {}  # {user_id: {'datos': {...}, 'notified': False}}
user_data_manager = UserDataManager()
citas_queue = CitasQueue()

# Estados para conversación de registro de datos
NOMBRE, APELLIDO, DOCUMENTO, EMAIL, TELEFONO = range(5)


async def cita_disponible_handler(dates):
    """Callback cuando se detecta cita disponible - Sistema FIFO (cola)"""
    logger.warning(f"🎯 CITA DISPONIBLE: {dates}")
    
    date_strings = [d["date"] if isinstance(d, dict) else str(d) for d in dates]
    first_date = date_strings[0] if date_strings else ""
    
    # 🔥 OBTENER SIGUIENTE USUARIO EN LA COLA (FIFO)
    next_user_id = citas_queue.get_next_user()
    
    if not next_user_id:
        logger.warning("⚠️ No hay usuarios en la cola")
        # Notificar admin
        if ADMIN_USER_ID:
            await application.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"🎯 **CITA DISPONIBLE** pero no hay usuarios en cola\n\n📅 {', '.join(date_strings)}"
            )
        return
    
    logger.info(f"👤 Procesando usuario #{next_user_id} (primero en cola)")
    
    try:
        user_info = user_data_manager.get_user_data(next_user_id)
        if not user_info:
            logger.error(f"❌ Usuario {next_user_id} no tiene datos registrados")
            citas_queue.remove_user(next_user_id)  # Sacarlo de la cola
            return
        
        # Preparar datos para auto-llenado
        fill_data = {
            'name': f"{user_info['nombre']} {user_info['apellido']}",
            'document': user_info['documento'],
            'email': user_info['email'],
            'phone': user_info['telefono']
        }
        
        # 🤖 INTENTAR AUTO-LLENADO AUTOMÁTICO
        logger.info(f"🤖 Iniciando auto-llenado para {fill_data['name']}")
        
        try:
            result = await auto_fill_appointment(fill_data, first_date)
            
            if result['success']:
                # ✅ ÉXITO - Reserva completada automáticamente
                confirmation = result.get('confirmation', 'COMPLETADO')
                screenshot_path = result.get('screenshot', '')
                
                success_msg = (
                    f"🎉 **¡RESERVA COMPLETADA AUTOMÁTICAMENTE!**\n\n"
                    f"📅 Fecha: {first_date}\n"
                    f"🔢 Confirmación: **{confirmation}**\n\n"
                    f"📋 **Tus datos:**\n"
                    f"👤 Nombre: {fill_data['name']}\n"
                    f"🆔 Documento: {fill_data['document']}\n"
                    f"📧 Email: {fill_data['email']}\n"
                    f"📞 Teléfono: {fill_data['phone']}\n\n"
                    f"✅ Revisa tu email para más detalles.\n"
                    f"📞 **Soporte:** +34 936 07 56 41"
                )
                
                await application.bot.send_message(chat_id=next_user_id, text=success_msg)
                
                # Enviar screenshot si existe
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        await application.bot.send_photo(
                            chat_id=next_user_id, 
                            photo=open(screenshot_path, 'rb'), 
                            caption="📸 Captura de la confirmación"
                        )
                    except Exception as e:
                        logger.error(f"Error enviando screenshot al usuario: {e}")
                
                # Notificar admin con screenshot
                if ADMIN_USER_ID:
                    admin_msg = (
                        f"✅ **AUTO-RESERVA EXITOSA**\n\n"
                        f"👤 {fill_data['name']}\n"
                        f"🆔 ID: {next_user_id}\n"
                        f"📅 Fecha: {first_date}\n"
                        f"🔢 Confirmación: **{confirmation}**"
                    )
                    await application.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_msg)
                    
                    if screenshot_path and os.path.exists(screenshot_path):
                        try:
                            await application.bot.send_photo(
                                chat_id=ADMIN_USER_ID,
                                photo=open(screenshot_path, 'rb'),
                                caption=f"📸 Confirmación - {fill_data['name']}"
                            )
                        except Exception as e:
                            logger.error(f"Error enviando screenshot al admin: {e}")
                
                # ✅ MARCAR COMO PROCESADO Y SACAR DE LA COLA
                citas_queue.mark_processed(next_user_id, first_date)
                if next_user_id in usuarios_activos:
                    del usuarios_activos[next_user_id]
                
                logger.info(f"✅ Usuario {next_user_id} procesado exitosamente y removido de la cola")
                return  # ✅ Éxito, terminar
                
        except Exception as e:
            logger.error(f"❌ Error en auto-llenado: {e}")
            # Enviar screenshot de error al admin si existe
            if 'result' in locals() and result and 'screenshot' in result:
                screenshot_path = result.get('screenshot')
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        await application.bot.send_photo(
                            chat_id=ADMIN_USER_ID,
                            photo=open(screenshot_path, 'rb'),
                            caption=f"❌ Error auto-llenado\n👤 {fill_data['name']} (ID: {next_user_id})\n{str(e)[:200]}"
                        )
                    except:
                        pass
        
        # 🔄 RESPALDO MANUAL - Si auto-llenado falló
        logger.warning(f"⚠️ Auto-llenado falló para {next_user_id}, enviando notificación manual")
        
        mensaje = (
            f"🎯 **¡CITA DISPONIBLE!**\n\n"
            f"⚠️ El auto-llenado no pudo completarse.\n"
            f"Por favor, **reserva manualmente AHORA**:\n\n"
            f"📅 Fechas: {', '.join(date_strings)}\n\n"
            f"📋 **Tus datos para copiar:**\n"
            f"👤 Nombre: `{fill_data['name']}`\n"
            f"🆔 Documento: `{fill_data['document']}`\n"
            f"📧 Email: `{fill_data['email']}`\n"
            f"📞 Teléfono: `{fill_data['phone']}`\n\n"
            f"⚡ **¡ACTÚA RÁPIDO!**\n\n"
            f"🔗 https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/\n\n"
            f"📞 **Soporte:** +34 936 07 56 41\n\n"
            f"💡 Usa /confirmar cuando consigas la cita"
        )
        
        await application.bot.send_message(chat_id=next_user_id, text=mensaje)
        
        # Notificar admin que se envió manual
        if ADMIN_USER_ID:
            await application.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"⚠️ **NOTIFICACIÓN MANUAL ENVIADA**\n\n👤 {fill_data['name']} (ID: {next_user_id})\n📅 {first_date}\n\n❌ Auto-llenado falló"
            )
        
        # NO remover de la cola - darle oportunidad en la próxima cita
        logger.info(f"ℹ️ Usuario {next_user_id} permanece en cola para próxima cita")
        
    except Exception as e:
        logger.error(f"❌ Error procesando usuario {next_user_id}: {e}")
        if ADMIN_USER_ID:
            try:
                await application.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=f"❌ **ERROR PROCESANDO USUARIO**\n\nID: {next_user_id}\nError: {str(e)[:200]}"
                )
            except:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    logger.info(f"Usuario {username} ({user_id}) inició el bot")
    
    has_data = user_data_manager.has_complete_data(user_id)
    data_status = "✅ Registrados" if has_data else "❌ Sin registrar"
    
    await update.message.reply_text(
        f"👋 ¡Bienvenido al Bot de Citas de Homologación!\n\n"
        f"🎯 Este bot monitorea 24/7 la disponibilidad de citas y te avisa instantáneamente.\n\n"
        f"📋 **Comandos disponibles:**\n"
        f"/datos - Registrar tus datos personales\n"
        f"/registrar - Activar monitoreo de citas\n"
        f"/status - Ver estado del monitor\n"          f"/pausar - Pausar monitoreo temporalmente\n"
          f"/reanudar - Reanudar monitoreo\n"
          f"/test - Probar notificaciones\n"
          f"/stats - Estad�sticas del bot\n"          f"/cola - Ver tu posici�n en la cola\n"          f"/confirmar - Confirmar que conseguiste cita\n"
          f"/cancelar - Salir de la cola\n"
        f"/mistats - Ver mis datos registrados\n"
        f"/stop - Detener monitoreo\n\n"
        f"📝 Tus datos: {data_status}\n\n"
        f"💡 El sistema revisa:\n"
        f"• Cada 0.1 segundos (modo ULTRA - 10 veces/seg)\n\n"
        f"📞 **Soporte:** +34 936 07 56 41\n\n"
        f"⚠️ Registra tus datos con /datos antes de activar el monitoreo.\n\n"
        f"User ID: `{user_id}`"
    )


async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /registrar - Activar monitoreo"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Verificar si tiene datos registrados
    if not user_data_manager.has_complete_data(user_id):
        await update.message.reply_text(
            "⚠️ **Necesitas registrar tus datos primero**\n\n"
            "Usa /datos para registrar:\n"
            "• Nombre y Apellido\n"
            "• NIE/DNI/Pasaporte\n"
            "• Email\n"
            "• Teléfono\n\n"
            "Estos datos se usarán para reservar automáticamente cuando aparezca una cita.\n\n"
            "📞 **Soporte:** +34 936 07 56 41"
        )
        return

    # Agregar a la cola de la base de datos
    position = citas_queue.add_user(user_id)
    # Nota: position puede ser 0 por error SQL menor, pero usuario s� se agrega
    if position is None or position < 0:
        await update.message.reply_text(
            " **Error al agregar a la cola**\n\n"
            "Por favor, intenta de nuevo m�s tarde."
        )
        return
    
    # Si position es 0, significa que hubo un warning pero s� se agreg�
    if position == 0:
        position = 1  # Asignar posici�n por defecto

    # Registrar usuario en memoria
    usuarios_activos[user_id] = {
        'username': username,
        'fecha_registro': datetime.now().isoformat(),
        'notified': False
    }

    logger.info(f"Usuario {username} ({user_id}) registrado para monitoreo - Posición en cola: {position}")

    keyboard = [
        [InlineKeyboardButton("📊 Ver Estado", callback_data="btn_status")],
        [InlineKeyboardButton("📋 Mi Posición en Cola", callback_data="btn_cola")],
        [InlineKeyboardButton("🔴 Pausar Monitoreo", callback_data="btn_stop")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ ¡Registrado correctamente!\n\n"
        f"📍 **Posición en cola: #{position}**\n\n"
        f"🔍 El bot está monitoreando citas 24/7.\n"
        f"📱 Recibirás notificación instantánea cuando aparezca una cita.\n"
        f"🤖 El bot intentará reservarla automáticamente con tus datos.\n\n"
        f"⚡ El bot revisa cada 0.1 segundos (10 veces por segundo).\n\n"
        f"📞 **Soporte:** +34 936 07 56 41\n\n"
        f"👇 Acciones rápidas:",
        reply_markup=reply_markup
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Ver estado del monitor"""
    if not monitor or not monitor.running:
        await update.message.reply_text(
            "❌ El monitor no está activo.\n"
            "Contacta al administrador."
        )
        return
    
    stats = monitor.get_stats()
    now = datetime.now()
    
    # Determinar modo actual
    if 12 <= now.hour < 14:
        modo = "⚡ MODO TURBO (0.3s)"
    elif now.hour == 11 and now.minute >= 55:
        modo = "🔥 PRE-TURBO (1s)"
    else:
        modo = "💤 Modo normal (30s)"
    
    user_id = update.effective_user.id
    is_registered = user_id in usuarios_activos
    has_data = user_data_manager.has_complete_data(user_id)
    
    keyboard = []
    if has_data and not is_registered:
        keyboard.append([InlineKeyboardButton("🟢 Activar Monitoreo", callback_data="btn_registrar")])
    if is_registered:
        keyboard.append([InlineKeyboardButton("📋 Ver Mi Posición", callback_data="btn_cola")])
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="btn_start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 **Estado del Monitor**\n\n"
        f"🔍 Estado: {'✅ Activo' if stats['running'] else '❌ Inactivo'}\n"
        f"⏱ Modo actual: {modo}\n"
        f"🔢 Checks realizados: {stats['checks_count']}\n"
        f"🕐 Último check: {stats['last_check']}\n"
        f"👤 Tu estado: {'✅ Registrado' if is_registered else '❌ No registrado'}\n\n"
        f"👥 Usuarios activos: {len(usuarios_activos)}\n\n"
        f"💡 El bot revisa la API cada {stats['current_interval']}s",
        reply_markup=reply_markup
    )


async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stop - Detener monitoreo para el usuario"""
    user_id = update.effective_user.id
    
    if user_id in usuarios_activos:
        del usuarios_activos[user_id]
        await update.message.reply_text(
            "✅ Has sido eliminado del monitoreo.\n"
            "Usa /registrar si quieres volver a activarlo."
        )
    else:
        await update.message.reply_text(
            "⚠️ No estabas registrado en el sistema."
        )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /admin - Estadísticas completas (solo admin)"""
    user_id = update.effective_user.id
    
    if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ No tienes permisos de administrador.")
        return
    
    stats = monitor.get_stats() if monitor else {}
    
    # Listar usuarios con sus datos
    users_info = []
    for uid, data in usuarios_activos.items():
        user_data = user_data_manager.get_user_data(uid)
        if user_data:
            users_info.append(
                f"👤 **{data['username']}** (ID: {uid})\n"
                f"   • Nombre: {user_data['nombre']} {user_data['apellido']}\n"
                f"   • Doc: {user_data['documento']}\n"
                f"   • Email: {user_data['email']}\n"
                f"   • Tel: {user_data['telefono']}\n"
            )
        else:
            users_info.append(f"👤 {data['username']} (ID: {uid}) - Sin datos")
    
    users_text = "\n".join(users_info) if users_info else "Ninguno"
    
    await update.message.reply_text(
        f"👨‍💼 **Panel de Administración**\n\n"
        f"📊 Monitor: {'✅ Activo' if stats.get('running') else '❌ Inactivo'}\n"
        f"🔢 Total checks: {stats.get('checks_count', 0)}\n"
        f"⏱ Intervalo: {stats.get('current_interval', 0)}s\n"
        f"👥 Usuarios registrados: {len(usuarios_activos)}\n\n"
        f"**Lista de usuarios con datos:**\n\n{users_text}\n\n"
        f"💡 Cuando aparezca cita, recibirás notificación con los datos para completar manualmente."
    )


# === COMANDOS PARA REGISTRO DE DATOS ===

async def datos_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Iniciar proceso de registro de datos /datos"""
    await update.message.reply_text(
        "📝 **Registro de Datos Personales**\n\n"
        "Voy a pedirte tus datos para poder reservar automáticamente cuando aparezca una cita.\n\n"
        "Puedes cancelar en cualquier momento con /cancelar\n\n"
        "**Paso 1 de 5: Nombre**\n"
        "Por favor, escribe tu nombre:"
    )
    return NOMBRE


async def datos_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir nombre"""
    context.user_data['nombre'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Nombre: {context.user_data['nombre']}\n\n"
        f"**Paso 2 de 5: Apellido**\n"
        f"Escribe tu apellido:"
    )
    return APELLIDO


async def datos_apellido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir apellido"""
    context.user_data['apellido'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Apellido: {context.user_data['apellido']}\n\n"
        f"**Paso 3 de 5: Documento**\n"
        f"Escribe tu NIE, DNI o Pasaporte:"
    )
    return DOCUMENTO


async def datos_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir documento"""
    context.user_data['documento'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Documento: {context.user_data['documento']}\n\n"
        f"**Paso 4 de 5: Email**\n"
        f"Escribe tu correo electrónico:"
    )
    return EMAIL


async def datos_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir email"""
    context.user_data['email'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Email: {context.user_data['email']}\n\n"
        f"**Paso 5 de 5: Teléfono**\n"
        f"Escribe tu número de teléfono (con prefijo +34 si es España):"
    )
    return TELEFONO


async def datos_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir teléfono y guardar todos los datos"""
    context.user_data['telefono'] = update.message.text.strip()
    
    # Guardar datos
    user_id = update.effective_user.id
    user_data_manager.set_user_data(
        user_id,
        context.user_data['nombre'],
        context.user_data['apellido'],
        context.user_data['documento'],
        context.user_data['email'],
        context.user_data['telefono']
    )
    
    await update.message.reply_text(
        f"✅ **Datos registrados correctamente**\n\n"
        f"📋 Resumen:\n"
        f"• Nombre: {context.user_data['nombre']} {context.user_data['apellido']}\n"
        f"• Documento: {context.user_data['documento']}\n"
        f"• Email: {context.user_data['email']}\n"
        f"• Teléfono: {context.user_data['telefono']}\n\n"
        f"🤖 Ahora usa /registrar para activar el monitoreo.\n"
        f"Cuando aparezca una cita, el bot intentará reservarla automáticamente con estos datos.\n\n"
        f"📞 **Soporte:** +34 936 07 56 41"
    )
    
    # Limpiar contexto
    context.user_data.clear()
    return ConversationHandler.END


async def datos_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar registro de datos"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Registro cancelado.\n\n"
        "Puedes iniciar de nuevo con /datos cuando quieras."
    )
    return ConversationHandler.END


async def mistats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver datos registrados del usuario"""
    user_id = update.effective_user.id
    data = user_data_manager.get_user_data(user_id)
    
    if not data:
        await update.message.reply_text(
            "❌ No tienes datos registrados.\n\n"
            "Usa /datos para registrar tu información."
        )
        return
    
    await update.message.reply_text(
        f"📋 **Tus Datos Registrados**\n\n"
        f"• Nombre: {data['nombre']} {data['apellido']}\n"
        f"• Documento: {data['documento']}\n"
        f"• Email: {data['email']}\n"
        f"• Teléfono: {data['telefono']}\n\n"
        f"✅ Datos completos para auto-reserva\n\n"
        f"Para modificar tus datos, usa /datos de nuevo.\n\n"
        f"📞 **Soporte:** +34 936 07 56 41"
    )


async def post_init(application: Application):
    """Inicializar monitor al arrancar el bot"""
    global monitor
    
    logger.info("Inicializando monitor de citas...")
    monitor = CitasMonitor(on_cita_available=cita_disponible_handler)
    
    # Iniciar monitor en background
    asyncio.create_task(monitor.start_monitoring())
    
    logger.info("✅ Bot completamente inicializado")



async def post_shutdown(application: Application):
    """Detener el monitor al cerrar el bot"""
    global monitor
    
    if monitor:
        logger.info(' Cerrando bot...')
        monitor.stop_monitoring()
        logger.info(' Monitor detenido')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar clicks en botones inline"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "btn_datos":
        await query.message.reply_text(
            "📝 **Registro de Datos Personales**\n\n"
            "Usa el comando /datos para iniciar el proceso de registro.\n\n"
            "Te pediré:\n"
            "• Nombre\n"
            "• Apellido\n"
            "• NIE/DNI/Pasaporte\n"
            "• Email\n"
            "• Teléfono\n\n"
            "Escribe /datos cuando estés listo."
        )
    
    elif data == "btn_mistats":
        user_data = user_data_manager.get_user_data(user_id)
        if user_data:
            keyboard = [[InlineKeyboardButton("✏️ Modificar Datos", callback_data="btn_datos")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"📋 **Tus Datos Registrados**\n\n"
                f"• Nombre: {user_data['nombre']} {user_data['apellido']}\n"
                f"• Documento: {user_data['documento']}\n"
                f"• Email: {user_data['email']}\n"
                f"• Teléfono: {user_data['telefono']}\n\n"
                f"✅ Datos completos para auto-reserva",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text("❌ No tienes datos registrados. Usa /datos")
    
    elif data == "btn_registrar":
        if not user_data_manager.has_complete_data(user_id):
            keyboard = [[InlineKeyboardButton("📝 Registrar Datos", callback_data="btn_datos")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⚠️ **Necesitas registrar tus datos primero**\n\n"
                "Usa el botón de abajo para comenzar:",
                reply_markup=reply_markup
            )
            return
        
        username = query.from_user.username or query.from_user.first_name
        position = citas_queue.add_user(user_id)
        
        if position is None or position < 0:
            await query.message.reply_text(
                "❌ **Error al agregar a la cola**\n\n"
                "Por favor, intenta de nuevo más tarde."
            )
            return
        
        if position == 0:
            position = 1
        
        usuarios_activos[user_id] = {
            'username': username,
            'fecha_registro': datetime.now().isoformat(),
            'notified': False
        }
        
        keyboard = [
            [InlineKeyboardButton("📊 Ver Estado", callback_data="btn_status")],
            [InlineKeyboardButton("📋 Mi Posición", callback_data="btn_cola")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"✅ ¡Registrado correctamente!\n\n"
            f"📍 **Posición en cola: #{position}**\n\n"
            f"🔍 El bot está monitoreando 24/7\n"
            f"📱 Te avisaremos instantáneamente",
            reply_markup=reply_markup
        )
    
    elif data == "btn_stop":
        if user_id in usuarios_activos:
            del usuarios_activos[user_id]
            keyboard = [[InlineKeyboardButton("🟢 Reactivar", callback_data="btn_registrar")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🔴 Monitoreo detenido\n\n"
                "Usa el botón de abajo para reactivarlo:",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text("⚠️ No estabas registrado")
    
    elif data == "btn_status":
        if not monitor or not monitor.running:
            await query.message.reply_text("❌ El monitor no está activo")
            return
        
        stats = monitor.get_stats()
        now = datetime.now()
        
        if 12 <= now.hour < 14:
            modo = "⚡ MODO TURBO (0.3s)"
        elif now.hour == 11 and now.minute >= 55:
            modo = "🔥 PRE-TURBO (1s)"
        else:
            modo = "💤 Modo normal (30s)"
        
        is_registered = user_id in usuarios_activos
        
        keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="btn_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"📊 **Estado del Monitor**\n\n"
            f"🔍 Estado: {'✅ Activo' if stats['running'] else '❌ Inactivo'}\n"
            f"⏱ Modo: {modo}\n"
            f"🔢 Checks: {stats['checks_count']}\n"
            f"👤 Tu estado: {'✅ Registrado' if is_registered else '❌ No registrado'}\n"
            f"👥 Usuarios activos: {len(usuarios_activos)}",
            reply_markup=reply_markup
        )
    
    elif data == "btn_cola":
        position = citas_queue.get_position(user_id)
        if position:
            keyboard = [[InlineKeyboardButton("📊 Ver Estado", callback_data="btn_status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"📋 **Tu Posición en la Cola**\n\n"
                f"📍 Posición: #{position}\n\n"
                f"⏳ Serás procesado cuando aparezca una cita",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🟢 Activar Monitoreo", callback_data="btn_registrar")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "❌ No estás en la cola\n\n"
                "Activa el monitoreo:",
                reply_markup=reply_markup
            )
    
    elif data == "btn_ayuda":
        keyboard = [[InlineKeyboardButton("🏠 Menú Principal", callback_data="btn_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "❓ **Ayuda - Cómo funciona**\n\n"
            "1️⃣ Registra tus datos con /datos\n"
            "2️⃣ Activa el monitoreo con /registrar\n"
            "3️⃣ El bot revisa cada 0.1 segundos\n"
            "4️⃣ Te avisa instantáneamente cuando aparezca cita\n"
            "5️⃣ Intenta reservar automáticamente\n\n"
            "📋 **Comandos útiles:**\n"
            "/datos - Registrar información\n"
            "/registrar - Activar monitoreo\n"
            "/status - Ver estado\n"
            "/mistats - Ver mis datos\n"
            "/cola - Mi posición\n"
            "/stop - Detener monitoreo\n\n"
            "📞 **Soporte:** +34 936 07 56 41",
            reply_markup=reply_markup
        )
    
    elif data == "btn_start":
        has_data = user_data_manager.has_complete_data(user_id)
        is_active = user_id in usuarios_activos
        
        keyboard = []
        if not has_data:
            keyboard.append([InlineKeyboardButton("📝 Registrar Datos", callback_data="btn_datos")])
        else:
            keyboard.append([InlineKeyboardButton("👤 Ver Mis Datos", callback_data="btn_mistats")])
        
        if has_data and not is_active:
            keyboard.append([InlineKeyboardButton("🟢 Activar Monitoreo", callback_data="btn_registrar")])
        elif is_active:
            keyboard.append([InlineKeyboardButton("🔴 Detener Monitoreo", callback_data="btn_stop")])
        
        keyboard.append([InlineKeyboardButton("📊 Ver Estado", callback_data="btn_status")])
        keyboard.append([InlineKeyboardButton("❓ Ayuda", callback_data="btn_ayuda")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🏠 **Menú Principal**\n\n"
            "👇 Selecciona una opción:",
            reply_markup=reply_markup
        )


def main():
    """Iniciar el bot"""
    global application
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "TU_TOKEN_AQUI":
        logger.error("❌ Debes configurar TELEGRAM_BOT_TOKEN en config.py")
        return
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    # Iniciar health server para Render
    logger.info('Iniciando health server...')
    start_health_server()
    
    # Handler de conversación para registro de datos
    datos_handler = ConversationHandler(
        entry_points=[CommandHandler("datos", datos_start)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_nombre)],
            APELLIDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_apellido)],
            DOCUMENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_documento)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_email)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, datos_telefono)],
        },
        fallbacks=[CommandHandler("cancelar", datos_cancelar)],
    )
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(datos_handler)
    application.add_handler(CommandHandler("registrar", registrar))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("mistats", mistats))
    application.add_handler(CommandHandler("stop", stop_monitoring))
    application.add_handler(CommandHandler("admin", admin_stats))
    
    # Registrar handler de botones
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("pausar", pausar_command))
    application.add_handler(CommandHandler("reanudar", reanudar_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("cola", cola_command))
    application.add_handler(CommandHandler("confirmar", confirmar_cita_command))
    application.add_handler(CommandHandler("cancelar", cancelar_cola_command))
    
    # Iniciar bot
    logger.info("🚀 Iniciando Bot de Citas...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import random
    import time
    
    # Delay aleatorio para evitar conflicto entre m�ltiples instancias
    delay = random.uniform(0, 60)
    logger.info(f" Esperando {delay:.1f}s para evitar conflictos...")
    time.sleep(delay)
    
    main()












