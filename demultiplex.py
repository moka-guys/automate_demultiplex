# coding=utf-8
""" Demultiplex NGS Run Folders

The script performs demultiplexing, and also performs samplesheet validation
using the seglh-naming library on runs that have not yet been demultiplexed to
act as an early warning system for samplesheet errors.

Firstly, runs a set of checks on all runfolders in a given directory to
determine whether demultiplexing is required for that runfolder. The runfolder
must meet the following requirements:
 - bcl2fastq2 logfile "bcl2fastq2_output.log" absent (demultiplexing not yet
   performed). bcl2fastq2 stdout and stderr streams are written to this file
 - Sequencing complete (presence of "RTAComplete.txt" file created by sequencer
   when sequencing completed)
 - bcl2fastq2 is installed
 - Sampleseheet does not contain any errors that would cause demultiplexing to
   fail. Must exist, be correctly named, be populated, contain minimum
   expected data headers, samplenames must only contain valid characters

If the sequencer does not require an integrity check, it skips straight to
run_demultiplexing()

If the sequencer does require an integrity check the following requirements
must be met for demultiplexing to occur:
- Checksum file must be present
- The run has not failed a previous integrity check performed by this script
- The checksums match in the checksum file

run_demultiplexing then carries out demultiplexing tasks:
- Create a demultiplexing log file to prevent a simultaneous attempt on the
  next run of the script (bcl2fastq2 is slow to create the logfile)
- If the run is a tso run, creates a tso bcl2fastq2 log file but does not
  demultiplex
- Demultiplexes all other runs that get this far

If the script has processed any runfolders, it renames the logfile with the
runfolder names
"""

import os
import subprocess
import re
import datetime
import ad_logger.ad_logger as ad_logger
from git_tag.git_tag import git_tag  # Import function which reads the git tag
from samplesheet_validator.samplesheet_validator import SamplesheetCheck
import ad_config as config  # Import config file
import panel_config
from runfolder_obj.runfolder_obj import RunfolderObject


