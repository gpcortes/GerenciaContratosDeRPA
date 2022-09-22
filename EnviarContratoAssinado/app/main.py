from worker import worker
from storage import JoomlaStorage
from time import sleep
from os.path import expanduser
import javaobj
from base64 import b64decode

worker = Worker()


def unserialize(data):
    if data.type_ == 'Object':
        java_obj = b64decode(data.value)
        return javaobj.loads(java_obj)
    elif data.type_ == 'String':
        return [data.value]
    else:
        return data


if __name__ == '__main__':
    while True:
        home = expanduser("~")

        tasks = worker.fetch_tasks(max_tasks=10)

        storage = JoomlaStorage()

        for task in tasks:
            print('Task {} processing.'.format(task.id_))
            file_name = 'Contrato RPA nº {rpaID} - {nome_completo}.pdf'.format(
                rpaID=task.variables['rpaID'].value, nome_completo=task.variables['nome_completo'].value)
            try:
                remote_file = task.variables['documento_assinado'].value
                index = remote_file.rfind('/')
                remote_file_name = remote_file[index+1:]

                storage.download(remote_file_name, home +
                                 '/outputs/', file_name)
                storage.close()

                taskVariables = {
                    'document_signed': {
                        'name': 'document_signed',
                        'value': file_name
                    }
                }

                worker.complete_task(task.id_, taskVariables)
            except:
                print('Error downloading file.')

        if len(tasks) == 0:
            sleep(30)
