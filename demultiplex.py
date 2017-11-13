"""
Demultiplex NGS Run Folders

This script runs bcl2fastq on newly completed NGS run folders in a specific directory. Sequencing is
deemed complete by the presence of a file ("RTAComplete.txt"), which is created by the sequencer
when the run is ready for demultiplexing. A sample sheet must be present in the samplesheets folder
with the name "RUN_samplesheet.csv", where "RUN" is the name of the run folder.

Before demultiplexing, the script checks for the absence of the log file "demultiplex_log.txt" in
the run folder. bcl2fastq stdout and stderr streams are written to this file, which when present
indicates that demultiplexing is in process or has already been performed.
"""

__version__ = "1.0"

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

from automate_demultiplex_config import *


class get_list_of_runs():
    """Loop through and process NGS runfolders in a given directory.

    Methods defined here:

    loop_through_runs()
        Pass each runfolder to an instance of ready2start_demultiplexing().
    combine_log_files()
        Merge log files for runfolders demultiplexed in the same cycle.

    A single class instance is required to demultiplex all NGS runfolders. Example:
    >>> runs = get_list_of_runs()
    >>> runs.loop_through_runs()
    """

    def __init__(self):
        #!!! self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        # self.runfolders points to the location of runfolders on the workstation,
        # its value here must be the same as in ready2start_demultiplexing().
        self.runfolders ="/media/data1/share"
        self.now="" # Stores time stamp for log file

    def loop_through_runs(self):
        """Pass NGS run folders to an instance of ready2start_demultiplexing() for processing.
        After demultiplexing is performed (or skipped) for all runfolders, combine log files.
        """
        # Set a time stamp to append to the logfile name
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))

        # List all files and folders in the runfolder directory
        all_runfolders = os.listdir(self.runfolders)

        # Create a class instance for checking and running demultiplexing on each runfolder
        demultiplex = ready2start_demultiplexing()

        # Loop through directory listing, ignoring items named "samplesheets" or "GlacierTest".
        # Pass directories to demultiplex.already_demultiplexed()
        for folder in all_runfolders:
            if folder != "samplesheets" or folder != "GlacierTest":
                if os.path.isdir(self.runfolders+"/"+folder): # Select directories only
                    demultiplex.already_demultiplexed(folder, self.now)

        # Call function to combine log files
        self.combine_log_files()

    def combine_log_files(self):
        """Merge log files for runfolders processed by an instance of get_list_of_runs()."""
        count=0
        list_of_logfiles=[]

        # Loop through files in the log file directory
        for file in os.listdir(ready2start_demultiplexing().script_logfile_path):
            # Look for time-stamp (self.now) in filename
            if fnmatch.fnmatch(file,self.now+'*'):
                # Increment count of logfiles
                count=count+1
                # Append log file path to list_of_logfiles
                list_of_logfiles.append(ready2start_demultiplexing().script_logfile_path+file)

        if count > 1: # Continue if more than 1 log file found
            # Create a string of all log file names in list_of_log files, excluding the file with
            # the longest name
            longest_name=max(list_of_logfiles, key=len)
            list_of_logfiles.remove(longest_name)
            remaining_files=" ".join(list_of_logfiles)

            # Set shell command strings. Append all log files to the log file with the longest name
            # and delete appended files
            cmd = "cat " + remaining_files + " >> " + longest_name.replace(".txt","_demultiplexing_log.txt")
            rmcmd= "rm " + remaining_files
            # Run commands
            proc = subprocess.call([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            proc = subprocess.call([rmcmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)


class ready2start_demultiplexing():
    """Call bcl2fastq on runfolders after asserting that runfolder has not been demultiplexed and a
    valid samplesheet is present.

    Methods defined here:

    already_demultiplexed(runfolder, now)
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
    send_an_email()
        Send progress messages via email.
    test_bcl2fastq()
        Raise exception if bcl2fastq is not installed.
    smartsheet_demultiplex_in_progress()
        Update smartsheet to say that demultiplexing is in progress.
    smartsheet_demultiplex_complete()
        Update smartsheet to say that demultiplexing is complete.
    logger()
        Write log messages to the system log.
    """

    def __init__(self):
        #!!! self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        # self.runfolders points to the location of runfolders on the workstation,
        # its value here must be the same as in get_list_of_runs().
        self.runfolders ="/media/data1/share"

        # Samplesheet folder
        self.samplesheets = self.runfolders + "/samplesheets"
        # File which denotes the end of a sequencing run
        self.complete_run = "RTAComplete.txt"
        # File which denotes demultiplexing is under way or complete
        self.demultiplexed = "demultiplexlog.txt"

        # Empty variables to be defined based on the run
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.list_of_samplesheets=[]

        # Path to bcl2fastq
        self.bcl2fastq = bcl2fastq

        # Succesful run message
        self.logfile_success="Processing completed with 0 errors and 0 warnings."

        # Bcl2fastq test file
        self.bcltest= "/home/mokaguys/Documents/automate_demultiplexing_logfiles/bcl2fastq.txt"

        #!!! self.script_logfile_path="/home/aled/Documents/automate_demultiplexing_logfiles/logrecord.txt" # aled pc
        # Log file path and name
        self.script_logfile_path="/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files/"
        self.logfile_name=""

        # Email server settings
        self.user = 'AKIAIO3XY2MMSBEQNNXQ'
        self.pw   = '***REMOVED***'
        self.host = 'email-smtp.eu-west-1.amazonaws.com'
        self.port = 587
        self.me   = 'gst-tr.mokaguys@nhs.net'
        self.you  = ('gst-tr.mokaguys@nhs.net',)
        self.smtp_do_tls = True

        # Email message variables
        self.email_subject=""
        self.email_message=""
        self.email_priority=3

        # Variables for renaming the log file
        self.rename=""
        self.name=""
        self.now=""

        # Smartsheet config
        # =================
        # API key
        self.api_key="***REMOVED***"
        # Smartsheet id
        self.sheetid=2798264106936196
        # New row variable
        self.rowid=""
        # Time stamp
        self.smartsheet_now=""
        # Column ids
        self.ss_title=str(6197963270711172)
        self.ss_description=str(3946163457025924)
        self.ss_samples=str(957524288530308)
        self.ss_status=str(8449763084396420)
        self.ss_priority=str(4790588387157892)
        self.ss_assigned=str(2538788573472644)
        self.ss_received=str(6723667267741572)
        self.ss_completed=str(4471867454056324)
        self.ss_duration=str(6519775204534148)
        self.ss_metTAT=str(4267975390848900)
        # Requests info
        self.headers={"Authorization": "Bearer "+self.api_key,"Content-Type": "application/json"}
        self.url='https://api.smartsheet.com/2.0/sheets/'+str(self.sheetid)

        # Log command
        self.echo_to_log="echo %s 2>&1 | /usr/bin/logger -t %s"

    def already_demultiplexed(self, runfolder, now):
        """Check if the runfolder has been demultiplexed. This is denoted by the presence of the
        file "demultiplex_log.txt". If the runfolder has not been demultiplexed, call
        ready2start_demultiplexing.has_run_finished() to proceed.

        Arguments
        runfolder - A string containing the runfolder name
        now - A string containing the time stamp for this cycle's script log file
        """
        # Timestamp (string)
        self.now=now

        # Open the logfile for this hour's cron job (script log file).
        self.logfile_name=self.script_logfile_path+self.now+".txt"
        self.script_logfile=open(self.logfile_name,'a')

        # Capture the runfolder and its path
        self.runfolder = str(runfolder)
        self.runfolderpath = self.runfolders + "/" + self.runfolder

        # Write to log file
        self.script_logfile.write("automate_demultiplexing release:"+script_release+"\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\nAssessing......... " + self.runfolderpath+"\n")

        # If the demultiplex log file is present
        if os.path.isfile(self.runfolderpath + "/" + self.demultiplexed):
            # Stop script and write to log file
            self.script_logfile.write("Checking if already demultiplexed .........Demultiplexing has already been completed  -  demultiplex log found @ "+self.runfolderpath + "/" + self.demultiplexed+" \n--- STOP ---\n")
        else:
            # Else proceed
            self.script_logfile.write("Checking if already demultiplexed .........Run has not yet been demultiplexed\n")
            self.has_run_finished()

    def has_run_finished(self):
        """Check if sequencing has completed for the current runfolder. This is denoted by the
        presence of the file "RTAComplete.txt". If sequencing is complete, call
        ready2start_demultiplexing.look_for_sample_sheet() to proceed.
        """
        # Check if the RTAcomplete.txt file is present
        if os.path.isfile(self.runfolderpath + "/" + self.complete_run):
            self.script_logfile.write("Run has finished  -  RTAcomplete.txt found @ "+ self.runfolderpath + "/" + self.complete_run+"\n")
            # If so proceed
            self.look_for_sample_sheet()
        else:
            # Else stop
            self.script_logfile.write("run is not yet complete \n--- STOP ---\n")

    def look_for_sample_sheet(self):
        """Check that the sample sheet for the current runfolder is present."""
        # Set the name and path of the sample sheet to find
        self.samplesheet=self.samplesheets + "/" + self.runfolder + "_SampleSheet.csv"

        # Get an uppercase list of samplesheets in the samplesheets folder
        all_runfolders = os.listdir(self.samplesheets)
        for samplesheet in all_runfolders:
            self.list_of_samplesheets.append(samplesheet.upper())

        # Set the expected samplesheet name in uppercase
        expected_samplesheet = self.runfolder.upper() + "_SAMPLESHEET.CSV"
        # Check that the expected samplesheet exists
        if expected_samplesheet in self.list_of_samplesheets:
            self.script_logfile.write("Looking for a samplesheet .........samplesheet found @ " +self.samplesheet+"\n")
            #!!!# Send an email:2
            #!!! self.email_subject="MOKAPIPE ALERT: Demultiplexing initiated"
            #!!! self.email_message="demultiplexing for run " + self.runfolder + " has been initiated"
            #!!! self.send_an_email()
            #!!! proceed
            # If the samplesheet contains valid characters, run demultiplexing
            if self.check_valid_samplesheet():
                self.script_logfile.write("Checking for invalid characters in 'Sample_ID' and 'Sample_Name' columns " + \
                                        "......... All characters valid \n")
                self.run_demuliplexing()
            # Else stop and write error message to logger.
            else:
                self.script_logfile.write("Checking for invalid characters in 'Sample_ID' and 'Sample_Name' columns" + \
                                        "......... Invalid characters found \n--- STOP ---\n")
                self.logger("Invalid characters persent in samplesheet. Demultiplexing not started for run " + \
                    self.runfolder,"demultiplex_invalid_samplesheet_character")
        else:
            # stop
            self.script_logfile.write("Looking for a samplesheet ......... no samplesheet present \n--- STOP ---\n")
            self.logger("no samplesheet found demultiplexing not started for run "+self.runfolder,"demultiplex_no_sample_sheet_present")

    def check_valid_samplesheet(self):
        '''Validate the 'Sample_ID' and 'Sample_Name' table columns within the sample sheet csv
        file. The presence of invalid characters in these columns raises an error in bcl2fastq2.
        Return True if no invalid characters found.
        '''
        # Create empty list to store sample ids and sample names from the samplesheet
        sampleStrings = []

        # Set a string containing valid characters, defined by bcl2fastq as an alphanumeric, '-', or '_' character.
        validChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        # Separate characters into a set for quick lookup
        validCharSet = set(validChars.split())

        # Open samplesheet and loop through in reverse order.
        with open(self.samplesheet,'r') as samplesheetIOstream:
            for line in reversed(samplesheetIOstream.readlines()):
                # If the line contains table headers, stop looping through the file
                 if line.startswith("Sample_ID"):
                    break
                 else:
                    # Split the current line of the csv, with commas as the delimiter
                    columns = line.split(",")
                    # Remove leading and trailing whitespace from sampleID and sampleName.
                    # bcl2fastq tolerates leading and trailing whitespace.
                    sampleId, sampleName = columns[0].strip(" "), columns[1].strip(" ")
                    # Append sample id and sample name to sampleStrings for testing
                    sampleStrings.append(sampleId)
                    sampleStrings.append(sampleName)

        # Loop through the characters of each sample name and id
        for sampleString in sampleStrings:
            for char in sampleString:
                # Check that each character in the string is valid, returning True if valid and False if not
                if char not in validChars:
                    return False
        else:
            return True

    def run_demuliplexing(self):
        """Run bcl2fastq using runfolder as input. Create demultiplex log file in runfolder."""

        # Test bcl2fastq is installed
        self.test_bcl2fastq()
        # Update smartsheet
        self.smartsheet_demultiplex_in_progress()

        # Set a string with the shell command to run demultiplexing
        # Example command: "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq
        # -R 160822_NB551068_0006_AHGYM7BGXY/
        # --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv
        # --no-lane-splitting"
        command = self.bcl2fastq + " -R " + self.runfolders+"/"+self.runfolder + " --sample-sheet " + self.samplesheet + " --no-lane-splitting"

        # Write to script log file
        self.script_logfile.write("running bcl2fastq ......... \ncommand = " + command+"\n")

        # Open a demultiplex log file in the current runfolder
        demultiplex_log = open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'w')

        # Add entry to system log
        self.logger("demultiplexing started for run "+self.runfolder,"demultiplex_started")

        # Run the command, redirecting the stderror stream to stdout
        proc = subprocess.Popen([command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)

        # Capture and write the streams to the runfolder's demultiplex log file
        # Note: stderr is redirected to stdout
        (out, err) = proc.communicate()
        demultiplex_log.write(out)
        demultiplex_log.close()

        # Call method to check the success of demultiplexing
        self.check_demultiplexlog_file()

    def check_demultiplexlog_file(self):
        """Check demultiplexing completed successfully."""
        # Open the runfolder's demultiplex log file
        logfile=open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'r')

        # Store the contents and line number of the last line in the log file.
        # This line details the success or failure of the bcl2fastq command.
        count=0
        lastline=""
        for i in logfile:
            count=count+1
            lastline=i

        # If demultiplexing completed successfully
        if  self.logfile_success in lastline:
            #!!! self.email_subject="MOKAPIPE ALERT: Demultiplexing complete"
            #!!! self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed
            #!!! self.send_an_email()
            #!!! Write to script log file
            self.script_logfile.write("demultiplexing complete\n")
            # Write to system log
            self.logger("demultiplexing complete without error for run "+self.runfolder,"demultiplex_success")
            # Update smartsheet
            self.smartsheet_demultiplex_complete()
            # Close script log file
            self.script_logfile.close()
            # Set a variable with the name of the current runfolder
            self.rename=self.rename+self.runfolder
            # Append the name of the processed runfolder to the name of the script log file.
            # Each runfolder passed to ready2start_demultiplexing.already_demultiplexed() opens a
            # script log file with the same time stamp, which is renamed here after processing.
            os.rename(self.logfile_name,self.script_logfile_path+self.now+"_"+self.rename+".txt")

        else:
            #!!! self.email_subject="MOKAPIPE ALERT: DEMULTIPLEXING FAILED"
            #!!! self.email_priority=1
            #!!! self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed
            #!!! self.send_an_email()
            # Write to log file
            self.script_logfile.write("ERROR - DEMULTIPLEXING UNSUCCESFULL - please see "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed+"\n")
            # Write to system log
            self.logger("demultiplexing completed with error or failed for run "+self.runfolder,"demultiplex_fail")

    def send_an_email(self):
        """Send progress log messages via email to recipient (self.you) via SMTP."""
        #!!! body = self.runfolder
        #!!! msg  = 'Subject: %s\n\n%s' % (self.email_subject, self.email_message)
        #!!! m['From'] = self.me
        #!!! m['To'] = self.you

        # Write to script log file
        self.script_logfile.write("Sending an email to..... " +self.me)

        # Create email.Message() object. Set e-mail headers for X-Priority and Subject
        m = Message()
        m['X-Priority'] = str(self.email_priority)
        m['Subject'] = self.email_subject
        # Add error messages to e-mail body using email.Message.set_payload()
        m.set_payload(self.email_message)

        # Configure SMTP server connection for sending log messages via e-mail
        server = smtplib.SMTP(host = self.host,port = self.port,timeout = 10)
        # Output connection debug messages
        server.set_debuglevel(1)
        # Encrypt SMTP commands using Transport Layer Security mode
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
        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # Capture the streams
        (out, err) = proc.communicate()

        # If bcl2fastq is installed and called with no inputs, the first line of stderr should
        # contain the string "BCL to FASTQ file converter".
        if "BCL to FASTQ file converter" not in err:
            #!!! self.email_subject="MOKAPIPE ALERT: ERROR - PRESENCE OF BCL2FASTQ TEST FAILED"
            #!!! self.email_priority=1
            #!!! self.email_message="The test to check if bcl2fastq is working ("+command+") failed"
            #!!! self.send_an_email()
            # Write to system log and raise exception
            self.logger("BCL2FastQ installation test failed","demultiplex_BCL2FASTQ_function_test_fail")
            raise Exception, "bcl2fastq not installed"
        else:
            # Write to system log
            self.logger("BCL2FastQ installation test ok","demultiplex_BCL2FASTQ_function_test_pass")

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

        # Capture the NGS run number and increment count
        count = 0
        with open(self.samplesheet,'r') as samplesheet:
            for line in samplesheet:
                if line.startswith("NGS") or line.startswith("ONC"):
                    count=count+1
                    runnumber=line.split("_")[0]

        # Set all values to be inserted into smartsheet
        payload='{"cells": [{"columnId": '+self.ss_title+', "value": "'+self.runfolder+'"}, {"columnId": '+self.ss_description+', "value": "Demultiplex"}, {"columnId": '+self.ss_samples+', "value": '+str(count)+'},{"columnId": '+self.ss_status+', "value": "In Progress"},{"columnId": '+self.ss_priority+', "value": "Medium"},{"columnId": '+self.ss_assigned+', "value": "aledjones@nhs.net"},{"columnId": '+self.ss_received+', "value": "'+str(self.smartsheet_now)+'"}],"toBottom":true}'

        # Create url for uploading a new row
        url=self.url+"/rows"

        # Add the row using POST
        r = requests.post(url,headers=self.headers,data=payload)

        # Capture the row id
        response= r.json()
        print response
        for i in response["result"]:
            if i == "id":
                self.rowid=response["result"][i]

        # Check the result of the update attempt
        for i in response:
            if i == "message":
                if response[i] =="SUCCESS":
                    self.script_logfile.write("smartsheet updated to say in progress\n")
                    self.logger("initiation of demultiplexing added to smartsheet","smartsheet_demultiplex_started_update_ok")
                else:
                    #!!! #send an email if the update failed
                    #!!! self.email_subject="MOKAPIPE ALERT: SMARTSHEET WAS NOT UPDATED"
                    #!!! self.email_message="Smartsheet was not updated to say demultiplexing is inprogress"
                    #!!! self.send_an_email()
                    self.script_logfile.write("smartsheet NOT updated at in progress step\n"+str(response))
                    self.logger("Smartsheet was not updated to say demultiplexing is in progress for run "+self.runfolder,"smartsheet_demultiplex_started_update_fail")

    def smartsheet_demultiplex_complete(self):
        """Update smartsheet to say demultiplexing is complete. Add the completed date and calculate
        the duration (in days) and if met TAT.
        """
        # Build URL to read a row
        url='https://api.smartsheet.com/2.0/sheets/'+str(self.sheetid)+'/rows/'+str(self.rowid)
        # Get row
        r = requests.get(url, headers=self.headers)
        # Read response in json
        response= r.json()
        # Loop through each column and extract the recieved date
        for col in response["cells"]:
            if str(col["columnId"]) == self.ss_received:
                recieved=datetime.datetime.strptime(col['value'], '%Y-%m-%d')

        # Take current timestamp
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))
        now=datetime.datetime.strptime(self.smartsheet_now, '%Y-%m-%d')

        # Calculate the number of days taken (add one so if same day this counts as 1 day not 0)
        duration = (now-recieved).days+1

        # Set flag to show if TAT was met.
        TAT=1
        if duration > 4:
            TAT=0

        # Build payload used to update the row
        payload = '{"id":"'+str(self.rowid)+'", "cells": [{"columnId":"'+ str(self.ss_duration)+'","value":"'+str(duration)+'"},{"columnId":"'+ str(self.ss_metTAT)+'","value":"'+str(TAT)+'"},{"columnId":"'+ str(self.ss_status)+'","value":"Complete"},{"columnId": '+self.ss_completed+', "value": "'+str(self.smartsheet_now)+'"}]}'

        # Build url to update row
        url=self.url+"/rows"
        update_OPMS = requests.request("PUT", url, data=payload, headers=self.headers)

        # Check the result of the update attempt
        response= update_OPMS.json()
        print response
        for i in response:
            if i == "message":
                if response[i] =="SUCCESS":
                    self.script_logfile.write("smartsheet updated to say complete\n")
                    self.logger("smartsheet updated at end of demultiplexing","smartsheet_demultiplex_complete_update_ok")
                else:
                    #!!! #send an email if the update failed
                    #!!! self.email_subject="MOKAPIPE ALERT: SMARTSHEET WAS NOT UPDATED"
                    #!!! self.email_message="Smartsheet was not updated to say demultiplexing was completed"
                    #!!! self.send_an_email()
                    self.script_logfile.write("smartsheet NOT updated at complete step\n"+str(response))
                    self.logger("smartsheet NOT updated at end of demultiplexing for run "+self.runfolder,"smartsheet_demultiplex_complete_update_fail")

    def logger(self, message, tool):
        """Write log messages to the system log."""
        # Create subprocess command
        log=self.echo_to_log % (message,tool)
        # Run the command
        proc = subprocess.Popen([log], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        # Capture the streams
        (out, err) = proc.communicate()
        # Write output to log file if no stderr
        if not err:
            self.script_logfile.write("log written to /usr/bin/logger\n"+log+"\n")


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # Process all runfolders
    runs.loop_through_runs()
