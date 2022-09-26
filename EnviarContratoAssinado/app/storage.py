import ftplib
import os
import envconfiguration as config


class JoomlaStorage:
    def __init__(self):
        self.FINAN_FTP_HOST = config.FINAN_FTP_HOST
        self.FINAN_FTP_USER = config.FINAN_FTP_USER
        self.FINAN_FTP_PASSWD = config.FINAN_FTP_PASSWD
        self.ftp = ftplib.FTP(self.FINAN_FTP_HOST, self.FINAN_FTP_USER, self.FINAN_FTP_PASSWD)

    def upload(self, file_path):
        with open(file_path, 'rb') as f:
            self.ftp.storbinary('STOR ' + file_path, f)

    def download(self, file_path, local_path, file_name):
        local_file = os.path.join(local_path, file_name)
        with open(local_file, 'wb') as f:
            self.ftp.retrbinary('RETR ' + file_path, f.write)

    def close(self):
        self.ftp.quit()