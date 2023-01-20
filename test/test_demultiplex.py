# coding=utf-8
""" demultiplex.py pytest unit tests
"""
import os
import shutil
import datetime
import itertools
from test.test_samplesheet_validator import (
    base_path,
    valid_samplesheets,
    invalid_paths,
    invalid_names,
    empty_file,
    invalid_contents,
)
import pytest
import sys
from mock import patch
import demultiplex
import ad_config as config  # Import config file
import ad_logger.ad_logger as ad_logger
import inspect

# Variables used across test classes

# Path of directory containing test files
testfiles_dir = os.path.abspath("test/demultiplex_test_files/")
# Location of the bcl2fastq executable within this repository for testing purposes
# Temporary directory to copy test files into and to contain outputs
temp_dir = os.path.join(testfiles_dir, "temp/")
demultiplex_log_file = os.path.join(temp_dir, f"{datetime.datetime.now():%Y%m%d_%H%M%S}.txt")
temp_runfolderdir = os.path.join(temp_dir, "test_runfolders/")
temp_samplesheetsdir = os.path.join(temp_runfolderdir, "samplesheets/")


# @patch('config.demultiplex_logpath', temp_dir)
# @patch('demultiplex.config.demultiplex_logpath', temp_dir)
# @patch('demultiplex.config.demultiplex_logpath', temp_dir)
# @patch('demultiplex.GetRunfolders.demultiplex_log', demultiplex_log_file)


@pytest.fixture(scope="module", autouse=True)
def run_before_and_after_tests():
    """Setup and teardown before and after each test
    Copy all files over to a temporary directory before each test is run
    Removes temporary directory (containing temporary test files and created flag files)
    after testing complete
    """
    shutil.copytree(testfiles_dir, temp_dir)
    yield  # Where the testing happens
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)


class TestGetRunfolders(object):
    """Test GetRunfolders class - UPDATE THIS
    There is no test for the case where demultiplex_runfolders passes runfolders to
    DemultiplexRunfolder which are processed by DemultiplexRunfolder
    This is because the script tries to run bcl2fastq which inevitably fails for the test cases due
    to the absence of any sequencing data in the test cases. This should be tested using real data
    on the workstation."""

    @patch('demultiplex.config.runfolders', temp_runfolderdir)
    @pytest.fixture(scope="function", autouse=True)
    def gr_mock(self, monkeypatch):
        """Create GetRunfolders object to use in tests
        Fixture is called automatically for all tests
        Monkeypatch paths from config that will not exist on the local machine so would cause
        tests to fail
        We want this to re-run for each test in case any patching has been performed
        within individual tests"""
        monkeypatch.setattr(config, "runfolders", temp_runfolderdir)
        monkeypatch.setattr(config, "demultiplex_logpath", temp_dir)
        monkeypatch.setattr(config, "bcl2fastq_path", os.path.join("/bin/true"))
        return demultiplex.GetRunfolders()

    @pytest.fixture(scope="function")
    def processed_runfolders(self):
        """String of 4 processed runfolders"""
        return [(4, ["these", "are", "processed", "runfolders"])]
    # NEED TO RETHINK THIS AND ADD A PASS AND FAIL CASE - SHOULD BE POSSIBLE NOW WITH MONKEYPATCH
    def test_rundemultiplexrunfolders(self, gr_mock):
        """Pass set of dummy runfolders to the test and assert that the expected number are
        processed. processed_runfolders should be empty as the script tries to run bcl2fastq so
        inevitably fails for all runfolders due to absence of sequencing data in test cases"""
        assert not gr_mock.run_demultiplexrunfolders()

    def test_bcl2fastq_installed_pass(self, gr_mock): # DONE
        """Check bcl2fastq_install function is working using functional test bcl2fastq executable"""
        assert gr_mock.bcl2fastq_installed()

    def test_bcl2fastq_installed_fail(self, monkeypatch, gr_mock): # DONE
        """Provide incorrect bcl2fastq path"""
        monkeypatch.setattr(gr_mock, "bcl2fastq_path", "/path/to/nonexistent/bcl2fastq")
        assert not gr_mock.bcl2fastq_installed()

    def test_rename_demultiplex_logfile(self, processed_runfolders, gr_mock):  # DONE
        """Tests that script logfile is renamed if there are processed runfolders
        Create the file ready for function to rename"""
        for num_runfolders, runfolders in processed_runfolders:
            open(gr_mock.demultiplex_logfile, 'w+', encoding="utf-8").close()  # Create logfile
            assert gr_mock.rename_demultiplex_logfile(runfolders, num_runfolders)
            assert all(name in gr_mock.demultiplex_logfile for name in runfolders)


