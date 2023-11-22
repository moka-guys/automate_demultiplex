# coding=utf-8
""" ad_email.py pytest unit tests

N.B. test_email_sending_success() will only pass when running on the
workstation where the required auth details are stored
"""
import pytest
from test.conftest import logger_obj
from ad_email.ad_email import AdEmail
from config import ad_config


class TestAdEmail:
    """
    Test Email class
    """

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
            [ad_config.MAIL_SETTINGS["binfx_recipient"]],
            [
                ad_config.MAIL_SETTINGS["binfx_recipient"],
                ad_config.MAIL_SETTINGS["binfx_email"],
            ],
        ]

    # TODO write test for generate_email_html
    # def test_generate_email_html():

    def test_send_email_success(
        self,
        logger_obj,
        email_subject,
        email_recipients,
    ):
        """
        Test email sending success. NB this test will only pass when running
        on the workstation where the required auth details are stored
        """
        for recipients_list in email_recipients:
            ad_email_obj = AdEmail(logger_obj)
            email_html = ad_email_obj.generate_email_html(
                "test_runfolder", "workflow",
                "SQL_str", 5
            )
            assert email_html
            assert ad_email_obj.send_email(
                recipients_list,
                email_subject,
                email_html,
                1,
            )

    def test_send_email_fail(
        self,
        monkeypatch,
        logger_obj,
        email_subject,
        email_recipients,
    ):
        """
        Test email sending failure - incorrect credentials provided
        """
        for recipients_list in email_recipients:
            ad_email_obj = AdEmail(logger_obj)
            monkeypatch.setattr(ad_email_obj, "email_user", "abc")
            email_html = ad_email_obj.generate_email_html(
                "test_runfolder", "workflow",
                "SQL_str", 5
            )
            with pytest.raises(Exception):
                ad_email_obj.send_email(
                    recipients_list,
                    email_subject,
                    email_html,
                    1,
                )
