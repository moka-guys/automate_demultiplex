# coding=utf-8
""" Demultiplex NGS Run Folders

The script performs demultiplexing, and also performs samplesheet validation using the seglh-naming library on runs
that have not yet been demultiplexed to act as an early warning system for samplesheet errors.

Firstly, runs a set of checks on all runfolders in a given directory to determine whether demultiplexing
is required for that runfolder. The runfolder must meet the following requirements:
 - bcl2fastq2 logfile "bcl2fastq2_output.log" absent (demultiplexing not yet performed). bcl2fastq2 stdout and stderr
   streams are written to this file
 - Sequencing complete (presence of "RTAComplete.txt" file created by sequencer when sequencing completed)
 - bcl2fastq2 is installed
 - Sampleseheet does not contain any errors that would cause demultiplexing to fail. Must exist, be correctly named, be
   populated, contain minimum expected data headers, samplenames must only contain valid characters

If the sequencer does not require an integrity check, it skips straight to run_demultiplexing()

If the sequencer does require an integrity check the following requirements must be met for demultiplexing to occur:
- Checksum file must be present
- The run has not failed a previous integrity check performed by this script
- The checksums match in the checksum file

run_demultiplexing then carries out demultiplexing tasks:
- Create a demultiplexing log file to prevent a simultaneous attempt on the next run of the script (bcl2fastq2 is slow
  to create the logfile)
- If the run is a tso run, creates a tso bcl2fastq2 log file but does not demultiplex
- Demultiplexes all other runs that get this far

If the script has processed any runfolders, it renames the logfile with the runfolder names
"""

import os
import subprocess
import datetime
import smtplib
import logging
import logging.handlers
import re
from email.message import Message
from git_tag.git_tag import git_tag  # Import function which reads the git tag
from samplesheet_validator.samplesheet_validator import SamplesheetCheck
import automate_demultiplex_config as config  # Import config file


class GetRunfolders(object):
    """
    Loop through and process NGS runfolders in a given directory.
    Single class instance required to demultiplex all NGS runfolders. E.g.:
        >>> runs = GetListOfRuns().loop_through_runs()

    Methods:
        run_demultiplexrunfolders()
            Pass NGS runfolders to instance of DemultiplexRunfolder() for processing.
            After demultiplexing is performed (or skipped) for all runfolders, close script log file.
        bcl2fastq_installed()
            Check bcl2fastq exe file present and executable using os.access, raise exception if not installed
        rename_demultiplex_logfile()
            If runfolders processed, rename the logfile using processed runfolder names.
    """

    def __init__(self, runfolders_path, demultiplex_logfiles, datetime_now):
        """self.runfolders_path points to workstation runfolders location
        Its value here must be same as in ReadyToStartDemultiplexing()
        """
        self.runfolders_path = runfolders_path
        self.runfolder_names = os.listdir(self.runfolders_path)
        self.runfolder_pattern = config.runfolder_pattern
        self.datetime_now = datetime_now
        self.bcl2fastq_path = config.bcl2fastq_path  # Path to bcl2fastq2
        # Logging
        self.demultiplex_logfiles = demultiplex_logfiles  # Directory containing script log
        self.scriptlog_path = "{}{}.txt".format(self.demultiplex_logfiles,  # Script logfile for this hour's cron job
                                                str('{:%Y%m%d_%H%M%S}'.format(self.datetime_now)))
        self.logger = Logging(self.scriptlog_path).logger
        self.log_msgs = config.demux_logmsgs
        self.log_flags = config.demultiplex_log_flags

    def run_demultiplexrunfolders(self):
        """Pass NGS runfolders to instance of DemultiplexRunfolder() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file."""

        open(self.scriptlog_path, 'w').close()  # Create logfile

        self.logger.info(self.log_msgs['demux_script_start'].format(git_tag()), extra={'flag': "demultiplex_started"})
        processed_runfolders = []

        for folder_name in self.runfolder_names:  # Pass runfolders to demultiplex.demultiplex_checks()
            runfolderpath = "{}/{}".format(self.runfolders_path, folder_name)
            samplesheet_path = "{}samplesheets/{}_SampleSheet.csv".format(self.runfolders_path, folder_name)
            if self.bcl2fastq_installed() and os.path.isdir(runfolderpath) and \
                    re.compile(self.runfolder_pattern).match(folder_name):
                # If runfolder has been processed during this run of the scripts
                demultiplex_obj = DemultiplexRunfolder(self.scriptlog_path, samplesheet_path,
                                                       runfolderpath, folder_name, self.bcl2fastq_path)
                demultiplex_obj.setoff_workflow()
                if demultiplex_obj.run_processed:
                    processed_runfolders.append(folder_name)  # Add runfolder to processed runfolder list

        self.rename_demultiplex_logfile(processed_runfolders)
        return processed_runfolders

    def bcl2fastq_installed(self):
        """Check bcl2fastq exe file present and executable using os.access, raise exception if not installed.
        """
        if os.access(self.bcl2fastq_path, os.X_OK):
            self.logger.info(self.log_msgs['bcl2fastq_test_pass'], extra={'flag': self.log_flags['success']})
            return True
        else:
            self.logger.error(self.log_msgs['bcl2fastq_test_fail'], extra={'flag': self.log_flags['fail']})


    def rename_demultiplex_logfile(self, processed_runfolders):
        """If runfolders processed by bcl2fastq during this cycle,, rename the logfile using processed runfolder names.
        Allows easy identification of processed runs in logfile name, and differentiates log from others
        uploaded to DNAnexus """

        num_processed_runfolders = len(processed_runfolders)
        self.logger.info(self.log_msgs['demux_script_end'].format(git_tag(), str(num_processed_runfolders)),
                         extra={'flag': "demultiplex_complete"})
        if num_processed_runfolders > 0:
            processed_run_string = "_{}_demultiplex_script_log.txt".format("_".join(processed_runfolders))
            new_scriptlog_name = "{}{}".format(os.path.splitext(self.scriptlog_path)[0], processed_run_string)
            os.rename(self.scriptlog_path, new_scriptlog_name)
            self.scriptlog_path = new_scriptlog_name
            return True


