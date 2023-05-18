# coding=utf-8
""" ad_logger.py pytest unit tests
"""
import datetime
import pytest
from upload_and_setoff_workflows import RunfolderObject
import ad_logger.ad_logger as ad_logger


class TestAdLoggers:
    """ Test Logging class"""

    @pytest.fixture(scope="function")
    def timestamp(self):
        """ Return a timestamp"""
        return f"{datetime.datetime.now():%Y%m%d_%H%M%S}"

    @pytest.fixture(scope="function")
    def runfolder_obj(self, timestamp):
        """ Return a runfolder object using a runfolder from the test files
        directory
        """
        return RunfolderObject("999999_A01229_0000_00000TEST1", timestamp)

    @pytest.fixture(scope="function")
    def script_logger_names(self):
        return ["usw_script", "demultiplex_script"]

    @pytest.fixture(scope="function")
    def runfolder_logger_names(self):
        return [
            "usw_rf", "demultiplex_rf", "upload_agent", "backup",
            "project", "dx_run"
            ]

    def test_get_log_config(self, timestamp):
        """ Test logging when no runfolder_obj is supplied"""
        assert ad_logger.AdLoggers(timestamp).loggers

    def test_get_runfolder_log_config(self, timestamp, runfolder_obj):
        """ Test function successfully returns runfolder-specific log ad_config
        """
        assert ad_logger.AdLoggers(timestamp, runfolder_obj).loggers

    def test_rf_loggers(self, timestamp, runfolder_obj,
                        caplog, runfolder_logger_names):
        """ Test all loggers (runfolder-level and script-level) """
        loggers = ad_logger.AdLoggers(timestamp, runfolder_obj)

        for logger_name in runfolder_logger_names:
            logger = getattr(loggers, logger_name)
            logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )
            assert logger.name in caplog.text

        # Test logging shutdown works as expected
        loggers.shutdown_logs()

        for logger_name in runfolder_logger_names:
            logger = getattr(loggers, logger_name)
            assert not logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )

    def test_script_loggers(self, timestamp, caplog, script_logger_names):
        """ Test script-level loggers"""
        loggers = ad_logger.AdLoggers(timestamp)

        # Test logging works as expected
        for logger_name in script_logger_names:
            logger = getattr(loggers, logger_name)
            logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )
            assert logger.name in caplog.text

        # Test logging shutdown works as expected
        loggers.shutdown_logs()

        for logger_name in script_logger_names:
            logger = getattr(loggers, logger_name)
            assert not logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )
