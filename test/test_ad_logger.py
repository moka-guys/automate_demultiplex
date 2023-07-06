#!/usr/bin/python3
# coding=utf-8
"""
ad_logger.py pytest unit tests
"""
import pytest
from shared_functions.shared_functions import RunfolderObject
import ad_logger.ad_logger as ad_logger
import config.ad_config as ad_config
import logging
import test.conftest as test_config
import inspect


# No logging disabled for this test as we are testing logging

# TODO add tests for SensitiveFormatter class
# TODO add test for shutdown_logs and shutdown_streamhandler
# TODO add test that checks that streamhandler, filehandler and syslog handler are all
# added as expected
class TestAdLoggers:
    """Test Logging class"""

    @pytest.fixture(scope="function")
    def rf_obj(self):
        """
        Return a runfolder object using a runfolder from the test files directory
        """
        loggers = ad_logger.AdLoggers(
            {"usw": ad_config.USW_SCRIPT_LOGFILE % ad_config.TIMESTAMP}
            )
        rf_obj = RunfolderObject(
            "999999_A01229_0000_00000TEST1", loggers, ad_config.TIMESTAMP
            )
        rf_obj.add_runfolder_loggers()
        return rf_obj

    @pytest.fixture(scope="function")
    def runfolder_logger_names(self):
        return [
            "usw",
            "demultiplex",
            "upload_agent",
            "backup",
            "project",
            "dx_run",
        ]

    def test_rf_loggers(self, rf_obj, caplog, runfolder_logger_names):
        """
        Test all runfolder-level loggers
        """
        for logger_name in runfolder_logger_names:
            logger = getattr(rf_obj.rf_loggers, logger_name)
            # Test logging works as expected
            logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )
            assert logger.name in caplog.text

            # Test logging shutdown works as expected
            for logger in rf_obj.rf_loggers.loggers:
                logger.shutdown_logs()
            assert not logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )

    def test_script_loggers(self, rf_obj, caplog):
        """
        Test all script-level loggers
        """
        for logger_name in rf_obj.script_loggers.logfiles_config.keys():
            logger = getattr(rf_obj.script_loggers, logger_name)
            # Test logging works as expected
            logger.info(
                "Test log message. Logger %s",
                logger_name,
                extra={"flag": "demultiplex_started"},
            )
            assert logger.name in caplog.text

            # Test logging shutdown works as expected
            rf_obj.script_loggers.shutdown_logs()
            assert not logger.info(
                "Test log message. Logger %s",
                logger_name,
                extra={"flag": "demultiplex_started"},
            )
