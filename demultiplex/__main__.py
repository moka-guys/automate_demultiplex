"""
Main entry point for demultiplex module.

Demultiplexes NGS Run Folders. See README and docstrings for further details
"""

import argparse
from demultiplex.demultiplex import GetRunfolders
from ad_logger.ad_logger import set_root_logger

set_root_logger()

def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        :return argparse.Namespace (object):    Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Used to demultiplex a runfolder using the demultiplexing script."
            "If given an input runfolder name, will process just that single "
            "runfolder. Runfolder input should only be used for processing "
            "development runs as it will bypass SampleSheet errors and run "
            "demultiplexing anyway"
        ),
        usage="Used to demultiplex a runfolder using the demultiplexing script",
    )
    parser.add_argument(
        "-r",
        "--runfolder_name",
        type=str,
        required=False,
        help=(
            "Runfolder name for script to process. This argument should only "
            "be used for processing development runs as it will bypass SampleSheet "
            "errors and run demultiplexing anyway"
        ),
    )
    return parser.parse_args()


parsed_args = get_arguments()

if parsed_args.runfolder_name:  # If run with runfolder name provided as input
    gr_obj = GetRunfolders(parsed_args.runfolder_name)

else:
    gr_obj = GetRunfolders()

gr_obj.setoff_processing()
