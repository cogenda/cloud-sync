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
    API_DESTROY_RESOURCE='/api/destroy-resource'
    BASIC_AUTH=json.dumps({'username': 'cogenda', 'password':'cogenda'})


    @staticmethod
    def authenticate():
        headers = {'content-type': 'application/json'}
        resp = requests.post('%s%s' %(SyncHelper.WS_HOST, SyncHelper.API_AUTHENTICATION), data=SyncHelper.BASIC_AUTH, headers=headers)
        if resp.status_code != 200:
            return None
        result = json.loads(resp.json())
        if result['auth_success']:
            return result['auth_token']
        return None


    @staticmethod
    def sync_resource(auth_token, filename, url, status, server):
        payload = json.dumps({'filename': filename, 'url': url, 'status': status, 'server': server, 'type': '0'})
        headers = {'content-type': 'application/json', 'Authorization': auth_token}
        response = requests.post('%s%s' %(SyncHelper.WS_HOST, SyncHelper.API_MODIFY_RESOURCE), data=payload, headers=headers)
        if response.status_code != 200:
            return None
        return json.loads(response.json())


    @staticmethod    
    def destroy_resource(auth_token, filename, server):
        payload = json.dumps({'filename': filename, 'server': server})
        headers = {'content-type': 'application/json', 'Authorization': auth_token}
        response = requests.post('%s%s' %(SyncHelper.WS_HOST, SyncHelper.API_DESTROY_RESOURCE), data=payload, headers=headers)
        if response.status_code != 200:
            return None
        return json.loads(response.json())




if __name__ == '__main__':
    auth_token = SyncHelper.authenticate()
    if not auth_token:
        raise SyncHelperError('Authenticate with cogenda server failed!')

    print '-----------------------'
    print auth_token
    print '-----------------------'
    print SyncHelper.sync_resource(auth_token, 'xxxxxx', 'http://test.com/xx.png', '1', 'oss')
    print SyncHelper.destroy_resource(auth_token, 'xxxxxx', 'oss')
