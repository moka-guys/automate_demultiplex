# coding=utf-8
import pytest, os, sys
from samplesheet_validator.samplesheet_validator import SamplesheetCheck
from automate_demultiplex_config import sequencer_ids, runtype_list, panel_list, tso500_panel_list


@pytest.fixture
def base_path():
    return os.path.join(os.getcwd(), 'test/test_files/')


@pytest.fixture
def valid_samplesheets(base_path):
    """Test cases with valid paths, files are populated, and valid samplesheet names, and contain:
    - Expected headers, matching Sample_IDs and Sample_Names, valid samples, valid pan nos, valid runtypes
    """
    return [
        ('{}210408_M02631_0186_000000000-JFMNK_SampleSheet.csv'.format(base_path)),
        ('{}210917_NB551068_0409_AH3YNFAFX3_SampleSheet.csv'.format(base_path)),
        ('{}221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv'.format(base_path)),
        ('{}221024_A01229_0146_BHKGG2DRX2_SampleSheet.csv'.format(base_path))
    ]


@pytest.fixture
def invalid_paths(base_path):
    return [
        ('{}210408_M02631_0186_000000000-JFMNN_SampleSheet.csv'.format(base_path)),
        ('{}210918_NB551068_551068_0409_AH3YNFAFX3_SampleSheet.csv'.format(base_path)),
        ('{}221021_A01229_0143_BHGGTHDMXY_SampleSheet.csv'.format(base_path)),
    ]


@pytest.fixture
def invalid_names(base_path):
    return [
        ('{}21108_A01229_0040_AHKGTFDRXY_SampleSheet.csv'.format(base_path)),
        ('{}21aA08_A01229_0040_AHKGTFDRXY_SampleSheet.csv'.format(base_path)),
        ('{}2110915_M02353_0632_000000000-K242J_SampleSheet.csv'.format(base_path)),
    ]


@pytest.fixture
def empty_file(base_path):
    """Empty file with an invalid sequencer ID
    """
    return[
        ('{}220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv'.format(base_path)),
    ]


@pytest.fixture
def invalid_contents(base_path):
    """Test cases with all the following: invalid sequencer id, invalid headers, invalid sample names,
    non-matching samplenames, invalid panel number, invalid runtype
    """
    return [
        ('{}220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv'.format(base_path)),
        ('{}220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'.format(base_path)),
        ('{}200817_NB068_0009_AH3YERAFX3_SampleSheet.csv'.format(base_path)),
    ]


def test_check_paths_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert "sspresent_err" not in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                       runtype_list, tso500_panel_list).errors

def test_check_paths_invalid(invalid_paths):
    for samplesheet in invalid_paths:
        msg = 'Samplesheet with supplied name not present'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["sspresent_err"])


def test_check_ss_name_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert "ssname_err" not in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                    runtype_list, tso500_panel_list).errors


def test_check_ss_name_invalid(invalid_names):
    for samplesheet in invalid_names:
        assert "ssname_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                runtype_list, tso500_panel_list).errors


def test_check_sequencer_id_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "sequencerid_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                         runtype_list, tso500_panel_list).errors


def test_check_sequencer_id_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Sequencer id not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["sequencerid_err"])


def test_check_ss_contents_populated(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "ssempty_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                     runtype_list, tso500_panel_list).errors


def test_check_ss_contents_empty(empty_file):
    for samplesheet in empty_file:
        msg = 'Samplesheet empty (<10 bytes)'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["ssempty_err"])


def test_expected_headers_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "headers_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                     runtype_list, tso500_panel_list).errors


def test_expected_headers_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Header(/s) missing from [Data] section'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["headers_err"])


def test_comp_samplenameid_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "samplenameid_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                          runtype_list, tso500_panel_list).errors


def test_comp_samplenameid_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'The following Sample IDs do not match the corresponding Sample Name'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["samplenameid_err"])


def test_check_illegal_chars_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "validchars_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                        runtype_list, tso500_panel_list).errors


def check_illegal_chars_invalid(invalid_contents):
    msg = 'Sample name contains invalid characters'
    for samplesheet in invalid_contents:
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["validchars_err"])


def test_check_sample_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "sample_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                    runtype_list, tso500_panel_list).errors


def test_check_sample_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        assert "sample_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                runtype_list, tso500_panel_list).errors


def test_check_pannos_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "panno_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                   runtype_list, tso500_panel_list).errors


def test_check_pannos_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Pan number not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["panno_err"])


def test_check_runtypes_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not "runtypes_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                      runtype_list, tso500_panel_list).errors


def test_check_runtypes_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Runtype not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                           runtype_list, tso500_panel_list).errors["runtypes_err"])


def test_multiple_errors(invalid_contents):
    """Tests all expected errors are present at once - invalid sequencer id, invalid headers, invalid sample names,
    non-matching samplenames, invalid panel number, invalid runtype
    """
    msgs = ['Sequencer id not in allowed list', 'Header(/s) missing from [Data] section',
            'The following Sample IDs do not match the corresponding Sample Name',
            'Pan number not in allowed list', 'Runtype not in allowed list']
    for samplesheet in invalid_contents:
        for msg in msgs:
            flatlist = [item for sublist in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                             runtype_list, tso500_panel_list).errors.values()
                        for item in sublist]

            assert any(msg in s for s in flatlist)

        assert "sample_err" in SamplesheetCheck(samplesheet, sequencer_ids, panel_list,
                                                runtype_list, tso500_panel_list).errors