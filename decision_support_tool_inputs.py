"""
Print inputs required by decision support tool upload applications on DNAnexus.
See Readme and doctrings for further details
"""
import subprocess
import json
import re
import argparse
import config.ad_config as ad_config
import config.panel_config as panel_config
import ad_logger.log_config as logger_config
import ad_logger.ad_logger as ad_logger
from shared_functions.shared_functions import execute_subprocess_command, git_tag


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        :return argparse.Namespace (object):    Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "given an analysis-id will obtain the job ids for bam and vcf "
            "files for upload to the specified decision support tool"
        )
    )
    parser.add_argument(
        "-a",
        "--analysis_id",
        required=True,
        help="workflow Analysis ID in format Analysis-abc123",
    )
    parser.add_argument(
        "-t",
        "--tool",
        choices=["congenica"],
        required=True,
        help="decision support tool (currently only supports congenica)",
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="The DNAnexus project name in which the analysis is running",
    )
    return parser.parse_args()


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
        set_jobid_cmds()
            Set commands for retrieving the job ID for the vcf and bam workflow stages
        get_jobids()
            Get job ids for bam and vcf jobs within the workflow
        set_app_input_string()
            Set the input string for the congenica app
        printer()
            Print inputs to decision support upload app (congenica upload)
    """
    def __init__(self, analysis_id, project, workflow, loggers):
        """
        Constructor for the DecisionTooler class
            :param analysis_id (str):   Workflow analysis ID
            :param project (str):       DNAnexus project ID
            :param loggers
        """
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token
        self.analysis_id = analysis_id
        self.project = project
        self.workflow = workflow
        self.loggers = loggers
        self.loggers.decision_support.info(
            self.loggers.msgs["decision_support"]["script_start"],
            git_tag(),
            extra={"flag": self.loggers.log_flags["info"] % "dst"},
        )
        # Contains strings used by the script to build the commands
        self.file_dict = ad_config.DECISION_SUPPORT_INPUTS[self.workflow]
        self.loggers.decision_support.info(
                self.loggers.msgs["decision_support"]["workflow_type"],
                self.workflow,
                extra={"flag": self.loggers.log_flags["info"] % "dst"},
            )
        self.set_jobid_cmds()
        self.get_jobids()
        self.set_app_input_string()

    def set_jobid_cmds(self) -> None:
        """
        Set the commands for retrieving the job ID for the vcf and bam workflow stages
            :return None:
        """
        self.loggers.decision_support.info(
                self.loggers.msgs["decision_support"]["setting_job_id_cmds"],
                extra={"flag": self.loggers.log_flags["info"] % "dst"},
            )
        try:
            for file_name in self.file_dict.keys():
                find_execution_id_cmd = ad_config.DX_CMDS['find_execution_id'] % (
                    f"{self.project}:{self.analysis_id}",
                    self.dnanexus_apikey, self.file_dict[file_name]['stage']
                    )
                setattr(self, f"{file_name}jobid_cmd", find_execution_id_cmd)
        except Exception as exception:
            self.loggers.decision_support.exception(
                self.loggers.msgs["decision_support"]["setting_job_id_cmds_err"],
                exception,
                extra={"flag": self.loggers.log_flags["fail"] % "dst"},
            )

    def get_jobids(self) -> None:
        """
        Get job ids for bam and vcf jobs within the workflow by executing the job id
        retrieval commands. Set as class attributes.
            :return None:
        """
        for outfile in self.file_dict.keys():
            self.loggers.decision_support.info(
                self.loggers.msgs["decision_support"]["get_job_id"], outfile,
                extra={"flag": self.loggers.log_flags["info"] % "dst"},
            )
            jobid = False
            returncode = 1
            tries = 0
            jobid_cmd = getattr(self, f"{outfile}jobid_cmd")
            while returncode != 0 and not jobid:
                try:
                    jobid, err, returncode = execute_subprocess_command(
                        jobid_cmd, self.loggers.decision_support
                        )
                    self.loggers.decision_support.info(
                        self.loggers.msgs["decision_support"]["found_job_id"], outfile,
                        jobid,
                        extra={"flag": self.loggers.log_flags["info"] % "dst"},
                    )
                    setattr(self, f"{outfile}jobid", jobid)
                except Exception as exception:
                    self.loggers.decision_support.info(
                        self.loggers.msgs["decision_support"]["get_job_id_err"],
                        outfile, exception,
                        extra={"flag": self.loggers.log_flags["info"] % "dst"},
                    )
                    tries += 1
                    if tries == 1000:  # Can take a while for job to set off
                        self.loggers.decision_support.exception(
                            self.loggers.msgs["decision_support"][
                                "get_job_id_fail"
                                ],
                            outfile, exception,
                            extra={"flag": self.loggers.log_flags["fail"] % "dst"},
                        )

    def set_app_input_string(self) -> None:
        """
        Set the input string for the congenica app
            :return None:
        """
        try:
            self.loggers.decision_support.info(
                self.loggers.msgs["decision_support"]["setting_app_input_str"],
                extra={"flag": self.loggers.log_flags["info"] % "dst"},
            )
            congenica_app_inputs = (
                f"{ad_config.APP_INPUTS['congenica_upload']['vcf']}"
                f"{self.vcfjobid}:{self.file_dict['vcf']['name']} "
                f"{ad_config.APP_INPUTS['congenica_upload']['bam']}"
                f"{self.bamjobid}:{self.file_dict['bam']['name']}"
            )
            setattr(self, 'congenica_app_inputs', congenica_app_inputs)
        except Exception as exception:
            self.loggers.decision_support.exception(
                self.loggers.msgs["decision_support"]["app_input_str_err"],
                exception,
                extra={"flag": self.loggers.log_flags["fail"] % "dst"},
            )

    def printer(self) -> str:
        """
        Print inputs to decision support upload app (congenica upload)
            :return (str):  Bam and vcf congenica app inputs in string format
        """
        self.loggers.decision_support.info(
            self.loggers.msgs["decision_support"]["printing_app_input_str"],
            extra={"flag": self.loggers.log_flags["info"] % "dst"},
        )
        print(self.congenica_app_inputs)


if __name__ == "__main__":
    parsed_args = get_arguments()
    with open(
        ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
    ) as token_file:
        dnanexus_apikey = token_file.readline().rstrip()  # Auth token

    analysis_info = json.loads(
        subprocess.check_output(
            [
                "dx",
                "describe",
                parsed_args.analysis_id,
                "--auth",
                dnanexus_apikey,
                "--json",
            ]
        )
    )
    # Get settings for analysis panel (to determine which workflow is running)
    pannumber = re.search(r"Pan\d+", analysis_info["name"]).group()

    script_loggers = ad_logger.AdLoggers(
        {"decision_support": (
            logger_config.LOGFILES['decision_support_script_logs'] % parsed_args.project
            )}
        )
    # Disable the stream handler to prevent logs being sent to stdout (we only want the
    # project and file IDs to be stored)
    script_loggers.shutdown_streamhandler()

    # Print decision support tool inputs, using the analysis ID and the
    # workflow name from the ad_config panel dictionary
    tooler = DecisionTooler(
        parsed_args.analysis_id, parsed_args.project,
        panel_config.PANEL_DICT[pannumber]["pipeline"], script_loggers
    )
    # Print congenica app inputs
    tooler.printer()

    script_loggers.decision_support.info(
        script_loggers.msgs["decision_support"]["script_end"],
        git_tag(),
        extra={"flag": script_loggers.log_flags["info"] % "dst"},
    )
