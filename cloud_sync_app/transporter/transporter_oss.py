# -*- coding:utf-8 -*-

""" AliYun OSS transporter """

from .transporter import *
from ..aliyun_oss.backends.oss import *

TRANSPORTER_CLASS = "TransporterOSS"

class TransporterOSS(Transporter):
    name='OSS'
    headers = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT',
        'Cache-Control': 'max-age=31536000',
    }

    def __init__(self, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        try:
            self.storage = OSSStorage()
        except Exception, e:            
            raise ConnectionError(e)

    """
    def __init__(self, settings, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        default_acl = 'public-read'
        if not settings['IS_PUBLIC']:
            default_acl = 'private'

        try:
            self.storage = OSSStorage(
                    bucket=settings['OSS_STORAGE_BUCKET_NAME'].encode('utf-8'),
                    acl = default_acl,
                    self.__class__.headers
                    )
        except Exception, e:            
            raise ConnectionError(e)
    """
