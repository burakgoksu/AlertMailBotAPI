import logging
import os
from logging.handlers import RotatingFileHandler
from selenium import webdriver
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


class AlertAvailableSessions:
    def __init__(self, link1, link2, txt_file1, txt_file2, sender_email, sender_password, receiver_email, headless=True):
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
        self.chrome_option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0")
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

    def GetSessionInfo(self):

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")  # This is important for some versions of Chrome
        chrome_options.add_argument("--remote-debugging-port=9222")  # This is recommended
        chrome_options.add_argument("--window-size=1280,1024")
        chrome_options.add_argument("--disable-software-rasterizer")

        # Set path to Chrome binary
        chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"
        #/opt/chrome/chrome-linux64/chrome
        # Set path to ChromeDriver
        chrome_service = Service(executable_path="/opt/chromedriver/chromedriver-linux64/chromedriver")

        # Set up driver
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_option)
        try:
            driver.get(self.link1)

            # Bekleme: Öğelerin yüklenmesini bekleyin
            wait = WebDriverWait(driver, 10)
            tc_no = wait.until(EC.presence_of_element_located((By.ID, 'txtTCPasaport')))
            tc_no.send_keys('53875003034')
            password = wait.until(EC.presence_of_element_located((By.ID, 'txtSifre')))
            password.send_keys('B1245789630g')
            login_buton = wait.until(EC.element_to_be_clickable((By.ID, 'btnGirisYap')))
            login_buton.click()
            self.logger.info('Login Successfully')
        except Exception as e:
            self.logger.error(f'Login failed: {e}')
            driver.quit()
            return

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

        time.sleep(2)

        try:
            wait2 = WebDriverWait(driver, 5)
            wait2.until(EC.element_to_be_clickable((By.ID, 'closeModal')))
            close_button = driver.find_element(By.ID, 'closeModal')
            close_button.click()
            self.logger.info('Pop-up was closed')
        except Exception as e:
            self.logger.info('No pop-up to close')
            print(f'Pop-up kapatılmadı: {e}')

        time.sleep(2)
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

        driver.quit()

        with open(self.txt_file1, "r") as file:
            content = file.read()

            entries = content.split('------------------------------------------------------------')
            for entry in entries:
                if(entry.find("Yer Var") > 0):
                    self.__sent_sessions_list.append(entry)
                    self.__sent_sessions_list.append("***************")

            self.logger.info('Available Sessions: ' + str(self.__sent_sessions_list))

            if os.path.exists(self.txt_file2):
                with open(self.txt_file2, "r") as file:
                    existing_content = file.read()

                if ''.join(self.__sent_sessions_list).strip() == existing_content.strip():
                    self.__is_new_sessions = False
                    print('Yeni içerik mevcut içerikle aynı. Dosya güncellenmedi ve mail gönderilmedi.')
                    self.logger.warning('The new content is the same as the existing content. No file updates and e-mails did not sent.')
                else:
                    self.__is_new_sessions = True
                    with open(self.txt_file2, "w") as txt_file2:
                        for sent_session in self.__sent_sessions_list:
                            txt_file2.writelines(sent_session)

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
        message['Subject'] = 'Ümraniye Çakmak Yüzme Havuzu Boş Seanslar'
        message_content = MIMEText(file_content, 'plain')
        message.attach(message_content)

        try:
            mail_server = smtplib.SMTP('smtp.gmail.com', 587)
            mail_server.starttls()
            mail_server.login(self.sender_email, self.sender_password)
            mail_server.send_message(message)
            mail_server.quit()
            print('E-posta başarıyla gönderildi')
            self.logger.info('Email sent successfully to ' + self.receiver_email)
        except Exception as e:
            print(f'E-posta gönderilemedi: {e}')
            self.logger.error('Email could not sent to ' + self.receiver_email)

    def sessions(self):
        if not os.path.exists(self.txt_file1):
            pass
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
            time.sleep(600)


    def stop(self):
        self.logger.info('AlertAvailableSessions bot stopped')
        self._running = False
