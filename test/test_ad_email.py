# coding=utf-8
""" ad_email.py pytest unit tests
"""
import os
import shutil
import logging
import pytest
from ad_email.ad_email import AdEmail
import ad_config as config  # Import config file


# Variables used across test classes

# Path of directory containing test files
testfiles_dir = os.path.abspath("test/demultiplex_test_files/")
# Temporary directory to run tests in
temp_dir = os.path.join(testfiles_dir, "temp/")
temp_runfolderdir = os.path.join(temp_dir, "test_runfolders/")

@pytest.fixture(scope="function", autouse=True)
def run_before_and_after_tests(monkeypatch):
    """Setup and teardown before and after each test
    Create temp dir for script to create files in. Removed by teardown class
    Removes temporary directory (containing created files) after testing complete
    """
    # SETUP - run before all tests
    os.makedirs(temp_dir)
    yield  # Where the testing happens
    # TEARDOWN - cleanup after each test
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)


class TestAdEmail():
    """ Test Email class """

    @pytest.fixture(scope="function")
    def upload_script_logger(self):
        """Create basic logger for testing purposes"""
        return logging.getLogger('test_logger')

    @pytest.fixture(scope="function")
    def email_subject(self):
        return "DEMULTIPLEX TEST - PLEASE IGNORE"

    @pytest.fixture(scope="function")
    def email_message(self):
        return "Please ignore this email. This is a demultiplex.py unit test"

    @pytest.fixture(scope="function")
    def email_recipients(self):
        return [(config.mokaguys_recipient),
                ([config.mokaguys_recipient, config.mokaguys_recipient])]

    def test_send_email_success(self, upload_script_logger, email_subject,
                                email_message, email_recipients):
        for recipients in email_recipients:
            ad_email_obj = AdEmail(email_priority=1, logger=upload_script_logger)
            assert ad_email_obj.send_email(email_recipients, email_subject, email_message)

    def test_send_email_fail(self, monkeypatch, upload_script_logger, email_subject,
                             email_message, email_recipients):
        """Test email sending failure - incorrect credentials provided
        """
        for recipients in email_recipients:
            monkeypatch.setattr(config, "user", "abc")
            ad_email_obj = AdEmail(email_priority=1, logger=upload_script_logger)
            assert not ad_email_obj.send_email(recipients, email_subject, email_message)
