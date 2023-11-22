#!/usr/bin/python3
# coding=utf-8
"""
Demultiplexes NGS Run Folders. See Readme and docstrings for further details
"""
import sys
import os
import re
from typing import Union, Tuple
from config import ad_config
from ad_logger import ad_logger
from toolbox import toolbox
from samplesheet_validator import samplesheet_validator


class GetRunfolders(object):
    """
    Loop through and process NGS runfolders in a given directory

    Attributes
        runfolder_names (list):         List of runfolders, specified within ad_config
        script_logger (object):         Script-level logger
        timestamp (str):                Timestamp in the format %Y%m%d_%H%M%S
        processed_runfolders (list):    List to hold names of processed runfolders,
                                        updated dynamically
        num_processed_runfolders (int): No. runfolders processed during this cycle

    Methods
        get_runfolder_names()
            Get test-mode-dependent runfolder names
        setoff_processing()
            Call methods to set off runfolder processing
        demultiplex_runfolder(folder_name)
            Pass NGS runfolder to instance of DemultiplexRunfolder() for processing
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile (bcl2fastq2_output.log)
        return_num_processed_runfolders()
            Add number of total processed runfolders as attribute
    """

    def __init__(self):
        """
        Constructor for the GetRunfolders class
        """
        self.runfolder_names = []
        self.script_logger = ad_logger.AdLogger(
            "demultiplex",
            "demultiplex",
            toolbox.return_scriptlog_config()["demultiplex"],
        ).get_logger()
        self.timestamp = self.script_logger.timestamp
        self.processed_runfolders = []

    def get_runfolder_names(self) -> list:
        """
        Get test-mode-dependent runfolder names
            :return runfolder_names (list):  List of runfolder names
        """
        runfolder_names = []

        if ad_config.TESTING:
            folders = ad_config.DEMULTIPLEX_TEST_RUNFOLDERS
        else:
            folders = os.listdir(ad_config.RUNFOLDERS)

        for folder_name in folders:
            if toolbox.get_runfolder_path(folder_name) and re.compile(
                ad_config.RUNFOLDER_PATTERN
            ).match(folder_name):
                runfolder_names.append(folder_name)
        return runfolder_names

    def setoff_processing(self) -> None:
        """
        Call methods to set off runfolder processing
            :return None:
        """
        self.runfolder_names = self.get_runfolder_names()
        if toolbox.test_processing_software(self.script_logger):
            for runfolder in self.runfolder_names:
                self.demultiplex_runfolder(runfolder)
        self.return_num_processed_runfolders()

    def demultiplex_runfolder(self, folder_name: str) -> None:
        """
        Pass NGS runfolder to instance of DemultiplexRunfolder() for processing
            :param folder_name(str):    Name of runfolder
        """
        if self.bcl2fastqlog_absent(folder_name):
            demultiplex_obj = DemultiplexRunfolder(folder_name, self.timestamp)
            demultiplex_obj.setoff_workflow()
            ad_logger.shutdown_logs(demultiplex_obj.demux_rf_logger)

            # If runfolder has been processed during this script run
            if demultiplex_obj.run_processed:
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
        rf_obj = toolbox.RunfolderObject(folder_name, self.timestamp)

        if os.path.isfile(rf_obj.bcl2fastqlog_path):
            self.script_logger.info(
                self.script_logger.log_msgs["demux_already_complete"],
                rf_obj.runfolder_name,
                rf_obj.bcl2fastqlog_path,
            )
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["demux_not_complete"],
                rf_obj.runfolder_name,
                rf_obj.bcl2fastqlog_path,
            )
            return True

    def return_num_processed_runfolders(self) -> None:
        """
        Add number of total processed runfolders as attribute
            :return None:
        """
        num_processed_runfolders = toolbox.get_num_processed_runfolders(
            self.script_logger, self.processed_runfolders
        )
        setattr(self, "num_processed_runfolders", num_processed_runfolders)


