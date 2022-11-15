# coding=utf-8
""" Demultiplex NGS Run Folders

The script performs demultiplexing, and also performs samplesheet validation using the seglh-naming library on runs
that have not yet been demultiplexed to act as an early warning system for samplesheet errors.

Firstly, runs a set of checks on all runfolders in a given directory to determine whether demultiplexing
is required for that runfolder. The runfolder must meet the following requirements:
 - bcl2fastq logfile "bcl2fastq2_output.log" absent (demultiplexing not yet performed). bcl2fastq stdout and stderr
   streams are written to this file
 - Sequencing complete (presence of "RTAComplete.txt" file created by sequencer when sequencing completed)
 - bcl2fastq is installed
 - Sampleseheet does not contain any errors that would cause demultiplexing to fail. Must exist, be correctly named, be
   populated, contain minimum expected data headers, samplenames must only contain valid characters

If the sequencer does not require an integrity check, it skips straight to run_demultiplexing()

If the sequencer does require an integrity check the following requirements must be met for demultiplexing to occur:
- Checksum file must be present
- The run has not failed a previous integrity check performed by this script
- The checksums match in the checksum file

run_demultiplexing then carries out demultiplexing tasks:
- Create a demultiplexing log file to prevent a simultaneous attempt on the next run of the script (bcl2fastq is slow
  to create the logfile)
- If the run is a tso run, creates a tso bcl2fastq log file but does not demultiplex
- Demultiplexes all other runs that get this far

If the script has processed any runfolders, it renames the logfile with the runfolder names
"""

import os
import subprocess
import datetime
import smtplib
import re
from email.message import Message
import automate_demultiplex_config as config  # Import config file
from git_tag.git_tag import git_tag  # Import function which reads the git tag
from samplesheet_validator.samplesheet_validator import SamplesheetCheck


