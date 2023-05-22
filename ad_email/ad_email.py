""" Email sending module
"""
import smtplib
from email.message import Message
import config.ad_config as ad_config

# TODO incorporate traceback into logging - import traceback


class AdEmail(object):
    """
    Send email to recipient via SMTP

    Methods:
        send_email()
            Send email using mail settings from init
    """

    def __init__(self, logger):
        """
        Input = logger, email_priority
        Uses smtplib to send an email.
        Returns = None
        """
        self.logger = logger
        self.sender = ad_config.MAIL_SETTINGS["alerts_email"]
        # Get email username
        with open(
            ad_config.CREDENTIALS["email_user"], "r", encoding="utf-8"
        ) as email_user_file:
            self.email_user = email_user_file.readline().rstrip()
        # Get email password
        with open(
            ad_config.CREDENTIALS["email_pw"], "r", encoding="utf-8"
        ) as email_pw_file:
            self.email_pw = email_pw_file.readline().rstrip()

    def send_email(self, recipients, email_subject, email_message, email_priority):
        """Send email using mail settings from init"""
        # Create email message object and specify settings
        self.msg = Message()
        # Set email priority. 1 is highest
        self.msg["X-Priority"] = str(email_priority)
        try:
            self.logger.info(
                "Sending an email. Recipient: %s. Subject: %s. Body: %s",
                self.sender,
                email_subject,
                email_message,
                extra={"flag": self.loggers.log_flags["email"]["info"]},
            )
            if type(recipients) == list:
                recipients = ", ".join(list(recipients))

            self.msg["Subject"] = email_subject
            self.msg["From"] = self.sender
            self.msg["To"] = recipients

            self.msg.set_payload(email_message)  # Add messages to e-mail body
            self.logger.info(
                "Sending the email message: %s",
                self.msg,
                extra={"flag": self.loggers.log_flags["email"]["info"]},
            )
            # Configure SMTP server connection for sending email
            server = smtplib.SMTP(
                host=ad_config.MAIL_SETTINGS["host"],
                port=ad_config.MAIL_SETTINGS["port"],
                timeout=10,
            )
            # Output connection debug messages
            server.set_debuglevel(False)
            # Encrypt SMTP commands using Transport Layer Security
            server.starttls()
            # Identify client to ESMTP server using EHLO commands
            server.ehlo()
            # Login to server with user credentials
            server.login(self.email_user, self.email_pw)
            # Send email to server
            server.sendmail(self.sender, recipients, self.msg.as_string())
            self.logger.info(
                "Email sent successfully",
                extra={"flag": self.loggers.log_flags["email"]["success"]},
            )
            return True

        except Exception as exception:
            self.logger.exception(
                "ERROR - Email not sent. Exception: %s",
                exception,
                extra={"flag": self.loggers.log_flags["email"]["fail"]},
            )
