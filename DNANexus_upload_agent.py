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
from shutil import copyfile

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
        if debug: # use test folder
            all_runfolders = ['999999_NB551068_0024_AHHVCTAFXX_ALED_TEST']
        else:
            all_runfolders = os.listdir(runfolders)
            #all_runfolders = ['999999_NB551068_0024_AHHVCTAFXX_ALED_TEST']
        
        #create instance of the class
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

        # name of file which denotes demultiplexing is underway/complete
        self.demultiplexed = "demultiplexlog.txt"

        # fastq folder
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

        #variables to rename log file.
        self.rename=""
        self.now=""

        #####################################DNA Nexus########################
        # bash script that is used to execute dx commands
        self.bash_script=""

        # DNA Nexus commands 
        self.source_command = "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\ndepends_list=''\n"

        self.createprojectcommand="project_id=\"$(dx new project --bill-to %s \"%s\" --brief --auth-token "+Nexus_API_Key+")\"\n"
        self.base_command = "jobid=$(dx run "+app_project+workflow_path+" -y"
        self.multiqc_command= "dx run "+app_project+multiqc_path
        self.smartsheet_update_command="dx run "+app_project+smartsheet_path

        # project to upload run folder into
        self.nexusproject=NexusProjectPrefix

        #project_ID of created project
        self.projectid=""

        #arguments for command
        self.dest = " --dest="
        self.project = " --project="
        self.token = " --brief --auth-token "+Nexus_API_Key+")"
        self.depends= " -y $depends_list"

        #argument to capture jobids
        self.depends_list="depends_list=\"${depends_list} -d ${jobid} \""
        self.dx_run = []

        #create path to data in nexus eg /runfolder/Data
        self.nexus_path = ""

        #######################email message###############################
        self.email_subject = ""
        self.email_message = ""
        self.email_priority = 3

        #########################################smartsheet API##############
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
        #capture timestamp
        self.now=now
        
        #open the logfile for this hour's cron job.
        self.upload_agent_logfile_name=upload_agent_logfile+self.now+"_"+self.rename+".txt"
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name,'a')

        # capture the runfolder 
        self.runfolder = str(runfolder)
               
        # create full path to runfolder
        self.runfolderpath = runfolders + "/" + self.runfolder
       
        self.upload_agent_script_logfile.write("\n----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "----------------------\nAssessing " + self.runfolderpath + "\n\n----------------------HAS THIS FOLDER ALREADY BEEN UPLOADED?----------------------\n")
        print "looking at runfolder "+runfolder
         
        #look for the file denoting the upload has started
        if os.path.isfile(self.runfolderpath + "/" + upload_started_file):
            if not debug:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present \n----------------------STOP----------------------\n")
            else:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present but DEBUG MODE IS TRUE SO CONTINUING.......\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
                self.demultiplex_completed_successfully()     
        else:
            #if not check demultiplex has finished succesfully and write to file
            print "not already uploaded"
            self.upload_agent_script_logfile.write("NO - self.upload_started_file not present so continue\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
            self.demultiplex_completed_successfully() 
        
    def demultiplex_completed_successfully(self):
        '''check if the demultiplexing finished successfully by reading the last line of the demultiplex log'''
        
        #check demultiplexing has actually been done
        if os.path.isfile(runfolders + "/" + self.runfolder + "/" + self.demultiplexed):
            #open log file
            logfile = open(runfolders + "/" + self.runfolder + "/" + self.demultiplexed,'r')
            
            #find the last line of the demultiplexing log file
            lastline = ""
            for i in logfile:
                lastline = i
            
            # check if the success statement is in the last line
            if  logfile_success in lastline:
                self.upload_agent_script_logfile.write("Demultiplex was successfully completed.\ncompiling a list of fastqs....... ")
                #print "successfully demultiplexed"
                # if successfull call the module which creates a list of fastqs  
                self.find_fastqs()
            else:
                #write to logfile that demultplex was not successful
                self.upload_agent_script_logfile.write("!!!!!!!DEMULTIPLEXING DID NOT COMPLETE SUCCESSFULLY.!!!!!!!!!\n----------------------STOP----------------------\n")
        else:
            # write to logfile that not yet demultiplexed
            self.upload_agent_script_logfile.write("demultiplexing has not been performed.\n----------------------STOP----------------------\n")
            
    def find_fastqs(self):
        ''' find all the fastqs and send them to the upload command'''
        
        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath + fastq_folder
        
        # create a list of all files within the fastq folder
        all_fastqs = os.listdir(self.fastq_folder_path)
        
        #set counts to catch when not a panel to go through Nexus
        to_be_nexified=0
        # find all fastqs
        for fastq in all_fastqs:
            if fastq.endswith('fastq.gz'):
                for i in panelnumbers:
                    if i+"_" in fastq:
                        # count
                        to_be_nexified += 1
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
        if to_be_nexified ==0 :
            self.upload_agent_script_logfile.write("List of fastqs did not contain any known Pan numbers. Stopping\n")
        # else continue
        else:
            #write to logfile
            self.upload_agent_script_logfile.write(str(to_be_nexified)+" fastqs found.\n\n----------------------PREPARING UPLOAD OF FASTQS----------------------\ndefining path for fastq files.......")
        
            #build the file path with WES batch and NGS run numbers
            self.create_nexus_file_path()

            #create nexus project
            self.create_project()
            
            # send list to module to trigger upload
            self.upload()       
    
    def create_nexus_file_path(self):
        ''' get info from the fastq names to have a more informative folder structure within DNA nexus 
        want the ngs run number eg NGS95a and any wes batches eg WES_5
        example fastq name = NGS95a_13_94947_SW_WES_5_Pan493_S8_R2_001.fastq.gz'''
        
        # a list to hold all the wes numbers
        WES_numbers = []
        # a list to hold all the NGS numbers
        NGS_numbers=[]

        # for each fastq in the list of fastqs
        for fastq in self.list_of_samples:
            # split on underscores to capture the first element which is the ngs number
            splitfastq = fastq.split("_")
            # add NGS_run number
            NGS_numbers.append(splitfastq[0])
            
            # if the run has any WES samples
            if "WES" in fastq:
                # split on _WES to split the fastq name into two
                splitfastq = fastq.split("_WES")
                # take the second half of it and split on "_Pan"
                splitfastq2 = splitfastq[1].split("_Pan")

                #This should split the string in half again, with the first element either _5 or 5 depending if it's WES_5 or WES5
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

        # create a list of unique NGS numebrs
        for ngsnumber in set(NGS_numbers):
            # if multiple NGS numbers append each one with an underscore
            if self.NGS_run != '':
                self.NGS_run = self.NGS_run + "_" + ngsnumber
            else:
                self.NGS_run = ngsnumber


        # if wes batch numbers add this into the nexus path
        if self.wes_number != '':
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.NGS_run + "_" + self.wes_number + fastq_folder
            #build project name
            self.nexusproject=self.nexusproject+self.runfolder + "_" + self.NGS_run + "_" + self.wes_number
        else:
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.NGS_run + fastq_folder
            #build project name
            self.nexusproject=self.nexusproject+self.runfolder + "_" + self.NGS_run
        
        #write to log
        self.upload_agent_script_logfile.write("fastqs will be uploaded to "+self.nexus_path+"\n\n----------------------CREATE AND SHARED DNA NEXUS PROJECT----------------------\n") 


    def upload(self):
        '''takes a list of all the fastqs (with full paths) and calls the upload agent.'''
        
        # perform upload agent test
        self.test_upload_agent()

        self.test_dx_toolkit()

        # build the nexus upload command                        
        nexus_upload_command = upload_agent + " --auth-token "+Nexus_API_Key+" --project "+ self.nexusproject +"  --folder /" + self.nexus_path + " --do-not-compress --upload-threads 10" + self.fastq_string
        runfolder_upload_cmd_file = open(self.runfolderpath + "/" + runfolder_upload_cmds, 'w')
        runfolder_upload_cmd_file.write("----------------------Upload of fastqs----------------------\n"+nexus_upload_command+"\n\n----------------------Upload rest of runfolder----------------------\n")
        #write to logfile
        self.upload_agent_script_logfile.write("Uploading Fastqs to Nexus. See commands at "+self.runfolderpath + "/" + runfolder_upload_cmds + "\n\n----------------------CHECKING SUCCESSFUL UPLOAD OF FASTQS----------------------\n")
        
        #create file to show upload has started
        upload_started = open(self.runfolderpath + "/" + upload_started_file, 'a')
        
        if not debug:
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
            
            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()
        else:
            out="x"
            err="y"

        #write to log
        runfolder_upload_stdout_file = open(self.runfolderpath + "/" + upload_started_file, 'a')

        upload_started.write("\n----------------------Uploading fastqs "+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\n" + out)
        upload_started.close()
        
        #check fastqs uploaded successfully
        self.look_for_upload_errors_fastq()

        # set email content
        self.email_subject = "MOKAPIPE ALERT: Upload of fastqs from " + self.runfolder + " complete"
        self.email_priority = 3
        self.email_message = "Fastqs from "+self.runfolder + " have been uploaded to DNA Nexus.\nStandard out/error written to log file at: " + self.runfolderpath + "/" + upload_started_file
        if not debug:
            # send email
            self.send_an_email()
        # start pipeline
        self.create_run_pipeline_command()

        #back up rest of run folder to nexus
        self.upload_rest_of_runfolder()

        
        

    def send_an_email(self):
        '''function to send an email. uses self.email_subject, self.email_message and self.email_priority'''       
        #create message object
        m = Message()
        #set priority
        m['X-Priority'] = str(self.email_priority)
        #set subject
        m['Subject'] = self.email_subject
        #set body
        m.set_payload(self.email_message)
        
        # server details
        server = smtplib.SMTP(host = host,port = port,timeout = 10)
        server.set_debuglevel(1) # verbosity
        server.starttls()
        server.ehlo()
        server.login(user, pw)
        server.sendmail(me, [you], m.as_string())

        #write to logfile
        self.upload_agent_script_logfile.write("\nEmail sent to...... " + str(you) + "\nsubject:" + self.email_subject + "\nbody:" + self.email_message+"\n\n")

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
        self.upload_agent_script_logfile.write("upload agent check passed\n\n----------------------TEST DX TOOLKIT IS FUNCTIONING----------------------\n")

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
        self.upload_agent_script_logfile.write("dx toolkit check passed\n\n----------------------UPLOAD FASTQS----------------------\n")

    def create_project(self):
        '''create a project for each run names 002_runfolder'''
        project_bash_script=DNA_Nexus_project_creation_logfolder + self.runfolder + ".sh"
        
        #open bash script
        DNA_Nexus_bash_script = open(project_bash_script, 'w')
        DNA_Nexus_bash_script.write(self.source_command)
        if self.wes_number == '':
            DNA_Nexus_bash_script.write(self.createprojectcommand % (dev_organisation,self.nexusproject))
        else:
            DNA_Nexus_bash_script.write(self.createprojectcommand % (prod_organisation,self.nexusproject))

        #then need to share the project with the nexus usernames in the list in config file
        for i in users:
            DNA_Nexus_bash_script.write("dx invite %s $project_id ADMINISTER --auth-token %s\n" % (i,Nexus_API_Key))
        DNA_Nexus_bash_script.write("echo $project_id")
        #close before running
        DNA_Nexus_bash_script.close()     
        
        if not debug:
            # # run a command to execute the bash script made above
            cmd="bash "+project_bash_script
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            
            # capture the streams
            (out, err) = proc.communicate()

            std_out=out
            self.projectid="project"+std_out.split("project")[-1]
            print self.projectid
            #for i in out:
            #    if i.startswith("project"):
            #        self.projectid=i

            if self.projectid=="":
                self.email_subject = "MOKAPIPE ALERT: FAILED TO CREATE PROJECT IN DNA NEXUS"
                self.email_priority = 1
                self.email_message = "Unable to create the project %s.\nError message = %s%s" % (self.nexusproject, out,err)
                self.send_an_email()
                raise Exception, "Unable to create DNA Nexus project"
            else:               
                # write to log 
                user_str=""
                for i in users:
                    user_str=user_str+i+" "
                self.upload_agent_script_logfile.write("DNA Nexus project %s created and shared to " % (self.nexusproject) + user_str +"\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (self.projectid))
                
        else:
            self.projectid="project-F2gzY2j0xyXJ4x3z5Pq8BjQ4"

        

    def  create_run_pipeline_command(self):
        '''loop through the list of fastqs to create a set of commands to initiate the pipeline'''
        
        # Update script log file to say what is being done.
        self.upload_agent_script_logfile.write("\n\n----------------------RUN WORKFLOW----------------------\n")
        
        # define the bash script to contain the dx run commands
        self.bash_script=DNA_Nexus_workflow_logfolder + self.runfolder + ".sh"
        
        #open bash script
        self.DNA_Nexus_bash_script = open(self.bash_script, 'w')
        
        #write command to log file
        self.DNA_Nexus_bash_script.write(self.source_command)
        
        
        #loop through list of fastq files
        for fastq in self.list_of_samples:
            #take read one
            if "_R1_" in fastq:
                #assign read1
                read1 = self.nexus_path+"/"+fastq
                # assign read2 by replacing R1 with R2
                read2 = self.nexus_path+"/"+fastq.replace("_R1_", "_R2_")
                
                #get panel name and bed file
                for i in panelnumbers:
                    # add underscore to Pan number so Pan1000 is not true when looking for Pan100
                    if i+"_" in fastq:
                        # build path in nexus to the relevant sambamba bed
                        sambamba_bedfile=app_project+bedfile_folder+i+"dataSambamba.bed"
                        
                        # moka vendor bedfile
                        if i == "Pan493":
                            #specify this for the WES samples
                            moka_vendor_bedfile=app_project+bedfile_folder+"agilent_sureselect_human_all_exon_v5_b37_targets.bed"
                        else:
                            # otherwise build path in nexus to the relevant bed file
                            moka_vendor_bedfile=app_project+bedfile_folder+i+"data.bed"

                        # build path in nexus to the relevant RPKM bedfile
                        RPKM_bedfile=app_project+bedfile_folder+panelnumbers[i]+"data.bed"

                        # use same panelname to get the email which will be used to upload to IVA
                        ingenuity_email=email_panel_dict[i]

                # create the input command for the fastqc and BWA inputs
                read1_cmd=self.nexusproject +":"+ read1
                read2_cmd=self.nexusproject +":"+ read2

                # set the destination command as the root of the project
                dest_cmd=self.nexusproject +":/"

                # create the dx command
                command = self.base_command + fastqc1 + read1_cmd + fastqc2 + read2_cmd + sambamba_input + sambamba_bedfile + mokavendor_input + moka_vendor_bedfile + ingenuity_input + ingenuity_email+ self.dest + dest_cmd + self.token
                
                #add command for each pair of fastqs to a list 
                self.dx_run.append(command)
        
                       
        # call module to issue the dx run commands
        self.run_pipeline()

        # record timestamp at end of bash script
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

        # build multiqc command - eg command = dx run multiqc -iproject_for_multiqc=002_170222_ALEDTEST --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid
        multiqc_command=self.multiqc_command+multiqc_project_input+self.nexusproject+self.project+self.projectid.rstrip()+self.token.replace(")","")+self.depends
        # build smartsheet update command
        smartsheet_update_command = self.smartsheet_update_command + smartsheet_mokapipe_complete + self.runfolder +self.project+self.projectid.rstrip()+ self.depends+self.token.replace(")","")
        
        # write commands to bash script
        self.DNA_Nexus_bash_script.write(multiqc_command+"\n")
        self.DNA_Nexus_bash_script.write(smartsheet_update_command+"\n")
      
        # capture the workflow used
        app=workflow_path.replace("Workflows/","")

        # close bash script file handle
        self.DNA_Nexus_bash_script.close()

        # write to cron job script
        self.upload_agent_script_logfile.write("dx run commands issued - see "+self.bash_script+"\nMultiQC and Smartsheet complete apps set with the project id:"+self.projectid.rstrip()+"\n\njob ids captured from standard out:\n")
        
        # run a command to execute the bash script made above
        cmd="bash "+self.bash_script

        if not debug:
            # execute command
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        
            # capture the streams
            (out, err) = proc.communicate()
        else:
            out="x"
            err=""

        #capture standard out (the job ids) to the log file
        self.upload_agent_script_logfile.write(out)
        
        # if any standard error
        if err:
            # send email
            self.email_subject = "MOKAPIPE ALERT: Error message when starting pipeline"
            self.email_priority = 1 # high priority
            self.email_message = self.runfolder + " being processed using workflow " + app + "\nTHE PIPELINE MAY HAVE STARTED CORRECTLY. However, there was a standard error reported when starting pipeline.\nThe standard error messages are: "+ err + "Please see logfile at "+self.runfolderpath + "/" + upload_started_file
            
            # write error message to log file
            self.upload_agent_script_logfile.write("\n\n!!!!!!!!!Uh Oh!!!!!!!!\nstandard error: "+err+"\n\nemailing error message:\n"+self.email_message+"\n\n")
        else:
         # create sql string to update moka with
            DNA_list="('"
           # loop through unique list of dna numbers obtained from fastq filenames
            for DNA in set(self.list_of_DNA_numbers):
                # build the sq query
                DNA_list=DNA_list+DNA+"','"
            # close string
            DNA_list=DNA_list+")"

            # remove the excess ,' from the end of the string
            DNA_list=DNA_list.replace(",')",")")

            # build the rest of the sql update query
            sql="update NGSTest set PipelineVersion = "+moka_pipeline_ID+" where dna in " + DNA_list


            # email this query
            self.email_subject = "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for " + self.runfolder
            self.email_priority = 1 # high priority
            self.email_message = self.runfolder + " being processed using workflow " + app +"\n\nPlease update Moka using the query below:\n\n"+sql
                    
            if not debug:
                #call function to update smartsheet to say run in progress
                self.smartsheet_mokapipe_in_progress()
        
        if not debug:
            # send email
            self.send_an_email()
        

    def upload_rest_of_runfolder(self):
        # write status update to log file
        self.upload_agent_script_logfile.write("\n----------------------UPLOAD REST OF RUNFOLDER----------------------\n")

        # open file for upload agent standard out (in append mode)
        runfolder_upload_stdout_file = open(self.runfolderpath + "/" + upload_started_file, 'a')
        
        # distinguish between upload of fastq and rest of runfolder
        runfolder_upload_stdout_file.write("\n----------------------Uploading rest of runfolder "+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\n")

        # open file containing upload agent commands (in append mode)
        runfolder_upload_cmd_file = open(self.runfolderpath + "/" + runfolder_upload_cmds, 'a')

        # create the samplesheet name to copy
        samplesheet_name=self.runfolder+"_SampleSheet.csv"
        
        #copy samplesheet into project
        copyfile(samplesheets+samplesheet_name, self.runfolderpath+"/"+samplesheet_name)

        # write to the log file that samplesheet was copied and runfolder is being uploaded, linking to log files for cmds and stdout
        self.upload_agent_script_logfile.write("Copied samplesheet to runfolder\nUploading rest of run folder to Nexus using commands in "+self.runfolderpath + "/" + runfolder_upload_cmds +"\nsee standard out from these commands in log file @ "+self.runfolderpath + "/" + upload_started_file+"\n\n----------------CHECKING SUCCESSFUL UPLOAD OF RUNFOLDER----------------\n")

        # loop through the run folder
        for root, subFolder, files in os.walk(self.runfolderpath):
            # for every file 
            for item in files:
                # capture the path
                path=str(os.path.join(root,item))
                
                # skip image files
                if "/L00" in path:
                    pass
                #skip fastq files already uploaded
                elif path.endswith(".fastq.gz"):
                    pass
                # skip log files still being written to
                elif path.endswith(upload_started_file) or path.endswith(runfolder_upload_cmds) :
                    pass
                # skip samplesheet
                elif path.endswith("SampleSheet.csv"):
                    pass
                # otherwise upload
                else:
                    # Use path to build desitnation folder within nexus
                    path_to_upload=path                       
                    #remove the project prefix (002_), the path to the runfolders ("/media/data1/share") and the file name
                    path_for_nexus=path.replace(self.runfolder,self.nexusproject.replace(NexusProjectPrefix,"")).replace(runfolders,"").replace(item,"")

                    # build the nexus upload command                        
                    nexus_upload_command = upload_agent + " --auth-token "+Nexus_API_Key+" --project "+ self.nexusproject +"  --folder " + path_for_nexus + " --do-not-compress --upload-threads 10 " + path_to_upload
                
                    if not debug:
                        # copy the command to the cmd file
                        runfolder_upload_cmd_file.write(nexus_upload_command+"\n")
                        
                        # run the command, redirecting stderror to stdout
                        proc = subprocess.Popen([nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
                        
                        # capture the streams (err is redirected to out above)
                        (out, err) = proc.communicate()
                    
                    else:
                        runfolder_upload_cmd_file.write(nexus_upload_command+"\n")
                        out="x"
                        err="y"

                    
                    # capture standard out/standard error
                    runfolder_upload_stdout_file.write(out)

        # close log files
        runfolder_upload_stdout_file.close()
        runfolder_upload_cmd_file.close()

        # call function which looks for errors when uploading
        self.look_for_upload_errors_runfolder()
        
        # close the log file
        self.upload_agent_script_logfile.close()

        # rename file to show what runs were affected.
        self.rename=self.rename+self.runfolder
        os.rename(self.upload_agent_logfile_name,self.upload_agent_logfile_name.replace('.txt','')+self.rename+".txt")

        # capture the new file name so can continue to write to it.
        self.upload_agent_logfile_name=self.upload_agent_logfile_name.replace('.txt','')+self.rename+".txt"

        # call function to upload log files
        self.upload_log_files()

    def upload_log_files(self):
        ''' log files include:
        1. the log file for this script containing all commands used (/home/mokaguys/Documents/automate_demultiplexing_logfiles/Upload_agent_log)
        2. demultiplexing log file (/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files)
        3. nexus project creation logs (/home/mokaguys/Documents/automate_demultiplexing_logfiles/Nexus_project_creation_logs)
        4. runfolder_upload_commands (in the run folder)
        5. runfolder_upload_stdout (in the run folder)
        6. logfile used to set off the workflow (/home/mokaguys/Documents/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs)
        7. samplesheet
        '''

        #empty list to hold files (and paths) to be uploaded
        logfile_list=[]
        
        ######### path for upload agent log file (file1) #########
        # get full filepath for the log file containing the decisions made by this script
        upload_agent_log_file_to_upload=self.upload_agent_logfile_name
        # add to list
        logfile_list.append(upload_agent_log_file_to_upload)


        ######### demultiplexing log file (file2) #########
        # empty variable to build a list of files
        demultiplex_log=""
        #loop through files in demultiplex log folder (contains decisions made when demultiplexing script is run - have been renamed to contain run folder if a run was demultiplexed)
        for file in os.listdir(demultiplex_logfiles):
            # if runfolder in filename
            if self.runfolder in file:
                # add file path and file name to list
                demultiplex_log=demultiplex_logfiles+file
                logfile_list.append(demultiplex_log)


        ######### nexus project_creation_logfile (file 3) #########
        # get the full file path for file containing comands used to create and share nexus project
        nexus_project_creation_logfile=DNA_Nexus_project_creation_logfolder+ self.runfolder + ".sh"
        # add to list
        logfile_list.append(nexus_project_creation_logfile)        


        ######### runfolder upload commands (file 4) #########
        # get the full file path for the cmds used to upload fastq, runfolder and log files
        runfolder_upload_logfile_to_upload=self.runfolderpath + "/" + runfolder_upload_cmds
        # add to list
        logfile_list.append(runfolder_upload_logfile_to_upload)
        

        ######### runfolder upload stdout (file 5) #########
        # get the full file path for the file containing stdout/ stderr from upload agent
        runfolder_upload_logfile_to_upload=self.runfolderpath + "/" + upload_started_file
        # add to list
        logfile_list.append(runfolder_upload_logfile_to_upload)

        
        ######### bash script which sets off workflow (file 6) #########
        # add the file which sets off the dx run commands
        logfile_list.append(self.bash_script)


        ########## samplesheet (file7) #########
        # create a upload agent command for samplesheet (copied into the runfolder above) which is being uploaded into the runfolder
        samplesheet_nexus_upload_command = upload_agent + " --auth-token "+Nexus_API_Key+" --project "+ self.nexusproject +"  --folder /" + self.nexusproject.replace(NexusProjectPrefix,"")+"/" + " --do-not-compress --upload-threads 10 " + self.runfolderpath+"/"+self.runfolder+"_SampleSheet.csv "

        #create command line for files in the logfile_list (to be put into a logfiles subfolder)
        nexus_upload_command = upload_agent + " --auth-token "+Nexus_API_Key+" --project "+ self.nexusproject +"  --folder /" + self.nexusproject.replace(NexusProjectPrefix,"")+"/Logfiles/" + " --do-not-compress --upload-threads 10 " + " ".join(logfile_list)
        
        #write these commands to the runfolder_upload_cmds_logfile before upload.
        runfolder_upload_cmd_file = open(self.runfolderpath + "/" + runfolder_upload_cmds, 'a')
        runfolder_upload_cmd_file.write(samplesheet_nexus_upload_command+"\n"+nexus_upload_command)
        runfolder_upload_cmd_file.close()

        if not debug:
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([nexus_upload_command+" & "+samplesheet_nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
            
            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()
        
        else:
            print nexus_upload_command
            out="x"
            err="y"

        # capture stdout to log file containing stdour and stderr
        runfolder_upload_stdout_file = open(self.runfolderpath + "/" + upload_started_file, 'a')
        runfolder_upload_stdout_file.write("\n----------------------Uploading logfiles (this will not be included in the file within DNA Nexus) "+str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))+"-----------------\n")
        runfolder_upload_stdout_file.write(out)
        runfolder_upload_stdout_file.close()

        # check standard out from upload of log files
        # open logfile first to write info from check
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name,'a')
        self.look_for_upload_errors_logfiles.write("\n----------------CHECKING SUCCESSFUL UPLOAD OF LOGFILES (this will not be in DNA Nexus)----------------\n")
        
        # call function to check stdout
        self.look_for_upload_errors_logfiles()

        # send email to report backup of runfolder complete
        self.email_subject = "MOKAPIPE ALERT: backup of " + self.runfolder + " completed"
        self.email_priority = 3
        self.email_message = self.runfolder + " \t has been uploaded to DNA Nexus :-)\nPlease see log file at: " + self.runfolderpath + "/" + upload_started_file
        
        if not debug:
            # send email.            
            self.send_an_email()

        # close log file
        self.upload_agent_script_logfile.close()

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
        payload='{"cells": [{"columnId": '+self.ss_title+', "value": "'+self.runfolder+'"}, {"columnId": '+self.ss_description+', "value": "MokaPipe"},{"columnId": '+self.ss_samples+', "value": '+str(count)+'},{"columnId": '+self.ss_status+', "value": "In Progress"},{"columnId": '+self.ss_priority+', "value": "Medium"},{"columnId": '+self.ss_assigned+', "value": "aledjones@nhs.net"},{"columnId": '+self.ss_received+', "value": "'+str(self.smartsheet_now)+'"}], "toBottom":true}'
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

        self.upload_agent_script_logfile.write("\n----------------------UPDATE SMARTSHEET----------------------\n")
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

    def look_for_upload_errors_fastq(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file'''
        # Open the log file and read to look for the string "ERROR"               
        if "ERROR" in open(self.runfolderpath + "/" + upload_started_file).read():
            #send an email if the update failed
            self.email_subject="MOKAPIPE ALERT: FASTQ UPLOAD MAY NOT BE COMPLETE"
            self.email_message="The string \"ERROR\" was present in the upload agent standard out when uploading FastQ files. See the log file @ "+self.runfolderpath + "/" + upload_started_file
            self.email_priority = 1 # high priority
            self.send_an_email()
            #write the email message to log file
            self.upload_agent_script_logfile.write(self.email_message)
        else:
            #write to log file check was ok
            self.upload_agent_script_logfile.write("The string \"ERROR\" was not present in standard out\n")


    def look_for_upload_errors_runfolder(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file
        NB any errors from the fastq upload would also be detected here.'''

        # Open the log file and read to look for the string "ERROR"
        if "ERROR" in open(self.runfolderpath + "/" + upload_started_file).read():
            #send an email if the update failed
            self.email_subject="MOKAPIPE ALERT: RUNFOLDER UPLOAD MAY NOT BE COMPLETE"
            self.email_message="The string \"ERROR\" was present in the upload agent standard out when uploading the rest of the run folder. See the log file @ "+self.runfolderpath + "/" + upload_started_file+"\nNB this error may be a repeat of an error when uploading the fastq files"
            self.email_priority = 1 # high priority
            self.send_an_email()
            #write the email message to log file
            self.upload_agent_script_logfile.write(self.email_message)
        else:
            #write to log file check was ok
            self.upload_agent_script_logfile.write("The string \"ERROR\" was not present in standard out\n")

    def look_for_upload_errors_logfiles(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file
        NB any errors from the fastq upload and run folderwould also be detected here.'''

        # Open the log file and read to look for the string "ERROR"
        if "ERROR" in open(self.runfolderpath + "/" + upload_started_file).read():
            #send an email if the update failed
            self.email_subject="MOKAPIPE ALERT: UPLOAD OF LOGFILES MAY NOT BE COMPLETE"
            self.email_message="The string \"ERROR\" was present in the upload agent standard out when uploading the log files. See the log file @ "+self.runfolderpath + "/" + upload_started_file+"\nNB this error may be a repeat of an error from previous upload steps"
            self.email_priority = 1 # high priority
            self.send_an_email()
            #write the email message to log file
            self.upload_agent_script_logfile.write(self.email_message)
        else:
            #write to log file check was ok
            self.upload_agent_script_logfile.write("The string \"ERROR\" was not present in standard out\n")


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()

