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
from typing import Optional, Tuple
import samplesheet_validator.samplesheet_validator as samplesheet_validator
from config.ad_config import DemultiplexConfig
from ad_logger.ad_logger import AdLogger
from toolbox.toolbox import (
    return_scriptlog_config,
    get_runfolder_path,
    test_processing_software,
    RunfolderObject,
    get_num_processed_runfolders,
    git_tag,
    read_lines,
    write_lines,
    execute_subprocess_command,
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
        cmd_line_supplied_runfolder (bool): Denotes whether the runfolder name was supplied on
                                            the command line (i.e. the run is a development
                                            run requiring manual processing)
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
        demultiplex_runfolder(folder_name)
            Pass NGS runfolder to instance of DemultiplexRunfolder() for processing
        bcl2fastqlog_absent(folder_name)
            Check presence of demultiplex logfile (bcl2fastq2_output.log)
        return_num_processed_runfolders()
            Add number of total processed runfolders as attribute
    """

    def __init__(self, runfolder_names=False):
        """
        Constructor for the GetRunfolders class
            :param runfolder_name (str | False):    Optional command line argument
        """
        self.runfolder_names = runfolder_names
        self.cmd_line_supplied_runfolder = bool
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
                self.demultiplex_runfolder(runfolder)
        self.return_num_processed_runfolders()
        script_end_logmsg(script_logger, __file__)

    def demultiplex_runfolder(self, folder_name: str) -> None:
        """
        Pass NGS runfolder to instance of DemultiplexRunfolder() for processing
            :param folder_name(str):    Name of runfolder
        """
        if self.bcl2fastqlog_absent(folder_name):
            self.demultiplex_obj = DemultiplexRunfolder(
                folder_name, self.timestamp, self.cmd_line_supplied_runfolder
            )
            self.demultiplex_obj.setoff_workflow()
            # If runfolder has been processed during this script run
            if self.demultiplex_obj.run_processed:
                script_logger.info(
                    script_logger.log_msgs["runfolder_processed"],
                    folder_name,
                )
                # Add runfolder to processed runfolder list
                self.processed_runfolders.append(folder_name)
        else:
            script_logger.info(
                script_logger.log_msgs["skipping_runfolder"],
                folder_name,
            )

    def bcl2fastqlog_absent(self, folder_name: str) -> Optional[bool]:
        """
        Check presence of demultiplex logfile (bcl2fastq2_output.log)
            :param folder_name(str):    Name of runfolder
            :return (Optional[bool]):   Return true if demultiplex logfile exists
        """
        self.rf_obj = RunfolderObject(folder_name, self.timestamp)

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
        cmd_line_supplied_runfolder (bool): Denotes whether the runfolder name was supplied on
                                            the command line (i.e. the run is a development
                                            run requiring manual processing)
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
        development_run (bool):             True if run is a development run, else False
        run_processed (bool):               Denotes whether the run has been successfully
                                            processed

    Methods
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing is required
            (TSO runs don't require demultiplexing)
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexing tasks to determine whether
            demultiplexing is required.
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
        dev_run(sscheck_obj)
            Determine whether the run is a development run using the sscheck_obj development_run() method
        no_disallowed_sserrs(valid, sscheck_obj)
            Check for specific errors that would cause bcl2fastq2 to fail and whose
            presence should stop demultiplexing
        dev_run_requires_automated_processing()
            Check whether the development run requires manual processing or automated
            processing by the script
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again
        add_bcl2fastqlog_tso_msg()
            If runfolder is from TSO500 run, add specific message to
            bcl2fastq2_output.log file (TSO500 runs do not require demultiplexing)
        calculate_cluster_density()
            Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
            cluster density and saves files (runfolder.illumina_phasing_metrics and
            runfolder.illumina_lane_metrics) to the runfolder
        run_demultiplexing()
            Run demultiplexing command. If unsuccessful, exit script
        validate_fastqs()
            Validate the created fastqs in the BaseCalls directory and log success
            or failure error message accordingly. If any failure, remove bcl2fastq log
            file to trigger re-demultiplex on next script run
    """

    def __init__(
        self, folder_name: str, timestamp: str, cmd_line_supplied_runfolder: bool
    ):
        """
        Constructor for the DemultiplexRunfolder class
            :param folder_name(str):                    Runfolder name
            :param timestamp (str):                     Timestamp in the format %Y%m%d_%H%M%S
            :param cmd_line_supplied_runfolder (bool):  Denotes whether the runfolder name was supplied on
                                                        the command line (i.e. the run is a development
                                                        run requiring manual processing)
        """
        self.timestamp = timestamp
        self.cmd_line_supplied_runfolder = cmd_line_supplied_runfolder
        self.rf_obj = RunfolderObject(folder_name, self.timestamp)
        self.rf_obj.add_runfolder_loggers(
            __package__
        )  # Add rf loggers to runfolder object
        self.demux_rf_logger = self.rf_obj.rf_loggers["demux"]
        self.bcl2fastq2_rf_logger = self.rf_obj.rf_loggers["bcl2fastq2"]
        self.disallowed_sserrs = [
            "Samplesheet absent",
            "Samplesheet name invalid",
            "Samplesheet is empty",
            "Missing headers",
            "Illegal characters",
        ]
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
            if self.create_bcl2fastqlog() and self.calculate_cluster_density():
                # TSO500 runs do not require demultiplexing
                if self.tso:
                    self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["tso_run"])
                    self.run_processed = True
                elif self.run_demultiplexing():  # All other runs require demultiplexing
                    self.run_processed = True
                    self.validate_fastqs()
                return True

    def demultiplexing_required(self) -> Optional[bool]:
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing is
        required. Carries out the early warning SampleSheet checks. If sequencing is complete and
        the run is a development run, creates the bcl2fastq2 logfile to prevent further processing.
        Else, if sequencing is complete (RTAComplete.txt present) and the run is not a development
        run, the SampleSheet contains no disallowed errors, and either 1) the sequencer does not
        require an integrity check or 2) there has not previously been an integrity check and the
        checksums match, returns True as demultiplexing is required
            :return (Optional[bool]):  Return true if demultiplexing is required
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["ad_version"],
            git_tag(),
        )
        valid, sscheck_obj = self.valid_samplesheet()  # Early warning checks
        self.tso = sscheck_obj.tso

        if self.sequencing_complete():
            if self.pass_integrity_check():
                if self.dev_run(sscheck_obj) and self.no_disallowed_sserrs(
                    valid, sscheck_obj
                ):
                    if self.dev_run_requires_automated_processing():
                        return True
                # Only want SampleSheet checks to be performed on production runs not dev runs
                elif self.no_disallowed_sserrs(valid, sscheck_obj):
                    return True

    def valid_samplesheet(self) -> Tuple[bool, object]:
        """
        Check SampleSheet is present and naming and contents are valid, using the
        samplesheet_validator module
            :return (tuple):    Returns tuple of boolean (denotes whether SampleSheet
                                is valid), and SampleSheetCheck object containing any
                                errors identified
        """
        sscheck_obj = samplesheet_validator.SamplesheetCheck(
            self.rf_obj.samplesheet_path,
            DemultiplexConfig.SEQUENCER_IDS.keys(),
            DemultiplexConfig.PANELS,
            DemultiplexConfig.TSO_PANELS,
            DemultiplexConfig.DEVELOPMENT_PANEL,
            os.path.dirname(self.rf_obj.samplesheet_validator_logfile),
        )
        sscheck_obj.ss_checks()
        if sscheck_obj.errors:
            return False, sscheck_obj
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sschecks_passed"],
                self.rf_obj.samplesheet_path,
            )
            return True, sscheck_obj

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
            :return (Optional[bool]):  True if successful, None if unsuccessful
        """
        if self.seq_requires_no_ic():
            return True
        if self.checksumfile_exists():
            if not self.prior_ic():
                self.write_checksums_assessed()
                if self.checksums_match():
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
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["checksumfile_absent"],
                self.rf_obj.checksumfile_path,
            )

    def prior_ic(self) -> Optional[bool]:
        """
        Determines whether an integrity check has been previously performed by this
        script. Checks for presence of the CHECKSUMS_ALREADY_ASSESSED message in the
        md5checksum file (this message is added when self.checksums_match() is called
        to prevent the script from checking this file again until the cause of an issue
        is addressed. If this string is removed from the file then the script will check
        for the CHECKSUM_MATCH_MSG / CHECKSUM_DO_NOT_MATCH_MSG messages again using
        self.checksums_match() )
            :return (Optional[bool]):   Returns true if the checksum file has previously
                                        been checked for the success message by the script
        """
        checksums = read_lines(self.rf_obj.checksumfile_path)

        if DemultiplexConfig.CHECKSUMS_ALREADY_ASSESSED in checksums[-1]:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_checked"]
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["checksumfile_notchecked"]
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

    def dev_run(self, sscheck_obj: object) -> Optional[bool]:
        """
        Determine whether the run is a development run using the sscheck_obj development_run() method
            :sscheck_obj (obj):         Object created by samplesheet_validator.SampleheetCheck
            :return (Optional[bool]):   Return true if development run, else None
        """
        if sscheck_obj.development_run():
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["dev_run"],
                self.rf_obj.samplesheet_path,
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["not_dev_run"],
                self.rf_obj.samplesheet_path,
            )

    def no_disallowed_sserrs(self, valid: bool, sscheck_obj: object) -> Optional[bool]:
        """
        Check for specific errors that would cause bcl2fastq2 to fail and whose presence
        should stop demultiplexing. Write errors to flag file if they exist, which will
        stop the checks from continuing to fire in subsequent runs of the script. The first
        time the errors are detected it will log the message as an error which appears in
        slack, and on subsequent runs of the script it will log at level INFO so as not to
        overload slack with error messages
            :param valid (bool):            Denotes whether the SampleSheet is valid
                                            (conforms to requirements)
            :param sscheck_obj (object):    samplesheet_validator.SamplesheetCheck
                                            object, generated by the SampleSheet
                                            validator module
            :return (Optional[bool]):       Returns true if SampleSheet is valid
        """
        if valid and not any(
            error in list(sscheck_obj.errors_dict.keys())
            for error in self.disallowed_sserrs
        ):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["no_disallowed_ss_errs"],
                self.rf_obj.samplesheet_path,
            )
            return True
        else:
            err_str = ", ".join(list(sscheck_obj.errors_dict.keys()))
            if not os.path.exists(self.rf_obj.sscheck_flagfile_path):
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["ssfail_haltdemux"],
                    self.rf_obj.samplesheet_path,
                    err_str,
                )
            else:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["ssfail_haltdemux"],
                    self.rf_obj.samplesheet_path,
                    err_str,
                )
            write_lines(
                self.rf_obj.sscheck_flagfile_path,
                "w",
                DemultiplexConfig.SAMPLESHEET_ERRORS_MSG % err_str,
            )

    def dev_run_requires_automated_processing(self) -> Optional[bool]:
        """
        Check whether the development run requires manual processing or automated
        processing by the script. If the runfolder was supplied in command line mode,
        development run requires automated processing by the script. Otherwise,
        the bcl2fastqlog is created to prevent further processing, an alert will be
        sent to slack, and the development run will need to be processed by bioinformatics.
            :return (Optional[bool]):   True if requires automated processing, else None
        """
        if self.cmd_line_supplied_runfolder:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["dev_run_will_be_processed"],
            )
            return True
        # Create bcl2fastq2 log to prevent scripts processing this run
        elif self.create_bcl2fastqlog():
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["dev_run_needs_processing"],
            )

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
            if self.tso:
                self.add_bcl2fastqlog_tso_msg()
            return True
        except Exception as exception:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_fail"],
                exception,
            )
            sys.exit(1)

    def add_bcl2fastqlog_tso_msg(self) -> Optional[bool]:
        """
        If runfolder is from TSO500 run, add specific message to bcl2fastq2_output.log
        file (TSO500 runs do not require demultiplexing)
            :return (Optional[bool]):  True if log file successfully created and written to
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["tso500_run"],
            DemultiplexConfig.STRINGS["demultiplexlog_tso500_msg"],
        )
        write_lines(
            self.rf_obj.bcl2fastqlog_file,
            "w+",
            DemultiplexConfig.STRINGS["demultiplexlog_tso500_msg"],
        )
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["write_tso_msg_to_bcl2fastqlog"]
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
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["bcl2fastq_complete"],
            )
            self.bcl2fastq2_rf_logger.info(
                err  # Write stderr to bcl2fastq2 runfolder logfile
            )
            return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastq_failed"],
                out,
                err,
            )
            sys.exit(1)

    def validate_fastqs(self) -> None:
        """
        Validate the created fastqs in the BaseCalls directory and log success
        or failure error message accordingly. If any failure, remove bcl2fastq log
        file to trigger re-demultiplex on next script run
            :return None:
        """
        fastqs = [
            x for x in os.listdir(self.rf_obj.fastq_dir_path) if x.endswith("fastq.gz")
        ]
        returncodes = []

        for fastq in fastqs:
            out, err, returncode = execute_subprocess_command(
                f"gzip --test {os.path.join(self.rf_obj.fastq_dir_path, fastq)}",
                self.demux_rf_logger,
            )
            if returncode == 0:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["fastq_valid"],
                    fastq,
                )
            else:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["fastq_invalid"],
                    fastq,
                    out,
                    err,
                )

        if all(code == 0 for code in returncodes):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["demux_success"])
        else:
            if os.path.exists(self.rf_obj.bcl2fastqlog_file):
                os.remove(
                    self.rf_obj.bcl2fastqlog_file
                )  # Bcl2fastq log file removed to trigger re-demultiplex
            self.demux_rf_logger.error(self.demux_rf_logger.log_msgs["re_demultiplex"])
