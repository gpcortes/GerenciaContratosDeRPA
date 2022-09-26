from datetime import datetime, date
from docxtpl import DocxTemplate
import pandas as pd
from sqlalchemy import create_engine, text
from os.path import expanduser
import sys
import subprocess
import re
import os
import ftplib
import envconfiguration as config


home = expanduser("~")

def load_env():
    FINAN_HOST_DB = config.FINAN_HOST_DB
    FINAN_PORT_DB = config.FINAN_PORT_DB
    FINAN_USER_DB = config.FINAN_USER_DB
    FINAN_PASSWD_DB = config.FINAN_PASSWD_DB
    FINAN_DB = config.FINAN_DB

    return FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB

def convert_to(source, folder, timeout=None):
    args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', source, '--outdir', folder]

    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    filename = re.search('-> (.*?) using filter', process.stdout.decode())

    if filename is None:
        raise LibreOfficeError(process.stdout.decode())
    else:
        return os.path.basename(filename.group(1))

def libreoffice_exec():
    # TODO Provide support for more platforms
    if sys.platform == 'darwin':
        return '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    elif sys.platform == 'linux':
        return 'soffice'
    else: 
        return 'libreoffice'


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output
    
def get_engine():
    FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB = load_env()
    return create_engine('mysql+pymysql://'+FINAN_USER_DB+':'+FINAN_PASSWD_DB+'@'+FINAN_HOST_DB+':'+FINAN_PORT_DB+'/'+FINAN_DB)

def preencherRpa(id_, template, variables={}):

    dados = pd.read_sql_query(
        'select * from finan_00_recibo_de_pagamento_autonomo WHERE id = \''+str(id_)+'\'', con=get_engine())

    dados['data_de_nascimento'] = datetime.strftime(
        pd.Timestamp(dados['data_de_nascimento'].values[0]), '%Y-%m-%d')
    dados['data_de_emissao'] = datetime.strftime(
        pd.Timestamp(dados['data_de_emissao'].values[0]), '%Y-%m-%d')
    dados['data_do_rpa'] = date.today()
 
    for variable in variables:
        dados[variable] = variables[variable]

    emailPrestador = dados['e_mail'].values[0]
    rpaID = dados['rpaID'].values[0]
    nome_completo = dados['nome_completo'].values[0]

    doc1 = DocxTemplate(template)
    doc1.render(dados.iloc[0])
    docName = ('Contrato RPA nº {rpaID} - {nome_completo}.docx'.format(rpaID=rpaID, nome_completo=nome_completo))
    doc1.save(home + '/outputs/' + docName)

    pdfFileName = convert_to(home + '/outputs/' + docName, home + '/outputs')

    return pdfFileName, emailPrestador
