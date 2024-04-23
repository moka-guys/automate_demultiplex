#!/usr/bin/python3
# coding=utf-8
"""
Automate demultiplex logging. Classes required for logging
"""
import sys
import re
import logging
import logging.handlers
from config.ad_config import AdLoggerConfig


def shutdown_streamhandler(logger: logging.Logger) -> None:
    """
    Shut down the stream handler only for a logging object. For when
    we do not want to capture log messages in stdout
        :param logger (logging.Logger): Logger
        :return (None):
    """
    for handler in logger.handlers[:]:
        if handler.name == "stream_handler":
            logger.removeHandler(handler)
            handler.close()


def shutdown_logs(logger: logging.Logger) -> None:
    """
    To prevent duplicate filehandlers and system handlers close
    and remove all handlers for a logging object
        :param logger (logging.Logger): Logger
        :return (None):
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


class SensitiveFormatter(logging.Formatter):
    """
    Formatter that removes sensitive information in logs. Inherits
    the properties and methods from logging.Formatter

    Methods
        _filter(message)
            Filter out the auth key with regex
        format(record)
            Format the the record using logging.Formatter and _filter
    """

    @staticmethod
    def _filter(message: str) -> str:
        """
        Filter out the auth key with regex
            :param message (str):   Message to be filtered
            :return (str):          Filtered log message
        """
        return re.sub(r"--auth [^ ]+ ", r"--auth <MASKED_KEY> ", message)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the the record using _filter
            :param record (logging.LogRecord):  Object to be logged
            :return (str):                      Formatted filtered log message
        """
        original = logging.Formatter.format(self, record)  # Call parent method
        return self._filter(original)


class AdLogger(AdLoggerConfig):
    """
    Creates a python logging object with custom attributes and a
    file handler, syslog handler and stream handler

    Attributes
        logger_name (str):      Name of logger
        logger_type (str):      Type of logger, e.g. demultiplex, sw, etc.
        filepath (str):         Name of filepath to provide to _file_handler()
        formatter (object):     Sensitive formatter object

    Methods
        get_logger()
            Returns a Python logging object
        _get_file_handler()
            Get file handler for the logger
        _get_logging_formatter()
            Get formatter for logging. This is script mode-dependent
        _get_syslog_handler()
            Get syslog handler for the logger
        _get_stream_handler()
            Get stream handler for the logger (sends to stdout)
    """

    def __init__(self, logger_name: str, logger_type: str, filepath: str):
        """
        Constructor for the AdLogger class
            :param logger_name (str):   Name of logger
            :param logger_type (str):   Type of logger, e.g. demultiplex, sw, etc.
            :param filepath (str):      Name of filepath to provide to _file_handler()
        """
        self.logger_name = logger_name
        self.logger_type = logger_type
        self.filepath = filepath
        self.formatter = SensitiveFormatter(self._get_logging_formatter())

    def get_logger(self) -> logging.Logger:
        """
        Returns a Python logging object, and give it a name
            :return logger (object):    Python logging object with custom attributes
        """
        logger = logging.getLogger(self.logger_name)
        logger.filepath = self.filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler())
        logger.addHandler(self._get_stream_handler())
        logger.addHandler(self._get_syslog_handler())
        logger.timestamp = (
            AdLoggerConfig.TIMESTAMP
        )  # Timestamp in the format %Y%m%d_%H%M%S
        logger.log_msgs = (
            AdLoggerConfig.LOG_MSGS["general"] | AdLoggerConfig.LOG_MSGS["ad_email"]
        )
        if self.logger_type in AdLoggerConfig.LOG_MSGS.keys():
            logger.log_msgs.update(AdLoggerConfig.LOG_MSGS[self.logger_type])
        return logger

    def _get_file_handler(self) -> logging.FileHandler:
        """
        Get file handler for the logger, and give it a name
            :return file_handler (logging.FileHandler): FileHandler
        """
        file_handler = logging.FileHandler(self.filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        file_handler.name = "file_handler"
        return file_handler

    def _get_logging_formatter(self) -> str:
        """
        Get formatter for logging. This is script mode-dependent
            :return (str):  Logging formatter string
        """
        return (
            f"%(asctime)s - AUTOMATED SCRIPTS {AdLoggerConfig.SCRIPT_MODE} "
            "- %(name)s - %(levelname)s - %(message)s"
        )

    def _get_syslog_handler(self) -> logging.handlers.SysLogHandler:
        """
        Get syslog handler for the logger, and give it a name
            :return syslog_handler (logging.SysLogHandler): SysLogHandler
        """
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self.formatter)
        syslog_handler.name = "syslog_handler"
        return syslog_handler

    def _get_stream_handler(self) -> logging.StreamHandler:
        """
        Get stream handler for the logger (sends to stdout)
            :return stream_handler (logging.StreamHandler): StreamHandler
        """
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self.formatter)
        stream_handler.name = "stream_handler"
        return stream_handler


class RunfolderLoggers(object):
    """
    Creates an RunfolderLoggers object that contains various loggers required by the
    script that calls it. The loggers created are dictated by the logfiles_config dict
    provided as a parameter

    Attributes
        logfiles_config (dict): Dictionary of paths for each logfile
        loggers (dict):         Dict of loggers

    Methods
        get_loggers()
            Create loggers dict using AdLogger class and logfiles_config
    """

    def __init__(self, logfiles_config: dict):
        """
        Constructor for the RunfolderLoggers class
            :param logfiles_config (dict):  Dictionary containing the configuration
                                            for the required loggers
        """
        self.logfiles_config = logfiles_config
        self.loggers = self.get_loggers()  # Collect all loggers

    def get_loggers(self) -> dict:
        """
        Assign loggers using logfiles_config
            :return all_loggers (dict): Dict of logger types
        """
        loggers = {}
        for logger_type in self.logfiles_config.keys():
            logger_name = f"{logger_type} rf"
            ad_logger_obj = AdLogger(
                logger_name, logger_type, self.logfiles_config[logger_type]
            )
            loggers[logger_type] = ad_logger_obj.get_logger()
        return loggers
