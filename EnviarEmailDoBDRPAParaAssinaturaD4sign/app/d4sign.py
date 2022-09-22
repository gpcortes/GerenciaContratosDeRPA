import os
import requests
import json
from requests_toolbelt import MultipartEncoder

class client:
    def __init__(self):
        self.D4SIGN_TOKEN, self.D4SIGN_KEY, self.D4SIGN_URL, self.D4SIGN_SAFE, self.D4SIGN_HMAC_KEY = self.__load_env()
        self.UUID_SAFE = self.__get_safe(self.D4SIGN_SAFE)
        self.signers = {
            'signers': []
        }
        self.signer_collection = self.signers.copy()
        self.signer = {
            "email": "",
            "act": "1",
            "foreign": "1",
            "foreign_lang": "ptBR",
            "certificadoicpbr": "0",
            "assinatura_presencial": "0",
            "docauth": "0",
            "docauthandselfie": "0",
            "embed_methodauth": "email",
            "embed_smsnumber": "",
            "upload_allow": "0",
            "upload_obs": "Contrato RPA",
            "after_position": "0",
            "skipemail": "0",
            "whatsapp_number": "",
            "uuid_grupo": "",
            "certificadoicpbr_tipo": "0",
            "certificadoicpbr_cpf": "",
            "certificadoicpbr_cnpj": "",
            "password_code": "",
            "auth_pixel": "0",
            "auth_pix_nome": "",
            "auth_pix_cpf": "",
            "videoselfie": "0",
            "d4sign_score": "0",
            "d4sign_score_nome": "",
            "d4sign_score_cpf": "",
            "d4sign_score_similarity": "75",
        }
        self.fields = {}

    def __load_env(self):
        if os.getenv('NODE_ENV') != 'production':
            from os.path import join, dirname
            from dotenv import load_dotenv
            dotenv_path = join(dirname(__file__), 'd4sign.env')
            load_dotenv(dotenv_path)

        D4SIGN_TOKEN = os.getenv('D4SIGN_TOKEN')
        D4SIGN_KEY = os.getenv('D4SIGN_KEY')
        D4SIGN_URL = os.getenv('D4SIGN_URL')
        D4SIGN_SAFE = os.getenv('D4SIGN_SAFE')
        D4SIGN_HMAC_KEY = os.getenv('D4SIGN_HMAC_KEY')

        return D4SIGN_TOKEN, D4SIGN_KEY, D4SIGN_URL, D4SIGN_SAFE, D4SIGN_HMAC_KEY

    def __send(self, method, payload=None):

        http_method = 'POST' if payload else 'GET'

        url = self.D4SIGN_URL + method

        querystring = {
            "tokenAPI": self.D4SIGN_TOKEN,
            "cryptKey": self.D4SIGN_KEY
        }

        try:
            content_type = payload.content_type
        except:
            content_type = "application/json"

        headers = {"Content-Type": content_type}

        response = requests.request(
            http_method, url, headers=headers, params=querystring, data=payload
        )

        return json.loads(response.text)

    def __get_safe(self, name_safe):
        safe = self.__send('safes')

        print(safe)

        uuid_safe = None

        for dict in safe:
            if dict['name-safe'] == name_safe:
                uuid_safe = dict['uuid_safe']
                break

        return uuid_safe

    def get_folder(self, name_folder):
        folder = self.__send(
            'folders/{uuid_safe}/find'.format(uuid_safe=self.UUID_SAFE))

        uuid_folder = None

        for dict in folder:
            if dict['name'] == name_folder:
                uuid_folder = dict['uuid_folder']
                break

        return uuid_folder

    def send_document(self, file, uuid_folder):
        payload = MultipartEncoder(
            fields={
                'file': file,
                'uuid_folder': uuid_folder
            }
        )

        return self.__send('documents/{uuid_safe}/upload'.format(uuid_safe=self.UUID_SAFE), payload)

    def add_signers(self, uuid_document, signers):
        return self.__send('documents/{uuid_document}/createlist'.format(uuid_document=uuid_document), json.dumps(signers))

    def list_signers(self, uuid_document):
        return self.__send('documents/{uuid_document}/list'.format(uuid_document=uuid_document))

    def send_to_sign(self, uuid_document):
        payload = {
            "message": "Assinatura de documento",
            "skip_email": "0",
            "workflow": "0",
        }

        return self.__send('documents/{uuid_document}/sendtosigner'.format(uuid_document=uuid_document), json.dumps(payload))

    def create_folder(self, folder_name):
        payload = {
            "folder_name": folder_name,
        }

        return self.__send('folders/create', json.dumps(payload))

    def download_document(self, uuid_document):
        payload = {
            "type": "PDF",
            "language": "pt"
        }

        return self.__send('documents/{uuid_document}/download'.format(uuid_document=uuid_document), json.dumps(payload))

    def create_webhook(self, uuid_document, webhook_url):
        payload = {
            "url": webhook_url
        }

        return self.__send('documents/{uuid_document}/webhooks'.format(uuid_document=uuid_document), json.dumps(payload))
