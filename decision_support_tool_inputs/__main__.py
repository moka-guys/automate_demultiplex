import subprocess
import json
import re
import argparse
import config.ad_config as ad_config
import config.panel_config as panel_config
import ad_logger.ad_logger as ad_logger
from shared_functions.shared_functions import git_tag
from decision_support_tool_inputs.decision_tooler import DecisionTooler


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

script_logger = ad_logger.return_scriptlogger("decision_support", parsed_args.project)

# Disable the stream handler to prevent logs being sent to stdout (we only want the
# project and file IDs to be stored)
script_logger.shutdown_streamhandler()

# Print decision support tool inputs, using the analysis ID and the
# workflow name from the ad_config panel dictionary
tooler = DecisionTooler(
    parsed_args.analysis_id, parsed_args.project,
    panel_config.PANEL_DICT[pannumber]["pipeline"], script_logger.decision_support
)
tooler.printer()  # Print congenica app inputs

script_logger.decision_support.info(
    script_logger.decision_support.log_msgs["script_end"],
    git_tag(),
    "decision_support_tool_inputs.py",
    extra={"flag": script_logger.decision_support.log_flags["info"] % "dst"},
)
