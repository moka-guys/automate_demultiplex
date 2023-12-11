#!/usr/bin/python3
# coding=utf-8
"""
demultiplex.py pytest unit tests

# TODO write the following tests which are currently missing or incomplete:
- test_get_runfolder_names_test
- test_get_runfolder_names_prod
- test_setoff_processing_toproc
- test_setoff_processing_nottoproc
- test_demultiplex_runfolder_toproc
- test_demultiplex_runfolder_nottoproc
- test_check_dev_run_fail
- test_pass_integrity_check_pass
- test_pass_integrity_check_fail
- test_add_bcl2fastqlog_tso_msg_fail
"""
import os
import itertools
import pytest
from demultiplex import demultiplex
from config import ad_config
from test import conftest
from ad_logger import ad_logger
from pytest_cases import fixture_union


def get_dr_obj(runfolder):
    """"""
    dr_obj = demultiplex.DemultiplexRunfolder(runfolder, ad_config.TIMESTAMP, False)
    return dr_obj


def get_gr_obj():
    """"""
    gr_obj = demultiplex.GetRunfolders()
    return gr_obj


@pytest.fixture(scope="function")
def valid_samplesheets():
    """
    Test cases with valid paths, files are populated, and valid samplesheet names, and
    contain:
        Expected headers, matching Sample_IDs and Sample_Names, valid samples, valid pan
        nos, valid runtypes
    """
    return [
        (
            "210408_M02631_0186_000000000-JFMNK",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "210408_M02631_0186_000000000-JFMNK_SampleSheet.csv",
            ),
        ),
        (
            "210917_NB551068_0409_AH3YNFAFX3",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "210917_NB551068_0409_AH3YNFAFX3_SampleSheet.csv",
            ),
        ),
        (
            "221021_A01229_0145_BHGGTHDMXY",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv",
            ),
        ),
        (
            "221024_A01229_0146_BHKGG2DRX2",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "221024_A01229_0146_BHKGG2DRX2_SampleSheet.csv",
            ),
        ),
    ]


@pytest.fixture(scope="function")
def invalid_paths():
    """
    Collection of nonexistent samplesheets
    """
    return [
        (
            "210408_M02631_0186_000000000-JFMNN",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "210408_M02631_0186_000000000-JFMNN_SampleSheet.csv",
            ),
        ),
        (
            "210918_NB551068_551068_0409_AH3YNFAFX3",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "210918_NB551068_551068_0409_AH3YNFAFX3_SampleSheet.csv",
            ),
        ),
        (
            "221021_A01229_0143_BHGGTHDMXY",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "221021_A01229_0143_BHGGTHDMXY_SampleSheet.csv",
            ),
        ),
    ]


@pytest.fixture(scope="function")
def invalid_names():
    """
    Collection of samplesheets with invalid names
    """
    return [
        (
            "21108_A01229_0040_AHKGTFDRXY",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "21108_A01229_0040_AHKGTFDRXY_SampleSheet.csv",
            ),
        ),
        (
            "21aA08_A01229_0040_AHKGTFDRXY",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "21aA08_A01229_0040_AHKGTFDRXY_SampleSheet.csv",
            ),
        ),
        (
            "2110915_M02353_0632_000000000-K242J",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "2110915_M02353_0632_000000000-K242J_SampleSheet.csv",
            ),
        ),
    ]



@pytest.fixture(scope="function")
def empty_file():
    """
    Empty file with an invalid sequencer ID
    """
    return [
        (
            "220413_A01229_0032_AHGKBIEKFR",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv",
            ),
        ),
    ]


@pytest.fixture(scope="function")
def invalid_contents():
    """
    Test cases with all the following: invalid sequencer id, invalid headers, invalid
    sample names, non-matching samplenames, invalid panel number, invalid runtype
    """
    return [
        (
            "220404_B01229_0348_HFGIFEIOPY",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv",
            ),
        ),
        (
            "220408_A02631_0186_000000000-JLJFE",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "220408_A02631_0186_000000000-JLJFE_SampleSheet.csv",
            ),
        ),
        (
            "200817_NB068_0009_AH3YERAFX3",
            os.path.join(
                conftest.sv_samplesheet_temp_dir,
                "200817_NB068_0009_AH3YERAFX3_SampleSheet.csv",
            ),
        ),
    ]


