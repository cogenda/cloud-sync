# -*- coding:utf-8 -*-

from ..fsmonitor.fsmonitor import *
from ..helper.sync_helper import SyncHelper

class WSHandler(object):

    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.syncHelper = SyncHelper(
            ws_shared_secret= os.environ.get('WS_SHARED_SECRET', 'cogenda-ws-secret'),
            ws_host=self.settings['WS_HOST'],
            api_modify_resource=self.settings['API_MODIFY_RESOURCE'],
            api_destroy_resource=self.settings['API_DESTROY_RESOURCE'])

    def sync_ws(self, event, transported_file_basename, transported_file, url, server):
        """ Sync with external web service """
        if not self.settings['SYNC_WS']: 
            return
        if event == FSMonitor.CREATED or event == FSMonitor.MODIFIED:
            result = self.syncHelper.sync_resource(transported_file_basename, url, server, transported_file)
            if not result:
                self.logger.critical('Failed to sync with web service filename: [%s]  vendor: [%s]' %(transported_file_basename, server))
            else:
                self.logger.info('Success to sync with web service filename: [%s]  vendor: [%s]' %(transported_file_basename, server))
        elif event == FSMonitor.DELETED:
            result = self.syncHelper.destroy_resource(transported_file_basename, server)
            if not result:
                self.logger.critical('Failed to destory resource with web service filename: [%s] vendor: [%s]' %(transported_file_basename, server))
            else:
                self.logger.info('Success to destroy resource with web service filename: [%s]  vendor: [%s]' %(transported_file_basename, server))
        else:
            raise Exception("Non-existing event set.")
        self.logger.debug("Sync web service -> 'synced file with web service' file: '%s' (URL: '%s')." % (transported_file, url))
