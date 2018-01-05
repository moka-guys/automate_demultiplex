"""
Demultiplex NGS Run Folders

This script runs bcl2fastq on newly completed NGS run folders in a specific directory. Sequencing is
deemed complete by the presence of a file ("RTAComplete.txt"), which is created by the sequencer
when the run is ready for demultiplexing. A sample sheet must be present in the samplesheets folder
with the name "RUN_samplesheet.csv", where "RUN" is the name of the run folder.

Before demultiplexing, the script checks for the absence of the log file "demultiplexlog.txt" in
the run folder. bcl2fastq stdout and stderr streams are written to this file, which when present
indicates that demultiplexing is in process or has already been performed.
"""

# Created: 19 Sep 2016
# Authors: Aled Jones <aled.jones@nhs.net>
#          Nana Mensah <Nana.mensah1@nhs.net>


import os
import subprocess
import datetime
import smtplib
import time
from email.Message import Message
import requests
import json
from checksumdir import dirhash
#import config file
import automate_demultiplex_config as config



class get_list_of_runs():
    """Loop through and process NGS runfolders in a given directory.

    Methods defined here:

    loop_through_runs()
        Pass each runfolder to an instance of ready2start_demultiplexing().

    A single class instance is required to demultiplex all NGS runfolders. Example:
    >>> runs = get_list_of_runs()
    >>> runs.loop_through_runs()
    """

    def __init__(self):
        # self.runfolders points to the location of runfolders on the workstation,
        # its value here must be the same as in ready2start_demultiplexing().
        self.runfolders = config.runfolders
        self.now = ""  # Stores time stamp for class instance, used in log file.

    def loop_through_runs(self):
        """Pass NGS run folders to an instance of ready2start_demultiplexing() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, close script log file.
        """
        # Set a time stamp to append to the logfile name
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))

        # List all files and folders in the runfolder directory
        all_runfolders = os.listdir(self.runfolders)

        # Create a class instance for checking and running demultiplexing on each runfolder
        demultiplex = ready2start_demultiplexing(self.now)
        # Write to system log to signal the start of the automate demultiplex script
        demultiplex.logger("automate demultiplex release %s started on workstation." % config.script_release,
                           "demultiplex_started")

        # Loop through directory listing and pass runfolders to demultiplex.already_demultiplexed()
        # This function determines if the runfolder is ready to be demultiplexed and triggers demultiplexing
        for folder in all_runfolders:
            # Ignore folders in the list config.ignore_directories and test that it is a directory (ignoring files)
            if folder not in config.ignore_directories and os.path.isdir(self.runfolders + "/" + folder):  
                demultiplex.already_demultiplexed(folder)

        # Get number of runfolders processed by bcl2fastq during this cycle
        num_processed_runfolders = len(demultiplex.processed_runfolders)

        # Write message to system log to indicate demultiplex complete
        demultiplex.logger("automate demultiplex release %s complete. %s runfolder(s) processed." % \
                          (config.script_release, str(num_processed_runfolders)), "demultiplex_complete")

        # Close the script log file when all processing is complete
        demultiplex.script_logfile.close()

        # If runfolders were processed by bcl2fastq during this cycle.
        if num_processed_runfolders > 0:
        # Create an underscore-delimited string of all runfolders demultiplexed in this cycle, 
        # ending with '_demultiplex_script_log.txt'.
            processed_run_string = "_" + "_".join(demultiplex.processed_runfolders) + "_demultiplex_script_log.txt"
        # Use os.path.splitext() to remove the ".txt" extension from the current script log file name 
        # and append processed_run_string. Store this in new_scriptlog_name.
            new_scriptlog_name = os.path.splitext(demultiplex.logfile_name)[0] + processed_run_string
        # Rename the script log file to new_scriptlog_name. Allows processed runs to be easily 
        # identified from the script log name and differentiates this log from others uploaded to DNA nexus.
            os.rename(demultiplex.logfile_name, new_scriptlog_name)