class DemultiplexRunfolder(object):
    """
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present.

    Attributes
        timestamp (str):            Timestamp in the format %Y%m%d_%H%M%S
        rf_obj (obj):               RunfolderObject object (contains runfolder-specific
                                    attributes)
        demux_rf_logger (object):   Demultiplex runfolder-level logger, extracted from
                                    the RunfolderObject containing runfolder-level
                                    loggers
        disallowed_sserrs (list):   List of disallowed samplesheet error strings
        bcl2fastq2_cmd (str):       Shell command to run demultiplexing
        cluster_density_cmd (str):  Shell command to run cluster density calculation
        tso (bool):                 Denotes whether the run is a tso500 run
        run_processed (bool):       Denotes whether the run has been successfully
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
        development_run(sscheck_obj)
            Check if the run is a development run, by determining if the run contains
            any development pan numbers from the config file
        sequencing_complete()
            Check if sequencing has completed for the current runfolder (presence of
            RTAComplete.txt)
        no_disallowed_sserrs()
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
        check_bcl2fastqlogfile()
            Read last 10 lines of demultiplex logfile and search for success statement
    """

    def __init__(self, folder_name: str, timestamp: str):
        """
        Constructor for the DemultiplexRunfolder class
            :param folder_name(str):        Runfolder name
            :param timestamp (str):         Timestamp in the format %Y%m%d_%H%M%S
        """
        self.timestamp = timestamp
        self.rf_obj = toolbox.RunfolderObject(folder_name, self.timestamp)
        self.rf_obj.add_runfolder_loggers()  # Add rf loggers to runfolder object
        self.demux_rf_logger = self.rf_obj.rf_loggers.demultiplex
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
        self.bcl2fastq2_cmd = ad_config.BCL2FASTQ2_CMD % (
            self.rf_obj.runfolderpath,
            self.rf_obj.samplesheet_path,
            self.rf_obj.samplesheet_name,
            self.rf_obj.samplesheet_name,
            self.rf_obj.bcl2fastqlog_path,
        )
        # Shell command to run cluster density calculation
        self.cluster_density_cmd = ad_config.CD_CMD % (
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
        Carries out per-runfolder pre-demultiplexing tasks to determine whether
        demultiplexing is required. Carries out the early warning samplesheet
        checks. If sequencing is complete (RTAComplete.txt present), the
        samplesheet contains no disallowed errors, and either 1) the sequencer
        does not require an integrity check or 2) there has not previously been
        an integrity check and the checksums match, returns True as
        demultiplexing is required
            :return True|None:  Return true if demultiplexing is required
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["ad_version"],
            toolbox.git_tag(),
        )
        valid, sscheck_obj = self.valid_samplesheet()  # Early warning checks
        self.tso = sscheck_obj.tso
        if self.sequencing_complete():
            if self.no_disallowed_sserrs(valid, sscheck_obj):
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
            self.rf_obj.runfolder_name,
            self.ss_validator_logger,
        )
        if not self.development_run(sscheck_obj):
            sscheck_obj.ss_checks()
            ad_logger.shutdown_logs(sscheck_obj.logger)
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
        else:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["dev_run"],
                self.rf_obj.samplesheet_path,
            )

    def development_run(self, sscheck_obj: object) -> Union[bool, None]:
        """
        Check if the run is a development run, by determining if the run contains
        any development pan numbers from the config file
            :param sscheck_obj (object):    Object created by
                                            samplesheet_validator.SampleheetCheck
        """
        if any(
            panno in ad_config.DEVELOPMENT_PANELS for panno in sscheck_obj.pannumbers
        ):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["not_dev_run"],
                self.rf_obj.samplesheet_path,
            )
            return True

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
                error in sscheck_obj.errors_list for error in self.disallowed_sserrs
            ):
                err_str = ", ".join(sscheck_obj.errors_list)
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
            for item in ad_config.SEQUENCERS_WITH_INTEGRITY_CHECK
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
        for the presence of the ad_config.CHECKSUM_COMPLETE_MSG in the checksum file
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
            with open(
                self.rf_obj.checksumfile_path, "r", encoding="utf-8"
            ) as checksumfile:
                checksums = checksumfile.readlines()
                if ad_config.CHECKSUM_COMPLETE_MSG in checksums[-1]:
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
        with open(
            self.rf_obj.checksumfile_path, "r+", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            checksumfile.write(f"\n{ad_config.CHECKSUM_COMPLETE_MSG}")

            if ad_config.CHECKSUM_MATCH_MSG in checksums[0]:
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
        bcl2fastq2 stdout is written to the file later
            :return True|None:  True if logfile is successfully created
        """
        try:
            open(self.rf_obj.bcl2fastqlog_path, "w", encoding="utf-8").close()
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_pass"],
                self.rf_obj.runfolder_name,
                self.rf_obj.bcl2fastqlog_path,
            )
            if self.tso:
                self.add_bcl2fastqlog_tso_msg()
            return True
        except Exception as exception:
            self.demux_rf_logger.exception(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_fail"],
                self.rf_obj.runfolder_name,
                exception,
            )

    def add_bcl2fastqlog_tso_msg(self) -> Union[bool, None]:
        """
        If runfolder is from TSO500 run, add specific message to bcl2fastq2_output.log
        file (TSO500 runs do not require demultiplexing)
            :return True|None:  True if log file successfully created and written to
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["TSO500_run"],
            self.rf_obj.runfolder_name,
        )
        with open(self.rf_obj.bcl2fastqlog_path, "w+", encoding="utf-8") as log:
            log.write(f"\n{ad_config.STRINGS['demultiplexlog_tso500_msg']}")
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["write_TSO_msg_to_bcl2fastqlog"],
                self.rf_obj.runfolder_name,
            )
            return True

    def run_demultiplexing(self) -> Union[bool, None]:
        """
        Run demultiplexing command
            :return True|None:  True if command executed succesfully and output is
                                successfully written to the logfile
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["bcl2fastq_start"],
            self.rf_obj.runfolder_name,
            self.bcl2fastq2_cmd,
        )
        # Runs bcl2fastq2 and checks if completed successfully
        out, err, returncode = toolbox.execute_subprocess_command(
            self.bcl2fastq2_cmd,
            self.demux_rf_logger,
        )
        if returncode == 0:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["bcl2fastq_complete"],
                self.rf_obj.runfolder_name,
            )
            self.check_bcl2fastqlogfile()  # Check for success statement
            return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastq_failed"],
                self.rf_obj.runfolder_name,
                out,
                err,
            )
            sys.exit(1)

    # TODO investigate whether this is needed if we are checking the returncode
    def check_bcl2fastqlogfile(self) -> Union[bool, None]:
        """
        Read last x lines of bcl2fastqlog logfile, search for success statement
        The last 10 lines of the demultiplex logfile detail the success of the
        bcl2fastq2 command. If success statement not present, report last few
        lines to demultiplex log
            :return True|None:  True if success statement in bcl2fastq2 logfile
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_path):
            with open(self.rf_obj.bcl2fastqlog_path, "r", encoding="utf-8") as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])

            if bcl2fastq2_log_tail:
                if ad_config.STRINGS["demultiplex_success"] in str(bcl2fastq2_log_tail):
                    self.demux_rf_logger.info(
                        self.demux_rf_logger.log_msgs["demux_complete"],
                        self.rf_obj.runfolder_name,
                    )
                    return True
                else:
                    self.demux_rf_logger.error(
                        self.demux_rf_logger.log_msgs["demux_error"],
                        self.rf_obj.runfolder_name,
                        self.rf_obj.bcl2fastqlog_path,
                    )
                    sys.exit(1)
            else:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["bcl2fastqlog_empty"],
                    self.rf_obj.runfolder_name,
                    self.rf_obj.bcl2fastqlog_path,
                )
                sys.exit(1)
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastqlog_absent"],
                self.rf_obj.runfolder_name,
            )
            sys.exit(1)

    def calculate_cluster_density(self) -> Union[bool, None]:
        """
        Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this calculates
        cluster density and saves files (runfolder.illumina_phasing_metrics and
        runfolder.illumina_lane_metrics) to the runfolder. If the success statement is
        seen in the stderr, record in the log file else raise a slack alert but don't
        stop the run. If run was sequenced on novaseq, an extra argument is provided
            :return True|None:  True if success statement seen
        """
        if ad_config.NOVASEQ_ID in self.rf_obj.runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        self.cluster_density_cmd = f"{self.cluster_density_cmd }{novaseq_flag}"

        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["running_cd"],
            self.cluster_density_cmd,
        )
        out, err, returncode = toolbox.execute_subprocess_command(
            self.cluster_density_cmd, self.demux_rf_logger
        )

        if returncode == 0:
            # Assess stderr , looking for expected success statement
            if ad_config.STRINGS["cd_success"] in out or err:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["cd_success"],
                    self.rf_obj.runfolder_name,
                )
                return True
        else:  # Raise slack alert
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["cd_fail"],
                self.rf_obj.runfolder_name,
                err,
            )
            sys.exit(1)
