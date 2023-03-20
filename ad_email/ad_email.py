""" NEED TO MODIFY THIS AND SET UP TO WORK WITH ADLOGGER, THEN CHANGE THE UPLOAD AND SETOFF
WORKFLOWS SCRIPT

Email needs to take multiple email addresses as input as a list
"""
import smtplib
from email.message import Message
import ad_config as config


class AdEmail(object):
    """
    Send email to recipient via SMTP

    Methods:
        send_email()
            Send email using mail settings from init
    """
    def __init__(self, email_priority, logger):
        '''
        Input = logger, email_priority
        Uses smtplib to send an email.
        Returns = None
        '''
        self.logger = logger
        self.sender = config.MOKA_ALERTS_EMAIL
        # Create email message object and specify settings
        self.msg = Message()
        self.msg['X-Priority'] = str(email_priority)  # Set email priority. 1 is highest

    def send_email(self, recipients, email_subject, email_message):
        """ Send email using mail settings from init """
        try:
            self.logger.info(config.LOG_MSGS['email']['email_sending'], self.sender, email_subject,
                             email_message, extra={'flag': config.LOG_FLAGS['info']})

            self.msg['Subject'] = email_subject
            # Add messages to e-mail body using email.Message.set_payload()
            self.msg.set_payload(email_message)

            # Configure SMTP server connection for sending log messages via e-mail
            server = smtplib.SMTP(host=config.HOST, port=config.PORT, timeout=10)
            server.set_debuglevel(False)  # Output connection debug messages
            server.starttls()  # Encrypt SMTP commands using Transport Layer Security mod
            server.ehlo()  # Identify client to ESMTP server using EHLO commands
            server.login(config.EMAIL_USER, config.EMAIL_PW)  # Login to server with user credentials
            # Send email to server
            server.sendmail(self.sender, [recipients], self.msg.as_string())
            self.logger.info(config.LOG_MSGS['email']['email_pass'],
                             extra={'flag': config.LOG_FLAGS['info']})
            return True

        except Exception as exception:
            self.logger.error(config.LOG_MSGS['email']['email_fail'], exception,
                              extra={'flag': config.LOG_FLAGS['fail']})
