# -*- coding:utf-8 -*-
import os

########################################################
#           Dummy settings for `django-storages`       #
########################################################
SECRET_KEY = 'cloud-sync-service'

########################################################
#               AWS S3 SETTINGS                        #
########################################################
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_QUERYSTRING_EXPIRE = 60*60*24*365*10
# The minimum part size(byte) (if there is more than one part). This value must be >= 5M
AWS_S3_FILE_BUFFER_SIZE = 5*1024*1024
AWS_HEADERS = {
    'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT',
    'Cache-Control': 'max-age=86400',
    'Vary': ' Accept-Encoding',
}

########################################################
#               AliYun OSS SETTINGS                    #
########################################################
OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', None)
OSS_SECRET_ACCESS_KEY = os.environ.get('OSS_SECRET_ACCESS_KEY', None)
OSS_STORAGE_BUCKET_NAME = 'cogenda-qd'
OSS_QUERYSTRING_EXPIRE = 60*60*24*365*10
OSS_FILE_BUFFER_SIZE = 5*1024*1024
OSS_HEADERS = {
    'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT',
    'Cache-Control': 'max-age=31536000',
}
