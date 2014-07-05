# -*- coding:utf-8 -*-

""" Sync with remote webservice helper"""

import requests
from requests.auth import HTTPBasicAuth
import json
import hmac
import base64
import hashlib

# Define exceptions.
class SyncHelperError(Exception): pass

class SyncHelper(object):

    def __init__(self, 
            cogenda_shared_secret='cogenda-ws-secret', 
            ws_host='http://localhost:8088', 
            api_modify_resource='/api/modify-resource',
            api_destroy_resource='/api/destroy-resource'):
        self.cogenda_shared_secret = cogenda_shared_secret
        self.ws_host = ws_host
        self.api_modify_resource = api_modify_resource
        self.api_destroy_resource = api_destroy_resource


    def sync_resource(self, filename, url, server, desc, type, status='1'):
        payload = json.dumps({
            'filename': filename, 
            'url': url, 
            'status': status, 
            'server': server, 
            'type': type,
            'desc': desc
            })
        auth_token = self._make_hamc_key(payload)
        headers = {'content-type': 'application/json', 'Authorization': auth_token}
        response = requests.post('%s%s' %(self.ws_host, self.api_modify_resource), data=payload, headers=headers)
        if response.status_code != 200:
            return None
        return json.loads(response.json())


    def destroy_resource(self, filename, server):
        payload = json.dumps({'filename': filename, 'server': server})
        auth_token = self._make_hamc_key(payload)
        headers = {'content-type': 'application/json', 'Authorization': auth_token}
        response = requests.post('%s%s' %(self.ws_host, self.api_destroy_resource), data=payload, headers=headers)
        if response.status_code != 200:
            return None
        return json.loads(response.json())


    def _make_hamc_key(self, message):
        """ Generate HMAC key """
        auth_token = base64.b64encode(hmac.new(self.cogenda_shared_secret, message, digestmod=hashlib.sha256).digest())
        return auth_token


if __name__ == '__main__':

    WS_HOST='http://localhost:8088'
    API_MODIFY_RESOURCE='/api/modify-resource'
    API_DESTROY_RESOURCE='/api/destroy-resource'

    syncHelper = SyncHelper(ws_host=WS_HOST, 
            cogenda_shared_secret='cogenda-ws-secret', 
            api_modify_resource=API_MODIFY_RESOURCE, 
            api_destroy_resource=API_DESTROY_RESOURCE)

    print syncHelper.sync_resource('xxxxxx', 'http://test.com/xx.png', '1', 'oss')
    print syncHelper.destroy_resource('xxxxxx', 'oss')
