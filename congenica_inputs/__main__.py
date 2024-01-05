"""
Main entry point for congenica_inputs module.

Prints inputs required by congenica upload apps on DNAnexus.
See README and docstrings for further details
"""
import subprocess
import json
import re
import argparse
from ..config.ad_config import CongenicaInputsConfig
from ..ad_logger.ad_logger import shutdown_logs
from ..toolbox.toolbox import get_credential, script_start_logmsg, script_end_logmsg
from ..congenica_inputs.congenica_inputs import CongenicaInputs


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
dnanexus_auth = get_credential(CongenicaInputsConfig.CREDENTIALS["dnanexus_authtoken"])

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

# Create CongenicaInputs object, using the analysis ID and the workflow name from the ad_config
# panel dictionary
ci_obj = CongenicaInputs(
    parsed_args.analysis_id,
    parsed_args.project,
    parsed_args.runfolder_name,
    CongenicaInputsConfig.PANEL_DICT[pannumber]["pipeline"],
)

script_start_logmsg(ci_obj.logger, __file__)

# Get and print decision support tool inputs
ci_obj.get_inputs()

script_end_logmsg(ci_obj.logger, __file__)

shutdown_logs(ci_obj.logger)
