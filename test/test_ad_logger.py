#!/usr/bin/python3
# coding=utf-8
"""
ad_logger.py pytest unit tests
"""
import pytest
from test import conftest
from toolbox import toolbox
from ad_logger import ad_logger
from config import ad_config
# import logging

# No logging disabled for this test as we are testing logging
# No patching required

# TODO add tests for SensitiveFormatter class
# TODO add test for shutdown_logs and shutdown_streamhandler
# TODO add test that checks that streamhandler, filehandler and syslog handler are all
# added as expected

# TODO write test for shutdown_streamhandler()
# def test_shutdown_streamhandler():

# TODO write test for shutdown_logs()
# def test_shutdown_logs():
#     """"""

#     ad_logger.shutdown_logs(logger)
# assert not logger.info(
#     "Test log message. Logger %s",
#     logger.name,
# )

# TODO write tests for SensitiveFormatter class
# class TestSensitiveFormatter:
#    """
#    Tests for the SensitiveFormatter class
#    """


# @pytest.fixture(scope="function", autouse=True)
# def setup(monkeypatch):
#     """
#     """
#     #  Re-enable logging as it is required for assertions
#     logging.disable(logging.NOTSET)
#     # Remove testfiles dir containing test runfolders as we don't need these files
#     # Apply patches required for test_ad_logger script. These point the paths to the
#     # temporary locations:
#     #     - Test logfiles in the temp logfiles dir and within the temp runfolder dirs
#     monkeypatch.setattr(toolbox.ad_config, "RUNFOLDERS", conftest.temp_runfolderdir)
#     monkeypatch.setattr(toolbox.ad_config, "AD_LOGDIR", conftest.temp_log_dir)


class TestRunfolderLoggers:
    """
    Tests for the SamplesheetCheck class
    """

    @pytest.fixture(scope="function")
    def logfiles_config(self):
        """
        Return a runfolder object using a runfolder from the test files directory
        """
        return toolbox.RunfolderObject(
            "999999_A01229_0000_00000TEST1", ad_config.TIMESTAMP
            ).logfiles_config

    @pytest.fixture(scope="function")
    def runfolder_logger_names(self):
        return [
            "sw",
            "demultiplex",
            "upload_agent",
            "backup",
            "project",
            "dx_run",
        ]

    def test_get_loggers(self, logfiles_config, caplog):
        """
        Test all runfolder-level loggers
        """
        # logging.disable(logging.NOTSET)  # Re-enable logging
        runfolder_loggers = ad_logger.RunfolderLoggers(logfiles_config)
        for logger in runfolder_loggers.loggers:
            # Test logging works as expected
            logger.info(f"Test log message. Logger {logger.name}")
            assert logger.name in caplog.text


# TODO write tests for AdLogger class
# class TestAdLogger:
    """
    Tests for the AdLogger class
    """
