import logging
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
import pytz
from twilio.rest import Client

class Twilio:
    def __init__(self,account_sid,auth_token):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            file_handler = RotatingFileHandler('Twilio.log', maxBytes=80000 * 80000, backupCount=10)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.account_sid = account_sid
        self.auth_token = auth_token

    def getSMSCode(self, currentDateTime, fromNumber):

        client = Client(self.account_sid, self.auth_token)
        date = currentDateTime.split(" ")[0]
        year = int(date[0:4])
        month = int(date[5:7])
        day = int(date[8:10])

        messages = client.messages.list(
            date_sent_after=datetime(year, month, day),
            from_= fromNumber
        )

        try:
            verification_sms = None
            verification_code = None
            regarding_inbound_sms = {}
            for msg in messages:

                date= str(msg.date_sent.date()) + " "
                smsDateTime = str(date) + str(msg.date_sent.time())
                regarding_inbound_sms[smsDateTime] = msg.body


                for smsDate, smsPayload in regarding_inbound_sms.items():
                    if(smsDate >= currentDateTime):
                        verification_sms = smsPayload

            self.logger.info(regarding_inbound_sms)
            match = re.search(r'\b\d{4}\b', verification_sms)
            if match:
                verification_code = match.group()
            else:
                self.logger.error(f"could not find verification code from SMS")

        except Exception as e:
            self.logger.error(f"could not get verification code from SMS:{e}")
            return False

        return verification_code


if __name__ == '__main__':
    timezone = pytz.timezone('GMT')
    current_datetime = datetime.now(timezone)
    current_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    #print(current_datetime)
    twilio = Twilio("ACd5050cdc2c5442fc228499850be5d42d","f81a4085f750a652a5512a8ced187933")
    twilio.getSMSCode("2025-08-03 19:11:01","+905075502378")
