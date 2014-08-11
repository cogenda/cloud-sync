# -*- coding:utf-8 -*-

""" Cloud Sync App Main """

import threading
from .handler.transporter_handler import *
from .handler.logger_handler import *
from .handler.fsmonitor_handler import *
from .handler.db_handler import *
from .handler.retry_handler import *
from .daemon_thread_runner import *
from .handler.ws_handler import *
import yaml
import time

# Define exceptions.
class CloudSyncError(Exception): pass
class CloudSyncInitError(CloudSyncError): pass

class CloudSync(threading.Thread):

    def __init__(self, settings, restart=False):
        threading.Thread.__init__(self, name="CloudSyncThread")
        self.lock = threading.Lock()
        self.die = False
        self.loggerHandler = LoggerHandler()
        self.logger = self.loggerHandler.init_logger(settings)
        if restart:
            self.logger.warning("Cloud Sync has restarted itself!")
        self.logger.warning("Cloud Sync is initializing.")
        self.transporterHandler = TransporterHandler(settings, self.logger, self.lock)
        self.dbHandler = DBHandler(settings, self.logger, self.lock)
        if settings['RUN_AS_SERVICE']: 
            self.retryHandler = RetryHandler(settings, self.logger, self.lock)
        else:
            self.wsHandler = WSHandler(settings, self.logger)
        self.fsmonitorHandler = FSMonitorHandler(settings, self.logger, self.lock)
        self.settings = settings

    def __setup(self): 
        self.transport_queue = self.transporterHandler.setup_transporters()
        self.db_queue = self.dbHandler.setup_db()
        if self.settings['RUN_AS_SERVICE']:
            self.retry_queue = self.retryHandler.setup_retry()
        self.fsmonitorHandler.setup_fsmonitor()

    def run(self):
        self.__setup()
        self.fsmonitorHandler.bootstrap()
        try:
            while not self.die:
                self.fsmonitorHandler.process_discover_queue(self.transport_queue)
                if self.settings['RUN_AS_SERVICE']: 
                    self.transporterHandler.process_transport_queue(self.db_queue, self.retry_queue)
                    self.dbHandler.process_db_queue()
                    self.retryHandler.process_retry_queue()
                    self.retryHandler.allow_retry(self.transport_queue)
                else:
                    time.sleep(2)
                    self.transporterHandler.process_transport_queue(self.db_queue)
                    self.dbHandler.process_db_queue()
                    if self.fsmonitorHandler.peek_monitored_count()*len(self.settings['TRANSPORTERS']) == self.dbHandler.peek_transported_count():
                        self.wsHandler.notify_ws()
                        break;
                time.sleep(0.2)
        except Exception, e:
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
        self.loggerHandler.shutdown()

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

def run_cloud_sync(settings, restart=False):
    try:
        cloud_sync = CloudSync(settings, restart)
    except CloudSyncInitError, e:
        print e.__class__.__name__, e
    except CloudSyncError, e:
        print e.__class__.__name__, e
        del cloud_sync
    else:
        if settings['RUN_AS_SERVICE']: 
            t = DaemonThreadRunner(cloud_sync, settings['PID_FILE'])
            t.start()
            del t
        else:
            try:
                cloud_sync.setDaemon(True)
                cloud_sync.start()
                while cloud_sync.isAlive():
                    cloud_sync.join(1)
            except KeyboardInterrupt, SystemExit:
                print '\n! Received keyboard interrupt, quitting cloud sync threads.\n'
                sys.exit()
        del cloud_sync

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exist(2)
    if not os.path.exists(sys.argv[1]):
        print 'Cloud Sync configuration file [%s] not exists.' % sys.argv[1]
        sys.exist(2)

    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'cloud_sync_app.django_storage_module'

    conf = open(sys.argv[1])
    settings = yaml.load(conf)
    conf.close()

    from django.conf import settings as django_settings
    setattr(django_settings, 'OSS_ACCESS_URL', settings['OSS_ACCESS_URL'])

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