class ready2start_demultiplexing():
    """Call bcl2fastq on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present. 

    Arguments:
    now
        Timestamp for log file name, assigned to self.now (str).

    Methods defined here:
    already_demultiplexed(runfolder)
        Check if the runfolder has been demultiplexed.
    has_run_finished()
        Check if sequencing run has completed.
    look_for_sample_sheet()
        Check expected samplesheet exists in runfolder.
    check_valid_samplesheet()
        Return True if no invalid characters are found in the samplesheet.
    run_demultiplexing()
        Run bcl2fastq with runfolder as input.
    check_demultiplexlog_file()
        Check demultiplexing completed succesfully.
    send_an_email(m_message, m_subject)
        Send progress messages via email.
    test_bcl2fastq()
        Raise exception if bcl2fastq is not installed.
    smartsheet_demultiplex_in_progress()
        Update smartsheet to say that demultiplexing is in progress.
    smartsheet_demultiplex_complete()
        Update smartsheet to say that demultiplexing is complete.
    logger(message, tool)
        Write log messages to the system log.
    """

    def __init__(self, now):
        # self.runfolders points to the location of runfolders on the workstation,
        # its value here must be the same as in get_list_of_runs().
        self.runfolders = config.runfolders
        # Assign timestamp from get_list_of_runs() to self.variable
        self.now = now

        # Samplesheet folder
        self.samplesheets = config.samplesheets
        # File which denotes the end of a sequencing run
        self.complete_run = config.file_complete_run
        # File which denotes demultiplexing is under way or complete
        self.demultiplexed = config.file_demultiplexing

        # Empty variables to be defined based on the run
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.list_of_samplesheets = []
        self.processed_runfolders = []

        # Path to bcl2fastq
        self.bcl2fastq = config.bcl2fastq

        # Set script log file path and name for this hour's cron job (script log file).
        self.script_logfile_path = config.demultiplex_logfiles
        self.logfile_name = self.script_logfile_path + self.now + ".txt"
        # Open the script logfile for logging throughout script.
        self.script_logfile = open(self.logfile_name, 'a')


        # Email server settings
        self.user = config.user
        self.pw = config.pw
        self.host = config.host
        self.port = config.port
        self.smtp_do_tls = config.smtp_do_tls
        # who the email is coming from
        self.me = config.me
        # who the email is going to
        self.you = config.you
        
        # some variables used by send_an_email function
        self.email_subject=""
        self.email_priority=1
        self.email_message=""

        # Smartsheet config
        # API key
        self.api_key = config.smartsheet_api_key
        # Smartsheet id
        self.sheetid = config.smartsheet_sheetid
        # New row variable
        self.rowid = ""
        # Time stamp for when run started
        self.smartsheet_started = ""
        self.smartsheet_complete = ""
        # Column ids
        self.ss_title = str(config.ss_title)
        self.ss_description = str(config.ss_description)
        self.ss_samples = str(config.ss_samples)
        self.ss_status = str(config.ss_status)
        self.ss_priority = str(config.ss_priority)
        self.ss_assigned = str(config.ss_assigned)
        self.ss_received = str(config.ss_received)
        self.ss_completed = str(config.ss_completed)
        self.ss_duration = str(config.ss_duration)
        self.ss_metTAT = str(config.ss_metTAT)
        # Requests info
        self.headers = config.smartsheet_request_headers
        self.url = config.smartsheet_request_url

        # variables to hold checksums:
        self.sequencer_checksum = ""
        self.workstation_checksum = ""
        
        # variable to count # samples on a run - used to update smartsheet
        self.sample_count=0


    def already_demultiplexed(self, runfolder):
        """Check if the runfolder has been demultiplexed. This is denoted by the presence of the
        file "demultiplexlog.txt". If the runfolder has not been demultiplexed, call
        ready2start_demultiplexing.has_run_finished() to proceed.

        Arguments:
        runfolder (str)
            The runfolder name 
        """

        # Capture the runfolder and its path
        self.runfolder = str(runfolder)
        self.runfolderpath = self.runfolders + "/" + self.runfolder

        # Write to log file, recording the version of the automate_demultiplex repository
        self.script_logfile.write("\nautomate_demultiplexing release: "+ config.script_release + "\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\nAssessing......... " + self.runfolderpath+"\n")

        # Check if the demultiplex log file is present 
        # using the os.path.isfile() function to determine if demultiplexlog.txt is present
        if os.path.isfile(self.runfolderpath + "/" + self.demultiplexed):
            # Stop processing this run folder and write to log file
            self.script_logfile.write("Checking if already demultiplexed .........Demultiplexing has already been completed  -  demultiplex log found @ " + self.runfolderpath + "/" + self.demultiplexed + " \n--- STOP ---\n")
        else:
            # Else proceed by calling the function which checks if sequencing has finished
            self.script_logfile.write("Checking if already demultiplexed .........Run has not yet been demultiplexed\n")
            self.has_run_finished()

    def has_run_finished(self):
        """Check if sequencing has completed for the current runfolder. This is denoted by the
        presence of the file "RTAComplete.txt". If sequencing is complete, call
        ready2start_demultiplexing.look_for_sample_sheet() to proceed.
        """
        # Check if the RTAcomplete.txt file is present
        # using the os.path.isfile() function to determine if the RTAcomplete.txt file is present
        if os.path.isfile(self.runfolderpath + "/" + self.complete_run):
            self.script_logfile.write("Run has finished  -  RTAcomplete.txt found @ " + self.runfolderpath + "/" + self.complete_run + "\n")
            # If so proceed by checking if a sample sheet is present
            self.look_for_sample_sheet()
        else:
            # Else stop
            self.script_logfile.write("run is not yet complete \n--- STOP ---\n")

    def look_for_sample_sheet(self):
        """Check that the sample sheet for the current runfolder is present."""
        # Set the name and path of the sample sheet to find
        self.samplesheet = self.samplesheets + "/" + self.runfolder + "_SampleSheet.csv"

        # Get a list of samplesheets in the samplesheets folder
        all_runfolders = os.listdir(self.samplesheets)
        # In case samplesheets have a mix of capitalisation, convert all names to uppercase
        for samplesheet in all_runfolders:
            self.list_of_samplesheets.append(samplesheet.upper())

        # Set the expected samplesheet name in uppercase
        expected_samplesheet = self.runfolder.upper() + "_SAMPLESHEET.CSV"
        # Check that the expected samplesheet exists
        if expected_samplesheet in self.list_of_samplesheets:
            self.script_logfile.write("Looking for a samplesheet .........samplesheet found @ " + self.samplesheet + "\n")
            # Test if the samplesheet contains valid characters using self.check_valid_samplsheet(). 
            # Returns true if the sample sheet does not contain illegal characters
            if self.check_valid_samplesheet():
                self.logger("Sample sheet is valid - no illegal characters found for run " + self.runfolder, "demultiplex_success")
                # Record result in log file
                self.script_logfile.write("Checking for invalid characters in 'Sample_ID' and 'Sample_Name' columns " +
                                          "......... All characters valid \n")
                # Call the function to run demultiplexing
                self.run_demultiplexing()
            # Else stop and write error messages to loggers and send error e-mail.
            else:
                # Record error messages in system log
                self.logger("Invalid characters found in samplesheet for run " + self.runfolder, "demultiplex_fail_samplesheet")
        else:
            # No samplesheet found. Stop and log message.
            self.script_logfile.write("Looking for a samplesheet ......... no samplesheet present \n--- STOP ---\n")
            self.logger("No samplesheet found for run " + self.runfolder, "demultiplex_fail_samplesheet")

    def check_valid_samplesheet(self):
        '''Validate the 'Sample_ID' and 'Sample_Name' table columns within the sample sheet csv
        file. The presence of invalid characters in these columns raises an error in bcl2fastq2.
        Return True if no invalid characters found.
        '''
        # Create empty list to store sample ids and sample names from the samplesheet
        sample_strings = []

        # Set a string containing valid characters, defined by bcl2fastq as an alphanumeric, '-', or '_' character.
        valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        # Separate characters into a set for quick lookup
        valid_char_set = set(valid_chars.split())

        # Open samplesheet as read only.
        with open(self.samplesheet, 'r') as samplesheet_stream:
            # read the file into a list and loop through the list in reverse (bottom to top).
            # this allows us to access the sample names, and stop when reach the column headers, skipping the header of the file.
            for line in reversed(samplesheet_stream.readlines()):
                # If the line contains table headers, stop looping through the file
                if line.startswith("Sample_ID"):
                    break
                # if it's a line detailing a sample 
                else:
                    # Split the current line of the csv, with commas as the delimiter
                    columns = line.split(",")
                    # Remove leading and trailing whitespace from sampleID and sampleName.
                    # bcl2fastq tolerates leading and trailing whitespace.
                    sample_id, sample_name = columns[0].strip(" "), columns[1].strip(" ")
                    # Append sample id and sample name to sampleStrings for testing
                    sample_strings.append(sample_id)
                    sample_strings.append(sample_name)

                    # increase sample count to record in smartsheet how many samples have been processed
                    self.sample_count += 1

        # Loop through the characters of each sample string
        for sample_string in sample_strings:
            for char in sample_string:
                # Check that each character in the string is valid, returning True if valid and False if not
                if char not in valid_chars:
                    return False
        else:
            return True

    def run_demultiplexing(self):
        """Run bcl2fastq using runfolder as input. Create demultiplex log file in runfolder."""

        # Call function to test if bcl2fastq is installed and working as expected
        # if it fails an exception is raised.
        self.test_bcl2fastq()
        # Call function to add the run to smartsheet, with status set to 'in progress'
        self.smartsheet_demultiplex_in_progress()

        # before demultiplexing starts check the integrity of the runfolder against that on the sequencer. 
        # If the checks pass the funcion will return true. if it fails errors are reported within the function
        if self.prepare_integrity_check():
            # Set demultiplex log file name for this runfolder.
            demultiplex_log = (self.runfolders + "/" + self.runfolder + "/" + self.demultiplexed)
            # create this file to ensure demultiplexing doesn't start again - bcl2fastq2 v2.20 doesn't produce any standard out for a while after starting so create this here and append later
            create_file = open(demultiplex_log, 'w')
            #close file immediately
            create_file.close()

            # Set a string with the shell command to run demultiplexing.
            # The command appends bcl2fastq stdout and stderr to the demultiplex_log file.
            # Example: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
            #           -R 160822_NB551068_0006_AHGYM7BGXY/
            #           --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
            #           --no-lane-splitting >> 
            #           /media/data1/share/1111_M02353_NMNOV17_ONCTEST/demultiplexlog.txt 2&>1"
            # where --no-lane-splitting creates a single fastq for a sample, not into one fastq per lane
            command = (self.bcl2fastq + " -R " + self.runfolders + "/" + self.runfolder + 
                      " --sample-sheet " + self.samplesheet + " --no-lane-splitting >> " +
                      demultiplex_log + " 2>&1")

            # Write progress/status to script log file
            self.script_logfile.write("running bcl2fastq. command = " + command + "\n")
            # Add entry to system log
            self.logger("Demultiplexing started for run " + self.runfolder, "demultiplex_success")

            # Run the bcl2fastq command to start demultiplexing. the script won't continue until this 
            # process finishes. Stderr and stdout streams are redirected to the log file by the command
            subprocess.call([command], shell=True)

            # Add runfolder name to self.processed_runfolders. Runfolder names in this list are appended
            # to the script log file at the end of the script cycle.
            self.processed_runfolders.append(self.runfolder)

            # Call method to check the success of demultiplexing
            self.check_demultiplexlog_file()

    def check_demultiplexlog_file(self):
        """Check demultiplexing completed successfully. Read the stderr and stdout from bcl2fastq in
        the demultiplex log file, searching the last line for the expected success statement.
        """
        
        # Set the path to the demultiplex log file for this runfolder
        run_logfile_path = self.runfolderpath + "/" + self.demultiplexed
        # Read the last 10 lines of the runfolder's demultiplex log file, which details the success 
        # or failure of the bcl2fastq command. In the event of errors, this is written to the script log file.
        bcl2fastq_log_tail = subprocess.check_output(["tail","-n","10", run_logfile_path])

        # If demultiplexing completed successfully - looking for expected success statement as defined in config file
        if config.logfile_success in bcl2fastq_log_tail:
            # Write to system log
            self.logger("Demultiplexing complete without error for run " + self.runfolder, "demultiplex_success")
            # Call function which updates smartsheet, changing status for this run from in progress to complete, where task = demultiplex.
            self.smartsheet_demultiplex_complete()

        # If demultiplexing did not complete without errors
        else:
            # Write to log file and report last few lines of the failed runfolder's demultiplex log.
            self.script_logfile.write("ERROR - DEMULTIPLEXING UNSUCCESFULL - please see " + 
                                      run_logfile_path + "\n" + bcl2fastq_log_tail )
            # Write to system log
            self.logger("BCL2FastQ ERROR. Demultiplexing failed for run " + self.runfolder, "demultiplex_fail")

    def send_an_email(self):
        """Send progress log messages via email to recipient (self.you) via SMTP.
        
        Arguments:
        m_message
            Message to be sent in e-mail body (str)
        m_subject
            Subject line of email to be sent (str)
        """
        # Write to script log file
        self.script_logfile.write("Sending an email to..... " + self.me)

        # Create email.Message() object. Set e-mail headers for X-Priority and Subject
        m = Message()
        m['X-Priority'] = str(self.email_priority)  # X-Priority = 1. Sets a high-priority e-mail.
        m['Subject'] = self.email_subject
        # Add error messages to e-mail body using email.Message.set_payload()
        m.set_payload(self.email_message)

        # Configure SMTP server connection for sending log messages via e-mail
        server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
        # Output connection debug messages
        server.set_debuglevel(1)
        # Encrypt SMTP commands using Transport Layer Security mode$
        server.starttls()
        # Identify client to ESMTP server using EHLO commands
        server.ehlo()
        # Login to server with user credentials
        server.login(self.user, self.pw)
        # Send email to server. Message is a call to email.Message.as_string()
        server.sendmail(self.me, [self.you], m.as_string())
        # Write to script log file
        self.script_logfile.write("................email sent\n")

    def test_bcl2fastq(self):
        """Raise exception if bcl2fastq is not installed."""
        
        # call the path to bcl2fastq2 using subprocess to capture the stderr and stdout. NB the required text is in stderr not stdout
        proc = subprocess.Popen([self.bcl2fastq],stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        # Capture the streams
        (out, err) = proc.communicate()

        # If bcl2fastq is installed and called with no inputs, the first line of stderr should contain the string "BCL to FASTQ file converter".
        if "BCL to FASTQ file converter" not in err:
            # Write to script log file
            self.script_logfile.write('ERROR - BCL2FastQ installation test failed.')
            # Write to system log and raise exception
            self.logger("BCL2FastQ installation test failed.", "demultiplex_fail")
            raise Exception("bcl2fastq not installed")
        else:
            # Write test success message to system log
            self.logger("BCL2FastQ installation test passed.", "demultiplex_success")

    def smartsheet_demultiplex_in_progress(self):
        """Update smartsheet to say that demultiplexing is in progress."""

        # Take current time stamp
        self.smartsheet_started ='{:%Y-%m-%d}'.format(datetime.datetime.now())

        # Uncomment this block to get the column ids for a new sheet
        ########################################################################
        # # Get all columns.
        # url=self.url+"/columns"
        # r = requests.get(url, headers=self.headers)
        # response= r.json()
        #
        # # get the column ids
        # for i in response['data']:
        #     print i['title'], i['id']
        ########################################################################

                    

        # create a json object that is used to inserted row into  into smartsheet
        payload = '{"cells": [{"columnId": ' + self.ss_title + ', "value": "' + self.runfolder + '"}, {"columnId": ' + self.ss_description + \
        ', "value": "Demultiplex"}, {"columnId": ' + self.ss_samples + ', "value": ' + str(self.sample_count) + '},{"columnId": ' + self.ss_status + \
        ', "value": "In Progress"},{"columnId": ' + self.ss_priority + ', "value": "Medium"},{"columnId": ' + self.ss_assigned + \
        ', "value": "aledjones@nhs.net"},{"columnId": ' + self.ss_received + ', "value": "' + str(self.smartsheet_started) + '"}],"toBottom":true}'

        # Create url for uploading a new row
        url = self.url + "/rows"

        # Add the row using POST
        r = requests.post(url, headers=self.headers, data=payload)

        # capture the output of the POST statement to capture the id of the row that has been updated. 
        # This can be used when updating the status to complete in function smartsheet_demultiplex_complete().
        response = r.json()
        # capture the value of the row id from the json response
        self.rowid = response["result"]["id"]

        # Use response.get("") instead of response[""] to avoid KeyError if "message" missing.
        if response.get("message") == "SUCCESS":
            # Report to system log file
            self.logger("Smartsheet updated with initiation of demultiplexing for run " + self.runfolder, "smartsheet_pass")
        else:
            # Record error message to script log file
            self.script_logfile.write("smartsheet NOT updated at in progress step\n" + str(response))
            # Record failure in system logs so that an error can be reported via slack. 
            # Failure to update smartsheet is not critical as it does not stop the run being processed.
            self.logger("Smartsheet was NOT updated to say demultiplexing is in progress for run " + self.runfolder, "smartsheet_fail")


    def smartsheet_demultiplex_complete(self):
        """Update smartsheet to say demultiplexing is complete. 
        Add the completed date and calculate the duration (in days) and if met TAT.
        """
        # assign current timestamp to self.smartsheet_complete
        self.smartsheet_complete = '{:%Y-%m-%d}'.format(datetime.datetime.now())
                
        # Calculate the number of days taken (add one so if same day this counts as 1 day not 0).
        # This is the difference between now and the date received (recorded in smartsheet).
        # need to convert self.smartsheet_complete and self.smartsheet_started from string to datetime object
        duration = (datetime.datetime.strptime(self.smartsheet_complete, "%Y-%m-%d") -datetime.datetime.strptime(self.smartsheet_started, "%Y-%m-%d")).days + 1

        # Set flag to show if TAT was met. Give default value of 1, which can be changed to 0
        # if the duration exceeds the expected turnaround time.
        TAT = "1"
        # If duration is greater than 4, change TAT to 0 as this is outside the target TAT.
        if duration > config.allowed_time_for_tasks:
            TAT = "0"

        # Build payload used to update the row
        payload = '{"id":"' + str(self.rowid) + '", "cells": [{"columnId":"' + str(self.ss_duration) + '","value":"' + str(duration) + '"},{"columnId":"' \
        + str(self.ss_metTAT) + '","value":"' + TAT + '"},{"columnId":"' + str(self.ss_status) + '","value":"Complete"},{"columnId": ' + self.ss_completed + \
        ', "value": "' + str(self.smartsheet_complete) + '"}]}'

        # Build url to update row
        url = self.url + "/rows"
        update_OPMS = requests.request("PUT", url, data=payload, headers=self.headers)

        # Check the result of the update attempt
        response = update_OPMS.json()
        if response.get("message") == "SUCCESS":
            # Write to system log
            self.logger("Smartsheet updated at end of demultiplexing", "smartsheet_pass")
        else:
            # Record error message in script log file
            self.script_logfile.write("smartsheet NOT updated at complete step\n" + str(response))
            # Write to system log to enable alert via slack.
            # Failure to update smartsheet is not critical as it does not stop the run being processed.
            self.logger("Smartsheet NOT updated at end of demultiplexing for run " + self.runfolder, "smartsheet_fail")


    def logger(self, message, tool):
        """Write log messages to the system log.
        Arguments:
        message (str)
            Details about the logged event. 
        tool (str)
            Tool name. Used to search within the insight ops website.
        """
        # Create subprocess command string, passing message and tool name to the command
        log = "/usr/bin/logger -t %s '%s'" % (tool, message)
        
        if subprocess.call([log],shell=True) == 0:
            # If the log command produced no errors, record the log command string to the script logfile.
            self.script_logfile.write("Log written - " + tool + ": "+ message + "\n")
        # Else record failure to write to system log to the script log file
        else:
            self.script_logfile.write("Failed to write log to /usr/bin/logger\n" + log + "\n")


    def prepare_integrity_check(self):
        """
        We want to ensure the runfolder which was copied to the workstation hasn't been corrupted by the transfer.
        This is only possible for the NextSeq.
        Checksums are generated by a script running on the sequencer and these are assessed by this script.
        
        For nextseq runs the presence of the file containing the checksums is assessed.
        If the checksums are not present the script is stopped and it will be re-assessed the next time the script is run.
        This is recorded in the system log so an alert can be made if the checksums are not present after a number of hours        
        If the checksums are present these are read into a list and compared. If they match the function returns True and the script will proceed, else the script will return False and stop
        Records are written to the logfile and to the sys.log
        
        test runs (starting with 999999) will not exist on the sequencer so this step is skipped.
        """
        
        # write to log file to say integrity checking is being performed
        self.script_logfile.write("Data integrity checks starting...\n")

         # test runfolders (starting with 999999) won't exist on the sequencer. Therefore if it is a test folder return true, skipping any integrity checks (the function of the integrity check has already been tested)
        if self.runfolder.startswith('999999'):
            # write to the logfile that this runfolder is a test one so integrity check not being performed
            self.script_logfile.write("test run identified. This run folder is not on any sequencer so skipping integrity check\n")
            # return True to report integrity checking has passed
            return True
        
        # if it's not a nextseq run return true to continue without integrity check
        elif "NB551068" not in self.runfolder:
            self.script_logfile.write("MiSeq run identified. Integrity test not possible.\n")
            # return True to report integrity checking has passed
            return True

        # now have determined is a NextSeq run set the path to the checksum file
        # checksum file should have been written to the runfolder on the workstation by sequencer_checksum.py
        checksum_file_path = os.path.join(self.runfolderpath, config.md5checksum_name)

        
        # It's possible that the checksums file has not yet ben created - test if the file exist and if not wait 5 minutes (300 secs)
        # create a count to only wait 60 mins (it usually takes < 20 mins)
        time_count = 0
        while not os.path.isfile(checksum_file_path):
            # if we have waited an hour
            if time_count > 11:
                # checksums have taken a lot longer than expected - send an error message
                self.logger("integrity check not performed by NextSeq in expected timeframe for" + self.runfolder + ". Please ensure script is running on NextSeq", "demultiplex_fail")
                # write to log file
                self.script_logfile.write("Integrity check not performed on NextSeq in expected time frame. stopping....\n")
                #and return false to stop the script
                return False
            else:
                #write to script that we are waiting
                self.script_logfile.write("md5checksums not yet performed by nextseq. waiting 5 mins...\n")
                # increase time count
                time_count += 1
                # sleep for 5 mins
                time.sleep(300)
        

        # To ensure that the checksum has not already been checked - open the file containing the md5 checksums
        with open(checksum_file_path, 'r') as checksum_file:
            # read the checksum file into a list
            checksums = checksum_file.readlines()
        
        #assess last line in file (last element in list) to see if the flag which denotes checksum test has already been performed is present.
        if config.checksum_complete_flag in checksums[-1]:
            # if integrity check already reported write to sys.log that this has been seen
            self.logger("already reported failed integrity check " + self.runfolder, "demultiplex_fail")
            # return false to report integrity check not passed
            return False
        
        # if integrity check not yet performed perform it.
        else:    
            # pass checksum file path to function which compares checksums. function returns true if the checksums match
            if self.check_checksums(checksum_file_path):
                # write to sys log
                self.logger("integrity check of runfolder " + self.runfolder + " passed", "demultiplex_success")
                # return True to report integrity checking has passed
                return True
            # if md5checksums do not match send an email
            else:
                # send an email as it's very urgent
                self.email_subject = "MOKAPIPE ALERT: INTEGRITY CHECK FAILED"
                self.email_priority = 1
                self.email_message = "run:\t" + self.runfolder + "\nsequencer checksum =" + self.sequencer_checksum + "\n" \
                                    + "workstation checksum =" + self.workstation_checksum + "\n" \
                                    + "Please follow the protocol for when integrity checks fail"
                self.send_an_email()
        
                # record test failed in sys log
                self.logger("Integrity check fail. checksums do not match for " + self.runfolder + "see " + checksum_file_path, "demultiplex_fail")
                # return false to stop the script, saying integrity checking has not been completed      
                return False

            

    def check_checksums(self, checksum_file_path):
        """
        This function receives the path to a file which should contain the checksums for both copies of a run folder.
        Each line contains the checksum and some information about the folder which that checksum relates to
        The checksums are extracted from the lines and compared
        If they match the function returns true else it returns false.
        All error reporting is done outside this function
        """
        # open the file containing the md5 checksums
        with open(checksum_file_path, 'r') as checksum_file:
            # read the checksums into a list
            checksums = checksum_file.readlines()
        # each line contains the location of each checksum with an equals sign and then the checksum.
        # split on equals to capture just the checksum (and remove any new line characters incase they result in a differenece)
        self.workstation_checksum = checksums[0].split("=")[1].rstrip()
        self.sequencer_checksum = checksums[1].split("=")[1].rstrip()
        
        # Should the test fail the script will stop here but it will continue to reach this point every hour. 
        # open the file containing the md5 checksums as write, which  will overwrite the file
        with open(checksum_file_path, 'a') as checksum_file:
            # Add a flag into the checksum file which will stop it getting this far
            checksum_file.write(config.checksum_complete_flag)

        # if the checksums match
        if self.workstation_checksum == self.sequencer_checksum:
            # if md5checksums match return to say test passed
            return True
        else:
            #otherwise return false
            return False


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # Process all runfolders
    runs.loop_through_runs()

