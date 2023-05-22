""" Print inputs required by decision support tool upload
applicationson DNANexus

In order to run some run wide tasks we need to supply the inputs in the
    form jobid.output_name
This is hard to do if we are running workflows as the job id relates to one
    app within a workflow.
This script takes an analysis id and returns the job id of the specific stage.
The script prints the output to the command line formatted for the tool given
    in as an argument.
"""

import subprocess
import json
import re
from collections import namedtuple
import argparse
import config.ad_config as ad_config  # Import ad_config file
import config.panel_config as panel_config


# TODO incorporate logging, including traceback
def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
    """
    # Create ArgumentParser object. Description message will be displayed as
    # part of help message if script is run with -h flag
    parser = argparse.ArgumentParser(
        description=(
            "given an analysis-id will obtain the job ids for bam and vcf "
            "files for upload to the specified decision support tool"
        )
    )
    # Define the arguments that will be taken.
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
        help="The DNAnexus project id in which the analysis is running",
    )
    # Return the arguments
    return parser.parse_args()


class DecisionTooler(object):
    """
    Builds decision support tool command line inputs
    """

    # named tuple to hold all the output names - This tuple name is "workflow"
    # and has four attributes which can be accessed using Workflow.attribute
    workflow_object = namedtuple("Workflow", "name vcf_out bam_out bai_out")

    def __init__(self, analysis_id, project, workflow):
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token
        self.project = project
        self.analysis_id = analysis_id
        self.base_cmd = (
            f"source {ad_config.SCRIPTS['sdk_source']}; dx describe "
            f"{project}:{self.analysis_id} --json "
            f"--auth-token {self.dnanexus_apikey}"
        )
        if workflow == "pipe":
            self.workflow = "pipe"
            self.vcf_stage = "filter_vcf"
            self.bam_stage = "gatk"
            self.vcf = ad_config.PIPE_VCF_OUTPUT_NAME
            self.bam = ad_config.PIPE_BAM_OUTPUT_NAME
            self.bai = None
        else:
            self.workflow = "wes"
            # Same stage is used to produce both the BAM and VCF
            self.vcf_stage = "senteion"
            self.bam_stage = "senteion"
            self.vcf = ad_config.WES_SENTIEON_VCF_OUTPUT_NAME
            self.bam = ad_config.WES_SENTIEON_BAM_OUTPUT_NAME
            self.bai = ad_config.WES_SENTIEON_BAI_OUTPUT_NAME

        self.vcf_stageid = ad_config.NEXUS_IDS["STAGES"][self.workflow][self.vcf_stage]
        self.bam_stageid = ad_config.NEXUS_IDS["STAGES"][self.workflow][self.bam_stage]

        # Use workflow stage ID to identify job ID of required stage
        self.vcfjobid_cmd = (
            f"{self.base_cmd} | jq '.stages[] | select(.id == "
            f'"{self.vcf_stageid}")'
            ".execution.id'"
        )
        self.bamjobid_cmd = (
            f"{self.base_cmd} | jq '.stages[] | select( .id == "
            f'"\'"{self.bam_stageid}"\'")'
            ".execution.id'"
        )

        jobid = False
        tries = 0

        for file in ("vcf", "bam"):
            jobid_cmd = getattr(self, f"{file}jobid_cmd")
            while not jobid:
                try:
                    jobid = str(self.execute_subprocess(jobid_cmd))
                except Exception:
                    tries += 1
                    if tries == 1000:  # Can take a while for job to set off
                        raise Exception("Maximum Tries Exceeded")

            setattr(self, f"{file}jobid", jobid)

        self.congenica_app_inputs = (
            f" {ad_config.APP_INPUTS['congenica_upload']['vcf']}"
            f"{self.vcfjobid}:{self.vcf}"
            f"{ad_config.APP_INPUTS['congenica_upload']['bam']}"
            f"{self.bamjobid}:{self.bam}"
        )

    def execute_subprocess(self, cmd):
        """
        Execute command and capture and return the streams
        """
        proc = subprocess.Popen(
            [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
        )
        (out, _) = proc.communicate()
        return out.decode("utf-8").strip('"\n')

    def printer(self):
        """
        Print inputs to decision support upload app (congenica upload)
        """
        print(self.congenica_app_inputs)


if __name__ == "__main__":
    args = get_arguments()
    with open(
        ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
    ) as token_file:
        dnanexus_apikey = token_file.readline().rstrip()  # Auth token
    ajson = json.loads(
        subprocess.check_output(
            [
                "dx",
                "describe",
                args.analysis_id,
                "--auth",
                dnanexus_apikey,
                "--json",
            ]
        )
    )

    # Get settings for analysis panel (to determine which workflow is running)
    pannumber = re.search(r"Pan\d+", ajson["name"]).group()

    # Print decision support tool inputs, using the analysis ID and the
    # workflow name from the ad_config panel dictionary
    tooler = DecisionTooler(
        args.analysis_id, args.project, panel_config.PANEL_DICT[pannumber]["pipeline"]
    )

    # Print congenica app inputs
    tooler.printer()
