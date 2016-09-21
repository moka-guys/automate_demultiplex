'''
Created on 21 Sep 2016

Once demultiplexing has been complete the files require uploading to DNANexus.

This script will be scheduled to run and identify any folders that have not been uploaded.

It will trigger the upload agent to upload into the required project
 
@author: aled
'''

import os
import subprocess
import datetime


class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''
    
    def __init__(self):
        # directory of run folders - must be same as in upload2Nexus()
        self.runfolders ="/media/data1/share" # workstation
        self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        self.runfolders = "/home/mokaguys/Documents/upload_agent_test" # workstation dummy

    def loop_through_runs(self):
        # create a list of all the folders in the runfolders directory
        all_runfolders = os.listdir(self.runfolders)
        
        # for each folder if it is not samplesheets pass the runfolder to the next class
        for folder in all_runfolders:
            if folder != "samplesheets":
                if folder.endswith('.gz'):
                    pass
                else:
                    upload2Nexus().already_uploaded(folder)


class upload2Nexus():
    ''' This class is fed a runfolder which may be ready to be uploaded to DNA Nexus''' 
    
    def __init__(self):
        # directory of run folders - must be same as in get_list_of_runs()
        #self.runfolders ="/media/data1/share" # workstation
        self.runfolders = "/home/mokaguys/Documents/upload_agent_test" # workstation dummy
        #self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        
        # file which denotes demultiplexing is underway/complete 
        self.demultiplexed = "demultiplexlog.txt"
        
        # set empty variables to be defined based on the run  
        self.runfolder = ""
        self.runfolderpath = ""

        #succesful run statement
        self.logfile_success="Processing completed with 0 errors and 0 warnings."
        
        # upload started log file
        self.upload_started_file="DNANexus_upload_started.txt"
        
        # upload agent
        self.upload_agent="/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"
        
        # fastq folder
        self.fastq_folder="Data/Intensities/BaseCalls"
        self.fastq_folder_path=""
        
        #upload_agent_logfile
        self.upload_agent_logfile=self.runfolders+"/upload_logfile.txt"
        
        self.upload_agent_script_logfile=open(self.upload_agent_logfile,'a')
        
        
        
    def already_uploaded(self, runfolder):
        '''check folder hasn't already been uploaded'''
        self.upload_agent_script_logfile.write("\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\nAssessing......... " + self.runfolderpath+"\n")
                
        print "looking at runfolder "+runfolder
        # capture the runfolder 
        self.runfolder = str(runfolder)
               
        # create full path to runfolder
        self.runfolderpath = self.runfolders + "/" + self.runfolder
        
        #look for the file denoting the upload has started
        if os.path.isfile(self.runfolderpath + "/" + self.upload_started_file):
            self.upload_agent_script_logfile.write("self.upload_started_file present \n---STOP---\n")
        else:
            #if not check demultiplex has finished succesfully
            print "not already uploaded"
            self.upload_agent_script_logfile.write("self.upload_started_file_not_present so continue\n")
            self.demultiplex_completed_successfully() 
        
    def demultiplex_completed_successfully(self):
        '''check if the demultiplexing finished successfully by reading the last line of the demultiplex log'''
        
        #check demultiplexing has actually been done
        if os.path.isfile(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed):
            #open log file
            logfile=open(self.runfolders+"/"+self.runfolder+"/"+self.demultiplexed,'r')
            
            #find the last line of the demultiplexing log file
            lastline=""
            for i in logfile:
                lastline=i
            print lastline
            # check if the success statement is in the last line
            if  self.logfile_success in lastline:
                self.upload_agent_script_logfile.write("demultiplex was successfully completed. compile a list of fastqs \n")
                print "successfully demultiplexed"
                # if successfull call the module which creates a list of fastqs  
                self.find_fastqs()
            else:
                self.upload_agent_script_logfile.write("demultiplex was NOT successfully completed. \n ---STOP---\n")
        else:
            self.upload_agent_script_logfile.write("demultiplex has not been performed.\n---STOP---\n")
            
    def find_fastqs(self):
        ''' find all the fastqs and send them to the upload command'''
        
        # folder containing the fastqs for this project
        self.fastq_folder_path=self.runfolderpath+"/"+self.fastq_folder
        
        # create a list of all files within the fastq folder
        all_fastqs = os.listdir(self.fastq_folder_path)
        
        # string of fastqs
        fastq_string=""
        
        # find all fastqs
        for fastq in all_fastqs:
            if fastq.endswith('fastq.gz'):
                #exclude undertermined samples 
                if fastq.startswith('Undetermined'):
                    pass
                else:
                    #build the list of fastqs with full file paths
                    fastq_string=fastq_string+" "+self.fastq_folder_path+"/"+fastq
        
        self.upload_agent_script_logfile.write("list of fastqs found\n")
        # send list to module to trigger upload
        self.upload(fastq_string)       
        
    def upload(self, fastq_string):
        '''takes a list of all the fastqs (with full paths) and calls the upload agent.'''
        
        #create path to data in nexus eg /runfolder/Data
        nexus_path= self.runfolder+"Data"
                
        nexus_command = self.upload_agent + " --auth-token kMEShRwrLbRjiqwpol4um1Wi7BpXIHUO --project NGS_runs --folder /"+ nexus_path +" --do-not-compress --progress --upload-threads 10 "+ fastq_string
        
        self.upload_agent_script_logfile.write("Nexus command = \n"+nexus_command+"\n")
        
        #create file to show demultiplexing has started
        upload_started=open(self.runfolderpath+"/"+self.upload_started_file,'w')
        
        # run the command, redirecting stderror to stdout
        proc = subprocess.Popen([nexus_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
         
        # capture the streams (err is redirected to out above)
        (out, err) = proc.communicate()
        
        upload_started.write("\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\n" + out)
        upload_started.close()
        
        self.upload_agent_script_logfile.close()
if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
