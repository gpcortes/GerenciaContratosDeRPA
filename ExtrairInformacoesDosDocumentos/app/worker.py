from time import sleep, time
from datetime import date, datetime
import pycamunda.externaltask
import requests.auth
import requests.sessions
import pycamunda.processinst
import getDataCNH
import platform

HOST = platform.node()

url = 'http://camunda:8080/engine-rest'
worker_id = HOST + '-pyworker-get-data-doc'

session = requests.sessions.Session()
session.auth = requests.auth.HTTPBasicAuth(
    username="admin", password="CETT@root.8401")


def execute_task(url, session, worker_id):
    fetch_and_lock = pycamunda.externaltask.FetchAndLock(
        url=url, worker_id=worker_id, max_tasks=1)
    fetch_and_lock.add_topic(name='ExtrairInformacoesDosDocumentosTask', lock_duration=30000)
    fetch_and_lock.session = session


    try:
        tasks = fetch_and_lock()
    except ValueError:
        print('Featching and locking task failed.')
        return None

    for task in tasks:
        print('Task fetched and locked.')
        complete = pycamunda.externaltask.Complete(
            url=url, id_=task.id_, worker_id=worker_id)

        file1 = task.variables.get('docCPF').value
        file2 = task.variables.get('docComprovanteEndereco').value

        index1 = file1.rfind('/')
        index2 = file2.rfind('/')

        try:
            rpaID = getDataCNH.extrairdados(
                file1[index1+1:], file2[index2+1:], task.id_)
        except:
            rpaID = getDataCNH.dadosnovos(task.id_)

        # Send this variable to the instance
        complete.add_variable(name='rpaTaskCompleted', value=True)
        complete.add_variable(name='rpaID', value=rpaID)

        getDataCNH.update_task_id(task.process_instance_id, rpaID)

        complete.session = session
        complete()

        print('Task completed with id: {}'.format(rpaID))


if __name__ == '__main__':
    print('Worker started')
    while 0 == 0:
        # try:
        #     execute_task(url, session, worker_id)
        # except:
        #     print('Internal error executing worker.')
        execute_task(url, session, worker_id)
        sleep(10)
