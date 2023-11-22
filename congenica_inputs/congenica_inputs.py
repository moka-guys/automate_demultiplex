"""
Print inputs required by congenica upload applications on DNAnexus.
See Readme and doctrings for further details
"""
from config import ad_config
import toolbox.toolbox as toolbox
import ad_logger.ad_logger as ad_logger


# Used by the script to build the input commands for the congenica upload app
DECISION_SUPPORT_INPUTS = {
    "pipe": {
        "vcf": {
            "stage": ad_config.NEXUS_IDS['STAGES']['pipe']['filter_vcf'],
            "name": "filtered_vcf",
        },
        "bam": {
            "stage": ad_config.NEXUS_IDS['STAGES']['pipe']['gatk'],
            "name": "bam",
        },
        "bai": {
            "stage": ad_config.NEXUS_IDS['STAGES']['pipe']['gatk'],
            "name": "bai",
        },
    },
    # Same stage is used to produce both the BAM and VCF
    "wes": {
        "vcf": {
            "stage": ad_config.NEXUS_IDS['STAGES']['wes']['sentieon'],
            "name": "variants_vcf",
        },
        "bam": {
            "stage": ad_config.NEXUS_IDS['STAGES']['wes']['sentieon'],
            "name": "mappings_bam",
        },
        "bai": {
            "stage": ad_config.NEXUS_IDS['STAGES']['wes']['sentieon'],
            "name": "mappings_bam_bai",
        },
    },
}


