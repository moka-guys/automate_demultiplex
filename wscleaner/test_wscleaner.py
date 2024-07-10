import pytest
from pathlib import Path
import shutil
from . import wscleaner
from .conftest import data_test_runfolders, data_test_runfolders_fail
from ..conftest import test_data_temp
from config.ad_config import RunfolderCleanupConfig



@pytest.fixture
def rfm(monkeypatch):
    """
    Return an instance of the runfolder manager with the test/data directory
    Monkeypatch is used to overwrite the upload runfolder logfile to the file created
    in the conftest
    """
    monkeypatch.setattr(
        RunfolderCleanupConfig,
        "RUNFOLDERS",
        test_data_temp,
    )
    return wscleaner.RunFolderManager(str(test_data_temp))


@pytest.fixture
def rfm_dry(monkeypatch):
    """Return an instance of the runfolder manager with the test/data directory
    Monkeypatch is used to overwrite the upload runfolder logfile to the file created
    in the conftest"""
    monkeypatch.setattr(
        RunfolderCleanupConfig,
        "RUNFOLDERS",
        test_data_temp,
    )
    return wscleaner.RunFolderManager(dry_run=True)


class TestCheckRunfolder:

    def test_runfolders_ready(self, data_test_runfolders):
        """
        Test that test runfolders pass checks for deletion
        """
        for test_case in data_test_runfolders:
            runfolder_name, upload_runfolder_logfile, fastq_list_file, fastqs_list = test_case
            crf = wscleaner.CheckRunfolder(runfolder_name=runfolder_name, upload_runfolder_logfile=upload_runfolder_logfile, fastqs_list=fastqs_list, logfile_count=6) 
            assert all(
                [
                    crf.dx_project,
                    crf.check_fastqs(),
                    crf.check_logfiles(),
                    crf.upload_log_exists(),
                    crf.check_upload_log(),
                ]
            )

    def test_runfolders_ready_fail(self, data_test_runfolders_fail):
        """
        Test that test runfolders pass checks for deletion
        """
        for test_case in data_test_runfolders_fail:
            runfolder_name, upload_runfolder_logfile, fastq_list_file, fastqs_list = test_case
            crf = wscleaner.CheckRunfolder(runfolder_name=runfolder_name, upload_runfolder_logfile=upload_runfolder_logfile, fastqs_list=fastqs_list, logfile_count=6) 
            assert not all(
                [
                    crf.dx_project,
                    crf.check_fastqs(),
                    crf.check_logfiles(),
                    crf.upload_log_exists(),
                    crf.check_upload_log(),
                ]
            )

    def test_to_delete(self, data_test_runfolders):
        """
        Test the function correctly identifies that the runfolders require deletion
        """
        for test_case in data_test_runfolders:
            runfolder_name, upload_runfolder_logfile, fastq_list_file, fastqs_list = test_case
            crf = wscleaner.CheckRunfolder(runfolder_name=runfolder_name, upload_runfolder_logfile=upload_runfolder_logfile, fastqs_list=fastqs_list, logfile_count=6) 
            result = crf.to_delete()
            assert result == True
