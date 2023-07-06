#!/usr/bin/python3
# coding=utf-8
"""
Demultiplexes NGS Run Folders. See Readme and docstrings for further details
"""
import os
import re
import ad_logger.ad_logger as ad_logger
import shared_functions.shared_functions as shared_functions
import samplesheet_validator.samplesheet_validator as samplesheet_validator
import config.ad_config as ad_config
from typing import Union, Tuple
import inspect


class GetRunfolders(object):
    """
    Loop through and process NGS runfolders in a given directory

    Attributes
        runfolder_names (list):         List of runfolders, specified within ad_config
        script_loggers (object):        AdLoggers object with script-level loggers
        timestamp (str):                Timestamp in the format %Y%m%d_%H%M%S
        processed_runfolders (list):    List to hold names of processed runfolders,
                                        updated dynamically
        num_processed_runfolders (int): No. runfolders processed during this cycle
        processed_run_string (str):     Comma delimited string of all runfolders
                                        demultiplexed in cycle

    Methods
        demultiplex_runfolders()
            Pass NGS runfolders to instance of DemultiplexRunfolder() for processing.
            Only processed if software passes tests, runfolder exists and matches the
            expected naming pattern
        test_software()
            Test the software is installed and performing
    """

    def __init__(self):
        """
        Constructor for the GetRunfolders class
        """
        self.runfolder_names = self.get_runfolder_names()
        self.script_logger = ad_logger.return_scriptlogger(
            'demultiplex', ad_config.TIMESTAMP
            )
        self.timestamp = self.script_logger.timestamp
        self.processed_runfolders = []

    def get_runfolder_names(self):
        """
        Get test-mode-dependent runfolder names
        """
        if ad_config.TESTING:
            return ad_config.DEMULTIPLEX_TEST_RUNFOLDERS
        else:
            return os.listdir(ad_config.RUNFOLDERS)

    def demultiplex_runfolders(self):
        """
        Pass NGS runfolders to instance of DemultiplexRunfolder() for processing. Only
        processed if software passes tests, runfolder exists and matches the expected
        naming pattern
            :return processed_runfolders (list):    List of runfolders processed by the
                                                    class
        """
        self.script_logger.info(
            self.script_logger.log_msgs["script_start"],
            shared_functions.git_tag(),
            "demultiplex.py",
            extra={"flag": self.script_logger.log_flags["info"] % "demultiplex"},
        )
        if self.test_software():
            for folder_name in self.runfolder_names:
                if (
                    shared_functions.get_runfolder_path(folder_name)
                    and re.compile(ad_config.RUNFOLDER_PATTERN).match(folder_name)
                ):
                    demultiplex_obj = DemultiplexRunfolder(
                        folder_name, self.timestamp, self.script_logger
                        )
                    demultiplex_obj.setoff_workflow()
                    ad_logger.shutdown_logs(demultiplex_obj.script_logger)

                    # If runfolder has been processed during this script run
                    if demultiplex_obj.run_processed:
                        self.script_logger.info(
                            self.script_logger.log_msgs["runfolder_processed"],
                            folder_name,
                            extra={
                                "flag": self.script_logger.log_flags["info"] % "demultiplex"
                                },
                        )
                        # Add runfolder to processed runfolder list
                        self.processed_runfolders.append(folder_name)

        setattr(self, 'num_processed_runfolders', len(self.processed_runfolders))
        setattr(self, 'processed_run_string', ", ".join(self.processed_runfolders))

        self.script_logger.info(
            self.script_logger.log_msgs["runfolders_processed"],
            self.num_processed_runfolders,
            self.processed_run_string,
            extra={"flag": self.script_logger.log_flags["info"] % "demultiplex"},
        )
        self.script_logger.info(
            self.script_logger.log_msgs["script_end"],
            shared_functions.git_tag(),
            "demultiplex.py",
            extra={"flag": self.script_logger.log_flags["info"] % "demultiplex"},
        )
        return self.processed_runfolders

    def test_software(self) -> Union[bool, None]:
        """
        Test the software is installed and performing, by calling the test_upload_agent
        and test_dx_toolkit functions
            :return True|None:  Return true if the tests all pass
        """
        if shared_functions.test_programs(
            "bcl2fastq2", self.script_logger
            ) and shared_functions.test_programs(
                "gatk_collect_lane_metrics", self.script_logger
        ):
            return True


