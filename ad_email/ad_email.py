""" NEED TO MODIFY THIS AND SET UP TO WORK WITH ADLOGGER, THEN CHANGE THE UPLOAD AND SETOFF
WORKFLOWS SCRIPT

NEED TO CHECK EMAIL RECIPIENTS ARE CORRECT

NEED TO ADD LOGGING FUNCTIONALITY BACK

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

        self.email_priority = email_priority
        self.sender = config.mokalerts_email
        self.server = ''

        # Create email message object and specify settings
        self.msg = Message()
        self.msg['X-Priority'] = str(self.email_priority)  # Set email priority. 1 is highest

    def send_email(self, recipients, email_subject, email_message):
        """ Send email using mail settings from init """
        try:
            self.logger.info(config.email_logmsgs['email_sending'], self.sender, email_subject,
                             email_message, extra={'flag': config.log_flags['info']})

            self.msg['Subject'] = email_subject
            # Add messages to e-mail body using email.Message.set_payload()
            self.msg.set_payload(email_message)

            # Configure SMTP server connection for sending log messages via e-mail
            self.server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
            self.server.set_debuglevel(False)  # Output connection debug messages
            self.server.starttls()  # Encrypt SMTP commands using Transport Layer Security mod
            self.server.ehlo()  # Identify client to ESMTP server using EHLO commands
            self.server.login(config.user, config.pw)  # Login to server with user credentials
            # Send email to server
            self.server.sendmail(self.sender, [recipients], self.msg.as_string())
            self.logger.info(config.email_logmsgs['email_pass'], extra={'flag': config.log_flags['info']})
            return True

        except Exception as exception:
            self.logger.error(config.email_logmsgs['email_fail'], exception,
                              extra={'flag': config.log_flags['fail']})
