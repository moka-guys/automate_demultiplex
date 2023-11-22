"""
Main entry point for samplesheet_validator module.

Checks sample sheet naming and contents. See README and docstrings for further details
"""
import argparse
import toolbox.toolbox as toolbox
import ad_logger.ad_logger as ad_logger
import samplesheet_validator.samplesheet_validator as samplesheet_validator
from config import ad_config


def get_arguments():
    """
    Uses argparse module to define and handle command line input arguments
    and help menu
        :return argparse.Namespace (object):    Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "Given an input samplesheet, will validate the samplesheet using "
            "seglh-naming conventions and output a logfile"
        ),
        usage=(
            "Used to validate a samplesheet using the seglh-naming conventions"
        )
    )
    parser.add_argument(
        "-s",
        "--samplesheet_path",
        type=lambda x: toolbox.is_valid_file(parser, x),
        required=True,
        help="Path to samplesheet requiring validation",
    )
    parser.add_argument(
        "-r",
        "--runfolder_name",
        type=str,
        required=True,
        help="Name of runfolder, required for naming logfile"

    )
    return parser.parse_args()


parsed_args = get_arguments()

rf_obj = toolbox.RunfolderObject(
    parsed_args.runfolder_name, ad_config.TIMESTAMP
    )
rf_obj.add_runfolder_logger('ss_validator')  # Add ss_validator logger
logger = rf_obj.rf_loggers.ss_validator

sscheck_obj = samplesheet_validator.SamplesheetCheck(
    parsed_args.samplesheet_path, parsed_args.runfolder_name, logger
)

toolbox.script_start_logmsg(sscheck_obj.logger, __file__)

sscheck_obj.ss_checks()  # Carry out samplesheeet validation
sscheck_obj.log_summary()  # Log a summary of the validation
ad_logger.shutdown_logs(sscheck_obj.logger)

toolbox.script_end_logmsg(sscheck_obj.logger, __file__)

ad_logger.shutdown_logs(sscheck_obj.logger)
