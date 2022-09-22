import numpy as np
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table
import requests
import base64
import json
import os
import re
import pandas as pd
import ftplib
from datetime import date, datetime
import locale
import pycamunda.task
# locale.setlocale(locale.LC_TIME, "pt_BR")

def load_env():
    if os.getenv('EVN') != 'production':
        from os.path import join, dirname
        from dotenv import load_dotenv
        dotenv_path = join(dirname(__file__), 'finan.env')
        load_dotenv(dotenv_path)

    FINAN_HOST_DB = os.getenv('FINAN_HOST_DB')
    FINAN_PORT_DB = os.getenv('FINAN_PORT_DB')
    FINAN_USER_DB = os.getenv('FINAN_USER_DB')
    FINAN_PASSWD_DB = os.getenv('FINAN_PASSWD_DB')
    FINAN_DB = os.getenv('FINAN_DB')
    FINAN_FTP_HOST = os.getenv('FINAN_FTP_HOST')
    FINAN_FTP_USER = os.getenv('FINAN_FTP_USER')
    FINAN_FTP_PASSWD = os.getenv('FINAN_FTP_PASSWD')

    return FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB, FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD


def update_task_id(instance_id, rpaID):
    engine = get_engine()
    md = MetaData(engine)

    table = Table('finan_00_recibo_de_pagamento_autonomo', md, autoload=True)
    upd = table.update(values={table.c.id_do_processo: instance_id}).where(
        table.c.id == rpaID)

    result = engine.execute(upd)

    return result


def get_engine():
    FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB, _, _, _ = load_env()
    return create_engine('mysql+pymysql://'+FINAN_USER_DB+':'+FINAN_PASSWD_DB+'@'+FINAN_HOST_DB+':'+FINAN_PORT_DB+'/'+FINAN_DB)


def ocrGoogleVisionApicnh(arquivo):

    _, _, _, _, _, FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD = load_env()

    ftp_server = ftplib.FTP(FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD)

    ftp_server.encoding = "utf-8"
    filename = arquivo

    with open(filename, "wb") as file:
        ftp_server.retrbinary(f"RETR {filename}", file.write)

    ftp_server.quit()

    caminho = os.path.join("./", filename)

    with open(caminho, "rb") as img_file:
        my_base64 = base64.b64encode(img_file.read())

    url = "https://vision.googleapis.com/v1/images:annotate?key=AIzaSyD_VXG7AQYZLH8bvFXAix91tF1SUAcpoiE"
    data = {
        'requests': [
            {
                'image': {
                    'content': my_base64.decode('utf-8'),
                },
                'features': [
                    {
                        'type': 'TEXT_DETECTION'
                    }
                ]
            }
        ]
    }

    r = requests.post(url=url, data=json.dumps(data))
    texts = r.json()['responses'][0]['textAnnotations']

    results = []

    for t in texts:
        results.append(t['description'])

    return results


def ocrGoogleVisionApiEnel(arquivo1):

    _, _, _, _, _, FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD = load_env()

    ftp_server = ftplib.FTP(FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD)

    ftp_server.encoding = "utf-8"

    filename = arquivo1

    with open(filename, "wb") as file:
        ftp_server.retrbinary(f"RETR {filename}", file.write)

    ftp_server.quit()

    caminho = os.path.join("./", filename)

    with open(caminho, "rb") as img_file:
        my_base64 = base64.b64encode(img_file.read())

    url = "https://vision.googleapis.com/v1/images:annotate?key=AIzaSyD_VXG7AQYZLH8bvFXAix91tF1SUAcpoiE"
    data = {
        'requests': [
            {
                'image': {
                    'content': my_base64.decode('utf-8'),
                },
                'features': [
                    {
                        'type': 'TEXT_DETECTION'
                    }
                ]
            }
        ]
    }

    r = requests.post(url=url, data=json.dumps(data))
    texts = r.json()['responses'][0]['textAnnotations']

    results = []

    for t in texts:
        results.append(t['description'])

    return results


