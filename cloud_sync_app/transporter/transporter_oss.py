# -*- coding:utf-8 -*-

""" AliYun OSS transporter """

from .transporter import *
from ..aliyun_oss.backends.oss import *

TRANSPORTER_CLASS = "TransporterOSS"

class TransporterOSS(Transporter):

    name = 'OSS'

    def __init__(self, conf, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        default_acl = 'public-read'
        default_bucket = conf['OSS_STORAGE_BUCKET_NAME']
        if not conf['IS_PUBLIC']:
            default_acl = 'private'
            default_bucket = conf['OSS_STORAGE_BUCKET_PVT_NAME']

        try:
            self.storage = OSSStorage(
                bucket=default_bucket.encode('utf-8'),
                acl=default_acl
            )
        except Exception, e:
            raise ConnectionError(e)
