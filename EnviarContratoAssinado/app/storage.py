import ftplib
import os

class JoomlaStorage:
    def __init__(self):
        self.FINAN_FTP_HOST, self.FINAN_FTP_USER, self.FINAN_FTP_PASSWD = self.__load_env()
        self.ftp = ftplib.FTP(self.FINAN_FTP_HOST, self.FINAN_FTP_USER, self.FINAN_FTP_PASSWD)

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

    def upload(self, file_path):
        with open(file_path, 'rb') as f:
            self.ftp.storbinary('STOR ' + file_path, f)

    def download(self, file_path, local_path, file_name):
        local_file = os.path.join(local_path, file_name)
        with open(local_file, 'wb') as f:
            self.ftp.retrbinary('RETR ' + file_path, f.write)

    def close(self):
        self.ftp.quit()