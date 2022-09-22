import requests
import os


class FinanFTP:
    def __init__(self):
        self.host, self.user, self.passwd = self.__load_env()

    def __load_env(self):
        if os.getenv('ENV') != 'production':
            from os.path import join, dirname
            from dotenv import load_dotenv
            dotenv_path = join(dirname(__file__), 'finan.env')
            load_dotenv(dotenv_path)

        FINAN_FTP_HOST = os.getenv('FINAN_FTP_HOST')
        FINAN_FTP_USER = os.getenv('FINAN_FTP_USER')
        FINAN_FTP_PASSWD = os.getenv('FINAN_FTP_PASSWD')

        return FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD

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
