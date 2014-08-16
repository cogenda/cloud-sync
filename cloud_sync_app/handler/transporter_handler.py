# -*- coding:utf-8 -*-

import os
import sys
from ..utils.advanced_queue import AdvancedQueue
from ..fsmonitor.fsmonitor import *
from ..transporter.transporter import Transporter, ConnectionError

class TransporterAvailabilityTestError(Exception): pass

# Copied from django.utils.functional
def curry(_curried_func, *args, **kwargs):
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
    return _curried

class TransporterHandler(object):

    DELETE_OLD_FILE = 0xFFFFFFFF

    def __init__(self, settings, logger, lock):
        self.logger = logger
        self.settings = settings
        self.lock = lock
        self.transporters_running = 0
        # Verify that all referenced transporters are available.
        transporters_not_found = 0
        for transporter in settings['TRANSPORTERS']:
            transporter_class = self._import_transporter(transporter)
            if not transporter_class:
                transporters_not_found += 1
        if transporters_not_found > 0:
            raise TransporterAvailabilityTestError("Transport not found, consult the log file for details")

    def setup_transporters(self):
        self.transporters = {}
        for server in self.settings['TRANSPORTERS']:
            self.transporters[server] = []
            self.logger.info("Setup: created transporter pool for the '%s' server." % (server))
        self.transport_queue = {}
        for server in self.settings['TRANSPORTERS']:
            self.transport_queue[server] = AdvancedQueue()
        self.error_transported_count = 0
        return self.transport_queue  

    def peek_error_transported_count(self):
        return self.error_transported_count

    def shutdown(self):
        # Stop the transporters and wait for their threads to end.
        for server in self.settings['TRANSPORTERS']:
            if len(self.transporters[server]):
                for transporter in self.transporters[server]:
                    transporter.stop()
                    transporter.join()
                self.logger.warning("Stopped transporters for the '%s' server." % (server))


    def process_transport_queue(self, db_queue, retry_queue=None):
        self.db_queue = db_queue
        self.retry_queue = retry_queue
        for server in self.settings['TRANSPORTERS']:
            processed = 0 
            while processed < self.settings['QUEUE_PROCESS_BATCH_SIZE'] and self.transport_queue[server].qsize() > 0:
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

                (id, place_in_queue, transporter) = self._get_transporter(server)
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
                    curried_callback = curry(self._transporter_callback,
                            input_file=input_file,
                            event=event,
                            processed_for_server=processed_for_server,
                            server=server
                            )
                    curried_error_callback = curry(self._transporter_error_callback,
                            input_file=input_file,
                            event=event
                            )

                    src = output_file
                    relative_paths = self.settings['SCAN_PATHS'].keys()
                    dst = self._calculate_transporter_dst(output_file, relative_paths)

                    # Start the transport.
                    transporter.sync_file(src, dst, action, curried_callback, curried_error_callback)

                    self.logger.info("Transport queue: '%s' to transfer to server '%s' with transporter #%d (of %d), place %d in the queue." % (output_file, server, id + 1, len(self.transporters[server]), place_in_queue))
                else:
                    self.logger.debug("Transporting: no more transporters are available for server '%s'." % (server))
                    break

                processed += 1


    def _get_transporter(self, server):
        """get a transporter; if one is ready for new work, use that one,
        otherwise try to start a new transporter"""

        # Try to find a running transporter that is ready for new work.
        for id in range(0, len(self.transporters[server])):
            transporter = self.transporters[server][id]
            # Don't put more than MAX_TRANSPORTER_QUEUE_SIZE files in each
            # transporter's queue.
            if transporter.qsize() <= self.settings['MAX_TRANSPORTER_QUEUE_SIZE']:
                place_in_queue = transporter.qsize() + 1
                return (id, place_in_queue, transporter)

        # Don't run more than the allowed number of simultaneous transporters.
        if not self.transporters_running < self.settings['MAX_SIMULTANEOUS_TRANSPORTERS']:
            return (None, None, None)

        # Don't run more transporters for each server than its "maxConnections"
        # setting allows.
        num_connections = len(self.transporters[server])
        max_connections = self.settings['MAX_TRANSPORTER_POOL_SIZE']
        if max_connections == 0 or num_connections < max_connections:
            transporter    = self._make_transporter(server)
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

    def _make_transporter(self, server):
        """create a transporter for the given server"""
        transporter_name = server
        transporter_class = self._import_transporter(transporter_name)

        # Attempt to create an instance of the transporter.
        try:
            transporter = transporter_class(self.settings, self._transporter_callback, self._transporter_error_callback, "CloudSync")
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
        alternatives = []
        default_prefix = 'cloud_sync_app.transporter.transporter_'
        if not transporter.startswith(default_prefix):
            alternatives.append('%s%s' % (default_prefix, transporter))
        for module_name in alternatives:
            try:
                module = __import__(module_name, globals(), locals(), ["TRANSPORTER_CLASS"], -1)
            except ImportError:
                import traceback
                traceback.print_exc()
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

    def _transporter_callback(self, src, dst, url, action, input_file, event, processed_for_server, server):
        # Map Transporter's variable names to ours.
        output_file      = src
        transported_file = dst

        if self.settings['CALLBACKS_CONSOLE_OUTPUT']:
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


    def _transporter_error_callback(self, src, dst, action, input_file, event):
        if self.settings['CALLBACKS_CONSOLE_OUTPUT']:
            print """TRANSPORTER ERROR CALLBACK FIRED:
                    (curried): input_file='%s'
                    (curried): event=%d""" % (input_file, event)

        if self.retry_queue:
            self.retry_queue.put((input_file, event))
            self.lock.acquire()
            self.error_transported_count += 1
            self.lock.release()
        
    def _calculate_transporter_dst(self, src, relative_paths=[]):
        dst = src
        parent_path=None

        # Strip off any relative paths.
        for relative_path in relative_paths:
            if dst.startswith(relative_path):
                parent_path = self.settings['SCAN_PATHS'][relative_path]
                dst = dst[len(relative_path):]

        # Ensure no absolute path is returned, which would make os.path.join()
        # fail.
        dst = dst.lstrip(os.sep)

        # Prepend any possible parent path.
        if not parent_path is None:
            dst = os.path.join(parent_path, dst)

        return dst

