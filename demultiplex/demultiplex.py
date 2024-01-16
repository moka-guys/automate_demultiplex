#!/usr/bin/python3
# coding=utf-8
"""
Demultiplexes NGS Run Folders. See Readme and docstrings for further details.
Contains the following classes:

- GetRunfolders
    Loop through and process NGS runfolders in a given directory
- DemultiplexRunfolder
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present

"""
import sys
import os
import re
from typing import Union, Tuple
import samplesheet_validator.samplesheet_validator as samplesheet_validator
from config.ad_config import DemultiplexConfig
from ad_logger.ad_logger import AdLogger, shutdown_logs
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


class GetRunfolders(DemultiplexConfig):
    """
    Loop through and process NGS runfolders in a given directory

    Attributes
        ad_logger_obj (object):             AdLogger object, used to create a python logging object with custom attributes
                                            and a file handler, syslog handler, and stream handler  
        script_logger (object):             Script-level logger
        cmd_line_supplied_runfolder (bool): Denotes whether the runfolder name was supplied on
                                            the command line (i.e. the run is a development
                                            run requiring manual processing)
        runfolder_names (list):             List of runfolders, specified within ad_config
        timestamp (str):                    Timestamp in the format %Y%m%d_%H%M%S
        processed_runfolders (list):        List to hold names of processed runfolders,
                                            updated dynamically
        num_processed_runfolders (int):     No. runfolders processed during this cycle
        demultiplex_obj (object):           DemultiplexRunfolder object
        rf_obj (object):                    RunfolderObject object (contains runfolder-specific
                                            attributes)

    Methods
        check_cmd_line_supplied_runfolder(runfolder_name)
            Determine whether runfolder name was supplied on the command line
        get_runfolder_names(runfolder_name)
            Get test-mode-dependent runfolder names
        setoff_processing()
            Call methods to set off runfolder processing
        demultiplex_runfolder(folder_name)
            Pass NGS runfolder to instance of DemultiplexRunfolder() for processing
        bcl2fastqlog_absent(folder_name)
            Check presence of demultiplex logfile (bcl2fastq2_output.log)
        return_num_processed_runfolders()
            Add number of total processed runfolders as attribute
    """

    def __init__(self, runfolder_name=False):
        """
        Constructor for the GetRunfolders class
            :param runfolder_name (str | False):    Optional command line argument
        """
        self.ad_logger_obj = AdLogger(
            "demultiplex",
            "demultiplex",
            return_scriptlog_config()["demultiplex"],
        )
        self.script_logger = self.ad_logger_obj.get_logger()
        self.cmd_line_supplied_runfolder = self.check_cmd_line_supplied_runfolder(
            runfolder_name
        )
        self.runfolder_names = self.get_runfolder_names(runfolder_name)
        self.timestamp = self.script_logger.timestamp
        self.processed_runfolders = []

    def check_cmd_line_supplied_runfolder(self, runfolder_name) -> bool:
        """
        Determine whether runfolder name was supplied on the command line. This only happens
        in the case of development runs as it should only be used in this way to process
        development runs
            :param runfolder_name (str | False):    Runfolder name or False
            :return bool:                           True if ss checks should be bypassed, False
                                                    if not
        """
        if runfolder_name:
            self.script_logger.info(
                self.script_logger.log_msgs["cmd_line_runfolder"], runfolder_name
            )
            return True
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["programmatic_runfolders"]
            )
            return False

    def get_runfolder_names(self, runfolder_name) -> list:
        """
        Get test-mode-dependent runfolder names
            :param runfolder_name (str | False):    Runfolder name or False
            :return runfolder_names (list):         List of runfolder names
        """
        if runfolder_name:
            runfolder_names = [runfolder_name]
        else:
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
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_names"],
                ", ".join(runfolder_names),
            )
        return runfolder_names

    def setoff_processing(self) -> None:
        """
        Call methods to set off runfolder processing
            :return None:
        """
        if test_processing_software(self.script_logger):
            for runfolder in self.runfolder_names:
                self.demultiplex_runfolder(runfolder)
        self.return_num_processed_runfolders()

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
            shutdown_logs(self.demultiplex_obj.demux_rf_logger)

            # If runfolder has been processed during this script run
            if self.demultiplex_obj.run_processed:
                self.script_logger.info(
                    self.script_logger.log_msgs["runfolder_processed"],
                    folder_name,
                )
                # Add runfolder to processed runfolder list
                self.processed_runfolders.append(folder_name)

    def bcl2fastqlog_absent(self, folder_name: str) -> Union[bool, None]:
        """
        Check presence of demultiplex logfile (bcl2fastq2_output.log)
            :param folder_name(str):    Name of runfolder
            :return True|None:          Return true if demultiplex logfile exists
        """
        self.rf_obj = RunfolderObject(folder_name, self.timestamp)

        if os.path.isfile(self.rf_obj.bcl2fastqlog_file):
            self.script_logger.info(
                self.script_logger.log_msgs["demux_already_complete"],
                self.rf_obj.runfolder_name,
                self.rf_obj.bcl2fastqlog_file,
            )
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["demux_not_complete"],
                self.rf_obj.runfolder_name,
                self.rf_obj.bcl2fastqlog_file,
            )
            return True

    def return_num_processed_runfolders(self) -> None:
        """
        Add number of total processed runfolders as attribute
            :return None:
        """
        num_processed_runfolders = get_num_processed_runfolders(
            self.script_logger, self.processed_runfolders
        )
        setattr(self, "num_processed_runfolders", num_processed_runfolders)


class DemultiplexRunfolder(DemultiplexConfig):
    """
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present.

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
        disallowed_sserrs (list):           List of disallowed samplesheet error strings
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
            Check samplesheet is present and naming and contents are valid, using the
            samplesheet_validator module
        sequencing_complete()
            Check if sequencing has completed for the current runfolder (presence of
            RTAComplete.txt)
        dev_run(sscheck_obj)
            Determine whether the run is a development run using the sscheck_obj development_run() method
        dev_run_requires_automated_processing()
            Check whether the development run requires manual processing or automated
            processing by the script
        pass_integrity_check()
            Check whether the integrity checking was successful
        no_disallowed_sserrs(valid, sscheck_obj)
            Check for specific errors that would cause bcl2fastq2 to fail and whose
            presence should stop demultiplexing
        seq_requires_no_ic()
            Determines whether the run requires integrity checking (not possible on all
            sequencers)
        no_prior_ic()
            Determines whether an integrity check has been previously performed by this
            script
        checksums_match()
            Checks for checksum match string to determine whether the workstation
            runfolder matches that on the sequencer
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again
        add_bcl2fastqlog_tso_msg()
            If runfolder is from TSO500 run, add specific message to
            bcl2fastq2_output.log file (TSO500 runs do not require demultiplexing)
        calculate_cluster_density()
            Run dockerised GATK to run Picard CollecIlluminaLaneMetrics cluster density
            calculation
        run_demultiplexing()
            Run demultiplexing command
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
        self.rf_obj.add_runfolder_loggers()  # Add rf loggers to runfolder object
        self.demux_rf_logger = self.rf_obj.rf_loggers.demultiplex
        self.bcl2fastq2_rf_logger = self.rf_obj.rf_loggers.bcl2fastq2
        self.ss_validator_logger = self.rf_obj.rf_loggers.ss_validator
        self.disallowed_sserrs = [
            "sspresent_err",
            "ssname_err",
            "ssempty_err",
            "headers_err",
            "validchars_err",
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

    def setoff_workflow(self) -> Union[bool, None]:
        """
        Setoff demultiplex workflow only for runs where demultiplexing is required (TSO
        runs don't require demultiplexing). First calls self.create_bcl2fastqlog() to
        create the log file which prevents a simultaneous demultiplex attempt on the
        next run of the script (bcl2fastq2 is slow to create the logfile). Then calls
        calculate_cluster_density(). If a tso run, stops here. Else calls
        run_demultiplexing() to demultiplex the run.
            :return True|None:  Return true if run successfully processed
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

            if self.run_processed:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["runfolder_processed"],
                    self.rf_obj.runfolder_name,
                )
                return True

    def demultiplexing_required(self) -> Union[bool, None]:
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing is
        required. Carries out the early warning samplesheet checks. If sequencing is complete and
        the run is a development run, creates the bcl2fastq logfile to prevent further processing.
        Else, if sequencing is complete (RTAComplete.txt present) and the run is not a development
        run, the samplesheet contains no disallowed errors, and either 1) the sequencer does not
        require an integrity check or 2) there has not previously been an integrity check and the
        checksums match, returns True as demultiplexing is required
            :return True|None:  Return true if demultiplexing is required
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["ad_version"],
            git_tag(),
        )
        valid, sscheck_obj = self.valid_samplesheet()  # Early warning checks
        self.tso = sscheck_obj.tso

        if self.sequencing_complete():
            if self.pass_integrity_check():
                if self.dev_run(sscheck_obj):
                    if self.dev_run_requires_automated_processing():
                        return True
                # Only want samplesheet checks to be performed on production runs not dev runs
                elif self.no_disallowed_sserrs(valid, sscheck_obj):
                    return True

    def dev_run(self, sscheck_obj):
        """
        Determine whether the run is a development run using the sscheck_obj development_run() method
            :sscheck_obj (obj):     Object created by samplesheet_validator.SampleheetCheck
            :return (True | None):  Return true if development run, else None
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

    def dev_run_requires_automated_processing(self) -> None:
        """
        Check whether the development run requires manual processing or automated
        processing by the script. If the runfolder was supplied in command line mode,
        development run requires automated processing by the script. Otherwise,
        the bcl2fastqlog is created to prevent further processing, an alert will be
        sent to slack, and the development run will need to be processed by bioinformatics.
            :return (True | None): True if requires automated processing, else None
        """
        if self.cmd_line_supplied_runfolder:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["dev_run_will_be_processed"],
                self.rf_obj.runfolder_name,
            )
            return True
        # Create bcl2fastq log to prevent scripts processing this run
        elif self.create_bcl2fastqlog():
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["dev_run_needs_processing"],
                self.rf_obj.runfolder_name,
            )

    def pass_integrity_check(self) -> Union[bool, None]:
        """
        Check whether the integrity checking was successful
            :return (True | None):  True if successful, None if unsuccessful
        """
        if self.seq_requires_no_ic():
            return True
        if self.no_prior_ic():
            if self.checksums_match():
                return True

    def valid_samplesheet(self) -> Tuple[bool, object]:
        """
        Check samplesheet is present and naming and contents are valid, using the
        samplesheet_validator module
            :return (tuple):    Returns tuple of boolean (denotes whether samplesheet
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
        shutdown_logs(sscheck_obj.logger)
        if sscheck_obj.errors:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["sschecks_not_passed"],
                self.rf_obj.samplesheet_path,
            )
            return False, sscheck_obj
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sschecks_passed"],
                self.rf_obj.samplesheet_path,
            )
            return True, sscheck_obj

    def sequencing_complete(self) -> Union[bool, None]:
        """
        Check if sequencing has completed for the current runfolder - presence of
        RTAComplete.txt.
            :return True|None:  Returns true if sequencing is complete
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

    def no_disallowed_sserrs(
        self, valid: bool, sscheck_obj: object
    ) -> Union[bool, None]:
        """
        Check for specific errors that would cause bcl2fastq2 to fail and whose presence
        should stop demultiplexing
            :param valid (bool):            Denotes whether the samplesheet is valid
                                            (conforms to requirements)
            :param sscheck_obj (object):    samplesheet_validator.SamplesheetCheck
                                            object, generated by the samplesheet
                                            validator module
            :return True|None:              Returns true if samplesheet is valid
        """
        if not valid:
            if any(
                error in list(sscheck_obj.errors_dict.values())
                for error in self.disallowed_sserrs
            ):
                err_str = ", ".join(list(sscheck_obj.errors_dict.values()))
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["ssfail_haltdemux"],
                    self.rf_obj.samplesheet_path,
                    err_str,
                )
        else:
            return True

    def seq_requires_no_ic(self) -> Union[bool, None]:
        """
        Check whether integrity check needed. Only runs from sequencers that can have
        checksums generated require this - not all sequencers can have checksums
        generated by the integrity check script (MiSeq can't have checksums generated).
            :return True|None:  Return True if sequencer does not require an integrity
                                check
        """
        if any(
            item in self.rf_obj.runfolder_name
            for item in DemultiplexConfig.SEQ_REQUIRE_IC
        ):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["ic_required"])
        else:
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["ic_notrequired"])
            return True

    def no_prior_ic(self) -> Union[bool, None]:
        """
        Determines whether an integrity check has been previously performed by this
        script. Does this by checking whether the checksum file is present (this is
        where the checksums are written to by the integrity check scripts), then checks
        for the presence of the CHECKSUM_COMPLETE_MSG in the checksum file
        (this message is added when self.checksums_match() is called to
        prevent the script from performing further integrity checks until the cause of
        the problem is addressed)
            :return True|None:  Returns true if the checksum file has not previously
                                been checked for the success message by the script
        """
        if not os.path.isfile(self.rf_obj.checksumfile_path):
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["csumfile_absent"])
        else:
            self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["csumfile_present"])

            checksums = read_lines(self.rf_obj.checksumfile_path)

            if DemultiplexConfig.CHECKSUM_COMPLETE_MSG in checksums[-1]:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["checksums_checked"]
                )
            else:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["checksums_notchecked"]
                )
                return True

    def checksums_match(self) -> Union[bool, None]:
        """
        Opens file containing md5 checksums and writes CHECKSUM_COMPLETE_MSG to file
        to prevent script performing checks in the future. Reads the file and checks for
        the presence of the CHECKSUM_MATCH_MSG (this is added by the integrity check
        scripts if the checksums match, meaning that the runfolder has not been
        corrupted during transfer from the sequencer). If the match string is not
        present, this means the runfolder on the workstation does not match the
        runfolder on the sequencer.
            :return True|None:  Returns True if checksum match string is present in
                                checksum file
        """
        self.demux_rf_logger.info(self.demux_rf_logger.log_msgs["ic_start"])

        with open(self.rf_obj.checksumfile_path, "r") as f:
            checksums = f.readlines()

        write_lines(
            self.rf_obj.checksumfile_path, "a", DemultiplexConfig.CHECKSUM_COMPLETE_MSG
        )

        if DemultiplexConfig.CHECKSUM_MATCH_MSG in checksums[0]:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["ic_pass"],
                self.rf_obj.runfolder_name,
            )
            return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["ic_fail"],
                self.rf_obj.runfolder_name,
                self.rf_obj.checksumfile_path,
            )

    def create_bcl2fastqlog(self) -> Union[bool, None]:
        """
        Create file to prevent demultiplexing starting again. bl2fastq2 v2.20 doesn't
        produce stdout for a while after starting so the file is created and the
        bcl2fastq2 stdout is written to the file later. If unsuccessful, exit script
            :return True|None:  True if logfile is successfully created
        """
        try:
            open(self.rf_obj.bcl2fastqlog_file, "w", encoding="utf-8").close()
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_pass"],
                self.rf_obj.runfolder_name,
                self.rf_obj.bcl2fastqlog_file,
            )
            if self.tso:
                self.add_bcl2fastqlog_tso_msg()
            return True
        except Exception as exception:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_fail"],
                self.rf_obj.runfolder_name,
                exception,
            )
            sys.exit(1)

    def add_bcl2fastqlog_tso_msg(self) -> Union[bool, None]:
        """
        If runfolder is from TSO500 run, add specific message to bcl2fastq2_output.log
        file (TSO500 runs do not require demultiplexing)
            :return True|None:  True if log file successfully created and written to
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["tso500_run"],
            self.rf_obj.runfolder_name,
            DemultiplexConfig.STRINGS["demultiplexlog_tso500_msg"],
        )
        write_lines(
            self.rf_obj.bcl2fastqlog_file,
            "w+",
            DemultiplexConfig.STRINGS["demultiplexlog_tso500_msg"],
        )

        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["write_tso_msg_to_bcl2fastqlog"],
            self.rf_obj.runfolder_name,
        )
        return True

    def run_demultiplexing(self) -> Union[bool, None]:
        """
        Run demultiplexing command. If unsuccessful, exit script
            :return True|None:  True if command executed succesfully and output is
                                successfully written to the logfile
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["bcl2fastq_start"],
            self.rf_obj.runfolder_name,
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
                self.rf_obj.runfolder_name,
            )
            self.bcl2fastq2_rf_logger.info(
                err  # Write stderr to bcl2fastq2 runfolder logfile
            )
            return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastq_failed"],
                self.rf_obj.runfolder_name,
                out,
                err,
            )
            sys.exit(1)

    def calculate_cluster_density(self) -> Union[bool, None]:
        """
        Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
        cluster density and saves files (runfolder.illumina_phasing_metrics and
        runfolder.illumina_lane_metrics) to the runfolder. If the success statement is
        seen in the stderr, record in the log file else raise a slack alert and exit
        script. If run was sequenced on novaseq, an extra argument is provided
            :return True|None:  True if success statement seen
        """
        if DemultiplexConfig.NOVASEQ_ID in self.rf_obj.runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        self.cluster_density_cmd = f"{self.cluster_density_cmd }{novaseq_flag}"

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
                    self.rf_obj.runfolder_name,
                    DemultiplexConfig.STRINGS["lane_metrics_suffix"],
                )
                return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["cd_fail"],
                self.rf_obj.runfolder_name,
                err,
            )
            sys.exit(1)
