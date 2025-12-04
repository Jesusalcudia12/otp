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
    CONSULTA_PREGUNTA
    CMD_IMC_PESO
    CMD_IMC_ALTURA
    CMD_FUR_REGULARIDAD
    CMD_FUR_FECHA
    CMD_FITNEST_DISCIPLINA
) = range(9, 10, 11, 12, 13, 14)


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
async def comando_consulta(update: Update, context: CallbackContext) -> int:
    """Inicia el flujo de consulta de síntomas."""
    user_data = context.user_data

    if not user_data.get('registrado'):
        await update.message.reply_text(
            "⚠️ **Por favor, regístrate primero** usando el comando /start para poder darte asistencia personalizada."
        )
        return ConversationHandler.END

    await update.message.reply_text("🔎 **Consulta de Síntomas:**\n"
                                    "Dime, **¿qué síntomas tienes?** (ej. 'fiebre alta y dolor de cabeza').")
    
    return CONSULTA_PREGUNTA

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
async def procesar_consulta(update: Update, context: CallbackContext) -> int:
    """Procesa los síntomas, busca el tratamiento y aplica la advertencia."""
    sintomas = update.message.text
    user_data = context.user_data
    nombre = user_data.get('nombre', 'Usuario')
    alergia = user_data.get('alergias', 'Ninguna conocida')
    
    # ----------------------------------------------------
    # 🔍 SIMULACIÓN DE BÚSQUEDA Y DIAGNÓSTICO (Con Google Search)
    # ----------------------------------------------------
    
    # Aquí es donde el bot llamaría a una herramienta de IA o a un API.
    # Usaremos una simulación para la respuesta:
    
    try:
        resultado_busqueda = await google:search("enfermedad y tratamiento para " + sintomas)
        
        # Procesamiento de la respuesta (muy simplificado)
        # Esto es un ejemplo, en la vida real se necesitaría un NLP avanzado.
        if "gripe" in resultado_busqueda.lower() or "resfriado" in resultado_busqueda.lower():
             enfermedad = "Resfriado Común/Gripe"
             medicamento = "Paracetamol (Acetaminofén)"
             requiere_receta = False
        else:
            enfermedad = "Posible infección que requiere supervisión"
            medicamento = "Amoxicilina"  # Usamos un medicamento de ejemplo que SÍ requiere receta
            requiere_receta = True
            
        respuesta_corta = resultado_busqueda[:150] + "..."
    except Exception as e:
        # En caso de que la búsqueda falle
        enfermedad = "Información no disponible"
        medicamento = "N/A"
        requiere_receta = False
        respuesta_corta = "Lo siento, hubo un error al buscar la información."
    ⚠️ APLICACIÓN DE ADVERTENCIA MÉDICA Y ALERGIAS
    # ----------------------------------------------------

    mensaje = f"Hola, **{nombre}**.\n\n"
    mensaje += f"De acuerdo a los síntomas de **{sintomas}**, la información general apunta a **{enfermedad}**.\n"
    
    # Advertencia de Medicamento Específica
    if medicamento != "N/A":
        mensaje += f"Un medicamento que suele aliviar estos síntomas es **{medicamento}**.\n\n"

    if requiere_receta:
        # Mensaje si requiere receta (Requerimiento del usuario)
        mensaje += (
            "⚠️ **ADVERTENCIA MÉDICA IMPORTANTE:**\n"
            "Este medicamento requiere **supervisión médica para ser suministrado**. "
            "Consulta a tu doctor antes de tomarlo."
        )
    
    # Recordatorio de Alergia
    if alergia != 'Ninguna conocida' and alergia != 'No':
        mensaje += (
            f"\n\n🚨 **Recuerda:** Tu perfil indica alergia a **{alergia}**. "
            "Asegúrate de mencionárselo al médico para evitar reacciones adversas."
        )
    
    mensaje += "\n\nRecuerda que no puedo sustituir la consulta médica real."

    await update.message.reply_text(mensaje, parse_mode='Markdown')
    
    return ConversationHandler.END
async def comando_ayuda(update: Update, context: CallbackContext) -> int:
    """Inicia el flujo de ayuda general, activando la búsqueda web."""
    
    # Si el bot puede manejar la búsqueda de forma asíncrona, no necesita ConversationHandler.
    
    # ----------------------------------------------------
    # MENSAJE SOLICITADO POR EL USUARIO
    # ----------------------------------------------------
    await update.message.reply_text(
        "🤔 **¡Dime, ¿en qué te puedo ayudar?**"
        "Escribe tu pregunta o duda (ej. '¿cómo prevenir la gripe?')."
    )
    
    # El bot pasa a un estado donde cualquier mensaje de texto 
    # se interpreta como una pregunta de ayuda general.
    return CONSULTA_PREGUNTA # Reutilizamos el estado para la próxima pregunta de texto.
