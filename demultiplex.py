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
from automate_demultiplex_config import *

class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''
    def __init__(self):
        # directory of run folders - must be same as in ready2start_demultiplexing()
        # self.runfolders = "/home/aled/demultiplex_testing" # aledpc
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
        # self.runfolders = "/home/aled/demultiplex_testing" # aledpc
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
        #self.script_logfile_path="/home/aled/Documents/automate_demultiplexing_logfiles/logrecord.txt" # aled pc
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
            
            #if so proceed
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
            # #send an email:2
            # self.email_subject="MOKAPIPE ALERT: Demultiplexing initiated"
            # self.email_message="demultiplexing for run " + self.runfolder + " has been initiated"
            # self.send_an_email()
            # proceed
            self.run_demuliplexing()
        else:
            # stop
            self.script_logfile.write("Looking for a samplesheet ......... no samplesheet present \n--- STOP ---\n")
            self.logger("no samplesheet found demultiplexing not started for run "+self.runfolder,"demultiplex_no_sample_sheet_present")

    def run_demuliplexing(self):
        '''Run the demultiplexing'''
        
        #print "demultiplexing ..... "+self.runfolder
        # example command sudo /usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq -R /media/data1/share/160914_NB551068_0007_AHGT7FBGXY --sample-sheet /media/data1/share/samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv --no-lane-splitting
        
        # practice command: 
        # command = "fv samtools faidx /home/aled/Documents/Reference_Genomes/hg19.fa xfvg chr1:10000000-10000002"
        
        # test bcl2fastq install
        self.test_bcl2fastq()
        self.smartsheet_demultiplex_in_progress()
        
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


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
