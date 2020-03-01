#!/usr/bin/python3

import logging
import logging.handlers

class PyuvalLogging(object):
    def __init__(self, ModuleName="pyuval"):
        logger = logging.getLogger(ModuleName)
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.handlers.SysLogHandler(address='/dev/log')
        fh.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        self.logger = logger

    def audit(self, message):
        self.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def critical(self, message):
        self.logger.critical(message)

    def error(self, message):
        self.logger.error(message)
        
    def fatal(self, custom_message, ex):
        template = "{0}{1}\n{2!r}"
        message = template.format(custom_message, type(ex).__name__, ex.args)
        self.logger.fatal(message)

    def exception(self, custom_message, ex):
        template = "{0}{1}\n{2!r}"
        message = template.format(custom_message, type(ex).__name__, ex.args)
        self.logger.fatal(message)