async def comando_imc(update: Update, context: CallbackContext) -> int:
    """Inicia el cálculo del IMC."""
    user_data = context.user_data
    
    if not user_data.get('registrado'):
        await update.message.reply_text("⚠️ Regístrate primero usando /start.")
        return ConversationHandler.END
        
    peso = user_data.get('peso')
    altura = user_data.get('altura')
    
    # Si los datos están incompletos, los pide
    if peso == 'N/A' or altura == 'N/A':
        await update.message.reply_text(
            "Para calcular el IMC, por favor, proporciónanos tu **peso en kg**."
        )
        # Guarda el estado de la conversación temporalmente
        context.user_data['temp_imc'] = {} 
        return CMD_IMC_PESO
        
    # Si los datos están en el perfil, calcula directamente
    return await calcular_e_informar_imc(update, context, peso, altura)

# --- Captura Peso para IMC ---
async def imc_obtener_peso(update: Update, context: CallbackContext) -> int:
    """Captura el peso y pide la altura."""
    try:
        peso = float(update.message.text.replace(',', '.'))
        context.user_data['temp_imc']['peso'] = peso
        await update.message.reply_text("Gracias. Ahora, proporciona tu **altura en metros** (ej. 1.75).")
        return CMD_IMC_ALTURA
    except ValueError:
        await update.message.reply_text("Por favor, ingresa un valor numérico válido para el peso.")
        return CMD_IMC_PESO

# --- Captura Altura y Calcula IMC ---
async def imc_obtener_altura(update: Update, context: CallbackContext) -> int:
    """Captura la altura y realiza el cálculo."""
    try:
        altura = float(update.message.text.replace(',', '.'))
        peso = context.user_data['temp_imc']['peso']
        
        if altura <= 0.5 or altura > 3.0: # Validación básica
            raise ValueError

        return await calcular_e_informar_imc(update, context, peso, altura)
    except ValueError:
        await update.message.reply_text("Por favor, ingresa una altura válida en metros (ej. 1.75).")
        return CMD_IMC_ALTURA

# --- Función de Cálculo y Mensaje ---
async def calcular_e_informar_imc(update: Update, context: CallbackContext, peso: float, altura: float) -> int:
    """Calcula y reporta el IMC."""
    try:
        # Fórmula: IMC = Peso / (Altura * Altura)
        imc = peso / (altura ** 2)
        
        if imc < 18.5:
            categoria = "Bajo peso"
        elif 18.5 <= imc <= 24.9:
            categoria = "Peso saludable"
        elif 25.0 <= imc <= 29.9:
            categoria = "Sobrepeso"
        else:
            categoria = "Obesidad"

        await update.effective_message.reply_text(
            f"✅ **Tu IMC es: {imc:.2f}**\n"
            f"Tu categoría actual es: **{categoria}**.\n\n"
            "Recuerda que el IMC es una guía y no sustituye la evaluación médica."
        )
    except ZeroDivisionError:
        await update.effective_message.reply_text("Error: La altura no puede ser cero. Inténtalo de nuevo con /imc.")
        
    # Finaliza la conversación
    return ConversationHandler.END
