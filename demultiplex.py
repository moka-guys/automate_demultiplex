'''
Created on 19 Sep 2016

This script loops through all the run folders in a directory looking for any newly completed runs ready to be demultiplexed
The run is deemed complete by the presense of a files called RTAComplete.txt. This will only be created when the run is ready for demultiplexing.
A sample sheet must be present so a samplesheet with the name of the run_samplesheet.csv must be present in the samplesheets folder.
Finally a check that the demultiplexing has (or is) not already being performed.

If the run is ready for demultiplexing then a command is issued.
The stdout and stderr is written to a log file (the same file which is checked for above).

Could possibly add a check/message if it fails.
 
@author: aled
'''

import os
import subprocess
import datetime
import smtplib
from email.Message import Message
import fnmatch
import requests
import json
from checksumdir import dirhash
from automate_demultiplex_config import *

class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''
    def __init__(self):
        # directory of run folders - must be same as in ready2start_demultiplexing()
        self.runfolders ="/media/data1/share" # workstation
        self.now=""

    def loop_through_runs(self):
        #set a time stamp to name the log file
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))

        # create a list of all the folders in the runfolders directory
        all_runfolders = os.listdir(self.runfolders)

        demultiplex=ready2start_demultiplexing()
        # for each folder if it is not samplesheets pass the runfolder to the next class ready2start_demultiplexing()
        for folder in all_runfolders:
            if folder != "samplesheets" or folder != "GlacierTest":
                if os.path.isdir(self.runfolders+"/"+folder):
                    demultiplex.already_demultiplexed(folder, self.now)
        #call function to combine log files
        self.combine_log_files()

    def combine_log_files(self):
        # count number of log files that match the time stamp
        count=0
        list_of_logfiles=[]
        for file in os.listdir(ready2start_demultiplexing().script_logfile_path):
            if fnmatch.fnmatch(file,self.now+'*'):
                count=count+1
                list_of_logfiles.append(ready2start_demultiplexing().script_logfile_path+file)
        
        if count > 1:
            longest_name=max(list_of_logfiles, key=len)
            list_of_logfiles.remove(longest_name)
            remaining_files=" ".join(list_of_logfiles)

            # combine all into one file with the longest filename
            cmd = "cat " + remaining_files + " >> " + longest_name.replace(".txt","_demultiplexing_log.txt")
            rmcmd= "rm " + remaining_files

            # run the command, redirecting stderror to stdout
            proc = subprocess.call([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            proc = subprocess.call([rmcmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)


class ready2start_demultiplexing():
    '''This class checks if a run is ready to be demultiplexed (samplesheet present, run finished and not previously demultiplexed) and if so runs demultiplexes''' 
    def __init__(self):
        # directory of run folders - must be same as in get_list_of_runs()
        self.runfolders ="/media/data1/share" # workstation
        
        #set the samplesheet folders
        self.samplesheets = self.runfolders + "/samplesheets"
        # file which denotes end of a run
        self.complete_run = "RTAComplete.txt"
        # file which denotes demultiplexing is underway/complete 
        self.demultiplexed = "demultiplexlog.txt"

        # set empty variables to be defined based on the run  
        self.runfolder = ""
        self.runfolderpath = ""
        self.samplesheet = ""
        self.list_of_samplesheets=[]

        # path to bcl2fastq
        self.bcl2fastq = bcl2fastq
        #succesful run
        self.logfile_success="Processing completed with 0 errors and 0 warnings."

        #bcl2fastq test file
        self.bcltest= "/home/mokaguys/Documents/automate_demultiplexing_logfiles/bcl2fastq.txt"
        
        #logfile
        self.script_logfile_path="/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files/" # workstation
        self.logfile_name=""
        
        #email server settings
        self.user = 'AKIAIO3XY2MMSBEQNNXQ'
        self.pw   = 'AmkKC7nXvLrxsvBHZf3zagNq953nun9c0iYN+zjifIbN'
        self.host = 'email-smtp.eu-west-1.amazonaws.com'
        self.port = 587
        self.me   = 'gst-tr.mokaguys@nhs.net'
        self.you  = ('gst-tr.mokaguys@nhs.net',)
        self.smtp_do_tls = True
        
        # email message
        self.email_subject=""
        self.email_message=""
        self.email_priority=3

        #rename log file
        self.rename=""
        self.name=""
        self.now=""

        #smartsheet API
        self.api_key="3asfndq3oi2zbww3td8gb67liv"
        
        #sheet id
        self.sheetid=2798264106936196
        #newly inserted row
        self.rowid=""

        #time stamp
        self.smartsheet_now=""

        #columnIds
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

        #requests info
        self.headers={"Authorization": "Bearer "+self.api_key,"Content-Type": "application/json"}
        self.url='https://api.smartsheet.com/2.0/sheets/'+str(self.sheetid)

        # log command
        self.echo_to_log="echo %s 2>&1 | /usr/bin/logger -t %s"

    def already_demultiplexed(self, runfolder, now):
        '''check if the runfolder has been demultiplexed (demultiplex_log is present)'''
        self.now=now
        #open the logfile for this hour's cron job.
        self.logfile_name=self.script_logfile_path+self.now+".txt"
        self.script_logfile=open(self.logfile_name,'a')

        # capture the runfolder 
        self.runfolder = str(runfolder)
               
        # create full path to runfolder
        self.runfolderpath = self.runfolders + "/" + self.runfolder
        
        self.script_logfile.write("automate_demultiplexing release:"+script_release+"\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\nAssessing......... " + self.runfolderpath+"\n")
        
        # if the demultiplex log file is present
        if os.path.isfile(self.runfolderpath + "/" + self.demultiplexed):
            # stop
            self.script_logfile.write("Checking if already demultiplexed .........Demultiplexing has already been completed  -  demultiplex log found @ "+self.runfolderpath + "/" + self.demultiplexed+" \n--- STOP ---\n")
        else:
            self.script_logfile.write("Checking if already demultiplexed .........Run has not yet been demultiplexed\n")
            # else proceed
            self.has_run_finished()

    def has_run_finished(self):
        ''' check for presence of RTAComplete.txt to denote a finished sequencing run'''
        # check if the RTAcomplete.txt file is present
        if os.path.isfile(self.runfolderpath + "/" + self.complete_run):
            self.script_logfile.write("Run has finished  -  RTAcomplete.txt found @ "+ self.runfolderpath + "/" + self.complete_run+"\n")
            
            self.look_for_sample_sheet()
        else:
            # else stop 
            self.script_logfile.write("run is not yet complete \n--- STOP ---\n")
        


    def look_for_sample_sheet(self):
        '''check sample sheet is present'''
        # set name and path of sample sheet to find
        self.samplesheet=self.samplesheets + "/" + self.runfolder + "_SampleSheet.csv"
        
        # get a list samplesheets in folder
        all_runfolders = os.listdir(self.samplesheets)
        for samplesheet in all_runfolders:
            # convert all to capitals
            self.list_of_samplesheets.append(samplesheet.upper())

        # set the expected samplesheet name (convert to uppercase)
        expected_samplesheet = self.runfolder.upper() + "_SAMPLESHEET.CSV"
        
        #if the samplesheet exists
        if expected_samplesheet in self.list_of_samplesheets:
            self.script_logfile.write("Looking for a samplesheet .........samplesheet found @ " +self.samplesheet+"\n")
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
        '''
        Validates the 'Sample_ID' and 'Sample_Name' columns of the samplesheet csv file.
        The presence of invalid characters in these strings raises an error in bcl2fastq2.
        Returns True if no invalid characters found.
        '''
        # Initialise empty list to store sample ids and sample names from the samplesheet
        sampleStrings = []

        # Store string containing valid characters, defined by bcl2fastq as an alphanumeric, '-', or '_' character.
        validChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        # Separate characters into a set for quick lookup
        validCharSet = set(validChars.split())

        # Open samplesheet and loop through in reverse order. 
        with open(self.samplesheet,'r') as samplesheetIOstream:
            for line in reversed(samplesheetIOstream.readlines()):
                # If the line contains table headers for the sample names, stop looping through the file
                 if line.startswith("Sample_ID"):
                    break
                 else:
                    # Split the current line of the csv, with commas as the delimiter
                    columns = line.split(",")
                    # Remove leading and trailing whitespace from sampleID and sampleName with str.strip(),
                    # as bcl2fastq tolerates leading and trailing whitespace in sample naming strings.
                    sampleId, sampleName = columns[0].strip(" "), columns[1].strip(" ")
                    # Append sample id and sample name to sampleStrings for testing
                    sampleStrings.append(sampleId)
                    sampleStrings.append(sampleName)

        # Loop through the characters of each sample name and sample id
        for sampleString in sampleStrings:
            for char in sampleString:
                # Check that each character in the string is valid, returning True if valid and False if not
                if char not in validChars:
                    return False
        else:
            return True

    def run_demuliplexing(self):
        '''Run the demultiplexing'''
        
        #print "demultiplexing ..... "+self.runfolder
        # example command sudo /usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq -R /media/data1/share/160914_NB551068_0007_AHGT7FBGXY --sample-sheet /media/data1/share/samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv --no-lane-splitting
        
        # practice command: 
        # command = "fv samtools faidx /home/aled/Documents/Reference_Genomes/hg19.fa xfvg chr1:10000000-10000002"
        
        # test bcl2fastq install
        self.test_bcl2fastq()
        self.smartsheet_demultiplex_in_progress()

        # before demultiplexing starts check the integrity of the runfolder against that on the sequencer. Only proceed if passes check
        if self.prepare_integrity_check():
       
            # create the command
            command = self.bcl2fastq + " -R " + self.runfolders+"/"+self.runfolder + " --sample-sheet " + self.samplesheet + " --no-lane-splitting"
            # command="/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq -R 160822_NB551068_0006_AHGYM7BGXY/ --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv --no-lane-splitting"
            
            self.script_logfile.write("running bcl2fastq ......... \ncommand = " + command+"\n")
            
            # open a log file
            demultiplex_log = open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'w')
            
            #add entry to logger
            self.logger("demultiplexing started for run "+self.runfolder,"demultiplex_started")
            
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
            
            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()
            
            # write this to the log file
            demultiplex_log.write(out)
            
            # close log file
            demultiplex_log.close()
            
            # call_log_file_check
            self.check_demultiplexlog_file()
        
        
    def check_demultiplexlog_file(self):
        #open log file
        logfile=open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'r')
        
        count=0
        lastline=""
        for i in logfile:
            count=count+1
            lastline=i
        #print "line count = "+str(count)
        
        if  self.logfile_success in lastline:
            self.script_logfile.write("demultiplexing complete\n")
            # self.email_subject="MOKAPIPE ALERT: Demultiplexing complete"
            # self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed
            # self.send_an_email()
            self.logger("demultiplexing complete without error for run "+self.runfolder,"demultiplex_success")
            #update smartsheet
            self.smartsheet_demultiplex_complete()

            self.script_logfile.close()
            self.rename=self.rename+self.runfolder
            os.rename(self.logfile_name,self.script_logfile_path+self.now+"_"+self.rename+".txt")

            

        else:
            self.script_logfile.write("ERROR - DEMULTIPLEXING UNSUCCESFULL - please see "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed+"\n")
            # self.email_subject="MOKAPIPE ALERT: DEMULTIPLEXING FAILED"
            # self.email_priority=1
            # self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed
            # self.send_an_email()
            self.logger("demultiplexing completed with error or failed for run "+self.runfolder,"demultiplex_fail")
    
    def send_an_email(self):
        #body = self.runfolder
        self.script_logfile.write("Sending an email to..... " +self.me)
        #msg  = 'Subject: %s\n\n%s' % (self.email_subject, self.email_message)
        m = Message()
        #m['From'] = self.me
        #m['To'] = self.you
        m['X-Priority'] = str(self.email_priority)
        m['Subject'] = self.email_subject
        m.set_payload(self.email_message)
        
        
        server = smtplib.SMTP(host = self.host,port = self.port,timeout = 10)
        server.set_debuglevel(1)
        server.starttls()
        server.ehlo()
        server.login(self.user, self.pw)
        server.sendmail(self.me, [self.you], m.as_string())
        self.script_logfile.write("................email sent\n")

    def test_bcl2fastq(self):
        command = self.bcl2fastq

        # run the command
        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        
        # capture the streams 
        (out, err) = proc.communicate()
        
        if "BCL to FASTQ file converter" not in err:
            # self.email_subject="MOKAPIPE ALERT: ERROR - PRESENCE OF BCL2FASTQ TEST FAILED"
            # self.email_priority=1
            # self.email_message="The test to check if bcl2fastq is working ("+command+") failed"
            # self.send_an_email()
            self.logger("BCL2FastQ installation test failed","demultiplex_BCL2FASTQ_function_test_fail")
            raise Exception, "bcl2fastq not installed"
        else:
            self.logger("BCL2FastQ installation test ok","demultiplex_BCL2FASTQ_function_test_pass")

        # write this to the log file
        self.script_logfile.write("bcl2fastq check passed\n")

    def smartsheet_demultiplex_in_progress(self):
        '''This function updates smartsheet to say that demultiplexing is in progress'''
        
        # take current timestamp for recieved
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))
        
        # #uncomment this block if want to get the column ids for a new sheet
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
        
        #capture the NGS run number and count
        count = 0
        with open(self.samplesheet,'r') as samplesheet:
            for line in samplesheet:
                if line.startswith("NGS") or line.startswith("ONC"):
                    count=count+1
                    runnumber=line.split("_")[0]
        
        # set all values to be inserted
        payload='{"cells": [{"columnId": '+self.ss_title+', "value": "'+self.runfolder+'"}, {"columnId": '+self.ss_description+', "value": "Demultiplex"}, {"columnId": '+self.ss_samples+', "value": '+str(count)+'},{"columnId": '+self.ss_status+', "value": "In Progress"},{"columnId": '+self.ss_priority+', "value": "Medium"},{"columnId": '+self.ss_assigned+', "value": "aledjones@nhs.net"},{"columnId": '+self.ss_received+', "value": "'+str(self.smartsheet_now)+'"}],"toBottom":true}'
        
        # create url for uploading a new row
        url=self.url+"/rows"
        
        # add the row using POST 
        r = requests.post(url,headers=self.headers,data=payload)
        
        # capture the row id
        response= r.json()
        print response
        for i in response["result"]:
            if i == "id":
                self.rowid=response["result"][i]

        #check the result of the update attempt
        for i in response:  
            if i == "message":
                if response[i] =="SUCCESS":
                    self.script_logfile.write("smartsheet updated to say in progress\n")
                    self.logger("initiation of demultiplexing added to smartsheet","smartsheet_demultiplex_started_update_ok")
                else:
                    # #send an email if the update failed
                    # self.email_subject="MOKAPIPE ALERT: SMARTSHEET WAS NOT UPDATED"
                    # self.email_message="Smartsheet was not updated to say demultiplexing is inprogress"
                    # self.send_an_email()
                    self.script_logfile.write("smartsheet NOT updated at in progress step\n"+str(response))
                    self.logger("Smartsheet was not updated to say demultiplexing is in progress for run "+self.runfolder,"smartsheet_demultiplex_started_update_fail")

    def smartsheet_demultiplex_complete(self):
        '''update smartsheet to say demultiplexing is complete (add the completed date and calculate the duration (in days) and if met TAT)'''
        #build url tp read a row
        url='https://api.smartsheet.com/2.0/sheets/'+str(self.sheetid)+'/rows/'+str(self.rowid)
        #get row
        r = requests.get(url, headers=self.headers)
        #read response in json
        response= r.json()
        #loop through each column and extract the recieved date
        for col in response["cells"]:
            if str(col["columnId"]) == self.ss_received:
                recieved=datetime.datetime.strptime(col['value'], '%Y-%m-%d')
        
        # take current timestamp
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))
        now=datetime.datetime.strptime(self.smartsheet_now, '%Y-%m-%d')
        
        #calculate the number of days taken (add one so if same day this counts as 1 day not 0)
        duration = (now-recieved).days+1
        
        # set flag to show if TAT was met.
        TAT=1
        if duration > 4:
            TAT=0
        
        #build payload used to update the row
        payload = '{"id":"'+str(self.rowid)+'", "cells": [{"columnId":"'+ str(self.ss_duration)+'","value":"'+str(duration)+'"},{"columnId":"'+ str(self.ss_metTAT)+'","value":"'+str(TAT)+'"},{"columnId":"'+ str(self.ss_status)+'","value":"Complete"},{"columnId": '+self.ss_completed+', "value": "'+str(self.smartsheet_now)+'"}]}' 
        
        #build url to update row
        url=self.url+"/rows"
        update_OPMS = requests.request("PUT", url, data=payload, headers=self.headers)
        
        #check the result of the update attempt
        response= update_OPMS.json()
        print response
        for i in response:
            if i == "message":
                if response[i] =="SUCCESS":
                    self.script_logfile.write("smartsheet updated to say complete\n")
                    self.logger("smartsheet updated at end of demultiplexing","smartsheet_demultiplex_complete_update_ok")
                else:
                    # #send an email if the update failed
                    # self.email_subject="MOKAPIPE ALERT: SMARTSHEET WAS NOT UPDATED"
                    # self.email_message="Smartsheet was not updated to say demultiplexing was completed"
                    # self.send_an_email()
                    self.script_logfile.write("smartsheet NOT updated at complete step\n"+str(response))
                    self.logger("smartsheet NOT updated at end of demultiplexing for run "+self.runfolder,"smartsheet_demultiplex_complete_update_fail")


    def logger(self, message, tool):
        # create subprocess command
        log=self.echo_to_log % (message,tool)
        
        # run the command
        proc = subprocess.Popen([log], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        
        # capture the streams 
        (out, err) = proc.communicate()
        #if no stderr
        if not err:
            # write this to the log file
            self.script_logfile.write("log written to /usr/bin/logger\n"+log+"\n")

    
    def prepare_integrity_check(self):
        """
        We want to ensure the runfolder which was copied to the workstation hasn't been corrupted by the transfer.
        The MiSeq run folders are accesible from the workstation, so the integrity checks are performed by this script.
        The NextSeq checksums are generated by the sequencer but assessed by this script.
        
        For nextseq runs the presence of the file containing the checksums is assessed.
        If the checksums are not present the script is stopped and it will be re-assessed the next time the script is run.
        This is recorded in the system log so an alert can be made if the checksums are not present after a number of hours        
        If the checksums are present these are read into a list and compared. If they match the function returns True and the script will proceed, else the script will return False and stop

        The integrity checks of miseq runs are performed in this script.
        Firstly the path to the sequencer copy of the runfolder (which has been mapped onto the workstation) is defined and tested 
        Then directory paths are passed to the function run_integrity_check which calculates and checks the checksums
        The checksums are written to a text file and this text file is read and checksums compared (in line with nextseq)
        If the checksums match this function returns true
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
        

        # if it's a nextseq run look for the pre-calculated MD5 checksum values
        if "NB551068" in self.runfolder:
            # the checksums have ben written to a file in the run folder
            # build file path
            checksum_file_path = os.join(self.runfolderpath, "md5checksums.txt")

        # if it's not a nextseq run need to calculate checksums
        else:
            # Need to identify the sequencer copy of the run folder on the mapped sequencer shares. The sequencer name is in the run folder name
            # loop through the dictionary of sequencer names
            for sequencer in sequencer_share:
                # search for the sequencer name in the runfolder
                if sequencer in self.runfolder:
                    # if it matches use dictionary key to build the path to run folder (appending runfolder name to file path)
                    sequencer_copy_path = sequencer_share[sequencer] + self.runfolder
                    # define path to file containing checksums within this fodler (written to below)
                    checksum_file_path = os.join(sequencer_copy_path, "md5checksums.txt")


            # check the run folder paths have been identified correctly
            # if the sequencer_copy_path exists
            if os.path.isdir(sequencer_copy_path):
                # write to sys.log to say mapped temp folder found
                self.logger("mapped sequencer runfolder identified - " + sequencer_copy_path, "integrity_sequencer_runfolder_ok")
                # write to the logfile
                self.script_logfile.write("mapped sequencer run folder identified ok: " + sequencer_copy_path + "\n")
            # if the sequencer_copy_path does not exist
            else:
                # write to sys.log
                self.logger("integrity check fail. mapped sequencer runfolder does not exist: " + sequencer_copy_path, "demultiplex_fail")
                # write to the logfile
                self.script_logfile.write("mapped sequencer run folder does NOT exist: " + sequencer_copy_path + "\n")
                # return false to stop the script, saying integrity checking has not been completed
                return False

            # create checksum for workstation copy
            workstation_checksum = self.run_integrity_check(self.runfolderpath)
            # create checksum for seqeuncer copy
            sequencer_checksum = self.run_integrity_check(sequencer_copy_path)

            # open the checksum file
            with open(checksum_file_path,'w') as checksum_file:
                # write the folder name and path and checksums, seperated by '='
                checksum_file.write("workstation checksum (" + self.runfolderpath + ") =" + workstation_checksum + "\n")
                checksum_file.write("sequencer checksum (" + sequencer_copy_path + ") =" + sequencer_checksum + "\n")
            
        # Unless it's a nextseq run and the checksums have not yet been created the checksum file path should point to a file
        if os.isfile(checksum_file_path):
            # pass checksum file path to function which compares checksums. function returns true if the checksums match
            if self.check_checksums(checksum_file_path):
                # write to sys log
                self.logger("integrity check of runfolder " + self.runfolder + " passed", "integrity_check_ok")
                # write to the logfile
                self.script_logfile.write("integrity check of runfolder passed\n")
                # return True to report integrity checking has passed
                return True
            # if md5checksums do not match - this is major - probably worth an email?
            else:
                # send an email as it's very urgent
                self.email_subject="MOKAPIPE ALERT: INTEGRITY CHECK FAILED"
                self.email_priority=1
                self.email_message="run:\t"+self.runfolder+"sequencer checksum (" + sequencer_copy_path + ") =" + sequencer_checksum + "\n" \
                                    + "workstation checksum (" + self.runfolderpath + ") =" + workstation_checksum + "\n" \
                                    + "Please follow the protocol for when integrity checks fail"
                self.send_an_email()
        
                # record test failed in sys log
                self.logger("Integrity check fail. checksums do not match for " + self.runfolder, "demultiplex_fail")
                # also write to logfile
                self.script_logfile.write("integrity check of runfolder failed - checksums do not match. see " + checksum_file_path + "\n")
                # return false to stop the script, saying integrity checking has not been completed      
                return False


        # if there is no checksum file it must be a nextseq run which has finished (we already checked for the RTAcomplete file) but checksums not available 
        else:   
            #write to script 
            self.script_logfile.write("md5checksums not performed by nextseq. waiting...\n")
            # write to sys.log - if this is found >2 hours in a row should probably be an alert
            self.logger("md5checksums not yet available on nextseq for " + self.runfolder , "demultiplex_fail")
            # return false to stop the script, saying integrity checking has not been completed  
            return False


    def run_integrity_check(self,dirpath):
        """
        This function is passed the path to a runfolder
        A checksum is calculated for that directory and returned
        """
        # calculate md5 checksum directory
        return dirhash(dirpath, 'md5')


    def check_checksums(self, checksum_file_path):
        """
        This function receives the path to a file which should contain the checksums for both copies of a run folder.
        Each line contains the checksum and some information about the folder which that checksum relates to
        The checksums are extracted from the lines and compared
        If they match the function returns true else it returns false.
        All error reporting is done outside this function

        """
        # if md5checksums exist open the file
        with open(checksum_file, 'r') as checksum_file:
            # read the checksums into a list
            checksums = checksum_file.readlines()
        # each line contains the location of each checksum with an equals sign and then the checksum.
        # split on equals to capture just the checksum (and remove any new line characters incase they result in a differenece)
        checksum1 = checksums[0].split("=")[1].rstrip()
        checksum2 = checksums[1].split("=")[1].rstrip()
        # if the checksums match
        if checksum1 == checksum2:
            # if md5checksums match return to say test passed
            return True
        else:
            #otherwise return false
            return False



if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
