import pytest
from test.conftest import logger_obj
from toolbox import toolbox
from config import ad_config


def test_upload_software_pass():
    """"""


def test_upload_software_fail(logger_obj, monkeypatch):
    """
    Check test_upload_software function fails when expected using /bin/false
    """
    temp_dict = ad_config.TEST_PROGRAMS_DICT
    temp_dict['dx_toolkit']['executable'] = "/bin/false"
    temp_dict['dx_toolkit']['test_cmd'] = "/bin/false"
    temp_dict['dx_toolkit']['executable'] = "/bin/false"
    temp_dict['dx_toolkit']['test_cmd'] = "/bin/false"
    monkeypatch.setattr(ad_config, 'TEST_PROGRAMS_DICT', temp_dict)
    with pytest.raises(Exception):
        toolbox.test_processing_software(logger_obj)


def test_processing_software_pass(logger_obj):
    """
    Check test_processing_software function is working. This is expected to fail if
    tests are being carried out on a machine other than the workstation
    """
    assert toolbox.test_processing_software(logger_obj)


def test_processing_software_fail():
    """"""
    """
    Check test_processing_software function fails when expected using /bin/false
    """


def test_programs_pass():
    """"""


def test_programs_fail():
    """"""


def test_docker_pass():
    """"""


def test_docker_fail():
    """"""
