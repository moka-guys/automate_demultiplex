#!/usr/bin/python3
"""
Variables used across test modules, including the setup and teardown fixture
that is run before and after every test
"""
import os
import shutil
import pytest
import tarfile
import logging

# sys.path.append("..")
from ad_logger import ad_logger
from toolbox import toolbox
from config import ad_config

# Variables used across test classes

# TODO prevent logging writing to syslog when in testing mode


test_data_dir = os.path.abspath("data")  # Data directory
test_data_dir_unzipped = os.path.join(
    test_data_dir, "data_unzipped/"
)  # Unzips data tar to here
test_data_temp = os.path.abspath("temp")  # Copies data to here for each test
# Place interop in test 7, test 9, test 11
data_tars = [
    {
        "src": os.path.join(test_data_dir, "demultiplex_test_files.tar.gz"),
        "dest": test_data_dir_unzipped,
    },
    {
        "src": os.path.join(test_data_dir, "samplesheets.tar.gz"),
        "dest": test_data_dir_unzipped,
    },
    {
        "src": os.path.join(test_data_dir, "InterOp/batch_1.tar.gz"),
        "dest": os.path.join(test_data_dir_unzipped, "InterOp"),
    },
    {
        "src": os.path.join(test_data_dir, "InterOp/batch_2.tar.gz"),
        "dest": os.path.join(test_data_dir_unzipped, "InterOp"),
    },
    {
        "src": os.path.join(test_data_dir, "InterOp/batch_3.tar.gz"),
        "dest": os.path.join(test_data_dir_unzipped, "InterOp"),
    },
]
source_runfolder_dirs = os.path.join(
    test_data_dir_unzipped, "demultiplex_test_files/test_runfolders/"
)

to_copy_interop_to = [
    os.path.join(source_runfolder_dirs, "999999_A01229_0000_00000TEST7/InterOp/"),
    os.path.join(source_runfolder_dirs, "999999_A01229_0000_00000TEST9/InterOp/"),
    os.path.join(source_runfolder_dirs, "999999_A01229_0000_0000TEST11/InterOp/"),
]

temp_runfolderdir = os.path.join(
    test_data_temp, "data_unzipped/demultiplex_test_files/test_runfolders/"
)
temp_log_dir = os.path.join(test_data_temp, "automate_demultiplexing_logfiles")
temp_samplesheet_logdir = os.path.join(
    temp_log_dir, "samplesheet_validator_script_logfiles"
)
# Temp directory for SampleSheet validator SampleSheet test cases
sv_samplesheet_temp_dir = os.path.join(test_data_temp, "data_unzipped/samplesheets")


@pytest.fixture(scope="function")
def logger_obj():
    temp_log = os.path.join(test_data_temp, "temp.log")
    return ad_logger.AdLogger(__name__, "demux", temp_log).get_logger()


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


def patch_toolbox(monkeypatch):
    """
    Apply patches required for toolbox script. These point the paths to the
    temporary locations:
        - Test logfiles in the temp logfiles dir and within the temp runfolder dirs
    """
    monkeypatch.setattr(toolbox.ToolboxConfig, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(toolbox.ToolboxConfig, "AD_LOGDIR", temp_log_dir)


@pytest.fixture(scope="session", autouse=True)
def run_before_and_after_session():
    """
    Remove data directory if exists. Cleans up directory structure in the event that the
    tests are force stopped part way through
    """
    # Create temporary dirs for testing
    os.makedirs(
        test_data_dir_unzipped
    )  # Holds the unzipped data to copy from for each test

    for tar in data_tars:
        with tarfile.open(tar["src"], "r:gz") as open_tar:
            open_tar.extractall(path=tar["dest"])
    for destination in to_copy_interop_to:
        shutil.copytree(os.path.join(test_data_dir_unzipped, "InterOp"), destination)
    yield
    for to_remove in [test_data_dir_unzipped, test_data_temp]:
        if os.path.isdir(to_remove):
            shutil.rmtree(to_remove)


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
    monkeypatch.setattr(ad_logger.AdLoggerConfig, "SCRIPT_MODE", "PYTEST_TESTS")
    patch_toolbox(monkeypatch)
    # SETUP - cleanup after each test
    if os.path.isdir(test_data_temp):
        # Remove dir and all flag files created
        shutil.rmtree(test_data_temp)
    # Create temporary dirs for testing
    shutil.copytree(test_data_dir, test_data_temp)
    create_logdirs()

    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(test_data_temp):
        # Remove dir and all flag files created
        shutil.rmtree(test_data_temp)
    ad_logger.remove_all_loggers()
