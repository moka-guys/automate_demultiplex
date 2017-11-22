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
from email.Message import Message
import fnmatch
import requests
import json

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

        # Loop through directory listing and pass runfolders to demultiplex.already_demultiplexed()
        for folder in all_runfolders:
            # Ignore folders in the list config.ignore_directories
            if folder not in config.ignore_directories:
                if os.path.isdir(self.runfolders + "/" + folder):  # Select directories only
                    demultiplex.already_demultiplexed(folder)

        # Close the script log file when all processing is complete
        demultiplex.script_logfile.close()


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
        self.me = config.me
        self.you = config.you
        self.smtp_do_tls = config.smtp_do_tls

        # Smartsheet config
        # =================
        # API key
        self.api_key = config.smartsheet_api_key
        # Smartsheet id
        self.sheetid = config.smartsheet_sheetid
        # New row variable
        self.rowid = ""
        # Time stamp
        self.smartsheet_now = ""
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
            # Stop script and write to log file
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
            # Call function which returns true if the sample sheet does not contain illegal characters
            if self.check_valid_samplesheet():
                # If the samplesheet contains valid characters, run demultiplexing
                self.script_logfile.write("Checking for invalid characters in 'Sample_ID' and 'Sample_Name' columns " +
                                          "......... All characters valid \n")
                self.run_demuliplexing()
            # Else stop and write error messages to loggers and send error e-mail.
            else:
                # Set error message details for invalid characters found
                invalid_char_message = ("Invalid characters persent in samplesheet.\n" +
                                        "Demultiplexing not started for run " + self.runfolder + ".\n"
                                        "Valid characters are defined by bcl2fastq as an alphanumeric," +
                                        " '-', or '_' character. \n")
                invalid_char_subject = "demultiplex_invalid_samplesheet_character"
                # Write error event to script log file
                self.script_logfile.write("Checking for invalid characters in 'Sample_ID' and 'Sample_Name' columns" +
                                          "......... Invalid characters found \n--- STOP ---\n")
                # Record error messages in system log
                self.logger(invalid_char_message, invalid_char_subject)
                # Send an e-mail. This necessary as the samplesheet must now be checked and fixed.
                # The samplesheet generator should also be checked as subsequent runs may be affected
                self.send_an_email(invalid_char_message, invalid_char_subject)

        else:
            # No samplesheet found. Stop and log message.
            self.script_logfile.write("Looking for a samplesheet ......... no samplesheet present \n--- STOP ---\n")
            self.logger("no samplesheet found demultiplexing not started for run " + self.runfolder, "demultiplex_no_sample_sheet_present")

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

        # Open samplesheet and loop through in reverse order.
        with open(self.samplesheet, 'r') as samplesheet_stream:
            for line in reversed(samplesheet_stream.readlines()):
                # If the line contains table headers, stop looping through the file
                if line.startswith("Sample_ID"):
                    break
                else:
                    # Split the current line of the csv, with commas as the delimiter
                    columns = line.split(",")
                    # Remove leading and trailing whitespace from sampleID and sampleName.
                    # bcl2fastq tolerates leading and trailing whitespace.
                    sample_id, sample_name = columns[0].strip(" "), columns[1].strip(" ")
                    # Append sample id and sample name to sampleStrings for testing
                    sample_strings.append(sample_id)
                    sample_strings.append(sample_name)

        # Loop through the characters of each sample string
        for sample_string in sample_strings:
            for char in sample_string:
                # Check that each character in the string is valid, returning True if valid and False if not
                if char not in valid_chars:
                    return False
        else:
            return True

    def run_demuliplexing(self):
        """Run bcl2fastq using runfolder as input. Create demultiplex log file in runfolder."""

        # Call function to test if bcl2fastq is installed and working as expected
        self.test_bcl2fastq()
        # Call function to add the run to smartsheet, with status set to 'in progress'
        self.smartsheet_demultiplex_in_progress()

        # Set demultiplex log file name for this runfolder.
        demultiplex_log = (self.runfolders + "/" + self.runfolder + "/" + self.demultiplexed)

        # Set a string with the shell command to run demultiplexing.
        # The command writes bcl2fastq stdout and stderr to the demultiplex_log file.
        # The presence of this file stops future re-processing of the runfolder.
        # Example: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
        #           -R 160822_NB551068_0006_AHGYM7BGXY/
        #           --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
        #           --no-lane-splitting >> 
        #           /media/data1/share/1111_M02353_NMNOV17_ONCTEST/demultiplexlog.txt 2&>1"
        command = (self.bcl2fastq + " -R " + self.runfolders + "/" + self.runfolder + 
                  " --sample-sheet " + self.samplesheet + " --no-lane-splitting >> " +
                  demultiplex_log + " 2>&1")

        # Write progress/status to script log file
        self.script_logfile.write("running bcl2fastq ......... \ncommand = " + command + "\n")
        # Add entry to system log
        self.logger("demultiplexing started for run " + self.runfolder, "demultiplex_started")

        # Run the bcl2fastq command to start demultiplexing. Redirects stderr to stdout so that any 
        # standard error can be captured in the log file.
        subprocess.call([command], shell=True)

        # Call method to check the success of demultiplexing
        self.check_demultiplexlog_file()

    def check_demultiplexlog_file(self):
        """Check demultiplexing completed successfully. Read the stderr and stdout from bcl2fastq in
        the demultiplex log file, searching the last line for the expected success statement.
        """
        
        # Succesful run message. A string to look for in the output of bcl2fastq which denotes 
        # succesful demultiplexing.
        logfile_success = "Processing completed with 0 errors and 0 warnings."

        # Read the last line of the runfolder's demultiplex log file, which details the success or 
        # failure of the bcl2fastq command.
        run_logfile_path = self.runfolderpath + "/" + self.demultiplexed
        lastline = subprocess.check_output(["tail","-n", "1", run_logfile_path])
        # Record last 10 lines of logfile to append to script log in case of error
        bcl2fastq_error_tail = subprocess.check_output(["tail","-n","10", run_logfile_path])

        # If demultiplexing completed successfully
        if logfile_success in lastline:
            # Write to script_logfile
            self.script_logfile.write("demultiplexing complete\n")
            # Write to system log
            self.logger("demultiplexing complete without error for run " + self.runfolder, "demultiplex_success")
            # Call function which updates smartsheet, changing status for this run from in progress to complete, where task = demultiplex.
            self.smartsheet_demultiplex_complete()
        # If demultiplexing did not complete without errors
        else:
            # Write to log file and report last few lines of the failed runfolder's demultiplex log.
            self.script_logfile.write("ERROR - DEMULTIPLEXING UNSUCCESFULL - please see " + 
                                      run_logfile_path + "\n" + bcl2fastq_error_tail )
            # Write to system log
            self.logger("demultiplexing completed with error or failed for run " + self.runfolder, "demultiplex_fail")

    def send_an_email(self, m_message, m_subject):
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
        m['X-Priority'] = str(3)
        m['Subject'] = m_subject
        # Add error messages to e-mail body using email.Message.set_payload()
        m.set_payload(m_message)

        # Configure SMTP server connection for sending log messages via e-mail
        server = smtplib.SMTP(host=self.host, port=self.port, timeout=10)
        # Output connection debug messages
        server.set_debuglevel(1)
        # Encrypt SMTP commands using Transport Layer Security mode
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
        # Call bcl2fastq executeable with no inputs
        command = self.bcl2fastq
        # Execute the bcl2fastq command
        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # Capture the streams
        (out, err) = proc.communicate()

        # If bcl2fastq is installed and called with no inputs, the first line of stderr should
        # contain the string "BCL to FASTQ file converter".
        if "BCL to FASTQ file converter" not in err:
            # Write to system log and raise exception
            self.logger("BCL2FastQ installation test failed", "demultiplex_BCL2FASTQ_function_test_fail")
            raise Exception("bcl2fastq not installed")
        else:
            # Write to system log
            self.logger("BCL2FastQ installation test ok", "demultiplex_BCL2FASTQ_function_test_pass")

        # Write to script log file
        self.script_logfile.write("bcl2fastq check passed\n")

    def smartsheet_demultiplex_in_progress(self):
        """Update smartsheet to say that demultiplexing is in progress."""

        # Take current time stamp
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))

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

        # Read the sample sheet, capture the NGS run number and count the number of samples on the run.
        count = 0
        with open(self.samplesheet, 'r') as samplesheet:
            for line in samplesheet:
                if line.startswith("NGS") or line.startswith("ONC"):
                    count = count + 1
                    runnumber = line.split("_")[0]

        # Set all values to be inserted into smartsheet
        payload = '{"cells": [{"columnId": ' + self.ss_title + ', "value": "' + self.runfolder + '"}, {"columnId": ' + self.ss_description + ', "value": "Demultiplex"}, {"columnId": ' + self.ss_samples + ', "value": ' + str(count) + '},{"columnId": ' + self.ss_status + ', "value": "In Progress"},{"columnId": ' + self.ss_priority + ', "value": "Medium"},{"columnId": ' + self.ss_assigned + ', "value": "aledjones@nhs.net"},{"columnId": ' + self.ss_received + ', "value": "' + str(self.smartsheet_now) + '"}],"toBottom":true}'

        # Create url for uploading a new row
        url = self.url + "/rows"

        # Add the row using POST
        r = requests.post(url, headers=self.headers, data=payload)

        # Parse the output of the POST statement to capture the id of the row that has been updated. 
        # This can be used when updating the status to complete in function smartsheet_demultiplex_complete().
        response = r.json()
        for i in response["result"]:
            if i == "id":
                self.rowid = response["result"][i]

        # Use response.get("") instead of response[""] to avoid KeyError if "message" missing.
        if response.get("message") == "SUCCESS":
            # Write to script log file  
            self.script_logfile.write("smartsheet updated to say in progress\n")
            # Report to system log file
            self.logger("initiation of demultiplexing added to smartsheet", "smartsheet_demultiplex_started_update_ok")
        else:
            # Record error message to script log file
            self.script_logfile.write("smartsheet NOT updated at in progress step\n" + str(response))
            # Record failure in system logs so that an error can be reported via slack. 
            # Failure to update smartsheet is not critical as it does not stop the run being processed.
            self.logger("Smartsheet was not updated to say demultiplexing is in progress for run " + self.runfolder, "smartsheet_demultiplex_started_update_fail")

    def smartsheet_demultiplex_complete(self):
        """Update smartsheet to say demultiplexing is complete. Add the completed date and calculate
        the duration (in days) and if met TAT.
        """
        # Build URL to read the row using the row id captured from smartsheet_demultiplex_in_progress()
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(self.sheetid) + '/rows/' + str(self.rowid)
        # Get row
        r = requests.get(url, headers=self.headers)
        # Read response in json
        response = r.json()
        # Loop through each column and extract the received date
        for col in response["cells"]:
            if str(col["columnId"]) == self.ss_received:
                recieved = datetime.datetime.strptime(col['value'], '%Y-%m-%d')

        # Convert the current time stamp into a string in specific format. 
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))
        # Reformat time stamp to a form that allows for calculating the time taken.
        now = datetime.datetime.strptime(self.smartsheet_now, '%Y-%m-%d')
        # Calculate the number of days taken (add one so if same day this counts as 1 day not 0).
        # This is the difference between now and the date received (recorded in smartsheet).
        duration = (now - recieved).days + 1

        # Set flag to show if TAT was met. Give default value of 1, which can be changed to 0
        # if the duration exceeds the expected turnaround time.
        TAT = 1
        # If duration is greater than 4, change TAT to 0 as this is outside the target TAT.
        if duration > 4:
            TAT = 0

        # Build payload used to update the row
        payload = '{"id":"' + str(self.rowid) + '", "cells": [{"columnId":"' + str(self.ss_duration) + '","value":"' + str(duration) + '"},{"columnId":"' + str(self.ss_metTAT) + '","value":"' + str(TAT) + '"},{"columnId":"' + str(self.ss_status) + '","value":"Complete"},{"columnId": ' + self.ss_completed + ', "value": "' + str(self.smartsheet_now) + '"}]}'

        # Build url to update row
        url = self.url + "/rows"
        update_OPMS = requests.request("PUT", url, data=payload, headers=self.headers)

        # Check the result of the update attempt
        response = update_OPMS.json()
        if response.get("message") == "SUCCESS":
            # Write to script log file
            self.script_logfile.write("smartsheet updated to say complete\n")
            # Write to system log
            self.logger("smartsheet updated at end of demultiplexing", "smartsheet_demultiplex_complete_update_ok")
        else:
            # Record error message in script log file
            self.script_logfile.write("smartsheet NOT updated at complete step\n" + str(response))
            # Write to system log to enable alert via slack.
            # Failure to update smartsheet is not critical as it does not stop the run being processed.
            self.logger("smartsheet NOT updated at end of demultiplexing for run " + self.runfolder, "smartsheet_demultiplex_complete_update_fail")

    def logger(self, message, tool):
        """Write log messages to the system log.
        
        Arguments:
        message (str)
            Details about the logged event. 
        tool (str)
            Tool name. Used to search within the OPMS website.
        """
        # Create subprocess command string, passing message and tool name to the command
        log = "echo %s 2>&1 | /usr/bin/logger -t %s" % (message, tool)
        # Run the command using subprocess
        proc = subprocess.Popen([log], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        # Capture the streams
        (out, err) = proc.communicate()
        # If no standard error, record in script logfile that information was written to system log.
        if not err:
            self.script_logfile.write("log written to /usr/bin/logger\n" + log + "\n")


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # Process all runfolders
    runs.loop_through_runs()
