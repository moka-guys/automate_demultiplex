"""
Main entry point for congenica_inputs module.

Prints inputs required by congenica upload apps on DNAnexus.
See README and docstrings for further details
"""
import subprocess
import json
import re
import argparse
from ..config import ad_config, panel_config
from ..ad_logger import ad_logger
from ..toolbox import toolbox
from ..congenica_inputs.congenica_inputs import DecisionTooler


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        :return argparse.Namespace (object):    Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Given an analysis-id, will obtain the job ids for bam and vcf "
            "files for upload to congenica"
        ),
        usage=(
            "Called from within the dx run commands to produce part of the "
            "dx run string for the congenica uploads"
        ),
    )
    parser.add_argument(
        "-a",
        "--analysis_id",
        required=True,
        type=str,
        help="workflow Analysis ID in format Analysis-abc123",
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        type=str,
        help="The DNAnexus project name in which the analysis is running",
    )
    parser.add_argument(
        "-r",
        "--runfolder_name",
        required=True,
        help="Workstation runfolder name",
        type=str,
    )
    return parser.parse_args()


parsed_args = get_arguments()
dnanexus_auth = toolbox.get_credential(ad_config.CREDENTIALS["dnanexus_authtoken"])

analysis_info = json.loads(
    subprocess.check_output(
        [
            "dx",
            "describe",
            parsed_args.analysis_id,
            "--auth",
            dnanexus_auth,
            "--json",
        ]
    )
)
# Get settings for analysis panel (to determine which workflow is running)
pannumber = re.search(r"Pan\d+", analysis_info["name"]).group()

# Create tooler object, using the analysis ID and the workflow name from the ad_config
# panel dictionary
tooler = DecisionTooler(
    parsed_args.analysis_id,
    parsed_args.project,
    parsed_args.runfolder_name,
    panel_config.PANEL_DICT[pannumber]["pipeline"],
)

toolbox.script_start_logmsg(tooler.logger, __file__)

# Get and print decision support tool inputs
tooler.get_inputs()

toolbox.script_end_logmsg(tooler.logger, __file__)

ad_logger.shutdown_logs(tooler.logger)
