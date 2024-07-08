"""
Automate demultiplex logging. Classes required for logging
"""
import sys
import re
import logging
import logging.handlers
from config.ad_config import AdLoggerConfig


def remove_all_loggers() -> None:
    """
    Remove all loggers
        :return None:
    """
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if isinstance(logging.Logger.manager.loggerDict[name], logging.Logger):
            logging.getLogger(name).handlers = []
            logging.getLogger(name).propagate = True
            logging.Logger.manager.loggerDict.pop(name)


def get_logging_formatter() -> str:
    """
    Get formatter for logging. This is script mode-dependent
        :return (str):  Logging formatter string
    """
    return (
        f"%(asctime)s - {AdLoggerConfig.SCRIPT_MODE} "
        "- %(name)s - %(levelname)s - %(message)s"
    )


def set_root_logger() -> None:
    """
    Set up root logger and add stream handler and syslog handler - we only want to add these once
    else it will duplicate log messages to the terminal. All loggers named with the same stem
    as the root logger will use these same syslog handler and stream handler
        :return None:
    """
    sensitive_formatter=SensitiveFormatter(get_logging_formatter())
    logger = logging.getLogger(AdLoggerConfig.REPO_NAME)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(sensitive_formatter)
    stream_handler.name = "stream_handler"
    syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
    syslog_handler.setFormatter(sensitive_formatter)
    syslog_handler.name = "syslog_handler"

    logging.basicConfig(
        level=logging.INFO,
        force=True,
        handlers=[
            stream_handler,
            syslog_handler,
        ]
    )


def shutdown_logs(logger: logging.Logger) -> None:
    """
    Close and remove all handlers for a logging object
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
    Creates a python logging object with custom attributes and a file handler

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
        self.formatter = SensitiveFormatter(get_logging_formatter())

    def get_logger(self) -> logging.Logger:
        """
        Returns a Python logging object, and give it a name
            :return logger (object):    Python logging object with custom attributes
        """
        logger = logging.getLogger(f"{AdLoggerConfig.REPO_NAME}.{self.logger_name}")
        logger.filepath = self.filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler())
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
        file_handler = logging.FileHandler(self.filepath, mode="w", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        file_handler.name = "file_handler"
        return file_handler


class RunfolderLoggers(object):
    """
    Creates an RunfolderLoggers object that contains various loggers required by the
    script that calls it. The loggers created are dictated by the logfiles_config dict
    provided as a parameter

    Attributes
        script (str):           Script from which the base logger was setup
                                (named in same way to ensure it uses the root syslog / stream handler)
        runfolder_name (str):   Runfolder name
        logfiles_config (dict): Dictionary of paths for each logfile
        loggers (dict):         Dict of loggers

    Methods
        get_loggers()
            Create loggers dict using AdLogger class and logfiles_config
    """

    def __init__(self, script: str, runfolder_name: str, logfiles_config: dict):
        """
        Constructor for the RunfolderLoggers class
            :param script (str):            Script from which the base logger was setup
                                            (named in same way to ensure it uses the root syslog / stream handler)
            :param runfolder_name (str):    Runfolder name
            :param logfiles_config (dict):  Dictionary containing the configuration
                                            for the required loggers
        """
        self.script = script
        self.runfolder_name = runfolder_name
        self.logfiles_config = logfiles_config
        self.loggers = self.get_loggers()  # Collect all loggers

    def get_loggers(self) -> dict:
        """
        Assign loggers using logfiles_config
            :return all_loggers (dict): Dict of logger types
        """
        loggers = {}
        for logger_type in self.logfiles_config.keys():
            logger_name = f"{self.script}.{logger_type}-{self.runfolder_name}"
            ad_logger_obj = AdLogger(
                logger_name, logger_type, self.logfiles_config[logger_type]
            )
            loggers[logger_type] = ad_logger_obj.get_logger()
        return loggers
