#!/usr/bin/python3
"""
Demultiplexes NGS Run Folders. See Readme and docstrings for further details.
Contains the following classes:

- GetRunfolders
    Loop through and process NGS runfolders in a given directory
- DemultiplexRunfolder
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid SampleSheet is present

"""
import sys
import os
import re
import datetime
import logging
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
        processed_runfolders (list):        List to hold names of processed runfolders,
                                            updated dynamically
        num_processed_runfolders (int):     No. runfolders processed during this cycle
        demultiplex_obj (object):           DemultiplexRunfolder object
        rf_obj (object):                    RunfolderObject object (contains runfolder-specific
                                            attributes)

    Methods
        get_runfolder_names(runfolder_name)
            Get test-mode-dependent runfolder names
        setoff_processing()
            Call methods to set off runfolder processing. Called by main module
        check_run_processed(dr_obj)
            If runfolder has been processed during this script run, append
            to processed_runfolders list
        return_num_processed_runfolders()
            Add number of total processed runfolders as attribute
    """

    def __init__(self, runfolder_names=False):
        """
        Constructor for the GetRunfolders class
            :param runfolder_name (str | False):    Optional command line argument
        """
        self.runfolder_names = runfolder_names
        self.timestamp = script_logger.timestamp
        self.processed_runfolders = []

    def get_runfolder_names(self) -> list:
        """
        Get test-mode-dependent runfolder names
            :return runfolder_names (list):         List of runfolder names
        """
        if self.runfolder_names:
            script_logger.info(
                script_logger.log_msgs["cmd_line_runfolder"], self.runfolder_name
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
        script_start_logmsg(script_logger, __file__)
        self.runfolder_names = self.get_runfolder_names()
        if test_processing_software(script_logger):
            for runfolder in self.runfolder_names:
                dr_obj = DemultiplexRunfolder(runfolder, self.timestamp)
                dr_obj.setoff_workflow()
                self.check_run_processed(dr_obj, runfolder)
        self.return_num_processed_runfolders()
        script_end_logmsg(script_logger, __file__)

    def check_run_processed(self, dr_obj: object, runfolder_name: str) -> None:
        """
        If runfolder has been processed during this script run, append
        to processed_runfolders list
            :param dr_obj (object): DemultiplexRunfolder object for the run
            :return None:
        """
        if dr_obj.run_processed:  # If runfolder has been processed during this script run
            script_logger.info(
                script_logger.log_msgs["script_success"],
                runfolder_name,
            )
            self.processed_runfolders.append(runfolder_name)

    def return_num_processed_runfolders(self) -> None:
        """
        Add number of total processed runfolders as attribute
            :return None:
        """
        num_processed_runfolders = get_num_processed_runfolders(
            script_logger, self.processed_runfolders
        )
        setattr(self, "num_processed_runfolders", num_processed_runfolders)


class DemultiplexRunfolder(DemultiplexConfig):
    """
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid SampleSheet is present.

    Attributes
        timestamp (str):                    Timestamp in the format %Y%m%d_%H%M%S
        rf_obj (obj):                       RunfolderObject object (contains runfolder-specific
                                            attributes)
        demux_rf_logger (object):           Demultiplex runfolder-level logger, extracted from
                                            the RunfolderObject containing runfolder-level
                                            loggers
        bcl2fastq2_rf_logger (object):      Bcl2fastq2 runfolder-level logger, extracted from the
                                            RunfolderObject containing runfolder-level loggers
        disallowed_sserrs (list):           List of disallowed SampleSheet error strings
        bcl2fastq2_cmd (str):               Shell command to run demultiplexing
        cluster_density_cmd (str):          Shell command to run cluster density calculation
        tso (bool):                         Denotes whether the run is a tso500 run
        dev_run (bool):                     Denotes whether the run is a dev run
        dev_umis (bool):                    Denotes whether the run is a dev run with UMIS
        development_run (bool):             True if run is a development run, else False
        run_processed (bool):               Denotes whether the run has been successfully
                                            processed

    Methods
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexing tasks to determine whether
            demultiplexing is required
        upload_flagfile_absent()
            Check if runfolder has already been uploaded
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile (bcl2fastq2_output.log)
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing is required
            (TSO runs don't require demultiplexing)
        previous_samplesheet_check()
            Checks if a prior samplesheet check has been carried out
        valid_samplesheet()
            Check SampleSheet is present and naming and contents are valid, using the
            samplesheet_validator module
        sequencing_complete()
            Check if sequencing has completed for the current runfolder (presence of
            RTAComplete.txt)
        pass_integrity_check()
            Check whether the integrity checking was successful
        seq_requires_no_ic()
            Determines whether the run requires integrity checking (not possible on all
            sequencers)
        checksumfile_exists()
            Check if md5checksum file exists (i.e. integrity check has been performed
            by integrity check scripts)
        prior_ic()
            Determines whether an integrity check has been previously performed by this
            script
        write_checksums_assessed()
            Write DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED message to file to prevent script
            performing checks on future runs of the script
        checksums_match()
            Reads the md5checksum file and checks for the presence of the CHECKSUM_MATCH_MSG /
            CHECKSUM_DO_NOT_MATCH_MSG denoting that the runfolder has not / has been corrupted
            during transfer from the sequencer respectively
        disallowed_sserrs_identified(valid, sscheck_obj)
            Check for specific errors that would cause bcl2fastq2 to fail and whose
            presence should stop demultiplexing
        dev_run_requires_demultiplexing(sscheck_obj)
            Determine whether the run is a development run requiring automated demultiplexing,
            or not (contains UMIs), using the sscheck_obj           
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again
        add_bcl2fastqlog_msg()
            If runfolder is from tso run or development run with UMIs, add specific message to
            bcl2fastq2_output.log file (these runs do not require demultiplexing)
        calculate_cluster_density()
            Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
            cluster density and saves files (runfolder.illumina_phasing_metrics and
            runfolder.illumina_lane_metrics) to the runfolder
        run_demultiplexing()
            Run demultiplexing command. If unsuccessful, exit script
        copy_file()
            Copy file from source path to dest path
    """

    def __init__(
        self, folder_name: str, timestamp: str
    ):
        """
        Constructor for the DemultiplexRunfolder class
            :param folder_name(str):                    Runfolder name
            :param timestamp (str):                     Timestamp in the format %Y%m%d_%H%M%S
        """
        self.timestamp = timestamp
        self.rf_obj = RunfolderObject(folder_name, self.timestamp)
        self.loggers = self.rf_obj.get_runfolder_loggers(
            __package__
        )  # Add rf loggers to runfolder object
        self.demux_rf_logger = self.loggers["demux"]
        self.bcl2fastq2_rf_logger = self.loggers["bcl2fastq2"]
        # N.B. --no-lane-splitting creates a single fastq for a sample,
        # not into one fastq per lane)
        self.bcl2fastq2_cmd = DemultiplexConfig.BCL2FASTQ2_CMD % (
            self.rf_obj.runfolderpath,
            self.rf_obj.samplesheet_path,
            self.rf_obj.samplesheet_name,
            self.rf_obj.samplesheet_name,
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
        runs don't require demultiplexing). First calls self.create_bcl2fastqlog() to
        create the log file which prevents a simultaneous demultiplex attempt on the
        next run of the script (bcl2fastq2 is slow to create the logfile). Then calls
        calculate_cluster_density(). If a tso run, stops here. Else calls
        run_demultiplexing() to demultiplex the run.
            :return (Optional[bool]):  Return true if run successfully processed
        """
        if self.demultiplexing_required():
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["demultiplexing_required"]
            )
            if self.create_bcl2fastqlog():
                if self.run_demultiplexing():
                    self.run_processed = True
                    rf_samples = RunfolderSamples(self.rf_obj, self.loggers["demux"])
                    if rf_samples.pipeline == "oncodeep":
                        self.copy_file(
                            self.rf_obj.masterfile_path,
                            self.rf_obj.runfolder_masterfile_path
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
        if self.upload_flagfile_absent() and self.bcl2fastqlog_absent():
            if not self.previous_samplesheet_check_fail():
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["ad_version"],
                    git_tag(),
                )
                valid_samplesheet = self.valid_samplesheet()  # Early warning checks
                if valid_samplesheet:
                    requires_no_ic = self.seq_requires_no_ic()
                    if requires_no_ic or self.checksumfile_exists():
                        if self.sequencing_complete():
                            if requires_no_ic or self.pass_integrity_check():
                                self.copy_file(
                                    self.rf_obj.samplesheet_path,
                                    self.rf_obj.runfolder_samplesheet_path
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

    def bcl2fastqlog_absent(self) -> Optional[bool]:
        """
        Check presence of demultiplex logfile (bcl2fastq2_output.log)
            :return (Optional[bool]):   Return true if demultiplex logfile exists
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_file):
            script_logger.info(
                script_logger.log_msgs["demux_already_complete"],
                self.rf_obj.bcl2fastqlog_file,
            )
        else:
            script_logger.info(
                script_logger.log_msgs["demux_not_complete"],
                self.rf_obj.bcl2fastqlog_file,
            )
            return True

    def previous_samplesheet_check_fail(self) -> Optional[bool]:
        """
        Checks if a prior samplesheet check which failed has been carried out. This is checked to
        determine whether to proceed with processing the run. This flag file must be removed for
        subsequent attempts to process the run in the case of the samplesheet check failing
            :logger (logging.Logger):   Logger
            :return (Optional[bool]):   Returns true if the samplesheet check flag file is present
        """
        if os.path.exists(self.rf_obj.sscheck_flagfile_path):
            with open(self.rf_obj.sscheck_flagfile_path, 'r') as sscheck_file:
                sscheckfile_contents = sscheck_file.readlines()
            if any(DemultiplexConfig.SAMPLESHEET_ERRORS_MSG in line for line in sscheckfile_contents):
                script_logger.info(
                    script_logger.log_msgs["previous_ss_check_fail"],
                    self.rf_obj.sscheck_flagfile_path,
                )
                return True
            else:
                script_logger.info(
                    script_logger.log_msgs["previous_ss_check_pass"],
                )
        else:
            script_logger.info(
                script_logger.log_msgs["ss_check_required"]
            )

    def valid_samplesheet(self) -> Tuple[bool, object]:
        """
        Check SampleSheet is present and naming and contents are valid, using the
        samplesheet_validator module
            :return (tuple):    Returns tuple of boolean (denotes whether SampleSheet
                                is valid), and SampleSheetCheck object containing any
                                errors identified
        """
        if not self.sscheck_success_msg_present():
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
            self.dev_run = sscheck_obj.dev_run
            err_str = '. '.join(', '.join(v) for v in sscheck_obj.errors_dict.values())

            if sscheck_obj.errors:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["sschecks_failed"],
                    err_str,
                )
                write_lines(
                    self.rf_obj.sscheck_flagfile_path,
                    "w",
                    f"{DemultiplexConfig.SAMPLESHEET_ERRORS_MSG} {err_str}",
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
                    DemultiplexConfig.SAMPLESHEET_SUCCESS_MSG,
                )
                return True
        else:
            return True

    def sscheck_success_msg_present(self) -> Optional[bool]:
        """
        Check samplesheet check success message is present in the sscheck flag file
            :return (Optional[bool]):       Returns true if success message is identified
        """
        if os.path.exists(self.rf_obj.sscheck_flagfile_path):
            with open(self.rf_obj.sscheck_flagfile_path, 'r') as sscheck_file:
                sscheckfile_contents = sscheck_file.readlines()
            if any(DemultiplexConfig.SAMPLESHEET_SUCCESS_MSG in line for line in sscheckfile_contents):
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["sscheck_success_msg_present"],
                )
                return True
            else:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["sscheck_success_msg_absent"],
                )
                return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sscheckfile_absent"],
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
            if not self.prior_ic_fail(checksums):
                self.write_checksums_assessed()
                if self.checksums_match():
                    return True

    def prior_ic_fail(self, checksums) -> Optional[bool]:
        """
        Determine whether a previous check has identified that the md5sum file contains
        the checksums do not match message
        """
        if DemultiplexConfig.CHECKSUM_DO_NOT_MATCH_MSG in checksums[0]:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["prior_ic_fail"]
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

    # def prior_ic(self, checksums) -> Optional[bool]:
    #     """
    #     Determines whether an integrity check has been previously performed by this
    #     script. Checks for presence of the CHECKSUMS_ALREADY_ASSESSED message in the
    #     md5checksum file (this message is added when self.checksums_match() is called
    #     to prevent the script from checking this file again until the cause of an issue
    #     is addressed. If this string is removed from the file then the script will check
    #     for the CHECKSUM_MATCH_MSG / CHECKSUM_DO_NOT_MATCH_MSG messages again using
    #     self.checksums_match() )
    #         :return (Optional[bool]):   Returns true if the checksum file has previously
    #                                     been checked for the success message by the script
    #     """
    #     if DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED in checksums[-1]:
    #         self.demux_rf_logger.info(
    #             self.demux_rf_logger.log_msgs["checksumfile_checked"]
    #         )
    #         return True
    #     else:
    #         self.demux_rf_logger.info(
    #             self.demux_rf_logger.log_msgs["checksumfile_notchecked"]
    #         )          

    def write_checksums_assessed(self) -> None:
        """
        Write DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED message to file to prevent script
        performing checks on future runs of the script
            :return None:
        """
        write_lines(
            self.rf_obj.checksumfile_path,
            "a",
            f"\n{DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED}",
        )

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

        with open(self.rf_obj.checksumfile_path, "r") as f:
            checksums = f.readlines()

        if DemultiplexConfig.CHECKSUM_MATCH_MSG in checksums[0]:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["ic_pass"],
                self.rf_obj.checksumfile_path,
            )
            return True
        elif DemultiplexConfig.CHECKSUM_DO_NOT_MATCH_MSG in checksums[0]:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["ic_fail"],
                self.rf_obj.checksumfile_path,
            )
        else:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["unexpected_checksumfile_contents"],
                self.rf_obj.checksumfile_path,
            )

    def runtype_requires_demultiplexing(self) -> Optional[bool]:
        """
        Determine whether the run does not require demultiplexing (TSO500, dev runs with UMIs), or does
        require demultiplexing. If it does not require demultiplexing, creates the bcl2fastq log file.
        If it does require demultiplexing, returns True. Alert sent for dev runs with UMIs, as these
        require manual processing by the bioinformatics team
            :return (Optional[bool]):   True if requires automated processing, else None
        """
        with open(self.rf_obj.runfolder_samplesheet_path, "r") as f:
            samplesheet = f.readlines()
        if any(any(pannum in line for line in samplesheet) for pannum in DemultiplexConfig.UMI_DEV_PANEL):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["dev_run_umis"])
            self.create_bcl2fastqlog()
            self.add_bcl2fastqlog_msg()
        if any(any(pannum in line for line in samplesheet) for pannum in DemultiplexConfig.TSO_PANELS):
            self.create_bcl2fastqlog()  # Create bcl2fastq2 log to prevent scripts processing this run
            self.add_bcl2fastqlog_msg()
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["tso_run"])
        else:
            return True

    def create_bcl2fastqlog(self) -> Optional[bool]:
        """
        Create file to prevent demultiplexing starting again. bcl2fastq2 v2.20 doesn't
        produce stdout for a while after starting so the file is created and the
        bcl2fastq2 stdout is written to the file later. If unsuccessful, exit script
            :return (Optional[bool]):  True if logfile is successfully created
        """
        try:
            open(self.rf_obj.bcl2fastqlog_file, "w", encoding="utf-8").close()
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_pass"],
                self.rf_obj.bcl2fastqlog_file,
            )
            return True
        except Exception as exception:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_fail"],
                exception,
            )
            sys.exit(1)

    def add_bcl2fastqlog_msg(self) -> Optional[bool]:
        """
        Write message to bcl2fastqlog file that demultiplexing is not required
            :return (Optional[bool]):  True if log file successfully created and written to
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["demux_not_required"],
            DemultiplexConfig.STRINGS["demultiplex_not_required_msg"],
        )
        write_lines(
            self.rf_obj.bcl2fastqlog_file,
            "w+",
            DemultiplexConfig.STRINGS["demultiplex_not_required_msg"],
        )
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["write_msg_to_bcl2fastqlog"]
        )
        return True

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

    def run_demultiplexing(self) -> Optional[bool]:
        """
        Run demultiplexing command. If unsuccessful, exit script
            :return (Optional[bool]):   True if command executed succesfully and output is
                                        successfully written to the logfile
        """
        if self.tso:  # TSO500 runs do not require demultiplexing
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["no_demultiplexing"], self.pipeline)
            return True
        else:  # All other runs require demultiplexing
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["bcl2fastq_start"],
                self.bcl2fastq2_cmd,
            )
            # Runs bcl2fastq2 and checks if completed successfully
            # Bcl2fastq2 returncode 0 upon success. Outputs info logs to stderr
            out, err, returncode = execute_subprocess_command(
                self.bcl2fastq2_cmd,
                self.demux_rf_logger,
            )
            if returncode == 0:
                if validate_fastqs(self.rf_obj.fastq_dir_path, self.loggers["sw"]):
                    self.demux_rf_logger.info(
                        self.demux_rf_logger.log_msgs["bcl2fastq_complete"],
                        self.rf_obj.runfolder_name
                    )
                    self.bcl2fastq2_rf_logger.info(
                        err  # Write stderr to bcl2fastq2 runfolder logfile
                    )
                    return True
                else:
                    os.remove(
                        self.bcl2fastqlog_file
                    )  # Bcl2fastq log file removed to trigger re-demultiplex
                    self.demux_rf_logger.error(self.demux_rf_logger.log_msgs["re_demultiplex"])
            else:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["bcl2fastq_failed"],
                    out,
                    err,
                )
                sys.exit(1)

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """
        Copy file from source path to dest path
            :param source_path (str):   Path of file to copy
            :param dest_path (str):     Path to copy to
            :return None:
        """
        if os.path.exists(source_path):  # Try to copy SampleSheet into project
            copyfile(source_path, dest_path)
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["file_copy_success"],
                source_path,
                dest_path,
            )
        else:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["file_copy_fail"],
                source_path
            )
            sys.exit(1)