class TestGetRunfolders(object):
    """
    Test GetRunfolders class
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

    # TODO need to work out how to setup these runfolders as they need full sequencing
    # data for the tests to be able to complete
    @pytest.fixture(scope="function")
    def runfolders_toproc(self):
        """
        List of runfolders requiring processing
        """
        return [
            # "999999_M02631_0000_00000TEST4",  # TODO fix test case
            # Barcodes in sample sheet are longer than the index length found in RunInfo.xml
            # "999999_A01229_0000_00000TEST7",  # TODO fix test case
            # Unable to find BCL file for 's_1_1101' in: /mnt/run/Data/Intensities/BaseCalls/L001/C1.1
            # "999999_A01229_0000_00000TEST9",  # TODO fix test case
            # Unable to find BCL file for 's_1_1101' in: /mnt/run/Data/Intensities/BaseCalls/L001/C1.1
            # "999999_A01229_0000_0000TEST11",  # TODO fix test case
            # Cannot read non-existent file: file:///input_run/RunInfo.xml
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

    @pytest.fixture(scope="function")
    def rf_no_bcl2fastqlog(self):
        """
        Return runfolders with absent bcl2fastqlog
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
    def rf_with_bcl2fastqlog(self):
        """
        Return runfolders with bcl2fastqlog present
        """
        return ["999999_A01229_0000_00000TEST1"]

    # TODO write tests
    # def test_get_runfolder_names_test(self):
    # def test_get_runfolder_names_prod(self):

    # TODO fix these tests
    def test_setoff_processing_toproc(self, runfolders_toproc, monkeypatch):
        """
        Pass set of runfolders expected to be successfully processed by script. Assert
        that the expected number are processed
        """
        # TODO fix the below patch
        monkeypatch.setattr(
            demultiplex.ad_config, "DEMULTIPLEX_TEST_RUNFOLDERS",
            runfolders_toproc
        )
        gr_obj = get_gr_obj()
        demultiplex.DemultiplexRunfolder.bcl2fastq2_cmd = (
            f"echo '{ad_config.STRINGS['demultiplex_success']}"
            )
        gr_obj.setoff_processing()
        assert all(
            runfolder in gr_obj.processed_runfolders
            for runfolder in runfolders_toproc
        )

    # def test_setoff_processing_nottoproc(self, runfolders_nottoproc, monkeypatch):
    #     """
    #     Pass set of runfolders that should not be processed for various reasons. Assert
    #     that none have been processed
    #     """
    #     monkeypatch.setattr(
    #         demultiplex.ad_config, "DEMULTIPLEX_TEST_RUNFOLDERS", runfolders_nottoproc
    #     )
    #     gr_obj = get_gr_obj()
    #     with pytest.raises(SystemExit) as pytest_wrapped_e:
    #         gr_obj.setoff_processing()
    #         assert pytest_wrapped_e.type == SystemExit
    #         assert pytest_wrapped_e.value.code == 1

    # TODO write test_demultiplex_runfolder_toproc(self):
    # TODO write test_demultiplex_runfolder_nottoproc(self):

    def test_bcl2fastqlog_absent_false(self, rf_with_bcl2fastqlog):
        """
        Test function correctly identifies presence of bcl2fastqlogfile using an empty
        file
        """
        for runfolder in rf_with_bcl2fastqlog:
            gr_obj = get_gr_obj()
            assert not gr_obj.bcl2fastqlog_absent(runfolder)

    def test_bcl2fastqlog_absent_true(self, rf_no_bcl2fastqlog):
        """
        Test function correctly identifies absence of bcl2fastqlogfile log file, using a
        path to a nonexistent file
        """
        for runfolder in rf_no_bcl2fastqlog:
            gr_obj = get_gr_obj()
            assert gr_obj.bcl2fastqlog_absent(runfolder)

    # TODO write test_return_num_processed_runfolders(self):


