# -*- coding:utf-8 -*-
import os
import logging

# Dummy settings for `django-storages`.
SECRET_KEY='cogenda-cloud-sync'
MEDIA_URL=''
MEDIA_ROOT=''

########################################################
#               AWS S3 CONFIGURATION                   #           
########################################################
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
AWS_STORAGE_BUCKET_NAME = 'cogenda'
AWS_QUERYSTRING_AUTH = False
AWS_HEADERS = {
        'Expires': 'Tue, 20 Jan 2037 03:00:00 GMT', 
        'Cache-Control': 'max-age=86400',
        'Vary':'Accept-Encoding',
}

# settings for cloud sync
RESTART_AFTER_UNHANDLED_EXCEPTION = False
RESTART_INTERVAL = 10
LOG_FILE = './cloud_sync.log'
PID_FILE = '~/.cloud_sync.pid'
PERSISTENT_DATA_DB = './persistent_data.db'
SYNCED_FILES_DB = './synced_files.db'
CONSOLE_LOGGER_LEVEL = logging.INFO
FILE_LOGGER_LEVEL = logging.INFO
MAX_SIMULTANEOUS_TRANSPORTERS = 10
MAX_TRANSPORTER_QUEUE_SIZE = 1
QUEUE_PROCESS_BATCH_SIZE = 20
CALLBACKS_CONSOLE_OUTPUT = True

SCAN_PATHS=[unicode('/Users/tim-tang/Work/test','utf-8')]
IGNORE_PATHS=[]
TRANSPORTERS=['s3']