class DemultiplexRunfolder(object):
    """Call bcl2fastq2 on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present.

    Methods:
        setoff_workflow()
            Setoff demultiplex workflow only on runs where demultiplexing is required
        demultiplexing_required()
            Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing required.
        bcl2fastqlog_absent()
            Check presence of demultiplex logfile
        valid_samplesheet()
            Check samplesheet is present and naming and contents are valid. Returns error string and boolean
        sequencing_complete()
            Check if sequencing run has completed.
        no_disallowed_sserrs()
            Check for specific errors that would case bcl2fastq2 to fail and whose presence should stop demultipelxing
        integritycheck_not_required()
            Determines whether the run requires integrity checking (not possible on all sequencers).
        run_demultiplexing()
            Call demultiplexing functions
        checksumfile_present()
            Checks if checksums generated for the run (i.e. integrity checking scripts have completed for the run).
        prior_integritycheck_failed()
            Check if run previously failed integrity check (needs manual intervention before further processing).
        integrity_check_success()
            Checks whether checksums in the checksum file match
            i.e. the runfolder copied to workstation has not been corrupted by the transfer.
        create_bcl2fastqlog()
            Create file to prevent demultiplexing starting again.
        add_bcl2fastqlog_tso_msg()
            If runfolder is from TSO500 run, specific message is added to bcl2fastq2_output.log file (TSO500 runs do not
            require demultiplexing)
        run_subprocess(cmd)
            Takes a string command as input and runs this as a subprocess
        check_bcl2fastqlogfile()
            Read last 10 lines of demultiplex logfile and search for success statement
        logger(message, flag)
            Write log messages to the system log.
    """

    def __init__(self, scriptlog_path, samplesheet_path, runfolderpath, folder_name, bcl2fastq_path):
        # Logging
        self.scriptlog_path = scriptlog_path
        self.log_msgs = config.demux_logmsgs
        self.log_flags = config.demultiplex_log_flags
        self.logger = Logging(self.scriptlog_path).logger
        # Runfolder
        self.runfolder_name = str(folder_name)
        self.runfolderpath = runfolderpath
        # Samplesheet
        self.samplesheet_path = samplesheet_path
        self.sequencerid_list = config.sequencer_ids
        self.panel_list = config.panel_list
        self.runtype_list = config.runtype_list
        self.tso500panel_list = config.tso500_panel_list
        self.disallowed_sserrs = ["sspresent_err", "ssname_err", "ssempty_err", "headers_err", "validchars_err"]
        # Sequencing finished
        self.rtacompletefile = config.rtacomplete_name  # File denoting end of sequencing run
        self.rtacompletefile_path = "{}/{}".format(self.runfolderpath, self.rtacompletefile)
        # Integrity check
        self.checksumfile = config.md5checksum_name
        self.checksumfile_path = os.path.join(self.runfolderpath, self.checksumfile)
        self.sequencers_with_integritycheck = config.sequencers_with_integrity_check
        self.checksumcomp_complete_msg = config.checksumcomp_complete_msg
        self.checksum_match_msg = config.checksum_match_msg
        self.icfail_emailsubj = config.icfail_emailsubj
        self.icfail_emailmsg = config.icfail_emailmsg.format(self.runfolder_name)
        # Bcl2fastq
        self.bcl2fastq_path = bcl2fastq_path
        self.bcl2fastqlog_name = config.bcl2fastqlog_name  # File denoting demultiplexing status
        self.bcl2fastqlog_path = os.path.join("{}/{}".format(self.runfolderpath, self.bcl2fastqlog_name))
        self.tso500_bcl2fastq_msg = config.demultiplexing_log_file_TSO500_message
        self.bcl2fastq_success_match = config.demultiplex_success_match
        # Shell command to run demultiplexing. Appends stdout and stderr to the bcl2fastqlog file.
        # (N.B. n--no-lane-splitting creates a single fastq for a sample, not into one fastq per lane)
        self.bcl2fastq_cmd = "{} -R {} --sample-sheet {} --no-lane-splitting " \
                             ">> {} 2>&1".format(self.bcl2fastq_path, self.runfolderpath,
                                                 self.samplesheet_path, self.bcl2fastqlog_path)
        self.run_processed = False

    def setoff_workflow(self):
        """ Setoff demultiplex workflow only on runs where demultiplexing is required """
        if self.demultiplexing_required():
            self.run_demultiplexing()

    def demultiplexing_required(self):
        """ Carries out per-runfolder pre-demultiplexing tasks to determine whether demultiplexing required.
        Returns true if demultiplexing is required.
        """
        # Write to log file, recording automate_demultiplex repo version
        self.logger.info(self.log_msgs['demux_runfolder_start'].format(git_tag(), self.runfolderpath),
                         extra={'flag': self.log_flags['info']})

        if self.bcl2fastqlog_absent():
            self.valid_samplesheet()  # Early warning checks
            if self.sequencing_complete():
                if self.no_disallowed_sserrs():
                    if self.integritycheck_not_required():
                        return True
                    elif self.checksumfile_present():
                        if not self.prior_integritycheck_failed():
                            if self.integrity_check_success():
                                return True
                            else:  # Send email denoting checksums check has failed
                                Email(self.scriptlog_path, self.icfail_emailsubj, self.icfail_emailmsg).send_email()
                                self.logger(
                                    self.log_msgs['ic_fail'].format(self.runfolder_name, self.checksumfile_path),
                                    extra={'flag': self.log_flags['fail']})

    def run_demultiplexing(self):
        """Call demultiplexing functions
        TSO runs don't require demultiplexing. Create bcl2fastq2 log so scripts skip over these runs in future.
        """
        # Prevent simultaneous demultiplex attempt on next run of script (bcl2fastq2 is slow to create logfile)
        if self.create_bcl2fastqlog():
            sscheck = SamplesheetCheck(self.samplesheet_path, self.sequencerid_list, self.panel_list,
                                       self.runtype_list, self.tso500panel_list)
            if sscheck.tso:
                self.add_bcl2fastqlog_tso_msg()
                self.run_processed = True
            else:
                self.logger.info(self.log_msgs['bcl2fastq_start'].format(self.runfolder_name, self.bcl2fastq_cmd),
                                 extra={'flag': self.log_flags['info']})
                if self.run_subprocess(self.bcl2fastq_cmd):  # Runs bcl2fastq2 and checks if completed successfully
                    self.logger.info(self.log_msgs['bcl2fastq_complete'].format(self.runfolder_name),
                                     extra={'flag': self.log_flags['success']})
                    self.check_bcl2fastqlogfile()  # Check for success statement in logfile
                    self.run_processed = True
                    return True
                else:
                    self.logger.error(self.log_msgs['bcl2fastq_failed'].format(self.runfolder_name),
                                      extra={'flag': self.log_flags['fail']})

    def bcl2fastqlog_absent(self):
        """Check presence of demultiplex logfile
        ("bcl2fastq2_output.log", or "demultiplexlog.txt" for backwards compatability)
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            self.logger.info(self.log_msgs['demux_already_complete'].format(self.bcl2fastqlog_path),
                             extra={'flag': self.log_flags['info']})
        else:
            self.logger.info(self.log_msgs['demux_not_complete'].format(self.bcl2fastqlog_path),
                             extra={'flag': self.log_flags['info']})
            return True

    def valid_samplesheet(self):
        """ Check samplesheet is present and naming and contents are valid. Returns error string and boolean.
        """
        sscheck = SamplesheetCheck(self.samplesheet_path, self.sequencerid_list, self.panel_list,
                                   self.runtype_list, self.tso500panel_list)
        err_str = ", ".join([item for sublist in sscheck.errors.values() for item in sublist])
        if err_str:
            self.logger.warning(self.log_msgs['sschecks_not_passed'].format(self.samplesheet_path, err_str),
                                extra={'flag': self.log_flags['ss_warning']})
            return False, sscheck
        else:
            self.logger.info(self.log_msgs['sschecks_passed'].format(self.samplesheet_path),
                             extra={'flag': self.log_flags['success']})
            return True, sscheck

    def sequencing_complete(self):
        """Check if sequencing has completed for the current runfolder - presence of "RTAComplete.txt".
        """
        if not os.path.isfile(self.rtacompletefile_path):
            self.logger.info(self.log_msgs['run_incomplete'], extra={'flag': self.log_flags['info']})
        else:
            self.logger.info(self.log_msgs['run_finished'].format(self.rtacompletefile_path),
                             extra={'flag': self.log_flags['info']})
            return True

    def no_disallowed_sserrs(self):
        """ Check for specific errors that would case bcl2fastq2 to fail and whose presence should stop demultipelxing
        """
        valid, sscheck_obj = self.valid_samplesheet()
        if not valid:
            if any(sscheck_obj.errors[key] for key in self.disallowed_sserrs):
                err_str = ", ".join([item for sublist in sscheck_obj.errors.values() for item in sublist])
                self.logger.error(self.log_msgs['ssfail_haltdemux'].format(self.samplesheet_path, err_str),
                                  extra={'flag': self.log_flags['fail']})
        else:
            return True

    def integritycheck_not_required(self):
        """Check whether integrity check needed. Only runs from sequencers that can have checksums generated require
        this - not all sequencers can have checksums generated by the integrity check script.
        """
        if any(item in self.runfolder_name for item in self.sequencers_with_integritycheck):
            self.logger.info(self.log_msgs['ic_required'], extra={'flag': self.log_flags['info']})
        else:
            self.logger.info(self.log_msgs['ic_notrequired'], extra={'flag': self.log_flags['info']})
            return True

    def checksumfile_present(self):
        """Determines whether checksum file is present (checksums written to file by integrity check scripts)
        """
        if not os.path.isfile(self.checksumfile_path):
            self.logger.info(self.log_msgs['csumfile_absent'], extra={'flag': self.log_flags['info']})
        else:
            self.logger.info(self.log_msgs['csumfile_present'], extra={'flag': self.log_flags['info']})
            return True

    def prior_integritycheck_failed(self):
        """Check if runfolder has failed a previous integrity check by this script
        Denoted by presence of self.checksumcomp_complete_msg string in checksum file (flag added when
        self.integrity_check() called and self.checksum_match_msg is absent in the first line of the file - prevents
        integrity_check performing further integrity checks
        """
        with open(self.checksumfile_path, 'r') as checksumfile:
            checksums = checksumfile.readlines()  # Read checksum file into list

        if self.checksumcomp_complete_msg in checksums[-1]:  # Last line in file, last element in list
            self.logger.info(['checksums_checked'], extra={'flag': self.log_flags['info']})
            return True

    def integrity_check_success(self):
        """Checks whether checksums in the checksum file match - i.e. the runfolder copied to workstation has not been
        corrupted by the transfer.
        Checksum generation and initial integrity checks are carried out by the sequencer_checksum.py script running on
        the sequencer, and written to a checksum file for access by this script. Checksum generation and integrity
        check is not possible on all sequencers (i.e. miseq).

        Checksum file should contain:
            Pass/fail statement in Line 1, checksums for both copies of run folder on lines 2 and 3
            Function adds line to file to denote integrity check has been assessed - stops repetition if check fails
        """
        self.logger.info(self.log_msgs['ic_start'], extra={'flag': self.log_flags['info']})

        with open(self.checksumfile_path, 'r') as checksumfile:  # Open file containing md5 checksums
            checksums = checksumfile.readlines()  # Read checksums into list

        # Add a flag into the checksum file to prevent script performing future integrity checks
        with open(self.checksumfile_path, 'a') as checksumfile:
            checksumfile.write("\n{}".format(self.checksumcomp_complete_msg))

        if self.checksum_match_msg in checksums[0]:  # Line 1 contains pass/fail statement from integrity check script
            self.logger.info(self.log_msgs['ic_pass'].format(self.runfolder_name),
                             extra={'flag': self.log_flags['success']})
            return True  # checksums match

    def create_bcl2fastqlog(self):
        """Create file to prevent demultiplexing starting again.
        bl2fastq2 v2.20 doesn't produce stdout for a while after starting so create file here and append stdout later
        """
        try:  # If TSO run
            open(self.bcl2fastqlog_path, 'w').close()
            self.logger.info(self.log_msgs['create_bcl2fastqlog_pass'].format(self.runfolder_name),
                             extra={'flag': self.log_flags['fail']})
            return True
        except Exception as e:
            self.logger.error(self.log_msgs['create_bcl2fastqlog_fail'].format(self.runfolder_name, e),
                              extra={'flag': self.log_flags['info']})

    def add_bcl2fastqlog_tso_msg(self):
        """ If runfolder is from TSO500 run, specific message is added to bcl2fastq2_output.log file (TSO500 runs do not
        require demultiplexing)
        """
        self.logger.info("{} is a {}".format(self.runfolder_name, self.tso500_bcl2fastq_msg),
                         extra={'flag': self.log_flags['success']})
        try:
            with open(self.bcl2fastqlog_path, 'w+') as log:
                log.write("\n{}".format(self.tso500_bcl2fastq_msg))
                self.logger.info(self.log_msgs['create_tsobcl2fastqlog_pass'].format(self.runfolder_name),
                                 extra={'flag': self.log_flags['info']})
            return True
        except Exception as e:
            self.logger.error(self.log_msgs['create_tsobcl2fastqlog_fail'].format(self.runfolder_name, e),
                              extra={'flag': self.log_flags['fail']})

    @staticmethod
    def run_subprocess(cmd):
        """Takes a string command as input and runs this as a subprocess.
        # """
        if subprocess.call([cmd], shell=True) == 0:  # Wait until subprocess completes
            return True

    def check_bcl2fastqlogfile(self):
        """ Read last x lines of bcl2fastqlog logfile and search for success statement
        The last 10 lines of the demultiplex logfile detail the success of the bcl2fastq2 command
        If success statement not present, report last few lines to demultiplex log
        """
        if os.path.isfile(self.bcl2fastqlog_path):
            with open(self.bcl2fastqlog_path) as logfile:
                bcl2fastq2_log_tail = "".join(logfile.readlines()[-10:])
            if bcl2fastq2_log_tail:
                if re.search(self.bcl2fastq_success_match, str(bcl2fastq2_log_tail)):
                    self.logger.info(self.log_msgs['demux_complete'].format(self.runfolder_name),
                                     extra={'flag': self.log_flags['success']})
                    return True
                else:
                    self.logger.error(self.log_msgs['demux_error'].format(self.runfolder_name, self.bcl2fastqlog_path),
                                      extra={'flag': self.log_flags['fail']})
            else:
                self.logger.error(self.log_msgs['bcl2fastqlog_empty'].format(
                    self.runfolder_name, self.bcl2fastqlog_path), extra={'flag': self.log_flags['fail']})
        else:
            self.logger.error(self.log_msgs['bcl2fastqlog_absent'].format(self.runfolder_name, self.bcl2fastqlog_path),
                              extra={'flag': self.log_flags['fail']})


class Email(object):
    """
    Send email to recipient (self.you) via SMTP

    Methods:
        send_email()
            Send email using mail settings from init
    """
    def __init__(self, scriptlog_path, email_subject, email_message):
        self.user = config.user
        self.pw = config.pw
        self.host = config.host
        self.port = config.port
        self.smtp_do_tls = config.smtp_do_tls

        self.me = config.me  # Email sender
        self.you = config.you  # Email recipient
        self.email_priority = 1
        self.email_subject = email_subject
        self.email_message = email_message

        # Create email
        self.m = Message()  # Create email.Message() object
        self.m.set_payload(self.email_message)  # Add error messages to e-mail body using email.Message.set_payload()
        self.m['X-Priority'] = str(self.email_priority)  # X-Priority = 1. Sets a high-priority e-mail.
        self.m['Subject'] = email_subject

        self.logger = Logging(scriptlog_path).logger  # Logging
        self.log_msgs = config.demux_logmsgs
        self.log_flags = config.demultiplex_log_flags

    def send_email(self):
        """ Send email using mail settings from init """
        try:
            self.logger.info(self.log_msgs['email_sending'].format(self.me, self.email_subject, self.email_message),
                             extra={'flag': self.log_flags['info']})
            # Configure SMTP server connection for sending log messages via e-mail
            self.server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
            self.server.set_debuglevel(1)  # Output connection debug messages
            self.server.starttls()  # Encrypt SMTP commands using Transport Layer Security mode$
            self.server.ehlo()  # Identify client to ESMTP server using EHLO commands
            self.server.login(self.user, self.pw)  # Login to server with user credentials
            self.server.sendmail(self.me, [self.you], self.m.as_string())  # Send email to server
            self.logger.info(self.log_msgs['email_pass'], extra={'flag': self.log_flags['info']})
            return True
        except Exception as e:
            self.logger.error(self.log_msgs['email_fail'].format(e), extra={'flag': self.log_flags['fail']})


class Logging(object):
    """ Create logger instance
    """
    if config.testing:
        formatter = logging.Formatter("%(asctime)s - TEST MODE - %(name)s - %(flag)s - %(levelname)s - %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(flag)s - %(levelname)s - %(message)s")

    def __init__(self, scriptlog_path):
        self.scriptlog_path = scriptlog_path
        self.logger = self._get_logger()

    def _get_logger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(self.scriptlog_path))
        logger.addHandler(self._get_syslog_handler())
        return logger

    def _get_file_handler(self, filepath):
        fh = logging.FileHandler(filepath, mode='a')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.formatter)
        return fh

    def _get_syslog_handler(self):
        slh = logging.handlers.SysLogHandler(address='/dev/log')
        slh.setLevel(logging.DEBUG)
        slh.setFormatter(self.formatter)
        return slh


if __name__ == '__main__':
    gr_obj = GetRunfolders(runfolders_path=config.runfolders, demultiplex_logfiles=config.demultiplex_logfiles,
                           datetime_now=datetime.datetime.now())
    gr_obj.run_demultiplexrunfolders()
