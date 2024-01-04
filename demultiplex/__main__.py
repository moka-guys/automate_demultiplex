"""
Main entry point for demultiplex module.

Demultiplexes NGS Run Folders. See README and docstrings for further details
"""
import argparse
from ..demultiplex import demultiplex
from ..toolbox import toolbox
from ..ad_logger import ad_logger


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
            "runfolder. Runfolder input should ONLY BE USED FOR PROCESSING "
            "DEVELOPMENT RUNS AS IT WILL BYPASS SAMPLESHEET ERRORS AND RUN "
            "DEMULTIPLEXING ANYWAY"
        ),
        usage="Used to demultiplex a runfolder using the demultiplexing script"
    )
    parser.add_argument(
        "-r",
        "--runfolder_name",
        type=str,
        required=False,
        help=(
            "Runfolder name for script to process. This argument should ONLY BE "
            "USED FOR PROCESSING DEVELOPMENT RUNS AS IT WILL BYPASS SAMPLESHEET "
            "ERRORS AND RUN DEMULTIPLEXING ANYWAY"
        ),
    )
    return parser.parse_args()


parsed_args = get_arguments()

if parsed_args.runfolder_name:  # If run with runfolder name provided as input
    gr_obj = demultiplex.GetRunfolders(parsed_args.runfolder_name)

else:
    gr_obj = demultiplex.GetRunfolders()


toolbox.script_start_logmsg(gr_obj.script_logger, __file__)

gr_obj.setoff_processing()

toolbox.script_end_logmsg(gr_obj.script_logger, __file__)
ad_logger.shutdown_logs(gr_obj.script_logger)
