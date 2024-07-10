"""conftest.py

Config for pytest.
"""

import os
import pytest
import shutil
import dxpy
from pathlib import Path
from config.ad_config import CREDENTIALS
from ..conftest import test_data_temp

PROJECT_DIR = str(Path(__file__).absolute().parent.parent)  # Project working directory


def pytest_addoption(parser):
    """Add command line options to pytest"""
    parser.addoption(
        "--auth_token_file",
        action="store",
        default=None,
        required=True,
        help="File containing DNANexus authentication key",
    )


@pytest.fixture(scope="function")
def data_test_runfolders():
    """A fixture that returns a list of tuples containing (runfolder_name, fastq_list_file)."""
    return [
        (
            "999999_NB551068_1234_WSCLEANT01",
            os.path.join(
                test_data_temp, "999999_NB551068_1234_WSCLEANT01_upload_runfolder.log"
            ),
            os.path.join(test_data_temp, "test_dir_1_fastqs.txt"),
            [
                f"{test_data_temp}/999999_NB551068_1234_WSCLEANT01/Data/Intensities/BaseCalls/"
                + line.strip()
                for line in open(os.path.join(test_data_temp, "test_dir_1_fastqs.txt"))
            ],
        ),
        (
            "999999_NB551068_1234_WSCLEANT02",
            os.path.join(
                test_data_temp, "999999_NB551068_1234_WSCLEANT02_upload_runfolder.log"
            ),
            os.path.join(test_data_temp, "test_dir_2_fastqs.txt"),
            [
                f"{test_data_temp}/999999_NB551068_1234_WSCLEANT02/Data/Intensities/BaseCalls/"
                + line.strip()
                for line in open(os.path.join(test_data_temp, "test_dir_2_fastqs.txt"))
            ],
        ),
    ]


@pytest.fixture(scope="function")
def data_test_runfolders_fail():
    """A fixture that returns a list of tuples containing (runfolder_name, fastq_list_file)."""
    return [
        (  # Failure case as fastqs in fastq list are different from those in runfolder
            "999999_NB551068_1234_WSCLEANT01",
            os.path.join(
                test_data_temp, "999999_NB551068_1234_WSCLEANT01_upload_runfolder.log"
            ),
            os.path.join(test_data_temp, "test_dir_1_fastqs.txt"),
            [
                f"{test_data_temp}/999999_NB551068_1234_WSCLEANT02/Data/Intensities/BaseCalls/"
                + line.strip()
                for line in open(os.path.join(test_data_temp, "test_dir_2_fastqs.txt"))
            ],
        ),
        (  # Failure case as runfolder name doesn't match an existing DNAnexus project
            "999999_NB551068_2468_WSCLEANT02",
            os.path.join(
                test_data_temp, "999999_NB551068_2468_WSCLEANT02_upload_runfolder.log"
            ),
            os.path.join(test_data_temp, "test_dir_2_fastqs.txt"),
            [
                f"{test_data_temp}/999999_NB551068_1234_WSCLEANT02/Data/Intensities/BaseCalls/"
                + line.strip()
                for line in open(os.path.join(test_data_temp, "test_dir_2_fastqs.txt"))
            ],
        ),
    ]


def data_test_runfolder_uploaderror():
    """ """


@pytest.fixture(scope="function", autouse=True)
def create_test_dirs(data_test_runfolders, request, monkeypatch):
    """Create test data for testing.

    This is an autouse fixture with session function, meaning it is run once per test
    """
    for test_case in data_test_runfolders:
        runfolder_name, upload_runfolder_logfile, fastq_list_file, fastqs_list = (
            test_case
        )
        # Create the runfolder directory as per Illumina spec
        runfolder_path = os.path.join(test_data_temp, runfolder_name)
        fastqs_path = os.path.join(
            test_data_temp, f"{runfolder_path}/Data/Intensities/BaseCalls"
        )
        Path(fastqs_path).mkdir(parents=True, exist_ok=True)
        # Create dummy logfile
        # open(upload_runfolder_logfile, 'w').close()
        # Generate empty fastqfiles in runfolder
        with open(fastq_list_file) as f:
            fastq_list = f.read().splitlines()
            for fastq_file in fastq_list:
                Path(fastqs_path, fastq_file).touch(mode=777, exist_ok=True)
        open(
            os.path.join(runfolder_path, "RTAComplete.txt"), "w"
        ).close()  # Create RTAComplete file
        open(
            upload_runfolder_logfile, "w"
        ).close()  # Create dummy upload runfolder log file
        with open(
            CREDENTIALS["dnanexus_authtoken"]
        ) as f:  # Setup dxpy authentication token read from command line file
            auth_token = f.read().rstrip()
        dxpy.set_security_context(
            {"auth_token_type": "Bearer", "auth_token": auth_token}
        )

    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    for test_case in data_test_runfolders:
        runfolder_name, upload_runfolder_logfile, fastq_list_file, fastqs_list = (
            test_case
        )
        runfolder_path = os.path.join(test_data_temp, runfolder_name)
        shutil.rmtree(runfolder_path)
