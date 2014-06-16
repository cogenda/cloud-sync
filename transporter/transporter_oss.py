# -*- coding:utf-8 -*-

""" AliYun OSS transporter """

from transporter import *
from aliyun_oss.backends.oss import *

TRANSPORTER_CLASS = "TransporterOSS"

class TransporterOSS(Transporter):

    name='OSS'

    def __init__(self, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        try:
            self.storage = OSSStorage()
        except Exception, e:            
            raise ConnectionError(e)


    def alter_url(self, url):
        """Alter the generated URL"""
        url = 'http://%s.%s/%s' %(OSS_STORAGE_BUCKET_NAME, ACCESS_ADDRESS, url)
        return url
