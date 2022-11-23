# coding=utf-8
""" demultiplex.py pytest unit tests
"""
import pytest
import datetime
import os
import shutil
from demultiplex import GetRunfolders, DemultiplexRunfolder, Email, Logging
from test.test_samplesheet_validator import base_path, valid_samplesheets, invalid_paths, invalid_names, \
    empty_file, invalid_contents
import itertools

# Variables used across all test classes
datetime_now = datetime.datetime.now()
test_files_dir = "{}/test/demultiplex_test_files/".format(os.getcwd())
temp_dir = "{}temp/".format(test_files_dir)
scriptlog_path = "{}/{}.txt".format(temp_dir, str('{:%Y%m%d_%H%M%S}'.format(datetime_now)))


class TestGetRunfolders(object):
    """ Test GetRunfolders class
    There is no test for the case where demultiplex_runfolders passes runfolders to DemultiplexRunfolder which are
    processed by DemultiplexRunfolder
    This is because the script tries to run bcl2fastq which inevitably fails for the test cases due to the absence of
    any sequencing data in the test cases. This should be tested using real data on the workstation."""

    @classmethod
    def class_attributes(cls):
        cls.temp_dir = temp_dir
        cls.runfolders_path = "{}test_runfolders/".format(cls.temp_dir)
        cls.demultiplex_logfiles = cls.temp_dir
        cls.datetime_now = datetime.datetime.now()
        cls.test_files_dir = test_files_dir
        cls.scriptlog_path = scriptlog_path
        cls.bcl2fastq_path = "{}bcl2fastq".format(test_files_dir)

    @pytest.fixture
    def gr_obj(cls):
        """ Create DemultiplexRunfolder object to use in tests
        """
        gr_obj = GetRunfolders(runfolders_path=cls.runfolders_path, demultiplex_logfiles=cls.demultiplex_logfiles,
                               datetime_now=cls.datetime_now, bcl2fastq_path=cls.bcl2fastq_path)
        return gr_obj

    @pytest.fixture
    def processed_runfolders(cls):
        # String of 4 processed runfolders
        return ['these', 'are', 'processed', 'runfolders']

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(cls):
        """Fixture to execute asserts before and after a test is run - resets class variables and removes tem
        dirs"""
        # SETUP -
        cls.class_attributes()  # Get class attributes
        # Copy all test files across to a temporary dir for testing
        shutil.copytree(cls.test_files_dir, cls.temp_dir)
        yield  # Where the testing happens
        # TEARDOWN - cleanup after each test
        if os.path.isdir(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

    def test_rundemultiplexrunfolders(cls):
        """ Pass set of dummy runfolders to the test and assert that the expected number are processed.
        processed_runfolders should be empty as the script tries to run bcl2fastq so inevitably fails for all runfolders
        due to absence of sequencing data in test cases"""
        gr_obj = GetRunfolders(runfolders_path=cls.runfolders_path, demultiplex_logfiles=cls.demultiplex_logfiles,
                               datetime_now=cls.datetime_now)
        processed_runfolders = gr_obj.run_demultiplexrunfolders()
        assert not processed_runfolders

    def test_bcl2fastq_installed_pass(cls, gr_obj):
        """ Check bcl2fastq_install function is working using functional test bcl2fastq executable"""
        assert gr_obj.bcl2fastq_installed()

    def test_bcl2fastq_installed_fail(cls, gr_obj):
        """ Provide incorrect bcl2fastq path """
        gr_obj.bcl2fastq_path = "/path/does/not/exist/bcl2fastq"
        assert not gr_obj.bcl2fastq_installed()

    def test_rename_demultiplex_logfile(cls, gr_obj, processed_runfolders):
        """ Tests that script logfile is renamed if there are processed runfolders"""
        assert gr_obj.rename_demultiplex_logfile(processed_runfolders)
        assert all(name in gr_obj.scriptlog_path for name in processed_runfolders)


class TestDemultiplexRunfolder(object):
    """ Test DemultiplexRunfolder class """

    @classmethod
    def class_attributes(cls):
        cls.temp_dir = temp_dir
        cls.temp_runfolderdir = "{}test_runfolders/".format(cls.temp_dir)
        cls.md5checksum_pass = "{}md5checksum_pass.txt".format(cls.temp_dir)
        cls.md5checksum_fail = "{}md5checksum_fail.txt".format(cls.temp_dir)
        cls.bcl2fastqlog_path = "{}bcl2fastq2_output.log".format(cls.temp_dir)

        cls.test_runfolder = ''
        cls.test_files_dir = test_files_dir
        cls.scriptlog_path = scriptlog_path
        cls.samplesheet_path = ''.format(os.getcwd())
        cls.md5checksum_prevfail = "{}md5checksum_previouslyfailed.txt".format(cls.test_files_dir)

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(cls):
        """Fixture to execute asserts before and after a test is run - resets class variables and removes tem
        dirs"""
        # SETUP -
        cls.class_attributes()  # Get class attributes
        # Copy all test files across to a temporary dir for testing
        shutil.copytree(cls.test_files_dir, cls.temp_dir)
        yield  # Where the testing happens
        # TEARDOWN - cleanup after each test
        if os.path.isdir(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

    @pytest.fixture
    def dr_obj(cls):
        """ Create DemultiplexRunfolder object to use in tests
        """
        dr = DemultiplexRunfolder(cls.scriptlog_path, cls.samplesheet_path, cls.test_files_dir, cls.test_runfolder)
        dr.bcl2fastqlog_path = cls.bcl2fastqlog_path
        dr.bcl2fastq_path = "{}bcl2fastq".format(cls.test_files_dir)  # Path to functioning test bcl2fastq executable

        dr.runfolder_name = ''
        dr.runfolderpath = ''
        dr.email_subject = "string"
        dr.email_message = "Please ignore this email. This is a demultiplex.py unit test"
        return dr

    @pytest.fixture
    def bcl2fastqlog_fail(cls):
        """ Logfiles containing bcl2fastq pass and fail messages """
        return [
            ("{}bcl2fastq2_output_nomsg.log".format(cls.test_files_dir)),  # No success message present in logfile
            'nonexistent.log',  # Logfile nonexistent
            ("{}bcl2fastq2_output_empty.log".format(cls.test_files_dir)),  # Logfile empty
        ]

    @pytest.fixture
    def icheck_required(cls):
        """Runfolder that would require an integrity check """
        return "999999_NB551068_0009_AH3YERAFX3"

    @pytest.fixture
    def icheck_notrequired(cls):
        """Runfolder that would not require an integrity check """
        return "999999_M02353_0641_000000000-TESTS"

    @pytest.fixture
    def nonexistent_bcl2fastqlog(cls):
        """Nonexistent bcl2fastq logfile """
        return "/path/to/nonexistent/file.log"

    @pytest.fixture
    def internal_chars_invalid(cls):
        return ['{}/test/samplesheets/210513_M02631_0236_000000000-JFMNK_SampleSheet.csv'.format(os.getcwd())]

    @pytest.fixture
    def ss_with_disallowed_sserrs(cls, empty_file, invalid_paths, invalid_names,
                                  invalid_contents, internal_chars_invalid):
        """ Samplesheets with disallowed errors in the more stringent set of requirements than the base samplesheet
        validator check. These lists have been imported from the test_samplesheet_validator test suite"""
        return list(itertools.chain(empty_file, invalid_paths, invalid_names, invalid_contents,
                                    internal_chars_invalid))

    @pytest.fixture
    def demultiplexing_notrequired(cls):
        """ This test covers all runfolder cases where demultiplexing is not required
        runfolerpath, folder_name, samplesheet_path
        """
        return [
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST1'), '999999_A01229_0000_00000TEST1',
             "{}samplesheets/999999_A01229_0000_00000TEST1_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST2'), '999999_A01229_0000_00000TEST2',
             "{}samplesheets/999999_A01229_0000_00000TEST2_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST3'), '999999_A01229_0000_00000TEST3',
             "{}samplesheets/999999_A01229_0000_00000TEST3_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST5'), '999999_A01229_0000_00000TEST5',
             "{}samplesheets/999999_A01229_0000_00000TEST5_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST6'), '999999_A01229_0000_00000TEST6',
             "{}samplesheets/999999_A01229_0000_00000TEST6_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_0000TEST10'), '999999_A01229_0000_0000TEST10',
             "{}samplesheets/999999_A01229_0000_0000TEST10_SampleSheet.csv".format(cls.temp_runfolderdir)),
        ]

    @pytest.fixture
    def demultiplexing_required(cls):
        """ This test covers all runfolder cases where demultiplexing is required
        """
        return [
            ("{}{}".format(cls.temp_runfolderdir, '999999_M02631_0000_00000TEST4'), '999999_M02631_0000_00000TEST4',
             "{}samplesheets/999999_M02631_0000_00000TEST4_SampleSheet.csv".format(cls.temp_runfolderdir)),
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST7'), '999999_A01229_0000_00000TEST7',
             "{}samplesheets/999999_A01229_0000_00000TEST7_SampleSheet.csv".format(cls.temp_runfolderdir)),
        ]

    @pytest.fixture
    def tso_runfolder(cls):
        """ This test covers all runfolder cases where the runfolder is from a tso run
        """
        return [
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST8'), '999999_A01229_0000_00000TEST8',
             "{}samplesheets/999999_A01229_0000_00000TEST8_SampleSheet.csv".format(cls.temp_runfolderdir)),
        ]

    @pytest.fixture
    def non_tso_runfolder(cls):
        """ This test case contains runfolders that are not a tso run """
        return [
            ("{}{}".format(cls.temp_runfolderdir, '999999_A01229_0000_00000TEST9'), '999999_A01229_0000_00000TEST9',
             "{}samplesheets/999999_A01229_0000_00000TEST9_SampleSheet.csv".format(cls.temp_runfolderdir)),
        ]

    def test_run_demultiplexing_tso_valid(cls, tso_runfolder):
        for runfolderpath, folder_name, samplesheet_path in tso_runfolder:
            runfolder_obj = DemultiplexRunfolder(scriptlog_path=cls.scriptlog_path, samplesheet_path=samplesheet_path,
                                                 runfolderpath=runfolderpath, folder_name=folder_name)

            assert not runfolder_obj.run_demultiplexing()  # TSO runs are not demultiplexed
            assert runfolder_obj.run_processed

    def test_run_demultiplexing_tso_invalid(cls, non_tso_runfolder):
        for runfolderpath, folder_name, samplesheet_path in non_tso_runfolder:
            runfolder_obj = DemultiplexRunfolder(scriptlog_path=cls.scriptlog_path, samplesheet_path=samplesheet_path,
                                                 runfolderpath=runfolderpath, folder_name=folder_name)

            # Command to run in place of bcl2fastq command that appends processing complete string to bcl2fastq logfile
            runfolder_obj.bcl2fastq_cmd = 'echo "Processing completed with 0 " \
                                          "errors and 0 warnings" >> {}'.format(runfolder_obj.bcl2fastqlog_path)

            assert runfolder_obj.run_demultiplexing()
            assert runfolder_obj.run_processed

    def test_demultiplexing_required_false(cls, demultiplexing_notrequired):
        """ Test demultiplexing_required() does not return True for cases where demultiplexing is not required"""
        for runfolderpath, folder_name, samplesheet_path in demultiplexing_notrequired:
            assert not DemultiplexRunfolder(scriptlog_path=cls.scriptlog_path, samplesheet_path=samplesheet_path,
                                            runfolderpath=runfolderpath,
                                            folder_name=folder_name).demultiplexing_required()

    def test_demultiplexing_required_true(cls, demultiplexing_required):
        """ Test demultiplexing_required() returns True for cases where demultiplexing is required"""
        for runfolderpath, folder_name, samplesheet_path in demultiplexing_required:
            assert DemultiplexRunfolder(scriptlog_path=cls.scriptlog_path, samplesheet_path=samplesheet_path,
                                        runfolderpath=runfolderpath, folder_name=folder_name).demultiplexing_required()

    def test_valid_samplesheet_pass(cls, dr_obj, valid_samplesheets):
        for path in valid_samplesheets:
            dr_obj.samplesheet_path = path
            valid, sscheck_obj = dr_obj.valid_samplesheet()
            assert valid

    def test_valid_samplesheet_fail(cls, dr_obj, ss_with_disallowed_sserrs):
        for path in ss_with_disallowed_sserrs:
            dr_obj.samplesheet_path = path
            valid, sscheck_obj = dr_obj.valid_samplesheet()
            assert not valid

    def test_bcl2fastqlog_absent_false(cls, dr_obj):
        """ Test function that checks if bcl2fastqlogfile is present using an empty file"""
        open(cls.bcl2fastqlog_path, 'w').close()
        assert not dr_obj.bcl2fastqlog_absent()

    def test_bcl2fastqlog_absent_true(cls, dr_obj, nonexistent_bcl2fastqlog):
        dr_obj.bcl2fastqlog_path = nonexistent_bcl2fastqlog
        assert dr_obj.bcl2fastqlog_absent()

    def test_sequencing_complete_pass(cls, dr_obj):
        """ Test sequencing_complete() can identify presence of rtacomplete file"""
        dr_obj.rtacompletefile_path = "{}RTAComplete.txt".format(cls.test_files_dir)
        assert dr_obj.sequencing_complete()

    def test_sequencing_complete_fail(cls, dr_obj):
        """ Provide path to nonexistent rtacompletefile """
        dr_obj.rtacompletefile_path = "/path/to/nonexistent/file.txt"
        assert not dr_obj.sequencing_complete()

    def test_no_disallowed_sserrs_pass(cls, dr_obj):
        """ Test no_disallowed_sserrs() using a perfect samplesheet"""
        ss_path = "{}/test/samplesheets/210408_M02631_0186_000000000-JFMNK_SampleSheet.csv".format(os.getcwd())
        dr_obj.samplesheet_path = ss_path
        assert dr_obj.no_disallowed_sserrs()

    def test_no_disallowed_sserrs_fail(cls, dr_obj, ss_with_disallowed_sserrs):
        """ Tests function identifies all disallowed ss errors"""
        for samplesheet_path in ss_with_disallowed_sserrs:
            dr_obj.samplesheet_path = samplesheet_path
            assert not dr_obj.no_disallowed_sserrs()

    def test_integritycheck_not_required_fail(cls, dr_obj, icheck_required):
        dr_obj.runfolder_name = icheck_required
        assert not dr_obj.integritycheck_not_required()

    def test_integritycheck_not_required_pass(cls, dr_obj, icheck_notrequired):
        dr_obj.runfolder_name = icheck_notrequired
        assert dr_obj.integritycheck_not_required()

    def test_checksumfile_present_pass(cls, dr_obj):
        dr_obj.checksumfile_path = cls.md5checksum_pass
        assert dr_obj.checksumfile_present()

    def test_checksumfile_present_fail(cls, dr_obj):
        dr_obj.checksumfile_path = "abcd"
        assert not dr_obj.checksumfile_present()

    def test_prior_integritycheck_failed_false(cls, dr_obj):
        dr_obj.checksumfile_path = cls.md5checksum_pass
        assert not dr_obj.prior_integritycheck_failed()

    def test_prior_integritycheck_failed_true(cls, dr_obj):
        dr_obj.checksumfile_path = cls.md5checksum_prevfail
        assert dr_obj.prior_integritycheck_failed()

    def test_integrity_check_success_true(cls, dr_obj):
        """ Test function determining whether checksums match.
        Copies file as the function adds a line of text to the file.
        """
        dr_obj.checksumfile_path = cls.md5checksum_pass
        assert dr_obj.integrity_check_success()

    def test_integrity_check_success_false(cls, dr_obj):
        """ Test function determining whether checksums match.
        Copies file as the function adds a line of text to the file."""
        dr_obj.checksumfile_path = cls.md5checksum_fail
        assert not dr_obj.integrity_check_success()

    def test_create_bcl2fastqlog_success(cls, dr_obj):
        assert dr_obj.create_bcl2fastqlog()
        assert os.path.isfile(dr_obj.bcl2fastqlog_path)

    def test_add_bcl2fastqlog_tso_msg_success(cls, dr_obj):
        """ Checks function can correctly add tso message to the bcl2fastq2 logfile """
        assert dr_obj.add_bcl2fastqlog_tso_msg()
        assert os.path.isfile(dr_obj.bcl2fastqlog_path)
        with open(dr_obj.bcl2fastqlog_path) as f:
            assert dr_obj.tso500_bcl2fastq_msg in f.read()

    def test_run_subprocess_success(cls, dr_obj):
        """ Test subprocess is successfully executed"""
        assert dr_obj.run_subprocess("echo `This is a test`")

    def test_check_bcl2fastqlogfile_success(cls, dr_obj):
        """ Test check_bcl2fastqlogfile returns True for logfiles containing expected success message from
        cautomate demultiplex config """
        dr_obj.bcl2fastqlog_path = "{}bcl2fastq2_output_success.log".format(cls.temp_dir)
        assert dr_obj.check_bcl2fastqlogfile()

    def test_check_bcl2fastqlogfile_fail(cls, dr_obj, bcl2fastqlog_fail):
        """ Test check_bcl2fastqlogfile returns False for logfiles not containing expected success message from
        cautomate demultiplex config """
        for logpath in bcl2fastqlog_fail:
            dr_obj.bcl2fastqlog_path = logpath  # Reset path to that from test case
            assert not dr_obj.check_bcl2fastqlogfile()


