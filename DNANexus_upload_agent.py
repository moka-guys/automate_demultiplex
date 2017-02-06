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
import smtplib
from email.Message import Message
import fnmatch
import requests
import json
from DNANexus_upload_agent_config import *


class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''
    
    def __init__(self):
        # directory of run folders - must be same as in upload2Nexus()
        #self.runfolders = "/media/data1/share" # workstation
        #self.runfolders = "/home/aled/demultiplex_testing" # aledpc
        #self.runfolders = "/media/data2/data" # workstation dummy
        self.now=""
    
    def loop_through_runs(self):
        #set a time stamp to name the log file
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))
        # create a list of all the folders in the runfolders directory
        all_runfolders = os.listdir(runfolders)
        #print all_runfolders
        upload=upload2Nexus()
        # for each folder if it is not samplesheets pass the runfolder to the next class
        for folder in all_runfolders:
            if folder != "samplesheets":
                if folder.endswith('.gz'):
                    pass
                else:
                    upload.already_uploaded(folder, self.now)

        self.combine_log_files()

    def combine_log_files(self):
        # count number of log files that match the time stamp
        count=0
        # empty list
        list_of_logfiles=[]
        #loop through the folder containing log files
        for file in os.listdir(DNA_Nexus_workflow_logfolder):
            #if is one with this time stamp, ie if was made by this running of this script
            if fnmatch.fnmatch(file,self.now+'*'):
                #add count and append to list
                count=count+1
                list_of_logfiles.append(upload2Nexus().DNA_Nexus_workflow_logfolder+file)
        
        #if more than one log file we want to concatenate them
        if count > 1:
            # get the filename with the longest name
            longest_name=max(list_of_logfiles, key=len)
            #remove from the list
            list_of_logfiles.remove(longest_name)
            #concatenate all the remaining filenames into a string, seperated by spaces
            remaining_files=" ".join(list_of_logfiles)

            # combine all into one file with the longest filename (that will have the run folder name)
            cmd = "cat " + remaining_files + " >> " + longest_name
            # remove the files that have been written to the longer file
            rmcmd= "rm " + remaining_files
            
            # run the command, redirecting stderror to stdout
            proc = subprocess.call([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            proc = subprocess.call([rmcmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)


class upload2Nexus():
    ''' This class is fed a runfolder which may be ready to be uploaded to DNA Nexus''' 
    
    def __init__(self):

        # set empty variables to be defined based on the run  
        self.runfolder = ""
        self.runfolderpath = ""

        # fastq folder
        #self.fastq_folder = "Data/Intensities/BaseCalls"
        self.fastq_folder_path = ""
        
        #upload_agent_logfile
        #self.upload_agent_logfile = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/Upload_agent_log/"
        self.upload_agent_logfile_name=""

        # string of fastqs for upload agent
        self.fastq_string = ""
        # list of fastqs to get ngs run number and WES batch
        self.list_of_samples = []

        self.list_of_DNA_numbers=[]

        #strings for NGSrun and wes numbers
        self.NGS_run = ''
        self.wes_number = ''

        # variables for running pipeline
        self.bash_script=""
        self.source_command = "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\ndepends_list=''\n"
        self.base_command = "jobid=$(dx run "+app_project+workflow_path+" -y"

        
        self.dest = " --dest="
        self.token = " --brief --auth-token "+Nexus_API_Key+")"
        #argument to capture jobids
        self.depends_list="depends_list=\"${depends_list} --depends-on ${jobid} \""
        self.dx_run = []

        #create path to data in nexus eg /runfolder/Data
        self.nexus_path = ""
        
        # email message
        self.email_subject = ""
        self.email_message = ""
        self.email_priority = 3

        #variable to rename log file.
        self.rename=""
        self.now=""

        #smartsheet API
        self.api_key=smartsheet_api_key
        
        #sheet id
        #self.sheetid=sheetid
        #newly inserted row
        self.rowid=""

        #time stamp
        self.smartsheet_now=""

        #columnIds
        self.ss_title=str(ss_title)
        self.ss_description=str(ss_description)
        self.ss_samples=str(ss_samples)
        self.ss_status=str(ss_status)
        self.ss_priority=str(ss_priority)
        self.ss_assigned=str(ss_assigned)
        self.ss_received=str(ss_received)
        self.ss_completed=str(ss_completed)
        self.ss_duration=str(ss_duration)
        self.ss_metTAT=str(ss_metTAT)

        #requests info
        self.headers={"Authorization": "Bearer "+smartsheet_api_key,"Content-Type": "application/json"}
        self.url='https://api.smartsheet.com/2.0/sheets/'+str(smartsheet_sheetid)

    def already_uploaded(self, runfolder, now):
        '''check folder hasn't already been uploaded'''
        self.now=now
        #open the logfile for this hour's cron job.
        self.upload_agent_logfile_name=upload_agent_logfile+self.now+"_"+self.rename+".txt"
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name,'a')

        # capture the runfolder 
        self.runfolder = str(runfolder)
               
        # create full path to runfolder
        self.runfolderpath = runfolders + "/" + self.runfolder
       
        self.upload_agent_script_logfile.write("\n----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\nAssessing......... " + self.runfolderpath + "\n")
        #print "looking at runfolder "+runfolder
         
        #look for the file denoting the upload has started
        if os.path.isfile(self.runfolderpath + "/" + upload_started_file):
            self.upload_agent_script_logfile.write("self.upload_started_file present \n---STOP---\n")
        else:
            #if not check demultiplex has finished succesfully and write to file
            print "not already uploaded"
            self.upload_agent_script_logfile.write("self.upload_started_file_not_present so continue\n")
            self.demultiplex_completed_successfully() 
        
    def demultiplex_completed_successfully(self):
        '''check if the demultiplexing finished successfully by reading the last line of the demultiplex log'''
        
        #check demultiplexing has actually been done
        if os.path.isfile(runfolders + "/" + self.runfolder + "/" + demultiplexed):
            #open log file
            logfile = open(runfolders + "/" + self.runfolder + "/" + demultiplexed,'r')
            
            #find the last line of the demultiplexing log file
            lastline = ""
            for i in logfile:
                lastline = i
            
            # check if the success statement is in the last line
            if  logfile_success in lastline:
                self.upload_agent_script_logfile.write("demultiplex was successfully completed. compile a list of fastqs \n")
                print "successfully demultiplexed"
                # if successfull call the module which creates a list of fastqs  
                self.find_fastqs()
            else:
                #write to logfile that demultplex was not successful
                self.upload_agent_script_logfile.write("demultiplex was NOT successfully completed. \n ---STOP---\n")
        else:
            # write to logfile that not yet demultiplexed
            self.upload_agent_script_logfile.write("demultiplex has not been performed.\n---STOP---\n")
            
    def find_fastqs(self):
        ''' find all the fastqs and send them to the upload command'''
        
        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath + "/" + fastq_folder
        
        # create a list of all files within the fastq folder
        all_fastqs = os.listdir(self.fastq_folder_path)
        
        #set counts to catch when not a panel to go through Nexus
        panel_count=0
        # find all fastqs
        for fastq in all_fastqs:
            if fastq.endswith('fastq.gz'):
                for i in coverage_bedfile_dict:
                    if i in fastq:
                        # count
                        panel_count=panel_count+1
                        #exclude undertermined samples 
                        if fastq.startswith('Undetermined'):
                            pass
                        else:
                            #build the list of fastqs with full file paths
                            self.fastq_string = self.fastq_string + " " + self.fastq_folder_path + "/" + fastq
                            #add the fastq name to a list to be used in create_nexus_file_path
                            self.list_of_samples.append(fastq)
                            #split line to get DNA number
                            self.list_of_DNA_numbers.append(fastq.split("_")[2])

           
        #write to logfile
        # if there were no WES samples state this in log message 
        if panel_count ==0 :
            self.upload_agent_script_logfile.write("List of fastqs did not contain any WES or custom panel samples. Stopping\n")
        # else continue
        else:
            #write to logfile
            self.upload_agent_script_logfile.write(str(panel_count)+" fastqs found...starting upload\n")
        
            #build the file path with WES batch and NGS run numbers
            self.create_nexus_file_path()
            
            # send list to module to trigger upload
            self.upload()       
    
    def create_nexus_file_path(self):
        ''' get info from the fastq names to have a more informative folder structure within DNA nexus 
        want the ngs run number eg NGS95a and any wes batches eg WES_5
        example fastq name = NGS95a_13_94947_SW_WES_5_S8_R2_001.fastq.gz'''
        
        # a list to hold all the wes numbers
        WES_numbers = []
        # for each fastq in the list of fastqs
        for fastq in self.list_of_samples:
            # split on underscores to capture the first element which is the ngs number
            splitfastq = fastq.split("_")
            # assign self.ngs_run
            self.ngs_run = splitfastq[0]
            
            # if the run has any WES samples
            if "WES" in fastq:
                # split on _WES to split the fastq name into two
                splitfastq = fastq.split("_WES")
                # take the second half of it and split on "_S"
                splitfastq2 = splitfastq[1].split("_S")

                #This should split the string in half again, with the first element either _5 or 5 depending if tit's WES_5 or WES5
                #append this to WES (which was replaced as part of the split) and add to a list
                wesrun = "WES" + splitfastq2[0].replace('_','')
                WES_numbers.append(wesrun)
        
        # if there are wes batch numbers
        if len(WES_numbers)>0:
            # create a list of unique WES batches
            for wesnumber in set(WES_numbers):
                # if multiple WES batches append each one with an underscore
                if self.wes_number != '':
                    self.wes_number = self.wes_number + "_" + wesnumber
                else:
                    self.wes_number = wesnumber

        # if wes batch numbers add this into the nexus path
        if self.wes_number == '':
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.ngs_run + "_" + self.wes_number + fastq_folder
        else:
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.ngs_run + fastq_folder
        
        #write to log
        self.upload_agent_script_logfile.write(self.nexus_path+"\n") 


    def upload(self):
        '''takes a list of all the fastqs (with full paths) and calls the upload agent.'''
        
        # perform upload agent test
        self.test_upload_agent()

        self.test_dx_toolkit()

        # build the nexus upload command                        
        nexus_upload_command = upload_agent + " --auth-token "+Nexus_API_Key+" --project "+NexusProject+"  --folder /" + self.nexus_path + " --do-not-compress --upload-threads 10" + self.fastq_string
        
        #write to logfile
        self.upload_agent_script_logfile.write("Nexus command = \n" + nexus_upload_command + "\n")
        
        #create file to show demultiplexing has started
        upload_started = open(self.runfolderpath + "/" + upload_started_file, 'w')
        
        if not debug:
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
            
            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()
        else:
            out="x"
            err="y"

        #write to log
        upload_started.write("\n----------------------"+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\n" + out)
        upload_started.close()
        
        # set email content
        self.email_subject = "MOKAPIPE ALERT: Upload of " + self.runfolder + " completed"
        self.email_priority = 3
        self.email_message = self.runfolder + " \t has been uploaded to DNA Nexus :-)\nPlease see log file at: " + self.runfolderpath + "/" + upload_started_file
        if not debug:
            # send email
            self.send_an_email()
        # start pipeline
        self.create_run_pipeline_command()

        # close the log file
        self.upload_agent_script_logfile.close()

        #rename file to show what runs were affected.
        self.rename=self.rename+self.runfolder
        os.rename(self.upload_agent_logfile_name,self.upload_agent_logfile_name.replace('.txt','')+self.rename+".txt")
        

    def send_an_email(self):
        #body = self.runfolder
        self.upload_agent_script_logfile.write("Sending email to...... " + str(you))
        #msg  = 'Subject: %s\n\n%s' % (self.email_subject, self.email_message)
        m = Message()
        #m['From'] = self.me
        #m['To'] = self.you
        m['X-Priority'] = str(self.email_priority)
        m['Subject'] = self.email_subject
        m.set_payload(self.email_message)
        
        
        server = smtplib.SMTP(host = host,port = port,timeout = 10)
        server.set_debuglevel(10)
        server.starttls()
        server.ehlo()
        server.login(user, pw)
        server.sendmail(me, [you], m.as_string())

        #write to logfile
        self.upload_agent_script_logfile.write("Email sent\n")
        #self.upload_agent_script_logfile.close()

    def test_upload_agent(self):
        '''test the upload agent is installed'''
        
        #command
        command = upload_agent + " --version"

        # run the command
        proc = subprocess.Popen([command], stderr = subprocess.PIPE, stdout = subprocess.PIPE, shell = True)
        
        # capture the streams
        (out, err) = proc.communicate()
        
        if "Upload Agent Version:" not in out:
            self.email_subject = "MOKAPIPE ALERT: ERROR - PRESENCE OF DNA NEXUS UPLOAD AGENT TEST FAILED"
            self.email_priority = 1
            self.email_message = "The test to check the upload agent has been installed (" + command + ") failed"
            self.send_an_email()
            raise Exception, "Upload agent not installed"

        # write this to the log file
        self.upload_agent_script_logfile.write("upload agent check passed\n")

    def test_dx_toolkit(self):
        '''test the dx toolkit is installed'''
        
        #command
        command = "source /etc/profile.d/dnanexus.environment.sh;dx --version"

        # run the command
        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")
        
        # capture the streams
        (out, err) = proc.communicate()
        
        if "dx v0.2" not in out:
            self.email_subject = "MOKAPIPE ALERT: ERROR - DX TOOLKIT TEST FAILED"
            self.email_priority = 1
            self.email_message = "The test to check that the dx toolkit is working (" + command + ") failed. Hopefully this just means it's been upgraded past v0.2!\n"+err
            self.send_an_email()
            raise Exception, "dx toolkit not installed"

        # write this to the log file
        self.upload_agent_script_logfile.write("dx toolkit check passed\n")

    def  create_run_pipeline_command(self):
        '''loop through the list of fastqs to create a set of commands to initiate the pipeline'''
        self.bash_script=DNA_Nexus_workflow_logfolder + self.runfolder + ".sh"
        
        #open bash script
        self.DNA_Nexus_bash_script = open(self.bash_script, 'w')
        #write command to log file
        self.DNA_Nexus_bash_script.write(self.source_command)
        print self.list_of_samples
        #loop through list of fastq files
        for fastq in self.list_of_samples:
            #take read one
            if "_R1_" in fastq:
                #assign read1
                read1 = self.nexus_path+"/"+fastq
                # assign read2 by replacing R1 with R2
                read2 = self.nexus_path+"/"+fastq.replace("_R1_", "_R2_")
                
                #get panel name and bed file
                for i in coverage_bedfile_dict:
                    if i in fastq:
                        sambamba_bedfile=app_project+bedfile_folder+coverage_bedfile_dict[i]
                        capture_bedfile=app_project+bedfile_folder+capture_bedfile_dict[i]

                read1_cmd=NexusProject +":"+ read1
                read2_cmd=NexusProject +":"+ read2
                bwa_fastq1_cmd = NexusProject +":"+ read1
                bwa_fastq2_cmd = NexusProject +":"+ read2
                dest_cmd=NexusProject +":"+ self.runfolder + "_" + self.ngs_run + "_" + self.wes_number

                # create the dx command
                command = self.base_command + fastqc1 + read1_cmd + fastqc2 + read2_cmd + bwa_fastq1 + bwa_fastq1_cmd + bwa_fastq2 + bwa_fastq2_cmd + samb_bed + sambamba_bedfile + self.dest + dest_cmd + self.token
                #add command for each pair of fastqs to a list 
                self.dx_run.append(command)
        
                
        # call module to issue the dx run commands
        self.run_pipeline()

        #record timestamp
        self.DNA_Nexus_bash_script = open(self.bash_script, 'a')
        self.DNA_Nexus_bash_script.write("#----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")
        self.DNA_Nexus_bash_script.close()

    def run_pipeline(self):
        '''issue dna nexus run commands''' 
               
        # loop through all dx_run commands:       
        for command in self.dx_run:
            # write command to log file
            self.DNA_Nexus_bash_script.write(command+"\n")
            # write line to append job id to depends_list
            self.DNA_Nexus_bash_script.write(self.depends_list+"\n")

            # capture the sample name
            #step 1 split the command to get the last argument (read2)
            split_command = command.split(fastq_folder)
            read_2 = split_command[1].replace("/","")

            # split this fastq name on _
            read = read_2.split("_")
            # eg name NGS150B_14_152061_BS_WES11_S2_R2_001
            sample = read[0]+"_"+read[1]+"_"+read[2]+"_"+read[3]+"_"+read[4]
            
            #capture the workflow used
            app=workflow_path.replace("Workflows/","")


        #self.DNA_Nexus_bash_script.write("echo $depends_list\n")
        
        # issue multiqc command
        #self.DNA_Nexus_bash_script.write(command+"\n")
        #self.DNA_Nexus_bash_script.write("\#multiqc command $depends_list")
        
        #close bash script file handle
        self.DNA_Nexus_bash_script.close()

        #write to cron job script
        self.upload_agent_script_logfile.write("dx run commands issued\nSee "+self.bash_script+"\n")
        
        # # run a command to execute the bash script made above
        cmd="bash "+self.bash_script
        if not debug:
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        
            # capture the streams
            (out, err) = proc.communicate()
        else:
            out="x"
            err=""

        #reopen log file containing output from upload agent
        upload_started = open(self.runfolderpath + "/" + upload_started_file, 'a')
        
        #write to log + close
        upload_started.write(out)
        upload_started.close()

        if err:
            upload_started.write("Uh Oh! standard error: "+err)
            #create email message
            self.email_subject = "MOKAPIPE ALERT: Error message when started pipeline"
            self.email_priority = 1
            self.email_message = self.runfolder + " being processed using workflow " + app + "\nTHE PIPELINE MAY HAVE STARTED CORRECTLY. However, there was a standard error reported when starting pipeline.\nThe standard error messages are: "+ err + "Please see logfile at "+self.runfolderpath + "/" + upload_started_file
        
        else:
            DNA_list="('"
            for DNA in self.list_of_DNA_numbers:
                if DNA in DNA_list:
                    pass
                else:
                    DNA_list=DNA_list+DNA+"',"
            DNA_list=DNA_list+")"
            DNA_list=DNA_list.replace(",)",")")
            sql="update NGSTest set PipelineVersion = (select itemID from item where item = 'mokapipe v2.2') where dna in " + DNA_list
            #create email message
            self.email_subject = "MOKAPIPE ALERT: Started pipeline for " + self.runfolder
            self.email_priority = 3
            self.email_message = self.runfolder + " being processed using workflow " + app +"\n\nPlease update Moka using the query below:\n\n"+sql
            
            if not debug:
                self.smartsheet_mokapipe_in_progress()
            
        if not debug:
            # send email
            self.send_an_email()

    def smartsheet_mokapipe_in_progress(self):
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
        for file in os.listdir(self.runfolderpath+"/Data/Intensities/BaseCalls"):
            if file.endswith("fastq.gz"):
                if file.startswith("Undetermined"):
                    pass
                else:
                    count = count + 0.5
                    runnumber=file.split("_")[0]
        
        # set all values to be inserted
        payload='{"cells": [{"columnId": '+self.ss_title+', "value": "MokaPipe '+runnumber+'"}, {"columnId": '+self.ss_description+', "value": "MokaPipe"},{"columnId": '+self.ss_samples+', "value": '+str(count)+'},{"columnId": '+self.ss_status+', "value": "In Progress"},{"columnId": '+self.ss_priority+', "value": "Medium"},{"columnId": '+self.ss_assigned+', "value": "aledjones@nhs.net"},{"columnId": '+self.ss_received+', "value": "'+str(self.smartsheet_now)+'"}], "toBottom":true}'
        #print payload
        # create url for uploading a new row
        url=self.url+"/rows"
        
        # add the row using POST 
        r = requests.post(url,headers=self.headers,data=payload)
        
        # capture the row id
        response= r.json()
        #print response

        for i in response["result"]:
            if i == "id":
                self.rowid=response["result"][i]

        
        #check the result of the update attempt
        for i in response:  
            #print i
            if i == "message":
                if response[i] =="SUCCESS":
                    self.upload_agent_script_logfile.write("smartsheet updated to say in progress\n")
                else:
                    #send an email if the update failed
                    self.email_subject="MOKAPIPE ALERT: SMARTSHEET WAS NOT UPDATED"
                    self.email_message="Smartsheet was not updated to say MokaPipe is inprogress"
                    self.send_an_email()
                    self.upload_agent_script_logfile.write("smartsheet NOT updated at in progress step\n"+str(response))




if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
