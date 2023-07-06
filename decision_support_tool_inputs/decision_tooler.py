"""
Print inputs required by decision support tool upload applications on DNAnexus.
See Readme and doctrings for further details
"""
import config.ad_config as ad_config
from shared_functions.shared_functions import execute_subprocess_command, git_tag


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
    Builds decision support tool command line inputs

    Attributes
        dnanexus_apikey(str):       DNAnexus auth token
        project(str):               DNAnexus project ID
        workflow(str):              Name of pipeline used to process the sample
        file_dict(dict):            Dictionary containing strings required for building
                                    the congenica upload app input string
        loggers(object):            Script level logger for the script
        vcfjobid_cmd(str):          Command for retrieving the VCF creation job ID
        bamjobid_cmd(str):          Command for retrieving the BAM creation job ID
        baijobid_cmd(str):          Commmand for retrieving the BAI creation job ID
        bamjobid(str):              BAM job ID
        vcfjobid(str):              VCF job ID
        baijobid(str):              BAI job ID
        congenica_app_inputs(str):  Input string for the congenica app

    Methods
        return_file_dict()
            Return file dict of congenica upload inputs if workflow is valid (requires
            congenica upload), else raise exception
        set_jobid_cmds()
            Set commands for retrieving the job ID for the vcf and bam workflow stages
        get_jobids()
            Get job ids for bam and vcf jobs within the workflow
        set_app_input_string()
            Set the input string for the congenica app
        printer()
            Print inputs to decision support upload app (congenica upload)
    """
    def __init__(self, analysis_id: str, project: str, workflow: str, logger: object):
        """
        Constructor for the DecisionTooler class
            :param analysis_id (str):   Workflow analysis ID
            :param project (str):       DNAnexus project ID
            :param workflow (str):      Workflow used to analyse the sample
            :param logger (object):     Logger object
        """
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token
        self.analysis_id = analysis_id
        self.project = project
        self.workflow = workflow
        self.logger = logger
        self.logger.info(
            self.logger.log_msgs["script_start"],
            git_tag(),
            "decision_support_tool_inputs.py",
            extra={"flag": self.logger.log_flags["info"] % "dst"},
        )
        self.file_dict = self.return_file_dict()
        self.set_jobid_cmds()
        self.get_jobids()
        self.set_app_input_string()

    def return_file_dict(self) -> dict:
        """
        Return file dict of congenica upload inputs if workflow is valid (requires
        congenica upload), else raise exception
            :return (dict): Dictionary of congenica upload inputs
        """
        if self.workflow in ["wes", "pipe"]:
            self.logger.info(
                self.logger.log_msgs["workflow_type"],
                self.workflow,
                extra={"flag": self.logger.log_flags["info"] % "dst"},
            )
            return DECISION_SUPPORT_INPUTS[self.workflow]
        else:
            self.logger.exception(
                self.logger.log_msgs["incorrect_workflow"],
                self.workflow,
                extra={"flag": self.logger.log_flags["fail"] % "dst"},
            )
            raise Exception

    def set_jobid_cmds(self) -> None:
        """
        Set the commands for retrieving the job ID for the vcf and bam workflow stages
            :return None:
        """
        self.logger.info(
                self.logger.log_msgs["setting_job_id_cmds"],
                extra={"flag": self.logger.log_flags["info"] % "dst"},
            )
        try:
            for file_name in self.file_dict.keys():
                find_execution_id_cmd = ad_config.DX_CMDS['find_execution_id'] % (
                    f"{self.project}:{self.analysis_id}",
                    self.dnanexus_apikey, self.file_dict[file_name]['stage']
                    )
                setattr(self, f"{file_name}jobid_cmd", find_execution_id_cmd)
        except Exception as exception:
            self.logger.exception(
                self.logger.log_msgs["setting_job_id_cmds_err"],
                exception,
                extra={"flag": self.logger.log_flags["fail"] % "dst"},
            )

    def get_jobids(self) -> None:
        """
        Get job ids for bam and vcf jobs within the workflow by executing the job id
        retrieval commands. Set as class attributes.
            :return None:
        """
        for outfile in self.file_dict.keys():
            self.logger.info(
                self.logger.log_msgs["get_job_id"], outfile,
                extra={"flag": self.logger.log_flags["info"] % "dst"},
            )
            jobid = False
            returncode = 1
            tries = 0
            jobid_cmd = getattr(self, f"{outfile}jobid_cmd")
            while returncode != 0 and not jobid:
                try:
                    jobid, err, returncode = execute_subprocess_command(
                        jobid_cmd, self.logger
                        )
                    self.logger.info(
                        self.logger.log_msgs["found_job_id"], outfile,
                        jobid,
                        extra={"flag": self.logger.log_flags["info"] % "dst"},
                    )
                    setattr(self, f"{outfile}jobid", jobid)
                except Exception as exception:
                    self.logger.info(
                        self.logger.log_msgs["get_job_id_err"],
                        outfile, exception,
                        extra={"flag": self.logger.log_flags["info"] % "dst"},
                    )
                    tries += 1
                    if tries == 1000:  # Can take a while for job to set off
                        self.logger.exception(
                            self.logger.log_msgs[
                                "get_job_id_fail"
                                ],
                            outfile, exception,
                            extra={"flag": self.logger.log_flags["fail"] % "dst"},
                        )

    def set_app_input_string(self) -> None:
        """
        Set the input string for the congenica app
            :return None:
        """
        try:
            self.logger.info(
                self.logger.log_msgs["setting_app_input_str"],
                extra={"flag": self.logger.log_flags["info"] % "dst"},
            )
            congenica_app_inputs = (
                f"{ad_config.APP_INPUTS['congenica_upload']['vcf']}"
                f"{self.vcfjobid}:{self.file_dict['vcf']['name']} "
                f"{ad_config.APP_INPUTS['congenica_upload']['bam']}"
                f"{self.bamjobid}:{self.file_dict['bam']['name']}"
            )
            setattr(self, 'congenica_app_inputs', congenica_app_inputs)
        except Exception as exception:
            self.logger.exception(
                self.logger.log_msgs["app_input_str_err"],
                exception,
                extra={"flag": self.logger.log_flags["fail"] % "dst"},
            )

    def printer(self) -> str:
        """
        Print inputs to decision support upload app (congenica upload)
            :return (str):  Bam and vcf congenica app inputs in string format
        """
        self.logger.info(
            self.logger.log_msgs["printing_app_input_str"],
            extra={"flag": self.logger.log_flags["info"] % "dst"},
        )
        print(self.congenica_app_inputs)
