# -*- coding:utf-8 -*-

""" AWS S3 transporter """

from .transporter import *
from storages.backends.s3boto import S3BotoStorage
from django.conf import settings

TRANSPORTER_CLASS = "TransporterS3"

class TransporterS3(Transporter):

    name = 'S3'
    headers = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT', 
        'Cache-Control': 'max-age=86400',
        'Vary':'Accept-Encoding',
    }

    def __init__(self, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)
        try:
            self.storage = S3BotoStorage()
        except Exception, e:            
            raise ConnectionError(e)

    """
    def __init__(self, conf, callback, error_callback, parent_logger=None):
        Transporter.__init__(self, callback, error_callback, parent_logger)

        default_acl = 'public-read'
        if not conf['IS_PUBLIC']:
            default_acl = 'private'

        setattr(settings, 'OSS_ACCESS_URL', conf['OSS_ACCESS_URL'])

        try:
            self.storage = S3BotoStorage(
                    acl= default_acl,
                    bucket= conf['AWS_STORAGE_BUCKET_NAME'].encode('utf-8'),
                    self.__class__.headers
                    )
        except Exception, e:
            raise ConnectionError(e)
    """
