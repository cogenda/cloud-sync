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

from persistent.persistent_list import *
from persistent.persistent_queue import *
from fsmonitor.fsmonitor import *
from helper.sync_helper import SyncHelper
from transporter.transporter import Transporter, ConnectionError
from daemon_thread_runner import *


# Define exceptions.
class CloudSyncError(Exception): pass
class CloudSyncInitError(CloudSyncError): pass
class ConfigError(CloudSyncInitError): pass
class TransporterAvailabilityTestError(CloudSyncInitError): pass
class ServerConnectionTestError(CloudSyncInitError): pass
class FSMonitorInitError(CloudSyncInitError): pass

# Copied from django.utils.functional
def curry(_curried_func, *args, **kwargs):
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
    return _curried

class AdvancedQueue(UserList):
    """queue that supports peeking and jumping"""

    def peek(self):
        return self[0]

    def jump(self, item):
        self.insert(0, item)

    def put(self, item):
        self.append(item)

    def get(self):
        return self.pop(0)

    def qsize(self):
        return len(self)

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
        for server in TRANSPORTERS:
            self.transporters[server] = []
            self.logger.info("Setup: created transporter pool for the '%s' server." % (server))

        self.transport_queue = {}
        for server in TRANSPORTERS:
            self.transport_queue[server] = AdvancedQueue()

        self.failed_files = PersistentList("failed_files_list", PERSISTENT_DATA_DB)
        num_failed_files = len(self.failed_files)
        self.logger.warning("Setup: initialized 'failed_files' persistent list, contains %d items." % (num_failed_files))
        self.discover_queue  = Queue.Queue()
        self.db_queue = Queue.Queue()
        self.retry_queue = Queue.Queue()

        # Create connection to synced files DB.
        self.dbcon = sqlite3.connect(SYNCED_FILES_DB)
        self.dbcon.text_factory = unicode # This is the default, but we set it explicitly, just to be sure.
        self.dbcur = self.dbcon.cursor()
        self.dbcur.execute("CREATE TABLE IF NOT EXISTS synced_files(input_file text, transported_file_basename text, url text, server text)")
        self.dbcur.execute("CREATE UNIQUE INDEX IF NOT EXISTS file_unique_per_server ON synced_files (input_file, server)")
        self.dbcon.commit()
        self.dbcur.execute("SELECT COUNT(input_file) FROM synced_files")
        num_synced_files = self.dbcur.fetchone()[0]
        self.logger.warning("Setup: connected to the synced files DB. Contains metadata for %d previously synced files." % (num_synced_files))

        # Initialize the FSMonitor.
        fsmonitor_class = get_fsmonitor()
        self.fsmonitor = fsmonitor_class(self.fsmonitor_callback, True, True, IGNORE_PATHS, FSMONITOR_DB, "CloudSync")
        self.logger.warning("Setup: initialized FSMonitor.")


        # Monitor all sources' scan paths.
        for source in SCAN_PATHS.keys(): 
            self.logger.info("Setup: monitoring '%s'" % (source))
            self.fsmonitor.add_dir(source, FSMonitor.CREATED | FSMonitor.MODIFIED | FSMonitor.DELETED)


    def run(self):        

        self.__setup()

        self.fsmonitor.start()

        self.logger.warning("Fully up and running now.")

        try:
            while not self.die:
                self.__process_discover_queue()
                self.__process_transport_queues()
                self.__process_db_queue()
                self.__process_retry_queue()
                self.__allow_retry()

                # Processing the queues 5 times per second is more than sufficient
                # because files are modified, processed and transported much
                # slower than that.
                time.sleep(0.2)
        except Exception, e:
            self.logger.exception("Unhandled exception of type '%s' detected, arguments: '%s'." % (e.__class__.__name__, e.args))
            self.logger.error("Stopping Cloud Sync to ensure the application is stopped in a clean manner.")
            os.kill(os.getpid(), signal.SIGTERM)
        self.logger.warning("Cloud Sync stopping...") 

        # Stop the FSMonitor and wait for its thread to end.
        self.fsmonitor.stop()
        self.fsmonitor.join()
        self.logger.warning("Stopped FSMonitor.")

        # Sync the discover queue one more time: now that the FSMonitor has
        # been stopped, no more new discoveries will be made and we can safely
        # sync the last batch of discovered files.
        self.__process_discover_queue()
        self.logger.info("Final sync of discover queue to pipeline queue made.")

        # Stop the transporters and wait for their threads to end.
        # Stop the transporters and wait for their threads to end.
        for server in TRANSPORTERS:
            if len(self.transporters[server]):
                for transporter in self.transporters[server]:
                    transporter.stop()
                    transporter.join()
                self.logger.warning("Stopped transporters for the '%s' server." % (server))

        # Log information about the synced files DB.
        self.dbcur.execute("SELECT COUNT(input_file) FROM synced_files")
        num_synced_files = self.dbcur.fetchone()[0]
        self.logger.warning("synced files DB contains metadata for %d synced files." % (num_synced_files))


        # Final message, then remove all loggers.
        self.logger.warning("Cloud Sync has shut down.")
        while len(self.logger.handlers):
            self.logger.removeHandler(self.logger.handlers[0])
        logging.shutdown()


    def __process_discover_queue(self):

        self.lock.acquire()
        while self.discover_queue.qsize() > 0:
            # Discover queue -> pipeline queue.
            (input_file, event) = self.discover_queue.get()
            for server in TRANSPORTERS:
                self.transport_queue[server].put((input_file, event, server, input_file))
            self.logger.info("Discover queue -> pipeline queue: '%s'." % (input_file))
        self.lock.release()


    def __process_transport_queues(self):

        for server in TRANSPORTERS:
            processed = 0 

            while processed < QUEUE_PROCESS_BATCH_SIZE and self.transport_queue[server].qsize() > 0:
                # Peek at the first item from the queue. We cannot get the
                # item from the queue, because there may be no transporter
                # available, in which case the file should remain queued.
                self.lock.acquire()
                (input_file, event, processed_for_server, output_file) = self.transport_queue[server].peek()
                self.lock.release()

                # Derive the action from the event.
                if event == FSMonitor.DELETED:
                    action = Transporter.DELETE
                elif event == FSMonitor.CREATED or event == FSMonitor.MODIFIED:
                    action = Transporter.ADD_MODIFY
                elif event == CloudSync.DELETE_OLD_FILE:
                    # TRICKY: if the event is neither of DELETED, CREATED, nor
                    # MODIFIED, which everywhere else in the cloud sync it
                    # should be, then it must be the special case of a file
                    # that has been modified and already transported, but the
                    # old file must still be deleted. Hence we map this event
                    # to the Transporter's DELETE action.
                    action = Transporter.DELETE
                else:
                    raise Exception("Non-existing event set.") 


                (id, place_in_queue, transporter) = self.__get_transporter(server)
                if not transporter is None:
                    # A transporter is available!
                    # Transport queue -> Transporter -> transporter_callback -> db queue.
                    self.lock.acquire()
                    (input_file, event, processed_for_server, output_file) = self.transport_queue[server].get()
                    self.lock.release()

                    # Create curried callbacks so we can pass additional data
                    # to the transporter callback without passing it to the
                    # transporter itself (which cannot handle sending
                    # additional data to its callback functions).
                    curried_callback = curry(self.transporter_callback,
                            input_file=input_file,
                            event=event,
                            processed_for_server=processed_for_server,
                            server=server
                            )
                    curried_error_callback = curry(self.transporter_error_callback,
                            input_file=input_file,
                            event=event
                            )

                    src = output_file
                    relative_paths = SCAN_PATHS.keys()
                    dst = self.__calculate_transporter_dst(output_file, relative_paths)

                    # Start the transport.
                    transporter.sync_file(src, dst, action, curried_callback, curried_error_callback)

                    self.logger.info("Transport queue: '%s' to transfer to server '%s' with transporter #%d (of %d), place %d in the queue." % (output_file, server, id + 1, len(self.transporters[server]), place_in_queue))
                else:
                    self.logger.debug("Transporting: no more transporters are available for server '%s'." % (server))
                    break

                processed += 1


    def __process_retry_queue(self):
        processed = 0

        while processed < QUEUE_PROCESS_BATCH_SIZE and self.retry_queue.qsize() > 0:
            # Retry queue -> failed files list.
            # And remove from files in pipeline.
            self.lock.acquire()
            (input_file, event) = self.retry_queue.get()

            if (input_file, event) not in self.failed_files:
                self.failed_files.append((input_file, event))
                already_in_failed_files = False
            else:
                already_in_failed_files = True
            self.lock.release()

            # Log.
            if not already_in_failed_files:
                self.logger.warning("Retry queue -> 'failed_files' persistent list: '%s'. Retrying later." % (input_file))
            else:
                self.logger.warning("Retry queue -> 'failed_files' persistent list: '%s'. File already being retried later." % (input_file))
            processed += 1


    def __allow_retry(self):
        num_failed_files = len(self.failed_files)
        should_retry = self.last_retry + RETRY_INTERVAL < time.time()
        
        if num_failed_files > 0 and should_retry:
            failed_items = []

            processed = 0
            while processed < QUEUE_PROCESS_BATCH_SIZE and processed < len(self.failed_files):
                item = self.failed_files[processed]
                failed_items.append(item)
                for server in TRANSPORTERS:
                    self.transport_queue[server].put((item[0], item[1], server, item[0]))
                processed += 1
            
            for item in failed_items:
                self.failed_files.remove(item)

            self.last_retry = time.time()
            self.logger.warning("Moved %d items from the 'failed_files' persistent list into the 'pipeline' persistent queue." % (processed))


    def __process_db_queue(self):
        processed = 0 
        syncHelper = SyncHelper(
                cogenda_shared_secret=COGENDA_SHARED_SECRET,
                ws_host=WS_HOST,
                api_modify_resource=API_MODIFY_RESOURCE,
                api_destroy_resource=API_DESTROY_RESOURCE)

        while processed < QUEUE_PROCESS_BATCH_SIZE and self.db_queue.qsize() > 0:
            # DB queue -> database.
            self.lock.acquire()
            (input_file, event, processed_for_server, output_file, transported_file, url, server) = self.db_queue.get()
            self.lock.release()
            # Commit the result to the database.            
            transported_file_basename = os.path.basename(output_file)
            if event == FSMonitor.CREATED:
                try:
                    self.dbcur.execute("INSERT INTO synced_files VALUES(?, ?, ?, ?)", (input_file, transported_file_basename, url, server))
                    self.dbcon.commit()
                except sqlite3.IntegrityError, e:
                    self.logger.critical("Database integrity error: %s. Duplicate key: input_file = '%s', server = '%s'." % (e, input_file, server))

            elif event == FSMonitor.MODIFIED:
                self.dbcur.execute("SELECT COUNT(*) FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                if self.dbcur.fetchone()[0] > 0:
                    # Look up the transported file's base name. This
                    # might be different from the input file's base
                    # name due to processing.
                    self.dbcur.execute("SELECT transported_file_basename FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                    old_transport_file_basename = self.dbcur.fetchone()[0]
                    # Update the transported_file_basename and url fields for
                    # the input_file that has been transported.
                    self.dbcur.execute("UPDATE synced_files SET transported_file_basename=?, url=? WHERE input_file=? AND server=?", (transported_file_basename, url, input_file, server))
                    self.dbcon.commit()
                else:
                    self.dbcur.execute("INSERT INTO synced_files VALUES(?, ?, ?, ?)", (input_file, transported_file_basename, url, server))
                    self.dbcon.commit()
            elif event == FSMonitor.DELETED:
                self.dbcur.execute("DELETE FROM synced_files WHERE input_file=? AND server=?", (input_file, server))
                self.dbcon.commit()
            else:
                raise Exception("Non-existing event set.")
            self.logger.debug("DB queue -> 'synced files' DB: '%s' (URL: '%s')." % (input_file, url))

            self.__sync_congenda(syncHelper, event, transported_file_basename, transported_file, url, server)
        processed += 1


    def __sync_congenda(self, syncHelper, event, transported_file_basename, transported_file, url, server):
        # Sync with cogenda web server
        if OSS_DEFAULT_ACL != 'private' or AWS_DEFAULT_ACL != 'private':
            return
        if event == FSMonitor.CREATED or event == FSMonitor.MODIFIED:
            resource_type = self.__filter_resource_type(transported_file)
            result = syncHelper.sync_resource(transported_file_basename, url, server, '', resource_type)
            if not result:
                self.logger.critical('Failed to sync with cogenda server filename: [%s]  vendor: [%s]' %(transported_file_basename, server))
        elif event == FSMonitor.DELETED:
            result = syncHelper.destroy_resource(transported_file_basename, server)
            if not result:
                self.logger.critical('Failed to destory resource with cogenda server filename: [%s] vendor: [%s]' %(transported_file_basename, server))
        else:
            raise Exception("Non-existing event set.")
        self.logger.debug("Sync cogenda -> 'synced file with cogenda web server' file: '%s' (URL: '%s')." % (transported_file, url))


    def __filter_resource_type(self, transported_file):
        if 'public/publication' in transported_file:
            return 1
        elif 'public/documentation' in transported_file: 
            return 2
        elif 'public/examples' in transported_file:
            return 3
        elif 'alluser/installer' in transported_file: 
            return 4
        elif 'alluser/software-pkg' in transported_file:
            return 5
        elif 'private/' in transported_file:
            return 6
        else:
            raise Exception("Invalide downloads dir structure.")



    def __get_transporter(self, server):
        """get a transporter; if one is ready for new work, use that one,
        otherwise try to start a new transporter"""

        # Try to find a running transporter that is ready for new work.
        for id in range(0, len(self.transporters[server])):
            transporter = self.transporters[server][id]
            # Don't put more than MAX_TRANSPORTER_QUEUE_SIZE files in each
            # transporter's queue.
            if transporter.qsize() <= MAX_TRANSPORTER_QUEUE_SIZE:
                place_in_queue = transporter.qsize() + 1
                return (id, place_in_queue, transporter)

        # Don't run more than the allowed number of simultaneous transporters.
        if not self.transporters_running < MAX_SIMULTANEOUS_TRANSPORTERS:
            return (None, None, None)

        # Don't run more transporters for each server than its "maxConnections"
        # setting allows.
        num_connections = len(self.transporters[server])
        max_connections = MAX_TRANSPORTER_POOL_SIZE
        if max_connections == 0 or num_connections < max_connections:
            transporter    = self.__create_transporter(server)
            id             = len(self.transporters[server]) - 1
            # If a transporter was succesfully created, add it to the pool.
            if transporter:
                self.transporters[server].append(transporter)
                transporter.start()
                self.transporters_running += 1
                # Since this transporter was just created, it's obvious that we're
                # first in line.
                place_in_queue = 1
                return (id, 1, transporter)
        return (None, None, None)

    def __create_transporter(self, server):
        """create a transporter for the given server"""

        transporter_name = server
        transporter_class = self._import_transporter(transporter_name)

        # Attempt to create an instance of the transporter.
        try:
            transporter = transporter_class(self.transporter_callback, self.transporter_error_callback, "CloudSync")
        except ConnectionError, e:
            self.logger.error("Could not start transporter '%s'. Error: '%s'." % (transporter_name, e))
            return False
        else:
            self.logger.warning("Created '%s' transporter for the '%s' server." % (transporter_name, server))

        return transporter

    def _import_transporter(self, transporter):
        """Imports transporter module and class, returns class.

        Input value can be:

        * a full/absolute module path, like
          "MyTransporterPackage.SomeTransporterClass"
        """
        transporter_class = None
        module = None
        alternatives = [transporter]
        default_prefix = 'transporter.transporter_'
        if not transporter.startswith(default_prefix):
            alternatives.append('%s%s' % (default_prefix, transporter))
        for module_name in alternatives:
            try:
                module = __import__(module_name, globals(), locals(), ["TRANSPORTER_CLASS"], -1)
            except ImportError:
                pass

        if not module:
            msg = "The transporter module '%s' could not be found." % transporter
            if len(alternatives) > 1:
                msg = '%s Tried (%s)' % (msg, ', '.join(alternatives))
            self.logger.error(msg)
        else:
            try:
                classname = module.TRANSPORTER_CLASS
                module = __import__(module_name, globals(), locals(), [classname])
                transporter_class = getattr(module, classname)
            except AttributeError:
                self.logger.error("The Transporter module '%s' was found, but its Transporter class '%s' could not be found."  % (module_name, classname))
        return transporter_class


    def fsmonitor_callback(self, monitored_path, event_path, event, discovered_through):
        # Map FSMonitor's variable names to ours.
        input_file = event_path

        if CALLBACKS_CONSOLE_OUTPUT:
            print """FSMONITOR CALLBACK FIRED:
                    input_file='%s'
                    event=%d"
                    discovered_through=%s""" % (input_file, event, discovered_through)

        # The file may have already been deleted!
        deleted = event == FSMonitor.DELETED
        touched = event == FSMonitor.CREATED or event == FSMonitor.MODIFIED
        if deleted or (touched and os.path.exists(event_path)):
            # Ignore directories (we cannot test deleted files to see if they
            # are directories, because they obviously don't exist anymore).
            if touched:
                try:
                    if stat.S_ISDIR(os.stat(event_path)[stat.ST_MODE]):
                        return
                except OSError, e:
                    # The file (or directory, we can't be sure at this point)
                    # does no longer exist (despite the os.path.exists() check
                    # above!): it must *just* have been deleted.
                    if e.errno == os.errno.ENOENT:
                        return

            # Map FSMonitor's variable names to ours.
            input_file = event_path

            # Add to discover queue.
            self.lock.acquire()
            self.discover_queue.put((input_file, event))
            self.lock.release()


    def transporter_callback(self, src, dst, url, action, input_file, event, processed_for_server, server):
        # Map Transporter's variable names to ours.
        output_file      = src
        transported_file = dst

        if CALLBACKS_CONSOLE_OUTPUT:
            print """TRANSPORTER CALLBACK FIRED:
                    (curried): input_file='%s'
                    (curried): event=%d
                    (curried): processed_for_server='%s'
                    output_file='%s'
                    transported_file='%s'
                    url='%s'
                    server='%s'""" % (input_file, event, processed_for_server, output_file, transported_file, url, server)

        # Add to db queue.
        self.lock.acquire()
        self.db_queue.put((input_file, event, processed_for_server, output_file, transported_file, url, server))
        self.lock.release()
        self.logger.info("Transport queue -> DB queue: '%s' (server: '%s')." % (input_file, server))


    def transporter_error_callback(self, src, dst, action, input_file, event):
        if CALLBACKS_CONSOLE_OUTPUT:
            print """TRANSPORTER ERROR CALLBACK FIRED:
                    (curried): input_file='%s'
                    (curried): event=%d""" % (input_file, event)

        self.retry_queue.put((input_file, event))


    def __calculate_transporter_dst(self, src, relative_paths=[]):
        dst = src
        parent_path=None

        # Strip off any relative paths.
        for relative_path in relative_paths:
            if dst.startswith(relative_path):
                parent_path = SCAN_PATHS[relative_path]
                dst = dst[len(relative_path):]

        # Ensure no absolute path is returned, which would make os.path.join()
        # fail.
        dst = dst.lstrip(os.sep)

        # Prepend any possible parent path.
        if not parent_path is None:
            dst = os.path.join(parent_path, dst)

        return dst


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
    if len(sys.argv) == 2:
        setting = None
        if sys.argv[1] == 'pub':
            from sync_pub_settings import *
            setting = 'sync_pub_settings'
        else:
            from sync_pvt_settings import *
            setting = 'sync_pvt_settings'

        if not 'DJANGO_SETTINGS_MODULE' in os.environ:
            os.environ['DJANGO_SETTINGS_MODULE'] = setting
    else:
        sys.exist(2)

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
