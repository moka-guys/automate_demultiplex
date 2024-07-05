"""
Main entry point for upload_runfolder module.

Uploads runfolder to DNAnexus by passing given arguments to the UploadRunfolder script.
See README and docstrings for further details
"""

import os
import argparse
from config.ad_config import URConfig
from upload_runfolder.upload_runfolder import UploadRunfolder
from toolbox.toolbox import (
    get_credential,
    RunfolderObject,
    execute_subprocess_command,
    script_start_logmsg,
    script_end_logmsg,
)
from ad_logger.ad_logger import set_root_logger, shutdown_logs


set_root_logger()


def get_arguments():
    """
    Parses command line arguments
        :return argparse.Namespace(object):    With attributes named after long-option
                                               command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Uploads runfolder to DNAnexus",
        usage=(
            "Upload user-specified runfolder to DNAnexus, providing a project ID to upload ""to, and any file patterns that should be ignored"
        ),
    )
    parser.add_argument(  # Define arguments
        "-r",
        "--runfolder_name",
        required=True,
        help="Workstation runfolder name",
        type=str,
    )
    parser.add_argument(
        "--ignore",
        default=None,
        help=(
            "Comma-separated list of patterns which prevents the file from being uploaded "
            "if any pattern is present in filename or filepath."
        ),
    )
    parser.add_argument(
        "-p",
        "--project_id",
        required=True,
        default=None,
        help="The ID of an existing DNAnexus project for the given runfolder",
    )
    return parser.parse_args()  # Collect arguments and return


parsed_args = get_arguments()  # Get command line arguments

rf_obj = RunfolderObject(parsed_args.runfolder_name, URConfig.TIMESTAMP)
loggers = rf_obj.get_runfolder_loggers(__package__)
dnanexus_auth = get_credential(URConfig.CREDENTIALS["dnanexus_authtoken"])

if parsed_args.project_id:
    project_name_cmd = URConfig.DX_CMDS["proj_name_from_id"] % (
        parsed_args.project_id,
        dnanexus_auth,
    )
    project_name, err, returncode = execute_subprocess_command(
        project_name_cmd, loggers["backup"], "exit_on_fail"
    )
    nexus_identifiers = {
        "proj_name": project_name,
        "proj_id": parsed_args.project_id,
    }
else:
    nexus_identifiers = False

script_start_logmsg(loggers["backup"], __file__)

# Create an object to set up the upload agent command
ur_obj = UploadRunfolder(
    loggers["backup"],
    rf_obj.runfolder_name,
    rf_obj.runfolderpath,
    rf_obj.upload_flagfile,
    nexus_identifiers,
)
ur_obj.upload_rest_of_runfolder(parsed_args.ignore)

script_end_logmsg(loggers["backup"], __file__)
