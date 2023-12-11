#!/usr/bin/python3
# coding=utf-8
"""
Variables used across test modules, including the setup and teardown fixture
that is run before and after every test
"""
import os
import shutil
import pytest
from toolbox import toolbox
from demultiplex import demultiplex
from test import test_demultiplex
from test import test_ad_logger
from ad_logger import ad_logger
from toolbox import toolbox
from config import ad_config

# Variables used across test classes

# TODO prevent logging writing to syslog when in testing mode

data_dir = os.path.abspath("test/data/")
# Temporary directories to copy test files into and to contain outputs
tempdir = os.path.join(os.path.abspath("test"), "temp/")
temp_testfiles_dir = os.path.join(tempdir, "demultiplex_test_files")
temp_runfolderdir = os.path.join(temp_testfiles_dir, "test_runfolders/")
# temp_samplesheets_dir = os.path.join(temp_runfolderdir, "samplesheets")
# temp_samplesheet_path = os.path.join(temp_samplesheets_dir, "%s_SampleSheet.csv")
temp_log_dir = os.path.join(tempdir, "automate_demultiplexing_logfiles")

# Temp directory for samplesheet validator samplesheet test cases
sv_samplesheet_temp_dir = os.path.join(tempdir, "samplesheets")


@pytest.fixture(scope="function")
def logger_obj():
    temp_log = os.path.join(tempdir, "temp.log")
    return ad_logger.AdLogger("demultiplex", "demultiplex", temp_log).get_logger()


def create_logdirs():
    """
    Create temporary log directories for testing purposes
    """
    os.makedirs(temp_log_dir)
    rf_obj = toolbox.RunfolderObject("TEST_FOLDER", ad_config.TIMESTAMP)
    for logfile in rf_obj.logfiles_config.values():
        parent_dir = os.path.dirname(logfile)
        if not os.path.isdir(parent_dir):
            os.makedirs(parent_dir)


def patch_test_ad_logger(monkeypatch):
    """
    Apply patches required for test_ad_logger script. These point the paths to the
    temporary locations:
        - Test logfiles in the temp logfiles dir and within the temp runfolder dirs
    """
    monkeypatch.setattr(toolbox.ad_config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(toolbox.ad_config, "AD_LOGDIR", temp_log_dir)

def patch_test_demultiplex(monkeypatch):
    """
    Apply patches required for test_demultiplex script. These point the paths to the
    temporary locations:
        - Test runfolders in the temp dir
        - Test logfiles in the temp logfiles dir and within the temp runfolder dirs
    """
    monkeypatch.setattr(toolbox.ad_config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(ad_logger.ad_config, "AD_LOGDIR", temp_log_dir)


# TODO fix patching of script loggers as this is not set up correctly !!
@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """
    Setup and teardown before and after each test. Copy all files over to a temporary
    directory before each test is run. Patch variables as temporary directory paths.
    After testing complete remove temporary directory (containing temporary test files,
    created flag files and log files) after testing complete
    """
    # PATCH MODULES THAT NEED PATCHING FOR TESTING (test_ad_email and test_toolbox do
    # not require any patching)
    monkeypatch.setattr(ad_logger.ad_config, "SCRIPT_MODE", "PYTEST_TESTS")
    patch_test_ad_logger(monkeypatch)
    patch_test_demultiplex(monkeypatch)

    # SETUP - cleanup after each test
    if os.path.isdir(tempdir):
        # Remove dir and all flag files created
        shutil.rmtree(tempdir)
    # Create temporary dirs for testing
    shutil.copytree(data_dir, tempdir)
    create_logdirs()

    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(tempdir):
        # Remove dir and all flag files created
        shutil.rmtree(tempdir)
    # logging.disable(logging.NOTSET)  # Re-enable logging
