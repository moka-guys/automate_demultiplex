#!/usr/bin/python3
# coding=utf-8
"""
Automate demultiplex logging. Classes required for logging
"""
import sys
import re
import logging
import logging.handlers
import ad_logger.log_config as logger_config
import inspect


class SensitiveFormatter(logging.Formatter):
    """
    Formatter that removes sensitive information in logs. Inherits the properties and
    methods from logging.Formatter

    Methods
        _filter()
            Filter out the auth key with regex
        format()
            Format the the record using _filter
    """

    @staticmethod
    def _filter(s: str) -> str:
        """
        Filter out the auth key with regex
        """
        return re.sub(r'--auth-token [^ ]+ ', r'--auth-token <MASKED_KEY> ', s)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the the record using _filter
        """
        original = logging.Formatter.format(self, record)  # Call parent method
        return self._filter(original)


class AdLoggers(object):
    """
    Creates an AdLoggers object that contains various loggers required by the script
    that calls it. The loggers created are dictated by the logfiles_config dict provided

    Attributes
        timestamp (str):            Timestamp in the format %Y%m%d_%H%M%S
        logfiles_config (dict):     Dictionary of paths for each logfile
        log_flags (dict):           Flags used in log messages
        loggers (list):             List of loggers
        msgs (dict):                Messages used in logging

    Methods
        get_loggers()
            Assign loggers using logfiles_config
        _get_logger()
            Returns a Python logging object
        _get_file_handler()
            Get file handler for the logger
        _get_syslog_handler()
            Get syslog handler for the logger
        _get_stream_handler()
            Get stream handler for the logger (sends to stdout)
        shutdown_logs()
            To prevent duplicate filehandlers and system handlers close and remove all
            handlers for the AdLoggers object
        shutdown_streamhandler()
            Shut down the stream handler only. For when we do not want to capture log
            messages in stdout
    """

    _sensitive_formatter = SensitiveFormatter(logger_config.LOGGING_FORMATTER)

    def __init__(self, logfiles_config: dict):
        """
        Constructor for the AdLoggers class
            :param logfiles_config (dict):  Dictionary containing the configuration for
                                            the required loggers
        """
        self.timestamp = logger_config.TIMESTAMP
        self.logfiles_config = logfiles_config
        self.log_flags = logger_config.LOG_FLAGS
        self.loggers = self.get_loggers()  # Collect all loggers
        self.msgs = logger_config.LOG_MSGS

    def get_loggers(self) -> list:
        """
        Assign loggers using logfiles_config
        """
        all_loggers = []
        for key in self.logfiles_config.keys():
            setattr(AdLoggers, key, self._get_logger(key, self.logfiles_config[key]))
            all_loggers.append(getattr(AdLoggers, key))
        return all_loggers

    def _get_logger(self, name: str, filepath: str) -> logging.Logger:
        """
        Returns a Python logging object
            :param name(str):       Logger name
            :param filepath(str):   Logfile path
        """
        logger = logging.getLogger(name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)

        file_handler = self._get_file_handler(filepath)
        file_handler.name = "file_handler"
        logger.addHandler(file_handler)
        stream_handler = self._get_stream_handler()
        stream_handler.name = "stream_handler"
        logger.addHandler(stream_handler)
        syslog_handler = self._get_syslog_handler()
        syslog_handler.name = "syslog_handler"
        logger.addHandler(syslog_handler)
        return logger

    def _get_file_handler(self, filepath: str) -> logging.FileHandler:
        """
        Get file handler for the logger
        """
        file_handler = logging.FileHandler(filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._sensitive_formatter)
        return file_handler

    def _get_syslog_handler(self) -> logging.handlers.SysLogHandler:
        """
        Get syslog handler for the logger
        """
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self._sensitive_formatter)
        return syslog_handler

    def _get_stream_handler(self) -> logging.StreamHandler:
        """
        Get stream handler for the logger (sends to stdout)
        """
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self._sensitive_formatter)
        return stream_handler

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove
        all handlers for the AdLoggers object
        """
        for logger in self.loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

    def shutdown_streamhandler(self):
        """
        Shut down the stream handler only. For when we do not want to capture log
        messages in stdout
        """
        for logger in self.loggers:
            for handler in logger.handlers[:]:
                if handler.name == "stream_handler":
                    logger.removeHandler(handler)
                    handler.close()
