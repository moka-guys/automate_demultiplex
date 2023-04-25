# coding=utf-8
"""
demultiplex.py pytest unit tests

N.B. test_bcl2fastq_installed_pass() will only pass when the testing is being
carried out on the workstation
"""
import os
import shutil
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
import demultiplex
import ad_config as config  # Import config file

# Variables used across test classes

# Path of directory containing test files
testfiles_dir = os.path.abspath("test/demultiplex_test_files/")
# Temporary directory to copy test files into and to contain outputs
temp_dir = os.path.join(testfiles_dir, "temp/")
temp_runfolderdir = os.path.join(temp_dir, "test_runfolders/")

samplesheet_path = os.path.join(
    temp_runfolderdir, "samplesheets", "%s_SampleSheet.csv"
)


@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """
    Setup and teardown before and after each test. Copy all files over to a
    temporary directory before each test is run. Removes temporary directory
    (containing temporary test files and created flag files) after testing
    complete
    """
    monkeypatch.setattr(demultiplex.config, "RUNFOLDERS", temp_runfolderdir)

    monkeypatch.setattr(
        demultiplex.ad_logger.config, "RUNFOLDERS", temp_runfolderdir
    )
    monkeypatch.setattr(config, "DEMULTIPLEX_LOGPATH", temp_dir)
    monkeypatch.setattr(
        demultiplex.ad_logger.config, "DEMULTIPLEX_LOGPATH", temp_dir
    )

    monkeypatch.setattr(config, "SAMPLESHEET_PATH", samplesheet_path)

    shutil.copytree(testfiles_dir, temp_dir)
    yield  # Where the testing happens
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)


