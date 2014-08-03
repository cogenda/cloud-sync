# -*- coding:utf-8 -*-

""" Cloud Sync App Main """

import threading
from .handler.transporter_handler import *
from .handler.logger_handler import *
from .handler.fsmonitor_handler import *
from .handler.db_handler import *
from .handler.retry_handler import *
import yaml

class CloudSync(threading.Thread):

    def __init__(self, restart=False):
        threading.Thread.__init__(self, name="CloudSyncThread")
        self.lock = threading.Lock()
        self.logger = LoggerHandler(settings)
        if restart:
            self.logger.warning("Cloud Sync has restarted itself!")
        self.logger.warning("Cloud Sync is initializing.")
        #TODO:
        #self.transporterHandler = TransporterHandler()

if __name__ == '__main__':

    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_storage_module'

    conf = open('/Users/tim-tang/Work/cloud-sync/cloud_sync_app/cloud_sync.yml')
    settings = yaml.load(conf)
    print settings
    print type(settings['AWS_HEADERS'])
    conf.close()

