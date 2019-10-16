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
        self.now = str('{:%Y%m%d_%H}'.format(datetime.datetime.now()))

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
                process_runfolder().quarterback(folder, self.now)

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


class process_runfolder():
    ''' 
    This class assesses a runfolder to check if it required processing. 
    A  number of tests are performed, assessing readiness to process and to identify if the runfolder meets the criteria to be processed.
    Fastqs are uploaded to DNA Nexus, dx run commands built and executed and then the rest of the runfolder is also uploaded.
    All actions are logged in the logfile created when the script is run.
    A new instance of this class is initiated for each runfolder being assessed. 
    '''

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
        self.list_of_processed_samples = []

        self.list_of_DNA_numbers_WES = []
        self.list_of_DNA_numbers_Onc = []
        self.list_of_DNA_numbers_nonWES = []

        # strings for NGSrun and wes numbers
        self.library_batch = ''  # first element of fastq file name.
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
        self.wes_command = "jobid=$(dx run " + config.app_project + config.mokawes_path + " -y"
        self.peddy_command = "jobid=$(dx run " + config.app_project + config.peddy_path
        self.multiqc_command = "jobid=$(dx run " + config.app_project + config.multiqc_path
        self.upload_multiqc_command = "dx run " + config.app_project + config.upload_multiqc_path + " -y"
        self.smartsheet_update_command = "dx run " + config.app_project + config.smartsheet_path
        self.RPKM_command = "dx run " + config.app_project + config.RPKM_path
        self.mokaonc_command = "jobid=$(dx run " + config.app_project + config.mokaonc_path + " -y"
        self.mokaamp_command = "jobid=$(dx run " + config.app_project + config.mokaamp_path + " -y"
        self.decision_support_preperation = "analysisid=$(python %s -a " % (os.path.join(os.path.dirname(os.path.realpath(__file__)),config.decision_support_tool_input_script))
        self.sapientia_upload_command = "jobid=$(dx run " + config.app_project + config.sentieon_app_path + " -y"
        self.iva_upload_command = "jobid=$(dx run " + config.app_project + config.iva_app_path + " -y"
        # project to upload run folder into
        self.nexusproject = config.NexusProjectPrefix

        # project_ID of created project
        self.projectid = ""

        # arguments for command
        self.dest = " --dest="
        self.dest_cmd = ""
        self.project = " --project="
        self.token = " --brief --auth-token " + config.Nexus_API_Key + ")"
        self.depends = " -y $depends_list"

        # argument to capture jobids
        self.depends_list = "depends_list=\"${depends_list} -d ${jobid} \"" + "\n"
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
        # newly inserted row
        self.rowid = ""

        # time stamp
        self.smartsheet_now = ""

        # requests info
        self.headers = {"Authorization": "Bearer " + config.smartsheet_api_key, "Content-Type": "application/json"}
        self.smartsheet_url = 'https://api.smartsheet.com/2.0/sheets/' + str(config.smartsheet_sheetid)

        self.panel_dictionary = {}

        self.sql_queries={}
    
    def test(self):
        return "Hello world"

    def quarterback (self, runfolder, now):
        """
        This module calls all other modules in order
        """
        # set up runfolder variables
        self.setup_variables(runfolder, now)
        # build dictionary of panel settings
        self.set_panel_dictionary()
        # perform upload agent test
        self.test_upload_agent()
        # test dx toolkit installation
        self.test_dx_toolkit()
        
        # check if already uploaded and demultiplkexing finished sucessfully
        if not self.already_uploaded() and self.demultiplex_completed_successfully():

            if self.find_fastqs():
                # build the file path with WES batch and NGS run numbers
                self.capture_any_WES_batch_numbers()
                self.capture_library_batch_numbers()
                self.build_nexus_project_name()
                # create nexus project
                self.create_project()
                # send list to module to trigger upload
                self.upload_fastqs()
                # check fastqs uploaded successfully
                self.look_for_upload_errors_fastq()

                self.write_dx_run_cmds(self.start_building_dx_run_cmds())
                self.run_dx_run_commands()
                self.smartsheet_workflows_commands_sent()
                self.write_opms_queries_mokawes()
                self.write_opms_queries_oncology()
                self.write_opms_queries_mokapipe()
                self.send_opms_queries()
                self.look_for_upload_errors(self.upload_rest_of_runfolder())
                self.look_for_upload_errors(self.upload_log_files())

    def setup_variables(self, runfolder, now):
        """
        Set up all run specific variables - A new instance of class containing this function is created for each runfolder so variables are runfolde specific.
        """
        # capture timestamp
        self.now = now
        
        # take current timestamp for recieved
        self.smartsheet_now = str('{:%Y-%m-%d}'.format(self.now))

        # open the logfile for this run's cron job.
        self.upload_agent_logfile_name = config.upload_agent_logfile + self.now + "_" + self.rename + ".txt"
        self.upload_agent_script_logfile = open(self.upload_agent_logfile_name, 'a')

        # capture the runfolder
        self.runfolder = str(runfolder)
        # create full path to runfolder
        self.runfolderpath = os.path.join(config.runfolders, self.runfolder)
        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath + config.fastq_folder
        # bash script for dx run commands
        self.bash_script = config.DNA_Nexus_workflow_logfolder + self.runfolder + ".sh"

    def set_panel_dictionary(self):
        """ 
        Populate the dictionary detailing panel specific settings.
        Default settings are set in the config file and then updated as and when required for each panel the defaults in config file.
        Loop through panel specific properties in config file and overwrite any default with panel specific settings
        """
        # for each panel 
        for panel in config.panel_list:           
            # 
            self.panel_dictionary[panel] = config.default_panel_properties
            for setting in config.panel_settings[panel]:
                self.panel_dictionary[panel][setting] = config.panel_settings[panel][setting]
    
    def test_upload_agent(self):
        """
        Tests the upload agent is installed by calling upload agent command with --version.
        Assesses if expected string is present in response. Raises exception if test fails.
        """

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
        """
        Tests if the dx toolkit is installed. 
        Calls dx run command and assesses if the expected string (set in config file) is present in output.
        Raises exception if test fails.
        """

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

    def already_uploaded(self):
        """
        The upload agent stdout is written to a file which also denotes that the runfolder has been processed.
        This function checks for presense of this file.
        Returns False if not already processed.
        """
        # write to log file including the github repo tag and time stamp
        self.upload_agent_script_logfile.write("automate_demultiplexing release:" + git_tag.git_tag() + \
            "\n----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + \
            "----------------------\nAssessing " + self.runfolderpath + \
            "\n\n----------------------HAS THIS FOLDER ALREADY BEEN UPLOADED?----------------------\n")

        # look for the file denoting the upload has started
        if os.path.isfile(os.path.join(self.runfolderpath, config.upload_started_file)):
            if not config.debug:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present \n----------------------STOP----------------------\n")
                return True
            else:
                self.upload_agent_script_logfile.write("YES - self.upload_started_file present but DEBUG MODE IS TRUE SO CONTINUING.......\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
                return False
        else:
            # if not check demultiplex has finished succesfully and write to file
            self.upload_agent_script_logfile.write("NO - self.upload_started_file not present so continue\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
            return False
            
    def demultiplex_completed_successfully(self):
        """
        Check if the demultiplexing finished successfully by reading the last line of the demultiplex log
        The demultiplexing script will raise any alerts if issues are found with demultiplexing.
        Uses expected success status defined in config.
        Returns True is completed sucessfully
        """
        # check demultiplexing has actually been done
        if os.path.isfile(os.path.join(config.runfolders, self.runfolder, self.demultiplexed)):
            with open(os.path.join(config.runfolders, self.runfolder, self.demultiplexed), 'r') as logfile:
                # check if the success statement is in the last line
                if config.logfile_success in logfile.readlines()[-1]:
                    self.upload_agent_script_logfile.write("Demultiplex was successfully completed.\ncompiling a list of fastqs....... ")
                    # if successfull call the module which creates a list of fastqs
                    return True
                else:
                    # write to logfile that demultplex was not successful
                    self.upload_agent_script_logfile.write("!!!!!!!DEMULTIPLEXING DID NOT COMPLETE SUCCESSFULLY.!!!!!!!!!\n----------------------STOP----------------------\n")
                    return False
        else:
            # write to logfile that not yet demultiplexed
            self.upload_agent_script_logfile.write("demultiplexing has not been performed.\n----------------------STOP----------------------\n")
            return False
    
    def find_fastqs(self):
        """
        Loops through all the fastq files in the expected location within the runfolder
        Identifies the pan number and checks for presense in the dictionary of panel settings.
        If there are any files where the pan number was not found sent an alert.
        If samples which do require processing are found variables are updated with a list of samples to be processed and a string of fastq names and the function returns True.
        """

        # set up list of fastqs not to be processed
        not_processed = []

        # find all fastqs
        for fastq in os.listdir(self.fastq_folder_path):
            if fastq.endswith('fastq.gz') and not fastq.startswith('Undetermined'):
                pannumber = ""
                pannumber = "Pan" + fastq.split("_Pan")[1].split("_")[0]
                if pannumber in config.panelnumbers:
                    # we know what to do with it:
                    # append to string of paths for upload agent
                    self.fastq_string = self.fastq_string + " " + self.fastq_folder_path + "/" + fastq
                    # add the fastq name to a list to be used in create_nexus_file_path
                    self.list_of_processed_samples.append(fastq)
                elif pannumber == "":
                    # haven't identified pan number
                    # TO DO warn or something?
                    pass
                else:
                    not_processed.append(fastq)
        
        if len(not_processed) > 0:
            # add to logger
            self.logger("unrecognised panel number found in run " + self.runfolder, "UA_fail")
            # write to logfile
            self.upload_agent_script_logfile.write("Some fastq files contained an unrecognised panel number: " + ",".join(not_processed) + "\n")
        
        if len(self.list_of_processed_samples) == 0:
            self.upload_agent_script_logfile.write("List of fastqs did not contain any known Pan numbers. Stopping\n")
            return False
        else:
            self.upload_agent_script_logfile.write(str(len(self.list_of_processed_samples)) + " fastqs found.\n\n----------------------PREPARING UPLOAD OF FASTQS----------------------\ndefining path for fastq files.......")
            return True

    def capture_any_WES_batch_numbers(self):
        """
        DNANexus project names are the runfolder suffixed with identifiers to help future dearchival easier.
        This function parses samplenames and identifies any WES batch numbers from the samplenames (identified as anything between "_WES" and "_Pan".
        This is captures as a string within updates a class wide variable
        """
        # a list to hold all the wes numbers
        wes_numbers = []
        
        # for each fastq in the list of fastqs
        for fastq in self.list_of_processed_samples:
            # if the run has any WES samples
            if "WES" in fastq:
                # split on _WES to split the fastq name into two, take the second half of it and split on "_Pan"
                # this will capture 5 or _5 depending if was WES5 or WES_5
                # remove any underscores and suffix to WES to make WES5
                wesbatch = "WES" + fastq.split("_WES")[1].split("_Pan").replace('_', '')
                wes_numbers.append(wesbatch)

        self.wes_number = "_".join(set(wesnumbers))
        
    def capture_library_batch_numbers(self):
        """
        DNANexus project names are the runfolder suffixed with identifiers to help future dearchival easier.
        This function parses samplenames and identifies the library prep numbers, identified as the first element in the sample name (before the first underscore)
        This updates a class wide variable
        """
        # a list to hold all the librray batch numbers
        library_batch_numbers = []

        # for each fastq in the list of fastqs
        for fastq in self.list_of_processed_samples:
            # split on underscores to capture the first element which is the library_batch number eg ONC100 or NGS100
            library_batch_numbers.append(fastq.split("_")[0])

        self.library_batch = "_".join(set(library_batch_numbers))
        
    def build_nexus_project_name(self):
        """
        The DNA Nexus project name contains all the information required to quickly and easily identify the contents, which may help in the future.
        The project name starts with a code to denote the status of the project (eg live clinical, development or archived) and is followed by the name of the runfolder.
        The WES batches and library prep strings are suffixed onto the project name.
        Project names (and relevant file paths within the projext are saved to variables)
        """
        # if wes batch numbers add this into the nexus path
        if self.wes_number != '':
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.library_batch + "_" + self.wes_number + config.fastq_folder
            # build project name
            self.nexusproject = self.nexusproject + self.runfolder + "_" + self.library_batch + "_" + self.wes_number
        else:
            # self.nexus path
            self.nexus_path = self.runfolder + "_" + self.library_batch + config.fastq_folder
            # build project name
            self.nexusproject = self.nexusproject + self.runfolder + "_" + self.library_batch

        self.dest_cmd = self.nexusproject + ":/"
        # write to log
        self.upload_agent_script_logfile.write("fastqs will be uploaded to " + self.nexus_path + "\n\n----------------------CREATE AND SHARED DNA NEXUS PROJECT----------------------\n")
    
    def create_project(self):
        """
        Once the project name has been defined the project can be created.
        This uses the DNANexus sdk, where commands are written to a bash script and executed using subprocess.
        The project is created and shared with users, with varying degrees of access as defined in the config file.
        Successful creation of the project is assertained by assessing the capture of a project id which fits the expected project name pattern (project-132456)
        Any issues identifying the project id will result in an alert being sent.
        """
        project_bash_script = config.DNA_Nexus_project_creation_logfolder + self.runfolder + ".sh"

        # open bash script
        DNA_Nexus_bash_script = open(project_bash_script, 'w')
        DNA_Nexus_bash_script.write(self.source_command)
        DNA_Nexus_bash_script.write(self.createprojectcommand % (config.prod_organisation, self.nexusproject))

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

            # split std_out on "project" and get the last item to capture the project ID
            self.projectid = "project" + out.split("project")[-1].rstrip()

            # if haven't captured a project id report an error to system log
            if self.projectid == "":
                self.logger("failed to create project in dna nexus " + self.nexusproject, "UA_fail")

                # raise exception to stop script
                raise Exception, "Unable to create DNA Nexus project"
            else:
                # record in log file who project was shared with (VIEW)
                self.upload_agent_script_logfile.write("DNA Nexus project %s created and shared (VIEW) to " % (self.nexusproject) + ",".join(config.view_users) +
                    "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (self.projectid))
                
                # record in log file who project was shared with (ADMIN)
                self.upload_agent_script_logfile.write("DNA Nexus project %s created and shared (ADMIN) to " % (self.nexusproject) + ",".join(config.admin_users) +
                    "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (self.projectid))

        else:
            # for debug mode use example project id
            self.projectid = "project-F2gzY2j0xyXJ4x3z5Pq8BjQ4"

    def upload_fastqs(self):
        """
        All samples to be processed were identified in find_fastqs(). This function populated a string of local filepaths for each fastq that can be used by the upload agent.
        This command is executed using subprocess and all standard error/standard out written to a log file
        The upload command is written in a way where it is repeated until it exits with an exit status of 0.
        """
        # build the nexus upload command
        nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
            + "  --folder /" + self.nexus_path + " --do-not-compress --upload-threads 10" + self.fastq_string + self.restart_ua_2 % ("fastq files")

        # open a file to hold all the upload agent commands
        with open(os.path.join(self.runfolderpath, config.runfolder_upload_cmds), 'w') as runfolder_upload_cmd_file:
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
    
    def look_for_upload_errors_fastq(self):
        """
        Parse the file containing standard error/standard out from the upload agent.
        The upload agent command is reissued until it exists with a status of 0 which must be taken into account when identifying errors.
        If the expected error message (defined in config file) is present but the string "upload successfully" is still present it is assumed it uploaded successfully on the repeated attempt.
        If the success statement is absent raise an alert 
        """
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

    def nexus_fastq_paths(self, read1):
        """
        Receive name of read 1 fastq file
        Returns a tuple with the DNA Nexus fastq file paths for both reads to be used to build the dx run comand
        """
        # build full file nexus path including project
        read1_nexus_path = self.nexusproject + ":" + os.path.join(self.nexus_path, read1)
        # create read2 by replacing R1 with R2
        read2_nexus_path = self.nexusproject + ":" + os.path.join(self.nexus_path, read1.replace("_R1_", "_R2_"))
        return ((read1_nexus_path,read2_nexus_path))

    def nexus_bedfiles(self, pannumber):
        """
        Build dictionary of all bedfile inputs for given pan number.
        This will create a path to a BED file for every app that takes a BED file, even if the file does not exist, however this dictionary entry will not be used in the dx run command
        Will use the pan number unless a different bedfile is specified in the panel dictionary
        Returns a dictionary
        """
        #create dict
        bed_dict = {}

        # for sambamba/hs metrics bed file if a different bed file is specified in config file use that, otherwise use the pannumber
        if self.panel_dictionary[pannumber]["sambamba_bedfile"]:
            bed_dict["sambamba"] = config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["sambamba_bedfile"]
        else:
            bed_dict["sambamba"] = config.app_project + config.bedfile_folder + pannumber + "Sambamba.bed"
            
        if self.panel_dictionary[pannumber]["hsmetrics_bedfile"]:
            bed_dict["hsmetrics"] = config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["hsmetrics_bedfile"]
        else:
            bed_dict["hsmetrics"] = config.app_project + config.bedfile_folder + pannumber + "Data.bed"
        
        bed_dict["mokaamp_bed_PE_input"] = config.app_project + config.bedfile_folder + pannumber + "_PE.bed"
        bed_dict["mokaamp_variant_calling_bed"] = config.app_project + config.bedfile_folder + pannumber + "_flat.bed"

        bed_dict["rpkm_bedfile"] = [config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]]
        
        return bed_dict

    def start_building_dx_run_cmds(self):
        """
        loop through the list of fastqs to generate commands used to initiate the pipeline.
        For each sample use the panel dictionary to determine which functions are called.
        Each function builds a dx run command which is added to a list.
        The list of commands is returned
        """

        # Update script log file to say what is being done.
        self.upload_agent_script_logfile.write("\n\n----------------------RUN WORKFLOW----------------------\n")
        # list to hold all commands.
        commands_list = []
        commands_list.append(self.source_command)
        # lists/flags for run wide commands
        mokaamp_list = []
        mokaonc_list = []
        # flags to determine if run wide jobs are needed
        sapientia = False
        iva = False
        peddy = False
        joint_variant_calling = False
        # list for panels needing RPKM analysis
        rpkm_list = []
        
        # loop through samples
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number and use this to determine which dx run commands are needed for the sample
                panel = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])

                # The order in which the modules are called here is important to ensure the order of dx run commands is correct. This can affect which decision support tool data is sent to.
                if self.panel_dictionary[panel]["mokawes"]:
                    commands_list.append(self.create_mokawes_command(fastq, pannumber))
                    commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command())
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.run_sapientia_command())
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["peddy"]:
                        peddy = True
                    if self.panel_dictionary[panel]["joint_variant_calling"]:
                        joint_variant_calling = True


                if self.panel_dictionary[panel]["mokapipe"]:
                    commands_list.append(self.create_mokapipe_command(fastq, pannumber))
                    commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command())
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.run_sapientia_command())
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["RPKM_pan"]:
                        rpkm_list.append(pannumber)


                if self.panel_dictionary[panel]["mokaonc"]:
                    mokaonc_list.append(fastq)
                    
                if self.panel_dictionary[panel]["mokaamp"]:
                    commands_list.append(self.create_mokaamp_command(fastq, pannumber))
                    commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.add_to_depends_list())
        
        # run wide jobs
