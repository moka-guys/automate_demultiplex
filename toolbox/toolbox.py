#!/usr/bin/python3
"""
This script contains functions shared across scripts / modules. Contains the following classes:

- RunfolderObject:
    An object with runfolder-specific properties
"""
import sys
import os
import subprocess
import logging
import argparse
from distutils.spawn import find_executable
from typing import Union, Optional
from config.ad_config import ToolboxConfig
from ad_logger.ad_logger import RunfolderLoggers


def get_credential(file):
    """
    File from which to read credential
    """
    with open(file, "r") as to_read:
        credential = to_read.readline().rstrip()
        return credential


def write_lines(file: str, mode: str, lines: str):
    """
    Write line to newline of file
        :param file (str):          Filepath
        :param mode (str):          Mode to open the file in
        :param lines (str | list):  Line (/s)
    """
    if isinstance(lines, str):
        lines = [lines]
    with open(file, mode) as open_file:
        for line in lines:
            open_file.write(f"{line}\n")


def read_lines(file: str):
    """
    Read lines from file
        :param file (str):      Filepath
        :return lines (list):   List of lines
    """
    with open(file, "r") as f:
        return f.readlines()


def return_scriptlog_config() -> dict:
    """
    Return script-level logfile configuration
        :return (dict): Dictionary containing logger names and logfile paths
    """
    return {
        "demux": os.path.join(  # Record demultiplex script logs
            ToolboxConfig.AD_LOGDIR,
            "demultiplexing_script_logfiles",
            f"{ToolboxConfig.TIMESTAMP}_demultiplex_script.log",
        ),
        "sw": os.path.join(  # Record sw script logs
            ToolboxConfig.AD_LOGDIR,
            "sw_script_logfiles",
            f"{ToolboxConfig.TIMESTAMP}_setoff_workflow.log",
        ),
    }


def script_start_logmsg(logger: logging.Logger, file: str) -> None:
    """
    Adds the log message that denotes the start of the script
    running to the logfile
        :param logger (logging.Logger): Logger
        :param file (str):              Path to logfile
        :return None:
    """
    logger.info(
        logger.log_msgs["script_start"],
        git_tag(),
        os.path.basename(os.path.dirname(file)),
    )


def script_end_logmsg(logger: logging.Logger, file: str) -> None:
    """
    Adds the log message that denotes the end of the script
    runnign to the logfile
        :param logger (logging.Logger): Logger
        :param file (str):              Path to logfile
        :return None:
    """
    logger.info(
        logger.log_msgs["script_end"],
        git_tag(),
        os.path.basename(os.path.dirname(file)),
    )


def is_valid_dir(parser: argparse.ArgumentParser, file: str) -> str:
    """
    Check directory path is valid
        :param parser (argparse.ArgumentParser):    Holds necessary info to parse cmd
                                                    line into Python data types
        :param file (str):                          Input argument
    """
    if not os.path.isdir(file):
        parser.error(f"The directory {file} does not exist!")
    else:
        return file


def is_valid_file(parser: argparse.ArgumentParser, file: str) -> str:
    """
    Check file path is valid
        :param parser (argparse.ArgumentParser):    Holds necessary info to parse cmd
                                                    line into Python data types
        :param file (str):                          Input argument
    """
    if not os.path.exists(file):
        parser.error(f"The file {file} does not exist!")
    else:
        return file


def git_tag() -> str:
    """
    Obtain the git tag of the current commit
        :return (str):  Git tag
    """
    filepath = os.path.dirname(os.path.realpath(__file__))
    cmd = f"git -C {filepath} describe --tags"

    proc = subprocess.Popen(
        [cmd],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )
    out, _ = proc.communicate()
    #  Return standard out, removing any new line characters
    return out.rstrip().decode("utf-8")


def execute_subprocess_command(
    command: str, logger: logging.Logger, exit_on_fail=False
) -> Union[str, str, int]:
    """
    Execute a subprocess
        :param command(str):            Input command
        :param logger(logging.Logger):  Logger
        :return (stdout(str),
        stderr(str)) (tuple):           Outputs from the command
    """
    logger.info(logger.log_msgs["executing_command"], command)
    proc = subprocess.Popen(
        [command],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
        executable="/bin/bash",
    )
    out, err, returncode = check_returncode(proc, logger)
    if exit_on_fail == "exit_on_fail":
        exit_on_returncode(returncode)
    return out, err, returncode


def exit_on_returncode(returncode: int) -> None:
    """
    Exit the script if the returncode is not 0 (success)
    """
    if returncode != 0:
        sys.exit(1)


def check_returncode(
    proc: subprocess.Popen, logger: logging.Logger
) -> Union[str, str, int]:
    """
    Check for success returncode and write to log accordingly
        :param proc (class):                subprocess.Popen class
        :param logger (logging.Logger):     Logger
        :return (stdout(str),
        stderr(str),
        returncode(int))(tuple):            Stdout, stderr, returncode
    """
    out, err = proc.communicate()
    out = out.decode("utf-8").strip()
    err = err.decode("utf-8").strip()
    returncode = proc.returncode

    if returncode == 0:
        logger.info(logger.log_msgs["cmd_success"], returncode)
        return out, err, returncode
    else:
        logger.error(logger.log_msgs["cmd_fail"], returncode, out, err)
        return out, err, returncode


