"""
Main entry point for demultiplex module.

Demultiplexes NGS Run Folders. See README and docstrings for further details
"""

import argparse
from contextlib import nullcontext

from ad_logger.ad_logger import set_root_logger
from config.ad_config import DemultiplexConfig
from demultiplex.process_lock import demultiplex_process_lock

root_logger = set_root_logger()


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


def get_process_lock(runfolder_name):
    """
    Return a lock for scheduled scans and no-op for targeted manual runs.
    """
    if runfolder_name:
        return nullcontext()
    return demultiplex_process_lock(
        DemultiplexConfig.PROCESS_LOCK_FILE, root_logger
    )


def main() -> None:
    """
    Serialize scheduled scans while allowing targeted manual runs.
    """
    parsed_args = get_arguments()

    with get_process_lock(parsed_args.runfolder_name):
        # Importing creates the per-invocation file logger, so do it only after
        # scheduled processing owns the lock.
        from demultiplex.demultiplex import GetRunfolders

        if parsed_args.runfolder_name:
            gr_obj = GetRunfolders(parsed_args.runfolder_name)
        else:
            gr_obj = GetRunfolders()

        gr_obj.setoff_processing()


if __name__ == "__main__":
    main()