class TestGetRunfolders(object):
    """
    Test GetRunfolders class - UPDATE THIS
    There is no test for the case where demultiplex_runfolders passes
    runfolders to DemultiplexRunfolder which are processed by
    DemultiplexRunfolder. This is because the script tries to run bcl2fastq
    which inevitably fails for the test cases due to the absence of any
    sequencing data in the test cases. This should be tested using real data
    on the workstation
    """

    @pytest.fixture(scope="function")
    def processed_runfolders(self):
        """
        String of 4 dummy processed runfolders
        """
        return ['these", "are", "processed", "runfolders']

    @pytest.fixture(scope="function")
    def no_processed_runfolders(self):
        """
        Empty list, i.e. no runfolders were processed
        """
        return []

    @pytest.fixture(scope="function")
    def runfolders_toproc(self):
        """
        List of runfolders requiring processing
        """
        return [
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST9",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def runfolders_nottoproc(self):
        """
        List of runfolders that do not require processing
        """
        return [
            "999999_A01229_0000_00000TEST1",
            "999999_A01229_0000_00000TEST2",
            "999999_A01229_0000_00000TEST3",
            "999999_A01229_0000_00000TEST5",
            "999999_A01229_0000_00000TEST6",
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_00000TEST8",
            "999999_A01229_0000_0000TEST10",
        ]

    def test_demultiplex_runfolders_toproc(
        self, monkeypatch, runfolders_toproc
    ):
        """
        Pass set of runfolders expected to be successfully processed by script.
        Assert that the expected number are processed
        """
        monkeypatch.setattr(config, "BCL2FASTQ", os.path.join("/bin/true"))
        gr_obj = demultiplex.GetRunfolders()
        monkeypatch.setattr(gr_obj, "runfolder_names", runfolders_toproc)
        assert all(
            runfolders in runfolders_toproc
            for runfolders in gr_obj.demultiplex_runfolders()
        )

    def test_demultiplex_runfolders_nottoproc(
        self, monkeypatch, runfolders_nottoproc
    ):
        """
        Pass set of runfolders that shouldnt be processed for various reasons.
        Assert that none have been processed
        """
        gr_obj = demultiplex.GetRunfolders()
        monkeypatch.setattr(gr_obj, "runfolder_names", runfolders_nottoproc)
        assert not gr_obj.demultiplex_runfolders()

    def test_bcl2fastq_installed_pass(self):
        """
        Check bcl2fastq_install function is working using blc2fastq path.
        This is expected to fail if tests are being carried out on a machine
        other than the workstation
        """
        assert demultiplex.GetRunfolders().bcl2fastq_installed()

    def test_bcl2fastq_installed_dummy_pass(self, monkeypatch):
        """
        Check bcl2fastq_install function is working using /bin/true instead
        of bcl2fastq executable (in case bcl2fastq is not functional on the
        machine in use)
        """
        monkeypatch.setattr(config, "BCL2FASTQ", os.path.join("/bin/true"))
        assert demultiplex.GetRunfolders().bcl2fastq_installed()

    def test_bcl2fastq_installed_fail(self, monkeypatch):
        """
        Provide incorrect bcl2fastq path
        """
        monkeypatch.setattr(
            config, "BCL2FASTQ", "/path/to/nonexistent/bcl2fastq"
        )
        assert not demultiplex.GetRunfolders().bcl2fastq_installed()

    def test_get_new_logfilename_processed(self, processed_runfolders):
        """
        Test function returns logfile name containing processed runfolders
        """
        gr_obj = demultiplex.GetRunfolders()
        assert all(
            name in gr_obj.get_new_logfilename(processed_runfolders)
            for name in processed_runfolders
        )

    def test_get_new_logfilename_noneprocessed(self, no_processed_runfolders):
        """
        Test function returns None logfile name when no runfolders processed
        """
        gr_obj = demultiplex.GetRunfolders()
        assert not gr_obj.get_new_logfilename(no_processed_runfolders)

    def test_rename_demultiplex_logfile_renamed(self):
        """
        Tests that script logfile is renamed if there are processed runfolders
        Create the file ready for function to rename
        """
        gr_obj = demultiplex.GetRunfolders()
        old_logfile_name = gr_obj.log_config["demultiplex"]
        new_logfile_name = f"{old_logfile_name}_addedtext"
        open(
            gr_obj.log_config["demultiplex"], "w", encoding="utf-8"
        ).close()  # Create logfile
        assert gr_obj.rename_demultiplex_logfile(new_logfile_name)
        assert os.path.exists(new_logfile_name)

    def test_rename_demultiplex_logfile_notrenamed(self):
        """
        Test exception raised if logfile cannot be renamed, by using a
        nonexistent logfile
        """
        gr_obj = demultiplex.GetRunfolders()
        old_logfile_name = gr_obj.log_config["demultiplex"]
        new_logfile_name = f"/nonexistent/path/{old_logfile_name}_addedtext"
        assert not gr_obj.rename_demultiplex_logfile(new_logfile_name)
        assert not os.path.exists(new_logfile_name)
        with open(
            gr_obj.log_config["demultiplex"], "r", encoding="utf-8"
        ) as logfile:
            assert "Demultiplex logfile rename failed" in logfile.read()

    def test_get_new_logger_pass(self):
        """
        Test function successfully creates new logger
        """
        gr_obj = demultiplex.GetRunfolders()
        old_logfile_name = gr_obj.log_config["demultiplex"]
        new_logfile_name = f"{old_logfile_name}_addedtext"
        gr_obj.get_new_logger(new_logfile_name)
        assert gr_obj.log_config["demultiplex"] == new_logfile_name
        assert gr_obj.loggers.demultiplex.filepath == new_logfile_name


class TestDemultiplexRunfolder(object):
    """
    Test DemultiplexRunfolder class
    """

    @pytest.fixture(scope="function")
    def bcl2fastqlog_fail(self):
        """
        Logfiles not containing expected success message from automate
        demultiplex config
        """
        return [
            (
                os.path.join(testfiles_dir, "bcl2fastq2_output_nomsg.log")
            ),  # No success message present in logfile
            ("nonexistent.log"),  # Logfile nonexistent
            (
                os.path.join(testfiles_dir, "bcl2fastq2_output_empty.log")
            ),  # Logfile empty
        ]

    @pytest.fixture(scope="function")
    def bcl2fastqlog_pass(self):
        """
        Logfiles containing expected success message from automate demultiplex
        config
        """
        return os.path.join(temp_dir, "bcl2fastq2_output_success.log")

    @pytest.fixture(scope="function")
    def icheck_required(self):
        """
        Runfolder that would require an integrity check
        """
        return ["999999_NB551068_0009_AH3YERAFX3"]

    @pytest.fixture(scope="function")
    def icheck_notrequired(self):
        """
        Runfolder that would not require an integrity check
        """
        return ["999999_M02353_0641_000000000-TESTS"]

    @pytest.fixture(scope="function")
    def internal_chars_invalid(self):
        """
        Samplesheet containing invalid characters in sample name
        """
        return [
            os.path.join(
                os.getcwd(),
                (
                    "/test/samplesheets/"
                    "210513_M02631_0236_000000000-JFMNK_SampleSheet.csv"
                ),
            )
        ]

    @pytest.fixture(scope="function")
    def perfect_ss(self):
        """
        Path to perfect samplesheet
        """
        return os.path.join(
            os.getcwd(),
            (
                "test/samplesheets/"
                "210408_M02631_0186_000000000-JFMNK_SampleSheet.csv"
            ),
        )

    @pytest.fixture(scope="function")
    def ss_with_disallowed_sserrs(
        self,
        empty_file,
        invalid_paths,
        invalid_names,
        invalid_contents,
        internal_chars_invalid,
    ):
        """
        Samplesheets with disallowed errors in the more stringent set of
        requirements than the base samplesheet validator check. These lists
        have been imported from the test_samplesheet_validator test suite
        """
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
    def demultiplexing_required(self):
        """
        Return runfolders where demultiplexing is required. Both runfolers -
        sequencing complete, demultiplexing has not yet started
        """
        return [
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST7",
        ]

    @pytest.fixture(scope="function")
    def demultiplexing_notrequired(self):
        """
        This test covers all runfolder cases where demultiplexing is not
        required runfolerpath, folder_name, samplesheet_path
        """
        return [
            # Demultiplexing already complete
            "999999_A01229_0000_00000TEST1",
            # Sequencing not yet complete
            "999999_A01229_0000_00000TEST2",
            # Fatal samplesheet errors (headers missing from data section)
            "999999_A01229_0000_00000TEST3",
            # Checksum file absent
            "999999_A01229_0000_00000TEST5",
            # Checksums do not match
            "999999_A01229_0000_00000TEST6",
            # TSO run
            "999999_A01229_0000_00000TEST8",
            # Samplesheet missing
            "999999_A01229_0000_0000TEST10",
            # TSO500 run
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def rf_with_bcl2fastqlog(self):
        """
        Return runfolders with bcl2fastqlog present
        """
        return ["999999_A01229_0000_00000TEST1"]

    @pytest.fixture(scope="function")
    def rf_no_bcl2fastqlog(self):
        """
        Return reunfolders with absetnt bcl2fastqlog
        """
        return [
            "999999_A01229_0000_00000TEST2",
            "999999_A01229_0000_00000TEST3",
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST5",
            "999999_A01229_0000_00000TEST6",
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_00000TEST8",
            "999999_A01229_0000_00000TEST9",
            "999999_A01229_0000_0000TEST10",
        ]

    @pytest.fixture(scope="function")
    def rtacomplete_present(self):
        """
        Return runfolders containing RTAcomplete file
        """
        return [
            "999999_A01229_0000_00000TEST3",
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST5",
            "999999_A01229_0000_00000TEST6",
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_0000TEST10",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def rtacomplete_absent(self):
        """
        Return runfolders with no rtacomplete file
        """
        return [
            "999999_A01229_0000_00000TEST1",
            "999999_A01229_0000_00000TEST2",
        ]

    @pytest.fixture(scope="function")
    def checksumfile_present_pass_checked(self):
        """
        Return runfolders containing checksumfile containing matching
        checksums, a pass message, and a previous checksum check message
        """
        return ["999999_A01229_0000_0000TEST10"]

    @pytest.fixture(scope="function")
    def checksumfile_present_fail_notchecked(self):
        """
        Return runfolders containing checksumfile containing non-matching
        checksums, a failure message and no previous checksum check message
        """
        return ["999999_A01229_0000_00000TEST6"]

    @pytest.fixture(scope="function")
    def checksumfile_present_pass_notchecked(self):
        """
        Return runfolders containing checksumfile containing matching
        checksums, a checksum pass message, and no previous checksum check
        message
        """
        return [
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def checksumfile_absent(self):
        """
        Return runfolders with no checksum file
        """
        return [
            "999999_A01229_0000_00000TEST1",
            "999999_A01229_0000_00000TEST2",
            "999999_A01229_0000_00000TEST3",
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST5",
            "999999_A01229_0000_00000TEST8",
            "999999_A01229_0000_00000TEST9",
        ]

    @pytest.fixture(scope="function")
    def tso_runfolder(self):
        """
        This test covers all runfolder cases where the runfolder is from a tso
        run
        """
        return [
            "999999_A01229_0000_00000TEST8",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def non_tso_runfolder(self):
        """
        This test case contains runfolders requiring demultiplexing that are
        not a tso run
        """
        return [
            "999999_A01229_0000_00000TEST9",
            "999999_A01229_0000_00000TEST7",
        ]

    def test_setoff_workflow_success(
        self, monkeypatch, demultiplexing_required
    ):
        """
        Test that function sets off run processing correctly for runfolders
        that require it
        """
        monkeypatch.setattr(
            config, "BCL2FASTQ", f"echo '{config.DEMULTIPLEX_SUCCESS_REGEX}'"
        )
        for folder in demultiplexing_required:
            dr_obj = demultiplex.DemultiplexRunfolder(folder)
            monkeypatch.setattr(dr_obj, "bcl2fastq_cmd", "echo 'true'")
            assert dr_obj.setoff_workflow()

    def test_setoff_workflow_fail(self, demultiplexing_notrequired):
        """
        Test that function correctly does not process runfolders that do not
        need processing
        """
        for folder in demultiplexing_notrequired:
            assert not demultiplex.DemultiplexRunfolder(
                folder
            ).setoff_workflow()

    def test_demultiplexing_required_true(self, demultiplexing_required):
        """
        Test demultiplexing_required() returns True when demultiplexing
        required
        """
        for folder_name in demultiplexing_required:
            assert demultiplex.DemultiplexRunfolder(
                folder_name
            ).demultiplexing_required()

    def test_demultiplexing_required_false(self, demultiplexing_notrequired):
        """
        Test demultiplexing_required() returns none when demultiplexing not
        required
        """
        for folder_name in demultiplexing_notrequired:
            print(demultiplex.DemultiplexRunfolder(folder_name).loggers)
            assert not demultiplex.DemultiplexRunfolder(
                folder_name
            ).demultiplexing_required()

    def test_bcl2fastqlog_absent_false(self, rf_with_bcl2fastqlog):
        """
        Test function correctly identifies presence of bcl2fastqlogfile using
        an empty file
        """
        for runfolder in rf_with_bcl2fastqlog:
            assert not demultiplex.DemultiplexRunfolder(
                runfolder
            ).bcl2fastqlog_absent()

    def test_bcl2fastqlog_absent_true(self, rf_no_bcl2fastqlog):
        """
        Test function correctly identifies absence of bcl2fastqlogfile log
        file, using a path to a nonexistent file
        """
        for runfolder in rf_no_bcl2fastqlog:
            dr_obj = demultiplex.DemultiplexRunfolder(runfolder)
            assert dr_obj.bcl2fastqlog_absent()

    def test_valid_samplesheet_pass(self, monkeypatch, valid_samplesheets):
        """
        Test function correctly returns valid flag, using a set of
        representative samplesheets
        """
        for path in valid_samplesheets:
            dr_obj = demultiplex.DemultiplexRunfolder("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", path)
            valid, _ = dr_obj.valid_samplesheet()
            assert valid

    def test_valid_samplesheet_fail(
        self, monkeypatch, ss_with_disallowed_sserrs
    ):
        """
        Test function fails to return valid flag as expected, using a set of
        samplesheets covering all failure cases
        """
        for path in ss_with_disallowed_sserrs:
            dr_obj = demultiplex.DemultiplexRunfolder("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", path)
            valid, _ = dr_obj.valid_samplesheet()
            assert not valid

    def test_sequencing_complete_pass(self, rtacomplete_present):
        """
        Test sequencing_complete() can identify presence of rtacomplete file
        """
        for runfolder in rtacomplete_present:
            assert demultiplex.DemultiplexRunfolder(
                runfolder
            ).sequencing_complete()

    def test_sequencing_complete_fail(self, rtacomplete_absent):
        """
        Provide path to nonexistent rtacompletefile
        """
        for runfolder in rtacomplete_absent:
            assert not demultiplex.DemultiplexRunfolder(
                runfolder
            ).sequencing_complete()

    def test_no_disallowed_sserrs_pass(self, monkeypatch, perfect_ss):
        """
        Test no_disallowed_sserrs() using a perfect samplesheet
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", perfect_ss)
        valid, sscheck_obj = dr_obj.valid_samplesheet()
        assert dr_obj.no_disallowed_sserrs(valid, sscheck_obj)

    def test_no_disallowed_sserrs_fail(
        self, monkeypatch, ss_with_disallowed_sserrs
    ):
        """
        Tests function identifies all disallowed ss errors
        """
        for path in ss_with_disallowed_sserrs:
            dr_obj = demultiplex.DemultiplexRunfolder("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", path)
            valid, sscheck_obj = dr_obj.valid_samplesheet()
            assert not dr_obj.no_disallowed_sserrs(valid, sscheck_obj)

    def test_seq_requires_no_ic_pass(self, icheck_notrequired):
        """
        Test function correctly detects that runfolder does not require an
        integrity check
        """
        assert demultiplex.DemultiplexRunfolder(
            icheck_notrequired
        ).seq_requires_no_ic()

    def test_seq_requires_no_ic_fail(self, icheck_required):
        """
        Test function correctly detects that runfolder requires an integrity
        check
        """
        assert not demultiplex.DemultiplexRunfolder(
            icheck_required
        ).seq_requires_no_ic()

    @pytest.mark.parametrize(
        "no_prior_ic",
        [
            (pytest.lazy_fixture("checksumfile_present_pass_notchecked")),
            (pytest.lazy_fixture("checksumfile_present_fail_notchecked")),
        ],
    )
    def test_no_prior_ic_pass(self, no_prior_ic):
        """
        Test function correctly identifies there has been a prior integrity
        check
        """
        for runfolder in no_prior_ic:
            assert demultiplex.DemultiplexRunfolder(runfolder).no_prior_ic()

    def test_no_prior_ic_fail(self, checksumfile_present_pass_checked):
        """
        Test function correctly identifies checksums have been assessed by
        the script previously
        """
        for runfolder in checksumfile_present_pass_checked:
            assert not demultiplex.DemultiplexRunfolder(
                runfolder
            ).no_prior_ic()

    @pytest.mark.parametrize(
        "checksumfile_present",
        [
            (pytest.lazy_fixture("checksumfile_present_fail_notchecked")),
            (pytest.lazy_fixture("checksumfile_present_pass_notchecked")),
            (pytest.lazy_fixture("checksumfile_present_pass_checked")),
        ],
    )
    def test_checksumfile_present_pass(self, checksumfile_present):
        """
        Test function correctly detects presence of checksum file
        """
        for runfolder in checksumfile_present:
            assert demultiplex.DemultiplexRunfolder(
                runfolder
            ).checksumfile_present()

    def test_checksumfile_present_fail(self, checksumfile_absent):
        """
        Test function correctly detects absence of checksum file
        """
        for runfolder in checksumfile_absent:
            assert not demultiplex.DemultiplexRunfolder(
                runfolder
            ).checksumfile_present()

    @pytest.mark.parametrize(
        "checksum_msg_absent",
        [
            (pytest.lazy_fixture("checksumfile_present_pass_notchecked")),
            (pytest.lazy_fixture("checksumfile_present_fail_notchecked")),
        ],
    )
    def test_checksum_complete_msg_absent_pass(self, checksum_msg_absent):
        """
        Test function correctly identifies presence of checksum complete
        string in the checksum file
        """
        for runfolder in checksum_msg_absent:
            assert demultiplex.DemultiplexRunfolder(
                runfolder
            ).checksum_complete_msg_absent()

    def test_checksum_complete_msg_absent_fail(
        self, checksumfile_present_pass_checked
    ):
        """
        Test function correctly identifies absence of the checksum complete
        string in the checksum file
        """
        for runfolder in checksumfile_present_pass_checked:
            assert not demultiplex.DemultiplexRunfolder(
                runfolder
            ).checksum_complete_msg_absent()

    def test_checksums_match_pass(self, checksumfile_present_pass_notchecked):
        """
        Test function correctly identifies presence of checksum match string in
        checksum file. Also test function adds line to denote integrity check
        has been assessed
        """
        for runfolder in checksumfile_present_pass_notchecked:
            dr_obj = demultiplex.DemultiplexRunfolder(runfolder)
            assert demultiplex.DemultiplexRunfolder(
                runfolder
            ).checksums_match()
            with open(
                dr_obj.rf_obj.checksumfile_path, "r", encoding="utf-8"
            ) as checksumfile:
                assert config.CHECKSUM_COMPLETE_MSG in checksumfile.read()

    def test_checksums_match_fail(self, checksumfile_present_pass_notchecked):
        """
        Test function correctly identifies absence of checksum match string in
        checksum file. Also test function adds line to denote integrity check
        has been assessed
        """
        for runfolder in checksumfile_present_pass_notchecked:
            dr_obj = demultiplex.DemultiplexRunfolder(runfolder)
            assert dr_obj.checksums_match()
            with open(
                dr_obj.rf_obj.checksumfile_path, "r", encoding="utf-8"
            ) as checksumfile:
                assert config.CHECKSUM_COMPLETE_MSG in checksumfile.read()

    def test_create_bcl2fastqlog_success(self):
        """
        Test function can successfully create a bcl2fastq log file
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        assert dr_obj.create_bcl2fastqlog()
        assert os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_path)

    def test_create_bcl2fastqlog_fail(self, monkeypatch):
        """
        Test function fails when expected using dummy bcl2fastq log path with
        nonexistent dirs
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        monkeypatch.setattr(
            dr_obj.rf_obj, "bcl2fastqlog_path", "/path/to/nonexistent/log.log"
        )
        assert not dr_obj.create_bcl2fastqlog()
        assert not os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_path)

    def test_add_bcl2fastqlog_tso_msg_success(self):
        """
        Test function can correctly add tso message to the bcl2fastq2 logfile
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        assert dr_obj.add_bcl2fastqlog_tso_msg()
        assert os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_path)
        with open(dr_obj.rf_obj.bcl2fastqlog_path, encoding="utf-8") as file:
            assert config.DEMULTIPLEXLOG_TSO500MSG in file.read()

    def test_run_demultiplexing_success(self, non_tso_runfolder):
        """
        Test demultiplexing is performed successfully. N.B. this does not test
        the functioning of the bcl2fastq executable, which must be tested
        separately as part of the final manual testing
        """
        for folder_name in non_tso_runfolder:
            dr_obj = demultiplex.DemultiplexRunfolder(folder_name)
            # Command to run in place of bcl2fastq command that appends
            # processing complete string to bcl2fastq logfile
            dr_obj.bcl2fastq_cmd = "/bin/true"
            assert dr_obj.run_demultiplexing() and dr_obj.run_processed

    def test_run_demultiplexing_fail(self, non_tso_runfolder):
        """
        Test function fails when providing "/bin/false" as command
        """
        for folder_name in non_tso_runfolder:
            dr_obj = demultiplex.DemultiplexRunfolder(folder_name)
            # Command to run in place of bcl2fastq command that appends
            # processing complete string to bcl2fastq logfile
            dr_obj.bcl2fastq_cmd = "/bin/false"
            assert not dr_obj.run_demultiplexing() and not dr_obj.run_processed

    def test_run_subprocess_success(self):
        """
        Test function successfully executes subprocess
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        assert dr_obj.run_subprocess("echo 'This is a test'")

    def test_check_bcl2fastqlogfile_success(self, bcl2fastqlog_pass):
        """
        Test check_bcl2fastqlogfile returns True for logfiles containing
        expected success message from automate demultiplex config
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        dr_obj.rf_obj.bcl2fastqlog_path = (
            bcl2fastqlog_pass  # Reset path to that from test case
        )
        assert dr_obj.check_bcl2fastqlogfile()

    def test_check_bcl2fastqlogfile_fail(self, bcl2fastqlog_fail):
        """
        Test check_bcl2fastqlogfile returns False for logfiles not containing
        expected success message from automate demultiplex config
        """
        dr_obj = demultiplex.DemultiplexRunfolder("")
        for logpath in bcl2fastqlog_fail:
            dr_obj.rf_obj.bcl2fastqlog_path = (
                logpath  # Reset path to that from test case
            )
            assert not dr_obj.check_bcl2fastqlogfile()

    def test_calculate_cluster_density_pass(self, demultiplexing_required):
        """
        Test calculate_cluster_density() returns True for runfolders requiring
        a cluster density calculation
        """
        for folder_name in demultiplexing_required:
            dr_obj = demultiplex.DemultiplexRunfolder(folder_name)
            assert dr_obj.calculate_cluster_density()

    def test_calculate_cluster_density_fail(self, demultiplexing_notrequired):
        """
        Test calculate_cluster_density() returns None for runfolders where
        RunInfo.xml file is not present
        """
        for folder_name in demultiplexing_notrequired:
            dr_obj = demultiplex.DemultiplexRunfolder(folder_name)
            assert not dr_obj.calculate_cluster_density()
