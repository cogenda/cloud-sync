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
       
        # Collecting all necessary metadata for each rule.
        #TODO: rules
        self.rules = [] 
        
        # Initialize the the persistent 'pipeline' queue.
        self.pipeline_queue = PersistentQueue("pipeline_queue", PERSISTENT_DATA_DB)
        self.logger.warning("Setup: initialized 'pipeline' persistent queue, contains %d items." % (self.pipeline_queue.qsize()))

        self.transport_queue = {}
        or server in TRANSPORTERS:
            self.transport_queue[server] = AdvancedQueue()

        self.discover_queue  = Queue.Queue()
        self.db_queue = Queue.Queue()

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
        self.fsmonitor = fsmonitor_class(self.fsmonitor_callback, True, True, self.config.ignored_dirs.split(":"), "fsmonitor.db", "CloudSync")
        self.logger.warning("Setup: initialized FSMonitor.")


        # Monitor all sources' scan paths.
        for source in SCAN_PATHS: 
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
                #self.__process_files_to_delete()
                self.__process_retry_queue()
                self.__allow_retry()

                # Processing the queues 5 times per second is more than sufficient
                # because files are modified, processed and transported much
                # slower than that.
                time.sleep(0.2)
        except Exception, e:
            self.logger.exception("Unhandled exception of type '%s' detected, arguments: '%s'." % (e.__class__.__name__, e.args))
            self.logger.error("Stopping File Conveyor to ensure the application is stopped in a clean manner.")
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
        #TODO:

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
            item = self.pipeline_queue.get_item_for_key(key=input_file)
            # If the file does not yet exist in the pipeline queue, put() it.
            if item is None:
                self.pipeline_queue.put(item=(input_file, event), key=input_file)
            # Otherwise, merge the events, to prevent unnecessary actions.
            else:
                old_event = item[1]
                merged_event = FSMonitor.MERGE_EVENTS[old_event][event]
                if merged_event is not None:
                    self.pipeline_queue.update(item=(input_file, merged_event), key=input_file)
                    self.logger.info("Pipeline queue: merged events for '%s': %s + %s = %s." % (input_file, FSMonitor.EVENTNAMES[old_event], FSMonitor.EVENTNAMES[event], FSMonitor.EVENTNAMES[merged_event]))
                # The events being merged cancel each other out, thus remove
                # the file from the pipeline queue.
                else:
                    self.pipeline_queue.remove_item_for_key(key=input_file)
                    self.logger.info("Pipeline queue: merged events for '%s': %s + %s cancel each other out, thus removed this file." % (input_file, FSMonitor.EVENTNAMES[old_event], FSMonitor.EVENTNAMES[event]))
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
                #TODO: without rule.
                (input_file, event, rule, processed_for_server, output_file) = self.transport_queue[server].peek()
                self.lock.release()

                # Derive the action from the event.
                if event == FSMonitor.DELETED:
                    action = Transporter.DELETE
                elif event == FSMonitor.CREATED or event == FSMonitor.MODIFIED:
                    action = Transporter.ADD_MODIFY
                elif event == Arbitrator.DELETE_OLD_FILE:
                    # TRICKY: if the event is neither of DELETED, CREATED, nor
                    # MODIFIED, which everywhere else in the arbitrator it
                    # should be, then it must be the special case of a file
                    # that has been modified and already transported, but the
                    # old file must still be deleted. Hence we map this event
                    # to the Transporter's DELETE action.
                    action = Transporter.DELETE
                else:
                    raise Exception("Non-existing event set.") 

                # Make additional settings.
                dst_parent_path = ""

                (id, place_in_queue, transporter) = self.__get_transporter(server)
                if not transporter is None:
                    # A transporter is available!
                    # Transport queue -> Transporter -> transporter_callback -> db queue.
                    self.lock.acquire()
                    (input_file, event, rule, processed_for_server, output_file) = self.transport_queue[server].get()
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
                    relative_paths = SCAN_PATHS
                    dst = self.__calculate_transporter_dst(output_file, dst_parent_path, relative_paths)

                    # Start the transport.
                    transporter.sync_file(src, dst, action, curried_callback, curried_error_callback)

                    self.logger.info("Transport queue: '%s' to transfer to server '%s' with transporter #%d (of %d), place %d in the queue." % (output_file, server, id + 1, len(self.transporters[server]), place_in_queue))
                else:
                    self.logger.debug("Transporting: no more transporters are available for server '%s'." % (server))
                    break

                processed += 1

    
    def __process_db_queue(self):
        processed = 0 
        while processed < QUEUE_PROCESS_BATCH_SIZE and self.db_queue.qsize() > 0:
            # DB queue -> database.
            self.lock.acquire()
            (input_file, event, rule, processed_for_server, output_file, transported_file, url, server) = self.db_queue.get()
            self.lock.release()
            # Commit the result to the database.            
            remove_server_from_remaining_transporters = True
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
        max_connections = self.config.servers[server]["maxConnections"]
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


    def transporter_callback(self, src, dst, url, action, input_file, event, rule, processed_for_server, server):
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

    def __calculate_transporter_dst(self, src, parent_path=None, relative_paths=[]):
        dst = src

        # Strip off any relative paths.
        for relative_path in relative_paths:
            if dst.startswith(relative_path):
                dst = dst[len(relative_path):]

        # Ensure no absolute path is returned, which would make os.path.join()
        # fail.
        dst = dst.lstrip(os.sep)

        # Prepend any possible parent path.
        if not parent_path is None:
            dst = os.path.join(parent_path, dst)

        return dst
 

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
