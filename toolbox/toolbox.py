#!/usr/bin/python3
# coding=utf-8
"""
This script contains functions shared across scripts / modules
"""
import sys
import os
import subprocess
import logging
import argparse
from distutils.spawn import find_executable
from typing import Union
from config import ad_config
from ad_logger import ad_logger


# TODO improve README documentation


def script_start_logmsg(logger, file):
    """"""
    logger.info(
        logger.log_msgs["script_start"], git_tag(),
        os.path.basename(os.path.dirname(file))
    )


def script_end_logmsg(logger, file):
    """"""
    logger.info(
        logger.log_msgs["script_end"],
        git_tag(),
        os.path.basename(os.path.dirname(file))
    )


def is_valid_dir(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Check directory path is valid
        :param parser (argparse.ArgumentParser):    Holds necessary info to parse cmd
                                                    line into Python data types
        :param arg (str):                           Input argument
    """
    if not os.path.isdir(arg):
        parser.error(f"The directory {arg} does not exist!")
    else:
        return arg  # Return argument


def is_valid_file(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Check file path is valid
        :param parser (argparse.ArgumentParser):    Holds necessary info to parse cmd
                                                    line into Python data types
        :param arg (str):                           Input argument
    """
    if not os.path.exists(arg):
        parser.error(f"The file {arg} does not exist!")
    else:
        return arg  # Return argument


def git_tag():
    """
    Obtain the git tag of the current commit
        :return (str):  Git tag
    """
    filepath = os.path.dirname(os.path.realpath(__file__))
    cmd = f"git -C {filepath} describe --tags"

    proc = subprocess.Popen(
        [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
    )
    out, _ = proc.communicate()
    #  Return standard out, removing any new line characters
    return out.rstrip().decode("utf-8")


# TODO amend the log flags script references - need to decide what to do here
def execute_subprocess_command(command: str, logger: logging.Logger) -> (str, str, int):
    """
    Execute a subprocess
        :param command(str):            Input command
        :param logger(logging.Logger):  Logger
        :return (stdout(str),
        stderr(str),
        returncode(int))(tuple):        Outputs from the command
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

    # Capture the streams and return returncode
    return out, err, returncode


def check_returncode(proc: subprocess.Popen, logger: object) -> (str, str, int):
    """
    Check for success returncode and write to log accordingly
        :param proc (class):        subprocess.Popen class
        :param logger (object):     Logger
        :return (stdout(str),
        stderr(str),
        returncode(int))(tuple):    Stdout, stderr, returncode
        """
    out, err = proc.communicate()
    out = out.decode("utf-8").strip()
    err = err.decode("utf-8").strip()
    returncode = proc.returncode

    if returncode == 0:
        logger.info(logger.log_msgs["cmd_success"], returncode)
    else:
        logger.error(logger.log_msgs["cmd_fail"], returncode, out, err)
    return out, err, returncode


def get_runfolder_path(runfolder_name):
    """
    """
    return os.path.join(ad_config.RUNFOLDERS, runfolder_name)


def test_upload_software(logger) -> Union[bool, None]:
    """
    Test the required software is installed and performing
        :return True | None:    Return True if all software tests pass, else None
    """
    if test_programs("dx_toolkit", logger) and test_programs("upload_agent", logger):
        return True
    else:
        logger.error(logger.log_msgs["software_fail"])
        raise Exception


def test_processing_software(logger) -> Union[bool, None]:
    """
    Test the software is installed and performing, by calling the test_upload_agent
    and test_dx_toolkit functions
        :return True|None:  Return true if the tests all pass
    """
    if test_docker("bcl2fastq2", logger) and test_programs(
        "gatk_collect_lane_metrics", logger
    ):
        return True


def test_programs(software_name: str, logger: object) -> Union[bool, None]:
    """
    Check software exists in path, and that the test command executes successfully
    (return code 0).
        :param software_name (str):     Name of the sofware being tested
        :param logger (object):         Logger
        :return True | None:              Return True if test passes, else return None
    """
    software_dict = ad_config.TEST_PROGRAMS_DICT[software_name]

    logger.info(logger.log_msgs["testing_software"], software_name)

    if find_executable(software_dict["executable"]):
        logger.info(logger.log_msgs["found_program"], software_dict['executable'])
        out, err, returncode = execute_subprocess_command(
            software_dict["test_cmd"], logger
            )
        if returncode == 0:
            logger.info(logger.log_msgs["test_pass"], software_name)
            return True
        else:
            logger.error(logger.log_msgs["test_fail"], software_name)
            raise Exception  # Stop script
    else:
        logger.error(logger.log_msgs["program_missing"], software_dict['executable'])
        raise Exception  # Stop script


def test_docker(software_name: str, logger: object) -> Union[bool, None]:
    """
    """
    test_cmd = ad_config.TEST_IMAGES_DICT[software_name]

    logger.info(logger.log_msgs["testing_software"], software_name)

    out, err, returncode = execute_subprocess_command(test_cmd, logger)
    if returncode == 0:
        logger.info(logger.log_msgs["test_pass"], software_name)
        return True
    else:
        logger.error(logger.log_msgs["test_fail"], software_name)
        raise Exception  # Stop script


def return_scriptlogfile(logger_name):
    """
    Return 
    """
    SCRIPT_LOGS = {
        'demultiplex': os.path.join(  # Record demultiplex script logs
            ad_config.AD_LOGDIR, "demultiplexing_script_logfiles",
            f"{ad_config.TIMESTAMP}_demultiplex_script_log.log"
            ),
        'usw': os.path.join(  # Record usw script logs
            ad_config.AD_LOGDIR, "usw_script_logfiles",
            f"{ad_config.TIMESTAMP}_upload_and_setoff_workflow.log"
        ),
    }
    return SCRIPT_LOGS[logger_name]


def return_rflog_config(runfoldername):
    """
    Return runfolder-level logfile configuration
    """
    return {
        "demultiplex_runfolder_logfile": os.path.join(  # Record demultiplex script logs
            ad_config.AD_LOGDIR, "demultiplexing_script_logfiles",
            f"{runfoldername}_demultiplex_script_log.log"
            ),
        # Records output of upload and setoff workflow script
        "upload_runfolder_logfile": os.path.join(
            ad_config.AD_LOGDIR, "usw_script_logfiles",
            f"{runfoldername}_upload_and_setoff_workflow.log"
            ),
        # Records the logs from the backup runfolder script
        "backup_runfolder_logfile": os.path.join(
            ad_config.AD_LOGDIR, "backup_runfolder_script_logfiles",
            f"{runfoldername}_backup_runfolder.log"
            ),
        "runfolder_dx_run_script": os.path.join(
            ad_config.AD_LOGDIR, "dx_run_commands",
            f"{runfoldername}_dx_run_commands.sh"
            ),
        "post_run_dx_run_script": os.path.join(
            ad_config.AD_LOGDIR, "dx_run_commands",
            f"{runfoldername}_post_run_commands.sh"
            ),
        "congenica_dx_run_script": os.path.join(  # DNAnexus run command script
            ad_config.AD_LOGDIR, "dx_run_commands",
            f"{runfoldername}_congenica.sh"
            ),
        # Script containing dnanexus project creation command
        "proj_creation_script": os.path.join(
            ad_config.AD_LOGDIR, "nexus_project_creation_scripts",
            f"{runfoldername}_create_nexus_project.sh"
            ),
        "decision_support_tool_logfile": os.path.join(
            ad_config.AD_LOGDIR, "decision_support_script_logfiles",
            f"{runfoldername}_decision_support_script_log.log"
            ),
        "samplesheet_validator_logfile": os.path.join(
            ad_config.AD_LOGDIR, "samplesheet_validator_script_logfiles",
            f"{runfoldername}_samplesheet_validator_script_log.log"
        )
    }


def get_num_processed_runfolders(logger, script_name, processed_runfolders):
    """
    Set self.num_processed_runfolders
        :return num_processed_runfolders (int): Number of processed runfolders
    """
    num_processed_runfolders = len(processed_runfolders)
    logger.info(
        logger.log_msgs["runfolders_processed"],
        num_processed_runfolders,
        ", ".join(processed_runfolders),
    )
    return num_processed_runfolders


class RunfolderObject(object):
    """
    An object with runfolder-specific properties.

    Attributes
        dnanexus_apikey (str):                  DNAnexus auth token
        timestamp (str):                        Timestamp in the format
                                                str(f"{datetime.datetime.now():
                                                %Y%m%d_%H%M%S}")
        runfolder_name (str):                   Runfolder name string
        runfolderpath (str):                    Runfolder path
        samplesheet_name (str):                 Name of runfolder samplesheet
        rtacompletefile_path (str):             Sequencing finished filepath (within
                                                runfolder)
        runfolder_samplesheet_path (str):       Runfolder samplesheet path (within
                                                runfolder)
        checksumfile_path (str):                md5 checksum (integrity check) file path
                                                (within runfolder)
        bcl2fastqlog_path (str):                bcl2fastq2 logfile path (within
                                                runfolder)
        fastq_dir_path (str):                   Runfolder fastq directory path (within
                                                runfolder)
        upload_agent_logfile (str):             Upload agent logfile (within runfolder).
                                                Stores runfolder upload logs
        bcl2fastqstats_file (str):              Bcl2fastq stats file (within runfolder)
        samplesheet_path (str):                 Runfolder samplesheet (within
                                                samplesheets dir)
        demultiplex_runfolder_logfile (str):    Runfolder demultiplex logfile (within
                                                logfiles dir)
        upload_runfolder_logfile (str):         Runfolder upload and setoff workflows
                                                logfile (within logfiles dir)
        backup_runfolder_logfile (str):         Backup runfolder logfile (within
                                                logfiles dir)
        runfolder_dx_run_script (str):          Workflow dx run commands for runfolder
                                                (within logfiles dir)
        post_run_dx_run_script (str):           Separate DX run script for downstream
                                                processing apps (TSO only)
        congenica_dx_run_script (str):          Congenica upload commands for runfolder
                                                (within logfiles dir)
        proj_creation_script (str):             DNAnexus project creation bash script
                                                (within logfiles dir)
        decision_support_tool_logfile (str):    Decision support tool inputs script
                                                logfile (within logfiles dir)
        samplesheet_validator_logfile (str):    Samplesheet validator script logfile
                                                (within logfiles dir)
        cluster_density_files (list):           List containing runfolder lane metrics
                                                and phasing metrics file paths
        logfiles_config (dict):                 Contains all runfolder log files
        logfiles_to_upload (list):              All logfiles that require upload to
                                                DNAnexus
        logfile (path):                         One per runfolder logfile
        rf_loggers (object):                    RunfolderLoggers object containing
                                                runfolder-specific loggers

    Methods
        set_rf_logfiles()
            Add runfolder log files as class atributes
        add_runfolder_loggers()
            Add runfolder loggers to runfolder object
    """

    def __init__(self, runfolder_name: str, timestamp: str):
        """
        Constructor for the RunfolderObject class
            :param runfolder_name (str):    Name of runfolder
            :param timestamp (str):         Timestamp in the format
                                            str(f"{datetime.datetime.now():
                                            %Y%m%d_%H%M%S}")
        """
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()
        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.runfolderpath = get_runfolder_path(self.runfolder_name)
        self.samplesheet_name = f"{self.runfolder_name}_SampleSheet.csv"
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, "RTAComplete.txt",  # Sequencing complete file
        )
        self.samplesheet_path = os.path.join(
                ad_config.RUNFOLDERS, "samplesheets", self.samplesheet_name
            )
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        self.checksumfile_path = os.path.join(
            self.runfolderpath, "md5checksum.txt",  # File holding checksum results
        )
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, "bcl2fastq2_output.log",  # Holds bcl2fastq2 logs
        )
        # TODO change so that this is one variable decided by runfolder type
        self.fastq_dir_path = os.path.join(
            self.runfolderpath, ad_config.FASTQ_DIRS["fastqs"]
            )
        self.tso_fastq_dir_path = os.path.join(
            self.runfolderpath, ad_config.FASTQ_DIRS["tso_fastqs"]
        )
        self.upload_agent_logfile = os.path.join(
            self.runfolderpath, "DNANexus_upload_started.txt",  # Holds UA output
        )
        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            "Data/Intensities/BaseCalls/Stats/Stats.json",
        )
        self.set_rf_logfiles()
        self.cluster_density_files = [
            os.path.join(
                self.runfolderpath,
                f"{self.runfolder_name}{ad_config.STRINGS['lane_metrics_suffix']}"
            ),
            os.path.join(
                self.runfolderpath,
                (
                    f"{self.runfolder_name}"
                    f"{ad_config.STRINGS['phasing_metrics_suffix']}"
                )
            ),
        ]
        self.logfiles_config = {
            "usw": self.upload_runfolder_logfile,
            "demultiplex": self.demultiplex_runfolder_logfile,
            "upload_agent": self.upload_agent_logfile,
            "backup": self.backup_runfolder_logfile,
            "project": self.proj_creation_script,
            "dx_run": self.runfolder_dx_run_script,
            "post_run_cmds": self.post_run_dx_run_script,
            "decision_support": self.decision_support_tool_logfile,
            "ss_validator": self.samplesheet_validator_logfile,
        }
        self.logfiles_to_upload = [
            self.upload_runfolder_logfile,
            self.demultiplex_runfolder_logfile,
            self.backup_runfolder_logfile,
            self.proj_creation_script,
            self.runfolder_dx_run_script,
            self.post_run_dx_run_script,
            self.decision_support_tool_logfile,
            self.samplesheet_validator_logfile,
            self.bcl2fastqlog_path,
        ]

    def set_rf_logfiles(self) -> None:
        """
        Add runfolder log files as class atributes
            :return None:
        """
        for logfile, path in return_rflog_config(self.runfolder_name).items():
            setattr(self, logfile, path)

    def add_runfolder_loggers(self) -> None:
        """
        Add runfolder loggers to runfolder object
            :return None:
        """
        setattr(self, 'rf_loggers', ad_logger.RunfolderLoggers(self.logfiles_config))

    def add_runfolder_logger(self, logger_name) -> None:
        """
        Add a single runfolder logger to runfolder object
            :return None:
        """
        logfile_config = {logger_name: self.logfiles_config[logger_name]}
        setattr(self, 'rf_loggers', ad_logger.RunfolderLoggers(logfile_config))
