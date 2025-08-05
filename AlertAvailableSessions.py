import logging
import os
import threading
from logging.handlers import RotatingFileHandler

import pytz
from selenium import webdriver
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime

from Twilio import Twilio


class AlertAvailableSessions:
    def __init__(self, link1, link2, txt_file1, txt_file2, sender_email, sender_password, receiver_email, account_sid, auth_token, from_number, brans, tesis, target_date, target_time, pooling_time, headless=True):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            file_handler = RotatingFileHandler('AlertAvailableSessions.log', maxBytes=80000 * 80000, backupCount=10)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.chrome_option = Options()
        if headless:
            self.chrome_option.add_argument("--headless")
        self.chrome_option.add_argument("--disable-dev-shm-usage")
        self.chrome_option.add_argument("--no-sandbox")
        self.chrome_option.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection":False
        })
        self.chrome_option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        self.link1 = link1
        self.link2 = link2
        self.txt_file1 = txt_file1
        self.txt_file2 = txt_file2
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email
        self.__sent_sessions_list = []
        self.__is_new_sessions = False
        self.logger.info('Web Driver was started')
        self._running = False
        self.brans = brans
        self.tesis = tesis
        self.target_date = target_date
        self.target_time = target_time
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.polling_time = pooling_time
        self.lock = threading.Lock()


    def sanitize_filename(self, name):
        name = name.replace(" ", "_")  # boşlukları _ yap
        return re.sub(r'[<>:"/\\|?*]', '_', name)


    def GetSessionInfo(self, utc_time=None):

        timezone = pytz.timezone('GMT')
        current_datetime = datetime.now(timezone)
        current_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        twilio = Twilio(self.account_sid, self.auth_token)

        def safe_click(driver, by, selector, wait, retries=3):
            """
            StaleElementReference hatalarına karşı tıklamayı güvenli hale getirir.
            driver: Selenium WebDriver
            by, selector: locator tuple
            wait: WebDriverWait objesi
            retries: yeniden deneme sayısı
            """
            for attempt in range(retries):
                try:
                    elem = wait.until(EC.element_to_be_clickable((by, selector)))
                    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                    elem.click()
                    return True
                except StaleElementReferenceException:
                    # DOM yenilenmiş, yeniden dene
                    if attempt < retries - 1:
                        time.sleep(0.5)
                        continue
                except TimeoutException:
                    break
            return False

        # Setup Chrome options
        #chrome_options = Options()
        #chrome_options.add_argument("--headless")
        #chrome_options.add_argument("--no-sandbox")
        #chrome_options.add_argument("--disable-dev-shm-usage")
        #chrome_options.add_argument("--disable-gpu")  # This is important for some versions of Chrome
        #chrome_options.add_argument("--remote-debugging-port=9222")  # This is recommended
        #chrome_options.add_argument("--window-size=1280,1024")
        #chrome_options.add_argument("--disable-software-rasterizer")

        # Set path to Chrome binary
        #chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"
        #/opt/chrome/chrome-linux64/chrome
        # Set path to ChromeDriver
        #
        chrome_service = Service(executable_path="/opt/chromedriver/chromedriver-linux64/chromedriver")

        # Set up driver
        #driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_option)
        try:
            driver.get(self.link1)

            # Bekleme: Öğelerin yüklenmesini bekleyin
            wait = WebDriverWait(driver, 10)
            tc_no = wait.until(EC.presence_of_element_located((By.ID, 'txtTCPasaport')))
            tc_no.send_keys('53875003034')
            password = wait.until(EC.presence_of_element_located((By.ID, 'txtSifre')))
            password.send_keys('B1245789630g.')
            login_buton = wait.until(EC.element_to_be_clickable((By.ID, 'btnGirisYap')))
            login_buton.click()
            self.logger.info('Login Successfully')
        except Exception as e:
            self.logger.error(f'Login failed: {e}')
            driver.quit()
            return

        try:
            # Kısa bir bekleme süresiyle yalnızca popup’u arıyoruz
            short_wait = WebDriverWait(driver, 3)
            if safe_click(driver, By.ID, "closeModal", short_wait):
                self.logger.info("Login sonrası popup kapatıldı")
            else:
                self.logger.info("Popup mevcut değil, devam ediliyor")
        except Exception:
            self.logger.info("Popup bulunamadı, devam ediliyor")

        try:
            wait = WebDriverWait(driver, 10)
            driver.get(self.link2)
            wait.until(EC.element_to_be_clickable((By.ID, 'pageContent_rptListe_lbtnSeansSecim_0')))
            choose_session_button = driver.find_element(By.ID, 'pageContent_rptListe_lbtnSeansSecim_0')
            driver.execute_script("arguments[0].click();", choose_session_button)
            self.logger.info('Seans Secim Buton was Clicked')
        except Exception as e:
            self.logger.error(f'Seans Secim Buton was NOT Clicked: {e}')
            driver.quit()
            return

        time.sleep(1)

        # 1) Branş dropdown’ı aç ve TENİS seç
        try:
            if safe_click(driver, By.XPATH, '//span[@id="select2-ddlBransFiltre-container"]', wait):
                self.logger.info('Branş dropdown açıldı')
            else:
                raise Exception("Dropdown açma başarısız")

            time.sleep(1)  # Menü içeriğinin yüklenmesini bekle

            xpath_brans = f'//li[contains(text(), "{self.brans}")]'
            if safe_click(driver, By.XPATH, xpath_brans, wait):
                self.logger.info(f'{self.brans} seçildi')
            else:
                raise Exception(f'{self.brans} seçeneği tıklanamadı')

        except Exception as e:
            self.logger.error(f'Branş seçimi başarısız: {e}')

        # 2) Tesis dropdown’ı aç ve MALTEPE SAHİL SPOR TESİSİ seç
        try:
            if safe_click(driver, By.XPATH, '//span[@id="select2-ddlTesisFiltre-container"]', wait):
                self.logger.info('Tesis dropdown açıldı')
            else:
                raise Exception("Dropdown açma başarısız")

            time.sleep(1)  # Menü içeriğinin yüklenmesini bekle

            xpath_tesis = f'//li[contains(text(), "{self.tesis}")]'
            if safe_click(driver, By.XPATH, xpath_tesis, wait):
                self.logger.info(f'{self.tesis} seçildi')
            else:
                raise Exception(f'{self.tesis} seçeneği tıklanamadı')

        except Exception as e:
            self.logger.error(f'Tesis seçimi başarısız: {e}')

        # Email Step
        try:
            panels = driver.find_elements(By.CLASS_NAME, 'col-md-1')
            self.logger.info('Get Sessions Info')
        except Exception as e:
            self.logger.error(f'Failed to find session panels: {e}')
            driver.quit()
            return


        with open(self.txt_file1, "w") as txt_file1:
            for panel in panels:
                txt_file1.writelines(panel.text + "\n")
                txt_file1.writelines("------------------------------------------------------------\n")

        # İlgili Seansı Bul
        try:
            # 1) Tarihi bul
            panel = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f'//h3[contains(@class, "panel-title") and contains(., "{self.target_date}")]'
            )))

            # 2) O panel’in kök div’e çık
            panel_container = panel.find_element(
                By.XPATH, "./ancestor::div[contains(@class, 'panel-info')]"
            )

            # 3) Saat span’ını bul
            session_span = panel_container.find_element(
                By.XPATH, f'.//span[contains(., "{self.target_time}")]'
            )

            # 4) En yakın ".well" div’i
            well_div = session_span.find_element(
                By.XPATH, "./ancestor::div[contains(@class, 'well')]"
            )

            # 5) Eğer input varsa safe_click ile tıkla
            # well_div’in ID’sini alıp locator oluşturuyoruz
            well_id = well_div.get_attribute("id")
            locator = (By.XPATH, f"//div[@id='{well_id}']//input[@type='checkbox']")

            checkboxes = well_div.find_elements(*locator)
            if not checkboxes:
                self.logger.warning(f"No checkbox rendered for {self.target_date} {self.target_time}")
                return False

            # safe_click ile tıklama
            if safe_click(driver, locator[0], locator[1], wait):
                self.logger.info(f"✅ Seçildi: {self.target_date} {self.target_time}")
            else:
                self.logger.error(f"❌ {self.target_date} {self.target_time} seçilemedi (stale/intercept/timeout)")

        except Exception as e:
            self.logger.error(f"❌ Hata: {e}")
            return False



        # Rezervasyon checkbox ve Kaydet Butonu

        # 1) Rezervasyon onay checkbox’ı
        if not safe_click(driver, By.ID, "pageContent_cboxOnay", wait):
            self.logger.error("Rezervasyon onayı işaretlenemedi (stale element veya bulunamadı)")
            return False
        else:
            self.logger.info("Rezervasyon onay checkbox’ı işaretlendi")

        # 1) Element var mı?
        kaydet = wait.until(EC.presence_of_element_located((By.ID, "lbtnKaydet")))
        print("Visible:", kaydet.is_displayed(), "Enabled:", kaydet.is_enabled())

        # 2) Normal click
        try:
            kaydet.click()
            print("Direct click succeeded")
        except Exception as e:
            print("Direct click failed:", type(e).__name__, e)


        try:
            wait2 = WebDriverWait(driver, 5)
            wait2.until(EC.element_to_be_clickable((By.CLASS_NAME, 'panel-body')))
            close_button = driver.find_element(By.CLASS_NAME, 'panel-body')
            close_button.click()
            self.logger.info('Pop-up was closed')
        except Exception as e:
            self.logger.info('No pop-up to close')
            print(f'Pop-up kapatılmadı: {e}')

        time.sleep(8)
        # Getting Verification Code

        try:
            verification_code = twilio.getSMSCode(current_datetime, self.from_number)

            def safe_send_keys(driver, by, value, keys):
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((by, value)))
                    input_element = driver.find_element(by, value)
                    input_element.clear()
                    input_element.send_keys(keys)
                    self.logger.info(f"✔ '{keys}' was written in SMS input.")
                    return True
                except Exception as e:
                    self.logger.warning(f"⚠ Doğrulama kodu alanına yazılamadı: {e}")
                    return False

            # --- Kod bloğu ---
            input_field_id = "pageContent_txtDogrulamaKodu"
            safe_send_keys(driver, By.ID, input_field_id, verification_code)

            btn = driver.find_element(By.ID, "btnCepTelDogrulamaGonder")
            driver.execute_script("arguments[0].click();", btn)

            self.logger.info(f"✔ SMS button was clicked.")
            self.logger.info(f"✔ Reservation Made - {self.tesis} - {self.brans} - {self.target_date} - {self.target_time}")

        except Exception as e:
            self.logger.error(f"Could not get verification code from SMS and did not click verification button:{e}")

        driver.quit()


        with open(self.txt_file1, "r") as file:
            content = file.read()

            entries = content.split('------------------------------------------------------------')
            for entry in entries:
                # Tarihler ve saat formatları haricinde kalan sayıları yakala
                lines = entry.strip().splitlines()
                for line in lines:
                    # Satırda tarih (dd.mm.yyyy) ya da saat aralığı varsa geç
                    if re.search(r'\d{2}\.\d{2}\.\d{4}', line) or re.search(r'\d{2}:\d{2} - \d{2}:\d{2}', line):
                        continue
                    # Satır sadece sayısal içerikse ve 0'dan büyükse
                    if line.strip().isdigit() and int(line.strip()) > 0:
                        self.__sent_sessions_list.append(entry)
                        self.__sent_sessions_list.append("***************")
                        break

            self.logger.info('Available Sessions: ' + str(self.__sent_sessions_list))

            if os.path.exists(self.txt_file2):
                with open(self.txt_file2, "r") as file:
                    existing_content = file.read()

                if ''.join(self.__sent_sessions_list).strip() == existing_content.strip():
                    self.__is_new_sessions = False
                    print('Yeni içerik mevcut içerikle aynı. Dosya güncellenmedi ve mail gönderilmedi.')
                    self.logger.warning(
                        'The new content is the same as the existing content. No file updates and e-mails did not sent.')
                else:
                    self.__is_new_sessions = True
                    with open(self.txt_file2, "w") as txt_file2:
                        for sent_session in self.__sent_sessions_list:
                            txt_file2.writelines(sent_session)
            else:
                # Dosya yoksa oluştur ve içeriği yaz
                self.__is_new_sessions = True
                with open(self.txt_file2, "w") as txt_file2:
                    for sent_session in self.__sent_sessions_list:
                        txt_file2.writelines(sent_session)
                print(f"{self.txt_file2} dosyası oluşturuldu.")
                self.logger.info(f"{self.txt_file2} file was created because it didn't exist.")

            self.__sent_sessions_list.clear()
            self.logger.info('Sent Sessions List was cleared')

    def SendEmail(self):
        with open(self.txt_file2, "r") as file:
            file_content = file.read()

        if not file_content.strip():
            print('Dosya boş, e-posta gönderilmeyecek.')
            self.logger.warning('No sessions available, no email will be sent.')
            return

        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = self.receiver_email
        message['Subject'] = f"{self.tesis} {self.brans} Boş Seanslar"
        message_content = MIMEText(f"<html><body><h3>Boş Seanslar:</h3><pre>{file_content}</pre></body></html>", 'html')
        #message_content = MIMEText(file_content, 'plain')
        message.attach(message_content)

        try:
            mail_server = smtplib.SMTP('smtp.gmail.com', 587)
            mail_server.starttls()
            mail_server.login(self.sender_email, self.sender_password)
            mail_server.send_message(message)
            mail_server.quit()
            self.logger.info('Email sent successfully to ' + self.receiver_email)
        except Exception as e:
            self.logger.error(f"Email could not sent to: {e} " + self.receiver_email)

    def sessions(self):
        with self.lock:  # <- tüm metodu thread-safe hale getiriyoruz
            if not os.path.exists(self.txt_file1):
                open(self.txt_file1, 'w').close()
            else:
                self.GetSessionInfo()
                if self.__is_new_sessions:
                    self.SendEmail()
                else:
                    return


            with open(self.txt_file2) as file:
                lines = [line.rstrip() for line in file]
            return lines


    def start(self):
        self.logger.info('AlertAvailableSessions bot started')
        self._running = True
        while self._running:
            self.sessions()
            time.sleep(int(self.polling_time))


    def stop(self):
        self.logger.info('AlertAvailableSessions bot stopped')
        self._running = False

