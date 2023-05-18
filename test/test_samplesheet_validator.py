""" This script contains pytest tests for the samplesheet_validator.py script
"""
import os
import pytest
from samplesheet_validator.samplesheet_validator import SamplesheetCheck
import config.ad_config as ad_config
import config.panel_config as panel_config
import test.conftest as test_config


@pytest.fixture(scope="function")
def valid_samplesheets():
    """ Test cases with valid paths, files are populated, and valid
    samplesheet names, and contain:
    - Expected headers, matching Sample_IDs and Sample_Names, valid
    samples, valid pan nos, valid runtypes
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '210408_M02631_0186_000000000-JFMNK_SampleSheet.csv'
            )),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '210917_NB551068_0409_AH3YNFAFX3_SampleSheet.csv'
            )),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv')),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '221024_A01229_0146_BHKGG2DRX2_SampleSheet.csv'))
    ]


@pytest.fixture(scope="function")
def invalid_paths():
    """ Collection of nonexistent samplesheets
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '210408_M02631_0186_000000000-JFMNN_SampleSheet.csv'
            )),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '210918_NB551068_551068_0409_AH3YNFAFX3_SampleSheet.csv')),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '221021_A01229_0143_BHGGTHDMXY_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def invalid_names():
    """ Collection of samplesheets with invalid names
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '21108_A01229_0040_AHKGTFDRXY_SampleSheet.csv')),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '21aA08_A01229_0040_AHKGTFDRXY_SampleSheet.csv')),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '2110915_M02353_0632_000000000-K242J_SampleSheet.csv'
            )),
    ]


@pytest.fixture(scope="function")
def empty_file():
    """ Empty file with an invalid sequencer ID
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def invalid_contents():
    """ Test cases with all the following: invalid sequencer id, invalid
    headers, invalid sample names, non-matching samplenames, invalid panel
    number, invalid runtype
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv')),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'
            )),
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '200817_NB068_0009_AH3YERAFX3_SampleSheet.csv')),
    ]


@pytest.fixture(scope="function")
def tso_samplesheet_valid():
    """ Valid TSO samplesheets
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv'))
    ]


@pytest.fixture(scope="function")
def tso_samplesheet_invalid():
    """ Samplesheet not from TSO run
    """
    return [
        (os.path.join(
            test_config.sv_samplesheet_temp_dir,
            '220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'
            ))
    ]


