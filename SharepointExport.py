from io import BufferedReader
import os
from pathlib import Path
import requests
import logging
from typing import Dict
from datetime import datetime
from GenerateToken import Token

class SharepointExport(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='./logs/.SharepointExport_' + datetime.now().strftime('%Y-%m-%d_%H-%M') + '.log', level=logging.DEBUG)
        self.token: Dict[str, str] = {}
        self.header: Dict[str, str] = {}
        self.body: Dict[str, Dict[str, str]] = {}
        self.generator: Token = Token(plaintext=True)

    def update_token(self) -> None:
        self.token = self.generator.aquire_token()
        self.header = {'Authorization':'Bearer {}'.format(self.token['access_token'])}

    def get_file_size(self, file_path:str) -> int:
        return os.path.getsize(file_path)

    def upload_file(self, file_path: str, file_name: str, site_id: str, list_id: str, upload_path: str) -> bool:
        self.update_token()
        posix_path: str = Path(os.path.join(upload_path, file_name)).as_posix()
        file_size: int = self.get_file_size(os.path.join(file_path, file_name))
        if not file_size > 0:
            self.logger.error('File has no size: %s' % os.path.join(file_path, file_name))
            return False
        self.body = {"item": {"@microsoft.graph.conflictBehavior": "replace",'name':'{}'.format(file_name)}}
        request: requests.Response = requests.post('https://graph.microsoft.com/v1.0/sites/'+site_id+'/drives/'+list_id+'/items/root:/'+posix_path+':/createUploadSession', headers=self.header, json=self.body)
        if request.status_code == 400:
            self.logger.error('Request failed: %s' % request.reason)
            return False
        data = request.json()
        if not 'uploadUrl' in data:
            self.logger.error('uploadUrl not in data, SharepointExport.py:27')
            return False
        file: BufferedReader = open(os.path.join(file_path, file_name), "rb")
        file_data: bytes = file.read()
        file.close()
        upload_headers: Dict[str, str] = self.header
        upload_headers.update({'Content-Length': '{}'.format(file_size)})
        upload_headers.update({'Content-Range': 'bytes 0-{}/{}'.format(file_size - 1,file_size)})
        status: requests.Response = requests.put(data['uploadUrl'], headers=upload_headers,data=file_data)
        if status.status_code == 400:
            self.logger.error('Request failed: %s' % status.reason)
            return False
        return True

if __name__ == '__main__':
    exit()