# -*- coding:utf-8 -*-

""" Cloud Sync App Main """

import threading
from .handler.transporter_handler import *
from .handler.logger_handler import *
from .handler.fsmonitor_handler import *
from .handler.db_handler import *
from .handler.retry_handler import *
from .daemon_thread_runner import *
import yaml
import time

class CloudSync(threading.Thread):

    def __init__(self, settings, restart=False):
        threading.Thread.__init__(self, name="CloudSyncThread")
        self.lock = threading.Lock()
        self.settings = settings
        self.die = False
        self.logger = LoggerHandler(settings)
        if restart:
            self.logger.warning("Cloud Sync has restarted itself!")
        self.logger.warning("Cloud Sync is initializing.")
        self.transporterHandler = TransporterHandler(self.settings, self.logger, self.lock)
        self.dbHandler = DBHandler(self.settings, self.logger, self.lock)
        self.retryHandler = RetryHandler(self.settings, self.logger, self.lock)
        self.fsmonitorHandler = FSMonitorHandler(self.settings, self.logger, self.lock)
        
    def __setup(self): 
        db_queue = self.dbHandler.setup_db()
        transport_queue = self.transporterHandler.setup_transporters(db_queue)
        self.retryHandler.setup_retry(transport_queue) 
        db_queue = self.dbHandler.setup_db()
        self.fsmonitorHandler.set_fsmonitor(transport_queue)

    def run(self):
        self.__setup()
        self.fsmonitorHandler.bootstrap()
        try:
            while not self.die:
                self.fsmonitorHandler.process_discover_queue()
                self.transporterHandler.process_transport_queue()
                self.dbHandler.process_db_queue() 
                self.retryHandler.process_retry_queue()
                self.retryHandler.allow_retry()
                time.sleep(0.2)
        except: Exception, e:
            self.logger.exception("Unhandled exception of type '%s' detected, arguments: '%s'." % (e.__class__.__name__, e.args))
            self.logger.error("Stopping Cloud Sync to ensure the application is stopped in a clean manner.")
            os.kill(os.getpid(), signal.SIGTERM)
        self.logger.warning("Cloud Sync stopping...")

        # Stop the FSMonitor and wait for its thread to end.
        self.fsmonitorHandler.shutdown()

        # Stop the transporters and wait for their threads to end.
        self.transporterHandler.shutdown() 

        # Log information about the synced files DB.
        self.dbHandler.shutdown()

        # Final message, then remove all loggers.
        self.logger.shutdown()

    def stop(self):
        # Everybody dies only once.
        self.lock.acquire()
        if self.die:
            self.lock.release()
            return
        self.lock.release()

        # Die.
        self.logger.warning("Signaling to stop.")
        self.lock.acquire()
        self.die = True
        self.lock.release()

def run_cloud_sync(settings, restart=False)
    try:
        cloud_sync = CloudSync(restart)
    except CloudSyncInitError, e:
        print e.__class__.__name__, e
    except CloudSyncError, e:
        print e.__class__.__name__, e
        del cloud_sync
    else:
        t = DaemonThreadRunner(cloud_sync, settings['PID_FILE'])
        t.start()
        del t
        del cloud_sync

if __name__ == '__main__':

    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_storage_module'

    conf = open('/home/jitang/Work/cloud-sync/cloud_sync_app/cloud_sync.yml')
    settings = yaml.load(conf)
    print settings
    print type(settings['AWS_HEADERS'])
    conf.close()

    if not settings['RESTART_AFTER_UNHANDLED_EXCEPTION']:
        run_cloud_sync(settings)
    else:
        run_cloud_sync(settings)
        # Don't restart Cloud Sync, but actually quit it when it's stopped
        # by the user in the console. See DaemonThreadRunner.handle_signal()
        # for details.
        while True and not DaemonThreadRunner.stopped_in_console:
            # Make sure there's always a PID file, even when Cloud Sync 
            # technically isn't running.
            DaemonThreadRunner.write_pid_file(os.path.expanduser(settings['PID_FILE']))
            time.sleep(settings['RESTART_INTERVAL'])
            run_cloud_sync(restart=True)