class TestDemultiplexRunfolder(object):
    """Test DemultiplexRunfolder class"""

    @patch('demultiplex.config.runfolders', temp_runfolderdir)
    @pytest.fixture(scope="function", autouse=True)
    def gr_mock(self, monkeypatch):
        """Create GetRunfolders object to use in tests
        Fixture is called automatically for all tests
        Monkeypatch paths from config that will not exist on the local machine so would cause
        tests to fail
        We want this to re-run for each test in case any patching has been performed
        within individual tests"""
        monkeypatch.setattr(config, "runfolders", temp_runfolderdir)
        monkeypatch.setattr(config, "demultiplex_logpath", temp_dir)
        monkeypatch.setattr(config, "bcl2fastq_path", os.path.join("/bin/true"))
        return demultiplex.GetRunfolders()

    @pytest.fixture(scope="function")
    def dr_mock(self, monkeypatch, gr_mock):
        """Create DemultiplexRunfolder object to use in tests"""
        monkeypatch.setattr(config, "bcl2fastq_path", os.path.join("/bin/true"))

        dr_mock = demultiplex.DemultiplexRunfolder(samplesheet_path=os.getcwd(),
                                                   runfolderpath="",
                                                   folder_name="",
                                                   logger=gr_mock.demux_logger)
        monkeypatch.setattr(dr_mock, "rtacompletefile_path",  # Dummy sequencing complete file
                            os.path.join(testfiles_dir, "RTAComplete.txt"))
        monkeypatch.setattr(dr_mock, "bcl2fastqlog_path",  # Perfect samplesheet
                            os.path.join(temp_dir, "bcl2fastq2_output_success.log"))
        monkeypatch.setattr(dr_mock, "checksumfile_path",  # md5checksum pass file
                            os.path.join(temp_dir, "md5checksum_pass.txt"))
        return dr_mock

    @pytest.fixture(scope="function")
    def bcl2fastqlog_fail(self):
        """Logfiles containing bcl2fastq pass and fail messages"""
        return [
            (
                os.path.join(testfiles_dir, "bcl2fastq2_output_nomsg.log")
            ),  # No success message present in logfile
            "nonexistent.log",  # Logfile nonexistent
            (
                os.path.join(testfiles_dir, "bcl2fastq2_output_empty.log")
            ),  # Logfile empty
        ]

    @pytest.fixture(scope="function")
    def icheck_required(self):
        """Runfolder that would require an integrity check"""
        return "999999_NB551068_0009_AH3YERAFX3"

    @pytest.fixture(scope="function")
    def icheck_notrequired(self):
        """Runfolder that would not require an integrity check"""
        return "999999_M02353_0641_000000000-TESTS"

    @pytest.fixture(scope="function")
    def temp_md5checksum_fail(self):
        """Mock checksum file. This is a file within the repository that contains the md5
        checksum fail string"""
        return os.path.join(temp_dir, "md5checksum_fail.txt")

    @pytest.fixture(scope="function")
    def temp_md5checksum_prevfail(self):
        """Mock checksum file. This is a file within the repository that contains the checksum
        previously reported string
        """
        return os.path.join(testfiles_dir, "md5checksum_previouslyfailed.txt")

    @pytest.fixture(scope="function")
    def nonexistent_bcl2fastqlog(self):
        """Nonexistent bcl2fastq logfile"""
        return "/path/to/nonexistent/file.log"

    @pytest.fixture(scope="function")
    def internal_chars_invalid(self):
        """Samplesheet containing invalid characters in sample name"""
        return [
            os.path.join(os.getcwd(),
                         "/test/samplesheets/210513_M02631_0236_000000000-JFMNK_SampleSheet.csv")
        ]

    @pytest.fixture(scope="function")
    def perfect_ss(self):
        """Path to perfect samplesheet"""
        return os.path.join(
            os.getcwd(), "test/samplesheets/210408_M02631_0186_000000000-JFMNK_SampleSheet.csv")

    @pytest.fixture(scope="function")
    def ss_with_disallowed_sserrs(
        self,
        empty_file,
        invalid_paths,
        invalid_names,
        invalid_contents,
        internal_chars_invalid,
    ):
        """Samplesheets with disallowed errors in the more stringent set of requirements than the
        base samplesheet validator check. These lists have been imported from the
        test_samplesheet_validator test suite"""
        return list(
            itertools.chain(
                empty_file,
                invalid_paths,
                invalid_names,
                invalid_contents,
                internal_chars_invalid,
            )
        )

    @pytest.fixture(scope="function")
    def demultiplexing_notrequired(self):
        """This test covers all runfolder cases where demultiplexing is not required
        runfolerpath, folder_name, samplesheet_path
        999999_A01229_0000_00000TEST1: Demultiplexing already complete
        999999_A01229_0000_00000TEST2: Sequencing not yet complete
        999999_A01229_0000_00000TEST3: Fatal samplesheet errors (headers missing from data section)
        999999_A01229_0000_00000TEST5: Checksum file absent
        999999_A01229_0000_00000TEST6: Checksums do not match
        999999_A01229_0000_0000TEST10: Samplesheet missing
        """
        return [
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST1"),
                "999999_A01229_0000_00000TEST1",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST1_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST2"),
                "999999_A01229_0000_00000TEST2",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST2_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST3"),
                "999999_A01229_0000_00000TEST3",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST3_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST5"),
                "999999_A01229_0000_00000TEST5",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST5_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST6"),
                "999999_A01229_0000_00000TEST6",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST6_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_0000TEST10"),
                "999999_A01229_0000_0000TEST10",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_0000TEST10_SampleSheet.csv")
            ),
        ]

    @pytest.fixture(scope="function")
    def demultiplexing_required(self):
        """This test covers all runfolder cases where demultiplexing is required
        Both funfolers - sequencing complete, demultipelxing has not yet started
        """
        return [
            (
                os.path.join(temp_runfolderdir, "999999_M02631_0000_00000TEST4"),
                "999999_M02631_0000_00000TEST4",
                os.path.join(temp_samplesheetsdir, "999999_M02631_0000_00000TEST4_SampleSheet.csv")
            ),
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST7"),
                "999999_A01229_0000_00000TEST7",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST7_SampleSheet.csv")
            ),
        ]

    @pytest.fixture(scope="function")
    def tso_runfolder(self):
        """This test covers all runfolder cases where the runfolder is from a tso run
        999999_A01229_0000_00000TEST8: Demultiplexing not yet complete (no demultiplex logfile)
        """
        return [
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST8"),
                "999999_A01229_0000_00000TEST8",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST8_SampleSheet.csv")
            ),
        ]

    @pytest.fixture(scope="function")
    def non_tso_runfolder(self):
        """This test case contains runfolders that are not a tso run"""
        return [
            (
                os.path.join(temp_runfolderdir, "999999_A01229_0000_00000TEST9"),
                "999999_A01229_0000_00000TEST9",
                os.path.join(temp_samplesheetsdir, "999999_A01229_0000_00000TEST9_SampleSheet.csv")
            ),
        ]

    @pytest.mark.parametrize('notrequired', [
        (pytest.lazy_fixture('demultiplexing_notrequired')),
        (pytest.lazy_fixture('tso_runfolder'))])
    def test_demultiplexing_required_false(self, gr_mock, notrequired):  # DONE BUT NEED TO CHECK THIS COVERS ALL CASES
        """Test demultiplexing_required() does not return True for cases where demultiplexing is
        not required"""
        for runfolderpath, folder_name, samplesheet_path in notrequired:
            print("\n" + folder_name + "\n")
            assert not demultiplex.DemultiplexRunfolder(
                samplesheet_path=samplesheet_path,
                runfolderpath=runfolderpath,
                folder_name=folder_name,
                logger=gr_mock.demux_logger
            ).demultiplexing_required()

    def test_demultiplexing_required_true(self, gr_mock, demultiplexing_required):  # DONE BUT NEED TO CHECK THIS COVERS ALL CASES
        """Test demultiplexing_required() returns True for cases where demultiplexing is required"""
        for runfolderpath, folder_name, samplesheet_path in demultiplexing_required:
            assert demultiplex.DemultiplexRunfolder(
                samplesheet_path=samplesheet_path,
                runfolderpath=runfolderpath,
                folder_name=folder_name,
                logger=gr_mock.demux_logger
            ).demultiplexing_required()

    def test_run_demultiplexing_success(self, gr_mock, non_tso_runfolder):
        """Test function correctly identifies tso runfolder and so does not
        call demultiplexing functions"""
        for runfolderpath, folder_name, samplesheet_path in non_tso_runfolder:
            runfolder_obj = demultiplex.DemultiplexRunfolder(
                samplesheet_path=samplesheet_path,
                runfolderpath=runfolderpath,
                folder_name=folder_name,
                logger=gr_mock.demux_logger
            )

            # Command to run in place of bcl2fastq command that appends processing complete
            # string to bcl2fastq logfile
            runfolder_obj.bcl2fastq_cmd = f'echo "Processing completed with 0 errors and 0 " \
                "warnings" >> {runfolder_obj.bcl2fastqlog_path}'

            assert runfolder_obj.run_demultiplexing()
            assert runfolder_obj.run_processed

    def test_valid_samplesheet_pass(self, monkeypatch, dr_mock, valid_samplesheets):  # DONE
        """Test function correctly returns valid flag, using a set of representative 
        samplesheets"""
        for path in valid_samplesheets:
            monkeypatch.setattr(dr_mock, "samplesheet_path", path)
            valid, _ = dr_mock.valid_samplesheet()
            assert valid

    def test_valid_samplesheet_fail(self, monkeypatch, dr_mock, ss_with_disallowed_sserrs):  # DONE
        """Test function fails to return valid flag as expected, using a set of samplesheets
        covering all failure cases"""
        for path in ss_with_disallowed_sserrs:
            monkeypatch.setattr(dr_mock, "samplesheet_path", path)
            valid, _ = dr_mock.valid_samplesheet()
            assert not valid

    def test_bcl2fastqlog_absent_false(self, dr_mock):  # DONE
        """Test function correctly identifies presence of bcl2fastqlogfile using an empty file"""
        assert not dr_mock.bcl2fastqlog_absent()

    def test_bcl2fastqlog_absent_true(self, monkeypatch, dr_mock, nonexistent_bcl2fastqlog):
        """Test function correctly identifies absence of bcl2fastqlogfile log file, using a
        path to a nonexistent file"""
        monkeypatch.setattr(dr_mock, "bcl2fastqlog_path", nonexistent_bcl2fastqlog)
        assert dr_mock.bcl2fastqlog_absent()

    def test_sequencing_complete_pass(self, dr_mock):
        """Test sequencing_complete() can identify presence of rtacomplete file"""
        assert dr_mock.sequencing_complete()

    def test_sequencing_complete_fail(self, monkeypatch, dr_mock):
        """Provide path to nonexistent rtacompletefile"""
        monkeypatch.setattr(dr_mock, "rtacompletefile_path", "/path/to/nonexistent/file.txt")
        assert not dr_mock.sequencing_complete()

    # # THIS IS NOT CURRENTLY FUNCTIONING CORRECTLY
    # def test_no_disallowed_sserrs_pass(self, monkeypatch, dr_mock, perfect_ss):
    #     """Test no_disallowed_sserrs() using a perfect samplesheet"""
    #     monkeypatch.setattr(dr_mock, "samplesheet_path", perfect_ss)
    #     valid, sscheck_obj = self.valid_samplesheet()
    #     assert dr_mock.no_disallowed_sserrs(valid, sscheck_obj)

    # def test_no_disallowed_sserrs_fail(self, monkeypatch, dr_mock, ss_with_disallowed_sserrs):
    #     """Tests function identifies all disallowed ss errors"""
    #     for samplesheet_path in ss_with_disallowed_sserrs:
    #         monkeypatch.setattr(dr_mock, "samplesheet_path", ss_with_disallowed_sserrs)
    #         valid, sscheck_obj = self.valid_samplesheet()
    #         assert not dr_mock.no_disallowed_sserrs(valid, sscheck_obj)

    def test_integritycheck_not_required_fail(self, monkeypatch, dr_mock, icheck_required):
        """Test function correctly detects that runfolder requires an integrity check"""
        monkeypatch.setattr(dr_mock, "runfolder_name", icheck_required)
        assert not dr_mock.integritycheck_not_required()

    def test_integritycheck_not_required_pass(self, monkeypatch, dr_mock, icheck_notrequired):
        """Test function correctly detects that runfolder does not require an integrity check"""
        monkeypatch.setattr(dr_mock, "runfolder_name", icheck_notrequired)
        assert dr_mock.integritycheck_not_required()

    def test_checksumfile_present_pass(self, dr_mock):
        """Test function correctly detects presence of checksum file"""
        assert dr_mock.checksumfile_present()

    def test_checksumfile_present_fail(self, monkeypatch, dr_mock):
        """Test function correctly detects absence of checksum file"""
        monkeypatch.setattr(dr_mock, "checksumfile_path", "abcd")
        assert not dr_mock.checksumfile_present()

    def test_prior_integritycheck_failed_false(self, dr_mock):
        """Test function correctly identifies there have been no
        previously failed integrity checks"""
        assert not dr_mock.prior_integritycheck_failed()

    def test_prior_integritycheck_failed_true(self, monkeypatch,
                                              dr_mock, temp_md5checksum_prevfail):
        """Test function correctly identifies there has been a previously failed
        integrity check"""
        monkeypatch.setattr(dr_mock, "checksumfile_path", temp_md5checksum_prevfail)
        assert dr_mock.prior_integritycheck_failed()

    def test_integrity_check_success_true(self, dr_mock):
        """Test function correctly identifies checksums match.
        Copies file as the function adds a line of text to the file.
        """
        assert dr_mock.integrity_check_success()

    def test_integrity_check_success_false(self, monkeypatch, dr_mock, temp_md5checksum_fail):
        """Test function correctly identifes checksums do not match.
        Copies file as the function adds a line of text to the file."""
        monkeypatch.setattr(dr_mock, "checksumfile_path", temp_md5checksum_fail)
        assert not dr_mock.integrity_check_success()

    def test_create_bcl2fastqlog_success(self, dr_mock):
        """Test function can successfully create a bcl2fastq log file"""
        assert dr_mock.create_bcl2fastqlog()
        assert os.path.isfile(dr_mock.bcl2fastqlog_path)

    def test_add_bcl2fastqlog_tso_msg_success(self, dr_mock):
        """Test function can correctly add tso message to the bcl2fastq2 logfile"""
        assert dr_mock.add_bcl2fastqlog_tso_msg()
        assert os.path.isfile(dr_mock.bcl2fastqlog_path)
        with open(dr_mock.bcl2fastqlog_path, encoding="utf-8") as file:
            assert config.demultiplexing_logfile_tso500_msg in file.read()

    def test_run_subprocess_success(self, dr_mock):
        """Test function successfully executes subprocess"""
        assert dr_mock.run_subprocess("echo `This is a test`")

    # def test_check_bcl2fastqlogfile_success(self, dr_mock):
    #     """Test check_bcl2fastqlogfile returns True for logfiles containing expected succes
    #     message from automate demultiplex config"""
    #     dr_mock.bcl2fastqlog_path = os.path.join(temp_dir, "bcl2fastq2_output_success.log")
    #     assert dr_mock.check_bcl2fastqlogfile()

    def test_check_bcl2fastqlogfile_fail(self, dr_mock, bcl2fastqlog_fail):
        """Test check_bcl2fastqlogfile returns False for logfiles not containing expected success
        message from automate demultiplex config"""
        for logpath in bcl2fastqlog_fail:
            dr_mock.bcl2fastqlog_path = logpath  # Reset path to that from test case
            assert not dr_mock.check_bcl2fastqlogfile()
