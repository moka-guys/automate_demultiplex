#!/usr/bin/python3
# coding=utf-8
"""
This script contains functions shared across scripts / modules
"""
import os
import re
import subprocess
import logging
from distutils.spawn import find_executable
from typing import Union
import config.ad_config as ad_config
import ad_logger.ad_logger as ad_logger


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
    logger.info(
        logger.log_msgs["executing_command"],
        command,
        extra={"flag": logger.log_flags["info"] % "usw"},
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
        logger.info(
            logger.log_msgs["cmd_success"],
            returncode,
            extra={"flag": logger.log_flags["info"] % "usw"},
        )
    else:
        logger.exception(
            logger.log_msgs["cmd_fail"],
            returncode, out, err,
            extra={"flag": logger.log_flags["fail"] % "usw"},
        )
    return out, err, returncode


def get_runfolder_path(runfolder_name):
    """
    """
    return os.path.join(ad_config.RUNFOLDERS, runfolder_name)


def test_programs(software_name: str, logger: object) -> Union[bool, None]:
    """
    Check software exists in path, and that the test command executes successfully
    (return code 0).
        :param software_name (str):     Name of the sofware being tested
        :param logger (object):         Logger
        :return True | None:              Return True if test passes, else return None
    """
    software_dict = ad_config.TEST_PROGRAMS_DICT[software_name]
    logger.info(
        logger.log_msgs["testing_software"],
        "bcl2fastq2",
        extra={"flag": logger.log_flags["info"] % "usw"},
    )
    if find_executable(software_dict["executable"]):
        logger.info(
            logger.log_msgs["found_program"],
            software_dict['executable'],
            extra={"flag": logger.log_flags["info"] % "usw"},
            )
        out, err, returncode = execute_subprocess_command(
            software_dict["test_cmd"], logger
            )
        if returncode == 0:
            logger.info(
                logger.log_msgs["test_pass"],
                software_name,
                extra={"flag": logger.log_flags["info"] % "usw"},
            )
            return True
        else:
            logger.exception(
                logger.log_msgs["test_fail"],
                software_name,
                extra={"flag": logger.log_flags["fail"] % "usw"},
            )
            raise Exception  # Stop script
    else:
        logger.exception(
            logger.log_msgs["program_missing"],
            software_dict['executable'],
            extra={"flag": logger.log_flags["fail"] % "usw"},
        )
        raise Exception


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
        "congenica_upload_script": os.path.join(  # DNAnexus run command script
            ad_config.AD_LOGDIR, "dx_run_commands",
            f"{runfoldername}_congenica.sh"
            ),
        # Script containing dnanexus project creation command
        "proj_creation_script": os.path.join(
            ad_config.AD_LOGDIR, "nexus_project_creation_scripts",
            f"create_nexus_project_{runfoldername}.sh"
            ),
        "decision_support_tool_logfile": os.path.join(
            ad_config.AD_LOGDIR, "decision_support_script_logfiles",
            f"decision_support_script_log_{runfoldername}.log"
            ),
    }


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
        runfolder_dx_run_script (str):          Workflow dx run commands for runfolder
                                                (within logfiles dir)
        congenica_dx_run_script (str):          Congenica upload commands for runfolder
                                                (within logfiles dir)
        proj_creation_script (str):             DNAnexus project creation bash script
                                                (within logfiles dir)
        backup_runfolder_logfile (str):         Backup runfolder logfile (within
                                                logfiles dir)
        decision_support_tool_logfile (str):    Decision support tool inputs script
                                                logfile (within logfiles dir)
        upload_runfolder_logfile (str):         Runfolder upload and setoff workflows
                                                logfile (within logfiles dir)
        demultiplex_runfolder_logfile (str):    Runfolder demultiplex logfile (within
                                                logfiles dir)
        cluster_density_files (list):           List containing runfolder lane metrics
                                                and phasing metrics file paths
        logfiles_config (dict):                 Contains all runfolder log files
        script_loggers (object):                AdLoggers object with script-level
                                                loggers
        logfiles_to_upload (list):              All logfiles that require upload to
                                                DNAnexus
        loggers (object):                       AdLogger object containing
                                                runfolder-specific loggers

    Methods
        requires_processing()
            Calls other methods to determine whether the runfolder requires processing
            (demultiplexing has finished successfully and the runfolder has not already
            been uploaded)
        already_uploaded()
            Checks for presence of upload agent logfile (denotes that the runfolder has
            already been processed).
        has_demultiplexed()
            Check if demultiplexing has already been performed and completed sucessfully
        add_runfolder_loggers()
            Add runfolder loggers to runfolder object
    """

    def __init__(self, runfolder_name: str, script_logger: object, timestamp: str):
        """
        Constructor for the RunfolderObject class
            :param runfolder_name (str):    Name of runfolder
            :param script_loggers (object): Script-level logger object with log_msgs 
                                            and log_flags attributes
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
        }
        self.script_logger = script_logger
        self.logfiles_to_upload = [
            self.upload_runfolder_logfile,
            self.demultiplex_runfolder_logfile,
            self.backup_runfolder_logfile,
            self.proj_creation_script,
            self.runfolder_dx_run_script,
            self.bcl2fastqlog_path
        ]

    def set_rf_logfiles(self):
        """"""
        for logfile, path in return_rflog_config(self.runfolder_name).items():
            setattr(self, logfile, path)

        
        # setattr(
        #     self, "runfolder_dx_run_script",
        #     ad_config.RFLOG_CONFIG["dx_run_script"] % self.runfolder_name
        # )
        # self. = (
        # )
        # self.congenica_dx_run_script = (
        #     ad_config.RFLOG_CONFIG["congenica_upload_script"] % self.runfolder_name
        # )
        # self.proj_creation_script = (
        #     ad_config.RFLOG_CONFIG["proj_creation_script"] % self.runfolder_name
        # )
        # self.backup_runfolder_logfile = (
        #     ad_config.RFLOG_CONFIG["backup"] % self.runfolder_name
        # )
        # self.decision_support_tool_logfile = (
        #     ad_config.RFLOG_CONFIG["decision_support_script_log"] % self.runfolder_name
        # )
        # self.upload_runfolder_logfile = (
        #     ad_config.RFLOG_CONFIG["usw"] % self.runfolder_name
        # )
        # self.demultiplex_runfolder_logfile = (
        #     ad_config.RFLOG_CONFIG["demultiplex_script_logfile"] % self.runfolder_name
        #     )

    def requires_processing(self) -> bool:
        """
        Calls other methods to determine whether the runfolder requires processing
        (demultiplexing has finished successfully and the runfolder has not already been
        uploaded)
            :return bool:  Returns true if runfolder requires processing, else False
        """
        if (self.has_demultiplexed() and not self.already_uploaded()):
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_requires_proc"],
                self.runfolder_name,
                extra={"flag": self.script_logger.log_flags["info"] % "usw"},
            )
            return True
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_prev_proc"],
                self.runfolder_name,
                extra={"flag": self.script_logger.log_flags["info"] % "usw"},
            )
            return False

    def already_uploaded(self) -> bool:
        """
        Checks for presence of upload agent logfile (denotes that the runfolder has
        already been processed).
            :return (bool):     Returns True if runfolder already uploaded, else False
        """
        if os.path.isfile(self.upload_agent_logfile):
            self.script_logger.info(
                self.script_logger.log_msgs["ua_file_present"],
                extra={"flag": self.script_logger.log_flags["info"] % "usw"},
            )
            return True
        else:
            # If file doesn't exist return false to continue, write to log file
            self.script_logger.info(
                self.script_logger.log_msgs["ua_file_absent"],
                extra={"flag": self.script_logger.log_flags["info"] % "usw"},
            )
            return False

    def has_demultiplexed(self) -> bool:
        """
        Check if demultiplexing has already been performed and completed sucessfully
        Checks the demultiplex log file exists, and if present checks the expected
        success string is in the last line of the log file.
            :return (bool):     Return True if runfolder already demultiplexed, else
                                False
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            with open(self.bcl2fastqlog_path, "r", encoding="utf-8") as logfile:
                logfile_list = logfile.readlines()
                completed_strs = [
                    ad_config.STRINGS['demultiplexlog_tso500_msg'],
                    ad_config.STRINGS['demultiplex_success']
                ]
                if any(
                    re.search(success_str, logfile_list[-1])
                    for success_str in completed_strs
                ):
                    self.script_logger.info(
                        self.script_logger.log_msgs["demux_complete"],
                        extra={"flag": self.script_logger.log_flags["info"] % "usw"},
                    )
                    return True
                else:
                    self.script_logger.info(
                        self.script_logger.log_msgs["demux_failed"],
                        extra={"flag": self.script_logger.log_flags["info"] % "usw"},
                    )
                    return False
        else:
            # Write to logfile that not yet demultiplexed
            self.script_logger.info(
                self.script_logger.log_msgs["not_yet_demultiplexed"],
                extra={"flag": self.script_logger.log_flags["info"] % "usw"},
            )
            return False

    def add_runfolder_loggers(self):
        """
        Add runfolder loggers to runfolder object
        """
        setattr(self, 'rf_loggers', ad_logger.AdLoggers(self.logfiles_config))
