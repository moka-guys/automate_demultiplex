""" ad_email.py pytest unit tests. The test suite is currently incomplete

N.B. test_email_sending_success() will only pass when running on the
workstation where the required auth details are stored
"""

import os
import pytest
from ad_email.ad_email import AdEmail
from config.ad_config import AdEmailConfig
from ..conftest import test_data_temp
from ad_logger import ad_logger

# TODO finish this test suite as it is currently incomplete


@pytest.fixture(scope="function")
def logger_obj():
    temp_log = os.path.join(test_data_temp, "temp.log")
    return ad_logger.AdLogger(__name__, "demux", temp_log).get_logger()


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
            [AdEmailConfig.MAIL_SETTINGS["binfx_recipient"]],
            [
                AdEmailConfig.MAIL_SETTINGS["binfx_recipient"],
                AdEmailConfig.MAIL_SETTINGS["binfx_recipient"],
            ],
        ]

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
                "test_runfolder", "workflow", "SQL_str", 5, ["one", "two", "three"]
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
                "test_runfolder", "workflow", "SQL_str", 5, ["one", "two", "three"]
            )
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                ad_email_obj.send_email(
                    recipients_list,
                    email_subject,
                    email_html,
                    1,
                )
                assert pytest_wrapped_e.type == SystemExit
                assert pytest_wrapped_e.value.code == 1
