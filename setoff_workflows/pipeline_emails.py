"""pipeline_emails.py

Contains the PipelineEmails class for sending the start of pipeline emails.
Calls the AdEmail class for email sending. The following emails are sent:
    - Pipeline started email. Contains SQL queries used to update the Moka database
    - Samples being processed email
"""

import logging
from config.ad_config import SWConfig
from ad_email.ad_email import AdEmail
from toolbox.toolbox import RunfolderObject, RunfolderSamples


class PipelineEmails(SWConfig):
    """
    Class for sending the start of pipeline emails. Calls the AdEmail class for email
    sending. The following emails are sent:

        - SQL emails for all pipelines. These are sent to binfx. This is because
            samples processed using each workflow are recorded in Moka using an
            insert query per sample
        - Emails with details of the samples being processed. These are sent to binfx
            for all runs, plus to additional recipients as defined within the
            config.ad_config file

        Attributes
            rf_obj (obj):           RunfolderObject object (contains runfolder-specific attributes)
            workflows (list):       List of names of all workflows used to process samples within the run
            sample_count (int):     Number of samples in the run
            email_subj (str):       Email subject used by all emails sent within this class
            email (obj):            AdEmail object (contains methods for sending emails)
            queries (str):          Newline-separated string of SQL queries

        Methods
            send_sql_email()
                Construct and send pipeline started email using the AdEmail class
            send_samples_email()
                Construct and send the samples being processed email using AdEmail class
    """

    def __init__(
        self,
        rf_obj: RunfolderObject,
        rf_samples_obj: RunfolderSamples,
        sql_queries: str,
        logger: logging.Logger,
    ):
        """
        Constructor for the PipelineEmails class. Calls the class methods
        """
        self.rf_obj = rf_obj
        self.logger = logger
        self.rf_samples_obj = rf_samples_obj
        self.sql_queries = sql_queries
        self.sample_count = len(self.rf_samples_obj.samples_dict)
        self.email_subj = (
            SWConfig.MAIL_SETTINGS["pipeline_started_subj"] % self.rf_obj.runfolder_name
        )
        self.email = AdEmail(self.logger)

    def send_sql_email(self) -> None:
        """
        Construct and send pipeline started email using the AdEmail class. Email is sent
        to the binfx team. Contains SQL queries used to update the Moka database.
        Logging is carried out within the AdEmail class
            :return None:
        """
        email_html = self.email.generate_email_html(
            self.rf_obj.runfolder_name,
            self.rf_samples_obj.pipeline,
            " <br> ".join(self.sql_queries),
            self.sample_count,
            False,
        )
        self.email.send_email(
            recipients=[SWConfig.MAIL_SETTINGS["binfx_recipient"]],
            email_subject=self.email_subj,
            email_message=email_html,
            email_priority=1,
        )

    def send_samples_email(self) -> None:
        """
        Construct and send the samples being processed email using the AdEmail class.
        Email is sent to the binfx team and other relevant parties dependent upon the
        pipeline. Contains details to inform the relevant parties that the pipeline has
        been started. Logging is carried out within the AdEmail class
            :return None:
        """
        email_html = self.email.generate_email_html(
            self.rf_obj.runfolder_name,
            self.rf_samples_obj.pipeline,
            False,
            self.sample_count,
            " <br> ".join(self.rf_samples_obj.samples_dict.keys()),
        )
        recipients = [SWConfig.MAIL_SETTINGS["binfx_recipient"]]
        if self.rf_samples_obj.pipeline == "wes":
            recipients.extend(SWConfig.MAIL_SETTINGS["wes_samplename_emaillist"])
        elif self.rf_samples_obj.pipeline in ["tso500", "archerdx", "oncodeep"]:
            recipients.append(SWConfig.MAIL_SETTINGS["oncology_ops_email"])
        self.email.send_email(
            recipients=recipients,
            email_subject=self.email_subj,
            email_message=email_html,
            email_priority=1,
        )
