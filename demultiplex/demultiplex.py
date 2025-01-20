"""
Demultiplexes NGS Run Folders. See Readme and docstrings for further details.
Contains the following classes:

- GetRunfolders
    Loop through and process NGS runfolders in a given directory
- DemultiplexRunfolder
    Call bclconvert2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid SampleSheet is present

"""

import sys
import os
import re
import datetime
from importlib.metadata import version
from shutil import copyfile
from typing import Optional, Tuple
import samplesheet_validator.samplesheet_validator as samplesheet_validator
from config.ad_config import DemultiplexConfig
from ad_logger.ad_logger import AdLogger, shutdown_logs
from toolbox.toolbox import (
    return_scriptlog_config,
    get_runfolder_path,
    test_processing_software,
    RunfolderObject,
    RunfolderSamples,
    get_num_processed_runfolders,
    git_tag,
    read_lines,
    write_lines,
    execute_subprocess_command,
    validate_fastqs,
)
from toolbox.toolbox import script_start_logmsg, script_end_logmsg


ad_logger_obj = AdLogger(
    __name__,
    "demux",
    return_scriptlog_config()["demux"],
)
script_logger = ad_logger_obj.get_logger()


class GetRunfolders(DemultiplexConfig):
    """
    Loop through and process NGS runfolders in a given directory

    Attributes
        runfolder_names (list):             List of runfolders, specified within ad_config
        timestamp (str):                    Timestamp in the format %Y%m%d_%H%M%S

    Methods
        get_runfolder_names(runfolder_names)
            Get test-mode-dependent runfolder names
        setoff_processing()
            Call methods to set off runfolder processing. Called by main module
        check_run_processed(dr_obj, runfolder_name)
            If runfolder has been processed during this script run, append
            to processed_runfolders list
    """

    def __init__(self, runfolder_names=False):
        """
        Constructor for the GetRunfolders class
            :param runfolder_name (str | False):    Optional command line argument
        """
        self.runfolder_names = self.get_runfolder_names(runfolder_names)
        self.timestamp = script_logger.timestamp
        script_start_logmsg(script_logger, __file__)

    def get_runfolder_names(self, runfolder_names) -> list:
        """
        Get test-mode-dependent runfolder names
            :param runfolder_names (str | False):   Command line runfolder name string
                                                    (default is False if none provided)
            :return runfolder_names (list):         List of runfolder names
        """
        if runfolder_names:
            script_logger.info(
                script_logger.log_msgs["cmd_line_runfolder"], runfolder_names
            )
            runfolder_names = [self.runfolder_names]
        else:
            script_logger.info(script_logger.log_msgs["programmatic_runfolders"])
            runfolder_names = []
            if DemultiplexConfig.TESTING:
                folders = DemultiplexConfig.DEMULTIPLEX_TEST_RUNFOLDERS
            else:
                folders = os.listdir(DemultiplexConfig.RUNFOLDERS)

            for folder_name in folders:
                if get_runfolder_path(folder_name) and re.compile(
                    DemultiplexConfig.RUNFOLDER_PATTERN
                ).match(folder_name):
                    runfolder_names.append(folder_name)
            script_logger.info(
                script_logger.log_msgs["runfolder_names"],
                ", ".join(runfolder_names),
            )
        return runfolder_names

    def setoff_processing(self) -> None:
        """
        Call methods to set off runfolder processing. Called by main module
            :return None:
        """
        processed_runfolders = []
        if test_processing_software(script_logger):
            for runfolder in self.runfolder_names:
                dr_obj = DemultiplexRunfolder(runfolder, self.timestamp)
                dr_obj.setoff_workflow()
                if self.check_run_processed(dr_obj, runfolder):
                    processed_runfolders.append(runfolder)

        get_num_processed_runfolders(script_logger, processed_runfolders)
        script_end_logmsg(script_logger, __file__)

    def check_run_processed(self, dr_obj: object, runfolder_name: str) -> None:
        """
        If runfolder has been processed during this script run, append
        to processed_runfolders list
            :param dr_obj (object):         DemultiplexRunfolder object for the run
            :[aram runfolder_name (str):    Runfolder name string
            :return None:
        """
        if (
            dr_obj.run_processed
        ):  # If runfolder has been processed during this script run
            script_logger.info(
                script_logger.log_msgs["script_success"],
                runfolder_name,
            )
            return True


