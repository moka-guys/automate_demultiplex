""" ad_logger.py pytest unit tests. The test suite is currently incomplete
"""
import pytest
from toolbox import toolbox
from ad_logger import ad_logger
from config import ad_config

# TODO finish this test suite as it is currently incomplete


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
            "backup",
            "project",
            "dx_run",
        ]

    def test_get_loggers(self, logfiles_config, caplog):
        """
        Test all runfolder-level loggers
        """
        # logging.disable(logging.NOTSET)  # Re-enable logging
        loggers_obj = ad_logger.RunfolderLoggers(
            __package__, "DUMMY_NAME", logfiles_config
        )
        loggers = loggers_obj.get_loggers()
        for logger_name in loggers.keys():
            # Test logging works as expected
            loggers[logger_name].info(
                f"Test log message. Logger {loggers[logger_name].name}"
            )
            assert loggers[logger_name].name in caplog.text

