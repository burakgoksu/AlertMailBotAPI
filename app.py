import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, send_file
from flask_httpauth import HTTPBasicAuth
from AlertAvailableSessions import AlertAvailableSessions
from datetime import datetime
from pytz import timezone
import threading


app = Flask(__name__)

tz = timezone('Europe/Istanbul') # UTC, Asia/Shanghai, Europe/Berlin

def timetz(*args):
    return datetime.now(tz).timetuple()

logging.Formatter.converter = timetz

# Loglama için temel yapılandırmayı ayarla
logging.basicConfig(level=logging.INFO)

# Rotating log dosyaları oluştur, 10MB'da bir yeni dosya oluştur ve en fazla 10 dosya sakla
file_handler = RotatingFileHandler('KuryeNetApp.log', maxBytes=80000 * 80000, backupCount=10)
file_handler.setLevel(logging.INFO)  # INFO ve üzeri seviyedeki logları yakala

# Log mesajları için bir format belirle
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Flask app logger'ına file handler'ı ekle
app.logger.addHandler(file_handler)

auth = HTTPBasicAuth()

alert_empty_session = None
alert_thread = None


@auth.verify_password
def verify_password(username, password):
    if username == 'admin' and password == 'admin':
        app.logger.info(f"Method: verify_password, Username: {username}, Password: {password}, Basic Auth successful.")
        return True
    else:
        app.logger.error(f"Method: verify_password, Username: {username}, Password: {password}, Basic Auth failed.")
        return False

@app.route('/available_sessions_logs', methods=['GET'])
def show_available_sessions_logs():
    log_file_path = 'AlertAvailableSessions.log'
    return send_file(log_file_path, as_attachment=True)

@app.route('/start_available_sessions_bot', methods=['GET'])
def start_available_sessions_boy():
    global alert_empty_session, alert_thread
    if alert_empty_session is None:
        alert_empty_session = AlertAvailableSessions(
            link1="https://online.spor.istanbul/uyegiris",
            link2="https://online.spor.istanbul/uyespor",
            txt_file1="UmraniyeCakmakYuzmeHavuzuSeans.txt",
            txt_file2="UygunSeanslar.txt",
            headless=False,
            sender_email="gogsub58365@gmail.com",
            sender_password="hnma axon amcw sumr",
            receiver_email="gogsub58365@gmail.com"
        )
    if alert_thread is None or not alert_thread.is_alive():
        alert_thread = threading.Thread(target=alert_empty_session.start)
        alert_thread.start()
        app.logger.info('AlertAvailableSessions bot started')
        return 'AlertAvailableSessions bot started'
    else:
        return 'AlertAvailableSessions bot is already running'

@app.route('/stop_available_sessions_bot', methods=['GET'])
def stop_available_sessions_boy():
    global alert_empty_session, alert_thread
    if alert_empty_session is not None:
        alert_empty_session.stop()
        alert_empty_session = None
        alert_thread = None
        app.logger.info('AlertAvailableSessions bot stopped')
        return 'AlertAvailableSessions bot stopped'
    else:
        return 'AlertAvailableSessions bot is not running'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Heroku'nun belirlediği portu kullan
    app.run(debug=True, host='0.0.0.0', port=port)
