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


class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''
    def __init__(self):
        # directory of run folders - must be same as in ready2start_demultiplexing()
        # self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        self.runfolders ="/media/data1/share" # workstation

    def loop_through_runs(self):
        #set a time stamp to name the log file
        now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))

        # create a list of all the folders in the runfolders directory
        all_runfolders = os.listdir(self.runfolders)
        # for each folder if it is not samplesheets pass the runfolder to the next class ready2start_demultiplexing()
        for folder in all_runfolders:
            if folder != "samplesheets":
                if folder.endswith('.gz'):
                    pass
                else:
                    ready2start_demultiplexing().already_demultiplexed(folder, now)


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
        self.bcl2fastq = "/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq"
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
        self.pw   = '***REMOVED***'
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
        
        self.script_logfile.write("\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\nAssessing......... " + self.runfolderpath+"\n")
        
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
            #send an email:
            self.email_subject="DEMULTIPLEXING INITIATED"
            self.email_message="demultiplexing for run " + self.runfolder + " has been initiated\nPlease update smartsheet"
            self.send_an_email()
            # proceed
            self.run_demuliplexing()
        else:
            # stop
            self.script_logfile.write("Looking for a samplesheet ......... no samplesheet present \n--- STOP ---\n")

    def run_demuliplexing(self):
        '''Run the demultiplexing'''
        
        #print "demultiplexing ..... "+self.runfolder
        # example command sudo /usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq -R /media/data1/share/160914_NB551068_0007_AHGT7FBGXY --sample-sheet /media/data1/share/samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv --no-lane-splitting
        
        # practice command: 
        # command = "fv samtools faidx /home/aled/Documents/Reference_Genomes/hg19.fa xfvg chr1:10000000-10000002"
        
        # test bcl2fastq install
        self.test_bcl2fastq()

        # create the command
        command = self.bcl2fastq + " -R " + self.runfolders+"/"+self.runfolder + " --sample-sheet " + self.samplesheet + " --no-lane-splitting"
        # command="/usr/local/bcl2fastq2-v2.17.1.14/bin/bcl2fastq -R 160822_NB551068_0006_AHGYM7BGXY/ --sample-sheet samplesheets/160822_NB551068_0006_AHGYM7BGXY_SampleSheet.csv --no-lane-splitting"
        
        self.script_logfile.write("running bcl2fastq ......... \ncommand = " + command+"\n")
        
        # open a log file
        demultiplex_log = open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'w')
        
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
        
        if  "Processing completed with 0 errors and 0 warnings." in lastline:
            self.script_logfile.write("demultiplexing complete\n")
            self.email_subject="demultiplexing complete"
            self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed+"\n Please update smartsheet"
            self.send_an_email()
            self.script_logfile.close()
            self.rename=self.rename+self.runfolder+"_"
            os.rename(self.logfile_name,self.script_logfile_path+self.rename+self.now+".txt")

        else:
            self.script_logfile.write("ERROR - DEMULTIPLEXING UNSUCCESFULL - please see "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed+"\n")
            self.email_subject="DEMULTIPLEXING FAILED"
            self.email_priority=1
            self.email_message="run:\t"+self.runfolder+"\nPlease see log file at: "+self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed
            self.send_an_email()
    
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

        # run the command, redirecting stderror to stdout
        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        
        # capture the streams (err is redirected to out above)
        (out, err) = proc.communicate()
        
        if "BCL to FASTQ file converter" not in err:
            self.email_subject="ERROR - PRESENCE OF BCL2FASTQ TEST FAILED"
            self.email_priority=1
            self.email_message="The test to check if bcl2fastq is working ("+command+") failed"
            self.send_an_email()
            raise Exception, "bcl2fastq not installed"

        # write this to the log file
        self.script_logfile.write("bcl2fastq check passed\n")




if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
