# -*- coding:utf-8 -*-
import os
import logging

""" Dummy settings for `django-storages` """
SECRET_KEY='cogenda-cloud-sync'
MEDIA_URL=''
MEDIA_ROOT=''

########################################################
#             SYNC COGENDA WEB SETTINGS             #           
########################################################
WS_HOST='http://localhost:8088'
API_MODIFY_RESOURCE='/api/modify-resource'
API_DESTROY_RESOURCE='/api/destroy-resource'
COGENDA_SHARED_SECRET='cogenda-ws-secret'


########################################################
#               CLOUD SYNC SETTINGS                    #           
########################################################
RESTART_AFTER_UNHANDLED_EXCEPTION = False
RESTART_INTERVAL = 10
LOG_FILE = './cloud_sync.log'
PID_FILE = '/tmp/cloud_sync.pid'
PERSISTENT_DATA_DB = './cloud_sync.db'
SYNCED_FILES_DB = './cloud_sync.db'
FSMONITOR_DB = './cloud_sync.db'
CONSOLE_LOGGER_LEVEL = logging.INFO
FILE_LOGGER_LEVEL = logging.INFO
MAX_SIMULTANEOUS_TRANSPORTERS = 10
MAX_TRANSPORTER_QUEUE_SIZE = 5 
MAX_TRANSPORTER_POOL_SIZE = 5
QUEUE_PROCESS_BATCH_SIZE = 20
CALLBACKS_CONSOLE_OUTPUT = True
RETRY_INTERVAL=30


########################################################
#               AWS S3 SETTINGS                        #           
########################################################
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_QUERYSTRING_EXPIRE = 60*60*24*365*10
#The minimum part size(byte) (if there is more than one part). This value must be >= 5M
AWS_S3_FILE_BUFFER_SIZE=5*1024*1024
AWS_HEADERS = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT', 
        'Cache-Control': 'max-age=86400',
        'Vary':'Accept-Encoding',
        }
""" The `private/public` bucket name """
AWS_STORAGE_BUCKET_NAME = 'cogenda'
""" `True` for priavte file, `False` for public file """
AWS_QUERYSTRING_AUTH = False


""" `private` for private file, `public-read` for public file """
AWS_DEFAULT_ACL='public-read'


########################################################
#               AliYun OSS SETTINGS                    #           
########################################################
OSS_ACCESS_URL='oss-cn-qingdao-a.aliyuncs.com'
OSS_ACCESS_KEY_ID=os.environ.get('OSS_ACCESS_KEY_ID', None)
OSS_SECRET_ACCESS_KEY=os.environ.get('OSS_SECRET_ACCESS_KEY', None)
OSS_QUERYSTRING_EXPIRE = 60*60*24*365*10
OSS_HEADERS = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT',
        'Cache-Control': 'max-age=31536000',
        }

""" The `private/public` bucket name """
OSS_STORAGE_BUCKET_NAME = 'cogenda-qd'
"""The minimum part size(byte) (if there is more than one part). This value must be >= 5M """
OSS_FILE_BUFFER_SIZE=5*1024*1024

""" `private` for private file, `public-read` for public file """
OSS_DEFAULT_ACL='public-read'


########################################################
#                 USER SETTINGS                        #           
########################################################
COGENDA_STATIC_HOME=unicode(os.environ.get('COGENDA_STATIC_HOME', None),'utf-8')
SCAN_PATHS={
        COGENDA_STATIC_HOME: 'static',
        }
IGNORE_PATHS=[]
TRANSPORTERS=['oss', 's3']