class TestSamplesheetCheck(object):
    """"""

    def test_check_ss_present_valid(self, valid_samplesheets):
        """Test function is able to correctly identify that the samplesheet is
        present
        """
        for samplesheet in valid_samplesheets:
            assert "sspresent_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_ss_present_invalid(self, invalid_paths):
        """ Test function is able to correctly identify that the samplesheet is
        absent
        """
        for samplesheet in invalid_paths:
            msg = 'Samplesheet with supplied name not present'
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['sspresent_err'])

    def test_check_ss_name_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that sample names are
        valid
        """
        for samplesheet in valid_samplesheets:
            assert "ssname_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_ss_name_invalid(self, invalid_names):
        """ Test function is able to correctly identify that sample names are
        invalid
        """
        for samplesheet in invalid_names:
            assert "ssname_err" in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_sequencer_id_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that sequencer ids are
        valid
        """
        for samplesheet in valid_samplesheets:
            assert "sequencerid_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_sequencer_id_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that sequencer ids are
        invalid
        """
        for samplesheet in invalid_contents:
            msg = 'Sequencer id not in allowed list'
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['sequencerid_err'])

    def test_check_ss_contents_populated(self, valid_samplesheets):
        """ Test function is able to correctly identify that samplesheet is not
        empty
        """
        for samplesheet in valid_samplesheets:
            assert "ssempty_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_ss_contents_empty(self, empty_file):
        """ Test function is able to correctly identify that samplesheet i
        empty
        """
        for samplesheet in empty_file:
            msg = 'Samplesheet empty (<10 bytes)'
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['ssempty_err'])

    def test_expected_headers_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that samplesheet
        headers are valid
        """
        for samplesheet in valid_samplesheets:
            assert "headers_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_expected_headers_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that samplesheet
        headers are invalid
        """
        for samplesheet in invalid_contents:
            msg = 'Header(/s) missing from [Data] section'
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['headers_err'])

    def test_comp_samplenameid_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that samplename and
        sampleid match
        """
        for samplesheet in valid_samplesheets:
            assert "samplenameid_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_comp_samplenameid_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that samplename and
        sampleid do not match
        """
        for samplesheet in invalid_contents:
            msg = (
                'The following Sample IDs do not match the corresponding '
                'Sample Name'
                )
            assert msg in str(
                SamplesheetCheck(
                    samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                    ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                    ).errors['samplenameid_err'])

    def test_check_illegal_chars_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that samplename
        does not contain invalid characters"""
        for samplesheet in valid_samplesheets:
            assert "validchars_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def check_illegal_chars_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that samplename
        contains invalid characters
        """
        msg = 'Sample name contains invalid characters'
        for samplesheet in invalid_contents:
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['validchars_err'])

    def test_check_sample_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that sample name is
        valid
        """
        for samplesheet in valid_samplesheets:
            assert "sample_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_sample_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that sample name is not
        valid
        """
        for samplesheet in invalid_contents:
            assert "sample_err" in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_pannos_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that panel numbers are
        valid
        """
        for samplesheet in valid_samplesheets:
            assert "panno_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_pannos_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that panel numbers are
        not valid
        """
        for samplesheet in invalid_contents:
            msg = 'Pan number not in allowed list'
            assert msg in str(
                SamplesheetCheck(
                    samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                    ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                    ).errors['panno_err'])

    def test_check_runtypes_valid(self, valid_samplesheets):
        """ Test function is able to correctly identify that runtypes are valid
        """
        for samplesheet in valid_samplesheets:
            assert "runtypes_err" not in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors

    def test_check_runtypes_invalid(self, invalid_contents):
        """ Test function is able to correctly identify that runtypes are
        invalid
        """
        for samplesheet in invalid_contents:
            msg = 'Runtype not in allowed list'
            assert msg in str(SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS
                ).errors['runtypes_err'])

    def check_tso_true(self, tso_samplesheet_valid):
        """ Test function is able to correctly identify that runtypes are
        TSO500
        """
        assert SamplesheetCheck(
            tso_samplesheet_valid, ad_config.SEQUENCER_IDS,
            panel_config.PANELS, ad_config.RUNTYPE_LIST,
            panel_config.TSO500_PANELS).tso

    def check_tso_false(self, tso_samplesheet_invalid):
        """ Test function is able to correctly identify that runtypes are not
        TSO500
        """
        assert not SamplesheetCheck(
            tso_samplesheet_invalid, ad_config.SEQUENCER_IDS,
            panel_config.PANELS, ad_config.RUNTYPE_LIST,
            panel_config.TSO500_PANELS).tso

    def test_multiple_errors(self, invalid_contents):
        """ Tests all expected errors are present at once - invalid sequencer
        id, invalid headers, invalid sample names, non-matching samplenames,
        invalid panel number, invalid runtype
        """
        msgs = [
            'Sequencer id not in allowed list',
            'Header(/s) missing from [Data] section',
            (
                'The following Sample IDs do not match the corresponding '
                'Sample Name'
                ),
            'Pan number not in allowed list', 'Runtype not in allowed list']
        for samplesheet in invalid_contents:
            for msg in msgs:
                flatlist = [item for sublist in
                            SamplesheetCheck(
                                samplesheet, ad_config.SEQUENCER_IDS,
                                panel_config.PANELS, ad_config.RUNTYPE_LIST,
                                panel_config.TSO500_PANELS).errors.values()
                            for item in sublist]

                assert any(msg in s for s in flatlist)

            assert "sample_err" in SamplesheetCheck(
                samplesheet, ad_config.SEQUENCER_IDS, panel_config.PANELS,
                ad_config.RUNTYPE_LIST, panel_config.TSO500_PANELS).errors
