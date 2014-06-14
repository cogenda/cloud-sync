# -*- coding:utf-8 -*-

import logging
import logging.handlers
import Queue
import os
import stat
import threading
import time
import sys
import sqlite3
from UserList import UserList
import os.path
import signal

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cloud_sync_settings'

from cloud_sync_settings import *
from persistent.persistent_queue import *
from fsmonitor.fsmonitor import *
from transporter.transporter import Transporter, ConnectionError
from daemon_thread_runner import *


# Define exceptions.
class CloudSyncError(Exception): pass
class CloudSyncInitError(CloudSyncError): pass
class ConfigError(CloudSyncInitError): pass
class TransporterAvailabilityTestError(CloudSyncInitError): pass
class ServerConnectionTestError(CloudSyncInitError): pass
class FSMonitorInitError(CloudSyncInitError): pass

class CloudSync(threading.Thread):

    DELETE_OLD_FILE = 0xFFFFFFFF

    def __init__(self, restart=False):
    	threading.Thread.__init__(self, name="CloudSyncThread")
    	self.lock = threading.Lock()
        self.die = False
	    self.transporters_running = 0
	    self.last_retry = 0

	    # Register cloud sync logger.
	    self.logger = logging.getLogger("CloudSync")
        self.logger.setLevel(FILE_LOGGER_LEVEL)
        fileHandler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5242880, backupCount=5)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(CONSOLE_LOGGER_LEVEL)
        formatter = logging.Formatter("%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s")
        fileHandler.setFormatter(formatter)
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)
        if restart:
            self.logger.warning("Cloud Sync has restarted itself!")
        self.logger.warning("Cloud Sync is initializing.")

        # register scan paths
        source_paths = SCAN_PATHS

        # Verify that all referenced transporters are available.
        transporters_not_found = 0
        for transporter in TRANSPORTERS:
            transporter_class = self._import_transporter(transporter)
            if not transporter_class:
                transporters_not_found += 1
        if transporters_not_found > 0:
            raise TransporterAvailabilityTestError("Consult the log file for details")

    def __setup(self):
        # Create transporter (cfr. worker thread) pools for each server.
        # Create one initial transporter per pool, possible other transporters
        # will be created on-demand.
        self.transporters = {} 
       
        # Collecting all necessary metadata for each rule.
        self.rules = [] 

    def run(self):        

        self.__setup()
        #TODO:
        
        


def run_cloud_sync(restart=False):
    try:
        cloud_sync = CloudSync(restart)
    except CloudSyncInitError, e:
        print e.__class__.__name__, e
    except CloudSyncError, e:
        print e.__class__.__name__, e
        del cloud_sync
    else:
        t = DaemonThreadRunner(cloud_sync, PID_FILE)
        t.start()
        del t
        del cloud_sync


if __name__ == '__main__':
    if not RESTART_AFTER_UNHANDLED_EXCEPTION:
        run_cloud_sync()
    else:
        run_cloud_sync()
        # Don't restart Cloud Sync, but actually quit it when it's stopped
        # by the user in the console. See DaemonThreadRunner.handle_signal()
        # for details.
        while True and not DaemonThreadRunner.stopped_in_console:
            # Make sure there's always a PID file, even when File Conveyor
            # technically isn't running.
            DaemonThreadRunner.write_pid_file(os.path.expanduser(PID_FILE))
            time.sleep(RESTART_INTERVAL)
            run_cloud_sync(restart=True)
