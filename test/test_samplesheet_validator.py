import pytest
from samplesheet_validator import SamplesheetCheck
import argparse
import os
import re
from collections import defaultdict
import tempfile
import shutil
import logging
import automate_demultiplex_config as config
import adlogger #import ADLoggers, get_runfolder_log_config
from seglh_naming.sample import Sample
from seglh_naming.samplesheet import Samplesheet
import string


@pytest.fixture
def base_path():
    return os.path.join(os.getcwd(), 'test/test_files/')

@pytest.fixture
def valid_samplesheets(base_path):
    '''
    Test cases with valid paths, files are populated, and valid samplesheet names, and contain:
    - Expected headers, matching Sample_IDs and Sample_Names, valid samples, valid pan nos, valid runtypes
    '''
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
    '''
    Empty file with an invalid sequencer ID
    '''
    return[
        ('{}220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv'.format(base_path)),
    ]


@pytest.fixture
def invalid_contents(base_path):
    '''
    test cases with all the following: invalid sequencer id, invalid headers, invalid sample names,
    non-matching samplenames, invalid panel number, invalid runtype
    '''
    return [
        ('{}220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv'.format(base_path)),
        ('{}220408_A02631_0186_000000000-JLJFE_SampleSheet.csv'.format(base_path)),
        ('{}200817_NB068_0009_AH3YERAFX3_SampleSheet.csv'.format(base_path)),
    ]


def test_check_paths_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("sspresent_err")


def test_check_paths_invalid(invalid_paths):
    for samplesheet in invalid_paths:
        msg = 'Samplesheet with supplied name not present'
        assert msg in str(SamplesheetCheck(samplesheet).errors["sspresent_err"])


def test_check_ss_name_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("ssname_err")


def test_check_ss_name_invalid(invalid_names):
    for samplesheet in invalid_names:
       assert SamplesheetCheck(samplesheet).errors.has_key("ssname_err")


def test_check_sequencer_id_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("sequencerid_err")


def test_check_sequencer_id_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Sequencer id not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet).errors["sequencerid_err"])


def test_check_ss_contents_populated(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("sscontents_err")


def test_check_ss_contents_empty(empty_file):
    for samplesheet in empty_file:
        msg = 'Samplesheet empty (<10 bytes)'
        assert msg in str(SamplesheetCheck(samplesheet).errors["sscontents_err"])


def test_expected_headers_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("headers_err")


def test_expected_headers_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Header(/s) missing from [Data] section'
        assert msg in str(SamplesheetCheck(samplesheet).errors["headers_err"])


def test_compare_samplenames_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("samplenameid_err")


def test_compare_samplenames_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'The following Sample IDs do not match the corresponding Sample Name'
        assert msg in str(SamplesheetCheck(samplesheet).errors["samplenameid_err"])


def test_check_sample_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("sample_err")


def test_check_sample_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        assert SamplesheetCheck(samplesheet).errors.has_key("sample_err")


def test_check_pannos_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("panno_err")


def test_check_pannos_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Pan number not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet).errors["panno_err"])


def test_check_runtypes_valid(valid_samplesheets):
    for samplesheet in valid_samplesheets:
        assert not SamplesheetCheck(samplesheet).errors.has_key("runtypes_err")


def test_check_runtypes_invalid(invalid_contents):
    for samplesheet in invalid_contents:
        msg = 'Runtype not in allowed list'
        assert msg in str(SamplesheetCheck(samplesheet).errors["runtypes_err"])


def test_multiple_errors(invalid_contents):
    '''
    Tests all expected errors are present at once - invalid sequencer id, invalid headers, invalid sample names,
    non-matching samplenames, invalid panel number, invalid runtype
    '''
    msgs = ['Sequencer id not in allowed list', 'Header(/s) missing from [Data] section',
            'The following Sample IDs do not match the corresponding Sample Name',
            'Pan number not in allowed list', 'Runtype not in allowed list']
    for samplesheet in invalid_contents:
        for msg in msgs:
            flatlist = [item for sublist in SamplesheetCheck(samplesheet).errors.values() for item in sublist]
            assert any(msg in s for s in flatlist)
        assert SamplesheetCheck(samplesheet).errors.has_key("sample_err")