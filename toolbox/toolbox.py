"""
This script contains functions and classes shared across scripts / modules. Contains the following classes:

- RunfolderObject:
    An object with runfolder-specific properties

- RunfolderSamples
    An object with properties derived from the samples names in the samplesheet

- SampleObject
    Collect sample-specific attributes for a sample
"""

import sys
import os
import re
import subprocess
import logging
import time
import json
import seglh_naming
from pathlib import Path
from typing import Tuple
from distutils.spawn import find_executable
from typing import Union, Optional
from config.ad_config import ToolboxConfig
from ad_logger.ad_logger import RunfolderLoggers
import gzip
import zlib


def get_credential(file: str) -> None:
    """
    File from which to read credential
        :param file (str):  Filepath
        :return None:
    """
    with open(file, "r") as to_read:
        credential = to_read.readline().rstrip()
        return credential


def write_lines(file: str, mode: str, lines: str) -> None:
    """
    Write line to newline of file
        :param file (str):          Filepath
        :param mode (str):          Mode to open the file in
        :param lines (str | list):  Line (/s)
        :return None:
    """
    if isinstance(lines, str):
        lines = [lines]
    with open(file, mode) as open_file:
        for line in lines:
            open_file.write(f"{line}\n")


def read_lines(file: str) -> None:
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
        "wscleaner": os.path.join(  # Record wscleaner script logs
            ToolboxConfig.AD_LOGDIR,
            "wscleaner_logs",
            f"{ToolboxConfig.TIMESTAMP}_wscleaner.log",
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
    
def get_sequencer_type(runfolder_name: str) -> str:
    """
    Returns the ID of sequencer run was loaded to based on runfolder name
        :param runfolder_name (str):    Runfolder name string
        :return (str):                  Sequencer type string
    """
    if ToolboxConfig.AVITI_ID in runfolder_name:
        return ToolboxConfig.AVITI_ID
    else:
        return ToolboxConfig.NOVASEQ_ID
    
def get_samplesheet_name(sequencer_type: str, runfolder_name: str,aviti_runparameters_file: str) -> str:
    """
    Return the name of the samplesheet based on sequencer type. If Illumina find runfolder_Samplesheet.csv
    If AVITI, uses the RunParameters.json file to construct the samplesheet file name.
        :param sequencer_type (str):            Sequencer type string
        :param runfolder_name (str):            Runfolder name string
        :param aviti_runparameters_file (str):  RunParameters.json file string  
        :return (str):                          Samplesheet.csv string  
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        with open(aviti_runparameters_file, 'r') as file:
            runparameters_json = json.load(file)
            date = runparameters_json.get("Date").replace("-","")
            amended_date = date[2:8]
            instrument_name = runparameters_json.get("InstrumentName")
            side = runparameters_json.get("Side")[-1]
            flowcell = runparameters_json.get("FlowcellID")
        return f"{amended_date}_{instrument_name}_{side}{flowcell}_SampleSheet.csv"
    else:
        return f"{runfolder_name}_SampleSheet.csv"
    
def get_runfolder_path(sequencer_type: str, runfolder_name: str) -> str:
    """
    Return the path of the runfolder based on the sequencer type
        :param sequencer_type (str):    Sequencer type string
        :param runfolder_name (str):    Runfolder name string
        :return (str):                  Runfolder path
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        return os.path.join(ToolboxConfig.AVITI_RUNFOLDER, runfolder_name)
    else:
        return os.path.join(ToolboxConfig.RUNFOLDERS, runfolder_name)

def get_runcompletefile_path(sequencer_type: str, runfolderpath: str) -> str:
    """
    Return run complete file path based on seqeuncer used
        :param sequencer_type           Sequencer type string
        :param runfolderpath (str):     Runfolder path string
        :return (str):                  RTAComplete.txt/RunUploaded.json path
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        return os.path.join(
            runfolderpath, ToolboxConfig.FLAG_FILES["aviti_seq_complete"]
        )
    else:
        return os.path.join(
            runfolderpath, ToolboxConfig.FLAG_FILES["illumina_seq_complete"]
        )

def get_samplesheet_path(sequencer_type: str,samplesheet_name: str) -> str:
    """
    Return tech team uploaded samplesheet filepath based on sequencer used - 
    filepath necessary for Illumina runs but not AVITI 
        :param sequencer_type           Sequencer type string
        :param samplesheet_name (str):  Samplesheet name string
        :return (str):                  Samplesheet file path
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        return os.path.join(
            ToolboxConfig.AVITI_SAMPLESHEET, samplesheet_name
        )
    else:
        return os.path.join(
            ToolboxConfig.RUNFOLDERS, "samplesheets", samplesheet_name
        )

def get_demultiplexlog_file(sequencer_type: str, runfolderpath: str) -> str:
    """
    Returns name of demultiplex log file based on demultiplex tool needed
        :param sequencer_type           Sequencer type string
        :param runfolderpath (str):     Runfolder path string
        :return (str):                  bclconvert/bases2fastq log file string
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        return os.path.join(
            runfolderpath, ToolboxConfig.FLAG_FILES["bases2fastqlog"]
        )
    else:
        return os.path.join(
            runfolderpath, ToolboxConfig.FLAG_FILES["bclconvertlog"]
        )

def create_aviti_outputpath(runfolderpath: str) -> str:
    """
    Checks to see if bases2fastq output directory has been made, if
    not then creates output directory
        :param runfolderpath (str):     Runfolder path string
        :return (str):                  Fastq output folder string
    """  
    fastq_outputpath = os.path.join(runfolderpath, "Fastq")
    if os.path.exists(fastq_outputpath):
        return fastq_outputpath
    else:
        os.mkdir(fastq_outputpath)
        return fastq_outputpath

def get_fastq_dir_path(sequencer_type: str, runfolderpath: str) -> str:
    """
    Returns filepath for fastqs for demultiplexing based on sequencer used
        :param sequencer_type           Sequencer type string
        :param runfolderpath (str):     Runfolder path string
        :return (str):                  Fastq directory path string
    """
    if sequencer_type == ToolboxConfig.AVITI_ID:
        return os.path.join(
            runfolderpath, ToolboxConfig.FASTQ_DIRS["aviti_fastqs"]
        )
    else:
        return os.path.join(
            runfolderpath, ToolboxConfig.FASTQ_DIRS["illumina_fastqs"]
        )
    
def test_upload_software(logger: logging.Logger) -> True:
    """
    Test the required software is installed and performing. If not, exit the script
        :return True | None:    Return True if all software tests pass, else None
    """
    if test_programs("dx_toolkit", logger) and test_programs("upload_agent", logger):
        return True
    else:
        logger.error(logger.log_msgs["software_fail"])
        sys.exit(1)


def test_processing_software(logger: logging.Logger) -> Optional[bool]:
    """
    Test the software is installed and performing, by calling the test_upload_agent
    and test_dx_toolkit functions
        :return True|None:  Return true if the tests all pass
    """
    
    if test_programs("gatk_collect_lane_metrics", logger) and test_programs(
        "bclconvert", logger) and test_programs (
        "bases2fastq", logger):
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


def get_samplename_dict(
    logger: logging.Logger, samplesheet_path: str
) -> Optional[dict]:
    """
    Read SampleSheet to create a dict of samples and their pan numbers for the
    run. Reads file into list and loops through in reverse allowing us to access
    sample names and stop at column headers, skipping the file header
        :param logger (logging.Logger): Logger
        :param samplesheet_path (str):  Path to samplesheet
        :return samplename_dict (dict): Dict of sample names identified from the
                                        SampleSheet, and their pan numbers
    """
    samplename_dict = {}
    if os.path.exists(samplesheet_path):
        reversed_samplesheet = reversed(read_lines(samplesheet_path))
        for line in reversed_samplesheet:
            if line.startswith(("Sample_ID", "SampleName", "[Data],", "#",)):
                break
            # Skip empty lines (check first element of the line, after splitting on comma)
            elif len(line.split(",")[0]) < 2:
                pass
            else:  # If it's a line detailing a sample, get sample name and pan num
                panel_number = ""
                sample_name = line.split(",")[0]
                for pannum in ToolboxConfig.PANELS:
                    if pannum in line:
                        panel_number = pannum
                    samplename_dict[sample_name] = panel_number
        if samplename_dict:  # If samples identified
            return samplename_dict
    else:
        logger.error(logger.log_msgs["ss_missing"])


def validate_fastq_gzip(file_path: str, logger: logging.Logger) -> Optional[bool]:
    """
    Fast gzip validation with basic FASTQ structure checks
        :param file_path (str): Path to the FASTQ file
        :param logger (logging.Logger): Logger
        :return (bool, str): True if valid, False and error message if not
    """
    try:
        # Check compressed file header (magic number check)
        with open(file_path, 'rb') as f:
            magic = f.read(2)
            if magic != b'\x1f\x8b':
                return False, f"Invalid gzip magic bytes: {magic.hex()}"
            
            # Check footer (last 4 bytes for ISIZE)
            f.seek(-4, 2)
            isize = int.from_bytes(f.read(4), 'little')
            if isize == 0:
                return False, "Invalid zero uncompressed size"

        # Quick decompression check of first block
        with gzip.open(file_path, 'rb') as f:
            # Read first 4 lines (1 FASTQ record)
            lines = []
            for _ in range(4):
                line = f.readline().strip()
                if not line:  # Handle empty lines early
                    return False, "Incomplete FASTQ record"
                lines.append(line)
            
            # Basic FASTQ structure validation
            if len(lines) != 4:
                return False, "Invalid FASTQ: Not enough lines for complete record"
            if not lines[0].startswith(b'@'):
                return False, "Invalid FASTQ: Missing @ header"
            if not lines[2].startswith(b'+'):
                return False, "Invalid FASTQ: Missing + separator"
            if len(lines[1]) != len(lines[3]):
                return False, "Invalid FASTQ: Sequence/quality length mismatch"

        return True, None
        
    except (OSError, EOFError, zlib.error) as e:
        return False, f"Validation error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def validate_fastqs(fastq_dir_path: str, logger: logging.Logger) -> Optional[bool]:
    """
    Validate the created fastqs in the BaseCalls directory and log success
    or failure error message accordingly. If any failure, remove demultiplex log
    file to trigger re-demultiplex on next script run
        :param fastq_dir_path (str):    Runfolder fastq directory path (within runfolder)
        :param logger (logging.Logger): Logger
        :return Optional[bool]:         Return True if fastqs are all determined to be valid
    """
    fastqs = sorted([x for x in os.listdir(fastq_dir_path) if x.endswith("fastq.gz")])
    returncodes = []

    for fastq in fastqs:
        full_path = os.path.join(fastq_dir_path, fastq)
        is_valid, error_msg = validate_fastq_gzip(full_path, logger)
        
        if is_valid:
            logger.info(
                logger.log_msgs["fastq_valid"],
                fastq,
            )
            returncodes.append(True)
        else:
            logger.error(
                logger.log_msgs["fastq_invalid"],
                fastq,
                error_msg,
            )
            returncodes.append(False)

    if all(returncodes):
        logger.info(logger.log_msgs["demux_success"])
        return True

class RunfolderObject(ToolboxConfig):
    """
    An object with runfolder-specific properties

    Attributes
        dnanexus_auth (str):                    DNAnexus auth token
        timestamp (str):                        Timestamp in the format str(f"{datetime.datetime.now():
                                                %Y%m%d_%H%M%S}")
        runfolder_name (str):                   Runfolder name string
        sequencer_type (str):                   Sequencer ID string
        runfolderpath (str):                    Path of runfolder on workstation
        aviti_runparameters_file (str):         RunParameters.json path string for AVITI runs (within runfolder)
        samplesheet_name (str):                 Name of runfolder SampleSheet
        rtacompletefile_path (str):             Sequencing finished filepath (within runfolder)
        samplesheet_path (str):                 Path to SampleSheet in SampleSheets dir
        runfolder_samplesheet_path (str):       Runfolder SampleSheets path (within runfolder)
        checksumfile_path (str):                md5 checksum (integrity check) file path (within runfolder)
        initial_sscheck_flagfile_path (str):    initial Samplesheet check flag file path (within runfolder)
        sscheck_flagfile_path (str):            2nd attempt Samplesheet check flag file path (within runfolder)
        demultiplexlog_file (str):              Demultiplex logfile path - bases2fastq/bclconvert (within runfolder)
        fastq_dir_path (str):                   Runfolder fastq directory path (within runfolder)
        upload_flagfile (str):                  Flag file denoting upload has begun (within runfolder)
        bclconvertstats_file (str):             Bclconvert stats file (within runfolder)
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
        logfiles_to_upload (list):              All logfiles that require upload to DNAnexus

    Methods
        get_runfolder_loggers(script)
            Return dictionary of logger.Logging objects for the runfolder
    """

    def __init__(self, runfolder_name: str, timestamp: str):
        """
        Constructor for the RunfolderObject class
            :param runfolder_name (str):    Runfolder name
            :param timestamp (str):         Timestamp in the format str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
        """
        self.dnanexus_auth = get_credential(
            ToolboxConfig.CREDENTIALS["dnanexus_authtoken"]
        )
        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.sequencer_type = get_sequencer_type(self.runfolder_name)
        self.runfolderpath = get_runfolder_path(self.sequencer_type, self.runfolder_name)
        self.aviti_runparameters_file = os.path.join(
            self.runfolderpath, "RunParameters.json"
        )
        self.samplesheet_name = get_samplesheet_name(self.sequencer_type, self.runfolder_name, self.aviti_runparameters_file)
        self.runcompletefile_path = get_runcompletefile_path(self.sequencer_type, self.runfolderpath)
        self.samplesheet_path = get_samplesheet_path(self.sequencer_type, self.samplesheet_name)
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        self.masterfile_name = f"{self.runfolder_name}_MasterDataFile.xlsx"
        self.masterfile_path = os.path.join(
            ToolboxConfig.RUNFOLDERS, "samplesheets", self.masterfile_name
        )
        self.runfolder_masterfile_path = os.path.join(
            self.runfolderpath, self.masterfile_name
        )
        self.checksumfile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["md5checksum"]
        )
        self.initial_sscheck_flagfile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["initial_sscheck_flag"]
        )
        self.sscheck_flagfile_path = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["sscheck_flag"]
        )
        self.demultiplexlog_file = get_demultiplexlog_file(self.sequencer_type, self.runfolderpath)
        self.bases2fastq_log_output = os.path.join(
            self.runfolderpath, "Fastq", "info", "Bases2Fastq.log"
        )
        self.fastq_dir_path = get_fastq_dir_path(self.sequencer_type, self.runfolderpath)
        self.bases2fastq_outputpath = create_aviti_outputpath(self.runfolderpath)
        self.upload_flagfile = os.path.join(
            self.runfolderpath, ToolboxConfig.FLAG_FILES["upload_started"]
        )
        bclconvert_stats = [
            "Adapter_Cycle_Metrics.csv", "Adapter_Metrics.csv",
            "Demultiplex_Stats.csv", "fastq_list.csv", "Index_Hopping_Counts.csv", 
            "IndexMetricsOut.bin", "Quality_Metrics.csv", "Quality_Tile_Metrics.csv", 
            "RunInfo.xml", "SampleSheet.csv", "Top_Unknown_Barcodes.csv"
        ]
        self.bclconvertstats_file = []
        for stats in bclconvert_stats:
            self.bclconvertstats_file.append(
                os.path.join(
                    self.runfolderpath,
                    f"Data/Intensities/BaseCalls/Reports/{stats}", 
            )
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
            "backup": self.upload_runfolder_logfile,
            "demultiplex_docker_log": self.demultiplexlog_file,
            "ss_validator": self.samplesheet_validator_logfile,
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

    def age(self) -> int:
        """
        Return runfolder age in days
            :return age (int):  Runfolder age in days
        """
        return (time.time() - Path(self.runfolderpath).stat().st_mtime) // (24 * 3600)

    def get_runfolder_loggers(self, script: str) -> dict:
        """
        Return dictionary of logger.Logging objects for the runfolder
            :param script (str):            Script name the function has been called from
            :return (dict):                 Dictionary of logger.Logging objects
        """
        loggers_obj = RunfolderLoggers(
            script, self.runfolder_name, self.logfiles_config
        )
        return loggers_obj.loggers


class RunfolderSamples(ToolboxConfig):
    """
    An object with properties derived from the sample names in the samplesheet

    Attributes
        sequencer_type (str):               Sequencer ID
        samplesheet_name (str):             Samplesheet name string
        samplesheet_path (str):             Path to SampleSheet in SampleSheets dir
        runfolder_name (str):               Runfolder name string
        fastq_dir_path (str):               Runfolder fastq directory path (within runfolder)
        logger (logging.Logger):            Logger
        samplename_dict (dict):             Dict of sample names identified from the
                                            SampleSheet, and their pan numbers
        pipeline (str):                     Pipeline name
        runtype_str (str):                  Runtype name string
        nexus_runfolder_suffix (str):       String of '_' delimited unique library numbers,
                                            and WES batch numbers if run is a WES run
        nexus_paths (dict):                 Dictionary of paths within the DNAnexus project
                                            that are required for building dx commands
        unique_pannos (set):                Set of unique panel numbers within the run
        samples_dict (dict):                Dictionary of SampleObject per sample,
                                            containing sample-specific attributes
        fastqs_list (list):                 List of all sample fastqs in the run
        fastqs_str (str):                   Space separated string of sample fastqs with
                                            each fastq encased in quotation marks
        undetermined_fastqs_list (list):    List of all undetermined fastqs in the run
        undetermined_fastqs_str (str)       Space separated string of all undetermined fastqs
                                            in the run, with each fastq encased in quotation marks

    Methods
        get_pipeline()
            Use samplename_dict and the ToolboxConfig.PANEL_DICT to get the pipeline name for
            samples in the run
        get_runtype()
            Use self.samplename_dict and the ToolboxConfig.PANEL_DICT to get a list of runtype
            names for samples in the run. Returns the most frequent runtype name in the set
        get_nexus_runfolder_suffix()
            Get the runfolder suffix for the DNAnexus project name
        capture_library_numbers()
            Parse the names in self.samplename_dict to identify the library prep numbers
        capture_wes_batch_numbers()
            Parse the names in self.samplename_dict to identify the WES batch numbers
        get_nexus_paths()
            Build nexus paths, using NGS run numbers (and batch numbers in the case of WES)
        get_unique_pannos()
            Return set of unique pan numbers for samples within the run
        get_samples_dict()
            Create a SampleObject per sample, containing sample-specific properties, and
            add each SampleObject to a larger samples_dict
        check_for_missing_fastqs()
            Validate the fastqs in the BaseCalls directory by checking that all sample fastqs
            match a sample name from the self.samplename_dict
        fastq_not_undetermined(fastq_dir_file)
            Determine whether the fastq is an undetermined fastq
        get_fastqs_list()
            Return a list of sample fastqs for the run
        get_fastqs_str(fastqs_list)
            Return a space separated string of fastqs with each fastq encased in quotation marks
        get_undetermined_fastqs_list()
            Return a list of undetermined fastqs for the run
    """

    def __init__(self, rf_obj: object, logger: logging.Logger):
        """
        Constructor for the RunfolderSamples class
            :param rf_obj (object):     RunfolderObject object (contains runfolder-specific attributes)
            :logger (logging.Logger):   Logger
        """
        self.sequencer_type = rf_obj.sequencer_type
        self.samplesheet_name = rf_obj.samplesheet_name
        self.samplesheet_path = rf_obj.samplesheet_path
        self.runfolder_name = rf_obj.runfolder_name
        self.fastq_dir_path = rf_obj.fastq_dir_path
        self.logger = logger
        self.samplename_dict = get_samplename_dict(self.logger, self.samplesheet_path)
        self.pipeline = self.get_pipeline()
        self.runtype_str = self.get_runtype()
        self.nexus_runfolder_suffix = self.get_nexus_runfolder_suffix()
        self.nexus_paths = self.get_nexus_paths(self.sequencer_type)
        self.unique_pannos = self.get_unique_pannos()
        self.samples_dict = self.get_samples_dict()
        self.check_for_missing_fastqs()
        self.fastqs_list = self.get_fastqs_list()
        self.fastqs_str = self.get_fastqs_str(self.fastqs_list)
        self.undetermined_fastqs_list = self.get_undetermined_fastqs_list()
        self.undetermined_fastqs_str = self.get_fastqs_str(
            self.undetermined_fastqs_list
            )

    def get_pipeline(self) -> Optional[str]:
        """
        Use samplename_dict and the ToolboxConfig.PANEL_DICT to get a list of pipeline
        names for samples in the run. Generates error mesage if there is more than one
        pipeline name in the list. Returns the most frequent pipeline name in the set
            :return pipeline_name (Optional[str]):    Pipeline name if only one pipeline name in list
        """
        if self.samplename_dict:
            try:
                pipelines_list = []
                for sample, panno in self.samplename_dict.items():
                    pipelines_list.append(ToolboxConfig.PANEL_DICT[panno]["pipeline"])
                pipelines_list = sorted(list(set(pipelines_list)))
                if len(pipelines_list) > 1:
                    self.logger.error(
                        self.logger.log_msgs["multiple_pipeline_names"],
                        pipelines_list,
                        ToolboxConfig.PIPELINES,
                    )
                else:
                    pipeline_name = pipelines_list[0]  # Get pipeline from pipelines_list
                    self.logger.debug(
                        self.logger.log_msgs["pipeline_name"],
                        pipeline_name,
                    )
                return pipeline_name
            except Exception:
                return None

    def get_runtype(self) -> str:
        """
        Use samplename_dict and the ToolboxConfig.PANEL_DICT to get the runtype for samples
        in the run for Custom Panels and WES runs where sample types vary (VCP1/2/3/WES/WES EB)
            :return runtype_str (str):      Runtype name string
        """
        if self.samplename_dict:
            try:
                runtype_list = []
                for sample, panno in self.samplename_dict.items():
                    runtype_list.append(ToolboxConfig.PANEL_DICT[panno]["runtype"])
                    if ToolboxConfig.PANEL_DICT[panno]["sample_prefix"]:
                        if all(ToolboxConfig.PANEL_DICT[panno]["sample_prefix"] not in runtype for runtype in runtype_list):
                            runtype_list.append(ToolboxConfig.PANEL_DICT[panno]["sample_prefix"])
                runtype_str = "_".join(sorted(list(set(runtype_list))))
                self.logger.debug(
                    self.logger.log_msgs["runtype_str"],
                    runtype_str,
                )
                return runtype_str
            except Exception:
                return None

    def get_nexus_runfolder_suffix(self) -> str:
        """
        Get the runfolder suffix for the DNAnexus project name. This consists of the
        library number (see capture_library_numbers docstring for explanation), followed by
        the WES batch if the run is a WES run, followed by the runtype (e.g. VCP1 / CP2)
            :return suffix (str):   String of '_' delimited unique library numbers, and WES
                                    batch numbers if run is a WES run, followed by the runtype
        """
        if self.samplename_dict:
            library_numbers = self.capture_library_numbers()

            if self.pipeline == "wes":
                library_numbers.extend(self.capture_wes_batch_numbers())

            if self.pipeline in ["gatk_pipe", "seglh_pipe", "wes", "dev"]:
                library_numbers.append(self.runtype_str)

            suffix = f"{'_'.join(library_numbers)}"  # Provides more detail on contents of runs in runfolder name
            return suffix

    def capture_library_numbers(self) -> list:
        """
        Parse the names in self.samplename_dict to identify the library prep numbers.
        These are the first elements in the sample names (before the first underscore).
        These numbers are used as the suffix for the DNAnexus project name (along with
        the WES batch number in the case of WES runs). If no library prep numbers are
        found, exit the script
            :return list:List of unique library numbers
        """
        library_numbers = []
        for samplename in self.samplename_dict.keys():
            if "_" in str(samplename):  # Check there are underscores present
                # Split on underscores to capture library number e.g. ONC100 or NGS100
                library_numbers.append(samplename.split("_")[0])
        if library_numbers:  # Should always be library numbers found
            self.logger.debug(
                self.logger.log_msgs["library_nos_identified"],
                ", ".join(sorted(list(set(library_numbers)))),
            )
            return sorted(list(set(library_numbers)))
        else:  # Prompt a slack alert
            self.logger.error(self.logger.log_msgs["library_no_err"])
            sys.exit(1)

    def capture_wes_batch_numbers(self) -> list:
        """
        Parse the names in self.samplename_dict to identify the WES batch numbers. This
        along with the library prep number is used as the DNAnexus project name suffix.
        If unsuccessful, exit the script
            :return wes_batch_numbers_list (list):  List of unique WES batch numbers
        """
        wes_batch_numbers_list = []
        for samplename in self.samplename_dict.keys():
            if "WES" in str(samplename):
                # Capture WES batch (WES followed by digits)
                # Optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", samplename).group()
                wes_batch_numbers_list.append(wesbatch.replace("_", ""))
        if wes_batch_numbers_list:
            self.logger.debug(
                self.logger.log_msgs["wes_batch_nos_identified"],
                ", ".join(wes_batch_numbers_list),
            )
            return sorted(list(set(wes_batch_numbers_list)))
        else:  # Prompt a slack alert
            self.logger.error(self.logger.log_msgs["wes_batch_nos_missing"])
            sys.exit(1)

    def get_nexus_paths(self, sequencer_type: str) -> dict:
        """
        Build nexus paths, using NGS run numbers (and batch numbers in the case of WES).
        Builds the DNAnexus project name using the config-defined project prefix (denoting
        status of the DNAnexus project), followed by the runfolder name and the and
        self.nexus_runfolder_suffix as the suffix (library prep / WES batch numbers). Uses
        the DNAnexus project name to build additional paths required for later dx run commands
            :return nexus_paths (dict): Dictionary of paths within the DNAnexus project
                                        that are required for building dx commands
        """
        nexus_paths = {}
        if self.pipeline == "tso500":
            fastq_type = "tso_fastqs"
        # Conditional added to reformat project name for AVITI runs (runfolder name leads to duplication) and
        # direct to correct fastq location
        elif sequencer_type == ToolboxConfig.AVITI_ID:
            fastq_type = "aviti_fastqs"
            amended_runfolder_name = self.samplesheet_name.replace("_SampleSheet.csv","")
        else:
            fastq_type = "illumina_fastqs"
            amended_runfolder_name = self.runfolder_name
        nexus_paths["proj_name"] = (
            f"{ToolboxConfig.DNANEXUS_PROJECT_PREFIX}{amended_runfolder_name}_{self.nexus_runfolder_suffix}"
        )
        nexus_paths["fastqs_dir"] = os.path.join(
            f"/{self.runfolder_name}", ToolboxConfig.FASTQ_DIRS[fastq_type]
        )
        nexus_paths["logfiles_dir"] = os.path.join(
            f"/{self.runfolder_name}", "automated_scripts_logfiles"
        )
        return nexus_paths

    def get_unique_pannos(self) -> Optional[list]:
        """
        Return set of unique pan numbers for samples within the run
            :return Optional[list]: List of unique pan numbers if samples identified, else None
        """
        if self.samplename_dict:
            return set(self.samplename_dict.values())

    def get_samples_dict(self) -> dict:
        """
        Create a SampleObject for each sample which returns a sample dictionary
        containing the sample_name, pannum, panel_settings and fastqs paths for that
        sample. Add each SampleObject to a larger samples_dict
            :return samples_dict (dict):    Dictionary of SampleObject per sample,
                                            containing sample-specific attributes
        """
        if self.samplename_dict:
            samples_dict = {}
            for sample_name in self.samplename_dict.keys():
                self.sample_obj = SampleObject(
                    sample_name,
                    self.pipeline,
                    self.logger,
                    self.fastq_dir_path,
                    self.nexus_paths,
                    self.nexus_runfolder_suffix,
                )
                if self.sample_obj.fastqs_dict:
                    samples_dict[sample_name] = self.sample_obj.return_sample_dict()
                else:
                    self.logger.warning(
                        self.logger.log_msgs["sample_excluded"],
                        sample_name,
                    )
            return samples_dict

    def check_for_missing_fastqs(self) -> None:
        """
        Validate the fastqs in the BaseCalls directory by checking that all sample fastqs
        match a sample name from the self.samplename_dict. If they do not, log an error
        and add to a missing_samples list. Add all samples in the missing samples list to
        the samples_dict so that they are processed
            :return None:
        """
        if self.samplename_dict:
            missing_samples = []
            for fastq_dir_file in os.listdir(self.fastq_dir_path):
                if os.path.isfile(fastq_dir_file):
                    if fastq_dir_file.endswith("fastq.gz"):
                        self.logger.info(
                            self.logger.log_msgs["checking_fastq"],
                            fastq_dir_file,
                        )
                        if self.fastq_not_undetermined(
                            fastq_dir_file
                        ):  # Exclude undetermined
                            try:
                                seglh_naming.Sample.from_string(fastq_dir_file)
                                sample_name = [
                                    sample_name
                                    for sample_name in self.samplename_dict.keys()
                                    if sample_name in fastq_dir_file
                                ]
                                if sample_name:
                                    self.logger.info(
                                        self.logger.log_msgs["sample_match"],
                                        fastq_dir_file,
                                        sample_name,
                                    )
                                else:
                                    self.logger.error(
                                        self.logger.log_msgs["sample_mismatch"],
                                        fastq_dir_file,
                                    )
                                    sample_name = re.sub(
                                        "R[0-9]_001.fastq.gz", "", fastq_dir_file
                                    )
                                    missing_samples.append(fastq_dir_file)
                            except ValueError as exception:
                                self.logger.error(
                                    self.logger.log_msgs["fastq_wrong_naming"],
                                    fastq_dir_file,
                                    exception,
                                )
                    else:
                        self.logger.info(
                            self.logger.log_msgs["not_fastq"],
                            fastq_dir_file,
                        )
            for sample_name in missing_samples:  # Add the sample to the sample_obj
                # Strip end off sample name
                sample_name = re.sub(r"_S[0-9]+_R[1-2]{1}_001.fastq.gz", "", sample_name)
                self.logger.info(self.logger.log_msgs["add_missing_sample"], sample_name)
                self.sample_obj = SampleObject(
                    sample_name,
                    self.pipeline,
                    self.logger,
                    self.fastq_dir_path,
                    self.nexus_paths,
                    self.nexus_runfolder_suffix,
                )
                self.samples_dict[sample_name] = self.sample_obj.return_sample_dict()

    def fastq_not_undetermined(self, fastq_dir_file: str) -> Optional[bool]:
        """
        Determine whether the fastq is an undetermined fastq
            :param fastq_dir_file (str):
            :return (Optional[bool]):    Return True if undetermined, else return None
        """
        if not fastq_dir_file.startswith("Undetermined"):
            return True
        else:
            self.logger.info(
                self.logger.log_msgs["undetermined_identified"],
                fastq_dir_file,
            )

    def get_fastqs_list(self) -> list:
        """
        Return a list of sample fastqs for the run
            :return fastqs_list (list): List of all sample fastqs in the run
        """
        if self.samples_dict:
            fastqs_list = []
            for sample_name in self.samples_dict.keys():
                if self.samples_dict[sample_name]["fastqs"]:
                    fastqs_list.extend(
                        [
                            self.samples_dict[sample_name]["fastqs"][read]["path"]
                            for read, path in self.samples_dict[sample_name][
                                "fastqs"
                            ].items()
                        ]
                    )
            return fastqs_list

    def get_fastqs_str(self, fastqs_list: list) -> str:
        """
        Return a space-separated string of fastqs with each fastq encased in quotation marks.
        This is used for runs / samples that are demultiplexed locally
            :param fastqs_list (list):  List of sample fastqs
            :return (str):              Space separated string of fastqs with
                                        each fastq encased in quotation marks
        """
        if fastqs_list:
            quotation_marked_list = []
            for fastq in fastqs_list:
                quotation_marked = f"'{fastq}'"
                quotation_marked_list.append(quotation_marked)
            return " ".join(quotation_marked_list)

    def get_undetermined_fastqs_list(self) -> list:
        """
        Return a list and string of undetermined fastqs for the run
            :return undetermined_fastqs_list (list): List of all undetermined fastqs in the run
        """
        undetermined_fastqs_list = []
        r1 = os.path.join(self.fastq_dir_path, "Undetermined_S0_R1_001.fastq.gz")
        r2 = os.path.join(self.fastq_dir_path, "Undetermined_S0_R2_001.fastq.gz")
        for fastq in [r1, r2]:
            if os.path.exists(fastq):
                undetermined_fastqs_list.append(fastq)
        return undetermined_fastqs_list


# TODO eventually adapt this class to use the SamplesheetValidator package
class SampleObject(ToolboxConfig):
    """
    Collect sample-specific attributes for a sample. Including sample-specific command strings
    for calling the pipeline and decision support tools where relevant

    Attributes
        sample_name (str):                  Sample name
        pipeline (str):                     Pipeline name
        logger (logging.Logger):            Logger
        fastq_dir_path (str):               Runfolder fastq directory path (within runfolder)
        nexus_paths (dict):                 Dictionary of paths within the DNAnexus project that
                                            are required for building dx commands
        nexus_runfolder_suffix (str):       String of '_' delimited unique library numbers,
                                            and WES batch numbers if run is a WES run
        neg_control (bool):                 True if sample is a negative control, else False
        pos_control (bool):                 True if sample is a reference sample, else False
        pannum (str):                       Panel number that matches a config-defined panel
                                            number, or None if pannum not valid
        panel_settings (dict):              Config defined panel settings specific to the sample panel number
        primary_identifier (str):           Primary sample identifier
        secondary_identifier (str):         Secondary sample identifier
        fastqs_dict (dict):                 Dictionary containing R1 and R2 fastqs and their
                                            local and cloud paths

    Methods
        check_control(identifiers, control_type)
            Determine whether sample contains the control identifier strings
        find_pannum()
            Extract panel number from sample name using regular expression
        return_panel_settings()
            Return panel settings for the specified pan number, if exists
        validate_pannum(pannum)
            Check whether pan number is valid
        get_identifiers()
            For WES and PIPE samples, extract DNA number from sample name. For oncology
            samples, collect 3rd and 4th identifiers, setting secondary_identifier to
            null if the sample is a negative or positive control (these only have one identifier)
        get_fastqs_dict()
            Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        get_fastq_paths(read)
            Get fastqs in fastq directory that correspond to each sample name in the
            sample dictionary. Build the fastq name, local path, and DNAnexus path
            for each fastq file
        return_sample_dict()
            Return sample dictionary with all collected information about the sample
    """

    def __init__(
        self,
        sample_name: str,
        pipeline: str,
        logger: logging.Logger,
        fastq_dir_path: str,
        nexus_paths: dict,
        nexus_runfolder_suffix: str,
    ):
        """
        Constructor for the SampleObject class. Calls the class methods
            :param sample_name (str):               Sample name
            :param pipeline (str):                  Pipeline name
            :param logger (logging.Logger):         Logger
            :param fastq_dir_path (str):            Runfolder fastq directory path (within runfolder)
            :param nexus_paths (dict):              Dictionary of paths within the DNAnexus project that are
                                                    required for building dx commands
            :param nexus_runfolder_suffix (str):    String of '_' delimited unique library numbers,
                                                    and WES batch numbers if run is a WES run
        """
        self.sample_name = sample_name
        self.pipeline = pipeline
        self.logger = logger
        self.fastq_dir_path = fastq_dir_path
        self.nexus_paths = nexus_paths
        self.nexus_runfolder_suffix = nexus_runfolder_suffix
        self.neg_control = self.check_control(ToolboxConfig.NTCON_IDS, "Negative")
        self.pos_control = self.check_control(ToolboxConfig.PSCON_IDS, "Positive")
        self.pannum = self.find_pannum()
        self.panel_settings = self.return_panel_settings()
        self.primary_identifier, self.secondary_identifier = self.get_identifiers()
        self.fastqs_dict = self.get_fastqs_dict()

    def check_control(self, identifiers: list, control_type: str) -> Optional[bool]:
        """
        Determine whether sample contains the control identifier strings
            :param identifiers (list):  List of identifiers for control type (used in sample naming)
            :param control_type (str):  String describing the type of control. e.g. Negative, Positive
            :return (Optional[bool]):   True if sample contains any specified identifier, else False
        """
        if any(identifier in self.sample_name for identifier in identifiers):
            self.logger.debug(
                self.logger.log_msgs["control_sample"],
                control_type,
                self.sample_name,
            )
            return True

    def find_pannum(self) -> Optional[str]:
        """
        Extract panel number from sample name using regular expression
            :return pannum (Optional[str]): Panel number that matches a config-defined
                                            panel number, or None if pannum not valid
        """
        # print(ToolboxConfig.PANEL_DICT[pannum]["panel_name"])
        try:
            pannum = str(re.search(r"Pan\d+", self.sample_name).group()).strip()
            if self.validate_pannum(pannum):
                self.logger.debug(
                    self.logger.log_msgs["sample_identified"],
                    ToolboxConfig.PANEL_DICT[pannum]["panel_name"],
                    self.sample_name,
                )
                return pannum
        except:
            self.logger.error(
                self.logger.log_msgs["missing_panno"],
                self.sample_name,
            )
    
    def return_panel_settings(self) -> Optional[dict]:
        """
        Return panel settings for the specified pan number, if exists
            :return Optional[dict]: Return dictionary containing panel settings for the Pan number
        """
        if self.pannum:
            return ToolboxConfig.PANEL_DICT[self.pannum]

    def validate_pannum(self, pannum: int) -> bool:
        """
        Check whether pan number is valid
            :return bool:   True if pan number is valid, else None
        """
        if str(pannum) in ToolboxConfig.PANELS:
            self.logger.debug(
                self.logger.log_msgs["recognised_panno"],
                self.sample_name,
                pannum,
            )
            return True
        else:
            self.logger.error(
                self.logger.log_msgs["unrecognised_panno"],
                self.sample_name,
            )
            sys.exit(1)

    def get_identifiers(self) -> Tuple[str, str]:
        """
        For WES and GATK/SENTIEON PIPE samples, extract DNA number from sample name. For oncology
        samples, collect 3rd and 4th identifiers, setting secondary_identifier to null
        if the sample is a positive or negative control (these only have one identifier)
            :return primary_identifier (str):    Primary sample identifier
            :return secondary_identifier (str):  Secondary sample identifier
        """
        primary_identifier, secondary_identifier = False, False
        if self.pipeline in ("wes", "gatk_pipe", "seglh_pipe", "snp"):
            # Extract the dna number from sample name
            primary_identifier = self.sample_name.split("_")[2]
            secondary_identifier = False  # Secondary identifiers are not input to Moka
        elif self.pipeline in ("tso500", "archerdx", "oncodeep", "msk"):
            # Collect 3rd and 4th elements (identifiers)
            primary_identifier, secondary_identifier = self.sample_name.split("_")[2:4]
            # Negative and positive controls only have one ID so set id2 to null
            if any([self.neg_control, self.pos_control]):
                secondary_identifier = "NULL"
        return primary_identifier, secondary_identifier

    def get_fastqs_dict(self) -> Optional[dict]:
        """
        Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        tso500 runs are not demultiplexed locally so have no local fastq path. All other
        runfolders have fastqs in the BaseCalls directory
            :return fastqs_dict (dict | False): Dictionary containing R1 and R2 fastqs and
                                                their local and cloud paths. False if either
                                                fastq doesn't exist
        """
        fastqs_dict = {"R1": {}, "R2": {}}
        for read in ["R1", "R2"]:
            if self.pipeline == "tso500":
                fastqs_dict[read] = {
                    "name": None,
                    "path": None,
                    "nexus_path": os.path.join(
                        ToolboxConfig.FASTQ_DIRS["tso_fastqs"],
                        self.sample_name,
                        f"{self.sample_name}_{read}.fastq.gz",
                    ),
                }
            else:
                (fastq_name, fastq_path, nexus_fastq_path) = self.get_fastq_paths(read)
                if not fastq_path:
                    fastqs_dict = False
                    break
                else:
                    fastqs_dict[read] = {
                        "name": fastq_name,
                        "path": fastq_path,
                        "nexus_path": nexus_fastq_path,
                    }
        return fastqs_dict

    def get_fastq_paths(self, read: str) -> Union[str, str, str]:
        """
        Get fastqs in fastq directory that correspond to each sample name in the
        sample dictionary. Build the fastq name, local path, and DNAnexus path
        for each fastq file
            :param read (str):                  Either 'R1' or 'R2'
            :return fastq_name (str):           Fastq name
            :return fastq_path (str):           Local fastq path
            :return nexus_fastq_path (str):     DNAnexus fastq path
        """
        matches = [self.sample_name, f"_{read}"]
        try:
            fastq_name = list(
                fastq_path
                for fastq_path in os.listdir(self.fastq_dir_path)
                if all([substring in fastq_path for substring in matches])
            )[0]
            self.logger.debug(
                self.logger.log_msgs["fastq_identified"],
                fastq_name,
                ", ".join(matches),
            )
            fastq_path = os.path.join(self.fastq_dir_path, fastq_name)
            nexus_fastq_path = os.path.join(
                f"{ToolboxConfig.DNANEXUS_PROJ_ID}:{self.nexus_paths['fastqs_dir']}",
                fastq_name,
            )
            return fastq_name, fastq_path, nexus_fastq_path
        except Exception as exception:
            self.logger.error(
                self.logger.log_msgs["fastq_nonexistent"],
                ", ".join(matches),
                exception,
            )
            return False, False, False

    def return_sample_dict(self) -> dict:
        """
        Return sample dictionary with all collected information about the sample
            :return (dict): Collected information about the sample
        """
        return {
            "sample_name": self.sample_name,
            "pos_control": self.pos_control,
            "neg_control": self.neg_control,
            "identifiers": {
                "primary": self.primary_identifier,
                "secondary": self.secondary_identifier,
            },
            "pannum": self.pannum,
            "panel_settings": self.panel_settings,
            "fastqs": self.fastqs_dict,
        }
