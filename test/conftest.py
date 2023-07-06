#!/usr/bin/python3
# coding=utf-8
"""
Variables used across test modules, including the setup and teardown fixture
that is run before and after every test
"""
import os
import shutil
import pytest
import config.ad_config as ad_config  # Import ad_config file
import shared_functions.shared_functions as shared_functions
from demultiplex import demultiplex
import logging
from pathlib import Path
import test.test_demultiplex as test_demultiplex
import ad_logger.log_config as logger_config

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


# LOGDIRS = {
#     "demultiplex": os.path.join(temp_log_dir, "demultiplexing_script_logfiles"),
#     "dx_run_cmds": os.path.join(temp_log_dir, "dx_run_commands"),
#     "backup": os.path.join(temp_log_dir, "backup_runfolder_script_logfiles"),
#     "usw": os.path.join(temp_log_dir, "usw_script_logfiles"),
#     "nexus_project_creation_scripts": (
#         os.path.join(temp_log_dir, "nexus_project_creation_scripts")
#     ),
#     "decision_support_script_log":
#         os.path.join(temp_log_dir, "decision_support_script_logfiles"),
# }

# Paths to dummy logfiles in temp dir
# LOGFILES = {
#     # Records output of demultiplex script
#     "demultiplex_script_logfile": os.path.join(
#         temp_log_dir, "demultiplexing_script_logfiles/", "%s_demultiplex_script_log.log"
#     ),
#     # Records output of upload and setoff workflow script
#     "usw": os.path.join(
#         temp_log_dir,
#         "usw_script_logfiles",
#         "%s_upload_and_setoff_workflow.log",
#     ),
#     "backup": os.path.join(
#         temp_log_dir, "backup_runfolder_script_logfiles", "%s_backup_runfolder.log"
#     ),
#     "dx_run_script": os.path.join(
#         temp_log_dir, "dx_run_commands", "%s_dx_run_commands.sh"
#     ),
#     # DNAnexus run command script
#     "congenica_upload_script": os.path.join(
#         temp_log_dir, "dx_run_commands", "%s_congenica.sh"
#     ),
#     # Script containing dnanexus project creation command
#     "proj_creation_script": os.path.join(
#         temp_log_dir, "nexus_project_creation_scripts", "create_nexus_project_%s.sh"
#     ),
#     "decision_support_script_log": os.path.join(
#         temp_log_dir, "decision_support_script_logfiles",
#         "decision_support_script_log_%s.log"
#     )
# }

# # Upload and setoff workflows script logfile
# SCRIPTLOG_CONFIG = {
#     "usw": {"usw": LOGFILES["usw"] % ad_config.TIMESTAMP},
#     "demultiplex": {"demultiplex": LOGFILES["demultiplex_script_logfile"] % ad_config.TIMESTAMP},
#     "backup": {"backup": LOGFILES["backup"] % ad_config.TIMESTAMP},
# }


def create_logdirs():
    """
    Create temporary log directories for testing purposes
    """
    os.makedirs(temp_log_dir)
    for logfile in shared_functions.return_rflog_config("").values():
        parent_dir = os.path.dirname(logfile)
        if not os.path.isdir(parent_dir):
            os.makedirs(parent_dir)


# TODO fix the patching as it is not working correctly
@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """
    Setup and teardown before and after each test. Copy all files over to a temporary
    directory before each test is run. Patch variables as temporary directory paths.
    After testing complete remove temporary directory (containing temporary test files,
    created flag files and log files) after testing complete
    """
    # Disable messages at level DEBUG and below to reduce the number of log messages
    # logging.disable(logging.DEBUG)
    logging.disable(logging.NOTSET)
    # monkeypatch.setattr(ad_config, "RUNFOLDERS", temp_runfolderdir)
    # monkeypatch.setattr(ad_config, "AD_LOGDIR", temp_log_dir)
    # print(ad_config.PROJECT_DIR)
    # print(ad_config.DOCUMENT_ROOT)

    monkeypatch.setattr(demultiplex.ad_config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(demultiplex.shared_functions.ad_config, "RUNFOLDERS", temp_runfolderdir)

    for module in [
        demultiplex,
        demultiplex.shared_functions,
        demultiplex.shared_functions.ad_logger,
        test_demultiplex.demultiplex,
        test_demultiplex.demultiplex.shared_functions,
        test_demultiplex.demultiplex.shared_functions.ad_logger
    ]:
        monkeypatch.setattr(module.ad_config, "RUNFOLDERS", temp_runfolderdir)
        monkeypatch.setattr(module.ad_config, "AD_LOGDIR", temp_log_dir)

    # monkeypatch.setattr(demultiplex.ad_config, "RUNFOLDERS", conftest.temp_runfolderdir)
    # monkeypatch.setattr(demultiplex.shared_functions.ad_config, "RUNFOLDERS", conftest.temp_runfolderdir)

    # SETUP - cleanup after each test
    if os.path.isdir(tempdir):
        # Remove dir and all flag files created
        shutil.rmtree(tempdir)
    # Create temporary dirs for testing
    shutil.copytree(data_dir, tempdir)
    print(tempdir)
    create_logdirs()

    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(tempdir):
        # Remove dir and all flag files created
        shutil.rmtree(tempdir)
    logging.disable(logging.NOTSET)


# @pytest.fixture(autouse=True)
# def autofixt(request):
#     """
#     Disable messages at specified level and below to reduce the number of log messages
#     """
#     if 'disableloggerscritical' in request.keywords:
#         logging.disable(logging.CRITICAL)
#     elif 'disableloggerswarning' in request.keywords:
#         logging.disable(logging.WARNING)
#     elif 'disableloggersinfo' in request.keywords:
#         logging.disable(logging.INFO)


# @pytest.fixture(autouse=True)
# def run_before_and_after_tests(monkeypatch):
#     """
#     Run tasks specific to only these test cases before and after each test
    # """

    # # Patch RunfolderObject with the correct temp runfolder path


    # #     self.runfolderpath = os.path.join(ad_config.RUNFOLDERS, self.runfolder_name)


    # # logfiles_config




    # # ad_email does not require any patching
    # # samplesheet valdiator does not require any patching



    # # Need to patch RunfolderObject directly as this is used in test_samplesheet_validator and test_ad_logger
    # # Need to patch ad_logger.ad_logger and and ad_logger.log_config directly as these are used
    # # in
    # # 


    # #  passed as an input to

    # # Patch variables in demultiplex
    # # Patch variables in ad_logger

    # # monkeypatch.setattr(logger_config, "LOGFILES", LOGFILES)
    # # monkeypatch.setattr(ad_config, "SAMPLESHEET_PATH", temp_samplesheet_path)



    # # monkeypatch.setattr(shared_functions.logger_config, "LOGFILES", LOGFILES)
    # # monkeypatch.setattr(shared_functions.ad_config, "RUNFOLDERS", temp_runfolderdir)
    # # monkeypatch.setattr(
    # #     shared_functions.ad_config, "SAMPLESHEET_PATH", temp_samplesheet_path
    # # )
    # # monkeypatch.setattr(shared_functions.ad_config, "RUNFOLDERS", temp_runfolderdir
