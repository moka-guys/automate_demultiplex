'''
Created on 21 Sep 2016

Once demultiplexing has been complete the files require uploading to DNANexus.

This script will be scheduled to run and identify any folders that have not been uploaded.

It will trigger the upload agent to upload into the required project

@author: aled
'''

import os
import re
import subprocess
import datetime
import smtplib
from email.message import Message
from shutil import copyfile
import requests
# import config file
import automate_demultiplex_config as config
# import function which reads the git tag
import git_tag as git_tag


class get_list_of_runs():
    '''Loop through the directories in the directory containing the runfolders'''

    def __init__(self):
        # set variables for time
        self.now = ""

    def loop_through_runs(self):
        # set a time stamp to name the log file
        self.now = str('{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now()))

        # create a list of all the folders in the runfolders directory
        if config.debug:  # use test folder(s)
            all_runfolders = config.upload_test_folders
        else:
            all_runfolders = os.listdir(config.runfolders)

        # for each folder if it is not samplesheets/tar.gz folder pass the runfolder to the next class
        for folder in all_runfolders:
            # Ignore folders in the list config.ignore_directories and test that it is a directory (ignoring files)
            if folder not in config.ignore_directories and os.path.isdir(os.path.join(config.runfolders, folder)):
                # pass folder and timestamp to class
                upload2Nexus().already_uploaded(folder, self.now)

        # combine all the log files
        self.combine_log_files()

    def combine_log_files(self):
        # count number of log files that match the time stamp
        count = 0
        # empty list
        list_of_logfiles = []
        # loop through the folder containing log files
        for log in os.listdir(config.upload_agent_logfile):
            # if is one with this time stamp, ie if was made by this running of this script
            if self.now in log:
                # add count and append to list
                count += 1
                list_of_logfiles.append(config.upload_agent_logfile + log)

        # if more than one log file we want to concatenate them
        if count > 1:
            # create the start of the path to the logfile using the path to the log file and the time stamp (without.txt extension)
            logfile_name = os.path.join(config.upload_agent_logfile, self.now)
            # loop through all the log files to capture the run names
            for logfile in list_of_logfiles:
                # skip the empty timestamp
                if self.now + "_.txt" in logfile:
                    pass
                else:
                    # remove the time stamp and the logfolder path from each filename in the list and concatenate to the logfile_name created above
                    logfile_name = logfile_name + logfile.replace(self.now, '').replace(config.upload_agent_logfile, '').replace(".txt", "").replace(".txt.txt", "")

            # add extension
            logfile_name = logfile_name + ".txt"

            # concatenate all the remaining filenames into a string, seperated by spaces
            remaining_files = " ".join(list_of_logfiles)

            # combine all into one file with the longest filename (that will have the run folder name)
            cmd = "cat " + remaining_files + " >> " + logfile_name
            # remove the files that have been written to the longer file (removing the combined log file name from this list)
            rmcmd = "rm " + remaining_files.replace(logfile_name, "")

            # run the commands
            subprocess.call([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            subprocess.call([rmcmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)


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

        # upload_agent_logfile
        # self.upload_agent_logfile = "/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_log/"
        self.upload_agent_logfile_name = ""
        self.upload_agent_script_logfile = ""

        # string of fastqs for upload agent
        self.fastq_string = ""

        # list of fastqs to get ngs run number and WES batch
        self.list_of_samples = []

        self.list_of_DNA_numbers_WES = []
        self.list_of_DNA_numbers_Onc = []
        self.list_of_DNA_numbers_nonWES = []

        # strings for NGSrun and wes numbers
        self.NGS_run = ''  # first element of fastq file name.
        self.wes_number = ''  # WES number near the end of fastq file name.

        # variables to rename log file.
        self.rename = ""
        self.now = ""

        # ####################################DNA Nexus########################
        # bash script that is used to execute dx commands
        self.bash_script = ""
        self.DNA_Nexus_bash_script = ""

        # DNA Nexus commands
        self.source_command = "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\ndepends_list=''\n"

        self.createprojectcommand = "project_id=\"$(dx new project --bill-to %s \"%s\" --brief --auth-token " + config.Nexus_API_Key + ")\"\n"
        self.addprojecttag = "dx tag $project_id "
        self.base_command = "jobid=$(dx run " + config.app_project + config.mokapipe_path + " -y"
        self.wes_command = "jobid=$(dx run " + config.app_project + config.wes_path + " -y"
        self.peddy_command = "jobid=$(dx run " + config.app_project + config.peddy_path
        self.multiqc_command = "jobid=$(dx run " + config.app_project + config.multiqc_path
        self.upload_multiqc_command = "dx run " + config.app_project + config.upload_multiqc_path + " -y"
        self.smartsheet_update_command = "dx run " + config.app_project + config.smartsheet_path
        self.RPKM_command = "dx run " + config.app_project + config.RPKM_path
        self.mokaonc_command = "jobid=$(dx run " + config.app_project + config.mokaonc_path + " -y"
        self.mokaamp_command = "jobid=$(dx run " + config.app_project + config.mokaamp_path + " -y"

        # project to upload run folder into
        self.nexusproject = config.NexusProjectPrefix

        # project_ID of created project
        self.projectid = ""

        # arguments for command
        self.dest = " --dest="
        self.project = " --project="
        self.token = " --brief --auth-token " + config.Nexus_API_Key + ")"
        self.depends = " -y $depends_list"

        # argument to capture jobids
        self.depends_list = "depends_list=\"${depends_list} -d ${jobid} \""
        self.dx_run = []

        # create path to data in nexus eg /runfolder/Data
        self.nexus_path = ""

        # list of panels
        self.panels_in_run = []

        # command to restart upload agent part 1
        self.restart_ua_1 = "ua_status=1; while [ $ua_status -ne 0 ]; do "
        self.restart_ua_2 = "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo \"temporary issue when uploading file %s\"; fi ; done"

        # error message if upload agent fails
        self.ua_error = "Error Message: 'Could not resolve: api.dnanexus.com"

        # ######################email message###############################
        self.email_subject = ""
        self.email_message = ""
        self.email_priority = 3

        # ########################################smartsheet API##############
        self.api_key = config.smartsheet_api_key

        # sheet id
        # self.sheetid=sheetid
        # newly inserted row
        self.rowid = ""

        # time stamp
        self.smartsheet_now = ""

        # requests info
        self.headers = {"Authorization": "Bearer " + config.smartsheet_api_key, "Content-Type": "application/json"}
        self.url = 'https://api.smartsheet.com/2.0/sheets/' + str(config.smartsheet_sheetid)

    def already_uploaded(self, runfolder, now):
        '''check folder hasn't already been uploaded'''
        # capture timestamp
        self.now = now

        # open the logfile for this hour's cron job.
        self.upload_agent_logfile_name = config.upload_agent_logfile + self.now + "_" + self.rename + ".txt"
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name, 'a')

        # capture the runfolder
        self.runfolder = str(runfolder)

        # create full path to runfolder
        self.runfolderpath = os.path.join(config.runfolders, self.runfolder)

        # write to log file including the github repo tag and time stamp
        self.upload_agent_script_logfile.write("automate_demultiplexing release:" + git_tag.git_tag() + "\n----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) +
            "----------------------\nAssessing " + self.runfolderpath + "\n\n----------------------HAS THIS FOLDER ALREADY BEEN UPLOADED?----------------------\n")

        # look for the file denoting the upload has started
        if os.path.isfile(os.path.join(self.runfolderpath, config.upload_started_file)):
            if not config.debug:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present \n----------------------STOP----------------------\n")
            else:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present but DEBUG MODE IS TRUE SO CONTINUING.......\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
                self.demultiplex_completed_successfully()
        else:
            # if not check demultiplex has finished succesfully and write to file
            # print "not already uploaded"
            self.upload_agent_script_logfile.write("NO - self.upload_started_file not present so continue\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
            self.demultiplex_completed_successfully()

    def demultiplex_completed_successfully(self):
        '''check if the demultiplexing finished successfully by reading the last line of the demultiplex log'''

        # check demultiplexing has actually been done
        if os.path.isfile(os.path.join(config.runfolders, self.runfolder, self.demultiplexed)):
            # open log file
            logfile = open(os.path.join(config.runfolders, self.runfolder, self.demultiplexed), 'r')

            # find the last line of the demultiplexing log file
            lastline = ""
            for i in logfile:
                lastline = i

            # check if the success statement is in the last line
            if config.logfile_success in lastline:
                self.upload_agent_script_logfile.write("Demultiplex was successfully completed.\ncompiling a list of fastqs....... ")
                # if successfull call the module which creates a list of fastqs
                self.find_fastqs()
            else:
                # write to logfile that demultplex was not successful
                self.upload_agent_script_logfile.write("!!!!!!!DEMULTIPLEXING DID NOT COMPLETE SUCCESSFULLY.!!!!!!!!!\n----------------------STOP----------------------\n")
        else:
            # write to logfile that not yet demultiplexed
            self.upload_agent_script_logfile.write("demultiplexing has not been performed.\n----------------------STOP----------------------\n")

    def find_fastqs(self):
        ''' find all the fastqs and send them to the upload command'''

        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath + config.fastq_folder

        # create a list of all files within the fastq folder
        all_fastqs = os.listdir(self.fastq_folder_path)

        # list of fastqs not to be processed
        not_processed = []

        # set counts to catch when not a panel to go through Nexus
        to_be_nexified = 0
        # find all fastqs
        for fastq in all_fastqs:
            if fastq.endswith('fastq.gz'):
                # exclude undertermined samples
                if fastq.startswith('Undetermined'):
                    pass
                else:
                    # set up a flag to record fastq files which will not be processed
                    recognised_panel = False
                    for panel in config.panelnumbers:
                        if recognised_panel:
                            pass
                        else:
                            # add underscore to ensure Pan1000 is not true when looking for Pan100
                            if panel + "_" in fastq:
                                # count sample
                                to_be_nexified += 1
                                recognised_panel = True
                                # build the list of fastqs with full file paths
                                self.fastq_string = self.fastq_string + " " + self.fastq_folder_path + "/" + fastq
                                # add the fastq name to a list to be used in create_nexus_file_path
                                self.list_of_samples.append(fastq)
                                # if WES append to WES list:
                                if panel == "Pan493":
                                    # split line to get DNA number
                                    self.list_of_DNA_numbers_WES.append(fastq.split("_")[2])
                                # if oncology panel append onc list:
                                elif panel in config.oncology_panels:
                                    # split line to get DNA number
                                    self.list_of_DNA_numbers_Onc.append(fastq.split("_")[2])
                                # otherwise add to non_WES list
                                else:
                                    self.list_of_DNA_numbers_nonWES.append(fastq.split("_")[2])
                                    # record all non-WES panels for RPKM
                                    self.panels_in_run.append(panel)
                    # If an unrecognised panel number record this in a list
                    if not recognised_panel:
                        not_processed.append(fastq)

        # if there were no WES samples state this in log message and stop
        if to_be_nexified == 0:
            self.upload_agent_script_logfile.write("List of fastqs did not contain any known Pan numbers. Stopping\n")

        # else continue
        else:
            if len(not_processed) > 0:
                # add to logger
                self.logger("unrecognised panel number found in run " + self.runfolder, "UA_fail")
                # write to logfile
                self.upload_agent_script_logfile.write(str(to_be_nexified) + " fastqs found.\nSome fastq files contained an unrecognised panel number: " + ",".join(not_processed) +
                    "\n\n----------------------PREPARING UPLOAD OF FASTQS----------------------\ndefining path for fastq files.......")
            else:
                self.upload_agent_script_logfile.write(str(to_be_nexified) + " fastqs found.\n\n----------------------PREPARING UPLOAD OF FASTQS----------------------\ndefining path for fastq files.......")
            # build the file path with WES batch and NGS run numbers
            self.create_nexus_file_path()

            # create nexus project
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
        NGS_numbers = []

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

                # This should split the string in half again, with the first element either _5 or 5 depending if it's WES_5 or WES5
                # append this to WES (which was replaced as part of the split) and add to a list
                wesrun = "WES" + splitfastq2[0].replace('_', '')
                WES_numbers.append(wesrun)

        # if there are wes batch numbers
        if len(WES_numbers) > 0:
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
            self.nexus_path = self.runfolder + "_" + self.NGS_run + "_" + self.wes_number + config.fastq_folder
            # build project name
            self.nexusproject = self.nexusproject + self.runfolder + "_" + self.NGS_run + "_" + self.wes_number
        else:
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.NGS_run + config.fastq_folder
            # build project name
            self.nexusproject = self.nexusproject + self.runfolder + "_" + self.NGS_run

        # write to log
        self.upload_agent_script_logfile.write("fastqs will be uploaded to " + self.nexus_path + "\n\n----------------------CREATE AND SHARED DNA NEXUS PROJECT----------------------\n")

    def upload(self):
        '''takes a list of all the fastqs (with full paths) and calls the upload agent.'''

        # perform upload agent test
        self.test_upload_agent()

        # test dx toolkit installation
        self.test_dx_toolkit()

        # build the nexus upload command
        nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
            + "  --folder /" + self.nexus_path + " --do-not-compress --upload-threads 10" + self.fastq_string + self.restart_ua_2 % ("fastq files")

        # open a file to hold all the upload agent commands
        runfolder_upload_cmd_file = open(os.path.join(self.runfolderpath, config.runfolder_upload_cmds), 'w')
        # write fastq upload commands and a way of distinguishing between upload of fastq and rest of runfolder
        runfolder_upload_cmd_file.write("----------------------Upload of fastqs----------------------\n" + nexus_upload_command + "\n\n----------------------Upload rest of runfolder----------------------\n")

        # write to logfile
        self.upload_agent_script_logfile.write("Uploading Fastqs to Nexus. See commands at " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds) +
            "\n\n----------------------CHECKING SUCCESSFUL UPLOAD OF FASTQS----------------------\n")

        # open file to show upload has started and to hold upload agent standard out
        upload_started = open(os.path.join(self.runfolderpath, config.upload_started_file), 'a')

        if not config.debug:
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)

            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()
        else:
            out = "x"
            err = "y"

        # write to log
        upload_started.write("\n----------------------Uploading fastqs " + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n" + out)
        upload_started.close()

        # check fastqs uploaded successfully
        self.look_for_upload_errors_fastq()

        # start pipeline
        self.create_run_pipeline_command()

        # back up rest of run folder to nexus
        self.upload_rest_of_runfolder()

    def send_an_email(self, to):
        '''function to send an email. uses self.email_subject, self.email_message and self.email_priority'''
        # create message object
        m = Message()
        # set priority
        m['X-Priority'] = str(self.email_priority)
        # set subject
        m['Subject'] = self.email_subject
        # set body
        m.set_payload(self.email_message)

        # server details
        server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
        server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
        server.starttls()
        server.ehlo()
        server.login(config.user, config.pw)
        server.sendmail(config.me, to, m.as_string())

        # write to logfile
        self.upload_agent_script_logfile.write("\nEmail sent to...... " + str(to) + "\nsubject:" + self.email_subject + "\nbody:" + self.email_message + "\n\n")
        self.logger("Upload Agent email sent" + str(to) + ". Subject:" + self.email_subject + ". Body:" + self.email_message, "UA_pass")

    def test_upload_agent(self):
        '''test the upload agent is installed'''

        # command
        command = config.upload_agent + " --version"

        # run the command
        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # capture the streams
        (out, err) = proc.communicate()

        if "Upload Agent Version:" not in out:
            self.logger("Upload Agent Test Failed", "UA_fail")
            raise Exception, "Upload agent not installed"

        self.logger("Upload Agent function test passed", "UA_pass")

        # write this to the log file
        self.upload_agent_script_logfile.write("upload agent check passed\n\n----------------------TEST DX TOOLKIT IS FUNCTIONING----------------------\n")

    def test_dx_toolkit(self):
        '''test the dx toolkit is installed'''

        # run the command
        proc = subprocess.Popen(config.dx_sdk_test, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

        # capture the streams
        (out, err) = proc.communicate()

        if config.dx_sdk_test_expected_result not in out:
            self.logger("dx toolkit function test failed", "UA_fail")
            raise Exception, "dx toolkit not installed"
        self.logger("dx toolkit function test passed", "UA_pass")
        # write this to the log file
        self.upload_agent_script_logfile.write("dx toolkit check passed\n\n----------------------UPLOAD FASTQS----------------------\n")

    def create_project(self):
        '''create a project for each run names 002_runfolder'''
        project_bash_script = config.DNA_Nexus_project_creation_logfolder + self.runfolder + ".sh"

        # open bash script
        DNA_Nexus_bash_script = open(project_bash_script, 'w')
        DNA_Nexus_bash_script.write(self.source_command)
        DNA_Nexus_bash_script.write(self.createprojectcommand % (config.prod_organisation, self.nexusproject))
        # DNA_Nexus_bash_script.write(self.createprojectcommand % (dev_organisation,self.nexusproject))

        # Share the project with the nexus usernames in the list in config file
        # first give view permissions
        for user in config.view_users:
            DNA_Nexus_bash_script.write("dx invite %s $project_id VIEW --no-email --auth-token %s\n" % (user, config.Nexus_API_Key))
        # then give admin permissions - ensure done in this order incase some users are in both lists.
        for user in config.admin_users:
            DNA_Nexus_bash_script.write("dx invite %s $project_id ADMINISTER --no-email --auth-token %s\n" % (user, config.Nexus_API_Key))

        # add a tag to denote live project (as opposed to archived)
        DNA_Nexus_bash_script.write(self.addprojecttag + config.live_tag + " --auth-token %s\n" % (config.Nexus_API_Key))

        # echo the project id so it can be captured below
        DNA_Nexus_bash_script.write("echo $project_id")

        # close before running
        DNA_Nexus_bash_script.close()

        if not config.debug:
            # run a command to execute the bash script made above
            cmd = "bash " + project_bash_script
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # capture the streams
            (out, err) = proc.communicate()

            # capture out into std_out variable
            std_out = out

            # split std_out on "project" and get the last item to capture the project ID
            self.projectid = "project" + std_out.split("project")[-1]

            # if haven't captured a project id report an error to system log
            if self.projectid == "":
                self.logger("failed to create project in dna nexus " + self.nexusproject, "UA_fail")

                # raise exception to stop script
                raise Exception, "Unable to create DNA Nexus project"
            else:
                # build a string of the users list to make log look nice
                user_str = ",".join(config.view_users)
                # write to log
                self.upload_agent_script_logfile.write("DNA Nexus project %s created and shared (VIEW) to " % (self.nexusproject) + user_str +
                    "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (self.projectid))
                # repeat for admins
                user_str = ",".join(config.admin_users)
                # write to log
                self.upload_agent_script_logfile.write("DNA Nexus project %s created and shared (ADMIN) to " % (self.nexusproject) + user_str +
                    "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (self.projectid))

        else:
            # for debug mode use example project id
            self.projectid = "project-F2gzY2j0xyXJ4x3z5Pq8BjQ4"

    def create_run_pipeline_command(self):
        '''loop through the list of fastqs to generate commands used to initiate the pipeline.'''

        # Update script log file to say what is being done.
        self.upload_agent_script_logfile.write("\n\n----------------------RUN WORKFLOW----------------------\n")

        # define the bash script to contain the dx run commands
        self.bash_script = config.DNA_Nexus_workflow_logfolder + self.runfolder + ".sh"

        # open bash script
        self.DNA_Nexus_bash_script = open(self.bash_script, 'w')

        # write command to log file
        self.DNA_Nexus_bash_script.write(self.source_command)

        # initilise list of oncology fastq
        mokaonc_fastq_list = []

        # loop through list of fastq files
        for fastq in self.list_of_samples:
            # take read one
            if "_R1_" in fastq:
                # assign read1
                read1 = os.path.join(self.nexus_path, fastq)
                # assign read2 by replacing R1 with R2
                read2 = os.path.join(self.nexus_path, fastq.replace("_R1_", "_R2_"))

                # get panel name and bed file
                for panel in config.panelnumbers:
                    # add underscore to Pan number so Pan1000 is not true when looking for Pan100
                    # Find oncology samples and generate a list of fastq to run through amplivar pipeline
                    if panel + "_" in fastq and panel in config.oncology_panels:
                        # if it's an mokaonc (amplivar) panel add fastq to list - this stops other oncology panels being processed by this
                        if panel == "Pan1190":
                            mokaonc_fastq_list.append(read1)
                            mokaonc_fastq_list.append(read2)

                        # specify input files for stages
                        sambamba_bedfile = config.app_project + config.bedfile_folder + panel + "Sambamba.bed"
                        picard_bedfile = config.app_project + config.bedfile_folder + panel + ".bed"
                        mokaamp_bed_PE_input = config.app_project + config.bedfile_folder + panel + "_PE.bed"
                        variant_calling_bed = config.app_project + config.bedfile_folder + panel + "_flat.bed"

                    # Find NGS or WES samples
                    elif panel + "_" in fastq:
                        # build path in nexus to the relevant sambamba bed
                        sambamba_bedfile = config.app_project + config.bedfile_folder + panel + "dataSambamba.bed"

                        # specify moka vendor bedfile
                        if panel == "Pan493":  # identify WES tests
                            # skip for WES samples as mokavendor files are already specified in DNAnexus workflow for MokaWES
                            pass
                        elif panel == "Pan1620":  # Identify focused exome tests
                            # specify this for the focused exome
                            moka_vendor_bedfile = config.app_project + config.bedfile_folder + "UK_focused_exome_3_col.bed"
                            # use the exome bedfile to calculate coverage
                            sambamba_bedfile = config.app_project + config.bedfile_folder + "Pan493dataSambamba.bed"
                        else:
                            # otherwise build path in nexus to the relevant bed file
                            moka_vendor_bedfile = config.app_project + config.bedfile_folder + panel + "data.bed"

                        # use same panelname to get the email which will be used to upload to IVA
                        ingenuity_email = config.email_panel_dict[panel]

                # MokaAMP command construction for mokaamp samples.
                if "Pan1190_" in fastq or "Pan2684_" in fastq:
                    # create the input command for the fastqc
                    read1_cmd = self.nexusproject + ":" + read1
                    read2_cmd = self.nexusproject + ":" + read2

                    # set the destination command as the root of the project
                    dest_cmd = self.nexusproject + ":/"

                    # create the MokaAMP dx command
                    command = self.mokaamp_command + config.mokaamp_fastq_R1_stage + read1_cmd + \
                        config.mokaamp_fastq_R2_stage + read2_cmd + \
                        config.mokaamp_mokapicard_bed_stage + picard_bedfile + \
                        config.mokaamp_mokapicard_capturetype_stage + config.mokaamp_capture_type + \
                        config.mokaamp_bamclipper_BEDPE_stage + mokaamp_bed_PE_input + \
                        config.mokaamp_chanjo_cov_level_stage + config.mokaamp_coverage_level + \
                        config.mokaamp_sambamba_bed_stage + sambamba_bedfile + \
                        config.mokaamp_vardict_bed_stage + variant_calling_bed + \
                        config.mokaamp_varscan_bed_stage + variant_calling_bed + \
                        config.mokaamp_lofreq_bed_stage + variant_calling_bed + \
                        config.mokaamp_varscan_strandfilter_stage + config.mokaamp_strandfilter + \
                        self.dest + dest_cmd + self.token

                    # remove the bit that adds the job to the depends on list for the negative control as varscan fails on nearempty/-empty BAM files and this will stop multiqc etc running
                    if "NTCcon" in read1:
                        command = command.replace("jobid=$(", "").replace(config.Nexus_API_Key + ")", config.Nexus_API_Key)

                    # add command for each pair of fastqs to a list
                    self.dx_run.append(command)

                # Generate command to call MokaWES workflow for WES samples
                elif "Pan493_" in fastq:
                    # create the input command for the fastqc
                    read1_cmd = self.nexusproject + ":" + read1
                    read2_cmd = self.nexusproject + ":" + read2

                    # set the destination command as the root of the project
                    dest_cmd = self.nexusproject + ":/"

                    # if a sample name is not provided sention cleans the fastq file name to create one. However this includes removing all "_1", which is not ideal - theerfore specify one, using everything before "_R1" from read1 fastq filename
                    sention_sample_name = fastq.split("_R1_")[0]

                    # create the MokaWES dx command
                    command = self.wes_command + config.wes_fastqc1 + read1_cmd + config.wes_fastqc2 + read2_cmd + \
                        config.wes_sention_samplename + sention_sample_name + \
                        config.wes_iva_email_input + ingenuity_email + \
                        self.dest + dest_cmd + self.token

                    # add command for each pair of fastqs to a list
                    self.dx_run.append(command)

                # Set Mokapipe command for all other samples
                else:
                    # create the input command for the fastqc and BWA inputs
                    read1_cmd = self.nexusproject + ":" + read1
                    read2_cmd = self.nexusproject + ":" + read2

                    # set the destination command as the root of the project
                    dest_cmd = self.nexusproject + ":/"

                    # create the dx command
                    command = self.base_command + config.mokapipe_fastqc1 + read1_cmd \
                        + config.mokapipe_fastqc2 + read2_cmd \
                        + config.mokapipe_sambamba_input + sambamba_bedfile \
                        + config.mokapipe_mokapicard_vendorbed_input + moka_vendor_bedfile \
                        + config.mokapipe_iva_email_input + ingenuity_email \
                        + self.dest + dest_cmd + self.token

                    # add command for each pair of fastqs to a list
                    self.dx_run.append(command)

        # if oncology samples present, construct Amplivar dx run command inputs
        if len(mokaonc_fastq_list) > 1:
            command = self.mokaonc_command
            for fastq in mokaonc_fastq_list:
                read_cmd = config.mokaonc_fq_input + self.nexusproject + ":" + fastq
                command = command + read_cmd

            # set the destination command as the root of the project in dir AmplivarOutput
            dest_cmd = self.nexusproject + ":/Onco_Output"
            # create the dx command include email address for ingenuity
            command = command + config.mokaonc_ingenuity + config.oncology_email + self.dest + dest_cmd + self.token
            # add command to list
            self.dx_run.append(command)

        # call module to issue the dx run commands
        self.run_pipeline()

        # record timestamp at end of bash script
        self.DNA_Nexus_bash_script = open(self.bash_script, 'a')
        self.DNA_Nexus_bash_script.write("#----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")
        self.DNA_Nexus_bash_script.close()

    def run_pipeline(self):
        '''issue dna nexus run commands, and define what extra apps are run once all workflows are completed.
        The list of apps and workflows used is included in the 'MOKAPIPE ALERT - ACTION NEEDED' email'''

        # loop through all dx_run commands and generate a list of commands/ workflow paths for the alert email
        # Identify different workflows to direct/ define the running of additional apps following completion of the workflow

        # Flag to identify any WES samples - used to direct additional apps
        wes = False
        mokaamp = False
        custom_panel = False
        workflows = []
        # loop through each command in the dx run list
        for command in self.dx_run:
            # write command to log file
            self.DNA_Nexus_bash_script.write(command + "\n")
            # If command isn't a MokaAmp negative control, write line to append job id to depends_list
            if not re.search('MokaAMP.*NTCcon', command):
                self.DNA_Nexus_bash_script.write(self.depends_list + "\n")
            # Identify the workflows run (for notification email)
            if "Pan1190_" in command:
                workflows.append(config.mokaonc_path.replace("Workflows/", ""))
                workflows.append(config.mokaamp_path.replace("Workflows/", ""))
                # Update Flag to call mokaamp specific apps
                mokaamp = True
            elif "Pan2684_" in command:
                workflows.append(config.mokaamp_path.replace("Workflows/", ""))
                # Update Flag to call mokaamp specific apps
                mokaamp = True
            elif "Pan493_" in command:
                # Update Flag to call WES specific apps
                wes = True
                workflows.append(config.wes_path.replace("Workflows/", ""))
            else:
                # file structure not required for email notification, only keep the workflow name
                workflows.append(config.mokapipe_path.replace("Workflows/", ""))
                custom_panel = True

        #  If WES need to run peddy and use specific multiqc coverage level
        if wes:
            # state the coverage level used by multiqc, converting to str to help concatenation when building dx run cmd.
            multiqc_coverage_level = str(config.wes_multiqc_coverage_level)
            # build peddy command - eg command = jobid=$(dx run peddy -iproject_for_peddy = 002_170222_ALEDTEST --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid)
            peddy_command = self.peddy_command + config.peddy_project_input + self.nexusproject + self.project + self.projectid.rstrip() + self.depends + self.token
            # write peddy run commands to bash script
            self.DNA_Nexus_bash_script.write(peddy_command + "\n")
            # write line to append job id to depends_list so downstream functions (e.g. MultiQC and smartsheet) wait for peddy to complete
            self.DNA_Nexus_bash_script.write(self.depends_list + "\n")
        # if custom panel state coverage level
        elif custom_panel:
            multiqc_coverage_level = config.custom_panel_multiqc_coverage_level
        elif mokaamp:
            multiqc_coverage_level = config.mokaamp_multiqc_coverage_level
        # build multiqc command, capturing the job id- eg command = jobid=$(dx run multiqc -iproject_for_multiqc=002_170222_ALEDTEST -icoveragelevel=20 --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid --brief --auth xyz)
        multiqc_command = self.multiqc_command + config.multiqc_project_input + self.nexusproject + config.multiqc_coverage_level_input + multiqc_coverage_level \
            + self.project + self.projectid.rstrip() + self.depends + self.token
        # build upload_multiqc_report command. Need to strip the close bracket from  self.token as this is used when capturing jobids
        # use the job id from multiqc command to define the input for this app
        upload_multiqc_command = self.upload_multiqc_command + config.upload_multiqc_input + "$jobid:" + config.multiqc_html_output + self.project + self.projectid.rstrip() + self.token.rstrip(")")
        # write command to bash script
        self.DNA_Nexus_bash_script.write(multiqc_command + "\n" + upload_multiqc_command + "\n")

        # build smartsheet update command
        smartsheet_update_command = self.smartsheet_update_command + config.smartsheet_mokapipe_complete + self.runfolder + self.project + self.projectid.rstrip() + self.depends + self.token.rstrip(")")
        # write commands to bash script
        self.DNA_Nexus_bash_script.write(smartsheet_update_command + "\n")

        # if there are custom panels run RPKM analysis
        if len(self.panels_in_run) > 0:
            self.RPKM()

        # close bash script file handle
        self.DNA_Nexus_bash_script.close()

        # write to cron job script
        self.upload_agent_script_logfile.write("dx run commands issued - see " + self.bash_script + "\nMultiQC and Smartsheet complete apps set with the project id:" + self.projectid.rstrip() +
            "\n\njob ids captured from standard out:\n")

        # run a command to execute the bash script made above
        cmd = "bash " + self.bash_script

        if not config.debug:
            # execute command
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # capture the streams
            (out, err) = proc.communicate()
        else:
            out = "x"
            err = ""

        # capture standard out (the job ids) to the log file
        self.upload_agent_script_logfile.write(out)

        # if any standard error
        if err:
            self.logger("Error when starting pipeline for run " + self.runfolder + " stderror = " + err, "UA_fail")

            # write error message to log file# exact error message is written to log file by logger function
            self.upload_agent_script_logfile.write("\n\n!!!!!!!!!Uh Oh!!!!!!!!\nstandard error: " + err + "\n\n")
        else:
            # write error message to log file
            self.logger("dx run commands issued without error for run " + self.runfolder, "UA_pass")

        # create empty list for the sql queries
        sql = []
        # Set variable to count the number of records to be updated by SQL
        records = 0

        # loop through the WES DNA numbers to generate sql query to record Pipeline version
        if len(self.list_of_DNA_numbers_WES) > 0:
            # count the number of records the SQL will update to include in email - (WES)
            if records == 0:
                records = len(set(self.list_of_DNA_numbers_WES))
            else:
                records += len(set(self.list_of_DNA_numbers_WES))

            # start string
            DNA_list = "('"
            # loop through unique list of dna numbers obtained from fastq filenames
            for DNA in set(self.list_of_DNA_numbers_WES):
                # build the sql query
                DNA_list = DNA_list + DNA + "','"
            # close string
            DNA_list = DNA_list + ")"
            # remove the excess ,' from the end of the string
            DNA_list = DNA_list.replace(",')", ")")

            # build the rest of the sql update query and append to list.
            # Query will update pipeline and test status for tests which are currently active
            sql.append("update NGSTest set PipelineVersion = " + config.mokawes_pipeline_ID + " , StatusID = " + config.mokastatus_dataproc_ID + " where dna in " + DNA_list + " and StatusID = " + config.mokastat_nextsq_ID)

        # custom panels requires insert queries (one per sample)
        if len(self.list_of_DNA_numbers_nonWES) > 0:
            # count the number of records SQL will update to include in email (non-WES)
            if records == 0:
                records = len(set(self.list_of_DNA_numbers_nonWES))
            else:
                records += len(set(self.list_of_DNA_numbers_nonWES))

            # loop through unique list of dna numbers obtained from fastq filenames
            for DNA in set(self.list_of_DNA_numbers_nonWES):
                # build the rest of the sql update query
                sql.append("insert into NGSCustomRuns(DNAnumber,PipelineVersion) values ('" + DNA + "','" + config.mokapipe_pipeline_ID + "')")

        #  combine all the queries into a string suitable for an email
        sql_statements = ""

        # if there are no sql commands in the list it must be an oncology run
        if len(sql) == 0:
            # email the workflow used so this can be entered manually
            self.email_subject = "MOKAPIPE ALERT : Started pipeline for " + self.runfolder
            self.email_message = self.runfolder + " being processed using workflow " + ",".join(set(workflows)) + "\n\n" + config.mokaamp_email_message
            # send email
            self.send_an_email([config.oncology_you, config.you])
        # otherwise loop through each statement and create a string.
        else:
            for statement in sql:
                sql_statements = sql_statements + statement + "\n"

            # write action to system log file
            self.logger("SQL statement email sent for run " + self.runfolder, "UA_pass")

            # email this query
            self.email_subject = "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for " + self.runfolder
            self.email_priority = 1  # high priority
            self.email_message = self.runfolder + " being processed using workflow " + ",".join(set(workflows)) + "\n\nPlease update Moka using the below query and ensure that " + \
                str(records) + " records are updated:\n\n" + sql_statements
            # send email
            self.send_an_email(config.you)

        if not config.debug:
            # call function to update smartsheet to say run in progress
            self.smartsheet_mokapipe_in_progress()

    def RPKM(self):
        '''This function loops through all the panel numbers found in the fastq folders and where relevant submits a RPKM job '''
        # create a copy of the list of unique panels in this run - this will be used to report which panels have been processed in the log file.
        CNV_panels_reported = set(self.panels_in_run)
        # self.panel_in_run contains all panels found in the run, except for Pan493 and oncology panels - loop through this copy of the list not CNV_panels_reported as this list will have items removed
        for panel in set(self.panels_in_run):
            # ignore focussed exome  as this will never have RPKM (other panels which won't have RPKM have been filtered out previously)
            if panel != "Pan1620":
                # ensure there is a CNV bedfile in the dictionary but if not don't raise an exception, trigger a alert via system log.
                if not config.panelnumbers[panel]:
                    self.logger("Unknown CNV bedfile for " + panel, "UA_fail")
                    # remove this panel from the list of RPKM panels issued below
                    CNV_panels_reported.remove(panel)
                else:
                    # build RPKM command
                    RPKM_command = self.RPKM_command + config.RPKM_bedfile + config.app_project + config.bedfile_folder + config.panelnumbers[panel] + "_RPKM.bed" + config.RPKM_project + \
                        self.nexusproject + config.RPKM_bedfile_to_download + panel + self.project + self.projectid.rstrip() + self.depends + self.token.rstrip(")")
                    # write commands to bash script
                    self.DNA_Nexus_bash_script.write(RPKM_command + "\n")

        # write to cron job script using panels in CNV_panels_reported
        self.upload_agent_script_logfile.write("RPKM commands build for " + str(len(CNV_panels_reported)) + " panels (" + " ".join(CNV_panels_reported) + ") - see " + self.bash_script + "\n\n")

    def upload_rest_of_runfolder(self):
        # write status update to log file
        self.upload_agent_script_logfile.write("\n----------------------UPLOAD REST OF RUNFOLDER----------------------\n")

        # open file for upload agent standard out (in append mode)
        runfolder_upload_stdout_file = open(os.path.join(self.runfolderpath, config.upload_started_file), 'a')

        # distinguish between upload of fastq and rest of runfolder
        runfolder_upload_stdout_file.write("\n----------------------Uploading rest of runfolder " + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")

        # close log file
        runfolder_upload_stdout_file.close()

        # create temp bash_script
        temp_bash = os.path.join(self.runfolderpath, "/temp_" + config.runfolder_upload_cmds.replace('.txt', '.sh'))
        # open temp file containing upload agent commands
        temp_runfolder_upload_cmd_file = open(temp_bash, 'w')

        # create the samplesheet name to copy
        samplesheet_name = self.runfolder + "_SampleSheet.csv"

        # copy samplesheet into project
        copyfile(config.samplesheets + samplesheet_name, os.path.join(self.runfolderpath, samplesheet_name))

        # write to the log file that samplesheet was copied and runfolder is being uploaded, linking to log files for cmds and stdout
        self.upload_agent_script_logfile.write("Copied samplesheet to runfolder\nUploading rest of run folder to Nexus using commands in " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds) +
            "\nsee standard out from these commands in log file @ " + os.path.join(self.runfolderpath, config.upload_started_file) + "\n\n----------------CHECKING SUCCESSFUL UPLOAD OF RUNFOLDER----------------\n")

        # loop through the run folder
        for root, subFolder, files in os.walk(self.runfolderpath):
            # for every file
            for item in files:
                # capture the path
                path = str(os.path.join(root, item))

                # skip image files
                if "/L00" in path:
                    pass
                # skip fastq files already uploaded
                elif path.endswith(".fastq.gz"):
                    pass
                # skip log files still being written to
                elif path.endswith(config.upload_started_file) or path.endswith(temp_bash) or path.endswith(config.runfolder_upload_cmds):
                    pass
                # skip samplesheet
                elif path.endswith("SampleSheet.csv"):
                    pass
                # otherwise upload
                else:
                    # Use path to build desitnation folder within nexus. put in quotations to avoid weird characters and spaces
                    path_to_upload = "'" + path + "'"
                    # remove the project prefix (002_), the path to the runfolders ("/media/data1/share") and the file name
                    path_for_nexus = path.replace(self.runfolder, self.nexusproject.replace(config.NexusProjectPrefix, "")).replace(config.runfolders, "").replace(item, "")

                    # build the nexus upload command
                    nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
                        + "  --folder " + path_for_nexus + " --do-not-compress --upload-threads 10 " + path_to_upload + self.restart_ua_2 % (path_to_upload)

                    # copy the command to the temporary cmd file
                    temp_runfolder_upload_cmd_file.write(nexus_upload_command + "\n")
        temp_runfolder_upload_cmd_file.close()

        if not config.debug:
            # create command redirecting stderror to the log file
            run_upload_agent_script = "bash " + temp_bash + " >> " + os.path.join(self.runfolderpath, config.upload_started_file) + " 2>&1"
            # run the command
            proc = subprocess.Popen([run_upload_agent_script], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # capture the streams
            (out, err) = proc.communicate()

            # All standard error is redirected to stdout in the command need -  to parse STDout for errors
            # set a flag so a "no errors reported" message is only written if no errors are seen!
            error = False
            # for each line in the standard out
            for linenumber, line in enumerate(out):
                # skip if the line is empty, or it starts with Uploading or ends with the expected success statement
                if line.startswith("Uploading") or line.endswith("was uploaded successfully. Closing...") or len(line) < 2:
                    pass
                # if the line doesn't contain any of these expected lines
                else:
                    # set the flag so the no errors reported message is not written
                    error = True
                    # expect a pair of lines for each file to be uploaded, the first one detailing which file is being uploaded and the second a pass/fail statement.
                    # we are looking for the error in the second line so we want this and the line before it
                    # however if the error message is the first line can't record the line before it so use a if loop
                    if linenumber == 0:
                        # write only this line to log
                        self.upload_agent_script_logfile.write("Error when executing script:\n" + line + "\n")
                    else:
                        # write this line and the line before (as this contains the name of the file trying to upload) to log
                        self.upload_agent_script_logfile.write("Error when executing script:\nError lines = " + out[linenumber - 1] + "\n" + line + "\n")
                    # write to logger that there was an issue
                    self.logger("Error whilst uploading rest of runfolder - see all standard out " + os.path.join(self.runfolderpath, config.upload_started_file), "UA_fail")
            # if there were no errors write this to log file
            if not error:
                # write to log
                self.upload_agent_script_logfile.write("No errors reported\n")

        # copy commands from temporary upload agent file to the one containing the fastq upload command
        command = "cat " + temp_bash + " >> " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds)

        proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # capture the streams
        (out, err) = proc.communicate()

        if err:
            self.upload_agent_script_logfile.write("Error when copying temp upload commands to the archived script. See temp file @ " + os.path.join(self.runfolderpath, "temp_" + config.runfolder_upload_cmds) + "\n")
        else:
            self.upload_agent_script_logfile.write("upload agent commands copied to the file in " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds) + "\n")

            # if copy went ok, delete temp file
            delete_temp_file_cmd = "rm " + temp_bash
            proc = subprocess.Popen([delete_temp_file_cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # capture the streams
            (out, err) = proc.communicate()
            if err:
                self.upload_agent_script_logfile.write("Error deleting the temp file\n")

        # call function which looks for errors when uploading
        self.look_for_upload_errors_runfolder()

        # close the log file
        self.upload_agent_script_logfile.close()

        # rename file to show what runs were affected.
        self.rename = self.runfolder + "_upload_agent_log.txt"
        os.rename(self.upload_agent_logfile_name, self.upload_agent_logfile_name.replace('.txt', self.rename))

        # capture the new file name so can continue to write to it.
        self.upload_agent_logfile_name = self.upload_agent_logfile_name.replace('.txt', self.rename)

        # reset self.rename to prevent logfile being renamed incorrectly.
        self.rename = ""

        # call function to upload log files
        self.upload_log_files()

    def upload_log_files(self):
        ''' log files include:
        1. the log file for this script containing all commands used (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_log)
        2. demultiplexing log file (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_log_files)
        3. nexus project creation logs (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Nexus_project_creation_logs)
        4. runfolder_upload_commands (in the run folder)
        5. runfolder_upload_stdout (in the run folder)
        6. logfile used to set off the workflow (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs)
        7. samplesheet
        '''
        # empty list to hold files (and paths) to be uploaded
        logfile_list = []

        # ######## path for upload agent log file (file1) #########
        # get full filepath for the log file containing the decisions made by this script
        upload_agent_log_file_to_upload = self.upload_agent_logfile_name
        # add to list
        logfile_list.append(upload_agent_log_file_to_upload)

        # ######## demultiplexing log file (file2) #########
        # empty variable to build a list of files
        demultiplex_log = ""
        # loop through files in demultiplex log folder (contains decisions made when demultiplexing script is run - have been renamed to contain run folder if a run was demultiplexed)
        for logfile in os.listdir(config.demultiplex_logfiles):
            # if runfolder in filename
            if self.runfolder in logfile:
                # add file path and file name to list
                demultiplex_log = config.demultiplex_logfiles + logfile
                logfile_list.append(demultiplex_log)

        # ######## nexus project_creation_logfile (file 3) #########
        # get the full file path for file containing comands used to create and share nexus project
        nexus_project_creation_logfile = config.DNA_Nexus_project_creation_logfolder + self.runfolder + ".sh"
        # add to list
        logfile_list.append(nexus_project_creation_logfile)

        # ######## runfolder upload commands (file 4) #########
        # get the full file path for the cmds used to upload fastq, runfolder and log files
        runfolder_upload_logfile_to_upload = os.path.join(self.runfolderpath, config.runfolder_upload_cmds)
        # add to list
        logfile_list.append(runfolder_upload_logfile_to_upload)

        # ######## runfolder upload stdout (file 5) #########
        # get the full file path for the file containing stdout/ stderr from upload agent
        runfolder_upload_logfile_to_upload = os.path.join(self.runfolderpath, config.upload_started_file)
        # add to list
        logfile_list.append(runfolder_upload_logfile_to_upload)

        # ######## bash script which sets off workflow (file 6) #########
        # add the file which sets off the dx run commands
        logfile_list.append(self.bash_script)

        # ######### samplesheet (file7) #########
        # create a upload agent command for samplesheet (copied into the runfolder above) which is being uploaded into the runfolder
        samplesheet_nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
            + "  --folder /" + self.nexusproject.replace(config.NexusProjectPrefix, "") + "/" + " --do-not-compress --upload-threads 10 " + self.runfolderpath + "/" + self.runfolder + "_SampleSheet.csv " + self.restart_ua_2

        # create command line for files in the logfile_list (to be put into a logfiles subfolder)
        nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
            + "  --folder /" + self.nexusproject.replace(config.NexusProjectPrefix, "") + "/Logfiles/" + " --do-not-compress --upload-threads 10 " + " ".join(logfile_list) + self.restart_ua_2

        # write these commands to the runfolder_upload_cmds_logfile before upload.
        runfolder_upload_cmd_file = open(os.path.join(self.runfolderpath, config.runfolder_upload_cmds), 'a')
        runfolder_upload_cmd_file.write("\n----------------------Upload log files----------------------\n")
        runfolder_upload_cmd_file.write(samplesheet_nexus_upload_command + "\n" + nexus_upload_command)
        runfolder_upload_cmd_file.close()

        if not config.debug:
            # run the command, redirecting stderror to stdout
            proc = subprocess.Popen([nexus_upload_command + " & " + samplesheet_nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)

            # capture the streams (err is redirected to out above)
            (out, err) = proc.communicate()

        else:
            print nexus_upload_command
            out = "x"
            err = "y"

        # capture stdout to log file containing stdour and stderr
        runfolder_upload_stdout_file = open(os.path.join(self.runfolderpath, config.upload_started_file), 'a')
        runfolder_upload_stdout_file.write("\n----------------------Uploading logfiles (this will not be included in the file within DNA Nexus) " +
            str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")
        runfolder_upload_stdout_file.write(out)
        runfolder_upload_stdout_file.close()

        # check standard out from upload of log files
        # open logfile first to write info from check
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name, 'a')
        self.upload_agent_script_logfile.write("\n----------------CHECKING SUCCESSFUL UPLOAD OF LOGFILES (this will not be in DNA Nexus)----------------\n")

        # call function to check stdout
        self.look_for_upload_errors_logfiles()

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

        # capture the NGS run number and count
        count = 0
        for obj in os.listdir(self.runfolderpath + "/Data/Intensities/BaseCalls/"):
            if obj.endswith("fastq.gz"):
                if obj.startswith("Undetermined"):
                    pass
                else:
                    count = count + 0.5

        # set all values to be inserted
        payload = '{"cells": [{"columnId": ' + str(config.ss_title) + ', "value": "' + self.runfolder + '"}, {"columnId": ' + str(config.ss_description) + \
            ', "value": "MokaPipe"},{"columnId": ' + str(config.ss_samples) + ', "value": ' + str(count) + '},{"columnId": ' + str(config.ss_status) + \
            ', "value": "In Progress"},{"columnId": ' + str(config.ss_priority) + ', "value": "Medium"},{"columnId": ' + str(config.ss_assigned) + \
            ', "value": "aledjones@nhs.net"},{"columnId": ' + str(config.ss_received) + ', "value": "' + str(self.smartsheet_now) + '"}], "toBottom":true}'

        # create url for uploading a new row
        url = self.url + "/rows"

        # add the row using POST
        r = requests.post(url, headers=self.headers, data=payload)

        # capture the row id
        response = r.json()

        for i in response["result"]:
            if i == "id":
                self.rowid = response["result"][i]

        self.upload_agent_script_logfile.write("\n----------------------UPDATE SMARTSHEET----------------------\n")
        # check the result of the update attempt
        for i in response:
            if i == "message":
                if response[i] == "SUCCESS":

                    self.upload_agent_script_logfile.write("smartsheet updated to say in progress\n")
                    self.logger("run started added to smartsheet", "smartsheet_pass")
                else:
                    self.logger("run started NOT added to smartsheet for run " + self.runfolder, "smartsheet_fail")
                    self.upload_agent_script_logfile.write("smartsheet NOT updated at in progress step\n" + str(response))

    def look_for_upload_errors_fastq(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file'''
        # Open the log file and read to look for the string "ERROR"
        for upload in open(os.path.join(self.runfolderpath, config.upload_started_file)).read().split("Uploading file"):
            # if there was an error during the upload...
            if self.ua_error in upload:
                # if it still completed successfully carry on
                if "uploaded successfully" in upload:
                    self.upload_agent_script_logfile.write("There was a disruption to the network when uploading the Fastq files but it completed successfully\n")
                    self.logger("upload of fastq was disrupted but completed for run " + self.runfolder, "UA_disrupted")
                # other wise write to log
                else:
                    self.upload_agent_script_logfile.write("There was a disruption to the network which prevented the rest of the runfolder being uploaded\n")
                    self.logger("upload of fastqs failed for run " + self.runfolder, "UA_fail")
            else:
                # write to log file check was ok
                self.logger("upload of fastq files complete for run " + self.runfolder, "UA_pass")

    def look_for_upload_errors_runfolder(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file
        NB any errors from the fastq upload would also be detected here.'''

        # flag so no errors found statement only written once
        upload_error = False

        for upload in open(os.path.join(self.runfolderpath, config.upload_started_file)).read().split("Uploading file"):
            # if there was an error during the upload...
            if self.ua_error in upload:
                # if error seen set flag
                upload_error = True
                # if it still completed successfully carry on
                if "uploaded successfully" in upload:
                    self.upload_agent_script_logfile.write("There was a disruption to the network when uploading the rest of the runfolder but it completed successfully\n")
                    self.logger("upload of runfolder was disrupted but completed for run " + self.runfolder, "UA_disrupted")
                # other wise send an email and write to log
                else:
                    self.upload_agent_script_logfile.write("There was a disruption to the network which prevented the rest of the runfolder being uploaded\n")
                    self.logger("upload of runfolder failed for run " + self.runfolder, "UA_fail")

        # only state no errors seen if no errors were seen!
        if not upload_error:
            # write to log file check was ok
            self.upload_agent_script_logfile.write("There were no issues when backing up the run folder\n")
            self.logger("backup of runfolder complete for run " + self.runfolder, "UA_pass")

    def look_for_upload_errors_logfiles(self):
        '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
        If present email link to the log file
        NB any errors from the fastq upload and run folderwould also be detected here.'''

        # flag so no errors found statement only written once
        upload_error = False

        # Open the log file and split for each individual upload command
        for upload in open(os.path.join(self.runfolderpath, config.upload_started_file)).read().split("Uploading file"):
            # if there was an error during the upload...
            if self.ua_error in upload:
                # if error seen set flag
                upload_error = True
                # if it still completed successfully carry on
                if "uploaded successfully" in upload:
                    self.upload_agent_script_logfile.write("There was a disruption to the network when uploading logfiles but it completed successfully\n")
                    self.logger("upload of logfiles was disrupted but completed for run " + self.runfolder, "UA_disrupted")
                # other wise send an email and write to log
                else:
                    self.upload_agent_script_logfile.write("There was a disruption to the netowkr which prevented log files being uploaded\n")
                    self.logger("upload of log files failed for run " + self.runfolder, "UA_fail")
        # only state no errors seen if no errors were seen!
        if not upload_error:
            # write to log file check was ok
            self.upload_agent_script_logfile.write("There were no issues when uploading the logfiles\n")
            self.logger("upload of log files complete without issue " + self.runfolder, "UA_pass")

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

        if subprocess.call([log], shell=True) == 0:
            # If the log command produced no errors, record the log command string to the script logfile.
            self.upload_agent_script_logfile.write("Log written to /usr/bin/logger\n" + log + "\n")
        # Else record failure to write to system log to the script log file
        else:
            self.upload_agent_script_logfile.write("Failed to write log to /usr/bin/logger\n" + log + "\n")


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