class DecisionTooler(object):
    """
    Builds congenica upload DNAnexus app command line inputs

    Attributes
        dnanexus_apikey(str):       DNAnexus auth token
        analysis_id (str):          Workflow analysis ID
        project(str):               DNAnexus project ID
        runfolder_name (str):       Name of runfolder (used for naming logfile)
        workflow (str):             Name of pipeline used to process the sample
        logger (object):            Runfolder-level logger
        file_dict(dict):            Dictionary containing strings required for building
                                    the congenica upload app input string
        vcfjobid_cmd(str):          Command for retrieving the VCF creation job ID
        bamjobid_cmd(str):          Command for retrieving the BAM creation job ID
        baijobid_cmd(str):          Commmand for retrieving the BAI creation job ID
        bamjobid(str):              BAM job ID
        vcfjobid(str):              VCF job ID
        baijobid(str):              BAI job ID
        congenica_app_inputs(str):  Input string for the congenica app

    Methods
        get_inputs()
            Call methods to generate the congenica upload DNAnexus app input string
        get_file_dict()
            Get file dict of DNAnexus app inputs if workflow is valid (requires
            congenica upload), else raise exception
        set_jobid_cmds()
            Set commands for retrieving the job ID for the vcf and bam workflow stages
        get_jobids()
            Get job ids for bam and vcf jobs within the workflow and set as class
            attributes
        set_app_input_string()
            Set the input string for the congenica app as class attribute
        printer()
            Print inputs to congenica upload app (bam and vcf congenica app inputs
            in string format)
    """
    def __init__(
        self, analysis_id: str, project: str, runfolder_name: str, workflow: str
    ):
        """
        Constructor for the DecisionTooler class
            :param analysis_id (str):       Workflow analysis ID
            :param project (str):           DNAnexus project ID
            :param runfolder_name (str):    Name of runfolder (used for naming logfile)
            :param workflow (str):          Workflow used to analyse the sample
        """
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token

        self.analysis_id = analysis_id
        self.project = project
        self.runfolder_name = runfolder_name
        self.workflow = workflow
        self.logger = self.return_logger()

    def return_logger(self) -> object:
        """
        Add only the required logger
            :return logger (object):    Runfolder-level logger
        """
        rf_obj = toolbox.RunfolderObject(
            self.runfolder_name, ad_config.TIMESTAMP
        )
        rf_obj.add_runfolder_logger('decision_support')  # Add decision_support logger
        logger = rf_obj.rf_loggers.decision_support
        ad_logger.shutdown_streamhandler(logger)  # Prevents log
        return logger

    def get_inputs(self) -> None:
        """
        Call methods to generate the congenica upload DNAnexus app input string
            :return None:
        """
        self.get_file_dict()
        self.set_jobid_cmds()
        self.get_jobids()
        self.set_app_input_string()
        self.printer()

    def get_file_dict(self) -> dict:
        """
        Get file dict of DNAnexus app inputs if workflow is valid (requires
        congenica upload), else raise exception
            :return (dict): Dictionary of congenica upload app inputs
        """
        if self.workflow in ["wes", "pipe"]:
            self.logger.info(
                self.logger.log_msgs["workflow_type"], self.workflow
            )
            setattr(self, 'file_dict', DECISION_SUPPORT_INPUTS[self.workflow])
        else:
            self.logger.error(self.logger.log_msgs["incorrect_workflow"], self.workflow)
            raise Exception

    def set_jobid_cmds(self) -> None:
        """
        Set the commands for retrieving the job ID for the vcf and bam workflow stages
            :return None:
        """
        self.logger.info(self.logger.log_msgs["setting_job_id_cmds"])
        try:
            for file_name in self.file_dict.keys():
                find_execution_id_cmd = ad_config.DX_CMDS['find_execution_id'] % (
                    f"{self.project}:{self.analysis_id}",
                    self.dnanexus_apikey, self.file_dict[file_name]['stage']
                    )
                setattr(self, f"{file_name}jobid_cmd", find_execution_id_cmd)
        except Exception as exception:
            self.logger.exception(
                self.logger.log_msgs["setting_job_id_cmds_err"], exception,
            )
            raise Exception  # Stop script

    def get_jobids(self) -> None:
        """
        Get job ids for bam and vcf jobs within the workflow by executing the job id
        retrieval commands. Set as class attributes.
            :return None:
        """
        for outfile in self.file_dict.keys():
            self.logger.info(self.logger.log_msgs["get_job_id"], outfile)
            tries, returncode = 0, 1
            jobid_cmd = getattr(self, f"{outfile}jobid_cmd")
            # Can take a while for job to set off
            while tries < 1000 and returncode != 0:
                (
                    jobid, err, returncode
                ) = toolbox.execute_subprocess_command(
                    jobid_cmd, self.logger,
                )
                if returncode == 0:
                    self.logger.info(
                        self.logger.log_msgs["found_job_id"], outfile, jobid
                    )
                    setattr(self, f"{outfile}jobid", jobid)
                else: 
                    tries += 1
                    self.logger.warning(
                        self.logger.log_msgs["get_job_id_err"], outfile, err
                    )
            if tries > 1000:
                self.logger.exception(
                        self.logger.log_msgs["get_job_id_fail"], outfile
                    )
                raise Exception

    def set_app_input_string(self) -> None:
        """
        Set the input string for the congenica app as class attribute
            :return None:
        """
        try:
            self.logger.info(self.logger.log_msgs["setting_app_input_str"])
            congenica_app_inputs = (
                f"{ad_config.APP_INPUTS['congenica_upload']['vcf']}"
                f"{self.vcfjobid}:{self.file_dict['vcf']['name']} "
                f"{ad_config.APP_INPUTS['congenica_upload']['bam']}"
                f"{self.bamjobid}:{self.file_dict['bam']['name']}"
            )
            setattr(self, 'congenica_app_inputs', congenica_app_inputs)
        except Exception as exception:
            self.logger.exception(self.logger.log_msgs["app_input_str_err"], exception)
            raise Exception  # Stop script

    def printer(self) -> None:
        """
        Print inputs to congenica upload app (bam and vcf congenica
        app inputs in string format)
            :return None:  
        """
        self.logger.info(self.logger.log_msgs["printing_app_input_str"])
        print(self.congenica_app_inputs)