class DemultiplexRunfolder(DemultiplexConfig):
    """
    Call bclconvert2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid SampleSheet is present.

    Attributes
        timestamp (str):                    Timestamp in the format %Y%m%d_%H%M%S
        rf_obj (obj):                       RunfolderObject object (contains runfolder-specific
                                            attributes)
        loggers (dict):                     Dictionary of logger.Logging objects
        demux_rf_logger (object):           Demultiplex runfolder-level logger, extracted from
                                            the RunfolderObject containing runfolder-level
                                            loggers
        bclconvert2_rf_logger (object):     Bclconvert2 runfolder-level logger, extracted from the
                                            RunfolderObject containing runfolder-level loggers
        bclconvert2_cmd (str):              Shell command to run demultiplexing
        cluster_density_cmd (str):          Shell command to run cluster density calculation
        tso (bool):                         Denotes whether the run is a tso500 run
        run_processed (bool):               Denotes whether the run has been successfully
                                            processed

    Methods
        setoff_workflow()
            Setoff demultiplex workflow only for runs where demultiplexing is required
            (TSO runs don't require demultiplexing)
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexing tasks to determine whether
            demultiplexing is required
        upload_flagfile_absent()
            Check if runfolder has already been uploaded
        bclconvertlog_absent()
            Check presence of demultiplex logfile (bclconvert2_output.log)
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing is required
            (TSO runs don't require demultiplexing)
        previous_samplesheet_check()
            Checks if a prior SampleSheet check has been carried out
        previous_samplesheet_check_fail()
            Checks whether there has previously been a SampleSheet check fail for this run, by
            looking in the sscheck log file. This is checked to determine whether to proceed with
            processing the run
        sscheck_success_msg_present()
            Check SampleSheet check success message is present in the sscheck flag file
        valid_samplesheet()
            Check SampleSheet is present and naming and contents are valid, using the
            samplesheet_validator module
        seq_requires_no_ic()
            Determines whether the run requires integrity checking (not possible on all
            sequencers)
        checksumfile_exists()
            Check if md5checksum file exists (i.e. integrity check has been performed
            by integrity check scripts)
        sequencing_complete()
            Check if sequencing has completed for the current runfolder (presence of
            RTAComplete.txt)
        pass_integrity_check()
            Check whether the integrity checking was successful
        prior_ic(checksums)
            Determines whether an integrity check has been previously performed by this
            script
        checksum_match_message(checksums)
            Determine whether the md5sum file contains the checksums match message
        checksums_match()
            Reads the md5checksum file and checks for the presence of the CHECKSUM_MATCH_MSG /
            CHECKSUM_DO_NOT_MATCH_MSG denoting that the runfolder has not / has been corrupted
            during transfer from the sequencer respectively
        write_checksums_assessed()
            Write DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED message to file to prevent script
            performing checks on future runs of the script
        checksums_do_not_match_message(checksums)
            Determine whethe the md5sum file contains the checksums do not match message
        calculate_cluster_density()
            Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
            cluster density and saves files (runfolder.illumina_phasing_metrics and
            runfolder.illumina_lane_metrics) to the runfolder
        runtype_requires_demultiplexing()
            Determine whether the run does, or does not (TSO500, dev runs with UMIs)
            require demultiplexing
        create_bclconvertlog()
            Create file to prevent demultiplexing starting again
        add_bclconvertlog_msg(runtype)
            If runfolder is from tso run or development run with UMIs, add specific message to
            bclconvert2_output.log file (these runs do not require demultiplexing)
        run_demultiplexing()
            Run demultiplexing command. If unsuccessful, exit script
        copy_file()
            Copy file from source path to dest path
    """

    def __init__(self, folder_name: str, timestamp: str):
        """
        Constructor for the DemultiplexRunfolder class
            :param folder_name(str):                    Runfolder name
            :param timestamp (str):                     Timestamp in the format %Y%m%d_%H%M%S
        """
        self.timestamp = timestamp
        self.rf_obj = RunfolderObject(folder_name, self.timestamp)
        self.loggers = self.rf_obj.get_runfolder_loggers(
            __package__
        )  # Get dictionary of loggers
        self.demux_rf_logger = self.loggers["demux"]
        self.bclconvert2_rf_logger = self.loggers["bclconvert2"]
        # N.B. --no-lane-splitting creates a single fastq for a sample,
        # not into one fastq per lane)
        self.bclconvert2_cmd = DemultiplexConfig.BCLCONVERT2_CMD % (
            self.rf_obj.runfolderpath,
            os.path.join(
                self.rf_obj.runfolderpath,
                "Data/Intensities/BaseCalls/",
            ),
            os.path.join(
                self.rf_obj.runfolderpath,
                "Bcl_convert_logs",
            ),
            os.path.join(
                DemultiplexConfig.RUNFOLDERS,
                "samplesheets"
            ),
            self.rf_obj.samplesheet_name
        )
        # Shell command to run cluster density calculation
        self.cluster_density_cmd = DemultiplexConfig.CD_CMD % (
            self.rf_obj.runfolderpath,
            self.rf_obj.runfolder_name,
        )
        self.tso = False
        self.run_processed = False

    def setoff_workflow(self) -> Optional[bool]:
        """
        Setoff demultiplex workflow only for runs where demultiplexing is required (TSO
        runs don't require demultiplexing). First calls self.create_bclconvertlog() to
        create the log file which prevents a simultaneous demultiplex attempt on the
        next run of the script (bclconvert2 is slow to create the logfile). Then calls
        calculate_cluster_density(). If a tso run, stops here. Else calls
        run_demultiplexing() to demultiplex the run.
            :return (Optional[bool]):  Return true if run successfully processed
        """
        if self.demultiplexing_required():
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["demultiplexing_required"]
            )
            if self.create_bclconvertlog():
                if self.run_demultiplexing():
                    self.run_processed = True
                    rf_samples_obj = RunfolderSamples(
                        self.rf_obj, self.loggers["demux"]
                    )
                    if rf_samples_obj.pipeline == "oncodeep":
                        self.copy_file(
                            self.rf_obj.masterfile_path,
                            self.rf_obj.runfolder_masterfile_path,
                        )
                        self.run_processed = True
                return True

    def demultiplexing_required(self) -> Optional[bool]:
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing is
        required. If required (i.e. these have not previously been carried out), carries out the early
        warning SampleSheet checks. Processes development runs that do not contain UMIs automatically,
        and sends out log message denoting manual processing is required for runs that do contain UMIs.
        If sequencing is complete, (RTAComplete.txt present) the run does not contain UMIs, and the
        SampleSheet contains no disallowed errors, and either 1) the sequencer does not require an
        integrity check or 2) there has not previously been an integrity check and the checksums match,
        returns True as demultiplexing is required
            :return None:
        """
        if self.upload_flagfile_absent() and self.bclconvertlog_absent():
            if not self.previous_samplesheet_check_fail():
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["ad_version"],
                    git_tag(),
                )
                if (
                    self.sscheck_success_msg_present() or self.valid_samplesheet()
                ):  # Early warning ss checks
                    requires_no_ic = self.seq_requires_no_ic()
                    if requires_no_ic or self.checksumfile_exists():
                        if self.sequencing_complete():
                            if requires_no_ic or self.pass_integrity_check():
                                self.copy_file(
                                    self.rf_obj.samplesheet_path,
                                    self.rf_obj.runfolder_samplesheet_path,
                                )
                                self.calculate_cluster_density()
                                if self.runtype_requires_demultiplexing():
                                    return True

    def upload_flagfile_absent(self) -> None:
        """
        Check if runfolder has already been uploaded
            :return None:
        """
        if not os.path.exists(self.rf_obj.upload_flagfile):
            return True
        else:
            script_logger.info(
                script_logger.log_msgs["skipping_runfolder"],
                self.rf_obj.runfolder_name,
            )

    def bclconvertlog_absent(self) -> Optional[bool]:
        """
        Check presence of demultiplex logfile (bclconvert2_output.log)
            :return (Optional[bool]):   Return true if demultiplex logfile exists
        """
        if os.path.isfile(self.rf_obj.bclconvertlog_file):
            script_logger.info(
                script_logger.log_msgs["demux_already_complete"],
                self.rf_obj.bclconvertlog_file,
            )
        else:
            script_logger.info(
                script_logger.log_msgs["demux_not_complete"],
                self.rf_obj.bclconvertlog_file,
            )
            return True

    def previous_samplesheet_check_fail(self) -> Optional[bool]:
        """
        Checks whether there has previously been a SampleSheet check fail for this run, by
        looking in the sscheck log file. This is checked to determine whether to proceed with
        processing the run
            :return (Optional[bool]):   Returns true if either the SampleSheet check file does
                                        not exist, or contains no SampleSheet check error string
        """
        if self.previous_samplesheet_check():
            sscheckfile_contents = read_lines(self.rf_obj.sscheck_flagfile_path)
            if any(
                DemultiplexConfig.STRINGS["samplesheet_fail"].split(":")[0] in line
                for line in sscheckfile_contents
            ):
                script_logger.info(
                    script_logger.log_msgs["previous_ss_check_fail"],
                    self.rf_obj.sscheck_flagfile_path,
                )
                return True

    def previous_samplesheet_check(self) -> Optional[bool]:
        """
        Check if a previous SampleSheet check has been carried out
            :return (optional[bool]):   Returns true if the SampleSheet check flag file is present
        """
        if os.path.isfile(self.rf_obj.sscheck_flagfile_path):
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sscheckfile_absent"],
            )

    def sscheck_success_msg_present(self) -> Optional[bool]:
        """
        Check SampleSheet check success message is present in the sscheck flag file
            :return (Optional[bool]):       Returns true if success message is identified
        """
        if self.previous_samplesheet_check():
            sscheckfile_contents = read_lines(self.rf_obj.sscheck_flagfile_path)
            read_lines(self.rf_obj.sscheck_flagfile_path)
            if any(
                DemultiplexConfig.STRINGS["samplesheet_success"].split(":")[0] in line
                for line in sscheckfile_contents
            ):
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["sscheck_success_msg_present"],
                )
                return True
            else:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["sscheck_success_msg_absent"],
                )
                return True

    def valid_samplesheet(self) -> Tuple[bool, object]:
        """
        Check SampleSheet is present and naming and contents are valid, using the
        samplesheet_validator module
            :return (tuple):    Returns tuple of boolean (denotes whether SampleSheet
                                is valid), and SampleSheetCheck object containing any
                                errors identified
        """
        script_logger.info(script_logger.log_msgs["ss_check_required"])
        script_logger.info(
            script_logger.log_msgs["ss_validator_version"],
            version("samplesheet_validator"),
        )
        sscheck_obj = samplesheet_validator.SamplesheetCheck(
            self.rf_obj.samplesheet_path,
            DemultiplexConfig.SEQUENCER_IDS.keys(),
            DemultiplexConfig.PANELS,
            DemultiplexConfig.TSO_PANELS,
            DemultiplexConfig.DEV_PANEL,
            os.path.dirname(self.rf_obj.samplesheet_validator_logfile),
        )
        sscheck_obj.ss_checks()
        shutdown_logs(sscheck_obj.logger)
        self.tso = sscheck_obj.tso
        err_str = ". ".join(", ".join(v) for v in sscheck_obj.errors_dict.values())

        if sscheck_obj.errors:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["sschecks_failed"],
                err_str,
            )
            write_lines(
                self.rf_obj.sscheck_flagfile_path,
                "w",
                DemultiplexConfig.STRINGS["samplesheet_fail"] % err_str,
            )
            return False
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sschecks_passed"],
                self.rf_obj.samplesheet_path,
            )
            write_lines(
                self.rf_obj.sscheck_flagfile_path,
                "w",
                DemultiplexConfig.STRINGS["samplesheet_success"]
                % datetime.datetime.now(),
            )
            return True

    def seq_requires_no_ic(self) -> Optional[bool]:
        """
        Check whether integrity check needed. Only runs from sequencers that can have
        checksums generated require this - not all sequencers can have checksums
        generated by the integrity check script (MiSeq can't have checksums generated).
            :return (Optional[bool]):   Return True if sequencer does not require an integrity
                                        check
        """
        if any(
            item in self.rf_obj.runfolder_name
            for item in DemultiplexConfig.SEQ_REQUIRE_IC
        ):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["seq_with_ic"])
        else:
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["seq_without_ic"])
            return True

    def checksumfile_exists(self) -> Optional[bool]:
        """
        Check if md5checksum file exists (i.e. integrity check has been performed
        by integrity check scripts and it has written the checksums and success / failure
        message to this file)
            :return (Optional[bool]): Return True if md5checksum file exists
        """
        if os.path.isfile(self.rf_obj.checksumfile_path):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_present"],
                self.rf_obj.checksumfile_path,
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_absent"],
                self.rf_obj.checksumfile_path,
            )

    def sequencing_complete(self) -> Optional[bool]:
        """
        Check if sequencing has completed for the current runfolder - presence of
        RTAComplete.txt.
            :return (Optional[bool]):  Returns true if sequencing is complete
        """
        if os.path.isfile(self.rf_obj.rtacompletefile_path):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["run_finished"],
                self.rf_obj.rtacompletefile_path,
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["run_incomplete"],
                self.rf_obj.rtacompletefile_path,
            )

    def pass_integrity_check(self) -> Optional[bool]:
        """
        Check whether the integrity checking was successful
            :return (Optional[bool]):       True if successful, None if unsuccessful
        """
        if self.checksumfile_exists():
            checksums = read_lines(self.rf_obj.checksumfile_path)
            if self.prior_ic(
                checksums
            ):  # If the checksums already checked message is there
                if self.checksum_match_message(
                    checksums
                ):  # If the checksums match message is there
                    return True  # Checksums match so integrity check passed
                else:
                    return False  # We don't want script to continue if there is no checksum success message
            else:  # If the checksums already checked message is not present
                return self.checksums_match()  # Check for the checksums match message

    def prior_ic(self, checksums: list) -> Optional[bool]:
        """
        Determines whether an integrity check has been previously performed by this script
        Checks for presence of the CHECKSUMS_ALREADY_ASSESSED message in the md5checksum file
        (this message is added when self.checksums_match() is called to prevent the script from
        checking this file again until the cause of an issue is addressed. If this string is removed
        from the file then the script will check for the CHECKSUM_MATCH_MSG / CHECKSUM_DO_NOT_MATCH_MSG
        messages again using self.checksums_match() )
            :param checksums (list):    List of lines from the checksums file
            :return (Optional[bool]):   Returns true if the checksum file has previously
                                        been checked for the success message by the script
        """
        if (
            DemultiplexConfig.STRINGS["checksums_assessed"].split(":")[0]
            in checksums[-1]
        ):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_checked"]
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_notchecked"]
            )

    def checksum_match_message(self, checksums: list) -> Optional[bool]:
        """
        Determine whether the md5sum file contains the checksums match message
            :param checksums (list):    List of lines from the checksums file
        """
        if DemultiplexConfig.STRINGS["checksums_match"] in checksums[0]:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["ic_pass"],
                self.rf_obj.checksumfile_path,
            )
            return True

    def checksums_match(self) -> Optional[bool]:
        """
        Reads the md5checksum file and checks for the presence of the CHECKSUM_MATCH_MSG (this
        is added by the integrity check scripts if the checksums match, denoting that the runfolder
        has not been corrupted during transfer from the sequencer). If the CHECKSUM_DO_NOT_MATCH_MSG
        is present, this denotes that the runfolder has been corrupted during transfer from the
        sequencer). If neither string is present the contents of the file are not as expected and a
        warning message is sent
            :return (Optional[bool]):   Returns True if checksum match string is present in
                                        checksum file
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["checksumfilecheck_start"]
        )
        checksums = read_lines(self.rf_obj.checksumfile_path)
        self.write_checksums_assessed()

        if self.checksum_match_message(checksums):
            return True
        elif self.checksums_do_not_match_message(checksums):
            return False
        else:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["unexpected_checksumfile_contents"],
                self.rf_obj.checksumfile_path,
            )

    def write_checksums_assessed(self) -> None:
        """
        Write DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED message to file to prevent script
        performing checks on future runs of the script
            :return None:
        """
        write_lines(
            self.rf_obj.checksumfile_path,
            "a",
            DemultiplexConfig.STRINGS["checksums_assessed"] % datetime.datetime.now(),
        )

    def checksums_do_not_match_message(self, checksums: list) -> Optional[bool]:
        """
        Determine whethe the md5sum file contains the checksums do not match message
            :param checksums (list):    List of lines from the checksums file
            :return (Optional[bool]):   Returns True if checksums do not match string
                                        is present in checksum file
        """
        if DemultiplexConfig.STRINGS["checksums_do_not_match"] in checksums[0]:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["ic_fail"],
                self.rf_obj.checksumfile_path,
            )
            return True

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """
        Copy file from source path to dest path
            :param source_path (str):   Path of file to copy
            :param dest_path (str):     Path to copy to
            :return None:
        """
        if os.path.exists(source_path):  # Try to copy SampleSheet into project
            copyfile(source_path, dest_path)
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["file_copy_success"],
                source_path,
                dest_path,
            )
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["file_copy_fail"], source_path
            )
            sys.exit(1)

    def calculate_cluster_density(self) -> Optional[bool]:
        """
        Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
        cluster density and saves files (runfolder.illumina_phasing_metrics and
        runfolder.illumina_lane_metrics) to the runfolder. If the success statement is
        seen in the stderr, record in the log file else raise a slack alert and exit
        script. If run was sequenced on novaseq, an extra argument is provided
            :return (Optional[bool]):  True if success statement seen
        """
        if DemultiplexConfig.NOVASEQ_ID in self.rf_obj.runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        self.cluster_density_cmd = f"{self.cluster_density_cmd}{novaseq_flag}"

        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["running_cd"],
            self.cluster_density_cmd,
        )
        out, err, returncode = execute_subprocess_command(
            self.cluster_density_cmd, self.demux_rf_logger
        )
        if returncode == 0:
            # Assess stderr, looking for expected success statement
            if DemultiplexConfig.STRINGS["cd_success"] in out or err:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["cd_success"],
                    f"{self.rf_obj.runfolder_name}{DemultiplexConfig.STRINGS['lane_metrics_suffix']}",
                )
                return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["cd_fail"],
                err,
            )
            sys.exit(1)

    def runtype_requires_demultiplexing(self) -> Optional[bool]:
        """
        Determine whether the run does, or does not (TSO500, dev runs with UMIs) require demultiplexing.
        If it does not require demultiplexing, creates the bclconvert log file. If it does require
        demultiplexing, returns True. Alert sent for dev runs with UMIs, as these require manual
        processing by the bioinformatics team
            :return (Optional[bool]):   True if requires automated processing, else None
        """
        samplesheet = read_lines(self.rf_obj.runfolder_samplesheet_path)
        if any(
            any(pannum in line for line in samplesheet)
            for pannum in DemultiplexConfig.UMI_DEV_PANEL
        ):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["dev_run_umis"])
            self.create_bclconvertlog()
            self.add_bclconvertlog_msg("DEV UMIs")
            write_lines(  # Create upload started log file to prevent automated upload
                self.rf_obj.upload_flagfile,
                "a",
                DemultiplexConfig.STRINGS["upload_flag_umis"] % datetime.datetime.now(),
            )
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["dev_umis_upload_flagfile"],
                self.rf_obj.runfolder_name,
            )
        elif any(
            any(pannum in line for line in samplesheet)
            for pannum in DemultiplexConfig.TSO_PANELS
        ):
            self.create_bclconvertlog()  # Create bclconvert2 log to prevent scripts processing this run
            self.add_bclconvertlog_msg("TSO500")
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["tso_run"])
        else:
            return True

    def create_bclconvertlog(self) -> Optional[bool]:
        """
        Create file to prevent demultiplexing starting again. bclconvert2 v2.20 doesn't
        produce stdout for a while after starting so the file is created and the
        bclconvert2 stdout is written to the file later. If unsuccessful, exit script
            :return (Optional[bool]):  True if logfile is successfully created
        """
        try:
            open(self.rf_obj.bclconvertlog_file, "w", encoding="utf-8").close()
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["create_bclconvertlog_pass"],
                self.rf_obj.bclconvertlog_file,
            )
            return True
        except Exception as exception:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["create_bclconvertlog_fail"],
                exception,
            )
            sys.exit(1)

    def add_bclconvertlog_msg(self, runtype_str: str) -> Optional[bool]:
        """
        Write message to bclconvertlog file that demultiplexing is not required
            :return (Optional[bool]):  True if log file successfully created and written to
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["demux_not_required"],
            DemultiplexConfig.STRINGS["demultiplex_not_required_msg"] % runtype_str,
        )
        write_lines(
            self.rf_obj.bclconvertlog_file,
            "w+",
            DemultiplexConfig.STRINGS["demultiplex_not_required_msg"] % runtype_str,
        )
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["write_msg_to_bclconvertlog"],
        )
        self.run_processed = True
        return True

    def run_demultiplexing(self) -> Optional[bool]:
        """
        Run demultiplexing command. If unsuccessful, exit script
            :return (Optional[bool]):   True if command executed succesfully and output is
                                        successfully written to the logfile
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["bclconvert_start"],
            self.bclconvert2_cmd,
        )
        # Runs bclconvert2 and checks if completed successfully
        # Bclconvert2 returncode 0 upon success. Outputs info logs to stderr
        out, err, returncode = execute_subprocess_command(
            self.bclconvert2_cmd,
            self.demux_rf_logger,
        )
        if returncode == 0:
            if validate_fastqs(self.rf_obj.fastq_dir_path, self.demux_rf_logger):
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["bclconvert_complete"],
                    self.rf_obj.runfolder_name,
                )
                self.bclconvert2_rf_logger.info(
                    err  # Write stderr to bclconvert2 runfolder logfile
                )
                return True
            else:
                os.remove(
                    self.rf_obj.bclconvertlog_file
                )  # Bclconvert log file removed to trigger re-demultiplex
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["re_demultiplex"]
                )
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bclconvert_failed"],
                out,
                err,
            )
            sys.exit(1)