#        if len(mokaamp_list) !=0:
#            commands_list.append(self.create_mokaamp_command(mokaamp_list))
        if len(mokaonc_list) != 0:
            commands_list.append(self.create_mokaonc_command(mokaonc_list))
        if joint_variant_calling:
            commands_list.append(self.create_joint_variant_calling_command())
            
        if len(rpkm_list) != 0:
            # Create a set of RPKM numbers for one command per panel
            for rpkm in set(rpkm_list):
                commands_list.append(self.create_rpkm_command(rpkm))
        if peddy:
            commands_list.append(run_peddy_command())        
        
            
        # multiqc 
        commands_list.append(create_multiqc_command())
        # smartsheet 
        commands_list.append(create_smartsheet_command())


        return commands_list

    def create_mokawes_command(self, fastq, pannumber):
        """
        Takes fastq file and pan number for single sample and builds the mokawes dx run command
        Returns dx run command (string)
        """        
        # call function to build nexus fastq paths - returns tuple for read1 and read2
        fastqs = self.nexus_fastq_paths(fastq)

        bedfiles = self.nexus_bedfiles(pannumber)

        # if a sample name is not provided sention cleans the fastq file name to create one. However this includes removing all "_1", which is not ideal - theerfore specify one, using everything before "_R1" from read1 fastq filename
        sention_sample_name = fastq.split("_R1_")[0]

        # create the MokaWES dx command
        command = self.wes_command + config.wes_fastqc1 + fastqs[0] + config.wes_fastqc2 + fastqs[1] + \
            config.wes_sention_samplename + sention_sample_name + \
            config.wes_picard_bedfile + bedfiles["hsmetrics"] + \
            self.dest + self.dest_cmd + self.token

        return dx_command

    def create_mokapipe_command(self, fastq, pannumber):
        """
        Receieves R1 fastq file name and pan number for a single sample

        Returns dx run command for mokapipe (string)
        Valid for workflow GATK v3.10
        """
        # build nexus fastq paths - returns tuple for read1 and read2 and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # create the dx command
        command = self.base_command + config.mokapipe_fastqc1 + fastqs[0] \
            + config.mokapipe_fastqc2 + fastqs[1] \
            + config.mokapipe_sambamba_input + bedfiles["sambamba"] \
            + config.mokapipe_mokapicard_vendorbed_input + bedfiles["hsmetrics"] \
            + config.mokapipe_iva_email_input + ingenuity_email \
            + self.dest + self.dest_cmd + self.token

        return dx_command

    def create_mokaonc_command(self, mokaonc_list):
        """
        Receives a list of read1 fastqs. 
        MokaONC only supports one panel (Pan1190) so some values are hard coded here
        This pipeline is soon to be discontinued
        Returns one dx run command for all samples (string)
        """
        # start dx run command capturing job id etc
        dx_command = self.mokaonc_command
        # loop through the list of read 1 fastqs
        for sample_fq in mokaonc_list:
            # call function to build nexus fastq paths - returns tuple for read1 and read2
            fastqs = self.nexus_fastq_paths(sample_fq)
            # add each as an input 
            dx_command = config.mokaonc_fq_input +  fastqs[0] + config.mokaonc_fq_input + fastqs[1]

        # create the dx command include email address for ingenuity - NB only one panel is supported by MokaONC hense hard coded pan number
        dx_command = dx_command + config.mokaonc_ingenuity + self.panel_dictionary["Pan1190"]["ingenuity_email"] + self.dest + self.dest_cmd + "MokaONC_Output" + self.token
        
        return dx_command


    def build_iva_input_command(self):
        """
        Ingenuity import app is run once at the end of all workflows for all panels with iva_upload = True
        The ingenuity inputs are a list of jobid.output name. 
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
        This function returns the command for this python program
        """
        dx_command = "%s $jobid -t iva -p %s)" % (self.decision_support_preperation, self.nexusproject)
        return dx_command

    def sapientia_input_command(self):
        """
        Sapientia import app is run once at the end of all workflows for all panels with sapientia_upload = True
        The sapientia inputs are a list of jobid.output name. 
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
        This function returns the command for this python program
        """
        dx_command = "%s $jobid -t sapientia -p %s)" % (self.decision_support_preperation, self.nexusproject)
        return dx_command
    
    def create_mokaamp_command(self, fastq, pannumber):
        """
        Takes a single R1 fastq file and bed file
        builds nexus paths for input files
        returns dx run command for single sample (string)
        """

        # build nexus fastq paths - returns tuple for read1 and read2 and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # create the MokaAMP dx command
        dx_command = self.mokaamp_command + config.mokaamp_fastq_R1_stage + fastqs[0] + \
                    config.mokaamp_fastq_R2_stage + fastqs[1] + \
                    config.mokaamp_mokapicard_bed_stage + bedfiles["hsmetrics"] + \
                    config.mokaamp_mokapicard_capturetype_stage + self.panel_dictionary[pannumber]["capture_type"] + \
                    config.mokaamp_bamclipper_BEDPE_stage + bedfiles["mokaamp_bed_PE_input"] + \
                    config.mokaamp_chanjo_cov_level_stage + self.panel_dictionary[pannumber]["clinical_coverage_depth"] + \
                    config.mokaamp_sambamba_bed_stage + bedfiles["sambamba"] + \
                    config.mokaamp_vardict_bed_stage + bedfiles["mokaamp_variant_calling_bed"] + \
                    config.mokaamp_varscan_bed_stage + bedfiles["mokaamp_variant_calling_bed"] + \
                    config.mokaamp_lofreq_bed_stage + bedfiles["mokaamp_variant_calling_bed"] + \
                    config.mokaamp_varscan_strandfilter_stage + self.panel_dictionary[pannumber]["mokaamp_varscan_strandfilter"] + \
                    self.dest + self.dest_cmd + self.token
        
        # remove the bit that adds the job to the depends on list for the negative control as varscan fails on nearempty/-empty BAM files and this will stop multiqc etc running
        if "NTCcon" in read1:
            dx_command = dx_command.replace("jobid=$(", "").replace(config.Nexus_API_Key + ")", config.Nexus_API_Key)
        return dx_command


    def create_rpkm_command(self, pannumber):
        """
        The RPKM app requires a project id, bedfile and a string which contains the pannumber(s) of all files that should be included in this analysis.
        There can be multiple RPKM analyses per run and must wait until all other jobs have completed.
        This function returns the dx run command (string)
        """
        # call function to return all the bedfile paths
        bedfiles = self.nexus_bedfiles(pannumber)
        # Samples with different pannumbers can be included in the same rpkm analysis.
        # The app takes these pan numbers as a string, and will seperate on commas to identify multiple pan numbers
        # Multiple pannumbers are specified in the panel dictionary as a list under "RPKM_also_analyse"

        string_of_pannumbers_to_analyse = pannumber
        if self.panel_dictionary[pannumber]["RPKM_also_analyse"]:
            string_of_pannumbers_to_analyse + "," + ",".join(self.panel_dictionary[pannumber]["RPKM_also_analyse"])
                
        # build RPKM command
        dx_command = self.RPKM_command + config.rpkm_bedfile_input + bedfiles["rpkm_bedfile"] + config.rpkm_project_input + self.nexusproject \
            + config.rpkm_bamfiles_to_download_input + string_of_pannumbers_to_analyse + self.project + self.projectid + self.depends + self.token.rstrip(")")
        return dx_command
    
    def create_joint_variant_calling_command(self):
        return dx_command

    def run_sapientia_command(self):
        """
        The app which imports samples into ingenuity has been removed form the workflow. 
        It is now run as a seperate app, using the jobid.outputname as the input, which ensures the job doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job, and the output is captures into the variable $analysisid
        The dx run command is returned (string)
        """
        dx_command = self.sapientia_upload_command + " $analysisid" + self.dest + self.dest_cmd + self.project + self.projectid + self.token
        return dx_command
    
    def run_iva_command(self, pannumber):
        """
        The app which imports samples into ingenuity has been removed form the workflow. 
        It is now run as a seperate app, using the jobid.outputname as the input, which ensures the job doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job, and the output is captures into the variable $analysisid
        The ingenuity email is taken from the panel dictionary using the pan number input to this function.
        The dx run command is returned (string)
        """
        dx_command = self.iva_upload_command + " $analysisid" + config.iva_email_input_name + self.panel_dictionary[pannumber]["ingenuity_email"] + self.dest + self.dest_cmd + self.project + self.projectid + self.token
        return dx_command
    
    def add_to_depends_list(self):
        """
        As jobs are set off the jobid is captured
        The job ids are built into a string which can be passed to any apps which can't start untill specific jobs have sucessfully completed.
        This function returns a string which adds the jobid to the list of jobids
        """
        return self.depends_list

    def create_multiqc_command(self):
        """
        MultiQC is run at the very end of the run, after all QC tools have been run.
        MultiQC requires a project to download data from, and a coverage level.
        The coverage level differs between panels. The lowest value for the panels on this run is given as an input
        This function returns the dx run command (string)
        """
        lowest_coverage_level = 1000000
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                if int(self.panel_dictionary[pannumber]["multiqc_coverage_level"]) < lowest_coverage_level:
                    lowest_coverage_level = self.panel_dictionary[pannumber]["multiqc_coverage_level"]
        #multiqc_coverage_level = config.mokaamp_multiqc_coverage_level
        # build multiqc command, capturing the job id- eg command = jobid=$(dx run multiqc -iproject_for_multiqc=002_170222_ALEDTEST -icoveragelevel=20 --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid --brief --auth xyz)
        dx_command = self.multiqc_command + config.multiqc_project_input + self.nexusproject + config.multiqc_coverage_level_input + lowest_coverage_level \
            + self.project + self.projectid + self.depends + self.token
        return dx_command
    
    def run_peddy_command(self):
        """
        Peddy is run once at the end of a WES run. It takes a project and downloads all the required files.
        This function builds that commands and the dx run command is returned (string)
        """
        # build peddy command - eg command = jobid=$(dx run peddy -iproject_for_peddy = 002_170222_ALEDTEST --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid)
        dx_command = self.peddy_command + config.peddy_project_input + self.nexusproject + self.project + self.projectid.rstrip() + self.depends + self.token
        return dx_command

    def create_smartsheet_command(self):
        """
        Once all workflows have completed smartsheet can be updated to record OPMS.
        This function calls the app which updates smartsheet, returning the dx run command (string)
        """
        dx_command = self.smartsheet_update_command + config.smartsheet_mokapipe_complete + self.runfolder + self.project + self.projectid + self.depends + self.token.rstrip(")")
        return dx_command
    

    def write_dx_run_cmds(self, command_list):
        """
        Takes a list of commands and writes them to file.
        """
        with open(self.bash_script, 'w') as dxrun_commands:
            dxrun_commands.writelines(command_list)

    def run_dx_run_commands(self):
        """
        Executes the bash script
        Writes the job ids to log file
        Reports any standard error
        """
        # run a command to execute the bash script made above
        cmd = "bash " + self.bash_script

        if not config.debug:
            # execute command
            proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # capture the streams
            (out, err) = proc.communicate()
        else:
            out = "debug stdout example when setting off dx run commands"
            err = "debug stderr example when setting off dx run commands"

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

    
    def smartsheet_workflows_commands_sent(self):
        """
        This function updates smartsheet to say that the runfolder has started to be processed
        A payload is created, including a count of samples, timestamp and runfolder
        This is posted using the requests module to a given url
        The response is parsed to check the status was "success" otherwise an error is raised.
        """
        self.upload_agent_script_logfile.write("\n----------------------UPDATE SMARTSHEET----------------------\n")
        # #uncomment this block if want to get the column ids for a new sheet
        ########################################################################
        # # Get all columns.
        # url=self.smartsheet_url+"/columns"
        # r = requests.get(url, headers=self.headers)
        # response= r.json()
        #
        # # get the column ids
        # for i in response['data']:
        #     print i['title'], i['id']
        ########################################################################

        # set all values to be inserted
        payload = '{"cells": [{"columnId": ' + str(config.ss_title) + ', "value": "' + self.runfolder + '"}, {"columnId": ' + str(config.ss_description) + \
            ', "value": "MokaPipe"},{"columnId": ' + str(config.ss_samples) + ', "value": ' + str(len(self.list_of_processed_samples)/2) + '},{"columnId": ' + str(config.ss_status) + \
            ', "value": "In Progress"},{"columnId": ' + str(config.ss_priority) + ', "value": "Medium"},{"columnId": ' + str(config.ss_assigned) + \
            ', "value": "aledjones@nhs.net"},{"columnId": ' + str(config.ss_received) + ', "value": "' + str(self.smartsheet_now) + '"}], "toBottom":true}'

        # create url for uploading a new row
        url = self.smartsheet_url + "/rows"

        # add the row using POST
        r = requests.post(url, headers=self.headers, data=payload)

        # capture the row id
        response = r.json()
       
        # check the result of the update attempt
        for line_key in response:
            if line_key == "message":
                if response[line_key] == "SUCCESS":
                    self.upload_agent_script_logfile.write("smartsheet updated to say in progress\n")
                    self.logger("run started added to smartsheet", "smartsheet_pass")
                else:
                    self.logger("run started NOT added to smartsheet for run " + self.runfolder, "smartsheet_fail")
                    self.upload_agent_script_logfile.write("smartsheet NOT updated at in progress step\n" + str(response))
                    
    def write_opms_queries_mokapipe(self):
        """
        Samples processed using Mokapipe are recorded in moka using an insert query.
        This function will create an insert query for each sample processed through mokapipe.
        """
        queries = []
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokapipe add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokapipe"]:
                    queries.append("insert into NGSCustomRuns(DNAnumber,PipelineVersion) values ('" + str(fastq.split("_")[2]) + "','" + config.mokapipe_pipeline_ID + "')")
        if len(queries)> 0:
            # add workflow to sql dictionary
            self.sql_queries["mokapipe"]={"count":len(queries),"query":queries}

    def write_opms_queries_mokawes(self):
        """
        Samples processed using MokaWES are recorded in moka using an update query.
        This function will create an single query for all sample processed using mokawes.
        """
        dnanumbers=[]
        # add workflow to sql dictionary
        
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokawes add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokawes"]:
                    dnanumbers.append(str(fastq.split("_")[2]))
        if len(dnanumbers) > 0:
            self.sql_queries["mokawes"] = {"count":len(dnanumbers),"query":"update NGSTest set PipelineVersion = " + config.mokawes_pipeline_ID + " , StatusID = " + config.mokastatus_dataproc_ID + " where dna in ('" + ("','").join(dnanumbers) + "') and StatusID = " + config.mokastat_nextsq_ID}

    def write_opms_queries_oncology(self):
        """
        Samples tested using mokaamp or mokaonc are not booked into moka until the analysis stage so queries cannot be used to record pipeline version.
        This is recorded manually when creating the test in Moka
        Therefore an email informing the oncology team which version of the pipeline was applied is sent.
        """
        # list of workflows used in this run
        workflows=[]
        # loop through fastqs to see which workflows were used
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using one of the oncology pipelines add the query to list of queries
                # use the dnanexus workflow path, taking only the workflow name
                if self.panel_dictionary[pannumber]["oncology"]:
                    if self.panel_dictionary[pannumber]["mokaamp"]:
                        workflows.append(config.mokaamp_path.split("/")[-1])
                    if self.panel_dictionary[pannumber]["mokaonc"]:
                        workflows.append(config.mokaonc_path.split("/")[-1])
        # if oncology workflows were applied add email message (to dictionary to be sent)
        if len(workflows) > 0:
            self.sql_queries["oncology"] = {"workflows": set(workflows), \
                    "query": self.runfolder + " being processed using workflow " + ",".join(set(workflows))+ "\n\n" + config.mokaamp_email_message}

        
    def send_opms_queries(self):
        """
        Queries to record the pipeline versions are emailed. 
        Custom panel and WES queries are sent to bioinformatics to action where as cancer workflows are sent to oncology team to action.
        This function sends the emails, using the queries built earlier.
        The oncology and rare disease emails are sent seperately and independantly of each other.
        """
        # send oncology email first
        if "oncology" in self.sql_queries:
            # email the workflow used to the oncology team 
            self.email_subject = "MOKAPIPE ALERT : Started pipeline for " + self.runfolder
            self.email_message = self.runfolder + " being processed using workflow " + ",".join(self.sql_queries["oncology"]["workflows"]) \
                                + "\n\n" + self.sql_queries["oncology"]["query"]
            # send email - pass multiple reciepients in a list
            self.send_an_email([config.oncology_you, config.you])

        # determine if need to send rare disease email too.
        workflows = []
        sql_statements=[]
        count=0
        # use the dnanexus workflow path, taking only the workflow name
        if "mokapipe" in self.sql_queries:
            workflows.append(config.mokapipe_path.split("/")[-1])
            sql_statements += self.sql_queries["mokapipe"]["query"]
            count+=self.sql_queries["mokapipe"]["count"]
        if "mokawes" in self.sql_queries:
            workflows.append(config.mokawes_path.split("/")[-1])
            sql_statements += self.sql_queries["mokawes"]["query"]
            count+=self.sql_queries["mokapipe"]["count"]
        
        if len(workflows) > 0 and len(sql_statements) > 0:
            # email this query
            self.email_subject = "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for " + self.runfolder
            self.email_priority = 1  # high priority
            self.email_message = self.runfolder + " being processed using workflow " + ",".join(set(workflows)) + \
            "\n\nPlease update Moka using the below query and ensure that " + str(count) + " records are updated:\n\n" + "\n".join(sql_statements)
            # send email
            self.send_an_email(config.you)

    def upload_rest_of_runfolder(self):
        """
        The rest of the runfolder requires backing up, excluding bcl files.
        A python script which is a wrapper for the upload agent is used.
        """
        # write status update to log file
        self.upload_agent_script_logfile.write("\n----------------------UPLOAD REST OF RUNFOLDER----------------------\n")
        
        # create the samplesheet name to copy
        samplesheet_name = self.runfolder + "_SampleSheet.csv"

        # copy samplesheet into project
        copyfile(config.samplesheets + samplesheet_name, os.path.join(self.runfolderpath, samplesheet_name))

        cmd = "python config.backup_runfolder_script -i " + self.runfolderpath + " -p " + self.nexusproject + "  --ignore L00 --logpath " + config.backup_runfolder_logfile

        # write to the log file that samplesheet was copied and runfolder is being uploaded, linking to log files for cmds and stdout
        self.upload_agent_script_logfile.write("Copied samplesheet to runfolder\nUploading rest of run folder to Nexus using backup_runfolder.py:\n " + cmd /
                + "\nsee standard out from these commands in log file @ " + os.path.join(config.backup_runfolder_logfile, self.runfolder) + "\n\n----------------CHECKING SUCCESSFUL UPLOAD OF RUNFOLDER----------------\n")
        
        proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

        # capture the streams
        (out, err) = proc.communicate()
        

        
    def upload_log_files(self):
        pass
    def look_for_upload_errors(self):
        # assess backup runfolder output
        #and assess upload agent when uploading log files


    #     # create empty list for the sql queries
    #     sql = []
    #     # Set variable to count the number of records to be updated by SQL
    #     records = 0

    #     # loop through the WES DNA numbers to generate sql query to record Pipeline version
    #     if len(self.list_of_DNA_numbers_WES) > 0:
    #         # count the number of records the SQL will update to include in email - (WES)
    #         if records == 0:
    #             records = len(set(self.list_of_DNA_numbers_WES))
    #         else:
    #             records += len(set(self.list_of_DNA_numbers_WES))

    #         # start string
    #         DNA_list = "('"
    #         # loop through unique list of dna numbers obtained from fastq filenames
    #         for DNA in set(self.list_of_DNA_numbers_WES):
    #             # build the sql query
    #             DNA_list = DNA_list + DNA + "','"
    #         # close string
    #         DNA_list = DNA_list + ")"
    #         # remove the excess ,' from the end of the string
    #         DNA_list = DNA_list.replace(",')", ")")

    #         # build the rest of the sql update query and append to list.
    #         # Query will update pipeline and test status for tests which are currently active
    #         sql.append("update NGSTest set PipelineVersion = " + config.mokawes_pipeline_ID + " , StatusID = " + config.mokastatus_dataproc_ID + " where dna in " + DNA_list + " and StatusID = " + config.mokastat_nextsq_ID)

    #     # custom panels requires insert queries (one per sample)
    #     if len(self.list_of_DNA_numbers_nonWES) > 0:
    #         # count the number of records SQL will update to include in email (non-WES)
    #         if records == 0:
    #             records = len(set(self.list_of_DNA_numbers_nonWES))
    #         else:
    #             records += len(set(self.list_of_DNA_numbers_nonWES))

    #         # loop through unique list of dna numbers obtained from fastq filenames
    #         for DNA in set(self.list_of_DNA_numbers_nonWES):
    #             # build the rest of the sql update query
    #             sql.append("insert into NGSCustomRuns(DNAnumber,PipelineVersion) values ('" + DNA + "','" + config.mokapipe_pipeline_ID + "')")

    #     #  combine all the queries into a string suitable for an email
    #     sql_statements = ""

    #     # if there are no sql commands in the list it must be an oncology run
    #     if len(sql) == 0:
    #         # email the workflow used so this can be entered manually
    #         self.email_subject = "MOKAPIPE ALERT : Started pipeline for " + self.runfolder
    #         self.email_message = self.runfolder + " being processed using workflow " + ",".join(set(workflows)) + "\n\n" + config.mokaamp_email_message
    #         # send email
    #         self.send_an_email([config.oncology_you, config.you])
    #     # otherwise loop through each statement and create a string.
    #     else:
    #         for statement in sql:
    #             sql_statements = sql_statements + statement + "\n"

    #         # write action to system log file
    #         self.logger("SQL statement email sent for run " + self.runfolder, "UA_pass")

    #         # email this query
    #         self.email_subject = "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for " + self.runfolder
    #         self.email_priority = 1  # high priority
    #         self.email_message = self.runfolder + " being processed using workflow " + ",".join(set(workflows)) + "\n\nPlease update Moka using the below query and ensure that " + \
    #             str(records) + " records are updated:\n\n" + sql_statements
    #         # send email
    #         self.send_an_email(config.you)

    #     if not config.debug:
    #         # call function to update smartsheet to say run in progress
    #         self.smartsheet_workflows_commands_sent()

   
    # def RPKM(self):
    #     '''This function loops through all the panel numbers found in the fastq folders and where relevant submits a RPKM job '''
    #     # create a copy of the list of unique panels in this run - this will be used to report which panels have been processed in the log file.
    #     CNV_panels_reported = set(self.panels_in_run)
    #     # self.panel_in_run contains all panels found in the run, except for Pan493 and oncology panels - loop through this copy of the list not CNV_panels_reported as this list will have items removed
    #     for panel in set(self.panels_in_run):
    #         # ignore focussed exome  as this will never have RPKM (other panels which won't have RPKM have been filtered out previously)
    #         if panel != "Pan1620":
    #             # ensure there is a CNV bedfile in the dictionary but if not don't raise an exception, trigger a alert via system log.
    #             if not config.panelnumbers[panel]:
    #                 self.logger("Unknown CNV bedfile for " + panel, "UA_fail")
    #                 # remove this panel from the list of RPKM panels issued below
    #                 CNV_panels_reported.remove(panel)
    #             else:
    #                 # build RPKM command
    #                 RPKM_command = self.RPKM_command + config.rpkm_bedfile_input + config.app_project + config.bedfile_folder + config.panelnumbers[panel] + "_RPKM.bed" + config.RPKM_project + \
    #                     self.nexusproject + config.RPKM_bedfile_to_download + panel + self.project + self.projectid.rstrip() + self.depends + self.token.rstrip(")")
    #                 # write commands to bash script
    #                 self.DNA_Nexus_bash_script.write(RPKM_command + "\n")

    #     # write to cron job script using panels in CNV_panels_reported
    #     self.upload_agent_script_logfile.write("RPKM commands build for " + str(len(CNV_panels_reported)) + " panels (" + " ".join(CNV_panels_reported) + ") - see " + self.bash_script + "\n\n")

    # def upload_rest_of_runfolder(self):
    #     # write status update to log file
    #     self.upload_agent_script_logfile.write("\n----------------------UPLOAD REST OF RUNFOLDER----------------------\n")

    #     # open file for upload agent standard out (in append mode)
    #     runfolder_upload_stdout_file = open(os.path.join(self.runfolderpath, config.upload_started_file), 'a')

    #     # distinguish between upload of fastq and rest of runfolder
    #     runfolder_upload_stdout_file.write("\n----------------------Uploading rest of runfolder " + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")

    #     # close log file
    #     runfolder_upload_stdout_file.close()

    #     # create temp bash_script
    #     temp_bash = os.path.join(self.runfolderpath, "/temp_" + config.runfolder_upload_cmds.replace('.txt', '.sh'))
    #     # open temp file containing upload agent commands
    #     temp_runfolder_upload_cmd_file = open(temp_bash, 'w')

    #     # create the samplesheet name to copy
    #     samplesheet_name = self.runfolder + "_SampleSheet.csv"

    #     # copy samplesheet into project
    #     copyfile(config.samplesheets + samplesheet_name, os.path.join(self.runfolderpath, samplesheet_name))

    #     # write to the log file that samplesheet was copied and runfolder is being uploaded, linking to log files for cmds and stdout
    #     self.upload_agent_script_logfile.write("Copied samplesheet to runfolder\nUploading rest of run folder to Nexus using commands in " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds) +
    #         "\nsee standard out from these commands in log file @ " + os.path.join(self.runfolderpath, config.upload_started_file) + "\n\n----------------CHECKING SUCCESSFUL UPLOAD OF RUNFOLDER----------------\n")

    #     # loop through the run folder
    #     for root, subFolder, files in os.walk(self.runfolderpath):
    #         # for every file
    #         for item in files:
    #             # capture the path
    #             path = str(os.path.join(root, item))

    #             # skip image files
    #             if "/L00" in path:
    #                 pass
    #             # skip fastq files already uploaded
    #             elif path.endswith(".fastq.gz"):
    #                 pass
    #             # skip log files still being written to
    #             elif path.endswith(config.upload_started_file) or path.endswith(temp_bash) or path.endswith(config.runfolder_upload_cmds):
    #                 pass
    #             # skip samplesheet
    #             elif path.endswith("SampleSheet.csv"):
    #                 pass
    #             # otherwise upload
    #             else:
    #                 # Use path to build desitnation folder within nexus. put in quotations to avoid weird characters and spaces
    #                 path_to_upload = "'" + path + "'"
    #                 # remove the project prefix (002_), the path to the runfolders ("/media/data1/share") and the file name
    #                 path_for_nexus = path.replace(self.runfolder, self.nexusproject.replace(config.NexusProjectPrefix, "")).replace(config.runfolders, "").replace(item, "")

    #                 # build the nexus upload command
    #                 nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
    #                     + "  --folder " + path_for_nexus + " --do-not-compress --upload-threads 10 " + path_to_upload + self.restart_ua_2 % (path_to_upload)

    #                 # copy the command to the temporary cmd file
    #                 temp_runfolder_upload_cmd_file.write(nexus_upload_command + "\n")
    #     temp_runfolder_upload_cmd_file.close()

    #     if not config.debug:
    #         # create command redirecting stderror to the log file
    #         run_upload_agent_script = "bash " + temp_bash + " >> " + os.path.join(self.runfolderpath, config.upload_started_file) + " 2>&1"
    #         # run the command
    #         proc = subprocess.Popen([run_upload_agent_script], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    #         # capture the streams
    #         (out, err) = proc.communicate()

    #         # All standard error is redirected to stdout in the command need -  to parse STDout for errors
    #         # set a flag so a "no errors reported" message is only written if no errors are seen!
    #         error = False
    #         # for each line in the standard out
    #         for linenumber, line in enumerate(out):
    #             # skip if the line is empty, or it starts with Uploading or ends with the expected success statement
    #             if line.startswith("Uploading") or line.endswith("was uploaded successfully. Closing...") or len(line) < 2:
    #                 pass
    #             # if the line doesn't contain any of these expected lines
    #             else:
    #                 # set the flag so the no errors reported message is not written
    #                 error = True
    #                 # expect a pair of lines for each file to be uploaded, the first one detailing which file is being uploaded and the second a pass/fail statement.
    #                 # we are looking for the error in the second line so we want this and the line before it
    #                 # however if the error message is the first line can't record the line before it so use a if loop
    #                 if linenumber == 0:
    #                     # write only this line to log
    #                     self.upload_agent_script_logfile.write("Error when executing script:\n" + line + "\n")
    #                 else:
    #                     # write this line and the line before (as this contains the name of the file trying to upload) to log
    #                     self.upload_agent_script_logfile.write("Error when executing script:\nError lines = " + out[linenumber - 1] + "\n" + line + "\n")
    #                 # write to logger that there was an issue
    #                 self.logger("Error whilst uploading rest of runfolder - see all standard out " + os.path.join(self.runfolderpath, config.upload_started_file), "UA_fail")
    #         # if there were no errors write this to log file
    #         if not error:
    #             # write to log
    #             self.upload_agent_script_logfile.write("No errors reported\n")

    #     # copy commands from temporary upload agent file to the one containing the fastq upload command
    #     command = "cat " + temp_bash + " >> " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds)

    #     proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    #     # capture the streams
    #     (out, err) = proc.communicate()

    #     if err:
    #         self.upload_agent_script_logfile.write("Error when copying temp upload commands to the archived script. See temp file @ " + os.path.join(self.runfolderpath, "temp_" + config.runfolder_upload_cmds) + "\n")
    #     else:
    #         self.upload_agent_script_logfile.write("upload agent commands copied to the file in " + os.path.join(self.runfolderpath, config.runfolder_upload_cmds) + "\n")

    #         # if copy went ok, delete temp file
    #         delete_temp_file_cmd = "rm " + temp_bash
    #         proc = subprocess.Popen([delete_temp_file_cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    #         # capture the streams
    #         (out, err) = proc.communicate()
    #         if err:
    #             self.upload_agent_script_logfile.write("Error deleting the temp file\n")

    #     # call function which looks for errors when uploading
    #     self.look_for_upload_errors_runfolder()

    #     # close the log file
    #     self.upload_agent_script_logfile.close()

    #     # rename file to show what runs were affected.
    #     self.rename = self.runfolder + "_upload_agent_log.txt"
    #     os.rename(self.upload_agent_logfile_name, self.upload_agent_logfile_name.replace('.txt', self.rename))

    #     # capture the new file name so can continue to write to it.
    #     self.upload_agent_logfile_name = self.upload_agent_logfile_name.replace('.txt', self.rename)

    #     # reset self.rename to prevent logfile being renamed incorrectly.
    #     self.rename = ""

    #     # call function to upload log files
    #     self.upload_log_files()

    # def upload_log_files(self):
    #     ''' log files include:
    #     1. the log file for this script containing all commands used (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_log)
    #     2. demultiplexing log file (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_log_files)
    #     3. nexus project creation logs (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Nexus_project_creation_logs)
    #     4. runfolder_upload_commands (in the run folder)
    #     5. runfolder_upload_stdout (in the run folder)
    #     6. logfile used to set off the workflow (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs)
    #     7. samplesheet
    #     '''
    #     # empty list to hold files (and paths) to be uploaded
    #     logfile_list = []

    #     # ######## path for upload agent log file (file1) #########
    #     # get full filepath for the log file containing the decisions made by this script
    #     upload_agent_log_file_to_upload = self.upload_agent_logfile_name
    #     # add to list
    #     logfile_list.append(upload_agent_log_file_to_upload)

    #     # ######## demultiplexing log file (file2) #########
    #     # empty variable to build a list of files
    #     demultiplex_log = ""
    #     # loop through files in demultiplex log folder (contains decisions made when demultiplexing script is run - have been renamed to contain run folder if a run was demultiplexed)
    #     for logfile in os.listdir(config.demultiplex_logfiles):
    #         # if runfolder in filename
    #         if self.runfolder in logfile:
    #             # add file path and file name to list
    #             demultiplex_log = config.demultiplex_logfiles + logfile
    #             logfile_list.append(demultiplex_log)

    #     # ######## nexus project_creation_logfile (file 3) #########
    #     # get the full file path for file containing comands used to create and share nexus project
    #     nexus_project_creation_logfile = config.DNA_Nexus_project_creation_logfolder + self.runfolder + ".sh"
    #     # add to list
    #     logfile_list.append(nexus_project_creation_logfile)

    #     # ######## runfolder upload commands (file 4) #########
    #     # get the full file path for the cmds used to upload fastq, runfolder and log files
    #     runfolder_upload_logfile_to_upload = os.path.join(self.runfolderpath, config.runfolder_upload_cmds)
    #     # add to list
    #     logfile_list.append(runfolder_upload_logfile_to_upload)

    #     # ######## runfolder upload stdout (file 5) #########
    #     # get the full file path for the file containing stdout/ stderr from upload agent
    #     runfolder_upload_logfile_to_upload = os.path.join(self.runfolderpath, config.upload_started_file)
    #     # add to list
    #     logfile_list.append(runfolder_upload_logfile_to_upload)

    #     # ######## bash script which sets off workflow (file 6) #########
    #     # add the file which sets off the dx run commands
    #     logfile_list.append(self.bash_script)

    #     # ######### samplesheet (file7) #########
    #     # create a upload agent command for samplesheet (copied into the runfolder above) which is being uploaded into the runfolder
    #     samplesheet_nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
    #         + "  --folder /" + self.nexusproject.replace(config.NexusProjectPrefix, "") + "/" + " --do-not-compress --upload-threads 10 " + self.runfolderpath + "/" + self.runfolder + "_SampleSheet.csv " + self.restart_ua_2

    #     # create command line for files in the logfile_list (to be put into a logfiles subfolder)
    #     nexus_upload_command = self.restart_ua_1 + config.upload_agent + " --auth-token " + config.Nexus_API_Key + " --project " + self.nexusproject \
    #         + "  --folder /" + self.nexusproject.replace(config.NexusProjectPrefix, "") + "/Logfiles/" + " --do-not-compress --upload-threads 10 " + " ".join(logfile_list) + self.restart_ua_2

    #     # write these commands to the runfolder_upload_cmds_logfile before upload.
    #     with open(os.path.join(self.runfolderpath, config.runfolder_upload_cmds), 'a') as runfolder_upload_cmd_file:
    #         runfolder_upload_cmd_file.write("\n----------------------Upload log files----------------------\n")
    #         runfolder_upload_cmd_file.write(samplesheet_nexus_upload_command + "\n" + nexus_upload_command)
        

    #     if not config.debug:
    #         # run the command, redirecting stderror to stdout
    #         proc = subprocess.Popen([nexus_upload_command + " & " + samplesheet_nexus_upload_command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)

    #         # capture the streams (err is redirected to out above)
    #         (out, err) = proc.communicate()

    #     else:
    #         print nexus_upload_command
    #         out = "x"
    #         err = "y"

    #     # capture stdout to log file containing stdour and stderr
    #     runfolder_upload_stdout_file = open(os.path.join(self.runfolderpath, config.upload_started_file), 'a')
    #     runfolder_upload_stdout_file.write("\n----------------------Uploading logfiles (this will not be included in the file within DNA Nexus) " +
    #         str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")
    #     runfolder_upload_stdout_file.write(out)
    #     runfolder_upload_stdout_file.close()

    #     # check standard out from upload of log files
    #     # open logfile first to write info from check
    #     self.upload_agent_script_logfile = open(self.upload_agent_logfile_name, 'a')
    #     self.upload_agent_script_logfile.write("\n----------------CHECKING SUCCESSFUL UPLOAD OF LOGFILES (this will not be in DNA Nexus)----------------\n")

    #     # call function to check stdout
    #     self.look_for_upload_errors_logfiles()

    #     # close log file
    #     self.upload_agent_script_logfile.close()

    

    

    # def look_for_upload_errors_runfolder(self):
    #     '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
    #     If present email link to the log file
    #     NB any errors from the fastq upload would also be detected here.'''

    #     # flag so no errors found statement only written once
    #     upload_error = False

    #     for upload in open(os.path.join(self.runfolderpath, config.upload_started_file)).read().split("Uploading file"):
    #         # if there was an error during the upload...
    #         if self.ua_error in upload:
    #             # if error seen set flag
    #             upload_error = True
    #             # if it still completed successfully carry on
    #             if "uploaded successfully" in upload:
    #                 self.upload_agent_script_logfile.write("There was a disruption to the network when uploading the rest of the runfolder but it completed successfully\n")
    #                 self.logger("upload of runfolder was disrupted but completed for run " + self.runfolder, "UA_disrupted")
    #             # other wise send an email and write to log
    #             else:
    #                 self.upload_agent_script_logfile.write("There was a disruption to the network which prevented the rest of the runfolder being uploaded\n")
    #                 self.logger("upload of runfolder failed for run " + self.runfolder, "UA_fail")

    #     # only state no errors seen if no errors were seen!
    #     if not upload_error:
    #         # write to log file check was ok
    #         self.upload_agent_script_logfile.write("There were no issues when backing up the run folder\n")
    #         self.logger("backup of runfolder complete for run " + self.runfolder, "UA_pass")

    # def look_for_upload_errors_logfiles(self):
    #     '''parse the file containing standard error/standard out from the upload agent and look for the phrase "ERROR".
    #     If present email link to the log file
    #     NB any errors from the fastq upload and run folderwould also be detected here.'''

    #     # flag so no errors found statement only written once
    #     upload_error = False

    #     # Open the log file and split for each individual upload command
    #     for upload in open(os.path.join(self.runfolderpath, config.upload_started_file)).read().split("Uploading file"):
    #         # if there was an error during the upload...
    #         if self.ua_error in upload:
    #             # if error seen set flag
    #             upload_error = True
    #             # if it still completed successfully carry on
    #             if "uploaded successfully" in upload:
    #                 self.upload_agent_script_logfile.write("There was a disruption to the network when uploading logfiles but it completed successfully\n")
    #                 self.logger("upload of logfiles was disrupted but completed for run " + self.runfolder, "UA_disrupted")
    #             # other wise send an email and write to log
    #             else:
    #                 self.upload_agent_script_logfile.write("There was a disruption to the netowkr which prevented log files being uploaded\n")
    #                 self.logger("upload of log files failed for run " + self.runfolder, "UA_fail")
    #     # only state no errors seen if no errors were seen!
    #     if not upload_error:
    #         # write to log file check was ok
    #         self.upload_agent_script_logfile.write("There were no issues when uploading the logfiles\n")
    #         self.logger("upload of log files complete without issue " + self.runfolder, "UA_pass")
    
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