def extrairdados(arquivo, arquivo1, task_id):
    texto = ocrGoogleVisionApicnh(arquivo)
    enel = ocrGoogleVisionApiEnel(arquivo1)

    try:
        cnh_ = texto[0].split('\nVALIDADE')[1].split('OBSERVAÇÕES')[0]
        cnh_ = re.split(r'\d{2}/\d{2}/\d{4}', cnh_)[1]
        cnh_ = cnh_.split('\n')[1]
    except:
        cnh_ = None

    try:
        orgao_emissor = texto[0].split('EMISSOR')[1].split('\nCPF')[0]
        orgao_emissor = re.findall(r'SSP|DGPC|PC|SPTC', orgao_emissor)
        if orgao_emissor == []:
            orgao_emissor = None
    except:
        orgao_emissor = None

    try:
        rg = texto[0].split('EMISSOR')[1].split(
            'GO')[0].split('\n')[1].split(' ')[0]
    except:
        rg = str(texto).split('\'REGISTRO\', \'GERAL\',')[
            1].split('EXPEDIÇÃO')[0]
        rg = re.findall(r'\d+', rg)[0]

    try:
        nome_pai = texto[0].split('DATA NASCIMENTO')[1].split('PERMISSÃO')[0]
        nome_pai = re.split(r'FIUAÇÃO|FILIAÇÃO', nome_pai)[1].split('\n')[1]
        nome_mae = None
    except:
        nome_pai = str(texto).split('nFILIAÇÃO')[1].split('\\n')[0].strip()
        nome_mae = str(texto).split('nFILIAÇÃO')[1].split('\\n')[1].strip()

    try:
        emissao = texto[0].split('\nDATA EMISSÃO')[1].split(
            '\nASSINATURA DO EMISSOR')[0]
        emissao = re.findall(r'\d{2}/\d{2}/\d{4}', emissao)[0]
    except:
        emissao = str(texto).split('EXPEDIÇÃO')[1].split('FILIAÇÃO')[0]
        emissao = re.findall(r'\d{2}/\w{3}/\d{4}', emissao)[0].replace(
            'N0V', 'NOV').replace('0UT', 'OUT').replace('AG0', 'AGO')
        emissao = datetime.strptime(emissao, '%d/%b/%Y')
        emissao = datetime.strftime(emissao, '%Y-%m-%d')

    try:
        data_nascimento = re.split(r'CARTEIRA NACIONAL|CARTETRA NACIONAL', str(texto[0]))[
            1].split('VALIDADE')[0]
        data_nascimento = re.findall(r'\d{2}/\d{2}/\d{4}', data_nascimento)[0]
    except:
        rg_ = str(texto)
        data_nascimento = rg_.split('nFILIAÇÃO')[
            1].split('DATA DE NASCIMENTO')[0]
        data_nascimento = re.findall(r'\d{2}/\w{3}/\d{4}', data_nascimento)[0].replace(
            'N0V', 'NOV').replace('0UT', 'OUT').replace('AG0', 'AGO')
        data_nascimento = datetime.strptime(data_nascimento, '%d/%b/%Y')
        data_nascimento = datetime.strftime(data_nascimento, '%Y-%m-%d')

    try:
        nome = re.split('NOME', texto[0])[1].split('\n')[1].strip()
    except:
        nome = texto[0].split('NOME')[0]
        nome = re.split(r'\d{2}/\w{3}/\d{4}', nome)[1].split('\n')[1]

    try:
        cpf = re.split('CARTEIRA NACIONAL|CARTETRA NACIONAL',
                       texto[0])[1].split('FILIAÇÃO')[0]
        cpf = re.findall(
            r'\d{3}.\d{3}.\d{3}-\d{2}|\d{3}.\d{3}, \d{3}-\d{2}', cpf)[0].replace(', ', '.')

    except:
        cpf = str(texto)
        cpf = re.findall(
            r'\d{3}.\d{3}.\d{3}-\d{2}|\d{9}-\d{2}|\d{9}/\d{2}', cpf)[0]

    try:
        cep = re.split(r'\nCEP|\nCEP:', enel[0])[1]
        cep = re.findall(r'\d{8}|\d{5}-\d{3}|\d{2}.\d{3}-\d{3}', cep)[0]
    except:
        saneago = str(enel)
        cep = re.findall(r'\d{8}|\d{5}-\d{3}|\d{2}.\d{3}-\d{3}', saneago)[0]

    global rpa_cpf
    rpa_cpf = pd.read_sql_query(
        'select * from finan_00_recibo_de_pagamento_autonomo where id = (select MAX(id) from finan_00_recibo_de_pagamento_autonomo where cpf = \''+cpf+'\')', con=get_engine())

    if rpa_cpf.empty:
        cnh = [{'nome_completo': nome,
               'situacao': '',
                'cpf': cpf,
                'data_de_nascimento': data_nascimento,
                'sexo': '',
                'n_pis_pasep': '',
                'rg': rg,
                'cnh': cnh_,
                'orgao_emissor': orgao_emissor,
                'data_de_emissao': emissao,
                'nome_mae': nome_mae,
                'nome_pai': nome_pai,
                'banco': '',
                'agencia': '',
                'conta': '',
                'tipo_da_conta': '',
                'endereco': '',
                'n': '',
                'cep': cep,
                'bairro_setor': '',
                'complemento': '',
                'cidade': '',
                'e_mail': '',
                'celular': '',
                'nome_do_dependente_1': '',
                'grau_de_parentesco_1': '',
                'cpf_do_filho_1': '',
                'entra_na_declaraco_de_ir_1_': '',
                'data_de_nascimento_do_filho_1': '',
                'nome_do_dependente_2': '',
                'grau_de_parentesco_2': '',
                'cpf_do_filho_2': '',
                'entra_na_declaracao_de_ir_2_': '',
                'data_de_nascimento_do_filho_2': '',
                'descricao_da_atividade_executada': '',
                'data_inicio': '',
                'data_fim': '',
                'valor_liquido': '',
                'local_da_prestacao_do_servico': ''}]

        df = pd.DataFrame.from_dict(cnh)
        df.data_de_nascimento = pd.to_datetime(df.data_de_nascimento)
        df.data_de_emissao = pd.to_datetime(df.data_de_emissao)
        df.data_inicio = pd.to_datetime(df.data_inicio)
        df.data_fim = pd.to_datetime(df.data_fim)
        df.to_sql('finan_00_recibo_de_pagamento_autonomo',
                  con=get_engine(), if_exists='append', index=False)
        id_ = pd.read_sql_query(
            'select MAX(id) from finan_00_recibo_de_pagamento_autonomo WHERE cpf = \''+cpf+'\'', con=get_engine())
        id_list = id_['MAX(id)'].values.tolist()
        id_str = id_list[0]
        return id_str

    else:
        cnh = [{'nome_completo': rpa_cpf.nome_completo.values[0],
                'situacao': '',
                'cpf': rpa_cpf.cpf.values[0],
                'data_de_nascimento': rpa_cpf.data_de_nascimento.values[0],
                'sexo': rpa_cpf.sexo.values[0],
                'n_pis_pasep': rpa_cpf.n_pis_pasep.values[0],
                'rg': rpa_cpf.rg.values[0],
                'cnh': rpa_cpf.cnh.values[0],
                'orgao_emissor': rpa_cpf.orgao_emissor.values[0],
                'data_de_emissao': rpa_cpf.data_de_emissao.values[0],
                'nome_mae': rpa_cpf.nome_mae.values[0],
                'nome_pai': rpa_cpf.nome_pai.values[0],
                'banco': rpa_cpf.banco.values[0],
                'agencia': rpa_cpf.agencia.values[0],
                'conta': rpa_cpf.conta.values[0],
                'tipo_da_conta': rpa_cpf.tipo_da_conta.values[0],
                'endereco': rpa_cpf.endereco.values[0],
                'n': rpa_cpf.n.values[0],
                'cep': rpa_cpf.cep.values[0],
                'bairro_setor': rpa_cpf.bairro_setor.values[0],
                'complemento': rpa_cpf.complemento.values[0],
                'cidade': rpa_cpf.cidade.values[0],
                'e_mail': rpa_cpf.e_mail.values[0],
                'celular': rpa_cpf.celular.values[0],
                'nome_do_dependente_1': rpa_cpf.nome_do_dependente_1.values[0],
                'grau_de_parentesco_1': rpa_cpf.grau_de_parentesco_1.values[0],
                'cpf_do_filho_1': rpa_cpf.cpf_do_filho_1.values[0],
                'entra_na_declaraco_de_ir_1_': rpa_cpf.entra_na_declaraco_de_ir_1_.values[0],
                'data_de_nascimento_do_filho_1': rpa_cpf.data_de_nascimento_do_filho_1.values[0],
                'nome_do_dependente_2': rpa_cpf.nome_do_dependente_2.values[0],
                'grau_de_parentesco_2': rpa_cpf.grau_de_parentesco_2.values[0],
                'cpf_do_filho_2': rpa_cpf.cpf_do_filho_2.values[0],
                'entra_na_declaracao_de_ir_2_': rpa_cpf.entra_na_declaracao_de_ir_2_.values[0],
                'data_de_nascimento_do_filho_2': rpa_cpf.data_de_nascimento_do_filho_2.values[0],
                'descricao_da_atividade_executada': '',
                'data_inicio': '',
                'data_fim': '',
                'valor_liquido': '',
                'local_da_prestacao_do_servico': ''}]

        df = pd.DataFrame.from_dict(cnh)
        df.data_de_nascimento = pd.to_datetime(df.data_de_nascimento.iloc[0])
        df.data_de_emissao = pd.to_datetime(df.data_de_emissao.iloc[0])
        df.data_inicio = pd.to_datetime(df.data_inicio.iloc[0])
        df.data_fim = pd.to_datetime(df.data_fim.iloc[0])
        result = df.to_sql('finan_00_recibo_de_pagamento_autonomo',
                           con=get_engine(), if_exists='append', index=False)
        id_ = pd.read_sql_query(
            'select MAX(id) from finan_00_recibo_de_pagamento_autonomo WHERE cpf = \''+cpf+'\'', con=get_engine())
        id_list = id_['MAX(id)'].values.tolist()
        id_str = id_list[0]
        return id_str


