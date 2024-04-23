#!/usr/bin/python3
# coding=utf-8
"""
Email sending module. See Readme and docstrings for further details.
Contains the following classes:

- AdEmail
    Send email to recipient via SMTP
"""
import sys
import os
import jinja2
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from config.ad_config import AdEmailConfig
from toolbox.toolbox import get_credential, git_tag


class AdEmail(AdEmailConfig):
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
        generate_email_html(runfolder_name, workflows, queries, sample_count, samples)
            Renders the html string for the email message
        send_email(recipients, email_subject, email_message, email_priority)
            Create email message object and specify settings, then
            send email using mail settings from init
    """

    def __init__(self, logger: logging.Logger):
        """
        Constructor for the AdEmail class
            :param logger:  Logger object
        """
        self.logger = logger
        self.sender = AdEmailConfig.MAIL_SETTINGS["alerts_email"]
        self.email_user = get_credential(AdEmailConfig.CREDENTIALS["email_user"])
        self.email_pw = get_credential(AdEmailConfig.CREDENTIALS["email_pw"])
        self.template_dirpath = os.path.join(
            AdEmailConfig.PROJECT_DIR, "ad_email/templates"
        )
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dirpath),
            autoescape=True,
        ).get_template("email.html")

    def generate_email_html(
        self,
        runfolder_name: str,
        workflows: str,
        queries: str,
        sample_count: int,
        samples: list,
    ) -> str:
        """
        Generate HTML. If unsuccessful, exit script
            :param runfolder_name (str):    Name of runfolder
            :workflows (str):               Comma separated string of workflow names
            :queries (list):                List of SQL queries
            :sample_count (int):            Total number of samples processed
            :samples (list):                List of sample names being processed by the pipeline
            :return html (str):             Rendered html as a string
        """
        try:
            html = self.template.render(
                test_mode=AdEmailConfig.TESTING,
                runfolder_name=runfolder_name,
                workflows=workflows,
                queries=queries,
                sample_count=sample_count,
                samples=samples,
                git_tag=git_tag(),
            )
            self.logger.info(self.logger.log_msgs["html_success"])
            return html
        except Exception as exception:
            self.logger.error(self.logger.log_msgs["html_error"], exception)
            sys.exit(1)  # TODO move this to the next level up and only for some emails

    def send_email(
        self,
        recipients: list,
        email_subject: str,
        email_message: str,
        email_priority: int,
    ) -> Optional[bool]:
        """
        Create email message object and specify settings, then send email using mail
        settings from init. If unsuccessful, exit script
            :param recipients (list):       List of recipient email addresses
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
            with smtplib.SMTP(
                host=AdEmailConfig.MAIL_SETTINGS["host"],
                port=AdEmailConfig.MAIL_SETTINGS["port"],
                timeout=10,
            ) as server:
                server.set_debuglevel(False)  # Output connection debug messages
                server.starttls()  # Encrypt SMTP commands using Transport Layer Security
                server.ehlo()  # Identify client to ESMTP server using EHLO commands
                server.login(self.email_user, self.email_pw)
                server.sendmail(self.sender, recipients, self.msg.as_string())
                self.logger.info(self.logger.log_msgs["email_success"])
                return True
        except Exception as exception:
            self.logger.error(self.logger.log_msgs["email_fail"], exception)
            sys.exit(1)  # TODO move this to the next level up and only for some emails