class TestDemultiplexRunfolder(object):
    """
    Test DemultiplexRunfolder class
    """

    @pytest.fixture(scope="function")
    def bcl2fastqlog_fail(self):
        """
        Logfiles not containing expected success message from ad_config
        """
        return [
            (
                os.path.join(conftest.temp_testfiles_dir, "bcl2fastq2_output_nomsg.log")
            ),  # No success message present in logfile
            ("nonexistent.log"),  # Logfile nonexistent
            (
                os.path.join(conftest.temp_testfiles_dir, "bcl2fastq2_output_empty.log")
            ),  # Logfile empty
        ]

    @pytest.fixture(scope="function")
    def bcl2fastqlog_pass(self):
        """
        Logfiles containing expected success message from ad_config
        """
        return os.path.join(
            conftest.temp_testfiles_dir, "bcl2fastq2_output_success.log"
        )

    @pytest.fixture(scope="function")
    def icheck_required(self):
        """
        Runfolder that would require an integrity check
        """
        return "999999_NB551068_0009_AH3YERAFX3"

    @pytest.fixture(scope="function")
    def icheck_notrequired(self):
        """
        Runfolder that would not require an integrity check
        """
        return "999999_M02353_0641_000000000-TESTS"

    @pytest.fixture(scope="function")
    def internal_chars_invalid(self):
        """
        Samplesheet containing invalid characters in sample name
        """
        return [
            (
                "210513_M02631_0236_000000000-JFMNK",
                os.path.join(
                    conftest.sv_samplesheet_temp_dir,
                    "210513_M02631_0236_000000000-JFMNK_SampleSheet.csv",
                ),
            )
        ]

    @pytest.fixture(scope="function")
    def perfect_ss(self):
        """
        Path to perfect samplesheet
        """
        return os.path.join(
            conftest.sv_samplesheet_temp_dir,
            "210408_M02631_0186_000000000-JFMNK_SampleSheet.csv",
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
        Samplesheets with disallowed errors in the more stringent set of requirements
        than the base samplesheet validator check
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
        Return runfolders where demultiplexing is required. Sequencing complete,
        demultiplexing has not yet started
        """
        return [
            "999999_M02631_0000_00000TEST4",
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_00000TEST9",
        ]

    # TODO add a development run to this fixture
    @pytest.fixture(scope="function")
    def demultiplexing_notrequired(self):
        """
        This test covers all runfolder cases where demultiplexing is not required
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
            "999999_A01229_0000_00000TEST9",
            "999999_A01229_0000_0000TEST10",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def rtacomplete_absent(self):
        """
        Return runfolders with no RTAComplete file
        """
        return [
            "999999_A01229_0000_00000TEST1",
            "999999_A01229_0000_00000TEST2",
        ]

    @pytest.fixture(scope="function")
    def checksumfile_present_pass_checked(self):
        """
        Return runfolders containing checksumfile containing matching checksums, a pass
        message, and a previous checksum check message
        """
        return ["999999_A01229_0000_0000TEST10"]

    @pytest.fixture(scope="function")
    def checksumfile_present_fail_notchecked(self):
        """
        Return runfolders containing checksumfile containing non-matching checksums, a
        failure message and no previous checksum check message
        """
        return ["999999_A01229_0000_00000TEST6"]

    @pytest.fixture(scope="function")
    def checksumfile_present_pass_notchecked(self):
        """
        Return runfolders containing checksumfile containing matching checksums, a
        checksum pass message, and no previous checksum check message
        """
        return [
            "999999_A01229_0000_00000TEST7",
            "999999_A01229_0000_00000TEST9",
            "999999_A01229_0000_0000TEST11",
        ]

    fixture_union(
        "no_prior_ic_rfs",
        [
            "checksumfile_present_pass_notchecked",
            "checksumfile_present_fail_notchecked",
        ],
    )

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
        This test covers all runfolder cases where the runfolder is from a tso run
        """
        return [
            "999999_A01229_0000_00000TEST8",
            "999999_A01229_0000_0000TEST11",
        ]

    @pytest.fixture(scope="function")
    def non_tso_runfolder(self):
        """
        This test case contains non-tso runfolders requiring demultiplexing
        """
        return [
            # "999999_A01229_0000_00000TEST9",  # Fix as per comments in runfolders_toproc
            # "999999_A01229_0000_00000TEST7",  # Fix as per comments in runfolders_toproc
        ]

    def test_setoff_workflow_success(self, demultiplexing_required, monkeypatch):
        """
        Test that function sets off run processing correctly for runfolders requiring it
        """
        for runfolder in demultiplexing_required:
            dr_obj = get_dr_obj(runfolder)
            # Command to run in place of bcl2fastq2 command that appends processing
            # complete string to bcl2fastq2 logfile
            monkeypatch.setattr(
                dr_obj,
                "bcl2fastq2_cmd",
                f"echo '{ad_config.STRINGS['demultiplex_success']}' >> "
                f"{dr_obj.rf_obj.bcl2fastqlog_file}",
            )
            assert dr_obj.setoff_workflow() and dr_obj.run_processed
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_setoff_workflow_fail(self, demultiplexing_notrequired):
        """
        Test that function correctly does not process runfolders that do not need
        processing
        """
        for runfolder in demultiplexing_notrequired:
            dr_obj = get_dr_obj(runfolder)
            assert not dr_obj.setoff_workflow() and not dr_obj.run_processed
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_demultiplexing_required_true(self, demultiplexing_required):
        """
        Test demultiplexing_required() returns True when demultiplexin required
        """
        for runfolder in demultiplexing_required:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.demultiplexing_required()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_demultiplexing_required_false(
        self, demultiplexing_notrequired, monkeypatch
    ):
        """
        Test demultiplexing_required() returns none when demultiplexing not required
        """
        for runfolder in demultiplexing_notrequired:
            dr_obj = get_dr_obj(runfolder)
            assert not dr_obj.demultiplexing_required()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_valid_samplesheet_pass(self, monkeypatch, valid_samplesheets):
        """
        Test function correctly returns valid flag, using a set of representative
        samplesheets
        """
        for runfoldername, sspath in valid_samplesheets:
            dr_obj = get_dr_obj("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", sspath)
            valid, _ = dr_obj.valid_samplesheet()
            assert valid
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_valid_samplesheet_fail(self, monkeypatch, ss_with_disallowed_sserrs):
        """
        Test function fails to return valid flag as expected, using a set of
        samplesheets covering all failure cases
        """
        for runfoldername, sspath in ss_with_disallowed_sserrs:
            dr_obj = get_dr_obj("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", sspath)
            valid, _ = dr_obj.valid_samplesheet()
            assert not valid
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_sequencing_complete_pass(self, rtacomplete_present):
        """
        Test sequencing_complete() can identify presence of rtacomplete file
        """
        for runfolder in rtacomplete_present:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.sequencing_complete()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_sequencing_complete_fail(self, rtacomplete_absent):
        """
        Provide path to nonexistent rtacompletefile
        """
        for runfolder in rtacomplete_absent:
            dr_obj = get_dr_obj(runfolder)
            assert not dr_obj.sequencing_complete()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)
    
    # TODO write test_check_dev_run_pass
    # TODO write test_check_dev_run_fail
    # TODO write test_pass_integrity_check_pass
    # TODO write test_pass_integrity_check_fail

    def test_no_disallowed_sserrs_pass(self, monkeypatch, perfect_ss):
        """
        Test no_disallowed_sserrs() using a perfect samplesheet
        """
        dr_obj = get_dr_obj("")
        monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", perfect_ss)
        valid, sscheck_obj = dr_obj.valid_samplesheet()
        assert dr_obj.no_disallowed_sserrs(valid, sscheck_obj)
        ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_no_disallowed_sserrs_fail(self, monkeypatch, ss_with_disallowed_sserrs):
        """
        Tests function identifies all disallowed ss errors
        """
        for runfoldername, sspath in ss_with_disallowed_sserrs:
            dr_obj = get_dr_obj("")
            monkeypatch.setattr(dr_obj.rf_obj, "samplesheet_path", sspath)
            valid, sscheck_obj = dr_obj.valid_samplesheet()
            assert not dr_obj.no_disallowed_sserrs(valid, sscheck_obj)
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_seq_requires_no_ic_pass(self, icheck_notrequired):
        """
        Test function correctly detects that runfolder does not require an integrity
        check
        """
        dr_obj = get_dr_obj(icheck_notrequired)
        assert dr_obj.seq_requires_no_ic()
        ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_seq_requires_no_ic_fail(self, icheck_required):
        """
        Test function correctly detects that runfolder requires an integrity check
        """
        dr_obj = get_dr_obj(icheck_required)
        assert not dr_obj.seq_requires_no_ic()
        ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_no_prior_ic_pass(self, no_prior_ic_rfs):
        """
        Test function correctly identifies there has been a prior integrity check
        """
        for runfolder in no_prior_ic_rfs:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.no_prior_ic()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_no_prior_ic_fail(self, checksumfile_present_pass_checked):
        """
        Test function correctly identifies checksums have been assessed by the script
        previously
        """
        for runfolder in checksumfile_present_pass_checked:
            dr_obj = get_dr_obj(runfolder)
            assert not dr_obj.no_prior_ic()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_checksums_match_pass(
        self, checksumfile_present_pass_notchecked, monkeypatch
    ):
        """
        Test function correctly identifies presence of checksum match string in checksum
        file. Also test function adds line to denote integrity check has been assessed
        """
        for runfolder in checksumfile_present_pass_notchecked:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.checksums_match()
            with open(dr_obj.rf_obj.checksumfile_path, "r") as checksumfile:
                assert ad_config.CHECKSUM_COMPLETE_MSG in checksumfile.read()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_checksums_match_fail(
        self, checksumfile_present_pass_notchecked, monkeypatch
    ):
        """
        Test function correctly identifies absence of checksum match string in checksum
        file. Also test function adds line to denote integrity check has been assessed
        """
        for runfolder in checksumfile_present_pass_notchecked:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.checksums_match()
            with open(dr_obj.rf_obj.checksumfile_path, "r") as checksumfile:
                assert ad_config.CHECKSUM_COMPLETE_MSG in checksumfile.read()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    @pytest.mark.nodisableloggers
    def test_create_bcl2fastqlog_success(self):
        """
        Test function can successfully create a bcl2fastq2 log file
        """
        dr_obj = get_dr_obj("")
        assert dr_obj.create_bcl2fastqlog()
        assert os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_file)
        ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    @pytest.mark.nodisableloggers
    def test_create_bcl2fastqlog_fail(self, monkeypatch):
        """
        Test function fails when expected using dummy bcl2fastq2 log path with
        nonexistent dirs
        """
        dr_obj = get_dr_obj("")
        monkeypatch.setattr(
            dr_obj.rf_obj, "bcl2fastqlog_file", "/path/to/nonexistent/log.log"
        )
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            dr_obj.create_bcl2fastqlog()
            assert not os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_file)
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)
            assert pytest_wrapped_e.type == SystemExit
            assert pytest_wrapped_e.value.code == 1

    def test_add_bcl2fastqlog_tso_msg_pass(self):
        """
        Test function can correctly add tso message to the bcl2fastq2 logfile
        """
        dr_obj = get_dr_obj("")
        assert dr_obj.add_bcl2fastqlog_tso_msg()
        assert os.path.isfile(dr_obj.rf_obj.bcl2fastqlog_file)
        with open(dr_obj.rf_obj.bcl2fastqlog_file, "r") as file:
            assert ad_config.STRINGS["demultiplexlog_tso500_msg"] in file.read()
        ad_logger.shutdown_logs(dr_obj.demux_rf_logger)
    
    # TODO write test_add_bcl2fastqlog_tso_msg_fail

    def test_run_demultiplexing_success(self, non_tso_runfolder):
        """
        Test demultiplexing is performed successfully. N.B. this does not test the
        functioning of the bcl2fastq2 executable, which must be tested separately as
        part of the final manual testing
        """
        for runfolder in non_tso_runfolder:
            dr_obj = get_dr_obj(runfolder)
            # Command to run in place of bcl2fastq2 command that appends processing
            # complete string to bcl2fastq2 logfile
            # TODO swap below to a patch
            dr_obj.bcl2fastq2_cmd = (
                f"echo '{ad_config.STRINGS['demultiplex_success']}' >> "
                f"{dr_obj.rf_obj.bcl2fastqlog_file}"
            )
            assert dr_obj.run_demultiplexing()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_run_demultiplexing_fail(self, non_tso_runfolder):
        """
        Test function fails when providing "/bin/false" as command
        """
        for runfolder in non_tso_runfolder:
            dr_obj = get_dr_obj(runfolder)
            # Command to run in place of bcl2fastq2 command that appends processing
            # complete string to bcl2fastq2 logfile
            # TODO swap below to a patch
            dr_obj.bcl2fastq2_cmd = "/bin/false"
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                dr_obj.run_demultiplexing()
                assert not dr_obj.run_processed
                ad_logger.shutdown_logs(dr_obj.demux_rf_logger)
                assert pytest_wrapped_e.type == SystemExit
                assert pytest_wrapped_e.value.code == 1

    def test_calculate_cluster_density_pass(self, demultiplexing_required):
        """
        Test calculate_cluster_density() returns True for runfolders requiring a cluster
        density calculation
        """
        for runfolder in demultiplexing_required:
            dr_obj = get_dr_obj(runfolder)
            assert dr_obj.calculate_cluster_density()
            ad_logger.shutdown_logs(dr_obj.demux_rf_logger)

    def test_calculate_cluster_density_fail(
        self, demultiplexing_notrequired, monkeypatch
    ):
        """
        Test calculate_cluster_density() returns None for runfolders where RunInfo.xml
        file is not present
        """
        for runfolder in demultiplexing_notrequired:
            dr_obj = get_dr_obj(runfolder)
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                dr_obj.calculate_cluster_density()
                ad_logger.shutdown_logs(dr_obj.demux_rf_logger)
                assert pytest_wrapped_e.type == SystemExit
                assert pytest_wrapped_e.value.code == 1
