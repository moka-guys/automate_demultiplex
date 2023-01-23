# coding=utf-8
""" Demultiplex NGS Run Folders

The script performs demultiplexing, and also performs samplesheet validation using the seglh-naming
library on runs that have not yet been demultiplexed to act as an early warning system for
samplesheet errors.

Firstly, runs a set of checks on all runfolders in a given directory to determine whether
demultiplexing is required for that runfolder. The runfolder must meet the following requirements:
 - bcl2fastq2 logfile "bcl2fastq2_output.log" absent (demultiplexing not yet performed).
   bcl2fastq2 stdout and stderr streams are written to this file
 - Sequencing complete (presence of "RTAComplete.txt" file created by sequencer
   when sequencing completed)
 - bcl2fastq2 is installed
 - Sampleseheet does not contain any errors that would cause demultiplexing to fail. Must exist,
   be correctly named, be populated, contain minimum expected data headers, samplenames must only
   contain valid characters

If the sequencer does not require an integrity check, it skips straight to run_demultiplexing()

If the sequencer does require an integrity check the following requirements must be met
for demultiplexing to occur:
- Checksum file must be present
- The run has not failed a previous integrity check performed by this script
- The checksums match in the checksum file

run_demultiplexing then carries out demultiplexing tasks:
- Create a demultiplexing log file to prevent a simultaneous attempt on the next run of the script
  (bcl2fastq2 is slow to create the logfile)
- If the run is a tso run, creates a tso bcl2fastq2 log file but does not demultiplex
- Demultiplexes all other runs that get this far

If the script has processed any runfolders, it renames the logfile with the runfolder names
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


class GetRunfolders(object):
    """
    Loop through and process NGS runfolders in a given directory.
    Single class instance required to demultiplex all NGS runfolders. E.g.:
        >>> runs = GetListOfRuns().loop_through_runs()

    Methods:
        run_demultiplexrunfolders()
            Pass NGS runfolders to instance of DemultiplexRunfolder() for processing.
            After demultiplexing is performed (or skipped) for all runfolders,
                close script log file.
        bcl2fastq_installed()
            Check bcl2fastq exe file present and executable using os.access, raise
                exception if not installed
        rename_demultiplex_logfile()
            If runfolders processed, rename the logfile using processed runfolder names.
    """

    def __init__(self):
        """self.runfolders_path points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.runfolders_path = config.runfolders
        self.runfolder_names = os.listdir(self.runfolders_path)

        self.timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"

        # Script logfile for this hour's cron job
        self.demultiplex_logfile = os.path.join(config.demultiplex_logpath, f"{self.timestamp}.txt")

        # Pass the dictionary into ADloggers class - ** unpacks this dictionary to populate inputs
        # This is used as an object where various logs can be written
        self.logger_instance = ad_logger.AdLogger('demultiplex', self.demultiplex_logfile)
        self.demux_logger = self.logger_instance.logger
        self.demux_logpath = self.logger_instance.logfile_path

        # This has to be a class attribute for pytest purposes
        self.bcl2fastq_path = config.bcl2fastq_path

    def run_demultiplexrunfolders(self):
        """Pass NGS runfolders to instance of DemultiplexRunfolder() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file."""
        self.demux_logger.info(config.demux_logmsgs["demux_script_start"], git_tag(),
                               extra={"flag": "demultiplex_started"})
        processed_runfolders = []

        for (
            folder_name
        ) in (
            self.runfolder_names
        ):  # Pass runfolders to demultiplex.demultiplex_checks()
            runfolderpath = os.path.join(self.runfolders_path, folder_name)
            samplesheet_path = os.path.join(self.runfolders_path, "samplesheets", folder_name)
            if (
                self.bcl2fastq_installed()
                and os.path.isdir(runfolderpath)
                and re.compile(config.runfolder_pattern).match(folder_name)
            ):
                # If runfolder has been processed during this run of the scripts
                demultiplex_obj = DemultiplexRunfolder(samplesheet_path, runfolderpath,
                                                       folder_name, self.demux_logger)
                demultiplex_obj.setoff_workflow()
                if demultiplex_obj.run_processed:
                    # Add runfolder to processed runfolder list
                    processed_runfolders.append(folder_name)

        num_processed_runfolders = len(processed_runfolders)
        self.rename_demultiplex_logfile(processed_runfolders, num_processed_runfolders)

        self.demux_logger.info(
                    config.demux_logmsgs["demux_script_end"], git_tag(), num_processed_runfolders,
                    extra={"flag": "demultiplex_complete"})

        return processed_runfolders

    def bcl2fastq_installed(self):
        """Check bcl2fastq exe file present and executable using os.access,
        raise exception if not installed."""
        if os.access(self.bcl2fastq_path, os.X_OK):
            self.demux_logger.info(
                config.demux_logmsgs["bcl2fastq_test_pass"],
                extra={"flag": config.log_flags["success"]},
            )
            return True
        else:
            self.demux_logger.error(
                config.demux_logmsgs["bcl2fastq_test_fail"],
                extra={"flag": config.log_flags["fail"]},
            )

    def rename_demultiplex_logfile(self, processed_runfolders, num_processed_runfolders):
        """If runfolders processed by bcl2fastq during this cycle, rename the logfile using
        processed runfolder names.
        Allows easy identification of processed runs in logfile name, and differentiates log from
        others uploaded to DNAnexus"""

        if num_processed_runfolders > 0:
            processed_runs_str = "_".join(processed_runfolders)
            demultiplex_log_noext = os.path.splitext(self.demultiplex_logfile)[0]  # Remove file ext
            new_demultiplex_logfile = f"{demultiplex_log_noext}_{processed_runs_str}" \
                                      "_demultiplex_script_log.txt"

            os.rename(self.demultiplex_logfile, new_demultiplex_logfile)
            if os.path.exists(new_demultiplex_logfile):
                self.demux_logger.info(
                    config.demux_logmsgs["rename_demuxlog_success"], new_demultiplex_logfile,
                    extra={"flag": "success"})

                # Assign new logfile and create new adlogger instance
                self.demultiplex_logfile = new_demultiplex_logfile
                self.logger_instance.shutdown_logs()  # Shutdown the old logger
                # New logger using the renamed logfile
                self.logger_instance = ad_logger.AdLogger('demultiplex', self.demultiplex_logfile)
                self.demux_logger = self.logger_instance.logger
                return True
            else:
                self.demux_logger.info(
                    config.demux_logmsgs["rename_demuxlog_fail"], self.demultiplex_logfile,
                    extra={"flag": "fail"})


