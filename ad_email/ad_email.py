#!/usr/bin/python3
# coding=utf-8
"""
Email sending module
"""
import os
import jinja2
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Union
from config import ad_config
from toolbox import toolbox


class AdEmail(object):
    """
    Send email to recipient via SMTP

    Attributes
        logger (logging.Logger):    Logger object
        sender (str):               Email address of sender
        email_user (str):           Email username
        email_pw (str):             Email password
        template_dirpath (str):     Path to the email template
        template (obj):             Loaded template

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
            :param logger:              Logger object
        """
        self.logger = logger
        self.sender = ad_config.MAIL_SETTINGS["alerts_email"]
        with open(
            ad_config.CREDENTIALS["email_user"], "r", encoding="utf-8"
        ) as email_user_file:
            self.email_user = email_user_file.readline().rstrip()  # Get email username
        with open(
            ad_config.CREDENTIALS["email_pw"], "r", encoding="utf-8"
        ) as email_pw_file:
            self.email_pw = email_pw_file.readline().rstrip()  # Get email password
        self.template_dirpath = os.path.join(
            ad_config.PROJECT_DIR, "ad_email/templates"
        )
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dirpath),
            autoescape=True,
        ).get_template("email.html")

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
                git_tag=toolbox.git_tag(),
            )
            self.logger.info(self.logger.log_msgs["html_success"])
            return html
        except Exception as exception:
            self.logger.exception(self.logger.log_msgs["html_error"], exception)

    def send_email(
        self,
        recipients: list,
        email_subject: str,
        email_message: str,
        email_priority: int,
    ) -> Union[bool, None]:
        """
        Create email message object and specify settings, then send email using mail
        settings from init
            :param recipients (list|str):   List or string of recipient email addresses
            :param email_subject (str):     Email subject string
            :param email_message (str):     Email message string
            :param email_priority (int):    Email priority integer
            :return True | None:            True if email successfully sent, else None
        """
        self.msg = MIMEMultipart()  # Create email message object and specify settings
        self.msg["X-Priority"] = str(email_priority)  # Set email priority. 1 is highest
        try:
            recipients = ", ".join(recipients)

            self.msg["Subject"] = email_subject
            self.msg["From"] = self.sender
            self.msg["To"] = recipients
            self.msg.attach(MIMEText(email_message, "html"))  # Add msg to e-mail body
            self.logger.info(self.logger.log_msgs["sending_email"], self.msg)
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
            self.logger.info(self.logger.log_msgs["email_success"])
            return True

        except Exception as exception:
            self.logger.exception(self.logger.log_msgs["email_fail"], exception)
            raise Exception  # Stop script