class TestEmail():
    """ Test Email class """
    @classmethod
    def class_attributes(cls):
        cls.email_subject = "DEMULTIPLEX TEST - PLEASE IGNORE"
        cls.email_message = "Please ignore this email. This is a demultiplex.py unit test"
        cls.scriptlog_path = scriptlog_path
        cls.temp_dir = temp_dir

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(cls):
        """Fixture to execute asserts before and after a test is run - resets class variables and removes tem
        dirs"""
        # SETUP -
        cls.class_attributes()  # Get class attributes
        cls.temp_dir = temp_dir
        os.makedirs(cls.temp_dir)  # Create temp dir for script to create file in. Removed by teardown class
        yield  # Where the testing happens
        # TEARDOWN - cleanup after each test
        if os.path.isdir(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

    def test_send_email_success(cls):
        email_obj = Email(cls.scriptlog_path, cls.email_subject, cls.email_message)
        assert email_obj.send_email()

    def test_send_email_fail(cls):
        """Test email sending failure - incorrect credentials provided
        """
        email_obj = Email(cls.scriptlog_path, cls.email_subject, cls.email_message)
        email_obj.user = "abc"
        assert not email_obj.send_email()


class TestLogging():
    """ Test Logging class """
    @classmethod
    def class_attributes(cls):
        cls.scriptlog_path = scriptlog_path
        cls.temp_dir = temp_dir

    @pytest.fixture
    def logger(cls):
        logger = Logging(cls.scriptlog_path).logger
        return logger

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(cls):
        """Fixture to execute asserts before and after a test is run - resets class variables and removes tem
        dirs"""
        # SETUP -
        cls.class_attributes()  # Get class attributes
        os.makedirs(cls.temp_dir)  # Create temp dir for script to create file in. Removed by teardown class
        open(cls.scriptlog_path, 'w').close()  # Create test scriptlog file
        yield  # Where the testing happens
        # TEARDOWN - cleanup after each test
        if os.path.isdir(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

    @pytest.fixture
    def expected_message(cls):
        return 'demultiplextest_info - INFO - Logging test string'

    def test_logger_pass(cls, logger, expected_message):
        """Check expected strings written to logfile. This means writing to syslog was also successful"""
        logger.info("Logging test string", extra={'flag': 'demultiplextest_info'})
        with open(cls.scriptlog_path) as f:
            assert expected_message in f.read()