def get_runfolder_path(runfolder_name: str) -> str:
    """
    Return the path of the runfolder based on the runfolder_name input
        :param runfolder_name (str):    Runfolder name string
        :return (str):                  Runfolder path
    """
    return os.path.join(ToolboxConfig.RUNFOLDERS, runfolder_name)


def test_upload_software(logger) -> True:
    """
    Test the required software is installed and performing. If not, exit the script
        :return True | None:    Return True if all software tests pass, else None
    """
    if test_programs("dx_toolkit", logger) and test_programs("upload_agent", logger):
        return True
    else:
        logger.error(logger.log_msgs["software_fail"])
        sys.exit(1)


def test_processing_software(logger) -> Optional[bool]:
    """
    Test the software is installed and performing, by calling the test_upload_agent
    and test_dx_toolkit functions
        :return True|None:  Return true if the tests all pass
    """
    if test_programs("bcl2fastq2", logger) and test_programs(
        "gatk_collect_lane_metrics", logger
    ):
        return True


def test_programs(software_name: str, logger: logging.Logger) -> True:
    """
    Check software exists in path, and that the test command executes successfully
    (return code 0). If it does not, exit script
        :param software_name (str):     Name of the sofware being tested
        :param logger (logging.Logger): Logger
        :return True:                   Return True if test passes, else exit script
    """
    software_dict = ToolboxConfig.TEST_PROGRAMS_DICT[software_name]

    logger.info(logger.log_msgs["testing_software"], software_name)

    if find_executable(software_dict["executable"]):
        logger.info(logger.log_msgs["found_program"], software_dict["executable"])
        out, err, returncode = execute_subprocess_command(
            software_dict["test_cmd"], logger, "exit_on_fail"
        )
        if returncode == 0:
            logger.info(logger.log_msgs["test_pass"], software_name)
            return True
        else:
            logger.error(logger.log_msgs["test_fail"], software_name, out, err)
            sys.exit(1)
    else:
        logger.error(logger.log_msgs["program_missing"], software_dict["executable"])
        sys.exit(1)


def get_num_processed_runfolders(
    logger: logging.Logger, processed_runfolders: list
) -> int:
    """
    Set self.num_processed_runfolders
        :param logger (logging.Logger):         Logger
        :param processed_runfolders (list):     List of names of processed runfolders
        :return num_processed_runfolders (int): Number of processed runfolders
    """
    num_processed_runfolders = len(processed_runfolders)
    logger.info(
        logger.log_msgs["runfolders_processed"],
        num_processed_runfolders,
        ", ".join(processed_runfolders),
    )
    return num_processed_runfolders


