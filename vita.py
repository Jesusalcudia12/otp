import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)

# Habilitar logging (útil para Termux)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# ----------------------------------------------------
# 1. DEFINICIÓN DE ESTADOS DEL REGISTRO
# ----------------------------------------------------

# Definición de estados para el ConversationHandler
(
    REG_NOMBRE,
    REG_APELLIDOS,
    REG_EDAD,
    REG_PESO,
    REG_ALTURA,
    REG_ALERGIAS,
    REG_SEXO,
    REG_EMBARAZO,
    REG_VALIDACION
) = range(9)


# ----------------------------------------------------
# 2. MANEJADOR DE COMANDOS /start y Bienvenida
# ----------------------------------------------------

async def start(update: Update, context: CallbackContext) -> int:
    """Inicia la conversación y pide el nombre."""
    user_data = context.user_data
    chat_id = update.effective_chat.id

    # Si el usuario ya está registrado, omite el registro
    if user_data.get('registrado'):
        await update.message.reply_text(
            f"¡Bienvenido/a de nuevo, {user_data['nombre']}! Ya estás registrado/a.\n"
            "Usa el menú o los comandos para acceder a los servicios:\n"
            "/consulta, /ayuda, /perfil, etc."
        )
        return ConversationHandler.END # Finaliza el ConversationHandler si ya está registrado

    # Mensaje de bienvenida e inicio de registro
    await update.message.reply_text(
        "¡Hola! Soy tu Asistente de Salud. Para comenzar a darte asistencia personalizada, "
        "necesito recopilar algunos datos de tu perfil.\n"
        "**Comencemos con tu Nombre Completo:**"
    )
    return REG_NOMBRE

# ----------------------------------------------------
# 3. FUNCIONES DE CAPTURA DE DATOS (PASOS DEL REGISTRO)
# ----------------------------------------------------

# --- A. Captura Nombre ---
async def obtener_nombre(update: Update, context: CallbackContext) -> int:
    """Captura el nombre y pide el apellido."""
    context.user_data['nombre'] = update.message.text
    await update.message.reply_text("Gracias. Ahora, **¿cuáles son tus Apellidos?**")
    return REG_APELLIDOS

# --- B. Captura Apellidos ---
async def obtener_apellidos(update: Update, context: CallbackContext) -> int:
    """Captura el apellido y pide la edad."""
    context.user_data['apellidos'] = update.message.text
    await update.message.reply_text("Perfecto. **¿Cuál es tu Edad?**")
    return REG_EDAD

# --- C. Captura Edad ---
async def obtener_edad(update: Update, context: CallbackContext) -> int:
    """Captura la edad y pide el peso (con opción de omitir)."""
    try:
        edad = int(update.message.text)
        if edad <= 0 or edad > 120:
            raise ValueError
        context.user_data['edad'] = edad
        
        await update.message.reply_text(
            "Entendido. **¿Cuál es tu Peso en Kilogramos (kg)?**\n"
            "*(Puedes responder '0' o 'N/A' si prefieres no responder.)*"
        )
        return REG_PESO
    except ValueError:
        await update.message.reply_text(
            "Por favor, ingresa una edad válida (solo números)."
        )
        return REG_EDAD

# --- D. Captura Peso (Opcional) ---
async def obtener_peso(update: Update, context: CallbackContext) -> int:
    """Captura el peso y pide la altura (con opción de omitir)."""
    peso_str = update.message.text.upper().strip()
    
    # Manejar '0' o 'N/A' como opcional
    if peso_str in ('0', 'N/A', 'N/O'):
        context.user_data['peso'] = 'N/A'
    else:
        try:
            # Aceptar números con o sin decimales
            peso = float(peso_str.replace(',', '.'))
            context.user_data['peso'] = peso
        except ValueError:
            await update.message.reply_text(
                "Por favor, ingresa un valor numérico para tu peso (ej. 75.5) o '0' / 'N/A'."
            )
            return REG_PESO

    await update.message.reply_text(
        "Gracias. **¿Cuál es tu Altura en Metros (m)?** (ej. 1.75)\n"
        "*(Puedes responder '0' o 'N/A' si prefieres no responder.)*"
    )
    return REG_ALTURA