class DemultiplexRunfolder(object):
    """Call bcl2fastq2 on runfolders after asserting that runfolder has not been
    demultiplexed and a valid samplesheet is present.

    Methods:
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing is required
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexin tasks to determine whether
                demultiplexing required.
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile
        valid_samplesheet()
            Check samplesheet is present and naming and contents are valid. Returns error string
            and boolean
        sequencing_complete()
            Check if sequencing run has completed.
        no_disallowed_sserrs()
            Check for specific errors that would case bcl2fastq2 to fail and whose presence should
            stop demultipelxing
        integritycheck_not_required()
            Determines whether the run requires integrity checking (not possible on all sequencers).
        run_demultiplexing()
            Call demultiplexing functions
        checksumfile_present()
            Checks if checksums generated for the run (i.e. integrity checking scripts have
            completed for the run).
        prior_integritycheck_failed()
            Check if run previously failed integrity check (needs manual intervention before
            further processing).
        integrity_check_success()
            Checks whether checksums in the checksum file match
            i.e. the runfolder copied to workstation has not been corrupted by the transfer.
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again.
        add_bcl2fastqlog_tso_msg()
            If runfolder is from TSO500 run, specific message is added to bcl2fastq2_output.log
            file (TSO500 runs do not require demultiplexing)
        run_subprocess(cmd)
            Takes a string command as input and runs this as a subprocess
        check_bcl2fastqlogfile()
            Read last 10 lines of demultiplex logfile and search for success statement
        logger(message, flag)
            Write log messages to the system log.
    """

    def __init__(self, samplesheet_path, runfolderpath, folder_name, logger):
        # Logging
        self.demux_logger = logger
        # Runfolder
        self.runfolder_name = str(folder_name)
        self.runfolderpath = runfolderpath
        # Samplesheet
        self.samplesheet_path = samplesheet_path
        self.disallowed_sserrs = [
            "sspresent_err",
            "ssname_err",
            "ssempty_err",
            "headers_err",
            "validchars_err",
        ]
        # Sequencing finished
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, config.rtacomplete_filename
        )
        # Integrity check
        self.checksumfile_path = os.path.join(
            self.runfolderpath, config.md5checksum_filename
        )
        # Bcl2fastq
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, config.bcl2fastqlog_filename
        )
        # Shell command to run demultiplexing. Appends stdout and stderr to the bcl2fastqlog file.
        # (N.B. n--no-lane-splitting creates a single fastq for a sample, not into one fastq per
        # lane)
        self.bcl2fastq_cmd = f"{config.bcl2fastq_path} -R {self.runfolderpath} --sample-sheet \
            {self.samplesheet_path} --no-lane-splitting >> {self.bcl2fastqlog_path} 2>&1"

        self.run_processed = False

    def setoff_workflow(self):
        """Setoff demultiplex workflow only on runs where demultiplexing is required"""
        if self.demultiplexing_required():
            self.run_demultiplexing()

    def demultiplexing_required(self):
        """Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing
        required.
        Returns true if demultiplexing is required.
        """
        # Write to log file, recording automate_demultiplex repo version
        self.demux_logger.info(
            config.demux_logmsgs["demux_runfolder_start"], git_tag(), self.runfolderpath,
            extra={"flag": config.log_flags["info"]}
        )

        if self.bcl2fastqlog_absent():
            valid, sscheck_obj = self.valid_samplesheet()  # Early warning checks
            if self.sequencing_complete():
                if self.no_disallowed_sserrs(valid, sscheck_obj):
                    if self.integritycheck_not_required():
                        return True
                    elif self.checksumfile_present():
                        if not self.prior_integritycheck_failed():
                            if self.integrity_check_success():
                                # TSO500 runs do not require demultiplexing
                                if sscheck_obj.tso:
                                    self.add_bcl2fastqlog_tso_msg()
                                else:
                                    return True

    def run_demultiplexing(self):
        """Call demultiplexing functions
        TSO runs don't require demultiplexing. Create bcl2fastq2 log so scripts skip over these
        runs in future.
        """
        # Prevent simultaneous demultiplex attempt on next run of script
        # (bcl2fastq2 is slow to create logfile)
        if self.create_bcl2fastqlog():
            self.demux_logger.info(
                config.demux_logmsgs["bcl2fastq_start"], self.runfolder_name, self.bcl2fastq_cmd,
                extra={"flag": config.log_flags["info"]}
            )
            # Runs bcl2fastq2 and checks if completed successfully
            if self.run_subprocess(self.bcl2fastq_cmd):
                self.demux_logger.info(
                    config.demux_logmsgs["bcl2fastq_complete"], self.runfolder_name,
                    extra={"flag": config.log_flags["success"]}
                )
                self.check_bcl2fastqlogfile()  # Check for success statement in logfile
                self.run_processed = True
                return True
            else:
                self.demux_logger.error(
                    config.demux_logmsgs["bcl2fastq_failed"], self.runfolder_name,
                    extra={"flag": config.log_flags["fail"]}
                )

    def bcl2fastqlog_absent(self):
        """Check presence of demultiplex logfile
        ("bcl2fastq2_output.log" for backwards compatability)
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            self.demux_logger.info(
                config.demux_logmsgs["demux_already_complete"], self.bcl2fastqlog_path,
                extra={"flag": config.log_flags["info"]}
            )
        else:
            self.demux_logger.info(
                config.demux_logmsgs["demux_not_complete"], self.bcl2fastqlog_path,
                extra={"flag": config.log_flags["info"]}
            )
            return True

    def valid_samplesheet(self):
        """Check samplesheet is present and naming and contents are valid.
        Returns error string and boolean."""
        sscheck = SamplesheetCheck(
            self.samplesheet_path,
            config.sequencer_ids,
            panel_config.panel_list,
            config.runtype_list,
            panel_config.tso500_panel_list,
        )
        err_str = ", ".join(
            [item for sublist in sscheck.errors.values() for item in sublist]
        )
        if err_str:
            self.demux_logger.warning(
                config.demux_logmsgs["sschecks_not_passed"], self.samplesheet_path, err_str,
                extra={"flag": config.log_flags["ss_warning"]}
            )
            return False, sscheck
        else:
            self.demux_logger.info(
                config.demux_logmsgs["sschecks_passed"], self.samplesheet_path,
                extra={"flag": config.log_flags["success"]}
            )
            return True, sscheck

    def sequencing_complete(self):
        """Check if sequencing has completed for the current runfolder - presence of
        "RTAComplete.txt"."""
        if not os.path.isfile(self.rtacompletefile_path):
            self.demux_logger.info(
                config.demux_logmsgs["run_incomplete"],
                extra={"flag": config.log_flags["info"]},
            )
        else:
            self.demux_logger.info(
                config.demux_logmsgs["run_finished"], self.rtacompletefile_path,
                extra={"flag": config.log_flags["info"]}
            )
            return True

    def no_disallowed_sserrs(self, valid, sscheck_obj):
        """Check for specific errors that would case bcl2fastq2 to fail and whose
        presence should stop demultipelxing"""
        print(valid)
        print(sscheck_obj.errors)
        if not valid:
            if any(sscheck_obj.errors[key] for key in self.disallowed_sserrs):
                err_str = ", ".join(
                    [
                        item
                        for sublist in sscheck_obj.errors.values()
                        for item in sublist
                    ]
                )
                self.demux_logger.error(
                    config.demux_logmsgs["ssfail_haltdemux"], self.samplesheet_path, err_str,
                    extra={"flag": config.log_flags["fail"]}
                )
        else:
            return True

    def integritycheck_not_required(self):
        """Check whether integrity check needed. Only runs from sequencers that can have
        checksums generated require this - not all sequencers can have checksums generated by
        the integrity check script.
        """
        if any(
            item in self.runfolder_name
            for item in config.sequencers_with_integrity_check
        ):
            self.demux_logger.info(
                config.demux_logmsgs["ic_required"], extra={"flag": config.log_flags["info"]}
            )
        else:
            self.demux_logger.info(
                config.demux_logmsgs["ic_notrequired"],
                extra={"flag": config.log_flags["info"]},
            )
            return True

    def checksumfile_present(self):
        """Determines whether checksum file is present
        (checksums written to file by integrity check scripts)"""
        if not os.path.isfile(self.checksumfile_path):
            self.demux_logger.info(
                config.demux_logmsgs["csumfile_absent"],
                extra={"flag": config.log_flags["info"]},
            )
        else:
            self.demux_logger.info(
                config.demux_logmsgs["csumfile_present"],
                extra={"flag": config.log_flags["info"]},
            )
            return True

    def prior_integritycheck_failed(self):
        """Check if runfolder has failed a previous integrity check by this script
        Denoted by presence of config.checksum_complete_msg string in checksum file (flag added when
        self.integrity_check() called and config.checksum_match_msg is absent in the first line of
        the file - prevents integrity_check performing further integrity checks
        """
        with open(self.checksumfile_path, "r", encoding="utf-8") as checksumfile:
            checksums = checksumfile.readlines()  # Read checksum file into list

        # Last line in file, last element in list
        if config.checksum_complete_msg in checksums[-1]:
            self.demux_logger.info(
                ["checksums_checked"], extra={"flag": config.log_flags["info"]}
            )
            return True

    def integrity_check_success(self):
        """Checks whether checksums in the checksum file match - i.e. the runfolder copied to
        workstation has not been corrupted by the transfer.
        Checksum generation and initial integrity checks are carried out by the
        sequencer_checksum.py script running on the sequencer, and written to a checksum file for
        access by this script. Checksum generation and integrity check is not possible on all
        sequencers (i.e. miseq).

        Checksum file should contain:
            Pass/fail statement in Line 1, checksums for both copies of run folder on lines 2 and 3
            Function adds line to file to denote integrity check has been assessed - stops
            repetition if check fails
        """
        self.demux_logger.info(
            config.demux_logmsgs["ic_start"], extra={"flag": config.log_flags["info"]}
        )

        with open(
            self.checksumfile_path, "r", encoding="utf-8"
        ) as checksumfile:  # Open file containing md5 checksums
            checksums = checksumfile.readlines()  # Read checksums into list

        # Add a flag into the checksum file to prevent script performing future integrity checks
        with open(self.checksumfile_path, "a", encoding="utf-8") as checksumfile:
            checksumfile.write(f"\n{config.checksum_complete_msg}")

        # Line 1 contains pass/fail statement from integrity check script
        if config.checksum_match_msg in checksums[0]:
            self.demux_logger.info(
                config.demux_logmsgs["ic_pass"], self.runfolder_name,
                extra={"flag": config.log_flags["success"]}
            )
            return True  # checksums match
        else:
            self.demux_logger.error(config.demux_logmsgs["ic_fail"], self.runfolder_name,
                                    self.checksumfile_path,
                                    extra={"flag": config.log_flags["fail"]})

    def create_bcl2fastqlog(self):
        """Create file to prevent demultiplexing starting again.
        bl2fastq2 v2.20 doesn't produce stdout for a while after starting so create file here
        and append stdout later
        """
        print(self.bcl2fastqlog_path)
        try:
            open(self.bcl2fastqlog_path, "w", encoding="utf-8").close()
            self.demux_logger.info(
                config.demux_logmsgs["create_bcl2fastqlog_pass"], self.runfolder_name,
                extra={"flag": config.log_flags["info"]}
            )
            return True
        except Exception as exception:
            self.demux_logger.error(
                config.demux_logmsgs["create_bcl2fastqlog_fail"], self.runfolder_name, exception,
                extra={"flag": config.log_flags["fail"]}
            )

    def add_bcl2fastqlog_tso_msg(self):
        """If runfolder is from TSO500 run, specific message is added to bcl2fastq2_output.log
        file (TSO500 runs do not require demultiplexing)
        """
        self.demux_logger.info("%s is a %s", self.runfolder_name,
                               config.demultiplexing_logfile_tso500_msg,
                               extra={"flag": config.log_flags["success"]})
        # Create bcl2fastq log to store tso500 message
        if self.create_bcl2fastqlog():
            try:
                with open(self.bcl2fastqlog_path, "w+", encoding="utf-8") as log:
                    log.write(f"\n{config.demultiplexing_logfile_tso500_msg}")
                    self.demux_logger.info(
                        config.demux_logmsgs["create_tsobcl2fastqlog_pass"], self.runfolder_name,
                        extra={"flag": config.log_flags["info"]}
                    )
                return True
            except Exception as exception:
                self.demux_logger.error(
                    config.demux_logmsgs["create_tsobcl2fastqlog_fail"], self.runfolder_name,
                    exception, extra={"flag": config.log_flags["fail"]}
                )

    @staticmethod
    def run_subprocess(cmd):
        """Takes a string command as input and runs this as a subprocess."""
        return (
            subprocess.call([cmd], shell=True) == 0
        )  # Wait until subprocess completes

    def check_bcl2fastqlogfile(self):
        """Read last x lines of bcl2fastqlog logfile and search for success statement
        The last 10 lines of the demultiplex logfile detail the success of the bcl2fastq2 command
        If success statement not present, report last few lines to demultiplex log
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            with open(self.bcl2fastqlog_path, "r", encoding="utf-8") as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])
            if bcl2fastq2_log_tail:
                if re.search(
                    config.demultiplex_success_regex, str(bcl2fastq2_log_tail)
                ):
                    self.demux_logger.info(
                        config.demux_logmsgs["demux_complete"], self.runfolder_name,
                        extra={"flag": config.log_flags["success"]}
                    )
                    return True
                else:
                    self.demux_logger.error(
                        config.demux_logmsgs["demux_error"], self.runfolder_name,
                        self.bcl2fastqlog_path, extra={"flag": config.log_flags["fail"]}
                    )
            else:
                self.demux_logger.error(
                    config.demux_logmsgs["bcl2fastqlog_empty"], self.runfolder_name,
                    self.bcl2fastqlog_path, extra={"flag": config.log_flags["fail"]}
                )
        else:
            self.demux_logger.error(
                config.demux_logmsgs["bcl2fastqlog_absent"], self.runfolder_name,
                self.bcl2fastqlog_path, extra={"flag": config.log_flags["fail"]}
            )


if __name__ == "__main__":
    gr_obj = GetRunfolders()
    gr_obj.run_demultiplexrunfolders()
