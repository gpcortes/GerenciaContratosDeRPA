from caworker import Worker
from preencher_formulario import preencherRpa
from os.path import expanduser
from os import makedirs
import time
from finanftp import FinanFTP
import json

home = expanduser("~")

worker = Worker()

template = open(home + '/templates/template_rpa.docx', 'rb')


def save_document(target_path, filename, text):
    if filename != None:
        filename = 'https://finan.cett.dev.br' + filename
        ext = filename.split('.')[-1]
        docName = 'Contrato RPA nº {text}.{ext}'.format(
            text=str(text), ext=ext)
        if ftp.download_document(filename, target_path + docName) is True:
            return True, docName
        else:
            return False, docName


if __name__ == '__main__':
    print('Worker started')
    while True:

        ftp = FinanFTP()
        tasks = worker.fetch_tasks()

        for task in tasks:
            print('Task: {}'.format(task.id_))

            rpaID = task.variables['rpaID'].value

            variables = {}

            for taskVariables in task.variables:
                variables[taskVariables] = task.variables[taskVariables].value

            docCPF = variables['docCPF'] if 'docCPF' in variables else None
            docDocumentoDeCPF = variables['docDocumentoDeCPF'] if 'docDocumentoDeCPF' in variables else None
            docRG = variables['docRG'] if 'docRG' in variables else None
            docPIS = variables['docPIS'] if 'docPIS' in variables else None
            docComprovanteEndereco = variables['docComprovanteEndereco'] if 'docComprovanteEndereco' in variables else None
            docCertidaoCasamento = variables['docCertidaoCasamento'] if 'docCertidaoCasamento' in variables else None
            docCpfDependente = variables['docCpfDependente'] if 'docCpfDependente' in variables else None
            docIdentidadeConjuge = variables['docIdentidadeConjuge'] if 'docIdentidadeConjuge' in variables else None
            docs = json.loads(
                variables['docs']) if 'docs' in variables else None
            numCPF = variables['cpf'].replace('.', '').replace(
                '-', '') if 'cpf' in variables else None

            target_path = home + '/outputs/'

            # target_path = home + '/outputs/' + numCPF
            # makedirs(target_path, exist_ok=True)

            rapDocName, emailPrestador = preencherRpa(
                rpaID, template, variables)

            taskVariables = {
                'rapDocName': {
                    'name': 'rapDocName',
                    'value': rapDocName,
                    'type': 'string'
                },
                'emailPrestador': {
                    'name': 'emailPrestador',
                    'value': emailPrestador,
                    'type': 'string'
                }
            }

            for doc in docs:
                if docs[doc]['value'] != '':
                    validate, docName = save_document(
                        target_path, docs[doc]['value'], str(rpaID) + ' - ' + docs[doc]['label'])
                    if docs[doc]['value'] != '':
                        taskVariables[doc] = {
                            'name': doc,
                            'value': docName,
                            'type': 'string'
                        }
                        docs[doc]['value'] = docName

            docs['rapDocName'] = {
                'value': rapDocName,
                'label': 'Contrato de RPA'
            }

            taskVariables['docs'] = {
                'name': 'docs',
                'value': json.dumps(docs),
                'type': 'json'
            }

            worker.complete_task(task.id_, taskVariables)
            del ftp

            time.sleep(30)
