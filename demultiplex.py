# coding=utf-8
"""
Demultiplex NGS Run Folders

Runs bcl2fastq on newly completed NGS run folders in a specific directory. Sequencing is deemed complete by the
presence of a file ("RTAComplete.txt"), created by the sequencer when sequencing is complete.

Carries out checks on the corresponding samplesheet in the samplesheets folder (should have name "RUN_samplesheet.csv",
where "RUN" is the name of the run folder, and conform to naming convention specified in the seglh-naming library,
contains expected data section headers, and contains allowed panel numbers and runtypes specified in the config file

Before demultiplexing, the script checks for the absence of the log file "bcl2fastq2_output.log" in the run folder.
bcl2fastq stdout and stderr streams are written to this file, which when present indicates that
demultiplexing is in process or has already been performed.
"""

import os
import subprocess
import datetime
import smtplib
from email.message import Message
import re
import automate_demultiplex_config as config  # import config file
import git_tag as git_tag  # import function which reads the git tag
from samplesheet_validator import SamplesheetCheck


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
        """self.runfolders points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.runfolders = config.runfolders
        self.now = str('{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now()))  # Set time stamp to append to logfile name
        # Set script log file path and name for this hour's cron job (script log file).
        self.script_logfile_path = config.demultiplex_logfiles
        self.logfile_name = "{}{}.txt".format(self.script_logfile_path, self.now)
        self.script_logfile = open(self.logfile_name, 'a')  # Open script logfile for logging
        # Create class instance for checking and running demultiplexing per runfolder
        self.demultiplex = ReadyToStartDemultiplexing(self.now, self.script_logfile)
        self.runfolder_pattern = config.runfolder_pattern
        self.ignore_directories = config.ignore_directories
        self.demultiplex_test_runfolders = config.demultiplex_test_folder
        self.testing = config.testing

    def loop_through_runs(self):
        """Pass NGS run folders to an instance of ReadyToStartDemultiplexing() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file.
        """
        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py started on "
                                "workstation.".format(git_tag.git_tag()), "demultiplex_started")

        if self.testing:  # List files and folders in runfolder directory
            runfolders = self.demultiplex_test_runfolders
        else:
            runfolders = os.listdir(self.runfolders)

        for folder in runfolders:  # Pass runfolders to demultiplex.demultiplex_checks()
            if folder not in self.ignore_directories and os.path.isdir("{}/{}".format(self.runfolders, folder)) \
                    and re.compile(self.runfolder_pattern).match(folder):  # ensure it matches folder pattern
                self.demultiplex.demultiplex_checks(folder)  # Pre-demultiplex checks and triggers demultiplexing

        # No. runfolders processed by bcl2fastq during this cycle
        num_processed_runfolders = len(self.demultiplex.processed_runfolders)

        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py complete. {} runfolder(s) processed."
                                "".format(git_tag.git_tag(), str(num_processed_runfolders)), "demultiplex_complete")

        if num_processed_runfolders > 0:  # If runfolders processed, rename logfile with runfolder names
            self.rename_demultiplex_logfile()
        self.script_logfile.close()  # Close script log file when all processing complete

    def rename_demultiplex_logfile(self):
        """Rename the logfile using runfolder names. Allows easy identification of processed runs in logfile name, and
        differentiates log from others uplaoded to DNAnexus

        Create string of all runfolders demultiplexed in the cycle, ending with '_demultiplex_script_log.txt'
        Take current script logfile name, remove .txt and append processed_run_string
        Rename log file with this new name
        """
        processed_run_string = "_{}_demultiplex_script_log.txt".format("_".join(self.demultiplex.processed_runfolders))
        new_scriptlog_name = "{}{}".format(os.path.splitext(self.logfile_name)[0], processed_run_string)
        os.rename(self.logfile_name, new_scriptlog_name)


class ReadyToStartDemultiplexing(object):
    """Call bcl2fastq on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present.

    Arguments:
        now
            Timestamp for log file name, assigned to self.now (str).

    Methods:
        setup_demultiplexing(runfolder)
            Carries out per-runfolder pre-demultiplexing tasks.
        bcl2fastq_log()
            Check presence of demultiplex logfile
        valid_samplesheet()
            Check samplesheet is present and naming and contents are valid. Returns error string and boolean
        has_run_finished()
            Check if sequencing run has completed.
        disallowed_ss_errs()
            Check for specific errors that would case bcl2fastq to fail and whose presence should stop demultipelxing
        bcl2fastq_installed()
            Return true if bcl2fastq installed. Raise exception if bcl2fastq is not installed.
        sequencer_requiring_integritycheck()
            Determines whether the run requires integrity checking (not possible on all sequencers).
        checksum_file_present()
            Checks if checksums generated for the run (i.e. integrity checking scripts have completed for the run).
        prior_integritycheck_failed()
            Check if run previously failed integrity check (needs manual intervention before further processing).
        checksums_match()
            Checks whether checksums match in checksum file.
        send_email()
            Send progress messages via email.
        tso500_run()
            Determine whether runfolder is from a TSO500 run.
        run_bcl2fastq()
            Run bcl2fastq with runfolder as input and check success.
        logger(message, tool)
            Write log messages to the system log.
    """

    def __init__(self, now, script_logfile):
        self.script_logfile = script_logfile
        # self.runfolders points to workstation runfolders location. Value must be same as in GetListOfRuns()
        self.runfolders = config.runfolders
        self.now = now  # Assign timestamp from GetListOfRuns() to self.variable

        self.run_complete = config.file_complete_run  # File denoting end of sequencing run
        self.demultiplexed = config.file_demultiplexing  # File denoting demultiplexing status
        self.demultiplexed_oldname = config.file_demultiplexing_old  # Old name for demultiplexing logfile
        self.bcl2fastq = config.bcl2fastq  # Path to bcl2fastq
        self.checksum_file = config.md5checksum_name
        self.tso500_bcl2fastq_msg = config.demultiplexing_log_file_TSO500_message
        self.ss_dir = config.samplesheets_dir
        self.sequencers_with_integritycheck = config.sequencers_with_integrity_check
        self.checksum_complete_flag = config.checksum_complete_flag
        self.checksum_match = config.checksum_match
        self.demultiplex_success_match = config.demultiplex_success_match

        # Email server settings
        self.user = config.user
        self.pw = config.pw
        self.host = config.host
        self.port = config.port
        self.smtp_do_tls = config.smtp_do_tls

        # send_email() variables
        self.email_subject = ""
        self.email_priority = 1
        self.email_message = ""
        self.me = config.me  # email sender
        self.you = config.you  # email recipient

        # Empty variables to be defined based on the run
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.samplesheet_path = ""
        self.processed_runfolders = []
        self.demultiplex_log = ""
        self.checksum_file_path = ""
        self.sequencer_checksum = ""
        self.workstation_checksum = ""


    def setup_demultiplexing(self, runfolder):
        """ Carries out per-runfolder pre-demultiplexing tasks.

         Check bcl2fastq installed, run integrity check if required, carry out samplesheet check, check if run is tso500,
        run bcl2fastq, check logfile to determine whether demultiplexing successful, mark runfolder as processed


        :param runfolder: Runfolder name
        """
        # Capture runfolder and path
        self.runfolder = str(runfolder)
        self.runfolderpath = "{}{}".format(self.runfolders, self.runfolder)
        self.checksum_file_path = os.path.join(self.runfolderpath, self.checksum_file)
        self.demultiplex_log = "{}/{}/{}".format(self.runfolders, self.runfolder, self.demultiplexed)

        # Write to log file, recording automate_demultiplex repo version
        self.logger("\nAutomate_demultiplexing release: {}\n-----------------{}-----------------\nAssessing......... "
                    "{}".format(git_tag.git_tag(), str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())),
                                self.runfolderpath), "demultiplex_info")

        if not self.bcl2fastq_log(): # If bcl2fastq logfile not present, perform samplesheet checks
            return True
        else:
            self.logger("Run has not yet been demultiplexed", "demultiplex_info")
            self.samplesheet = "{}_SampleSheet.csv".format(self.runfolder)
            self.samplesheet_path = os.path.join(self.ss_dir, self.samplesheet)
            self.valid_samplesheet()  # Does not stop the scripts at this point if there is an error
            # If sequencing complete,and no disallowed samplesheet errors, setup demultiplexing
            if self.has_run_finished():
                # If bcl2fastq installed and no disallowed samplesheet errors
                if self.bcl2fastq_installed() and not self.disallowed_ss_errs():
                    if self.sequencer_requiring_integritycheck() and self.checksum_file_present():
                        if not self.prior_integritycheck_failed():
                            # If checksums don't match, send failure email and stop processing
                            if not self.checksums_match():
                                self.send_icfail_email()
                            else:

                                # Create file to prevent demultiplexing starting again.  cl2fastq2 v2.20 doesn't
                                # produce stdout for a while after starting so create file here and append stdout later
                                open(self.demultiplex_log, 'w').close()  # Close file immediately

                                # TSO500 runs dont require demultiplexing (create bcl2fastqlog)
                                if SamplesheetCheck(self.samplesheet_path).tso:
                                    self.create_tso_bcl2fastqlog()
                                else:  # Run demultiplexing
                                    self.run_bcl2fastq()

                                # Add runfolder name to self.processed_runfolders. Runfolder names in this list are appended
                                # To the script log file at the end of the script cycle.
                                self.processed_runfolders.append(self.runfolder)

    def bcl2fastq_log(self):
        """Check presence of demultiplex logfile
        ("bcl2fastq2_output.log", or "demultiplexlog.txt" for backwards compatability)
        """
        log = os.path.isfile(os.path.join("{}/{}".format(self.runfolderpath, self.demultiplexed)))
        txt = os.path.isfile(os.path.join(self.runfolderpath, self.demultiplexed_oldname))

        if log:
            self.logger("Demultiplexing has already been completed - demultiplex log found @ {}/{} "
                        "\n--- STOP ---".format(self.runfolderpath, self.demultiplexed), "demultiplex_info")
            return True
        elif txt:
            self.logger("Demultiplexing has already been completed - demultiplex log found @ {}/{} "
                        "\n--- STOP ---".format(self.runfolderpath, self.demultiplexed_oldname), "demultiplex_info")
            return True
        else:
            self.logger("Demultiplexing not yet completed - no demultiplex log found @ {}/{} "
                        "\n--- CONTINUE ---".format(self.runfolderpath, self.demultiplexed_oldname), "demultiplex_info")

    def valid_samplesheet(self):
        """ Check samplesheet is present and naming and contents are valid. Returns error string and boolean.
        """
        ss = SamplesheetCheck(self.samplesheet_path)
        err_str = ", ".join([item for sublist in ss.errors.values() for item in sublist])
        if err_str:
            self.logger("Samplesheet checks failed {}: "
                        "{}".format(self.samplesheet, err_str), "samplesheet_warning")
            success = False
        else:
            self.logger("Samplesheet passed all checks {}".format(self.samplesheet), "demultiplex_success")
            success = True
        return ss.errors, success

    def has_run_finished(self):
        """Check if sequencing has completed for the current runfolder - presence of "RTAComplete.txt".
        """
        if os.path.isfile("{}/{}".format(self.runfolderpath, self.run_complete)):  # Is RTAcomplete.txt present
            self.logger("Run finished  -  RTAcomplete.txt found @ "
                        "{}/{}\n".format(self.runfolderpath, self.run_complete), "demultiplex_info")
            return True
        else:
            self.logger("Run not yet complete \n--- STOP ---\n", "demultiplex_info")

    def disallowed_ss_errs(self):
        """ Check for specific errors that would case bcl2fastq to fail and whose presence should stop demultipelxing
        """
        disallowed_errs = ["sspresent_err", "ssempty_err", "headers_err", "validchars_err"]
        errors, success = self.valid_samplesheet()
        if not success:
            if any(errors[key] for key in disallowed_errs):
                err_str = ", ".join([item for sublist in errors.values() for item in sublist])
                self.logger("Demultiplexing halted due to samplesheet errors {}: "
                            "{}".format(self.samplesheet, err_str), "demultiplex_fail_samplesheet")
        else:
            return True

    def create_tso_bcl2fastqlog(self):
        """If runfolder is from TSO500 run, create a bcl2fastq.log file and write to this (TSO500 runs do not
        require demultiplexing)
        """
        self.logger("{} is a {}".format(self.runfolder, self.tso500_bcl2fastq_msg),
                    "demultiplex_success")
        with open(self.demultiplex_log, 'w') as bcl2fastq2_log:
            bcl2fastq2_log.write("\n{}".format(self.tso500_bcl2fastq_msg))
            self.logger("Bcl2fastq.log file created for TSO run: {}".format(self.runfolder), "demultiplex_info")

    def bcl2fastq_installed(self):
        """Call path to bcl2fastq2 using subprocess, capture streams, raise exception if bcl2fastq not installed.
        """
        proc = subprocess.Popen([self.bcl2fastq], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        out, err = proc.communicate()  # Capture streams

        # If bcl2fastq installed and called with no inputs:
        # First line of stderr should contain the string: "BCL to FASTQ file converter"
        if "BCL to FASTQ file converter" not in err:
            self.logger("BCL2FastQ installation test failed.", "demultiplex_fail")
            raise Exception("bcl2fastq not installed")
        else:
            self.logger("BCL2FastQ installation test passed.", "demultiplex_success")
            return True

    def send_icfail_email(self):
        """Calls functions (pre-checks) to determine whether checksums can be checked for the run (integrity checking)

        Ensures runfolder copied to workstation hasn't been corrupted by the transfer.
        Checksum generation and initial integrity checks are carried out by the sequencer_checksum.py script running
        on the sequencer, and written to a checksum file for access by this script.

        NB. this integrity check is not possible on all sequencers (ie miseq).
        """
        self.email_subject = "MOKA ALERT: INTEGRITY CHECK FAILED"
        self.email_priority = 1
        self.email_message = "run:\t{}\nPlease follow the protocol "\
                             "for when integrity checks fail".format(self.runfolder)
        self.send_email()
        self.logger("Integrity check fail. checksums do not match for ""{} see "
                    "{}".format(self.runfolder, self.checksum_file_path), "demultiplex_fail")

    def sequencer_requiring_integritycheck(self):
        """Check whether checksum check needed. Only runs from sequencers that can have checksums generated require
        this - not all sequencers can have checksums generated by the integrity check script.
        """
        if any(item in self.runfolder for item in self.sequencers_with_integritycheck):
            return True
        else:
            self.logger("Data integrity check not required. Continuing...", "demultiplex_info")

    def checksum_file_present(self):
        """Determines whether checksum file is present
        """
        if os.path.isfile(self.checksum_file_path):  # checksums have been written to file by integrity check scripts
            self.logger("Checksums file present", "demultiplex_info")
            return True

        else:  # integrity check not been performed
            self.logger("Integrity check not yet performed on sequencer. Stopping...", "demultiplex_info")

    def prior_integritycheck_failed(self):
        """Check if runfolder has failed a previous integrity check by this script
        Denoted by presence of self.checksum_complete_flag string in checksum file
        This flag prevents checksums_match from performing further integrity checks
        (This string is added when self.checksums_match() is called and self.checksum_match
        is not present in the first line of the file)
        """
        with open(self.checksum_file_path, 'r') as checksum_file:
            checksums = checksum_file.readlines()  # read checksum file into list

        if self.checksum_complete_flag in checksums[-1]:  # (last line in file, last element in list)
            self.logger("Previously reported failed integrity check", "demultiplex_info")
            return True

    def checksums_match(self):
        """Checks whether checksums match in checksum file.
        File should contain: Pass/fail statement in Line 1, checksums for both copies of run folder on lines 2 and 3
        Function adds line to file to denote integrity check has been assessed - stops repetition if check fails
        """
        self.logger("Data integrity checks starting...", "demultiplex_info")

        with open(self.checksum_file_path, 'r') as checksum_file:  # Open file containing md5 checksums
            checksums = checksum_file.readlines()  # Read checksums into list

        # Add a flag into the checksum file to prevent script performing future checksum checks
        with open(self.checksum_file_path, 'a') as checksum_file:
            checksum_file.write("\n{}".format(self.checksum_complete_flag))

        if self.checksum_match in checksums[0]:  # Line 1 contains pass/fail statement from integrity check script
            self.logger("Integrity check of runfolder {} passed".format(self.runfolder), "demultiplex_success")
            return True  # checksums match

    def send_email(self):
        """Send progress log messages via email to recipient (self.you) via SMTP.
        """
        self.logfile("Sending an email. Recipient: {}. Subject: {}. "
                     "Body:\n{}".format(self.me, self.email_subject, self.email_message), "demultiplex_info")

        m = Message()  # Create email.Message() object
        m['X-Priority'] = str(self.email_priority)  # X-Priority = 1. Sets a high-priority e-mail.
        m['Subject'] = self.email_subject
        # Add error messages to e-mail body using email.Message.set_payload()
        m.set_payload(self.email_message)
        try:
            # Configure SMTP server connection for sending log messages via e-mail
            server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
            server.set_debuglevel(1)  # Output connection debug messages
            server.starttls()  # Encrypt SMTP commands using Transport Layer Security mode$
            server.ehlo()  # Identify client to ESMTP server using EHLO commands
            server.login("abc", self.pw)  # Login to server with user credentials
            server.sendmail(self.me, [self.you], m.as_string())  # Send email to server
            self.logger("Email sent without error", "demultiplex_info")
            return True
        except Exception:
            self.logger("Error when sending email. Email not sent.", "demultiplex_fail")

    def run_bcl2fastq(self):
        """Runs bcl2fastq and checks if completed successfully.
        Create and run bcl2fastq shell command to run demultiplexing using runfolder as input
        Append bcl2fastq stdout and stderr to the demultiplex_log file. Read demultiplex_log file and search last
        x lines for expected success statement.

        Example: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
                        -R 160822_NB551068_0006_AHGYM7BGXY/
                        --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
                        --no-lane-splitting >>
                        /media/data1/share/1111_M02353_NMNOV17_ONCTEST/bcl2fastq2_output.log 2&>1"
        (N.B. n--no-lane-splitting creates a single fastq for a sample, not into one fastq per lane)
        """
        cmd = "{} -R {}/{} --sample-sheet {} --no-lane-splitting >> {} 2>&1" \
              "".format(self.bcl2fastq, self.runfolders, self.runfolder, self.samplesheet_path, self.demultiplex_log)

        self.logger("Demultiplexing started for run {} using bcl2fastq command: "
                    "{}".format(self.runfolder, cmd), "demultiplex_info")

        subprocess.call([cmd], shell=True) # Wait until subprocess completes

        # Read last 10 lines of demultiplex logfile - details success or failure of bcl2fastq command
        bcl2fastq_log_tail = subprocess.check_output(["tail", "-n", "10", self.demultiplex_log])

        # Search for success statement defined in config file
        if re.search(self.demultiplex_success_match, bcl2fastq_log_tail):
            self.logger("Demultiplexing complete without error for run {}".format(self.runfolder),
                        "demultiplex_success")

        else:  # No success statement (demultiplex errors) - report last few lines of runfolder demultiplex log
            self.logger("ERROR - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ ERROR) - Demultiplexing failed for run {}. "
                        "Please see {}\n{}".format(self.runfolder, self.demultiplex_log, bcl2fastq_log_tail),
                        "demultiplex_fail")

    def logger(self, message, tool):
        """Write log messages to syslog.
        Arguments:
        message (str)
            Details about the logged event.
        tool (str)
            Tool name. Used to search within the insight ops website.
        """
        # Create subprocess command string, passing message and tool name to the command
        log = "/usr/bin/logger -t {} '{}'".format(tool, message)

        if subprocess.call([log], shell=True) == 0:
            # If the log command produced no errors, record the log command string to the script logfile.
            self.script_logfile.write("Log written - {}: {}\n".format(tool, message))
        else:
            self.script_logfile.write("Failed to write log to /usr/bin/logger\n{}\n".format(log))


if __name__ == '__main__':
    GetListOfRuns().loop_through_runs()