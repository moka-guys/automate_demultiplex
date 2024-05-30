#!/usr/bin/python3
""" ad_logger.py pytest unit tests

# TODO write the following unit tests which are currently missing or incomplete:
- shutdown_logs
- SensitiveFormatter
    - format
- AdLogger
    - get_logger
    - _get_file_handler
    - _get_logging_formatter
    - _get_syslog_handler
    - _get_stream_handler
"""
import pytest
from toolbox import toolbox
from ad_logger import ad_logger
from config import ad_config

# import logging

# No logging disabled for this test as we are testing logging
# No patching required

# TODO add tests for SensitiveFormatter class
# TODO add test for shutdown_logs
# TODO add test that checks that streamhandler, filehandler and syslog handler are all
# added as expected


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
    Tests for the RunfolderLoggers class
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
        loggers_obj = ad_logger.RunfolderLoggers(__package__, "DUMMY_NAME", logfiles_config)
        loggers = loggers_obj.get_loggers()
        for logger_name in loggers.keys():
            # Test logging works as expected
            loggers[logger_name].info(
                f"Test log message. Logger {loggers[logger_name].name}"
            )
            assert loggers[logger_name].name in caplog.text

    # TODO write tests for AdLogger class
    # class TestAdLogger:
    """
    Tests for the AdLogger class
    """
