import pytest
from test.conftest import logger_obj
from toolbox import toolbox
from config import ad_config


def test_software_pass(logger_obj):
    """
    Check test_processing_software function is working. This is expected to fail if
    tests are being carried out on a machine other than the workstation
    """
    assert toolbox.test_processing_software(logger_obj)


def test_software_fail(logger_obj, monkeypatch):
    """
    Check test_processing_software function is working using /bin/true instead of
    executables and test commands (determines software is not functional)
    """
    temp_dict = ad_config.TEST_PROGRAMS_DICT
    temp_dict['bcl2fastq2']['executable'] = "/bin/false"
    temp_dict['bcl2fastq2']['test_cmd'] = "/bin/false"
    temp_dict['bcl2fastq2']['executable'] = "/bin/false"
    temp_dict['bcl2fastq2']['test_cmd'] = "/bin/false"
    monkeypatch.setattr(ad_config, 'TEST_PROGRAMS_DICT', temp_dict)
    with pytest.raises(Exception):
        toolbox.test_processing_software(logger_obj)


def test_software_dummy_pass(logger_obj, monkeypatch):
    """
    Check test_processing_software function is working using /bin/true instead of
    bcl2fastq executable (in case bcl2fastq2 is not functional on the machine in
    use)
    """
    temp_dict = ad_config.TEST_PROGRAMS_DICT
    temp_dict['bcl2fastq2']['executable'] = "/bin/true"
    temp_dict['bcl2fastq2']['test_cmd'] = "/bin/true"
    temp_dict['bcl2fastq2']['executable'] = "/bin/true"
    temp_dict['bcl2fastq2']['test_cmd'] = "/bin/true"
    monkeypatch.setattr(ad_config, 'TEST_PROGRAMS_DICT', temp_dict)
    assert toolbox.test_processing_software(logger_obj)
