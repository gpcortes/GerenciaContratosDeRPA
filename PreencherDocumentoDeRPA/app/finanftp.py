import requests
import os
import envconfiguration as config

class FinanFTP:
    def __init__(self):
        self.host = config.FINAN_FTP_HOST
        self.user = config.FINAN_FTP_USER
        self.passwd = config.FINAN_FTP_PASSWD

    def download_document(self, source, target):
        try:
            data = requests.get(source)
            with open(target, 'wb') as file:
                file.write(data.content)
            print('Document downloaded', target)
            return True
        except Exception as e:
            print(e)    
            return False