def dadosnovos(task_id):
    cnh = [{'nome_completo': '',
            'situacao': '',
            'cpf': '',
            'data_de_nascimento': '',
            'sexo': '',
            'n_pis_pasep': '',
            'rg': '',
            'cnh': '',
            'orgao_emissor': '',
            'data_de_emissao': '',
            'nome_mae': '',
            'nome_pai': '',
            'banco': '',
            'agencia': '',
            'conta': '',
            'tipo_da_conta': '',
            'endereco': '',
            'n': '',
            'cep': '',
            'bairro_setor': '',
            'complemento': '',
            'cidade': '',
            'e_mail': '',
            'celular': '',
            'nome_do_dependente_1': '',
            'grau_de_parentesco_1': '',
            'cpf_do_filho_1': '',
            'entra_na_declaraco_de_ir_1_': '',
            'data_de_nascimento_do_filho_1': '',
            'nome_do_dependente_2': '',
            'grau_de_parentesco_2': '',
            'cpf_do_filho_2': '',
            'entra_na_declaracao_de_ir_2_': '',
            'data_de_nascimento_do_filho_2': '',
            'descricao_da_atividade_executada': '',
            'data_inicio': '',
            'data_fim': '',
            'valor_liquido': '',
            'local_da_prestacao_do_servico': '',
            'id_do_processo': task_id}]
    df = pd.DataFrame.from_dict(cnh)
    df.to_sql('finan_00_recibo_de_pagamento_autonomo',
              con=get_engine(), if_exists='append', index=False)
    id_ = pd.read_sql_query(
        'select MAX(id) from finan_00_recibo_de_pagamento_autonomo', con=get_engine())
    id_list = id_['MAX(id)'].values.tolist()
    id_str = id_list[0]
    return id_str
