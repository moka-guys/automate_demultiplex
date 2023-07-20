"""
This script contains pytest tests for the samplesheet_validator.py script
"""
import os
import pytest
import shutil
import logging
from samplesheet_validator.samplesheet_validator import SamplesheetCheck
from test import conftest
from ad_logger import ad_logger
from toolbox import toolbox


@pytest.fixture(scope="function")
def valid_samplesheets():
    """
    Test cases with valid paths, files are populated, and valid samplesheet names, and
    contain:
        Expected headers, matching Sample_IDs and Sample_Names, valid samples, valid pan
        nos, valid runtypes
    """
    return [
        ("210408_M02631_0186_000000000-JFMNK", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '210408_M02631_0186_000000000-JFMNK_SampleSheet.csv'
            )),
        ("210917_NB551068_0409_AH3YNFAFX3", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '210917_NB551068_0409_AH3YNFAFX3_SampleSheet.csv'
            )),
        ("221021_A01229_0145_BHGGTHDMXY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv')),
        ("221024_A01229_0146_BHKGG2DRX2", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '221024_A01229_0146_BHKGG2DRX2_SampleSheet.csv'))
    ]


@pytest.fixture(scope="function")
def invalid_paths():
    """
    Collection of nonexistent samplesheets
    """
    return [
        ("210408_M02631_0186_000000000-JFMNN", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '210408_M02631_0186_000000000-JFMNN_SampleSheet.csv'
            )),
        ("210918_NB551068_551068_0409_AH3YNFAFX3", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '210918_NB551068_551068_0409_AH3YNFAFX3_SampleSheet.csv')),
        ("221021_A01229_0143_BHGGTHDMXY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '221021_A01229_0143_BHGGTHDMXY_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def invalid_names():
    """
    Collection of samplesheets with invalid names
    """
    return [
        ("21108_A01229_0040_AHKGTFDRXY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '21108_A01229_0040_AHKGTFDRXY_SampleSheet.csv')),
        ("21aA08_A01229_0040_AHKGTFDRXY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '21aA08_A01229_0040_AHKGTFDRXY_SampleSheet.csv')),
        ("2110915_M02353_0632_000000000-K242J", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '2110915_M02353_0632_000000000-K242J_SampleSheet.csv'
            )),
    ]


@pytest.fixture(scope="function")
def empty_file():
    """
    Empty file with an invalid sequencer ID
    """
    return [
        ("220413_A01229_0032_AHGKBIEKFR", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def invalid_contents():
    """
    Test cases with all the following: invalid sequencer id, invalid headers, invalid
    sample names, non-matching samplenames, invalid panel number, invalid runtype
    """
    return [
        ("220404_B01229_0348_HFGIFEIOPY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv')),
        ("220408_A02631_0186_000000000-JLJFE", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'
            )),
        ("200817_NB068_0009_AH3YERAFX3", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '200817_NB068_0009_AH3YERAFX3_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def tso_samplesheet_valid():
    """
    Valid TSO samplesheets
    """
    return [
        ("221021_A01229_0145_BHGGTHDMXY", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv'))
    ]


@pytest.fixture(scope="function")
def tso_samplesheet_invalid():
    """
    Samplesheet not from TSO run
    """
    return [
        ("220408_A02631_0186_000000000-JLJFE", os.path.join(
            conftest.sv_samplesheet_temp_dir,
            '220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'
            ))
    ]


class TestSamplesheetCheck(object):
    """
    Tests for the SamplesheetCheck class
    """
    def test_check_ss_present_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that the samplesheet is present
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_ss_present_invalid(self, invalid_paths, caplog):
        """
        Test function is able to correctly identify that the samplesheet is absent
        """
        for runfoldername, samplesheet in invalid_paths:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Samplesheet with supplied name not present" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_ss_name_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that sample names are valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_ss_name_invalid(self, invalid_names, caplog):
        """
        Test function is able to correctly identify that sample names are invalid
        """
        for runfoldername, samplesheet in invalid_names:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Samplesheet name is invalid" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_sequencer_id_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that sequencer ids are valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_sequencer_id_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that sequencer ids are invalid
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Sequencer id not in allowed list" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_ss_contents_populated(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that samplesheet is not empty
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_ss_contents_empty(self, empty_file, caplog):
        """
        Test function is able to correctly identify that samplesheet is empty
        """
        for runfoldername, samplesheet in empty_file:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Samplesheet empty (<10 bytes)" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_expected_headers_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that samplesheet headers are valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_expected_headers_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that samplesheet headers are invalid
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Header(/s) missing from [Data] section:" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_comp_samplenameid_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that samplename and sampleid match
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_comp_samplenameid_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that samplename and sampleid do not
        match
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert (
                "The following Sample IDs do not match the corresponding Sample Name"
                in caplog.text
            )
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_illegal_chars_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that samplename does not contain
        invalid characters
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def check_illegal_chars_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that samplename contains invalid
        characters
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Sample name contains invalid characters" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_sample_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that sample name is valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_sample_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that sample name is not valid
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Sample name invalid" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_pannos_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that panel numbers are valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_pannos_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that panel numbers are not valid
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Pan no is invalid" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_runtypes_valid(self, valid_samplesheets, caplog):
        """
        Test function is able to correctly identify that runtypes are valid
        """
        for runfoldername, samplesheet in valid_samplesheets:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.errors
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_check_runtypes_invalid(self, invalid_contents, caplog):
        """
        Test function is able to correctly identify that runtypes are invalid
        """
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert "Runtype not in allowed list" in caplog.text
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def check_tso_true(self, tso_samplesheet_valid):
        """
        Test function is able to correctly identify that runtypes are TSO500
        """
        for runfoldername, samplesheet in tso_samplesheet_valid:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.tso
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def check_tso_false(self, tso_samplesheet_invalid, caplog):
        """
        Test function is able to correctly identify that runtypes are not TSO500
        """
        for runfoldername, samplesheet in tso_samplesheet_invalid:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert not sscheck_obj.tso
            ad_logger.shutdown_logs(sscheck_obj.logger)

    def test_multiple_errors(self, invalid_contents, caplog):
        """
        Tests all expected errors are present at once - invalid sequencer id, invalid
        headers, invalid sample names, non-matching samplenames, invalid panel number,
        invalid runtype
        """
        msgs = [
            'Sequencer id not in allowed list',
            'Header(/s) missing from [Data] section',
            'The following Sample IDs do not match the corresponding Sample Name',
            'Sample name invalid',
            'Pan no is invalid', 'Runtype not in allowed list',
            ]
        for runfoldername, samplesheet in invalid_contents:
            sscheck_obj = SamplesheetCheck(samplesheet, runfoldername)
            sscheck_obj.ss_checks()
            assert sscheck_obj.errors
            assert all(msg in caplog.text for msg in msgs)
            ad_logger.shutdown_logs(sscheck_obj.logger)
