#!/usr/bin/python3
# coding=utf-8
"""
Email sending module
"""
import jinja2
import smtplib
import config.ad_config as ad_config
import ad_logger.log_config as logger_config
import logging
from shared_functions.shared_functions import git_tag
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class AdEmail(object):
    """
    Send email to recipient via SMTP

    Attributes
        logger : (logging.Logger)
            Logger object
        log_flags : (dict)
            Flags used in log messages
        log_msgs : (dict)
            Messages used in logging
        sender : (str)
            Email address of sender
        email_user : (str)
            Email username
        email_pw : (str)
            Email password

    Methods
        generate_email_html()
            Renders the html string for the email message
        send_email()
            Create email message object and specify settings, then send email using
            mail settings from init
    """

    def __init__(self, logger: logging.Logger):
        """
        Constructor for the AdEmail class
            :param logger:  Logger object
        """
        self.logger = logger
        self.log_flags = logger_config.LOG_FLAGS
        self.log_msgs = logger_config.LOG_MSGS["ad_email"]
        self.sender = ad_config.MAIL_SETTINGS["alerts_email"]
        with open(
            ad_config.CREDENTIALS["email_user"], "r", encoding="utf-8"
        ) as email_user_file:
            self.email_user = email_user_file.readline().rstrip()  # Get email username
        with open(
            ad_config.CREDENTIALS["email_pw"], "r", encoding="utf-8"
        ) as email_pw_file:
            self.email_pw = email_pw_file.readline().rstrip()  # Get email password
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(ad_config.TEMPLATE_DIR),
            autoescape=True,
        ).get_template(ad_config.EMAIL_TEMPLATE)

    # TODO write test for this function
    def generate_email_html(
            self, runfolder_name: str, workflows: str, queries: str, sample_count: int
            ) -> str:
        """
        Generate HTML
            :param runfolder_name (str):    Name of runfolder
            :workflows (str):               Comma separated string of workflow names
            :queries (str):                 \n separated string of SQL queries
            :sample_count (int):            Total number of samples processed
            :return html (str):             Rendered html as a string
        """
        try:
            html = self.template.render(
                test_mode=ad_config.TESTING,
                runfolder_name=runfolder_name,
                workflows=workflows,
                queries=queries,
                sample_count=sample_count,
                git_tag=git_tag(),
            )
            self.logger.info(
                self.log_msgs["html_success"],
                extra={"flag": self.log_flags["info"] % "email"},
            )
            return html
        except Exception as exception:
            self.logger.exception(
                self.log_msgs["html_error"],
                exception,
                extra={"flag": self.log_flags["info"] % "email"},
            )

    def send_email(
        self, recipients: list, email_subject: str, email_message: str,
        email_priority: int
    ) -> True:
        """
        Create email message object and specify settings, then send email using mail
        settings from init
            :param (list|str) recipients:   List or string of recipient email addresses
            :param str email_subject:       Email subject string
            :param str email_message:       Email message string
            :param email_priority:          Email priority integer
        """
        self.msg = MIMEMultipart()  # Create email message object and specify settings
        self.msg["X-Priority"] = str(email_priority)  # Set email priority. 1 is highest
        try:
            recipients = ", ".join(recipients)

            self.msg["Subject"] = email_subject
            self.msg["From"] = self.sender
            self.msg["To"] = recipients
            self.msg.attach(MIMEText(email_message, "html"))  # Add msg to e-mail body
            self.logger.info(
                self.log_msgs["sending_email"],
                self.msg,
                extra={"flag": self.log_flags["info"] % "email"},
            )
            # Configure SMTP server connection for sending email
            server = smtplib.SMTP(
                host=ad_config.MAIL_SETTINGS["host"],
                port=ad_config.MAIL_SETTINGS["port"],
                timeout=10,
            )
            server.set_debuglevel(False)  # Output connection debug messages
            server.starttls()  # Encrypt SMTP commands using Transport Layer Security
            server.ehlo()  # Identify client to ESMTP server using EHLO commands
            server.login(self.email_user, self.email_pw)
            server.sendmail(self.sender, recipients, self.msg.as_string())
            self.logger.info(
                self.log_msgs["email_success"],
                extra={"flag": self.log_flags["info"] % "email"},
            )
            return True

        except Exception as exception:
            self.logger.exception(
                self.log_msgs["email_fail"],
                exception,
                extra={"flag": self.log_flags["fail"] % "email"},
            )