# TODO update documentation
class DemultiplexRunfolder(object):
    """
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present.

    Attributes
        script_loggers (object):    AdLoggers object with script-level loggers
        timestamp (str):            Timestamp in the format %Y%m%d_%H%M%S
        rf_obj (object):            Contains runfolder-specific attributes
        loggers (object):           AdLoggers object with runfolder-level loggers
        disallowed_sserrs (list):   List of disallowed samplesheet error strings
        bcl2fastq_cmd (str):        Shell command to run demultiplexing
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
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile (bcl2fastq2_output.log)
        valid_samplesheet()
            Check samplesheet is present and naming and contents are valid, using the
            samplesheet_validator module
        sequencing_complete()
            Check if sequencing has completed for the current runfolder (presence of
            RTAComplete.txt)
        no_disallowed_sserrs()
            Check for specific errors that would case bcl2fastq2 to fail and whose
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
    def __init__(self, folder_name: str, timestamp: str, script_logger: object):
        """
        Constructor for the DemultiplexRunfolder class
            :param folder_name(str):        Runfolder name
            :param timestamp (str):         Timestamp in the format %Y%m%d_%H%M%S
            :param script_loggers (object): AdLoggers logging object with script-level
                                            logger attributes
        """
        self.timestamp = timestamp
        self.script_logger = script_logger
        self.rf_obj = shared_functions.RunfolderObject(
            folder_name, self.script_logger, self.timestamp
        )
        self.rf_obj.add_runfolder_loggers()  # Add rf loggers to runfolder object
        self.demux_rf_logger = self.rf_obj.rf_loggers.demultiplex
        self.disallowed_sserrs = [
            "sspresent_err",
            "ssname_err",
            "ssempty_err",
            "headers_err",
            "validchars_err",
        ]
        # N.B. --no-lane-splitting creates a single fastq for a sample,
        # not into one fastq per lane)
        self.bcl2fastq_cmd = (
            f"{ad_config.BCL2FASTQ_EXE} -R {self.rf_obj.runfolderpath} --sample-sheet "
            f"{self.rf_obj.samplesheet_path} --no-lane-splitting"
        )
        # Shell command to run cluster density calculation
        self.cluster_density_cmd = (
            f"sudo docker run --rm -v {self.rf_obj.runfolderpath}:/input_run "
            "broadinstitute/gatk:4.1.8.1 ./gatk CollectIlluminaLaneMetrics "
            f"--RUN_DIRECTORY /input_run --OUTPUT_DIRECTORY /input_run --OUTPUT_PREFIX "
            f"{self.rf_obj.runfolder_name}"
        )
        self.tso = False
        self.run_processed = False

    def setoff_workflow(self) -> Union[bool, None]:
        """
        Setoff demultiplex workflow only for runs where demultiplexing is required (TSO
        runs don't require demultiplexing). First calls self.create_bcl2fastqlog() to
        create the log file which prevents a simultaneous demultiplex attempt on the
        next run of the script (bcl2fastq2 is slow to create logfile). Then calls
        calculate_cluster_density(). If a tso run, stops here. Else calls
        run_demultiplexing() to demultiplex the run.
            :return True|None:  Return true if run successfully processed
        """
        if self.demultiplexing_required():
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["demultiplexing_required"],
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            if self.create_bcl2fastqlog() and self.calculate_cluster_density():
                # TSO500 runs do not require demultiplexing
                if self.tso:
                    self.demux_rf_logger.usw.info(
                        self.demux_rf_logger.log_msgs["tso_run"],
                        extra={
                            "flag": self.demux_rf_logger.log_flags["info"] %
                            "demultiplex"
                            },
                    )
                    self.run_processed = True
                elif self.run_demultiplexing():  # All other runs require demultiplexing
                    self.run_processed = True

            if self.run_processed:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["runfolder_processed"],
                    self.rf_obj.runfolder_name,
                    extra={
                        "flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"
                        },
                )
                return True

    def demultiplexing_required(self) -> Union[bool, None]:
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether
        demultiplexing is required. If bcl2fastq logfile is absent (not yet
        demultiplexed), carries out early warning samplesheet checks, and if sequencing
        is complete, the samplesheet contains no disallowed errors, and the checksums
        match (if checksum check is required), then demuliplexing is required
            :return True|None:  Return true if demultiplexing is required
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["demux_runfolder_start"],
            shared_functions.git_tag(),
            self.rf_obj.runfolderpath,
            extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
        )
        if self.bcl2fastqlog_absent():
            valid, sscheck_obj = self.valid_samplesheet()  # Early warning checks
            self.tso = sscheck_obj.tso
            if self.sequencing_complete():
                if self.no_disallowed_sserrs(valid, sscheck_obj):
                    if self.seq_requires_no_ic():
                        return True
                    if self.no_prior_ic():
                        if self.checksums_match():
                            return True

    def bcl2fastqlog_absent(self) -> Union[bool, None]:
        """
        Check presence of demultiplex logfile (bcl2fastq2_output.log)
            :return True|None:  Return true if demultiplex logfile exists
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_path):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["demux_already_complete"],
                self.rf_obj.bcl2fastqlog_path,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["demux_not_complete"],
                self.rf_obj.bcl2fastqlog_path,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            return True

    def valid_samplesheet(self) -> Tuple[bool, object]:
        """
        Check samplesheet is present and naming and contents are valid, using the
        samplesheet_validator module
            :return (tuple):    Returns tuple of boolean (denotes whether samplesheet
                                is valid), and SampleSheetCheck object containing any
                                errors identified
        """
        # TODO fix log messages appearing twice
        sscheck = samplesheet_validator.SamplesheetCheck(
            self.rf_obj.samplesheet_path,
            self.demux_rf_logger,
        )
        if sscheck.errors:
            self.demux_rf_logger.warning(
                self.demux_rf_logger.log_msgs["sschecks_not_passed"],
                self.rf_obj.samplesheet_path,
                extra={
                    "flag": self.demux_rf_logger.log_flags["ss_warning"] % "demultiplex"
                },
            )
            return False, sscheck
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["sschecks_passed"],
                self.rf_obj.samplesheet_path,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            return True, sscheck

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
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            return True
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["run_incomplete"],
                self.rf_obj.rtacompletefile_path,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )

    def no_disallowed_sserrs(
        self, valid: bool, sscheck_obj: object
    ) -> Union[bool, None]:
        """
        Check for specific errors that would case bcl2fastq2 to fail and whose presence
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
                    extra={
                        "flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"
                    },
                )
        else:
            return True

    def seq_requires_no_ic(self) -> Union[bool, None]:
        """
        Check whether integrity check needed. Only runs from sequencers that can have
        checksums generated require this - not all sequencers can have checksums
        generated by the integrity check script (miseq can't have checksums generated).
            :return True|None:  Return True if sequencer does not require an integrity
                                check
        """
        if any(
            item in self.rf_obj.runfolder_name
            for item in ad_config.SEQUENCERS_WITH_INTEGRITY_CHECK
        ):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["ic_required"],
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["ic_notrequired"],
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            return True

    def no_prior_ic(self) -> Union[bool, None]:
        """
        Determines whether an integrity check has been previously performed by this
        script. Does this by Checking whether the checksum file is present (this is
        where the checksums are written to by the integrity check scripts), then checks
        for the presence of the ad_config.checksum_complete_msg in the checksum file. If
        present, checks for the absence of the checksum complete message from the
        checksum file (this flag is added when self.checksums_match() is called to
        prevent the script from performing further integrity checks until the cause of
        the problem is addressed)
            :return True|None:  Returns true if the checksum file has not previously
                                been checked for the success message by the script
        """
        if not os.path.isfile(self.rf_obj.checksumfile_path):
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["csumfile_absent"],
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
        else:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["csumfile_present"],
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            with open(
                self.rf_obj.checksumfile_path, "r", encoding="utf-8"
            ) as checksumfile:
                checksums = checksumfile.readlines()
                if ad_config.CHECKSUM_COMPLETE_MSG in checksums[-1]:
                    self.demux_rf_logger.info(
                        self.demux_rf_logger.log_msgs["checksums_checked"],
                        extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
                    )
                else:
                    self.demux_rf_logger.info(
                        self.demux_rf_logger.log_msgs["checksums_notchecked"],
                        extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
                    )
                    return True

    def checksums_match(self) -> Union[bool, None]:
        """
        Opens file containing md5 checksums and writes checksum complete message to file
        to prevent script performing checks in the future. Reads the file and checks for
        the presence of the checksum match string (this is added by the integrity check
        scripts if the checksums match, meaning that the runfolder has not been
        corrupted during transfer from the sequencer). If the match string is not
        present, this means the runfolder on the workstation does not match the
        runfolder on the sequencer.
            :return True|None:  Returns True if checksum match string is present in
                                checksum file
        """
        self.demux_rf_logger.info(
            self.demux_rf_logger.log_msgs["ic_start"],
            extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
        )
        with open(
            self.rf_obj.checksumfile_path, "r+", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            checksumfile.write(f"\n{ad_config.CHECKSUM_COMPLETE_MSG}")

            if ad_config.CHECKSUM_MATCH_MSG in checksums[0]:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["ic_pass"],
                    self.rf_obj.runfolder_name,
                    extra={
                        "flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"
                        },
                )
                return True
            else:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["ic_fail"],
                    self.rf_obj.runfolder_name,
                    self.rf_obj.checksumfile_path,
                    extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
                )

    def create_bcl2fastqlog(self) -> Union[bool, None]:
        """
        Create file to prevent demultiplexing starting again. bl2fastq2 v2.20 doesn't
        produce stdout for a while after starting so the file is created and the
        bcl2fastq2 stdout is written to the file later
            :return True|None:  True if logfile is successfully created
        """
        try:
            open(
                self.rf_obj.bcl2fastqlog_path, "w", encoding="utf-8"
            ).close()
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_pass"],
                self.rf_obj.runfolder_name,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            if self.tso:
                self.add_bcl2fastqlog_tso_msg()
            return True
        except Exception as exception:
            self.demux_rf_logger.exception(
                self.demux_rf_logger.log_msgs["create_bcl2fastqlog_fail"],
                self.rf_obj.runfolder_name,
                exception,
                extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
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
            extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
        )
        with open(
            self.rf_obj.bcl2fastqlog_path, "w+", encoding="utf-8"
        ) as log:
            log.write(f"\n{ad_config.STRINGS['demultiplexlog_tso500_msg']}")
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs[
                    "write_TSO_msg_to_bcl2fastqlog"
                ],
                self.rf_obj.runfolder_name,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
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
            self.bcl2fastq_cmd,
            extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
        )
        # Runs bcl2fastq2 and checks if completed successfully
        out, err, returncode = shared_functions.execute_subprocess_command(
            self.bcl2fastq_cmd, self.demux_rf_logger
            )
        if returncode == 0:
            self.demux_rf_logger.info(
                self.demux_rf_logger.log_msgs["bcl2fastq_complete"],
                self.rf_obj.runfolder_name,
                extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
            )
            with open(
                self.rf_obj.bcl2fastqlog_path, "w", encoding="UTF-8"
            ) as bcl2fastqlogfile:
                bcl2fastqlogfile.write(out)
                bcl2fastqlogfile.write(err)
            self.check_bcl2fastqlogfile()  # Check for success statement
            return True
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastq_failed"],
                self.rf_obj.runfolder_name,
                extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
            )

    # TODO investigate whether this is needed if we are checking the returncode
    def check_bcl2fastqlogfile(self) -> Union[bool, None]:
        """
        Read last x lines of bcl2fastqlog logfile, search for success statement
        The last 10 lines of the demultiplex logfile detail the success of the
        bcl2fastq2 command. If success statement not present, report last few
        lines to demultiplex log
            :return True|None:  True if success statement in bcl2fastq logfile
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_path):
            with open(
                self.rf_obj.bcl2fastqlog_path, "r", encoding="utf-8"
            ) as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])

            if bcl2fastq2_log_tail:
                if (
                    ad_config.STRINGS['demultiplex_success_regex'] in
                    str(bcl2fastq2_log_tail)
                ):
                    self.demux_rf_logger.info(
                        self.demux_rf_logger.log_msgs["demux_complete"],
                        self.rf_obj.runfolder_name,
                        extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
                    )
                    return True
                else:
                    self.demux_rf_logger.error(
                        self.demux_rf_logger.log_msgs["demux_error"],
                        self.rf_obj.runfolder_name,
                        self.rf_obj.bcl2fastqlog_path,
                        extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
                    )
            else:
                self.demux_rf_logger.error(
                    self.demux_rf_logger.log_msgs["bcl2fastqlog_empty"],
                    self.rf_obj.runfolder_name,
                    self.rf_obj.bcl2fastqlog_path,
                    extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
                )
        else:
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["bcl2fastqlog_absent"],
                self.rf_obj.runfolder_name,
                extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
            )

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
            extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
        )
        out, err, returncode = shared_functions.execute_subprocess_command(
            self.cluster_density_cmd, self.demux_rf_logger
            )

        if returncode == 0:
            # Assess stderr , looking for expected success statement
            if ad_config.STRINGS["cd_success"] in out or err:
                self.demux_rf_logger.info(
                    self.demux_rf_logger.log_msgs["cd_success"],
                    self.rf_obj.runfolder_name,
                    extra={"flag": self.demux_rf_logger.log_flags["info"] % "demultiplex"},
                )
                return True
        else:  # Raise slack alert
            self.demux_rf_logger.error(
                self.demux_rf_logger.log_msgs["cd_fail"],
                self.rf_obj.runfolder_name,
                err,
                extra={"flag": self.demux_rf_logger.log_flags["fail"] % "demultiplex"},
            )
