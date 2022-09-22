import jwt
import datetime
from d4sign import client
from caworker import Worker
from os.path import expanduser
from os import getenv
from time import sleep

home = expanduser("~")

worker = Worker()

DOMAIN_NAME = getenv('DOMAIN_NAME')


def create_jwt_token(private_key):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }

    return jwt.encode(payload, private_key, algorithm='HS256')


if __name__ == '__main__':
    while True:

        tasks = worker.fetch_tasks()

        for task in tasks:
            print(datetime.datetime.now().strftime(
                "%d/%m/%Y-%H:%M:%S.%f"), 'Task: {}'.format(task.id_))
            assing = client()

            emailPrestador = task.variables['emailPrestador'].value
            emailSolicitante = task.variables['emailSolicitante'].value

            rapDocName = task.variables['rapDocName'].value

            send_document_response = assing.send_document(
                (rapDocName,
                 open(home + '/outputs/' + rapDocName, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                assing.get_folder('Coletar assinatura')
            )

            if 'uuid' in send_document_response:
                uuid_document = send_document_response['uuid']
            else:
                worker.task_error(
                    task.id_, '500', send_document_response['message'])
                continue

            token = create_jwt_token(
                assing.D4SIGN_HMAC_KEY
            )

            webhook_url = 'http://' + DOMAIN_NAME + \
                ':5000/api/v1/task_update?token=' + token

            print(datetime.datetime.now().strftime(
                "%d/%m/%Y-%H:%M:%S.%f"), webhook_url)

            assing.create_webhook(
                uuid_document=uuid_document,
                webhook_url=webhook_url
            )

            signer = assing.signer.copy()
            signer['email'] = emailPrestador
            assing.signer_collection['signers'].append(signer)

            signer = assing.signer.copy()
            signer['email'] = emailSolicitante
            assing.signer_collection['signers'].append(signer)

            assing.add_signers(uuid_document, assing.signer_collection)

            task_variables = {
                'uuid_document': {
                    'name': 'uuid_document',
                    'value': uuid_document
                }
            }

            assing.send_to_sign(uuid_document)
            worker.complete_task(task.id_, task_variables)

            del assing

        if len(tasks) == 0:
            sleep(30)
