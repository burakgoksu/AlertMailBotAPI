import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, send_file, request
from flask_httpauth import HTTPBasicAuth
import re

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
file_handler = RotatingFileHandler('AlertBot.log', maxBytes=80000 * 80000, backupCount=10)
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

@app.route('/')
def home():
    return "API is up!"

@app.route('/available_sessions_logs', methods=['GET'])
def show_available_sessions_logs():
    log_file_path = 'AlertAvailableSessions.log'
    app.logger.info("Method: available_sessions_logs, log_file_path: {}".format(log_file_path))
    return send_file(log_file_path, as_attachment=True)

@app.route('/alert_bot_logs', methods=['GET'])
def alert_bot_logs():
    log_file_path = 'AlertBot.log'
    app.logger.info("Method: alert_bot_logs, log_file_path: {}".format(log_file_path))
    return send_file(log_file_path, as_attachment=True)

bots = {}
threads = {}
bot_key = None

def sanitize_filename(name):
    name = name.replace(" ", "_")  # boşlukları _ yap
    return re.sub(r'[<>:"/\\|?*]', '_', name)

@app.route('/start_available_sessions_bot', methods=['GET'])
def start_available_sessions_bot():
    bot_key = f"{request.args.get('tesis')}_{request.args.get('brans')}_{request.args.get('tarih')}_{request.args.get('saat')}"

    if bot_key not in bots:
        bots[bot_key] = AlertAvailableSessions(
            link1="https://online.spor.istanbul/uyegiris",
            link2="https://online.spor.istanbul/uyespor",
            txt_file1=sanitize_filename(f"{request.args.get('tesis')}_{request.args.get('brans')}_{request.args.get('tarih')}_{request.args.get('saat')}_Seans.txt"),
            txt_file2=sanitize_filename("UygunSeanslar.txt"),
            sender_email=request.args.get('sender_email'),
            sender_password=request.args.get('sender_email_password'),
            receiver_email=request.args.get('receiver_email'),
            account_sid=request.args.get('account_sid'),
            auth_token=request.args.get('auth_token'),
            from_number=request.args.get('telefon_no'),
            brans=request.args.get('brans'),
            tesis=request.args.get('tesis'),
            target_date=request.args.get('tarih'),
            target_time=request.args.get('saat'),
            pooling_time=request.args.get('pooling_time')
        )

    if bot_key not in threads or not threads[bot_key].is_alive():
        thread = threading.Thread(target=bots[bot_key].start)
        thread.start()
        threads[bot_key] = thread
        app.logger.info(f"Bot started for {bot_key}")
        return f'Bot started for {bot_key}'
    else:
        return f'Bot is already running for {bot_key}'


@app.route('/stop_available_sessions_bot', methods=['GET'])
def stop_available_sessions_bot():
    bot_key = f"{request.args.get('tesis')}_{request.args.get('brans')}_{request.args.get('tarih')}_{request.args.get('saat')}"

    if bot_key in bots:
        bots[bot_key].stop()
        threads[bot_key].join(timeout=5)  # Thread’in düzgün şekilde kapanmasını sağla
        del bots[bot_key]
        del threads[bot_key]
        app.logger.info(f"Bot stopped for {bot_key}")
        return f'Bot stopped for {bot_key}'
    else:
        return f'No running bot for {bot_key}'

@app.route('/list_active_bot', methods=['GET'])
def list_active_bot():
    if bool(bots) == False:
        return "There is no active bot"

    else:
        active_bot_name = ""
        for key in bots.keys():
            active_bot_name = "\n".join(bots.keys())

        app.logger.info(f'Active bot is {len(bots)} : \n {active_bot_name}')
        return f'Active bot is {len(bots)} : \n {active_bot_name}'





"""
@app.route('/start_available_sessions_bot', methods=['GET'])
def start_available_sessions_boy():
    global alert_empty_session, alert_thread
    if alert_empty_session is None:
        alert_empty_session = AlertAvailableSessions(
            link1="https://online.spor.istanbul/uyegiris",
            link2="https://online.spor.istanbul/uyespor",
            txt_file1=f"{request.args.get('tesis')}_{request.args.get('brans')}_Seans.txt",
            txt_file2="UygunSeanslar.txt",
            sender_email= request.args.get('sender_email'),
            sender_password= request.args.get('sender_email_password'),
            receiver_email= request.args.get('receiver_email'),
            account_sid = request.args.get('account_sid'),
            auth_token = request.args.get('auth_token'),
            from_number = request.args.get('telefon_no'),
            brans = request.args.get('brans'),
            tesis= request.args.get('tesis'),
            target_date = request.args.get('tarih'),
            target_time = request.args.get('saat'),
            pooling_time= request.args.get('pooling_time')
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
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Heroku'nun belirlediği portu kullan
    app.run(debug=True, host='0.0.0.0', port=port)
