"""
Print inputs required by Congenica upload applications on DNAnexus.
See Readme and doctrings for further details. Contains the following classes:

- CongenicaInputs
    Builds Congenica upload DNAnexus app command line inputs
"""
import sys
import time
from config.ad_config import CongenicaInputsConfig
from toolbox.toolbox import get_credential, RunfolderObject, execute_subprocess_command
from ad_logger.ad_logger import shutdown_streamhandler

# TODO simplify this so it e.g. takes just a sample name as input and outputs the entire command as string

class CongenicaInputs(CongenicaInputsConfig):
    """
    Builds Congenica upload DNAnexus app command line inputs

    Attributes
        dnanexus_auth (str):        DNAnexus auth token
        analysis_id (str):          Workflow analysis ID
        project(str):               DNAnexus project ID
        runfolder_name (str):       Name of runfolder (used for naming logfile)
        workflow (str):             Name of pipeline used to process the sample
        rf_obj (object):            RunfolderObject() object (contains runfolder-specific attributes)
        logger (object):            Runfolder-level logger
        file_dict(dict):            Dictionary containing strings required for building
                                    the Congenica upload app input string
        vcfjobid_cmd(str):          Command for retrieving the VCF creation job ID
        bamjobid_cmd(str):          Command for retrieving the BAM creation job ID
        baijobid_cmd(str):          Commmand for retrieving the BAI creation job ID
        bamjobid(str):              BAM job ID
        vcfjobid(str):              VCF job ID
        baijobid(str):              BAI job ID
        congenica_app_inputs(str):  Input string for the Congenica app

    Methods
        get_inputs()
            Call methods to generate the Congenica upload DNAnexus app input string
        get_file_dict()
            Get file dict of DNAnexus app inputs if workflow is valid (requires
            Congenica upload), else exit script
        set_jobid_cmds()
            Set commands for retrieving the job ID for the vcf and bam workflow stages
        get_jobids()
            Get job ids for bam and vcf jobs within the workflow and set as class
            attributes
        set_app_input_string()
            Set the input string for the Congenica app as class attribute
        printer()
            Print inputs to Congenica upload app (bam and vcf Congenica app inputs
            in string format)
    """

    def __init__(
        self, analysis_id: str, project: str, runfolder_name: str, workflow: str
    ):
        """
        Constructor for the CongenicaInputs class
            :param analysis_id (str):       Workflow analysis ID
            :param project (str):           DNAnexus project ID
            :param runfolder_name (str):    Name of runfolder (used for naming logfile)
            :param workflow (str):          Workflow used to analyse the sample
        """
        self.dnanexus_auth = get_credential(CongenicaInputsConfig.CREDENTIALS["dnanexus_authtoken"])  # Auth token
        self.analysis_id = analysis_id
        self.project = project
        self.runfolder_name = runfolder_name
        self.workflow = workflow
        self.rf_obj = RunfolderObject(self.runfolder_name, CongenicaInputsConfig.TIMESTAMP)
        self.logger = self.return_logger()

    def return_logger(self) -> object:
        """
        Add only the required logger
            :return logger (object):    Runfolder-level logger
        """
        self.rf_obj.add_runfolder_logger("decision_support")  # Add decision_support logger
        logger = self.rf_obj.rf_loggers.decision_support
        shutdown_streamhandler(logger)  # Prevents log
        return logger

    def get_inputs(self) -> None:
        """
        Call methods to generate the Congenica upload DNAnexus app input string
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
        Congenica upload), else exit script
            :return (dict): Dictionary of Congenica upload app inputs
        """
        if self.workflow in ["wes", "pipe"]:
            self.logger.info(self.logger.log_msgs["workflow_type"], self.workflow)
            setattr(self, "file_dict", CongenicaInputsConfig.DECISION_SUPPORT_INPUTS[self.workflow])
        else:
            self.logger.error(self.logger.log_msgs["incorrect_workflow"], self.workflow)
            sys.exit(1)

    def set_jobid_cmds(self) -> None:
        """
        Set the commands for retrieving the job ID for the vcf and bam workflow stages.
        If unsuccessful, exit script
            :return None:
        """
        self.logger.info(self.logger.log_msgs["setting_job_id_cmds"])
        try:
            for file_name in self.file_dict.keys():
                find_execution_id_cmd = CongenicaInputsConfig.DX_CMDS["find_execution_id"] % (
                    f"{self.project}:{self.analysis_id}",
                    self.dnanexus_auth,
                    self.file_dict[file_name]["stage"],
                )
                setattr(self, f"{file_name}jobid_cmd", find_execution_id_cmd)
        except Exception as exception:
            self.logger.error(
                self.logger.log_msgs["setting_job_id_cmds_err"],
                exception,
            )
            sys.exit(1)

    def get_jobids(self) -> None:
        """
        Get job ids for bam and vcf jobs within the workflow by executing the job id
        retrieval commands. Set as class attributes. If unsuccessful, exit script
            :return None:
        """
        for outfile in self.file_dict.keys():
            self.logger.info(self.logger.log_msgs["get_job_id"], outfile)
            max_tries = 20
            tries, returncode = 0, 1
            jobid_cmd = getattr(self, f"{outfile}jobid_cmd")
            # Can take a while for job to set off
            while tries < max_tries:
                (jobid, err, returncode) = execute_subprocess_command(
                    jobid_cmd,
                    self.logger,
                )
                if err:
                    self.logger.info(
                        self.logger.log_msgs["get_job_id_err"], outfile, err, tries
                    )
                    tries += 1
                    time.sleep(10)
                else:
                    self.logger.info(
                        self.logger.log_msgs["found_job_id"], outfile, jobid
                    )
                    setattr(self, f"{outfile}jobid", jobid)
                    break                    
            if tries == max_tries and err:
                self.logger.error(self.logger.log_msgs["get_job_id_fail"], max_tries, outfile)
                sys.exit(1)

    def set_app_input_string(self) -> None:
        """
        Set the input string for the Congenica app as class attribute. If
        unsuccessful, exit script
            :return None:
        """
        try:
            self.logger.info(self.logger.log_msgs["setting_app_input_str"])
            congenica_app_inputs = (
                f"{CongenicaInputsConfig.APP_INPUTS['congenica_upload']['vcf']}"
                f"{self.vcfjobid}:{self.file_dict['vcf']['name']} "
                f"{CongenicaInputsConfig.APP_INPUTS['congenica_upload']['bam']}"
                f"{self.bamjobid}:{self.file_dict['bam']['name']}"
            )
            setattr(self, "congenica_app_inputs", congenica_app_inputs)
        except Exception as exception:
            self.logger.error(self.logger.log_msgs["app_input_str_err"], exception)
            sys.exit(1)

    def printer(self) -> None:
        """
        Print inputs to Congenica upload app (bam and vcf Congenica
        app inputs in string format)
            :return None:
        """
        self.logger.info(self.logger.log_msgs["printing_app_input_str"], self.congenica_app_inputs)
        print(self.congenica_app_inputs)