class RunfolderObject(ToolboxConfig):
    """
    An object with runfolder-specific properties.

    Attributes
        dnanexus_auth (str):                    DNAnexus auth token
        timestamp (str):                        Timestamp in the format str(f"{datetime.datetime.now():
                                                %Y%m%d_%H%M%S}")
        runfolder_name (str):                   Runfolder name string
        runfolderpath (str):                    Runfolder path
        samplesheet_name (str):                 Name of runfolder SampleSheet
        rtacompletefile_path (str):             Sequencing finished filepath (within runfolder)
        samplesheet_path (str):                 Path to SampleSheet in SampleSheets dir
        runfolder_samplesheet_path (str):       Runfolder SampleSheets path (within runfolder)
        checksumfile_path (str):                md5 checksum (integrity check) file path (within runfolder)
        bcl2fastqlog_file (str):                bcl2fastq2 logfile path (within runfolder)
        fastq_dir_path (str):                   Runfolder fastq directory path (within runfolder)
        upload_flagfile (str):                  Flag file denoting upload has begun (within runfolder)
        bcl2fastqstats_file (str):              Bcl2fastq stats file (within runfolder)
        cluster_density_files (list):           List containing runfolder lane metrics
                                                and phasing metrics file paths
        demultiplex_runfolder_logfile (str):    Runfolder demultiplex logfile (within logfiles dir)
        sw_runfolder_logfile (str):             Records output of setoff workflow script
        upload_runfolder_logfile (str):         Records the logs from the upload_runfolder script
        runfolder_dx_run_script (str):          Workflow dx run commands for runfolder (within logfiles dir)
        post_run_dx_run_script (str):           Separate DX run script for downstream processing apps (TSO only)
        decision_support_upload_script (str):   Decision support upload commands for runfolder (within logfiles dir)
        proj_creation_script (str):             DNAnexus project creation bash script (within logfiles dir)
        samplesheet_validator_logfile (str):    SampleSheet validator script logfile (within logfiles dir)
        logfiles_config (dict):                 Contains all runfolder log files
        logfiles_to_upload (list):              All logfiles that require upload tozzzDNAnexus
        logfile (path):                         One per runfolder logfile
        rf_loggers (object):                    RunfolderLoggers object containing
                                                runfolder-specific loggers
    Methods
        add_runfolder_loggers(script)
            Add runfolder loggers to runfolder object
        add_runfolder_logger(script, logger_name)
            Add a single runfolder logger to runfolder object
    """

    def __init__(self, runfolder_name: str, timestamp: str):
        """
        Constructor for the RunfolderObject class
            :param runfolder_name (str):    Name of runfolder
            :param timestamp (str):         Timestamp in the format str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
        """
        self.dnanexus_auth = get_credential(
            ToolboxConfig.CREDENTIALS["dnanexus_authtoken"]
        )
        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.runfolderpath = get_runfolder_path(self.runfolder_name)
        self.samplesheet_name = f"{self.runfolder_name}_SampleSheet.csv"
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["seq_complete"]
        )
        self.samplesheet_path = os.path.join(
            ToolboxConfig.RUNFOLDERS, "samplesheets", self.samplesheet_name
        )
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        self.checksumfile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["md5checksum"]
        )
        self.sscheck_flagfile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["sscheck_flag"]
        )
        self.bcl2fastqlog_file = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["bcl2fastqlog"]
        )
        self.fastq_dir_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FASTQ_DIRS["fastqs"]
        )
        self.upload_flagfile = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["upload_started"]
        )
        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            "Data/Intensities/BaseCalls/Stats/Stats.json",
        )
        self.cluster_density_files = [
            os.path.join(
                self.runfolderpath,
                f"{self.runfolder_name}{ToolboxConfig.STRINGS['lane_metrics_suffix']}",
            ),
            os.path.join(
                self.runfolderpath,
                (
                    f"{self.runfolder_name}"
                    f"{ToolboxConfig.STRINGS['phasing_metrics_suffix']}"
                ),
            ),
        ]
        self.demultiplex_runfolder_logfile = (
            os.path.join(  # Record demultiplex script logs
                ToolboxConfig.AD_LOGDIR,
                "demultiplexing_script_logfiles",
                f"{self.runfolder_name}_demultiplex_runfolder.log",
            )
        )
        self.sw_runfolder_logfile = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "sw_script_logfiles",
            f"{self.runfolder_name}_setoff_workflow.log",
        )
        self.upload_runfolder_logfile = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "upload_runfolder_script_logfiles",
            f"{self.runfolder_name}_upload_runfolder.log",
        )
        self.runfolder_dx_run_script = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "dx_run_commands",
            f"{self.runfolder_name}_dx_run_commands.sh",
        )
        self.post_run_dx_run_script = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "dx_run_commands",
            f"{self.runfolder_name}_post_run_commands.sh",
        )
        self.decision_support_upload_script = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "dx_run_commands",
            f"{self.runfolder_name}_decision_support.sh",
        )
        self.proj_creation_script = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "dx_run_commands",
            f"{self.runfolder_name}_create_nexus_project.sh",
        )
        self.samplesheet_validator_logfile = os.path.join(
            ToolboxConfig.AD_LOGDIR,
            "samplesheet_validator_script_logfiles",
            f"{self.runfolder_name}_samplesheet_validator.log",
        )
        self.logfiles_config = {
            "sw": self.sw_runfolder_logfile,
            "demux": self.demultiplex_runfolder_logfile,
            "upload_flag": self.upload_flagfile,
            "backup": self.upload_runfolder_logfile,
            "project": self.proj_creation_script,
            "dx_run": self.runfolder_dx_run_script,
            "post_run_cmds": self.post_run_dx_run_script,
            "ss_validator": self.samplesheet_validator_logfile,
            "bcl2fastq2": self.bcl2fastqlog_file,
        }
        # Log files that sit outside the runfolder that require uploading
        self.logfiles_to_upload = [
            self.sw_runfolder_logfile,
            self.demultiplex_runfolder_logfile,
            self.proj_creation_script,
            self.runfolder_dx_run_script,
            self.samplesheet_validator_logfile,
            self.upload_runfolder_logfile,
        ]

    def add_runfolder_loggers(self, script: str) -> None:
        """
        Add runfolder loggers to runfolder object
            :param script (str):    Script name the function has been called from
            :return None:
        """
        loggers_obj = RunfolderLoggers(
            script, self.runfolder_name, self.logfiles_config
        )
        self.rf_loggers = loggers_obj.loggers

    def add_runfolder_logger(self, script: str, logger_name: str) -> None:
        """
        Add a single runfolder logger to runfolder object
            :param script (str):        Script name the function has been called from
            :param logger_name (str):   Name of the logger
            :return None:
        """
        logfile_config = {logger_name: self.logfiles_config[logger_name]}
        loggers_obj = RunfolderLoggers(__name__, self.runfolder_name, logfile_config)
        self.rf_loggers = loggers_obj.get_loggers()
