# coding=utf-8
""" ad_logger.py pytest unit tests
"""

import os
import shutil
import datetime
import pytest
from upload_and_setoff_workflows import RunfolderObject
import ad_config as config  # Import config file
import git_tag.git_tag as git_tag
import ad_logger.ad_logger as ad_logger

# Variables used across test classes
# Path of directory containing test files
testfiles_dir = os.path.abspath("test/demultiplex_test_files/")
# Temporary directory to copy test files into and to contain outputs
temp_dir = os.path.join(testfiles_dir, "temp")
temp_runfolderdir = os.path.join(temp_dir, "test_runfolders")
# Paths to dummy logfiles in temp dir
backup_runfolder_logfile = os.path.join(temp_dir, "%s_backup_runfolder.log")
proj_creation_script = os.path.join(temp_dir, "create_nexus_project_%s.sh")
dx_run_script = os.path.join(temp_dir, "%s_dx_run_commands.sh")
upload_script_logfile = os.path.join(
    temp_dir, "%s_upload_and_setoff_workflow.log"
)

# TODO finish writing test cases


@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """Fixture to execute asserts before and after a test is run - resets class variables and
    removes temp dirs"""
    # SETUP -
    # monkeypatch.setattr(config, "ad_logfiles", temp_dir)
    monkeypatch.setattr(
        config, "BACKUP_RUNFOLDER_LOGFILE", backup_runfolder_logfile
    )
    monkeypatch.setattr(config, "PROJ_CREATION_SCRIPT", proj_creation_script)
    monkeypatch.setattr(config, "DXRUN_SCRIPT", dx_run_script)
    monkeypatch.setattr(config, "UPLOAD_SCRIPT_LOGFILE", upload_script_logfile)
    monkeypatch.setattr(config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(config, "DEMULTIPLEX_LOGPATH", temp_dir)
    shutil.copytree(testfiles_dir, temp_dir)
    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)  # Remove dir and all flag files created


class TestAdLoggers:
    """Test Logging class"""

    @pytest.fixture(scope="function")
    def rf_obj(self):
        """Return a runfolder object using a runfolder from the test files directory"""
        return RunfolderObject("999999_A01229_0000_00000TEST1")

    @pytest.fixture(scope="function")
    def timestamp(self):
        """Return a timestamp"""
        return f"{datetime.datetime.now():%Y%m%d_%H%M%S}"

    def test_get_log_config(self, timestamp):
        """Test logging when no rf_obj is supplied"""
        assert ad_logger.get_log_config(timestamp)

    def test_get_runfolder_log_config(self, timestamp, rf_obj):
        """Test function successfully returns runfolder-specific log config"""
        assert ad_logger.get_log_config(timestamp, rf_obj)

    def test_loggers(self, timestamp, rf_obj, caplog):
        """Test runfolder-specific loggers"""
        log_config = ad_logger.get_log_config(timestamp, rf_obj)
        ad_loggers = ad_logger.AdLoggers(log_config).all_loggers

        for logger in ad_loggers:
            logger.info(
                "Test log message. Logger %s",
                logger.name,
                extra={"flag": "demultiplex_started"},
            )
            assert logger.name in caplog.text

    # def test_demux_logger():
    #     """Test demultiplex script logger (not runfolder-specfic)"""
    #     demux_log_config = ad_logger.get_demux_log_config(timestamp)
    #     demux_ad_loggers = ad_logger.AdLoggers(demux_log_config, runfolder=False)
    #     for logfile in loggers:
    #         with self.assertLogs() as captured:
    #             self.loggers.demultiplex.info("Test log message. Version %s", git_tag(),
    #                                             extra={"flag": "demultiplex_started"})
    #             self.assertEqual(len(captured.records), 1) # check that there is only one log message
    #             self.assertEqual(captured.records[0].getMessage(), "Hello, World!") # and it is the proper one

    # def test_shutdown_logs():

    # @pytest.fixture
    # def expected_message(cls):
    #     return 'demultiplextest_info - INFO - Logging test string'

    # def test_logger_pass(cls, logger, expected_message):
    #     """Check expected strings written to logfile. This means writing to syslog was also
    #     successful"""
    #     logger.info("Logging test string", extra={'flag': 'demultiplextest_info'})
    #     with open(cls.scriptlog_path) as f:
    #         assert expected_message in f.read()
