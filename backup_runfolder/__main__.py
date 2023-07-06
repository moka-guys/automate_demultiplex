"""
Uploads runfolder to DNAnexus by passing given arguments to the DNAnexus upload agent.
"""
import argparse
import os
import config.ad_config as ad_config
import ad_logger.ad_logger as ad_logger
from backup_runfolder import UACaller
from shared_functions.shared_functions import (
    execute_subprocess_command, RunfolderObject, git_tag
)


def get_arguments():
    """
    Parses command line arguments
        :return argparse.Namespace(object):    With attributes named after long-option
                                               command-line arguments
    """
    parser = argparse.ArgumentParser()

    with open(
        ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
    ) as token_file:
        dnanexus_apikey = token_file.readline().rstrip()  # Auth token

    # Define arguments
    parser.add_argument(
        "-r",
        "--runfolder_name",
        required=True,
        help="Workstation runfolder name",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--auth_token",
        help=(
            "A string or file containing a DNAnexus authorisation key used to "
            "access the DNAnexus project. If not specified, the config-specified auth"
            "token will be used by default"
        ),
        default=dnanexus_apikey,
        type=os.path.expanduser,
    )
    parser.add_argument(
        "--ignore",
        default=None,
        help=(
            "Comma-separated list of patterns which prevents the file "
            "from being uploaded if any pattern is present in filename "
            "or filepath."
        ),
    )
    parser.add_argument(
        "-p",
        "--project_id",
        default=None,
        help=("The ID of an existing DNAnexus project for the given runfolder"),
        )

    return parser.parse_args()  # Collect arguments and return


parsed_args = get_arguments()  # Get command line arguments

rf_obj = RunfolderObject(
    parsed_args.runfolder, ad_logger.backup_logger, ad_config.TIMESTAMP
    )
rf_obj.add_runfolder_loggers()  # Add loggers

# If a different auth token is supplied on command line, replace the attribute in the
# runfolder object
if parsed_args.auth_token:
    rf_obj.dnanexus_apikey = parsed_args.auth_token

if parsed_args.project_id:
    project_name_cmd = ad_config.DX_CMDS["proj_name_from_id"] % (parsed_args.project_id)
    project_name, err, returncode = execute_subprocess_command(
        project_name_cmd, rf_obj.rf_loggers.backup
        )
    nexus_identifiers = {
        "proj_name": project_name,
        "proj_id": parsed_args.project_id,
    }
else:
    nexus_identifiers = False


ad_logger.backup_logger.backup.info(
    ad_logger.backup_logger.backup.log_msgs["script_start"],
    git_tag(),
    "UACaller.py",
    extra={"flag": ad_logger.backup_logger.backup.log_flags["info"] % "dst"},
)

# Create an object to set up the upload agent command
backup_runfolder = UACaller(
    rf_obj=rf_obj,
    nexus_identifiers=nexus_identifiers,
)
backup_runfolder.upload_rest_of_runfolder(parsed_args.ignore)

ad_logger.backup_logger.backup.info(
    ad_logger.backup_logger.backup.log_msgs["script_end"],
    git_tag(),
    "UACaller.py",
    extra={"flag": ad_logger.backup_logger.backup.log_flags["info"] % "dst"},
)
