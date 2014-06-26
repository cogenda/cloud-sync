# -*- coding:utf-8 -*-

""" Sync with remote webservice helper"""

import requests
from requests.auth import HTTPBasicAuth
import json

class SyncHelper(object):

    @staticmethod
    def sync_resource(filename, url, status, server):
        payload = json.dumps({'filename': filename, 'url': url, 'status': status, 'server': server, 'type': '0'})
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:8088/api/modify-resource', data=payload, headers=headers)
        print response.json()
        return json.loads(response.json())['success']
        

    @staticmethod
    def authenticate():
        basic_auth= json.dumps({'username': 'cogenda', 'password':'cogenda'})
        headers = {'content-type': 'application/json'}
        resp = requests.post('http://localhost:8088/security/authenticate', data=basic_auth, headers=headers)
        return json.loads(resp.json())['auth_success']


if __name__ == '__main__':
    authenticated = SyncHelper.authenticate()
    if not authenticated:
        print authenticated
    print SyncHelper.sync_resource('xxxxxx', 'http://test.com/xx.png', '1', 'oss')
