# -*- coding:utf-8 -*-

import os, sys
import threading
import stat
from ..fsmonitor.fsmonitor import *


class FSMonitorHandler(object):

    def __init__(self, settings, logger, transport_queue, lock):
        self.lock = lock
        self.settings = settings
        self.logger = logger
        self.transport_queue = transport_queue

    def setup_fsmonitor(self):
        self.discover_queue  = Queue.Queue()
        # Initialize the FSMonitor.
        fsmonitor_class = get_fsmonitor()
        self.fsmonitor = fsmonitor_class(self._fsmonitor_callback, True, True, self.settings.IGNORE_PATHS, self.settings.FSMONITOR_DB, "CloudSync")

        # Monitor all sources' scan paths.
        for source in self.settings.SCAN_PATHS.keys(): 
            self.logger.info("Setup: monitoring '%s'" % (source))
            self.fsmonitor.add_dir(source, FSMonitor.CREATED | FSMonitor.MODIFIED | FSMonitor.DELETED)

    def bootstrap(self):
        self.fsmonitor.start()
        self.logger.warning("Fully up and running now.")
        
    def shutdown(self):
        # Stop the FSMonitor and wait for its thread to end.
        self.fsmonitor.stop()
        self.fsmonitor.join()
        # Sync the discover queue one more time: now that the FSMonitor has
        # been stopped, no more new discoveries will be made and we can safely
        # sync the last batch of discovered files.
        self.__process_discover_queue()
        self.logger.info("Final sync of discover queue to pipeline queue made.")
        self.logger.warning("Stopped FSMonitor.")

    def process_discover_queue(self):
        self.lock.acquire()
        while self.discover_queue.qsize() > 0:
            # Discover queue -> pipeline queue.
            (input_file, event) = self.discover_queue.get()
            for server in self.settings.TRANSPORTERS:
                self.transport_queue[server].put((input_file, event, server, input_file))
            self.logger.info("Discover queue -> pipeline queue: '%s'." % (input_file))
        self.lock.release()

    def _fsmonitor_callback(self, monitored_path, event_path, event, discovered_through):
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
