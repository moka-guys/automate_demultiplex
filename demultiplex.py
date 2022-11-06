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
import requests
import automate_demultiplex_config as config # import config file
import git_tag as git_tag # import function which reads the git tag
from samplesheet_verifier import ValidSamplesheet


class GetListOfRuns(object):
    """
    Loop through and process NGS runfolders in a given directory.
    Single class instance required to demultiplex all NGS runfolders. E.g.:
        >>> runs = GetListOfRuns()
        >>> runs.loop_through_runs()

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
        self.now = str('{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())) # Set time stamp to append to logfile name
        # Set script log file path and name for this hour's cron job (script log file).
        self.script_logfile_path = config.demultiplex_logfiles
        self.logfile_name = "{}{}.txt".format(self.script_logfile_path, self.now)
        self.script_logfile = open(self.logfile_name, 'a') # Open script logfile for logging
        # Create class instance for checking and running demultiplexing per runfolder
        self.demultiplex = ReadyToStartDemultiplexing(self.now, self.script_logfile)


    def loop_through_runs(self):
        """Pass NGS run folders to an instance of ReadyToStartDemultiplexing() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file.
        """
        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py started on "
                                "workstation.".format(git_tag.git_tag()), "demultiplex_started")

        if config.testing: # List files and folders in runfolder directory
            runfolders = config.demultiplex_test_folder
        else:
            runfolders = os.listdir(self.runfolders)

        # Pass runfolders to demultiplex.is_run_demultiplexed()
        for folder in runfolders:
            if folder not in config.ignore_directories and os.path.isdir("{}/{}".format(self.runfolders, folder)) \
                    and re.compile(config.runfolder_pattern).match(folder): # ensure it matches folder pattern
                self.demultiplex.is_run_demultiplexed(folder) # Pre-demultiplex checks and triggers demultiplexing

        # No. runfolders processed by bcl2fastq during this cycle
        num_processed_runfolders = len(self.demultiplex.processed_runfolders)

        self.demultiplex.logger("Automate demultiplex release {}: Demultiplex.py complete. {} runfolder(s) processed."
                                "".format(git_tag.git_tag(), str(num_processed_runfolders)), "demultiplex_complete")

        # If runfolders processed, rename logfile with runfolder names
        if num_processed_runfolders > 0:
            self.rename_demultiplex_logfile()
        self.script_logfile.close() # Close script log file when all processing complete


    def rename_demultiplex_logfile(self):
        """Rename the logfile using runfolder names. Allows easy identification of processed runs in logfile name, and
        differentiates log from others uplaoded to DNAnexus

        Create string of all runfolders demultiplexed in the cycle, ending with '_demultiplex_script_log.txt'
        Take current script logfile name, remove .txt and append processed_run_string
        Rename log file with this new name
        """
        processed_run_string = "_{}_demultiplex_script_log.txt".format("_".join(demultiplex.processed_runfolders))
        new_scriptlog_name = "{}{}".format(os.path.splitext(self.logfile_name)[0], processed_run_string)
        os.rename(self.logfile_name, new_scriptlog_name)


class ReadyToStartDemultiplexing(object):
    """Call bcl2fastq on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present.

    Arguments:
        now
            Timestamp for log file name, assigned to self.now (str).

    Methods:
        is_run_demultiplexed(runfolder)
            Check if the runfolder has been demultiplexed.
        check_bcl2fastq_log():
            Check presence of demultiplex logfile
        valid_samplesheet():
            Check samplesheet is present and naming and contents are valid. Returns boolean
        has_run_finished()
            Check if sequencing run has completed.
        setup_demultiplexing()
            Carries out pre-demultiplexing tasks.
        test_bcl2fastq()
            Raise exception if bcl2fastq is not installed.
        setup_integrity_check()
            Carries out pre-checks of to determine whether checksums can be checked for the run (integrity checking).
        sequencer_requiring_integritycheck()
            Determines whether the run requires integrity checking (not possible on all sequencers).
        checksum_file_present()
            checks if checksums generated for the run (i.e. integrity checking scripts have completed for the run).
        prior_integritycheck_failed()
            check if run previously failed integrity check (needs manual intervention before further processing).
        checksums_match()
            Checks whether checksums match in checksum file.
        send_email()
            Send progress messages via email.
        run_bcl2fastq()
            Run bcl2fastq with runfolder as input.
        check_demultiplex_logfile()
            Check demultiplexing completed succesfully.
        logger(message, tool)
            Write log messages to the system log.
    """

    def __init__(self, now, script_logfile):
        self.script_logfile = script_logfile
        # self.runfolders points to workstation runfolders location. Value must be same as in GetListOfRuns()
        self.runfolders = config.runfolders
        self.now = now # Assign timestamp from GetListOfRuns() to self.variable

        self.run_complete = config.file_complete_run # File denoting end of sequencing run
        self.demultiplexed = config.file_demultiplexing # File denoting demultiplexing status
        self.bcl2fastq = config.bcl2fastq  # Path to bcl2fastq
        self.checksum_file = config.md5checksum_name

        # Empty variables to be defined based on the run
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.samplesheet_path = ""
        self.processed_runfolders = []
        self.demultiplex_log = ""
        self.checksum_file_path = ""

        # Email server settings
        self.user = config.user
        self.pw = config.pw
        self.host = config.host
        self.port = config.port
        self.smtp_do_tls = config.smtp_do_tls

        self.me = config.me # email sender
        self.you = config.you # email recipient

        # variables used by send_email()
        self.email_subject = ""
        self.email_priority = 1
        self.email_message = ""

        # variables to hold checksums:
        self.sequencer_checksum = ""
        self.workstation_checksum = ""


    def is_run_demultiplexed(self, runfolder):
        """Check if runfolder has been demultiplexed (check for presence of bcl2fastq logfile)
        If demultiplexed, returns True. Else:
            Call samplesheet checking script
            Call has_run_finished()
        :param runfolder: Runfolder name
        """
        # Capture the runfolder and its path
        self.runfolder = str(runfolder)
        self.runfolderpath = "{}{}".format(self.runfolders, self.runfolder)

        # Write to log file, recording the version of the automate_demultiplex repository
        self.logger("\nAutomate_demultiplexing release: {}\n-----------------{}-----------------\nAssessing......... "
                    "{}".format(git_tag.git_tag(), str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())),
                                self.runfolderpath), "demultiplex_info")

        # If bcl2fastq logfile not present, perform samplesheet checks
        if self.check_bcl2fastq_log:
            return True
        else:
            self.logger("Run has not yet been demultiplexed", "demultiplex_info")
            self.samplesheet = "{}_SampleSheet.csv".format(self.runfolder)
            self.samplesheet_path = os.path.join(config.samplesheets_dir, self.samplesheet)
            self.valid_samplesheet() # does not stop the scripts at this point if there is an error
            self.has_run_finished()


    def check_bcl2fastq_log(self):
        """Check presence of demultiplex logfile
        ("bcl2fastq2_output.log", or "demultiplexlog.txt" for backwards compatability)
        """
        bcl2fastq_log = os.path.isfile(os.path.join("{}/{}".format(self.runfolderpath,self.demultiplexed)))
        bcl2fastq_txt = os.path.isfile(os.path.join(self.runfolderpath, config.file_demultiplexing_old))

        if bcl2fastq_log:
            self.logger("Checking if already demultiplexed .........Demultiplexing has already been completed - "
                        "demultiplex log found @ {}/{} \n--- STOP ---".format(self.runfolderpath, self.demultiplexed),
                        "demultiplex_info")
            return True

        elif bcl2fastq_txt:
            self.logger("Checking if already demultiplexed .........Demultiplexing has already been completed - "
                        "demultiplex log found @ {}/{} \n--- STOP ---".format(self.runfolderpath,
                                                                              config.file_demultiplexing_old),
                        "demultiplex_info")
            return True


    def valid_samplesheet(self):
        """Run samplesheet check for formatting errors. Write resulting messages to logfiles.
        """
        if ValidSamplesheet(self.samplesheet_path).errors:
            err_str = ", ".join([item for sublist in ss_verification_results.values() for item in sublist])
            self.logger("Samplesheet checks failed {}: {}".format(self.samplesheet, err_str), "samplesheet_warning")
        else:
            self.logger("Samplesheet passed all checks {}".format(self.samplesheet), "demultiplex_success")
            return True


    def has_run_finished(self):
        """Check if sequencing has completed for the current runfolder - presence of "RTAComplete.txt".
        If sequencing complete, call valid_samplesheet() then setup_demultiplexing()
        """
        if os.path.isfile("{}/{}".format(self.runfolderpath, self.run_complete)): # Is RTAcomplete.txt present
            self.logger("Run finished  -  RTAcomplete.txt found @ "
                        "{}/{}\n".format(self.runfolderpath, self.run_complete), "demultiplex_info")

            if self.valid_samplesheet(): # If samplesheet valid setup_demultiplexing(), else error thrown
                self.setup_demultiplexing()
            else:
                self.logger("Demultiplexing halted due to samplesheet errors: {}".format(self.runfolder),
                            "demultiplex_fail_samplesheet")
        else:
            self.logger("Run not yet complete \n--- STOP ---\n", "demultiplex_info")


    def setup_demultiplexing(self):
        """Carries out pre-demultiplexing tasks.
        Check bcl2fastq installed, run integrity check if required, carry out samplesheet check, check if run is tso500,
        run bcl2fastq, check logfile to determine whether demultiplexing successful, mark runfolder as processed
        """
        self.test_bcl2fastq() # raise exception if bcl2fastq not installed

        if self.setup_integrity_check(): # Stops processing runfolder until integrity check performed
            # Set runfolder demultiplex log file name
            self.demultiplex_log = "{}/{}/{}".format(self.runfolders, self.runfolder, self.demultiplexed)
            # create file to prevent demultiplexing starting again - bcl2fastq2 v2.20 doesn't produce stdout
            # for a while after starting so create file here and append stdout later
            open(self.demultiplex_log, 'w').close() # close file immediately

            if not tso500_run(): # TSO500 runs do not require demultiplexing
                self.run_bcl2fastq()  # Script won't continue until process finishes
                self.check_demultiplex_logfile()  # check demultiplex success

            # Add runfolder name to self.processed_runfolders. Runfolder names in this list are appended
            # to the script log file at the end of the script cycle.
            self.processed_runfolders.append(self.runfolder)


    # UNSURE AS TO WHETHER THIS FUNCTION ACTUALLY WORKS CORRECTLY
    def tso500_run(self):
        """TSO500 runs do not require demultiplexing: If runfolder is from TSO500 run, writes to bcl2fastq2.log file
        which allows script to process runfolder in future without looking for bcl2fastq success statement
        """
        if ValidSamplesheet(self.samplesheet_path).tso:  # check if TSO500 run
            self.logger("{} is a {}".format(self.runfolder, config.demultiplexing_log_file_TSO500_message),
                        "demultiplex_success")
            with open(self.demultiplex_log, 'w') as bcl2fastq2_log:
                bcl2fastq2_log.write("\n{}".format(config.demultiplexing_log_file_TSO500_message))
            return True


    def test_bcl2fastq(self):
        """Call path to bcl2fastq2 using subprocess, capture streams, raise exception if bcl2fastq not installed.
        """
        proc = subprocess.Popen([self.bcl2fastq], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        out, err = proc.communicate() # Capture streams

        # If bcl2fastq installed and called with no inputs:
        # first line of stderr should contain the string: "BCL to FASTQ file converter"
        if "BCL to FASTQ file converter" not in err:
            self.logger("BCL2FastQ installation test failed.", "demultiplex_fail")
            raise Exception("bcl2fastq not installed")
        else:
            self.logger("BCL2FastQ installation test passed.", "demultiplex_success")


    def setup_integrity_check(self):
        """Calls functions (pre-checks) to determine whether checksums can be checked for the run (integrity checking)

        Ensures runfolder copied to workstation hasn't been corrupted by the transfer.
        Checksum generation and initial integrity checks are carried out by the sequencer_checksum.py script running
        on the sequencer, and written to a checksum file for access by this script.

        NB. this integrity check is not possible on all sequencers (ie miseq).
        """
        self.checksum_file_path = os.path.join(self.runfolderpath, self.checksum_file)
        if sequencer_requiring_integritycheck() and checksum_file_present():
            if not self.prior_integritycheck_failed():
                if self.checksums_match(): # If false, script stops here but will reach this point every hour
                    return True  # integrity checking passed
                else:
                    self.email_subject = "MOKA ALERT: INTEGRITY CHECK FAILED"
                    self.email_priority = 1
                    self.email_message = "run:\t{}\nPlease follow the protocol " \
                                         "for when integrity checks fail".format(self.runfolder)
                    self.send_email()
                    self.logger("Integrity check fail. checksums do not match for ""{} see "
                                "{}".format(self.runfolder, self.checksum_file_path), "demultiplex_fail")
                    return False  # integrity checking failed - stop script for run


    def sequencer_requiring_integritycheck(self):
        """Check whether checksum check needed. Only runs from sequencers that can have checksums generated require
        this - not all sequencers can have checksums generated by the integrity check script.
        """
        if any(sequencer in config.sequencers_with_integrity_check in self.runfolder):
            return True
        else:
            self.logger("Data integrity check not required. Continuing...", "demultiplex_info")


    def checksum_file_present(self):
        """Determines whether checksum file is present
        """
        if os.path.isfile(self.checksum_file_path): # checksums have been written to file by integrity check scripts
            self.logger("Checksums file present", "demultiplex_info")
            return True
        else: # integrity check not been performed
            self.logger("Integrity check not yet performed on sequencer. Stopping...", "demultiplex_info")


    def prior_integritycheck_failed(self):
        """Check if runfolder has failed a previous integrity check by this script
        Denoted by presence of config.checksum_complete_flag string in checksum file
        This flag prevents checksums_match from performing further integrity checks
        (This string is added when self.checksums_match() is called and config.checksum_match
        is not present in the first line of the file)
        """
        with open(self.checksum_file_path, 'r') as checksum_file:
            checksums = checksum_file.readlines() # read checksum file into list

        if config.checksum_complete_flag in checksums[-1]: # (last line in file, last element in list)
            self.logger("Previously reported failed integrity check", "demultiplex_info")
            return True


    def checksums_match(self):
        """Checks whether checksums match in checksum file.
        File should contain: Pass/fail statement in Line 1, checksums for both copies of run folder on lines 2 and 3
        Function adds line to file to denote integrity check has been assessed - stops repetition if check fails
        """
        self.logger("Data integrity checks starting...", "demultiplex_info")

        with open(self.checksum_file_path, 'r') as checksum_file: # open file containing md5 checksums
            checksums = checksum_file.readlines() # read checksums into list

        # Add a flag into the checksum file to prevent script performing future checksum checks
        with open(self.checksum_file_path, 'a') as checksum_file:
            checksum_file.write("\n{}".format(config.checksum_complete_flag))

        if config.checksum_match in checksums[0]: # line 1 contains pass/fail statement from integrity check script
            self.logger("Integrity check of runfolder {} passed".format(self.runfolder), "demultiplex_success")
            return True # checksums match


    def send_email(self):
        """Send progress log messages via email to recipient (self.you) via SMTP.
        """
        self.logfile("Sending an email. Recipient: {}. Subject: {}. "
                     "Body:\n{}".format(self.me, self.email_subject, self.email_message), "demultiplex_info")

        m = Message() # Create email.Message() object
        m['X-Priority'] = str(self.email_priority)  # X-Priority = 1. Sets a high-priority e-mail.
        m['Subject'] = self.email_subject
        # Add error messages to e-mail body using email.Message.set_payload()
        m.set_payload(self.email_message)
        try:
            # Configure SMTP server connection for sending log messages via e-mail
            server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
            server.set_debuglevel(1) # Output connection debug messages
            server.starttls() # Encrypt SMTP commands using Transport Layer Security mode$
            server.ehlo() # Identify client to ESMTP server using EHLO commands
            server.login("abc", self.pw) # Login to server with user credentials
            server.sendmail(self.me, [self.you], m.as_string()) # Send email to server
            self.logger("Email sent without error", "demultiplex_info")
        except:
            self.logger("Error when sending email. Email not sent.", "demultiplex_fail")


    def run_bcl2fastq(self):
        """
        Create and run bcl2fastq shell command to run demultiplexing using runfolder as input
        Command appends bcl2fastq stdout and stderr to the demultiplex_log file.

        Example: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
                        -R 160822_NB551068_0006_AHGYM7BGXY/
                        --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
                        --no-lane-splitting >>
                        /media/data1/share/1111_M02353_NMNOV17_ONCTEST/bcl2fastq2_output.log 2&>1"
        (N.B. n--no-lane-splitting creates a single fastq for a sample, not into one fastq per lane)
        """
        command = "{} -R {}/{} --sample-sheet {} --no-lane-splitting >> " \
                  "{} 2>&1".format(self.bcl2fastq, self.runfolders, self.runfolder,
                                   self.samplesheet_path, self.demultiplex_log)

        self.logger("Running bcl2fastq. command = {}".format(command), "demultiplex_info")
        subprocess.call([command], shell=True) # waits until subprocess complete

        self.logger("Demultiplexing started for run {}".format(self.runfolder), "demultiplex_success")


    def check_demultiplex_logfile(self):
        """Check demultiplexing completed successfully. Read stderr and stdout from bcl2fastq in
        the demultiplex log file, searching the last line for the expected success statement.
        """
        # Runfolder demultiplex logfile
        run_demultiplex_logfile = "{}/{}".format(self.runfolderpath, self.demultiplexed)

        # Read last 10 lines of demultiplex log file - details success or failure of bcl2fastq command
        bcl2fastq_log_tail = subprocess.check_output(["tail", "-n", "10", run_demultiplex_logfile])

        # Search for success statement defined in config file
        if re.search(config.demultiplex_success_match, bcl2fastq_log_tail):
            self.logger("Demultiplexing complete without error for run {}".format(self.runfolder),
                        "demultiplex_success")

        else: # No success statement (demultiplex errors) - report last few lines of runfolder demultiplex log
            self.logger("ERROR - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ ERROR) - Demultiplexing failed for run {}. "
                        "Please see {}\n{}".format(self.runfolder, run_demultiplex_logfile, bcl2fastq_log_tail),
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