# --- E. Captura Altura (Opcional) ---
async def obtener_altura(update: Update, context: CallbackContext) -> int:
    """Captura la altura y pide las alergias."""
    altura_str = update.message.text.upper().strip()

    if altura_str in ('0', 'N/A', 'N/O'):
        context.user_data['altura'] = 'N/A'
    else:
        try:
            altura = float(altura_str.replace(',', '.'))
            context.user_data['altura'] = altura
        except ValueError:
            await update.message.reply_text(
                "Por favor, ingresa tu altura en un formato numérico (ej. 1.75) o '0' / 'N/A'."
            )
            return REG_ALTURA

    await update.message.reply_text(
        "Casi terminamos. **¿Tienes alguna alergia conocida a medicamentos o sustancias?**\n"
        "*(Si no tienes, simplemente escribe 'No' o 'Ninguna'.)*"
    )
    return REG_ALERGIAS

# --- F. Captura Alergias ---
async def obtener_alergias(update: Update, context: CallbackContext) -> int:
    """Captura las alergias y pide el sexo con un teclado de botones."""
    context.user_data['alergias'] = update.message.text

    reply_keyboard = [['Masculino', 'Femenino']]
    await update.message.reply_text(
        "¡Excelente! Finalmente, **¿Cuál es tu Sexo?**",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return REG_SEXO

# --- G. Captura Sexo y Condición para Embarazo ---
async def obtener_sexo(update: Update, context: CallbackContext) -> int:
    """Captura el sexo y, si es 'Femenino', pregunta por embarazo."""
    sexo = update.message.text.upper().strip()

    if sexo not in ('MASCULINO', 'FEMENINO'):
        reply_keyboard = [['Masculino', 'Femenino']]
        await update.message.reply_text(
            "Por favor, selecciona o escribe 'Masculino' o 'Femenino'.",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return REG_SEXO

    context.user_data['sexo'] = sexo
    
    # ----------------------------------------
    # PASO CONDICIONAL (REQUERIMIENTO 5)
    # ----------------------------------------
    if sexo == 'FEMENINO':
        await update.message.reply_text(
            "Entendido. Una pregunta de seguridad esencial para mujeres:\n"
            "**¿Te encuentras embarazada actualmente?**",
            reply_markup=ReplyKeyboardMarkup(
                [['Sí', 'No']], one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return REG_EMBARAZO
    else:
        context.user_data['embarazo'] = 'NO APLICA'
        return await validar_datos(update, context) # Pasa directamente a la validación

# --- H. Captura Embarazo (Condicional) ---
async def obtener_embarazo(update: Update, context: CallbackContext) -> int:
    """Captura el estado de embarazo y pasa a la validación."""
    embarazo = update.message.text.upper().strip()

    if embarazo not in ('SÍ', 'SI', 'NO'):
        await update.message.reply_text(
            "Por favor, responde 'Sí' o 'No'.",
            reply_markup=ReplyKeyboardMarkup(
                [['Sí', 'No']], one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return REG_EMBARAZO

    context.user_data['embarazo'] = 'SÍ' if embarazo == 'SÍ' or embarazo == 'SI' else 'NO'
    return await validar_datos(update, context)

# ----------------------------------------------------
# 4. FUNCIÓN DE VALIDACIÓN Y MENSAJE DE ÉXITO (PASO 3, 4, 6)
# ----------------------------------------------------

async def validar_datos(update: Update, context: CallbackContext) -> int:
    """
    Muestra los datos capturados y pide confirmación (Validación).
    Si se confirma, guarda el estado y da el mensaje de éxito.
    """
    user_data = context.user_data
    
    # Construir el mensaje de validación
    resumen = (
        "✅ **Validación de Datos (Revisa y confirma):**\n\n"
        f"**Nombre:** {user_data['nombre']} {user_data['apellidos']}\n"
        f"**Edad:** {user_data['edad']} años\n"
        f"**Peso:** {user_data['peso']} kg\n"
        f"**Altura:** {user_data['altura']} m\n"
        f"**Alergias:** {user_data['alergias']}\n"
        f"**Sexo:** {user_data['sexo']}\n"
        f"**Embarazo:** {user_data['embarazo']}\n\n"
        "**¿Toda la información es correcta?**"
    )

    reply_keyboard = [['Sí, Guardar y Continuar', 'No, Quiero Corregir']]
    await update.message.reply_text(
        resumen,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return REG_VALIDACION

async def confirmar_registro(update: Update, context: CallbackContext) -> int:
    """Finaliza el registro y da el mensaje de éxito."""
    respuesta = update.message.text.upper().strip()
    
    if 'SÍ' in respuesta or 'GUARDAR' in respuesta:
        
        # ----------------------------------------
        # PASO DE ALMACENAMIENTO (REQUERIMIENTO 4)
        # ----------------------------------------
        context.user_data['registrado'] = True 
        
        # ----------------------------------------
        # MENSAJE DE REGISTRO EXITOSO (REQUERIMIENTO 6)
        # ----------------------------------------
        await update.message.reply_text(
            "🎉 **¡Registro Exitoso!** Tus datos han sido guardados de forma segura.\n"
            "Ahora puedo empezar a asistirte con tu perfil de salud. Utiliza el menú o los siguientes comandos para empezar:\n"
            "**/consulta**: Para ver recomendaciones sobre síntomas.\n"
            "**/ayuda**: Para hacer una pregunta general.\n"
            "**/perfil**: Para ver o modificar tus datos.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    elif 'NO' in respuesta or 'CORREGIR' in respuesta:
        await update.message.reply_text(
            "De acuerdo, reiniciemos el registro. Por favor, escribe de nuevo **/start** para comenzar desde el principio.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        reply_keyboard = [['Sí, Guardar y Continuar', 'No, Quiero Corregir']]
        await update.message.reply_text(
            "Por favor, selecciona 'Sí, Guardar y Continuar' o 'No, Quiero Corregir'.",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return REG_VALIDACION

# Función para cancelar el registro en cualquier momento
async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancela la conversación iniciada por el usuario."""
    await update.message.reply_text(
        'Registro cancelado. Puedes reiniciarlo en cualquier momento con el comando /start.'
    )
    return ConversationHandler.END


# ----------------------------------------------------
# 5. CONFIGURACIÓN DEL MANEJADOR DE CONVERSACIÓN
# ----------------------------------------------------

def main():
    """Ejecuta el bot."""
    # ⚠️ REEMPLAZA ESTO CON TU TOKEN DE BOTFATHER ⚠️
    TOKEN = "TU_TOKEN_DE_BOT_AQUÍ" 
    
    application = Application.builder().token(TOKEN).build()

    # Definición del flujo del ConversationHandler
    registro_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        
        states={
            REG_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_nombre)],
            REG_APELLIDOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_apellidos)],
            REG_EDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_edad)],
            REG_PESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_peso)],
            REG_ALTURA: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_altura)],
            REG_ALERGIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_alergias)],
            REG_SEXO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_sexo)],
            REG_EMBARAZO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_embarazo)],
            REG_VALIDACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_registro)],
        },
        
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(registro_handler)
    
    # ----------------------------------------------------
    # AÑADE AQUÍ LOS MANEJADORES DE COMANDOS /consulta, /ayuda, etc.
    # ----------------------------------------------------
    # application.add_handler(CommandHandler("consulta", comando_consulta)) # Ejemplo
    
    # Iniciar el Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