class GetListOfRuns(object):
    """
    Loop through and process NGS runfolders in a given directory.
    Single class instance required to demultiplex all NGS runfolders. E.g.:
        >>> runs = GetListOfRuns().loop_through_runs()

    Methods:
        loop_through_runs()
            Pass each runfolder to an instance of ReadyToStartDemultiplexing().
        rename_demultiplex_logfile()
            Rename the logfile using runfolder names
    """

    def __init__(self):
        """self.runfolder_dir points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.runfolder_dir = config.runfolders
        self.runfolders = os.listdir(self.runfolder_dir)
        # Set script log file path and name for this hour's cron job (script log file).
        self.scriptlog = "{}{}.txt".format(config.demultiplex_logfiles,
                                           str('{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())))
        open(self.scriptlog, 'w').close()  # Create logfile
        # Create class instance for checking and running demultiplexing per runfolder
        self.runfolder_pattern = config.runfolder_pattern
        self.ignore_dirs = config.ignore_directories
        self.demultiplex = ReadyToStartDemultiplexing(self.scriptlog, self.runfolder_dir)
        self.num_processed_runfolders = 0  # Default value 0

    def loop_through_runs(self):
        """Pass NGS runfolders to instance of ReadyToStartDemultiplexing() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file.
        """
        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py started on "
                                "workstation.".format(git_tag.git_tag()), "demultiplex_started")

        for folder in self.runfolders:  # Pass runfolders to demultiplex.demultiplex_checks()
            if folder not in self.ignore_dirs and os.path.isdir("{}/{}".format(self.runfolder_dir, folder)) \
                    and re.compile(self.runfolder_pattern).match(folder):  # Ensure it matches folder pattern
                # Pre-demultiplex checks and trigger demultiplexing
                self.demultiplex.check_demultiplexing_required(folder)

        # No. runfolders processed by bcl2fastq during this cycle
        self.num_processed_runfolders = len(self.demultiplex.processed_runfolders)

        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py complete. {} runfolder(s) processed."
                                "".format(git_tag.git_tag(), str(self.num_processed_runfolders)),
                                "demultiplex_complete")

        if self.num_processed_runfolders > 0:  # If runfolders processed, rename logfile with runfolder names
            self.rename_demultiplex_logfile()

    def rename_demultiplex_logfile(self):
        """Rename the logfile using demultiplexed runfolder names. Allows easy identification of processed runs
        in logfile name, and differentiates log from others uploaded to DNAnexus
        """
        processed_run_string = "_{}_demultiplex_script_log.txt".format("_".join(self.demultiplex.processed_runfolders))
        new_scriptlog_name = "{}{}".format(os.path.splitext(self.scriptlog)[0], processed_run_string)
        os.rename(self.scriptlog, new_scriptlog_name)


class ReadyToStartDemultiplexing(object):
    """Call bcl2fastq on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present.

    Methods:
        check_demultiplexing_required(runfolder)
            Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing required.
        run_demultiplexing()
            Call demultiplexing functions
        bcl2fastqlog_present()
            Check presence of demultiplex logfile
        validate_samplesheet()
            Check samplesheet is present and naming and contents are valid. Returns error string and boolean
        sequencing_complete()
            Check if sequencing run has completed.
        bcl2fastq_installed()
            Return true if bcl2fastq installed. Raise exception if bcl2fastq is not installed.
        disallowed_ss_errs()
            Check for specific errors that would case bcl2fastq to fail and whose presence should stop demultipelxing
        sequencer_requires_integritycheck()
            Determines whether the run requires integrity checking (not possible on all sequencers).
        checksumfile_present()
            Checks if checksums generated for the run (i.e. integrity checking scripts have completed for the run).
        prior_integritycheck_failed()
            Check if run previously failed integrity check (needs manual intervention before further processing).
        checksums_match()
            Checks whether checksums in the checksum file match
            i.e. the runfolder copied to workstation has not been corrupted by the transfer.
        send_email()
            Send email message
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again.
        create_tso_bcl2fastqlog()
            If runfolder is from TSO500 run, create a bcl2fastq.log file and write to this (TSO500 runs do not
            require demultiplexing)
        run_bcl2fastq()
            Run bcl2fastq with runfolder as input and check success.
        logger(message, flag)
            Write log messages to the system log.
    """

    def __init__(self, scriptlog, runfolder_dir):
        self.log_flags = config.demultiplex_log_flags
        self.sequencers_with_integritycheck = config.sequencers_with_integrity_check
        # Logfiles
        self.scriptlog = scriptlog
        # Directories
        self.runfolder_dir = runfolder_dir  # Workstation runfolder location
        self.ss_dir = config.samplesheets_dir
        # Checksum file
        self.checksumfile = config.md5checksum_name
        self.checksumfile_path = ""
        self.sequencer_checksum = ""
        self.workstation_checksum = ""
        # Bcl2fastq flag file
        self.run_complete = config.file_run_complete  # File denoting end of sequencing run
        self.bcl2fastqlog = config.file_demultiplexing  # File denoting demultiplexing status
        self.bcl2fastqlog_path = ""
        self.bcl2fastq_path = config.bcl2fastq_path  # Path to bcl2fastq
        # Success / failure strings
        self.tso500_bcl2fastq_msg = config.demultiplexing_log_file_TSO500_message
        self.checksumcomp_complete_msg = config.checksumcomp_complete_msg
        self.checksum_match_msg = config.checksum_match_msg
        self.demultiplex_success_match = config.demultiplex_success_match
        # Email server settings
        self.user = config.user
        self.pw = config.pw
        self.host = config.host
        self.port = config.port
        self.smtp_do_tls = config.smtp_do_tls
        # send_email() variables
        self.me = config.me  # Email sender
        self.you = config.you  # Email recipient
        self.email_priority = 1
        self.email_subject = ""
        self.email_message = ""
        # Lists for samplesheet check
        self.sequencerid_list = config.sequencer_ids
        self.panel_list = config.panel_list
        self.runtype_list = config.runtype_list
        self.tso500panel_list = config.tso500_panel_list
        # Runfolder
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.samplesheet_path = ""

        self.processed_runfolders = []

    def check_demultiplexing_required(self, runfolder):
        """ Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing required
        :param runfolder: Runfolder name
        """
        # Capture runfolder and path
        self.runfolder = str(runfolder)
        self.runfolderpath = "{}{}".format(self.runfolder_dir, self.runfolder)
        self.checksumfile_path = os.path.join(self.runfolderpath, self.checksumfile)
        self.bcl2fastqlog_path = os.path.join("{}/{}".format(self.runfolderpath, self.bcl2fastqlog))
        print(self.bcl2fastqlog_path)
        self.samplesheet = "{}_SampleSheet.csv".format(self.runfolder)
        # Write to log file, recording automate_demultiplex repo version
        self.logger("\nAutomate_demultiplexing release: {}\n-----------------{}-----------------\nAssessing......... "
                    "{}".format(git_tag.git_tag(), str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())),
                                self.runfolderpath), self.log_flags['info'])

        if not self.bcl2fastqlog_present():
            self.validate_samplesheet()  # Early warning checks
            if self.sequencing_complete():
                if self.bcl2fastq_installed() and not self.disallowed_ss_errs():
                    if not self.sequencer_requiring_integritycheck():
                        self.run_demultiplexing()
                    if self.checksumfile_present():
                        if not self.prior_integritycheck_failed():
                            if self.checksums_match():
                                self.run_demultiplexing()
                            else:  # Send email denoting checksums check has failed
                                self.email_subject = "MOKA ALERT: INTEGRITY CHECK FAILED"
                                self.email_message = "run:\t{}\nPlease follow the protocol " \
                                                     "for when integrity checks fail".format(self.runfolder)
                                self.send_email()
                                self.logger("Integrity check fail. checksums do not match for ""{} see "
                                            "{}".format(self.runfolder, self.checksumfile_path), self.log_flags['fail'])

    def run_demultiplexing(self):
        """Call demultiplexing functions
        TSO runs don't require demultiplexing. Create bcl2fastq log so scripts skip over these runs in future.
        """
        # Prevent simultaneous demultiplex attempt on next run of script (bcl2fastq is slow to create logfile)
        self.create_bcl2fastqlog()
        ss = SamplesheetCheck(self.samplesheet_path, self.sequencerid_list, self.panel_list,
                              self.runtype_list, self.tso500panel_list)
        if ss.tso:
            self.create_tso_bcl2fastqlog()
        else:
            self.run_bcl2fastq()
        # Add runfolder name to processed runfolder list. Used to name script log file when all processing complete
        self.processed_runfolders.append(self.runfolder)

    def bcl2fastqlog_present(self):
        """Check presence of demultiplex logfile
        ("bcl2fastq2_output.log", or "demultiplexlog.txt" for backwards compatability)
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            self.logger("Demultiplexing has already been completed - demultiplex log found @ {}/{} "
                        "\n--- STOP ---".format(self.runfolderpath, self.bcl2fastqlog), self.log_flags['info'])
            return True
        else:
            self.logger("Demultiplexing not yet completed - no demultiplex log found @ {}/{} "
                        "\n--- CONTINUE ---".format(self.runfolderpath, self.bcl2fastqlog), self.log_flags['info'])

    def validate_samplesheet(self):
        """ Check samplesheet is present and naming and contents are valid. Returns error string and boolean.
        """
        ss = SamplesheetCheck(self.samplesheet_path, self.sequencerid_list, self.panel_list,
                              self.runtype_list, self.tso500panel_list)
        err_str = ", ".join([item for sublist in ss.errors.values() for item in sublist])
        if err_str:
            self.logger("Samplesheet checks failed {}: "
                        "{}".format(self.samplesheet, err_str), self.log_flags['ss_warning'])
            success = False
        else:
            self.logger("Samplesheet passed all checks {}".format(self.samplesheet), self.log_flags['success'])
            success = True
        return ss.errors, success

    def sequencing_complete(self):
        """Check if sequencing has completed for the current runfolder - presence of "RTAComplete.txt".
        """
        if os.path.isfile("{}/{}".format(self.runfolderpath, self.run_complete)):   # Is RTAcomplete.txt present
            self.logger("Run finished  -  RTAcomplete.txt found @ "
                        "{}/{}\n".format(self.runfolderpath, self.run_complete), self.log_flags['info'])
            return True
        else:
            self.logger("Run not yet complete \n--- STOP ---\n", self.log_flags['info'])

    def bcl2fastq_installed(self):
        """Call path to bcl2fastq2 using subprocess, capture streams, raise exception if bcl2fastq not installed.
        """
        proc = subprocess.Popen([self.bcl2fastq_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        out, err = proc.communicate()  # Capture streams

        # If bcl2fastq installed and called with no inputs:
        # First line of stderr should contain the string: "BCL to FASTQ file converter"
        if "BCL to FASTQ file converter" not in err:
            self.logger("BCL2FastQ installation test failed.", self.log_flags['fail'])
            raise Exception("bcl2fastq not installed")
        else:
            self.logger("BCL2FastQ installation test passed.", self.log_flags['success'])
            return True

    def disallowed_ss_errs(self):
        """ Check for specific errors that would case bcl2fastq to fail and whose presence should stop demultipelxing
        """
        disallowed_errs = ["sspresent_err", "ssname_err", "ssempty_err", "headers_err", "validchars_err"]
        errors, success = self.validate_samplesheet()
        if success:
            return True
        else:
            if any(errors[key] for key in disallowed_errs):
                err_str = ", ".join([item for sublist in errors.values() for item in sublist])
                self.logger("Demultiplexing halted due to samplesheet errors {}: "
                            "{}".format(self.samplesheet, err_str), self.log_flags['fail'])

    def sequencer_requires_integritycheck(self):
        """Check whether checksum check needed. Only runs from sequencers that can have checksums generated require
        this - not all sequencers can have checksums generated by the integrity check script.
        """
        if any(item in self.runfolder for item in self.sequencers_with_integritycheck):
            return True
        else:
            self.logger("Data integrity check not required. Continuing...", self.log_flags['info'])

    def checksumfile_present(self):
        """Determines whether checksum file is present
        """
        if os.path.isfile(self.checksumfile_path):  # checksums have been written to file by integrity check scripts
            self.logger("Checksums file present", self.log_flags['info'])
            return True

        else:  # integrity check not been performed
            self.logger("Integrity check not yet performed on sequencer. Stopping...", self.log_flags['info'])

    def prior_integritycheck_failed(self):
        """Check if runfolder has failed a previous integrity check by this script
        Denoted by presence of self.checksum_complete_flag string in checksum file (flag added when
        self.checksums_match() called and self.checksum_match_msg is absent in the first line of the file - prevents
        checksums_match performing further integrity checks
        """
        with open(self.checksumfile_path, 'r') as checksumfile:
            checksums = checksumfile.readlines()  # read checksum file into list

        if self.checksum_complete_flag in checksums[-1]:  # (last line in file, last element in list)
            self.logger("Previously reported failed integrity check", self.log_flags['info'])
            return True

    def checksums_match(self):
        """Checks whether checksums in the checksum file match - i.e. the runfolder copied to workstation has not been
        corrupted by the transfer.
        Checksum generation and initial integrity checks are carried out by the sequencer_checksum.py script running on
        the sequencer, and written to a checksum file for access by this script. Checksum generation and integrity
        check is not possible on all sequencers (i.e. miseq).

        Checksum file should contain:
            Pass/fail statement in Line 1, checksums for both copies of run folder on lines 2 and 3
            Function adds line to file to denote integrity check has been assessed - stops repetition if check fails
        """
        self.logger("Data integrity checks starting...", self.log_flags['info'])

        with open(self.checksumfile_path, 'r') as checksumfile:  # Open file containing md5 checksums
            checksums = checksumfile.readlines()  # Read checksums into list

        # Add a flag into the checksum file to prevent script performing future checksum checks
        with open(self.checksumfile_path, 'a') as checksumfile:
            checksumfile.write("\n{}".format(self.checksumcomp_complete_msg))

        if self.checksum_match_msg in checksums[0]:  # Line 1 contains pass/fail statement from integrity check script
            self.logger("Integrity check of runfolder {} passed".format(self.runfolder), self.log_flags['success'])
            return True  # checksums match

    def send_email(self):
        """Send email to recipient (self.you) via SMTP
        """
        self.logger("Sending an email. Recipient: {}. Subject: {}. "
                    "Body:\n{}".format(self.me, self.email_subject, self.email_message), self.log_flags['info'])

        m = Message()  # Create email.Message() object
        m['X-Priority'] = str(self.email_priority)  # X-Priority = 1. Sets a high-priority e-mail.
        m['Subject'] = self.email_subject

        try:
            # Add error messages to e-mail body using email.Message.set_payload()
            m.set_payload(self.email_message)
            # Configure SMTP server connection for sending log messages via e-mail
            server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
            server.set_debuglevel(1)  # Output connection debug messages
            server.starttls()  # Encrypt SMTP commands using Transport Layer Security mode$
            server.ehlo()  # Identify client to ESMTP server using EHLO commands
            server.login(self.user, self.pw)  # Login to server with user credentials
            server.sendmail(self.me, [self.you], m.as_string())  # Send email to server
            self.logger("Email sent without error", self.log_flags['info'])
            return True
        except Exception as e:
            self.logger("Error when sending email. Email not sent. Exception: {}".format(e), self.log_flags['fail'])

    def create_bcl2fastqlog(self):
        """Create file to prevent demultiplexing starting again.
        bl2fastq2 v2.20 doesn't produce stdout for a while after starting so create file here and append stdout later
        """
        try:
            open(self.bcl2fastqlog_path, 'w').close()
        except Exception as e:
            self.logger("Failed to create demultiplex logfile for run {}: {}".format(self.runfolder, e),
                        "demultiplex_warning")
            return False

    def create_tso_bcl2fastqlog(self):
        """If runfolder is from TSO500 run, create a bcl2fastq.log file and write to this (TSO500 runs do not
        require demultiplexing)
        """
        self.logger("{} is a {}".format(self.runfolder, self.tso500_bcl2fastq_msg), self.log_flags['success'])
        try:
            with open(self.bcl2fastqlog_path, 'w+') as log:
                log.write("\n{}".format(self.tso500_bcl2fastq_msg))
                self.logger("bcl2fastq.log file created for TSO run: {}".format(self.runfolder), self.log_flags['info'])
        except Exception as e:
            self.logger("Failed to create bcl2fastq.log file for TSO run: {}, {}".format(self.runfolder, e),
                        self.log_flags['fail'])

    def run_bcl2fastq(self):
        """Runs bcl2fastq and checks if completed successfully.
        Create and run bcl2fastq shell command to run demultiplexing using runfolder as input
        Append bcl2fastq stdout and stderr to the bcl2fastqlog file. Read bcl2fastqlog file and search last
        x lines for expected success statement.

        Example: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
                        -R 160822_NB551068_0006_AHGYM7BGXY/
                        --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
                        --no-lane-splitting >>
                        /media/data1/share/1111_M02353_NMNOV17_ONCTEST/bcl2fastq2_output.log 2&>1"
        (N.B. n--no-lane-splitting creates a single fastq for a sample, not into one fastq per lane)
        """
        cmd = "{} -R {}/{} --sample-sheet {} --no-lane-splitting >> {} 2>&1" \
              "".format(self.bcl2fastq_path, self.runfolder_dir, self.runfolder,
                        self.samplesheet_path, self.bcl2fastqlog_path)

        self.logger("Demultiplexing started for run {} using bcl2fastq command: "
                    "{}".format(self.runfolder, cmd), self.log_flags['info'])

        subprocess.call([cmd], shell=True)  # Wait until subprocess completes

        # Read last 10 lines of demultiplex logfile - details success or failure of bcl2fastq command
        bcl2fastq_log_tail = subprocess.check_output(["tail", "-n", "10", self.bcl2fastqlog_path])

        # Search for success statement defined in config file
        if re.search(self.demultiplex_success_match, bcl2fastq_log_tail):
            self.logger("Demultiplexing complete without error for run {}".format(self.runfolder),
                        self.log_flags['success'])

        else:  # No success statement (demultiplex errors) - report last few lines of runfolder demultiplex log
            self.logger("ERROR - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ ERROR) - Demultiplexing failed for run {}. "
                        "Please see {}\n{}".format(self.runfolder, self.bcl2fastqlog_path, bcl2fastq_log_tail),
                        self.log_flags['fail'])

    def logger(self, message, flag):
        """Write log messages to syslog.
        Arguments:
        message (str)
            Details about the logged event.
        flag (str)
            Tool name. Used to search within the insight ops website.
        """
        # Create subprocess command string, passing message and flag name to the command
        log = "/usr/bin/logger -t {} '{}'".format(flag, message)
        with open(self.scriptlog, 'a') as logfile:
            if subprocess.call([log], shell=True) == 0:
                # If the log command produced no errors, record the log command string to the script logfile.
                logfile.write("Log written - {}: {}\n".format(flag, message))
                return True
            else:
                logfile.write("Failed to write log to /usr/bin/logger\n{}\n".format(log))


if __name__ == '__main__':
    GetListOfRuns().loop_through_runs()
