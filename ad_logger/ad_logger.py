#!/usr/bin/python3
# coding=utf-8
"""
Automate demultiplex logging. Classes required for logging
"""
import os
import sys
import re
import logging
import logging.handlers
import config.ad_config as ad_config
import ad_logger.log_config as logger_config


def get_log_flags():
    """
    Return flags used in log messages. These are script mode-dependent
        :return (dict):     Dictionary of logging flags to add to log messages
    """
    if ad_config.TESTING:
        test_str = "test"
    else:
        test_str = ""
    return {
        "info": f"%s{test_str}_info",
        "fail": f"%s{test_str}_fail",
        "ss_warning": f"%s{test_str}_warning",
    }


def return_scriptlogger(logname, identifier):
    """"""
    # Script-level logfile configuration
    SCRIPTLOG_CONFIG = {
        "demultiplex": os.path.join(  # Record demultiplex script logs
            ad_config.AD_LOGDIR, "demultiplexing_script_logfiles",
            f"{identifier}_demultiplex_script_log.log"
            ),
        # Records output of upload and setoff workflow script
        "usw": os.path.join(
            ad_config.AD_LOGDIR, "usw_script_logfiles", 
            f"{identifier}_upload_and_setoff_workflow.log"
            ),
        # Records the logs from the backup runfolder script
        "backup": os.path.join(
            ad_config.AD_LOGDIR, "backup_runfolder_script_logfiles",
            f"{identifier}_backup_runfolder.log"
            ),
    }
    return AdLogger(logname, SCRIPTLOG_CONFIG[logname]).logger


# NOT WORKING
def shutdown_streamhandler(logger) -> None:
    """
    Shut down the stream handler only for a logging object. For when we do not want to
    capture log messages in stdout
        :return (None):
    """
    for handler in logger.handlers[:]:
        if handler.name == "stream_handler":
            logger.removeHandler(handler)
            handler.close()


# NOT WORKING
def shutdown_logs(logger) -> None:
    """
    To prevent duplicate filehandlers and system handlers close and remove
    all handlers for a logging object
        :return (None):
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


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
            :return (str):  Filtered log message
        """
        return re.sub(r'--auth-token [^ ]+ ', r'--auth-token <MASKED_KEY> ', s)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the the record using _filter
            :return (str):  Formatted filtered log message
        """
        original = logging.Formatter.format(self, record)  # Call parent method
        return self._filter(original)


class RunfolderLoggers(object):
    """
    Creates an RunfolderLoggers object that contains various loggers required by th
    script that calls it. The loggers created are dictated by the logfiles_config dict
    provided

    Attributes
        logfiles_config (dict): Dictionary of paths for each logfile
        loggers (list):         List of loggers
        logger (object):        Logger object created by AdLogger class, with custom
                                attributes. Various exist each with their own name as
                                per logfiles_config

    Methods
        get_loggers()
            Assign loggers using AdLogger class and logfiles_config
    """

    def __init__(self, logfiles_config: dict):
        """
        Constructor for the RunfolderLoggers class
            :param logfiles_config (dict):  Dictionary containing the configuration for
                                            the required loggers
        """
        self.logfiles_config = logfiles_config
        self.loggers = self.get_loggers()  # Collect all loggers

    def get_loggers(self) -> list:
        """
        Assign loggers using logfiles_config
            :return all_loggers (list): List of loggers
        """
        all_loggers = []
        for key in self.logfiles_config.keys():
            setattr(
                RunfolderLoggers, key, AdLogger(key, self.logfiles_config[key]).logger
            )
            all_loggers.append(getattr(RunfolderLoggers, key))
        return all_loggers


class AdLogger(object):
    """
    Creates a python logging object with custom attributes and a file handler, syslog
    handler and stream handler

    Attributes
        logger (object):    Python logging object with custom attributes

    Methods
        _get_logger()
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

    def __init__(self, logger_name, filepath):
        """
        Constructor for the AdLogger class
            :param logger_name (str):   Name of logger
            :param filepath (str):      Name of filepath to provide to _file_handler()
        """
        self.logger = self._get_logger(logger_name, filepath)

    def _get_logger(self, logger_name, filepath) -> logging.Logger:
        """
        Returns a Python logging object, and give it a name
            :param name(str):           Logger name
            :param filepath(str):       Logfile path
            :return logger (object):    Logger
        """
        logger = logging.getLogger(logger_name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(filepath))
        logger.addHandler(self._get_stream_handler())
        logger.addHandler(self._get_syslog_handler())
        logger.timestamp = ad_config.TIMESTAMP  # Timestamp in the format %Y%m%d_%H%M%S
        logger.log_flags = get_log_flags()
        logger.log_msgs = (
            logger_config.LOG_MSGS['general'] | logger_config.LOG_MSGS[logger_name]
            )
        return logger

    def _get_file_handler(self, filepath: str) -> logging.FileHandler:
        """
        Get file handler for the logger, and give it a name
            :param filepath (str):                      Path to log file
            :return file_handler (logging.FileHandler): FileHandler
        """
        file_handler = logging.FileHandler(filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(SensitiveFormatter(self.get_logging_formatter()))
        file_handler.name = "file_handler"
        return file_handler

    def _get_logging_formatter(self):
        """
        Get formatter for logging. This is script mode-dependent
            :return (str):  Logging formatter string
        """
        if ad_config.TESTING:
            flag = "TEST_MODE - "
        else:
            flag = ""
        return f"%(asctime)s - {flag}%(name)s - %(flag)s - %(levelname)s - %(message)s"

    def _get_syslog_handler(self) -> logging.handlers.SysLogHandler:
        """
        Get syslog handler for the logger, and give it a name
            :return syslog_handler (logging.SysLogHandler): SysLogHandler
        """
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(SensitiveFormatter(self.get_logging_formatter()))
        syslog_handler.name = "syslog_handler"
        return syslog_handler

    def _get_stream_handler(self) -> logging.StreamHandler:
        """
        Get stream handler for the logger (sends to stdout)
            :return stream_handler (logging.StreamHandler): StreamHandler
        """
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(SensitiveFormatter(self.get_logging_formatter()))
        stream_handler.name = "stream_handler"
        return stream_handler
