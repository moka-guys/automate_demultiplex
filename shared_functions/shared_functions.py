#!/usr/bin/python3
# coding=utf-8
"""
This script contains functions shared across scripts / modules
"""

import subprocess
import os
import config.ad_config as ad_config
import ad_logger.log_config as logger_config
import re
import ad_logger.ad_logger as ad_logger
import logging
from distutils.spawn import find_executable


# TODO amend the log flags script references - need to decide what to do here


def git_tag():
    """
    Obtain the git tag of the current commit
    """
    filepath = os.path.dirname(os.path.realpath(__file__))
    cmd = f"git -C {filepath} describe --tags"

    proc = subprocess.Popen(
        [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
    )
    out, _ = proc.communicate()
    #  Return standard out, removing any new line characters
    return out.rstrip().decode("utf-8")


def execute_subprocess_command(command: str, logger: logging.Logger):
    """
    Execute a subprocess
        :param command(str):            Input command
        :param logger(logging.Logger):  Logger
        :return (stdout(str),
        stderr(str),
        returncode(int))(tuple):        Outputs from the command
    """
    logger.info(
        logger_config.LOG_MSGS["shared_functions"]["executing_command"],
        command,
        extra={"flag": logger_config.LOG_FLAGS["info"] % "usw"},
    )
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


def check_returncode(proc, logger):
    """
    Check for success returncode and write to log accordingly
    """
    out, err = proc.communicate()
    out = out.decode("utf-8").strip()
    err = err.decode("utf-8").strip()
    returncode = proc.returncode

    if returncode == 0:
        logger.info(
            logger_config.LOG_MSGS["shared_functions"]["cmd_success"],
            returncode,
            extra={"flag": logger_config.LOG_FLAGS["info"] % "usw"},
        )
    else:
        logger.exception(
            logger_config.LOG_MSGS["shared_functions"]["cmd_fail"],
            returncode, out, err,
            extra={"flag": logger_config.LOG_FLAGS["fail"] % "usw"},
        )
    return out, err, returncode


def test_programs(software_name, logger):
    """Check upload agent exists in system path
    Uses distutils.spawn.find_executable package to assert the programs
    are callable by parsing the directories in the system PATH
    variable (i.e. bash `which` command)
    """
    # Raise error if any calls to find_executable() fail, or if the test command has
    # exit code other than 0 (success)
    software_dict = ad_config.TEST_PROGRAMS_DICT[software_name]
    logger.info(
        logger_config.LOG_MSGS["shared_functions"]["testing_software"],
        "bcl2fastq2",
        extra={"flag": logger_config.LOG_FLAGS["info"] % "usw"},
    )
    if find_executable(software_dict["executable"]):
        logger.info(
            logger_config.LOG_MSGS["shared_functions"]["found_program"],
            software_dict['executable'],
            extra={"flag": logger_config.LOG_FLAGS["info"] % "usw"},
            )
        out, err, returncode = execute_subprocess_command(
            software_dict["test_cmd"], logger
            )
        if returncode == 0:
            logger.info(
                logger_config.LOG_MSGS["shared_functions"]["test_pass"],
                software_name,
                extra={"flag": logger_config.LOG_FLAGS["info"] % "usw"},
            )
            return True
        else:
            logger.exception(
                logger_config.LOG_MSGS["shared_functions"]["test_fail"],
                software_name,
                extra={"flag": logger_config.LOG_FLAGS["fail"] % "usw"},
            )
            raise Exception  # Stop script
    else:
        logger.exception(
            logger_config.LOG_MSGS["shared_functions"]["program_missing"],
            software_dict['executable'],
            extra={"flag": logger_config.LOG_FLAGS["fail"] % "usw"},
        )
        raise Exception


class RunfolderObject(object):
    """
    An object with runfolder-specific properties.

    Args:
        runfolder_name (str):   Runfolder name string
        timestamp (str):        Timetamp in the format
                                str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
    """

    def __init__(self, runfolder_name, script_loggers, timestamp):
        """
        Constructor for the RunfolderObject class
        """
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token

        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.runfolderpath = os.path.join(ad_config.RUNFOLDERS, self.runfolder_name)
        self.samplesheet_name = ad_config.SAMPLESHEET_NAME % self.runfolder_name
        # Stored within runfolder
        # Sequencing finished file (within runfolder)
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["rtacomplete"]
        )
        # Samplesheet (within runfolder)
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        # Integrity check file (within runfolder)
        self.checksumfile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["md5checksum"]
        )
        # Bcl2fastq log file (within runfolder)
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["bcl2fastqlog"]
        )
        # Runfolder fastq folder (within runfolder)
        self.fastq_dir_path = os.path.join(self.runfolderpath, ad_config.DIRS["fastqs"])
        # Upload agent logfile (within runfolder). Stores runfolder upload logs
        self.upload_agent_logfile = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["upload_started"]
        )
        # Bcl2fastq stats file (within runfolder)
        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            ad_config.DIRS["bcl2fastq2_stats"],
            ad_config.FILENAMES["bcl2fastq2_stats"],
        )
        # Stored within samplesheets dir
        # Samplesheet (samplesheets dir)
        self.samplesheet_path = ad_config.SAMPLESHEET_PATH % self.runfolder_name

        # Stored within logfiles dir
        # Workflow dx run commands for runfolder (within logfiles dir)
        self.runfolder_dx_run_script = (
            logger_config.LOGFILES["dx_run_script"] % self.runfolder_name
        )
        # Congenica upload commands for runfolder (within logfiles dir)
        self.congenica_dx_run_script = (
            logger_config.LOGFILES["congenica_upload_script"] % self.runfolder_name
        )
        # Dnanexus project creation bash script (within logfiles dir)
        self.project_creation_logfile = (
            logger_config.LOGFILES["proj_creation_script"] % self.runfolder_name
        )
        # Backup runfolder logfile (within logfiles dir)
        self.backup_runfolder_logfile = (
            logger_config.LOGFILES["backup_runfolder"] % self.runfolder_name
        )
        self.decision_support_tool_logfiles = (
            logger_config.LOGFILES["decision_support_script_logs"] % self.runfolder_name
        )
        # Logfiles that contain timestamps - uses get_scriptlog() to search
        # for existing logfile containing runfolder name

        # Logfile to contain runfolder upload log
        self.upload_runfolder_logfile = self.get_runfolder_logs(
            logger_config.LOGDIRS["upload_script"],
            logger_config.LOGFILES["upload_script"] % self.runfolder_name,
        )
        # Logfile to contain runfolder demultiplex log
        self.demultiplex_runfolder_logfile = self.get_runfolder_logs(
            logger_config.LOGDIRS["demultiplex"],
            logger_config.LOGFILES["demultiplex_script_logfile"] % self.runfolder_name,
        )
        self.cluster_density_files = [
            os.path.join(
                self.runfolderpath,
                f"{self.runfolder_name}{ad_config.STRINGS['cd_file_suffix']}"
            ),
            os.path.join(
                self.runfolderpath,
                (
                    f"{self.runfolder_name}"
                    f"{ad_config.STRINGS['phasing_metrics_file_suffix']}"
                )
            ),
        ]
        self.logfiles_config = {
            "usw_rf": self.upload_runfolder_logfile,
            "demultiplex_rf": self.demultiplex_runfolder_logfile,
            "upload_agent": self.upload_agent_logfile,
            "backup": self.backup_runfolder_logfile,
            "project": self.project_creation_logfile,
            "dx_run": self.runfolder_dx_run_script,
        }
        self.script_loggers = script_loggers
        self.logfiles_to_upload = [
            self.upload_runfolder_logfile,
            self.demultiplex_runfolder_logfile,
            self.upload_agent_logfile,
            self.backup_runfolder_logfile,
            self.project_creation_logfile,
            self.runfolder_dx_run_script,
            self.bcl2fastqlog_path
        ]

    def get_runfolder_logs(self, directory, logfile):
        """
        Find the the logfile for the runfolder. Logfile contains an unknown
        timestamp. Search for any demultiplex logfiles matching the runfolder
        name and return the first
        If none exist, get the logfile from before it is renamed with
        processed runfolders
        """
        any_logs = [
            os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if self.runfolder_name in filename
        ]
        logfile = any_logs.pop() if any_logs else logfile
        return logfile

    def requires_processing(self):
        """
        Input = None
        This method calls other methods in order
        Returns = True if runfolder requires processing
        """
        # Check if already uploaded and demultiplexing finished sucessfully
        if (self.has_demultiplexed() and not self.already_uploaded()):
            self.script_loggers.usw_script.info(
                self.script_loggers.msgs["usw"]["runfolder_requires_proc"],
                self.runfolder_name,
                extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
            )
            return True
        else:
            self.script_loggers.usw_script.info(
                self.script_loggers.msgs["usw"]["runfolder_prev_proc"],
                self.runfolder_name,
                extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
            )
            return False

    def already_uploaded(self):
        """
        Input = None
        Upload agent stdout is written to a file, indicating that the runfolder
        has been processed.
        This function checks for presense of this file
        Returns = Boolean (True/False)
        """
        if os.path.isfile(self.upload_agent_logfile):
            self.script_loggers.usw_script.info(
                self.script_loggers.msgs["usw"]["ua_file_present"],
                extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
            )
            return True
        else:
            # If file doesn't exist return false to continue, write to log file
            self.script_loggers.usw_script.info(
                self.script_loggers.msgs["usw"]["ua_file_absent"],
                extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
            )
            return False

    def has_demultiplexed(self):
        """
        Input = runfolder object
        Check if demultiplexing has been performed and completed sucessfully.
        The demultiplexing script will raise any alerts if issues are found
        with demultiplexing, but we also need to prevent further processing
        of the run.
        Checks the demultiplex log file exists, and if present, checks the
        expected success string is in the last line of the log file.
        Returns = Boolean (True/False)
        """
        # Check demultiplexing log file exists
        if os.path.isfile(self.bcl2fastqlog_path):
            with open(self.bcl2fastqlog_path, "r", encoding="utf-8") as logfile:
                # Capture logfile into list (not doing this caused an issue
                # with the if loop below)
                logfile_list = logfile.readlines()
                if re.search(
                    ad_config.STRINGS['demultiplexlog_tso500_msg'], logfile_list[-1]
                ):
                    # Check if tso500 run
                    self.script_loggers.usw_script.info(
                        self.script_loggers.msgs["usw"]["tso_run"],
                        extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
                    )
                    return True
                # Check if successful demuliplex statement in last line of log
                elif re.search(
                    ad_config.STRINGS['demultiplex_success_regex'], logfile_list[-1]
                ):
                    self.script_loggers.usw_script.info(
                        self.script_loggers.msgs["usw"]["demux_complete"],
                        extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
                    )
                    return True
                else:
                    # Write to logfile that demultplex was not successful
                    self.script_loggers.usw_script.info(
                        self.script_loggers.msgs["usw"]["demux_failed"],
                        extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
                    )
                    return False
        else:
            # Write to logfile that not yet demultiplexed
            self.script_loggers.usw_script.info(
                self.script_loggers.msgs["usw"]["not_yet_demultiplexed"],
                extra={"flag": self.script_loggers.log_flags["info"] % "usw"},
            )
            return False

    def add_runfolder_loggers(self):
        """
        Add runfolder loggers to runfolder object
        """
        setattr(self, 'loggers', ad_logger.AdLoggers(self.logfiles_config))
