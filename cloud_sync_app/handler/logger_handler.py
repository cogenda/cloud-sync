# -*- coding:utf-8 -*-

import os
import sys
import logging
import logging.handlers

class LoggerHandler(object):

    def __init__(self, settings):
        self.logger = logging.getLogger("CloudSync")
        self.logger.setLevel(settings.FILE_LOGGER_LEVEL)
        fileHandler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5242880, backupCount=5)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(settings.CONSOLE_LOGGER_LEVEL)
        formatter = logging.Formatter("%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s")
        fileHandler.setFormatter(formatter)
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

    def shutdown(self):
        while len(self.logger.handlers):
            self.logger.removeHandler(self.logger.handlers[0])
        logging.shutdown()
