"""
Main entry point for upload_runfolder module.

Uploads runfolder to DNAnexus by passing given arguments to the UploadRunfolder script.
See README and docstrings for further details
"""
import os
import argparse
from ..config import ad_config
from ..upload_runfolder.upload_runfolder import UploadRunfolder
from ..toolbox import toolbox


def get_arguments():
    """
    Parses command line arguments
        :return argparse.Namespace(object):    With attributes named after long-option
                                               command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Uploads runfolder to DNAnexus",
        usage=(
            "Upload user-specified runfolder to DNAnexus, providing an auth token, "
            "project ID to upload to, and any file patterns that should be ignored"
        ),
    )
    dnanexus_auth = toolbox.get_credential(ad_config.CREDENTIALS["dnanexus_authtoken"])
    parser.add_argument(  # Define arguments
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
            "A string or file containing a DNAnexus authorisation key used to access the DNAnexus "
            "project. If not specified, the config-specified auth token will be used by default"
        ),
        default=dnanexus_auth,
        type=os.path.expanduser,
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
        default=None,
        help="The ID of an existing DNAnexus project for the given runfolder",
    )

    return parser.parse_args()  # Collect arguments and return


parsed_args = get_arguments()  # Get command line arguments

rf_obj = toolbox.RunfolderObject(parsed_args.runfolder_name, ad_config.TIMESTAMP)
rf_obj.add_runfolder_loggers()

# If a different auth token is supplied on command line, replace the attribute in the runfolder object
if parsed_args.auth_token:
    rf_obj.dnanexus_auth = parsed_args.auth_token

if parsed_args.project_id:
    project_name_cmd = ad_config.DX_CMDS["proj_name_from_id"] % (
        parsed_args.project_id,
        parsed_args.auth_token,
    )
    project_name, err, returncode = toolbox.execute_subprocess_command(
        project_name_cmd, rf_obj.rf_loggers.backup, "exit_on_fail"
    )
    nexus_identifiers = {
        "proj_name": project_name,
        "proj_id": parsed_args.project_id,
    }
else:
    nexus_identifiers = False

toolbox.script_start_logmsg(rf_obj.rf_loggers.backup, __file__)

# Create an object to set up the upload agent command
upload_runfolder = UploadRunfolder(
    rf_obj=rf_obj,
    nexus_identifiers=nexus_identifiers,
)
upload_runfolder.upload_rest_of_runfolder(parsed_args.ignore)

toolbox.script_end_logmsg(rf_obj.rf_loggers.backup, __file__)
