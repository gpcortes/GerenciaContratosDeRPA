from flask import Flask, request
import jwt
import json
from functools import wraps
from caworker import Worker
import hmac
from requests import get as rest_get
import os
home = os.path.expanduser("~")

worker = Worker()

app = Flask(__name__)

APP_DEBUG = True if os.getenv('NODE_ENV') != 'production' else False


def download_file(url, file_path):

    downloaded_file = rest_get(url, allow_redirects=True)

    file_name = downloaded_file.headers.get('FileName')

    output_file = file_path + file_name

    if downloaded_file.ok:
        print("Document saving to", os.path.abspath(output_file))
        with open(output_file, 'wb') as f:
            for chunk in downloaded_file.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:
        print("Download failed: status code {}\n{}".format(
            downloaded_file.status_code, downloaded_file.text))

    return file_name


def tokenRequired(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        from d4sign import client
        signature_service = client()
        if 'token' in request.args:
            token = request.args['token']
        elif 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        else:
            print('Token is missing!')
            return json.dumps({'message': 'Token is missing!'}), 401

        try:
            jwt.decode(token, signature_service.D4SIGN_HMAC_KEY,
                       algorithms=['HS256'])
        except:
            print('Token provided is invalid!')
            return json.dumps({'message': 'Token provided is invalid!'}), 401

        return function(*args, **kwargs)

    return decorated


def verify_hmac(hmac_provided, data, secret):
    hmac_calculated = hmac.new(
        secret.encode('utf-8'),
        msg=data.encode('utf-8'),
        digestmod='sha256'
    ).hexdigest()
    print('Calculated:', 'sha256=' + hmac_calculated)
    print('Provided:', hmac_provided)
    return hmac_provided == 'sha256=' + hmac_calculated


@app.route('/api/v1/task_update', methods=['POST'])
# @tokenRequired
def task_update():
    if 'Content-Hmac' in request.headers and 'uuid' in request.json:
        from d4sign import client
        signature_service = client()
        content_hmac = request.headers['Content-Hmac']
        uuid_document = request.json['uuid']

        if not verify_hmac(content_hmac, uuid_document, signature_service.D4SIGN_HMAC_KEY):
            print("Hmac verification failed! -> ", content_hmac)
            return json.dumps({'message': 'HMAC is invalid!'}), 401

        if 'message' in request.json:
            if request.json['type_post'] == "1":

                tasks = worker.fetch_tasks(topic=uuid_document)

                for task in tasks:

                    signed_document = signature_service.download_document(
                        task.variables['uuid_document'].value)
                    home = os.path.expanduser("~")
                    file_path = home + '/outputs/'

                    file_names = download_file(
                        signed_document['url'], file_path)
                    task_variables = {
                        'document_signed': {
                            'name': 'document_signed',
                            'value': file_names,
                            'type': 'string'
                        }
                    }

                    resp = worker.complete_task(task.id_, task_variables)

                    print('Task complete: ' + task.id_)

                del signature_service
                return json.dumps({'message': 'Task complete!'}), 200
            else:
                print('Task not completed!')
                del signature_service
                return json.dumps({'message': 'Task not completed!'})
        else:
            print('Notification received')
            del signature_service
            return json.dumps({'message': 'Notification received'}), 200
    else:
        print('Without identification')
        return json.dumps({'message': 'Without identification'}), 401


if __name__ == '__main__':
    app.run(debug=APP_DEBUG, host='0.0.0.0', port=5000)