# TODO merge this with the SequencingRuns class in usw
class GetRunfolders(object):
    """
    Loop through and process NGS runfolders in a given directory.
    Single class instance required to demultiplex all NGS runfolders. E.g.:
        >>> runs = GetListOfRuns().loop_through_runs()

    Methods:
        demultiplex_runfolders()
            Pass NGS runfolders to DemultiplexRunfolder() instance for
            processing. After demultiplexing is performed (or skipped) for all
            runfolders, close script log file.
        bcl2fastq_installed()
            Check bcl2fastq exe file present and executable using os.access,
            raise exception if not installed
        get_new_logfilename(processed_runfolders)
            If runfolders have been processed, returns new logfile name
        rename_demultiplex_logfile(processed_runfolders)
            If runfolders processed, rename the logfile using processed
            runfolder names.
        get_new_logger(new_demultiplex_logfile)
            Assign new logfile to class attribute, and create new adlogger
            instance
    """

    def __init__(self):
        """self.runfolders_path points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.runfolders_path = config.RUNFOLDERS
        self.runfolder_names = os.listdir(self.runfolders_path)

        self.timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"

        # Call the function which populates a dictionary with the script
        # logfile for this hour's cron job
        self.log_config = ad_logger.get_log_config(self.timestamp)

        # Pass the log_config dictionary into ADloggers class
        # This is used as an object where various logs can be written
        self.loggers = ad_logger.AdLoggers(self.log_config)
        # This has to be a class attribute for pytest purposes
        self.bcl2fastq_path = config.BCL2FASTQ

    def demultiplex_runfolders(self):
        """Pass NGS runfolders to instance of DemultiplexRunfolder() for
        processing. After demultiplexing is performed (or skipped) for all
        runfolders, close script log file.
        """
        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["demux_script_start"],
            git_tag(),
            extra={"flag": "demultiplex_started"},
        )
        processed_runfolders = []

        for (
            folder_name
        ) in (
            self.runfolder_names
        ):  # Pass runfolders to demultiplex.demultiplex_checks()
            rf_obj = RunfolderObject(folder_name)

            if (
                self.bcl2fastq_installed()
                and os.path.isdir(rf_obj.runfolderpath)
                and re.compile(config.RUNFOLDER_PATTERN).match(folder_name)
            ):
                # If runfolder has been processed during this script run
                demultiplex_obj = DemultiplexRunfolder(folder_name)
                demultiplex_obj.setoff_workflow()
                if demultiplex_obj.run_processed:
                    # Add runfolder to processed runfolder list
                    processed_runfolders.append(folder_name)

        new_logfilename = self.get_new_logfilename(processed_runfolders)
        if new_logfilename:
            self.rename_demultiplex_logfile(new_logfilename)

        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["demux_script_end"],
            git_tag(),
            extra={"flag": "demultiplex_complete"},
        )
        self.loggers.shutdown_logs()
        return processed_runfolders

    def bcl2fastq_installed(self):
        """
        Check bcl2fastq exe file present and executable using os.access,
        raise exception if not installed
        """
        if os.access(self.bcl2fastq_path, os.X_OK):
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["bcl2fastq_test_pass"],
                extra={"flag": config.LOG_FLAGS["success"]},
            )
            return True
        else:
            self.loggers.demultiplex.error(
                config.LOG_MSGS["demultiplex"]["bcl2fastq_test_fail"],
                extra={"flag": config.LOG_FLAGS["fail"]},
            )

    def get_new_logfilename(self, processed_runfolders):
        """
        If runfolders have been processed, returns new logfile name
        """
        num_processed_runfolders = len(processed_runfolders)
        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["runfolders_processed"],
            str(num_processed_runfolders),
            extra={"flag": "pass"},
        )
        new_logfilename = None
        if num_processed_runfolders > 0:
            demultiplex_log_noext = os.path.splitext(
                self.log_config["demultiplex"]
            )[0]
            proc_rf_string = "_".join(processed_runfolders)
            new_logfilename = (
                f"{demultiplex_log_noext}_"
                f"{proc_rf_string}_demultiplex_script_log.txt"
            )
        return new_logfilename

    def rename_demultiplex_logfile(self, new_logfilename):
        """
        If runfolders processed by bcl2fastq during this cycle (number of
        processed runfolders is greater than 0), rename the logfile
        incorporating processed runfolder names. Allows easy identification of
        processed runs in logfile name, and differentiates log from others
        uploaded to DNAnexus
        """
        try:
            os.rename(self.log_config["demultiplex"], new_logfilename)
            self.get_new_logger(
                new_logfilename
            )  # Assign logger for renamed file
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["rename_demuxlog_pass"],
                self.log_config["demultiplex"],
                new_logfilename,
                extra={"flag": "pass"},
            )
            return True
        except Exception as exception:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["rename_demuxlog_fail"],
                self.log_config["demultiplex"],
                exception,
                extra={"flag": "fail"},
            )

    def get_new_logger(self, new_demultiplex_logfile):
        """
        Assign new logfile to class attribute, and create new adlogger instance
        """
        self.loggers.shutdown_logs()  # Shutdown the old logger
        self.log_config["demultiplex"] = new_demultiplex_logfile
        self.loggers = ad_logger.AdLoggers(
            self.log_config
        )  # Get logger for renamed file


class DemultiplexRunfolder(object):
    """
    Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present.

    Methods:
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing
            is required
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexing tasks to determine
            whether demultiplexing is required.
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile
        valid_samplesheet()
            Check samplesheet is present and naming and contents are valid.
        sequencing_complete()
            Check if sequencing run has completed.
        no_disallowed_sserrs()
            Check for specific errors that would case bcl2fastq2 to fail and
            whose presence should stop demultiplexing
        seq_requires_no_ic()
            Determines whether the run requires integrity checking (not
            possible on all sequencers)
        no_prior_ic()
            Calls checksumfile_present() and checksum_complete_msg_absent() to
            determine whether an integrity check has been performed previously
        checksumfile_present()
            Checks if checksums generated for the run (i.e. integrity checking
            scripts have completed for the run, writing checksums to file).
        checksum_complete_msg_absent()
            Check for absence of config.checksum_complete_msg string in
            checksum file, denoting integrity check has not yet been performed
        checksums_match()
            Calls prevent_future_ics() to write checksum complete statement to
            file to prevent future integrity checks, checks md5 checksum file
            for checksum match message. If found, runfolder has not been
            corrupted during transfer
        prevent_future_ics()
            Add flag into file containing md5 checksums to prevent script
            performing future integrity checks
        run_demultiplexing()
            Call demultiplexing functions
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again.
        add_bcl2fastqlog_tso_msg()
            If runfolder is from TSO500 run, specific message is added to
            bcl2fastq2_output.log file (TSO500 runs do not require
            demultiplexing)
        run_subprocess(cmd)
            Takes a string command as input and runs this as a subprocess
        check_bcl2fastqlogfile()
            Read last 10 lines of demultiplex logfile and search for success
            statement
    """

    def __init__(self, folder_name):
        self.timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"

        # Runfolder object containing runfolder-specific attributes
        self.rf_obj = RunfolderObject(str(folder_name))
        # Call the function which populates a dictionary with the script
        # logfile for this hour's cron job
        self.log_config = ad_logger.get_log_config(self.timestamp)

        # Pass the log_config dictionary into ADloggers class
        # This is used as an object where various logs can be written
        self.loggers = ad_logger.AdLoggers(self.log_config)

        # Samplesheet
        self.disallowed_sserrs = [
            "sspresent_err",
            "ssname_err",
            "ssempty_err",
            "headers_err",
            "validchars_err",
        ]
        self.run_processed = False

        # Shell command to run demultiplexing. Appends stdout and stderr to
        # the bcl2fastqlog file. (N.B. n--no-lane-splitting creates a single
        # fastq for a sample, not into one fastq per lane)
        self.bcl2fastq_cmd = (
            f"{config.BCL2FASTQ} -R {self.rf_obj.runfolderpath} "
            "--sample-sheet {self.rf_obj} --no-lane-splitting >> "
            f"{self.rf_obj.bcl2fastqlog_path} 2>&1"
        )

    def setoff_workflow(self):
        """
        Setoff demultiplex workflow only on runs where demultiplexing
        is required
        """
        if self.demultiplexing_required():
            return self.run_demultiplexing()

    def demultiplexing_required(self):
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether
        demultiplexing required.
        Returns true if demultiplexing is required.
        """
        # Write to log file, recording automate_demultiplex repo version
        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["demux_runfolder_start"],
            git_tag(),
            self.rf_obj.runfolderpath,
            extra={"flag": config.LOG_FLAGS["info"]},
        )
        if self.bcl2fastqlog_absent():
            (
                valid,
                sscheck_obj,
            ) = self.valid_samplesheet()  # Early warning checks
            if self.sequencing_complete():
                if self.no_disallowed_sserrs(valid, sscheck_obj):
                    if self.seq_requires_no_ic():
                        return True
                    if self.no_prior_ic():
                        if self.checksums_match():
                            if (
                                sscheck_obj.tso
                            ):  # TSO500 runs do not require demultiplexing
                                self.add_bcl2fastqlog_tso_msg()
                            else:
                                return True

    def bcl2fastqlog_absent(self):
        """
        Check presence of demultiplex logfile
        ("bcl2fastq2_output.log" for backwards compatability)
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_path):
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["demux_already_complete"],
                self.rf_obj.bcl2fastqlog_path,
                extra={"flag": config.LOG_FLAGS["info"]},
            )
        else:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["demux_not_complete"],
                self.rf_obj.bcl2fastqlog_path,
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            return True

    def valid_samplesheet(self):
        """
        Check samplesheet is present and naming and contents are valid.
        Returns error string and boolean.
        """
        sscheck = SamplesheetCheck(
            self.rf_obj.samplesheet_path,
            config.SEQUENCER_IDS,
            panel_config.PANEL_LIST,
            config.RUNTYPE_LIST,
            panel_config.TSO500_PANEL_LIST,
        )
        err_str = ", ".join(
            [item for sublist in sscheck.errors.values() for item in sublist]
        )
        if err_str:
            self.loggers.demultiplex.warning(
                config.LOG_MSGS["demultiplex"]["sschecks_not_passed"],
                self.rf_obj.samplesheet_path,
                err_str,
                extra={"flag": config.LOG_FLAGS["ss_warning"]},
            )
            return False, sscheck
        else:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["sschecks_passed"],
                self.rf_obj.samplesheet_path,
                extra={"flag": config.LOG_FLAGS["success"]},
            )
            return True, sscheck

    def sequencing_complete(self):
        """
        Check if sequencing has completed for the current runfolder - presence
        of RTAComplete.txt.
        """
        if os.path.isfile(self.rf_obj.rtacompletefile_path):
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["run_finished"],
                self.rf_obj.rtacompletefile_path,
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            return True
        else:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["run_incomplete"],
                self.rf_obj.rtacompletefile_path,
                extra={"flag": config.LOG_FLAGS["info"]},
            )

    def no_disallowed_sserrs(self, valid, sscheck_obj):
        """
        Check for specific errors that would case bcl2fastq2 to fail and whose
        presence should stop demultipelxing
        """
        if not valid:
            if any(sscheck_obj.errors[key] for key in self.disallowed_sserrs):
                err_str = ", ".join(
                    [
                        item
                        for sublist in sscheck_obj.errors.values()
                        for item in sublist
                    ]
                )
                self.loggers.demultiplex.error(
                    config.LOG_MSGS["demultiplex"]["ssfail_haltdemux"],
                    self.rf_obj.samplesheet_path,
                    err_str,
                    extra={"flag": config.LOG_FLAGS["fail"]},
                )
        else:
            return True

    def seq_requires_no_ic(self):
        """
        Check whether integrity check needed. Only runs from sequencers that
        can have checksums generated require this - not all sequencers can have
        checksums generated by the integrity check script (miseq can't have
        checksums generated).
        """
        if any(
            item in self.rf_obj.runfolder_name
            for item in config.SEQUENCERS_WITH_INTEGRITY_CHECK
        ):
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["ic_required"],
                extra={"flag": config.LOG_FLAGS["info"]},
            )
        else:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["ic_notrequired"],
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            return True

    def no_prior_ic(self):
        """
        Check if an integrity check has been performed previously. Denoted by
        presence of config.checksum_complete_msg string in checksum file.
        Is checksum file present, is checksum complete message absent from the
        checksum file (this flag is added when self.checksums_match() is called
        to prevent the script from performing further integrity checks until
        the cause of the problem is addressed).
        """
        if self.checksumfile_present() and self.checksum_complete_msg_absent():
            return True

    def checksumfile_present(self):
        """Determines whether checksum file is present
        (checksums written to file by integrity check scripts)"""
        if not os.path.isfile(self.rf_obj.checksumfile_path):
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["csumfile_absent"],
                extra={"flag": config.LOG_FLAGS["info"]},
            )
        else:
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["csumfile_present"],
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            print("present")
            return True

    def checksum_complete_msg_absent(self):
        """Check for absence of config.checksum_complete_msg string in
        checksum file. This string is the last line in the file, so last
        element in list when file is read. Absence of this string denotes that
        an integrity check has not yet been performed
        """
        with open(
            self.rf_obj.checksumfile_path, "r", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            if config.CHECKSUM_COMPLETE_MSG in checksums[-1]:
                self.loggers.demultiplex.info(
                    config.LOG_MSGS["demultiplex"]["checksums_checked"],
                    extra={"flag": config.LOG_FLAGS["info"]},
                )
            else:
                self.loggers.demultiplex.info(
                    config.LOG_MSGS["demultiplex"]["checksums_notchecked"],
                    extra={"flag": config.LOG_FLAGS["info"]},
                )
                return True

    def checksums_match(self):
        """
        Open file containing md5 checksums. Add flag into file containing md5
        checksums to prevent script performing future integrity checks. Read
        file into list. Line 1 of checksum file contains a pass / fail
        statement from the integrity check scripts

        Then performs an integrity check by opening the md5 checksum file and
        looking for the pass/fail integrity check statement in line 1 of the
        file which was written by the integrity check scripts.

        If statement is present, this means the runfolder copied to the
        workstation has not been corrupted by the transfer.

        Checksum generation and initial integrity checks are carried out by the
        sequencer_checksum.py script running on the sequencer, and written to
        a checksum file for access by this script.

        Checksum file should contain:
            Pass/fail statement in Line 1, checksums for both copies of run
            folder on lines 2 and 3 Function adds line to file to denote
            integrity check has been assessed - stops repetition if check fails
        """
        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["ic_start"],
            extra={"flag": config.LOG_FLAGS["info"]},
        )

        with open(
            self.rf_obj.checksumfile_path, "r+", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            checksumfile.write(f"\n{config.CHECKSUM_COMPLETE_MSG}")

            if config.CHECKSUM_MATCH_MSG in checksums[0]:
                self.loggers.demultiplex.info(
                    config.LOG_MSGS["demultiplex"]["ic_pass"],
                    self.rf_obj.runfolder_name,
                    extra={"flag": config.LOG_FLAGS["success"]},
                )
                return True  # checksums match
            else:
                self.loggers.demultiplex.error(
                    config.LOG_MSGS["demultiplex"]["ic_fail"],
                    self.rf_obj.runfolder_name,
                    self.rf_obj.checksumfile_path,
                    extra={"flag": config.LOG_FLAGS["fail"]},
                )

    def create_bcl2fastqlog(self):
        """
        Create file to prevent demultiplexing starting again.
        bl2fastq2 v2.20 doesn't produce stdout for a while after starting so
        create file here and append stdout later
        """
        try:
            open(self.rf_obj.bcl2fastqlog_path, "w", encoding="utf-8").close()
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["create_bcl2fastqlog_pass"],
                self.rf_obj.runfolder_name,
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            return True
        except Exception as exception:
            self.loggers.demultiplex.error(
                config.LOG_MSGS["demultiplex"]["create_bcl2fastqlog_fail"],
                self.rf_obj.runfolder_name,
                exception,
                extra={"flag": config.LOG_FLAGS["fail"]},
            )

    def add_bcl2fastqlog_tso_msg(self):
        """
        If runfolder is from TSO500 run, specific message is added to
        bcl2fastq2_output.log file (TSO500 runs do not require demultiplexing)
        """
        self.loggers.demultiplex.info(
            config.LOG_MSGS["demultiplex"]["TSO500_run"],
            self.rf_obj.runfolder_name,
            extra={"flag": config.LOG_FLAGS["success"]},
        )
        if self.create_bcl2fastqlog():
            with open(
                self.rf_obj.bcl2fastqlog_path, "w+", encoding="utf-8"
            ) as log:
                log.write(f"\n{config.DEMULTIPLEXLOG_TSO500MSG}")
                self.loggers.demultiplex.info(
                    config.LOG_MSGS["demultiplex"][
                        "write_TSO_msg_to_bcl2fastqlog"
                    ],
                    self.rf_obj.runfolder_name,
                    extra={"flag": config.LOG_FLAGS["info"]},
                )
                return True

    def run_demultiplexing(self):
        """
        Call demultiplexing functions
        TSO runs don't require demultiplexing. First calls
        self.create_bcl2fastqlog() to create the log file which prevents a
        simultaneous demultiplex attempt on the next run of the script
        (bcl2fastq2 is slow to create logfile)
        """
        if self.create_bcl2fastqlog():
            self.loggers.demultiplex.info(
                config.LOG_MSGS["demultiplex"]["bcl2fastq_start"],
                self.rf_obj.runfolder_name,
                self.bcl2fastq_cmd,
                extra={"flag": config.LOG_FLAGS["info"]},
            )
            # Runs bcl2fastq2 and checks if completed successfully
            if self.run_subprocess(self.bcl2fastq_cmd):
                self.loggers.demultiplex.info(
                    config.LOG_MSGS["demultiplex"]["bcl2fastq_complete"],
                    self.rf_obj.runfolder_name,
                    extra={"flag": config.LOG_FLAGS["success"]},
                )
                self.check_bcl2fastqlogfile()  # Check for success statement
                self.run_processed = True
                return True
            else:
                self.loggers.demultiplex.error(
                    config.LOG_MSGS["demultiplex"]["bcl2fastq_failed"],
                    self.rf_obj.runfolder_name,
                    extra={"flag": config.LOG_FLAGS["fail"]},
                )

    # TODO add capturing errors
    @staticmethod
    def run_subprocess(cmd):
        """Takes a string command as input and runs this as a subprocess"""
        return (
            subprocess.call([cmd], shell=True) == 0
        )  # Wait until subprocess completes

    def check_bcl2fastqlogfile(self):
        """Read last x lines of bcl2fastqlog logfile and search for success
        statement
        The last 10 lines of the demultiplex logfile detail the success of the
        bcl2fastq2 command. If success statement not present, report last few
        lines to demultiplex log
        """
        if os.path.isfile(self.rf_obj.bcl2fastqlog_path):
            with open(
                self.rf_obj.bcl2fastqlog_path, "r", encoding="utf-8"
            ) as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])
            if bcl2fastq2_log_tail:
                if re.search(
                    config.DEMULTIPLEX_SUCCESS_REGEX, str(bcl2fastq2_log_tail)
                ):
                    self.loggers.demultiplex.info(
                        config.LOG_MSGS["demultiplex"]["demux_complete"],
                        self.rf_obj.runfolder_name,
                        extra={"flag": config.LOG_FLAGS["success"]},
                    )
                    return True
                else:
                    self.loggers.demultiplex.error(
                        config.LOG_MSGS["demultiplex"]["demux_error"],
                        self.rf_obj.runfolder_name,
                        self.rf_obj.bcl2fastqlog_path,
                        extra={"flag": config.LOG_FLAGS["fail"]},
                    )
            else:
                self.loggers.demultiplex.error(
                    config.LOG_MSGS["demultiplex"]["bcl2fastqlog_empty"],
                    self.rf_obj.runfolder_name,
                    self.rf_obj.bcl2fastqlog_path,
                    extra={"flag": config.LOG_FLAGS["fail"]},
                )
        else:
            self.loggers.demultiplex.error(
                config.LOG_MSGS["demultiplex"]["bcl2fastqlog_absent"],
                self.rf_obj.runfolder_name,
                extra={"flag": config.LOG_FLAGS["fail"]},
            )


if __name__ == "__main__":
    gr_obj = GetRunfolders()
    gr_obj.demultiplex_runfolders()
