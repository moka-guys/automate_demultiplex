"""
Variables used across test modules, including the setup and teardown fixture
that is run before and after every test
"""
import os
import shutil
import pytest
import config.ad_config as ad_config  # Import ad_config file
import runfolder_obj.runfolder_obj as runfolder_obj

# Variables used across test classes

data_dir = os.path.abspath("test/data/")
# Temporary directories to copy test files into and to contain outputs
tempdir = os.path.join(os.path.abspath("test"), "temp/")
temp_testfiles_dir = os.path.join(tempdir, "demultiplex_test_files")
temp_runfolderdir = os.path.join(temp_testfiles_dir, "test_runfolders/")
temp_samplesheets_dir = os.path.join(temp_runfolderdir, "samplesheets")
temp_samplesheet_path = os.path.join(temp_samplesheets_dir, "%s_SampleSheet.csv")
temp_log_dir = os.path.join(tempdir, "automate_demultiplexing_logfiles")

# Temp directory for samplesheet validator samplesheet test cases
sv_samplesheet_temp_dir = os.path.join(tempdir, "samplesheets")


LOGDIRS = {
    "demultiplex": os.path.join(temp_log_dir, "Demultiplexing_log_files/"),
    "dx_run_cmds": os.path.join(temp_log_dir, "dx_run_commands"),
    "backup_runfolder": os.path.join(temp_log_dir, "backup_runfolder_logfiles"),
    "upload_script": os.path.join(temp_log_dir, "upload_agent_script_logfiles"),
    "nexus_project_creation_scripts": (
        os.path.join(temp_log_dir, "nexus_project_creation_scripts")
    ),
}

# Paths to dummy logfiles in temp dir
LOGFILES = {
    # Records output of demultiplex script
    "demultiplex_script_logfile": os.path.join(
        temp_log_dir, "Demultiplexing_log_files/", "%s_demultiplex_script_log.log"
    ),
    # Records output of upload and setoff workflow script
    "upload_script": os.path.join(
        temp_log_dir,
        "upload_agent_script_logfiles",
        "%s_upload_and_setoff_workflow.log",
    ),
    "backup_runfolder": os.path.join(
        temp_log_dir, "backup_runfolder_logfiles", "%s_backup_runfolder.log"
    ),
    "dx_run_script": os.path.join(
        temp_log_dir, "dx_run_commands", "%s_dx_run_commands.sh"
    ),
    # DNAnexus run command script
    "congenica_upload_script": os.path.join(
        temp_log_dir, "dx_run_commands", "%s_congenica.sh"
    ),
    # Script containing dnanexus project creation command
    "proj_creation_script": os.path.join(
        temp_log_dir, "nexus_project_creation_scripts", "create_nexus_project_%s.sh"
    ),
}


@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """
    Setup and teardown before and after each test. Copy all files over to a
    temporary directory before each test is run. Patch variables as temporary
    directory paths. After testing complete remove temporary directory
    (containing temporary test files, created flag files and log files) after
    testing complete
    """
    monkeypatch.setattr(ad_config, "LOGFILES", LOGFILES)
    monkeypatch.setattr(ad_config, "LOGDIRS", LOGDIRS)
    monkeypatch.setattr(ad_config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(ad_config, "SAMPLESHEET_PATH", temp_samplesheet_path)

    monkeypatch.setattr(runfolder_obj.ad_config, "LOGFILES", LOGFILES)
    monkeypatch.setattr(runfolder_obj.ad_config, "LOGDIRS", LOGDIRS)
    monkeypatch.setattr(runfolder_obj.ad_config, "RUNFOLDERS", temp_runfolderdir)
    monkeypatch.setattr(
        runfolder_obj.ad_config, "SAMPLESHEET_PATH", temp_samplesheet_path
    )

    # Create temporary dirs for testing
    shutil.copytree(data_dir, tempdir)

    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(tempdir):
        # Remove dir and all flag files created
        shutil.rmtree(tempdir)
