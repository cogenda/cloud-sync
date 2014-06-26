# -*- coding:utf-8 -*-

""" Sync with remote webservice helper"""

import requests
from requests.auth import HTTPBasicAuth
import json

# Define exceptions.
class SyncHelperError(Exception): pass

class SyncHelper(object):

    WS_HOST='http://localhost:8088'
    API_AUTHENTICATION='/security/authenticate-ws'
    API_MODIFY_RESOURCE='/api/modify-resource'
    BASIC_AUTH=json.dumps({'username': 'cogenda', 'password':'cogenda'})

    @staticmethod
    def sync_resource(auth_token, filename, url, status, server):
        payload = json.dumps({'filename': filename, 'url': url, 'status': status, 'server': server, 'type': '0'})
        headers = {'content-type': 'application/json', 'Authorization': auth_token}
        response = requests.post('%s%s' %(SyncHelper.WS_HOST, SyncHelper.API_MODIFY_RESOURCE), data=payload, headers=headers)
        print response.json()
        return json.loads(response.json())['success']
        

    @staticmethod
    def authenticate():
        headers = {'content-type': 'application/json'}
        resp = requests.post('%s%s' %(SyncHelper.WS_HOST, SyncHelper.API_AUTHENTICATION), data=SyncHelper.BASIC_AUTH, headers=headers)
        result = json.loads(resp.json())
        if result['auth_success']:
            return result['auth_token']
        return None


if __name__ == '__main__':
    auth_token = SyncHelper.authenticate()
    if not auth_token:
        raise SyncHelperError('Authenticate with cogenda server failed!')

    print '-----------------------'
    print auth_token
    print '-----------------------'
    SyncHelper.sync_resource(auth_token, 'xxxxxx', 'http://test.com/xx.png', '1', 'oss')
