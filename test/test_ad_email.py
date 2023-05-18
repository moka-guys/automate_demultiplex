# coding=utf-8
""" ad_email.py pytest unit tests

N.B. test_email_sending_success() will only pass when running on the
workstation where the required auth details are stored
"""
import logging
import pytest
from ad_email.ad_email import AdEmail
import config.ad_config as ad_config  # Import config file
# import inspect


class TestAdEmail:
    """
    Test Email class
    """

    @pytest.fixture(scope="function")
    def upload_script_logger(self):
        """
        Create basic logger for testing purposes
        """
        return logging.getLogger("test_logger")

    @pytest.fixture(scope="function")
    def email_subject(self):
        """
        Return dummy email subject
        """
        return "DEMULTIPLEX TEST - PLEASE IGNORE"

    @pytest.fixture(scope="function")
    def email_message(self):
        """
        Return dummy email message
        """
        return "Please ignore this email. This is a demultiplex.py unit test"

    @pytest.fixture(scope="function")
    def email_recipients(self):
        """
        Return test email recipients
        """
        return [
            [ad_config.MAIL_SETTINGS['mokaguys_recipient']],
            [ad_config.MAIL_SETTINGS['mokaguys_recipient'],
             ad_config.MAIL_SETTINGS["mokaguys_email"]],
        ]

    def test_send_email_success(
        self,
        upload_script_logger,
        email_subject,
        email_message,
        email_recipients,
    ):
        """
        Test email sending success. NB this test will only pass when running
        on the workstation where the required auth details are stored
        """
        for recipients_list in email_recipients:
            ad_email_obj = AdEmail(logger=upload_script_logger)

            assert ad_email_obj.send_email(
                recipients_list, email_subject, email_message, 1,
            )

    def test_send_email_fail(
        self,
        monkeypatch,
        upload_script_logger,
        email_subject,
        email_message,
        email_recipients,
    ):
        """
        Test email sending failure - incorrect credentials provided
        """
        for recipients_list in email_recipients:
            ad_email_obj = AdEmail(logger=upload_script_logger)
            monkeypatch.setattr(ad_email_obj, "email_user", "abc")
            assert not ad_email_obj.send_email(
                recipients_list, email_subject, email_message, 1, 
            )