async def comando_fur(update: Update, context: CallbackContext) -> int:
    """Inicia el cálculo de la edad gestacional."""
    user_data = context.user_data
    
    if user_data.get('sexo') == 'MASCULINO':
        await update.message.reply_text("Este cálculo solo aplica para el sexo femenino. Usa /start para verificar tu perfil.")
        return ConversationHandler.END

    reply_keyboard = [['Regular', 'Irregular']]
    await update.message.reply_text(
        "Para calcular la fecha de parto, primero indica si tu ciclo menstrual es **Regular o Irregular**.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CMD_FUR_REGULARIDAD

# --- Captura Regularidad ---
async def fur_obtener_regularidad(update: Update, context: CallbackContext) -> int:
    """Captura la regularidad y pide la fecha."""
    regularidad = update.message.text.upper().strip()
    if regularidad not in ('REGULAR', 'IRREGULAR'):
        await update.message.reply_text("Por favor, selecciona 'Regular' o 'Irregular'.")
        return CMD_FUR_REGULARIDAD
        
    context.user_data['temp_fur'] = {'regularidad': regularidad}
    
    await update.message.reply_text(
        "Gracias. Ahora, introduce el **primer día** de tu **última menstruación (FUR)** "
        "en el siguiente formato: **DD/MM/AAAA**."
    )
    return CMD_FUR_FECHA

# --- Captura Fecha y Calcula ---
async def fur_calcular(update: Update, context: CallbackContext) -> int:
    """Realiza el cálculo de semanas y FPP."""
    from datetime import datetime, timedelta
    fur_str = update.message.text
    regularidad = context.user_data['temp_fur']['regularidad']
    
    try:
        # Convertir DD/MM/AAAA a objeto datetime
        fur_date = datetime.strptime(fur_str, '%d/%m/%Y')
        today = datetime.now()
        
        # Cálculo de Edad Gestacional (días)
        difference_in_days = (today - fur_date).days
        weeks_pregnant = difference_in_days // 7
        remaining_days = difference_in_days % 7

        # Cálculo de Fecha Probable de Parto (FPP)
        # 40 semanas = 280 días (Regla de Naegele)
        fpp_date = fur_date + timedelta(days=280)
        
        mensaje = f"🤰 **Estimación de Embarazo**\n\n"
        mensaje += f"Fecha de Última Regla (FUR): **{fur_date.strftime('%d/%m/%Y')}**\n"
        mensaje += f"Edad Gestacional: **{weeks_pregnant} semanas y {remaining_days} días**.\n"
        mensaje += f"Fecha Probable de Parto (FPP): **{fpp_date.strftime('%d/%m/%Y')}**.\n\n"
        
        if regularidad == 'IRREGULAR':
            mensaje += "⚠️ **Nota Importante:** Dado que tu ciclo es irregular, la FPP es solo una **estimación muy aproximada**. Consulta siempre a tu ginecólogo para una confirmación exacta mediante ultrasonido."
            
        await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
        
    except ValueError:
        await update.message.reply_text("Formato de fecha incorrecto. Por favor, usa el formato **DD/MM/AAAA** (ej. 25/06/2025).")
        return CMD_FUR_FECHA

    return ConversationHandler.END
async def comando_care(update: Update, context: CallbackContext):
    """Proporciona información sobre cuidado facial mediante búsqueda web."""
    query = "rutina de cuidado facial piel limpia y definida"
    
    await update.message.reply_text("🔎 Buscando en la web la mejor información para una piel limpia y definida...")
    
    try:
        resultado = await google:search(query)
        # Muestra un resumen de la búsqueda
        await update.message.reply_text(
            f"✨ **Resultados de Cuidado Facial:**\n\n"
            f"{resultado[:500]}..." # Se muestra una parte del resultado
            "\n\n**Tip:** Recuerda probar productos en una pequeña área de la piel antes de usarlos ampliamente."
        )
    except Exception:
        await update.message.reply_text("Lo siento, no pude acceder a la web en este momento. Inténtalo de nuevo más tarde.")
async def comando_fitnest(update: Update, context: CallbackContext) -> int:
    """Inicia la pregunta sobre la disciplina deportiva."""
    await update.message.reply_text("🏋️‍♀️ **¿Qué deportes, disciplina o pasatiempo practicas?**\n"
                                    "Esto me ayudará a buscar la dieta y ejercicios más adecuados para ti.")
    return CMD_FITNEST_DISCIPLINA

async def fitnest_buscar(update: Update, context: CallbackContext) -> int:
    """Busca dietas y ejercicios para la disciplina proporcionada."""
    disciplina = update.message.text
    query = f"mejores dietas y ejercicios para {disciplina}"
    
    await update.message.reply_text(f"🔎 Buscando las mejores dietas y rutinas para **{disciplina}**...")
    
    try:
        resultado = await google:search(query)
        await update.message.reply_text(
            f"💪 **Resultados para {disciplina}:**\n\n"
            f"{resultado[:500]}..."
            "\n\n**Advertencia:** Consulta a un profesional de la nutrición y un entrenador físico antes de iniciar cualquier plan."
        )
    except Exception:
        await update.message.reply_text("Lo siento, no pude obtener los resultados de la búsqueda.")
        
    return ConversationHandler.END
async def comando_maps(update: Update, context: CallbackContext):
    """Pide la ubicación para buscar farmacias y hospitales."""
    await update.message.reply_text(
        "📍 Para encontrar hospitales y farmacias cercanas, por favor **comparte tu ubicación** actual."
        "\n(Usa el clip 📎 y selecciona 'Ubicación')."
    )
    # NOTA: La lógica para PROCESAR la ubicación (MessageHandler(filters.LOCATION))
    # y usar un API de mapas debe implementarse aparte.

async def procesar_ubicacion(update: Update, context: CallbackContext):
    """(Función conceptual) Procesa la ubicación y busca puntos cercanos."""
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        
        await update.message.reply_text(f"Ubicación recibida. Buscando farmacias y hospitales cerca de: ({lat:.2f}, {lon:.2f})...")
        
        # Aquí se usa una búsqueda con Google Maps API o Google Search
        # Ejemplo:
        try:
            hospitales = await google:search(f"hospitales cercanos a {lat}, {lon}")
            farmacias = await google:search(f"farmacias cercanas a {lat}, {lon}")
            
            await update.message.reply_text(
                "🗺️ **Resultados Cercanos:**\n\n"
                f"**Hospitales:** {hospitales[:200]}...\n\n"
                f"**Farmacias:** {farmacias[:200]}..."
            )
        except Exception:
            await update.message.reply_text("No se pudieron obtener resultados de mapas en este momento.")
async def comando_perfil(update: Update, context: CallbackContext):
    """Muestra los datos del perfil y ofrece opción de modificación."""
    user_data = context.user_data
    
    if not user_data.get('registrado'):
        await update.message.reply_text("⚠️ No estás registrado/a. Usa /start para crear tu perfil.")
        return
        
    resumen = (
        "👤 **Tu Perfil Personal**\n\n"
        f"**Nombre Completo:** {user_data['nombre']} {user_data['apellidos']}\n"
        f"**Edad:** {user_data['edad']} años\n"
        f"**Peso:** {user_data.get('peso', 'N/A')} kg\n"
        f"**Altura:** {user_data.get('altura', 'N/A')} m\n"
        f"**Alergias:** {user_data['alergias']}\n"
        f"**Sexo:** {user_data['sexo']}\n"
        f"**Embarazo:** {user_data.get('embarazo', 'N/A')}\n\n"
    )
    
    await update.message.reply_text(
        resumen,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([['Modificar Datos']], one_time_keyboard=True, resize_keyboard=True)
    )
    # NOTA: Al pulsar 'Modificar Datos', se debe iniciar el ConversationHandler de REGISTRO (o uno nuevo de edición).
async def comando_salud(update: Update, context: CallbackContext):
    """Muestra el mensaje de venta y enlaces de ayuda."""
    
    # ⚠️ REEMPLAZA ESTOS CON TUS ENLACES REALES
    enlaces_proveedor = (
        "📚 **Guía Esencial de Longevidad** [LINK]\n"
        "🎬 **Video - 5 Secretos para la Vitalidad** [LINK]\n"
        "🔗 **Lista de Herramientas Nutricionales** [LINK]"
    )
    
    mensaje = (
        "✨ **¡Tu salud es lo primero!** ✨\n\n"
        "¿Quieres seguir viviendo por mucho tiempo? ¡Llegaste al lugar indicado!\n\n"
        "Como tu asistente médico, me encargué de buscar las mejores herramientas y a un precio accesible. "
        "¡No vale la pena invertir en tu salud! 😉\n\n"
        "**Te comparto esta lista de libros, guías y videos de ayuda:**\n"
        f"{enlaces_proveedor}"
    )
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ----------------------------------------------------
# 5. CONFIGURACIÓN DEL MANEJADOR DE CONVERSACIÓN
# ----------------------------------------------------

def main():
    """Ejecuta el bot."""
    # ⚠️ REEMPLAZA ESTO CON TU TOKEN DE BOTFATHER ⚠️
    TOKEN = "8330745974:AAE7hdMyFr_QR0_RP9FL4ngTIrrObMMFkCs" 
    
    application = Application.builder().token(TOKEN).build()

    # Definición del flujo del ConversationHandler
    registro_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start,)],
        entry_points=[CommandHandler("consulta", comando_consulta)],
        entry_points=[CommandHandler("ayuda", comando_ayuda)],
        entry_points=[CommandHandler("imc", comando_imc)],
        entry_points=[CommandHandler("fur", comando_fur)],
        entry_points=[CommandHandler("care", comando_care)],
        entry_points=[CommandHandler("salud", comando_salud)],
        entry_points=[CommandHandler("fitnest", comando_fitnest)],
        entry_points=[CommandHandler("maps", comando_maps)],
        
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
            CONSULTA_PREGUNTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_consulta)],
            CMD_IMC_PESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, imc_obtener_peso)],
            CMD_IMC_ALTURA: [MessageHandler(filters.TEXT & ~filters.COMMAND, imc_obtener_altura)],
            CMD_FUR_REGULARIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, fur_obtener_regularidad)],
            CMD_FUR_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fur_calcular)],
            CMD_FITNEST_DISCIPLINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fitnest_buscar)],
        },
        
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(registro_handler)
    application.add_handler(consulta_handler)
    application.add_handler(ayuda_handler)
    application.add_handler(imc_handler)
    application.add_handler(fur_handler)
    application.add_handler(care_handler)
    application.add_handler(salud_handler)
    application.add_handler(fitnest_handler)
    application.add_handler(perfil_handler)
    application.add_handler(maps_handler)
    application.add_handler(MessageHandler(filters.LOCATION, procesar_ubicacion))
    # ----------------------------------------------------
    # AÑADE AQUÍ LOS MANEJADORES DE COMANDOS /consulta, /ayuda, etc.
    # ----------------------------------------------------
    # application.add_handler(CommandHandler("consulta", comando_consulta)) # Ejemplo
    
    # Iniciar el Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
