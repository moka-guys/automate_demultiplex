#!/usr/bin/env python3
"""wscleaner

Delete runfolders in a root directory on the condition that it has uploaded to DNAnexus.

Methods:
    cli_parser(): Parses command line arguments
    main(): Process input directory or API keys
"""
import argparse
from toolbox.toolbox import git_tag
from config.ad_config import BRANCH, RunfolderCleanupConfig
from .wscleaner import RunFolderManager


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        :return argparse.Namespace (object):    Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Used to clean up runfolders that have been successfully uploaded "
            "to DNAnexus from the workstation. Will identify runfolders that "
            "meet the criteria for deletion and delete them if run without "
            "the --dry-run flag"
        ),
        usage="Used to clean up the runfolders directory on the workstation",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        help="Perform a dry run without deleting files",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-m",
        "--min-age",
        help="The age (days) a runfolder must be to be deleted",
        type=int,
        default=14,
    )
    parser.add_argument(
        "-l",
        "--logfile-count",
        help="The number of logfiles a runfolder must have in /automated_scripts_logfiles",
        type=int,
        default=6,
    )
    return parser.parse_args()


version = git_tag()
# Parse CLI arguments. Some arguments will exit the program intentionally. See docstring for detail.
parsed_args = get_arguments()


# If dry-run CLI flag is given, or script is run from the development area
# no directories are deleted by the runfolder manager
if parsed_args.dry_run or BRANCH != "main":
    dry_run = True  # Protects against deleting the test folders (!!)

RFM = RunFolderManager(
    dry_run=dry_run,
    min_age=parsed_args.min_age,
    logfile_count=parsed_args.logfile_count,
)
RFM.cleanup_runfolders()
