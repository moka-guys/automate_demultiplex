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
import config.ad_config as ad_config  # Import ad_config file
import config.panel_config as panel_config
import runfolder_obj.runfolder_obj as runfolder_obj


timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"


# TODO merge this with the SequencingRuns class in usw
# TODO incorporate traceback into logging

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
        rename_demultiplex_logfile(processed_runfolders)
            If runfolders processed, rename the logfile using processed
            runfolder names.
        get_new_logger(new_demultiplex_logfile)
            Assign new logfile to class attribute, and create new adlogger
            instance
    """

    def __init__(self):
        """
        self.runfolders_path points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.timestamp = timestamp

        if ad_config.TESTING:
            self.runfolder_names = ad_config.DEMULTIPLEX_TEST_RUNFOLDERS
        else:
            self.runfolder_names = os.listdir(ad_config.RUNFOLDERS)
        self.loggers = ad_logger.AdLoggers(timestamp)

        # This has to be a class attribute for pytest purposes
        self.bcl2fastq_path = ad_config.EXECUTABLES['bcl2fastq']

    def demultiplex_runfolders(self):
        """
        Pass NGS runfolders to instance of DemultiplexRunfolder() for
        processing. After demultiplexing is performed (or skipped) for all
        runfolders, close script log file.
        """
        self.loggers.demultiplex_script.info(
            self.loggers.msgs["demultiplex"]["script_start"],
            git_tag(),
            extra={"flag": "demultiplex_started"},
        )
        self.bcl2fastq_installed()  # Test bcl2fastq is installed

        processed_runfolders = []

        for (
            folder_name
        ) in (
            self.runfolder_names
        ):  # Pass runfolders to demultiplex.demultiplex_checks()
            rf_obj = runfolder_obj.RunfolderObject(folder_name, self.timestamp)

            if (
                os.path.isdir(rf_obj.runfolderpath)
                and re.compile(ad_config.RUNFOLDER_PATTERN).match(folder_name)
            ):
                # If runfolder has been processed during this script run
                demultiplex_obj = DemultiplexRunfolder(folder_name)
                demultiplex_obj.setoff_workflow()
                demultiplex_obj.loggers.shutdown_logs()
                if demultiplex_obj.run_processed:
                    self.loggers.demultiplex_script.info(
                        (
                            self.loggers.msgs['demultiplex']
                            ["runfolder_processed"]
                        ),
                        folder_name,
                        extra={"flag": "demultiplex_complete"},
                    )
                    # Add runfolder to processed runfolder list
                    processed_runfolders.append(folder_name)

        # No. runfolders processed during this cycle
        num_processed_runfolders = len(processed_runfolders)
        # Comma delimited string of all runfolders demultiplexed in cycle
        processed_run_string = ", ".join(processed_runfolders)

        self.loggers.demultiplex_script.info(
            self.loggers.msgs["demultiplex"]["demux_script_end"],
            git_tag(),
            num_processed_runfolders,
            processed_run_string,
            extra={"flag": "demultiplex_complete"},
        )
        return processed_runfolders

    def bcl2fastq_installed(self):
        """
        Check bcl2fastq exe file present and executable using os.access,
        raise exception if not installed
        """
        if os.access(self.bcl2fastq_path, os.X_OK):
            self.loggers.demultiplex_script.info(
                self.loggers.msgs["demultiplex"]["bcl2fastq_test_pass"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["success"]},
            )
            return True
        else:
            self.loggers.demultiplex_script.error(
                self.loggers.msgs["demultiplex"]["bcl2fastq_test_fail"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
            )


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
            Check for absence of ad_config.checksum_complete_msg string in
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
        self.timestamp = timestamp

        # Runfolder object containing runfolder-specific attributes
        self.runfolder_obj = runfolder_obj.RunfolderObject(
            str(folder_name), self.timestamp
            )

        # This is used as an object where various logs can be written
        self.loggers = ad_logger.AdLoggers(self.timestamp, self.runfolder_obj)

        # Samplesheet
        self.disallowed_sserrs = [
            "sspresent_err",
            "ssname_err",
            "ssempty_err",
            "headers_err",
            "validchars_err",
        ]
        self.run_processed = False

        # Shell command to run demultiplexing
        self.bcl2fastq_cmd = ad_config.CMDS["bcl2fastq"] % (
            self.runfolder_obj.runfolderpath,
            self.runfolder_obj.samplesheet_path,
        )
        # Shell command to run cluster density calculation
        self.cluster_density_cmd = ad_config.CMDS["cluster_density"] % (
            self.runfolder_obj.runfolderpath,
            self.runfolder_obj.runfolder_name,
        )
        self.tso = False

    def setoff_workflow(self):
        """
        Setoff demultiplex workflow only on runs where demultiplexing
        is required
        """
        if self.demultiplexing_required():
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["demultiplexing_required"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            # TSO500 runs do not require demultiplexing
            if (
                self.tso and self.add_bcl2fastqlog_tso_msg() and
                self.calculate_cluster_density()
            ):
                self.run_processed = True
            elif self.create_bcl2fastqlog():
                if (
                    self.run_demultiplexing() and
                    self.calculate_cluster_density()
                ):
                    self.run_processed = True

            if self.run_processed:
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"]["runfolder_processed"],
                    self.runfolder_obj.runfolder_name,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
                )
                return True

    def demultiplexing_required(self):
        """
        Carries out per-runfolder pre-demultiplexing tasks to determine whether
        demultiplexing required.
        Returns true if demultiplexing is required.
        """
        # Write to log file, recording automate_demultiplex repo version
        self.loggers.demultiplex_rf.info(
            self.loggers.msgs["demultiplex"]["demux_runfolder_start"],
            git_tag(),
            self.runfolder_obj.runfolderpath,
            extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
        )
        if self.bcl2fastqlog_absent():
            (
                valid,
                sscheck_obj,
            ) = self.valid_samplesheet()  # Early warning checks
            self.tso = sscheck_obj.tso
            if self.sequencing_complete():
                if self.no_disallowed_sserrs(valid, sscheck_obj):
                    if self.seq_requires_no_ic():
                        return True
                    if self.no_prior_ic():
                        if self.checksums_match():
                            return True

    def bcl2fastqlog_absent(self):
        """
        Check presence of demultiplex logfile
        ("bcl2fastq2_output.log" for backwards compatability)
        """
        if os.path.isfile(self.runfolder_obj.bcl2fastqlog_path):
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["demux_already_complete"],
                self.runfolder_obj.bcl2fastqlog_path,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
        else:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["demux_not_complete"],
                self.runfolder_obj.bcl2fastqlog_path,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            return True

    def valid_samplesheet(self):
        """
        Check samplesheet is present and naming and contents are valid.
        Returns error string and boolean.
        """
        sscheck = SamplesheetCheck(
            self.runfolder_obj.samplesheet_path,
            ad_config.SEQUENCER_IDS,
            panel_config.PANELS,
            ad_config.RUNTYPE_LIST,
            panel_config.TSO500_PANELS,
        )
        err_str = ", ".join(
            [item for sublist in sscheck.errors.values() for item in sublist]
        )
        if err_str:
            self.loggers.demultiplex_rf.warning(
                self.loggers.msgs["demultiplex"]["sschecks_not_passed"],
                self.runfolder_obj.samplesheet_path,
                err_str,
                extra={
                    "flag": self.loggers.log_flags["demultiplex"]["ss_warning"]
                    },
            )
            return False, sscheck
        else:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["sschecks_passed"],
                self.runfolder_obj.samplesheet_path,
                extra={"flag": self.loggers.log_flags["demultiplex"]["success"]},
            )
            return True, sscheck

    def sequencing_complete(self):
        """
        Check if sequencing has completed for the current runfolder - presence
        of RTAComplete.txt.
        """
        if os.path.isfile(self.runfolder_obj.rtacompletefile_path):
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["run_finished"],
                self.runfolder_obj.rtacompletefile_path,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            return True
        else:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["run_incomplete"],
                self.runfolder_obj.rtacompletefile_path,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
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
                self.loggers.demultiplex_rf.error(
                    self.loggers.msgs["demultiplex"]["ssfail_haltdemux"],
                    self.runfolder_obj.samplesheet_path,
                    err_str,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
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
            item in self.runfolder_obj.runfolder_name
            for item in ad_config.SEQUENCERS_WITH_INTEGRITY_CHECK
        ):
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["ic_required"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
        else:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["ic_notrequired"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            return True

    def no_prior_ic(self):
        """
        Check if an integrity check has been performed previously. Denoted by
        presence of ad_config.checksum_complete_msg string in checksum file.
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
        if not os.path.isfile(self.runfolder_obj.checksumfile_path):
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["csumfile_absent"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
        else:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["csumfile_present"],
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            return True

    def checksum_complete_msg_absent(self):
        """
        Check for absence of ad_config.checksum_complete_msg string in checksum
        file. This string is the last line in the file, so last element in the
        list when the file is read. Absence of this string denotes that an
        integrity check has not yet been performed
        """
        with open(
            self.runfolder_obj.checksumfile_path, "r", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            if ad_config.CHECKSUM_COMPLETE_MSG in checksums[-1]:
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"]["checksums_checked"],
                    extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
                )
            else:
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"]["checksums_notchecked"],
                    extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
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
        self.loggers.demultiplex_rf.info(
            self.loggers.msgs["demultiplex"]["ic_start"],
            extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
        )

        with open(
            self.runfolder_obj.checksumfile_path, "r+", encoding="utf-8"
        ) as checksumfile:
            checksums = checksumfile.readlines()
            checksumfile.write(f"\n{ad_config.CHECKSUM_COMPLETE_MSG}")

            if ad_config.CHECKSUM_MATCH_MSG in checksums[0]:
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"]["ic_pass"],
                    self.runfolder_obj.runfolder_name,
                    extra={
                        "flag": self.loggers.log_flags["demultiplex"]["success"]
                        },
                )
                return True  # checksums match
            else:
                self.loggers.demultiplex_rf.error(
                    self.loggers.msgs["demultiplex"]["ic_fail"],
                    self.runfolder_obj.runfolder_name,
                    self.runfolder_obj.checksumfile_path,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
                )

    def create_bcl2fastqlog(self):
        """
        Create file to prevent demultiplexing starting again.
        bl2fastq2 v2.20 doesn't produce stdout for a while after starting so
        create file here and append stdout later
        """
        try:
            open(
                self.runfolder_obj.bcl2fastqlog_path, "w", encoding="utf-8"
            ).close()
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["create_bcl2fastqlog_pass"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
            return True
        except Exception as exception:
            self.loggers.demultiplex_rf.exception(
                self.loggers.msgs["demultiplex"]["create_bcl2fastqlog_fail"],
                self.runfolder_obj.runfolder_name,
                exception,
                extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
            )

    def add_bcl2fastqlog_tso_msg(self):
        """
        If runfolder is from TSO500 run, specific message is added to
        bcl2fastq2_output.log file (TSO500 runs do not require demultiplexing)
        """
        self.loggers.demultiplex_rf.info(
            self.loggers.msgs["demultiplex"]["TSO500_run"],
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["demultiplex"]["success"]},
        )
        if self.create_bcl2fastqlog():
            with open(
                self.runfolder_obj.bcl2fastqlog_path, "w+", encoding="utf-8"
            ) as log:
                log.write(f"\n{ad_config.DEMULTIPLEXLOG_TSO500MSG}")
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"][
                        "write_TSO_msg_to_bcl2fastqlog"
                    ],
                    self.runfolder_obj.runfolder_name,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
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
        self.loggers.demultiplex_rf.info(
            self.loggers.msgs["demultiplex"]["bcl2fastq_start"],
            self.runfolder_obj.runfolder_name,
            self.bcl2fastq_cmd,
            extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
        )
        # Runs bcl2fastq2 and checks if completed successfully
        bcl2fastq_out = self.run_subprocess(self.bcl2fastq_cmd)
        self.loggers.demultiplex_rf.info(
            bcl2fastq_out.returncode,
            extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
        )
        if bcl2fastq_out.returncode == 0:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["bcl2fastq_complete"],
                self.runfolder_obj.runfolder_name,
                extra={
                    "flag": self.loggers.log_flags["demultiplex"]["success"]
                    },
            )
            with open(
                self.runfolder_obj.bcl2fastqlog_path, "w", encoding="UTF-8"
            ) as bcl2fastqlogfile:
                bcl2fastqlogfile.write(
                    bcl2fastq_out.stdout.decode(encoding="UTF-8")
                )
                bcl2fastqlogfile.write(
                    bcl2fastq_out.stderr.decode(encoding="UTF-8")
                )
            self.check_bcl2fastqlogfile()  # Check for success statement
            # TODO investigate whether the above is written correctly and
            # in correct order
            return True
        else:
            self.loggers.demultiplex_rf.error(
                self.loggers.msgs["demultiplex"]["bcl2fastq_failed"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
            )

    def run_subprocess(self, cmd):
        """
        Takes a string command as input and runs this as a subprocess
        """
        completedprocess = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=True,
        )
        if completedprocess.returncode == 0:
            self.loggers.demultiplex_rf.info(
                self.loggers.msgs["demultiplex"]["subprocess_success"],
                cmd,
                completedprocess.returncode,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
        else:
            self.loggers.demultiplex_rf.error(
                self.loggers.msgs["demultiplex"]["subprocess_fail"],
                cmd,
                completedprocess.returncode,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
            )
        for line in completedprocess.stderr.decode("utf-8").split("\r\n"):
            self.loggers.demultiplex_rf.info(
                line,
                extra={"flag": self.loggers.log_flags["demultiplex"]["info"]}
            )

        return completedprocess

    def check_bcl2fastqlogfile(self):
        """
        Read last x lines of bcl2fastqlog logfile, search for success statement
        The last 10 lines of the demultiplex logfile detail the success of the
        bcl2fastq2 command. If success statement not present, report last few
        lines to demultiplex log
        """
        if os.path.isfile(self.runfolder_obj.bcl2fastqlog_path):
            with open(
                self.runfolder_obj.bcl2fastqlog_path, "r", encoding="utf-8"
            ) as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])

            if bcl2fastq2_log_tail:
                if re.search(
                    ad_config.DEMULTIPLEX_SUCCESS_REGEX,
                    str(bcl2fastq2_log_tail)
                ):
                    self.loggers.demultiplex_rf.info(
                        self.loggers.msgs["demultiplex"]["demux_complete"],
                        self.runfolder_obj.runfolder_name,
                        extra={
                            "flag":
                            self.loggers.log_flags["demultiplex"]["success"]
                            },
                    )
                    return True
                else:
                    self.loggers.demultiplex_rf.error(
                        self.loggers.msgs["demultiplex"]["demux_error"],
                        self.runfolder_obj.runfolder_name,
                        self.runfolder_obj.bcl2fastqlog_path,
                        extra={
                            "flag": self.loggers.log_flags["demultiplex"]["fail"]
                            },
                    )
            else:
                self.loggers.demultiplex_rf.error(
                    self.loggers.msgs["demultiplex"]["bcl2fastqlog_empty"],
                    self.runfolder_obj.runfolder_name,
                    self.runfolder_obj.bcl2fastqlog_path,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
                )
        else:
            self.loggers.demultiplex_rf.error(
                self.loggers.msgs["demultiplex"]["bcl2fastqlog_absent"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
            )

    # TODO improve this
    def calculate_cluster_density(self):
        """
        Run dockerised GATK to run Picard CollectIlluminaLaneMetrics - this
        calculates cluster density and saves files
        (runfolder.illumina_phasing_metrics and
        runfolder.illumina_lane_metrics) to the runfolder. If the success
        statement is seen in the stderr, record in the log file else raise
        slack alert but don't stop the run
            :return True|None:  True if success statement seen
        """

        # If novaseq need to give an extra flag to CollectIlluminaLaneMetrics
        if ad_config.NOVASEQ_ID in self.runfolder_obj.runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        self.cluster_density_cmd = f"{self.cluster_density_cmd }{novaseq_flag}"

        self.loggers.demultiplex_rf.info(
            self.loggers.msgs["demultiplex"]["running_cd"],
            self.cluster_density_cmd,
            extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
        )
        clusterdensity_out = self.run_subprocess(self.cluster_density_cmd)

        if clusterdensity_out.returncode == 0:
            # Assess stderr , looking for expected success statement
            if ad_config.STRINGS[
                "cd_success"
            ] in clusterdensity_out.stderr.decode(
                encoding="UTF-8"
            ) or ad_config.STRINGS[
                "cd_err"
            ] not in clusterdensity_out.stderr.decode(
                encoding="UTF-8"
            ):
                self.loggers.demultiplex_rf.info(
                    self.loggers.msgs["demultiplex"]["cd_success"],
                    self.runfolder_obj.runfolder_name,
                    extra={"flag": self.loggers.log_flags["demultiplex"]["info"]},
                )
                return True
        else:  # Raise slack alert
            self.loggers.demultiplex_rf.error(
                self.loggers.msgs["demultiplex"]["cd_fail"],
                self.runfolder_obj.runfolder_name,
                clusterdensity_out.stderr,
                extra={"flag": self.loggers.log_flags["demultiplex"]["fail"]},
            )
            self.loggers.demultiplex_rf.error(clusterdensity_out.returncode)


if __name__ == "__main__":
    gr_obj = GetRunfolders()
    gr_obj.demultiplex_runfolders()
