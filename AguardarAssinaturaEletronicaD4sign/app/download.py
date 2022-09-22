from requests import get as rest_get
import os
from d4sign import client
signature_service = client()

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
        print("Download failed: status code {}\n{}".format(downloaded_file.status_code, downloaded_file.text))

    return file_name

signed_document = signature_service.download_document('25d4991a-bfd6-4160-90f1-908d281564ea', 'PDF')


file_path = '/mnt/docs/Sites/cett-ti/documentLibrary/Processos/GerenciaContratosDeRPAProcess/outputs/'

file_names = download_file(signed_document['url'], file_path)