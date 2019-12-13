"""upload_and_setoff_workflows.py
Once demultiplexing has been complete the files require uploading to DNANexus.
This script will be scheduled to run and identify any folders that require further processing
get_list_of_runs loops through runfolders and creates an instance of the process_runfolder class for each runfolder
The process_runfolder class creates an instance of the runfolder_object class and the quarterback module calls all other modules to assess the runfolder
if required, a Nexus project is created and shared, data uploaded and the pipelines set off as determined by the panel number encoded in the filename
@author: aled
"""

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
        all_runfolders = os.listdir(config.runfolders)

        # for each folder if it is not samplesheets/tar.gz folder pass the runfolder to the next class
        for folder in all_runfolders:
            # Ignore folders in the list config.ignore_directories and test that it is a directory (ignoring files)
            if folder not in config.ignore_directories and os.path.isdir(os.path.join(config.runfolders, folder)):
                # pass folder and timestamp to class instance
                runfolder_instance = process_runfolder(folder, self.now)
                runfolder_instance.quarterback()

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

class runfolder_object():
    """
    This class holds all the runfolder specific 
    """
    def __init__(self, runfolder):
        # set empty variables to be defined based on the run
        self.runfolder_name = runfolder
        # create full path to runfolder
        self.runfolderpath = os.path.join(config.runfolders, runfolder)
        
        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath +  config.fastq_folder
        
        # path to the run folder's dx run commands
        self.runfolder_dx_run_script = config.DNA_Nexus_workflow_logfolder + self.runfolder_name + ".sh"

        self.nexus_project_name =  ""
        self.nexus_path = ""

class process_runfolder():
    ''' 
    This class assesses a runfolder to check if it required processing.  if the runfolder meets the criteria to be processed.
    Fastqs are uploaded to DNA Nexus, dx run commands built and executed and then the rest of the runfolder is also uploaded.
    All actions are logged in the logfile created when the script is run.
    A new instance of this class is initiated for each runfolder being assessed. 
    '''

    def __init__(self,runfolder, now, debug_mode=False):
        # name of file which denotes demultiplexing is underway/complete
        self.demultiplexed = "demultiplexlog.txt"
        self.debug_mode = debug_mode
        # # fastq folder
        #self.fastq_folder_path = ""

        self.runfolder_obj = runfolder_object(runfolder)
        self.now = now
        
        self.upload_agent_logfile_path = config.upload_agent_logfile + self.now + "_.txt"
        
        # string of fastqs for upload agent
        self.fastq_string = ""

        # list of fastqs to get ngs run number and WES batch
        self.list_of_processed_samples = []

        self.list_of_DNA_numbers_WES = []
        self.list_of_DNA_numbers_Onc = []
        self.list_of_DNA_numbers_nonWES = []

        # ####################################DNA Nexus########################
        # DNA Nexus commands
        self.source_command = "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\ndepends_list=''\n"

        self.createprojectcommand = "project_id=\"$(dx new project --bill-to %s \"%s\" --brief --auth-token " + config.Nexus_API_Key + ")\"\n"
        self.addprojecttag = "dx tag $project_id "
        self.mokapipe_command = "jobid=$(dx run " + config.app_project + config.mokapipe_path + " -y --name "
        self.wes_command = "jobid=$(dx run " + config.app_project + config.mokawes_path + " -y --name "
        self.peddy_command = "jobid=$(dx run " + config.app_project + config.peddy_path
        self.multiqc_command = "jobid=$(dx run " + config.app_project + config.multiqc_path
        self.upload_multiqc_command = "jobid=$(dx run " + config.app_project + config.upload_multiqc_path + " -y"
        self.smartsheet_update_command = "dx run " + config.app_project + config.smartsheet_path
        self.RPKM_command = "dx run " + config.app_project + config.RPKM_path
        self.mokaonc_command = "jobid=$(dx run " + config.app_project + config.mokaonc_path + " -y"
        self.mokaamp_command = "jobid=$(dx run " + config.app_project + config.mokaamp_path + " -y --name "
        self.decision_support_preperation = "analysisid=$(python %s -a " % (os.path.join(os.path.dirname(os.path.realpath(__file__)),config.decision_support_tool_input_script))
        self.sapientia_upload_command = "jobid=$(dx run " + config.app_project + config.sapientia_app_path + " -y"
        self.iva_upload_command = "jobid=$(dx run " + config.iva_app_path + " -y"
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

        # list of panels
        self.panels_in_run = []

        # command to restart upload agent part 1
        self.restart_ua_1 = "ua_status=1; while [ $ua_status -ne 0 ]; do "
        self.restart_ua_2 = "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo \"temporary issue when uploading file %s\"; fi ; done"

        # ######################email message###############################
        self.email_subject = ""
        self.email_message = ""
        self.email_priority = 3

        # ########################################smartsheet API##############
        # newly inserted row
        self.rowid = ""

        # time stamp
        self.smartsheet_now =  str('{:%Y-%m-%d}'.format(datetime.datetime.utcnow()))

        # requests info
        self.headers = {"Authorization": "Bearer " + config.smartsheet_api_key, "Content-Type": "application/json"}
        self.smartsheet_url = 'https://api.smartsheet.com/2.0/sheets/' + str(config.smartsheet_sheetid)

        self.panel_dictionary = self.set_panel_dictionary()
        
        self.sql_queries={}

    
    def run_tests(self):        
        # perform upload agent test
        if not self.test_upload_agent(self.perform_test(self.execute_subprocess_command(config.upload_agent_path + config.upload_agent_test_command)[0], "ua")):
            raise Exception, "Upload agent not installed"

        # test dx toolkit installation
        if not self.test_dx_toolkit(self.perform_test(self.execute_subprocess_command(config.dx_sdk_test)[0],"dx_toolkit")):
            raise Exception, "dx toolkit not installed"
            

    def quarterback (self):
        """
        This module calls all other modules in order
        """
        self.run_tests()
        # build dictionary of panel settings
        self.panel_dictionary = self.set_panel_dictionary()
        
        # check if already uploaded and demultiplkexing finished sucessfully
        if not self.already_uploaded() and self.demultiplex_completed_successfully():
            self.list_of_processed_samples, self.fastq_string, not_processed = self.find_fastqs(self.runfolder_obj.fastq_folder_path)
            if self.list_of_processed_samples:
                # build the project name using the WES batch and NGS run numbers
                self.dest_cmd, self.runfolder_obj.nexus_path, self.runfolder_obj.nexus_project_name = self.build_nexus_project_name(self.capture_any_WES_batch_numbers(self.list_of_processed_samples),self.capture_library_batch_numbers(self.list_of_processed_samples))
                # create bash script to create and share nexus project -return filepath
                # pass filepath into module which runs project creation script - capturing projectid
                self.projectid = self.run_project_creation_script(self.write_create_project_script())
                # build upload agent command for fastq upload and write stdout to ua_stdout_log
                # pass the path to ua_stdout_log to function which checks fastqs were uploaded without error
                self.look_for_upload_errors_fastq(self.upload_fastqs())

                self.write_dx_run_cmds(self.start_building_dx_run_cmds(self.list_of_processed_samples))
                self.run_dx_run_commands()
                self.smartsheet_workflows_commands_sent()
                self.sql_queries["mokawes"] = self.write_opms_queries_mokawes(self.list_of_processed_samples)
                self.sql_queries["oncology"] = self.write_opms_queries_oncology(self.list_of_processed_samples)
                self.sql_queries["mokapipe"] = self.write_opms_queries_mokapipe(self.list_of_processed_samples)
                self.send_opms_queries()
                self.look_for_upload_errors(self.upload_rest_of_runfolder(), success=config.backup_runfolder_success)
                self.look_for_upload_errors(self.upload_log_files())
   
    def set_panel_dictionary(self):
        """ 
        Populate the dictionary detailing panel specific settings.
        Default settings are set in the config file and then updated as and when required for each panel the defaults in config file.
        Loop through panel specific properties in config file and overwrite any default with panel specific settings
        Return dictionary
        """
        dictionary_to_return = {}
        # for each panel 
        for panel in config.panel_list:          
            # loop through default settings, adding to dictionary and  then loop through panel settings from config, overwriting any defaults
            dictionary_to_return[panel] = {}
            for setting in  config.default_panel_properties:
                dictionary_to_return[panel][setting] = config.default_panel_properties[setting]
            for setting in config.panel_settings[panel]:
                dictionary_to_return[panel][setting] = config.panel_settings[panel][setting]
        return dictionary_to_return
    
    def test_upload_agent(self,test_result):
        """
        Tests the upload agent is installed by calling upload agent command with --version.
        Passess stdout to function perform_test which returns False if expected string not present
        This function raises exception if function returns False.
        """    
        if not test_result:
            if not self.debug_mode:
                self.logger("Upload Agent Test Failed", "UA_fail")
                return False
            else:
                return False
        else:
            if not self.debug_mode:
                self.logger("Upload Agent function test passed", "UA_pass")
                # write this to the log file
                self.write_to_uascript_logfile("upload agent check passed\n\n----------------------TEST DX TOOLKIT IS FUNCTIONING----------------------\n")
                return True
            else:
                return True

    def perform_test(self, test_input, test):
        """
        Recieves test name and stdout from execution of command
        Return False if expected response (as per config) not in stdout
        otherwise returns True
        """
        # if expected string not in stdout return Falsetest_upload_agent
        if test == "ua":
            if config.upload_agent_expected_stdout not in test_input:
                return False
        # if expected string not in stdout return False
        if test == "dx_toolkit":
            if config.dx_sdk_test_expected_stdout not in test_input:
                return False
        # For already_uplaoded or demultiplex_started want to return False if the files DO NOT exist
        if test in ["already_uploaded","demultiplex_started",]:
            if not os.path.isfile(test_input):
                return False
        # demultiplex success -return False  if expected string NOT in last line of log file 
        if test == "demultiplex_success":
            if config.demultiplex_success_string not in test_input:
                return False
        return True

    def test_dx_toolkit(self, test_result):
        """
        Tests if the dx toolkit is installed. 
        Calls dx run command and passes stdout to function which will test for expected string (set in config file) is present in output - this will return True if ok.
        Raises exception if test fails.
        """
        if not test_result:
            if not self.debug_mode:
                self.logger("dx toolkit function test failed", "UA_fail")
                return False
            else:
                return False
        else:
            if not self.debug_mode:
                self.logger("dx toolkit function test passed", "UA_pass")
                # write this to the log file
                self.write_to_uascript_logfile("dx toolkit check passed\n\n----------------------UPLOAD FASTQS----------------------\n")
                return True
            else:
                return True

    def already_uploaded(self):
        """
        The upload agent stdout is written to a file which also denotes that the runfolder has been processed.
        This function checks for presense of this file.
        Returns False if not already processed.
        """
        # write to log file including the github repo tag and time stamp
        self.write_to_uascript_logfile("automate_demultiplexing release:" + git_tag.git_tag() + \
            "\n----------------------" + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + \
            "----------------------\nAssessing " + self.runfolder_obj.runfolderpath + \
            "\n\n----------------------HAS THIS FOLDER ALREADY BEEN UPLOADED?----------------------\n")
        
        # use perform_test function to assert if the file exists - will return True if file exists
        if self.perform_test(os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file),"already_uploaded"):
            self.write_to_uascript_logfile("YES - self.upload_started_file present \n----------------------STOP----------------------\n")
            return True
        else:
            # if file doesn't exist return false to continue and write to log file
            self.write_to_uascript_logfile("NO - self.upload_started_file not present so continue\n\n----------------------CHECKING DEMULTIPLEXING COMPLETED SUCCESSFULLY----------------------\n")
            return False
            
    def demultiplex_completed_successfully(self):
        """
        Check if the demultiplexing finished successfully by reading the last line of the demultiplex log
        The demultiplexing script will raise any alerts if issues are found with demultiplexing.
        Uses expected success status defined in config.
        Returns True is completed sucessfully
        """
        demultiplex_file_path =  os.path.join(self.runfolder_obj.runfolderpath, self.demultiplexed)
        # check demultiplexing has actually been done using perform_test - returns true if file present
        if self.perform_test(demultiplex_file_path, "demultiplex_started"):        
            with open(demultiplex_file_path, 'r') as logfile:
                # check if successful demuliplex statement in last line of log
                if self.perform_test(logfile.readlines()[-1],"demultiplex_success"):
                    self.write_to_uascript_logfile("Demultiplex was successfully completed.\ncompiling a list of fastqs....... ")
                    # if successfull call the module which creates a list of fastqs
                    return True
                else:
                    # write to logfile that demultplex was not successful
                    self.write_to_uascript_logfile("!!!!!!!DEMULTIPLEXING DID NOT COMPLETE SUCCESSFULLY.!!!!!!!!!\n----------------------STOP----------------------\n")
                    return False
        else:
            # write to logfile that not yet demultiplexed
            self.write_to_uascript_logfile("demultiplexing has not been performed.\n----------------------STOP----------------------\n")
            return False

    

    def find_fastqs(self, runfolder_fastq_path):
        """
        Loops through all the fastq files in the given folder
        Identifies the pan number and checks for presense in the dictionary of panel settings.
        If there are any files where the pan number was not found sent an alert.
        returns a tuple of list of processed samples, string of fastq filepaths and list of not_processed samples.
        """
        # set up list of fastqs not to be processed
        not_processed = []
        list_of_processed_samples = []
        fastq_string = ""
        # find all fastqs
        for fastq in os.listdir(runfolder_fastq_path):
            # exclude undetermined and any fastqs created by miseq (seerated by "-" rather than "_")
            if fastq.endswith('fastq.gz') and not fastq.startswith('Undetermined') and "-Pan" not in fastq:
                pannumber = ""
                pannumber = "Pan" + fastq.split("_Pan")[1].split("_")[0]  
                if pannumber in config.panel_list:
                    # we know what to do with it:
                    # append to string of paths for upload agent
                    fastq_string = fastq_string + " " + self.runfolder_obj.fastq_folder_path + "/" + fastq
                    # add the fastq name to a list to be used in create_nexus_file_path
                    list_of_processed_samples.append(fastq)
                elif pannumber == "":
                    # haven't identified pan number
                    # TO DO warn or something?
                    pass
                else:
                    not_processed.append(fastq)
        
        if len(not_processed) > 0:
            # add to logger
            
            self.logger("unrecognised panel number found in run " + self.runfolder_obj.runfolder_name, "UA_fail")
            # write to logfile
            self.write_to_uascript_logfile("Some fastq files contained an unrecognised panel number: " + ",".join(not_processed) + "\n")
        
        if len(list_of_processed_samples) == 0:
            self.write_to_uascript_logfile("List of fastqs did not contain any known Pan numbers. Stopping\n")
            # if no fastqs to be processed return none object rather than empty list
            list_of_processed_samples = None
            fastq_string = None
        else:
            self.write_to_uascript_logfile(str(len(list_of_processed_samples)) + " fastqs found.\n\n----------------------PREPARING UPLOAD OF FASTQS----------------------\ndefining path for fastq files.......")
        
        return (list_of_processed_samples, fastq_string, not_processed)

    def capture_any_WES_batch_numbers(self,list_of_processed_samples):
        """
        DNANexus project names are the runfolder suffixed with identifiers to help future dearchival easier.
        This function parses samplenames and identifies any WES batch numbers from the samplenames (identified as anything between "_WES" and "_Pan".
        If found a string is returned, else None is returned
        """
        # a list to hold all the wes numbers
        wes_numbers = []
        
        # for each fastq in the list of fastqs
        for fastq in list_of_processed_samples:
            # if the run has any WES samples
            if "WES" in fastq:
                
                # split on _WES to split the fastq name into two, take the second half of it and split on "_Pan"
                # this will capture 5 or _5 depending if was WES5 or WES_5
                # remove any underscores and suffix to WES to make WES5
                wesbatch = "WES" + fastq.split("_WES")[1].split("_Pan")[0].replace('_', '')
                wes_numbers.append(wesbatch)
        # if no wes numbers are found return None rather than an empty string
        if len(wes_numbers) > 0:
            return "_".join(set(wes_numbers))
        else:
            return None
            
    def capture_library_batch_numbers(self, list_of_processed_samples):
        """
        DNANexus project names are the runfolder suffixed with identifiers to help future dearchival easier.
        This function parses samplenames and identifies the library prep numbers, identified as the first element in the sample name (before the first underscore)
        library batch numbers should always be dentified so this is returned as a string - if not an error is raised
        """
        # a list to hold all the librray batch numbers
        library_batch_numbers = []

        # for each fastq in the list of fastqs
        for fastq in list_of_processed_samples:
            # check there are underscores present
            if "_" in fastq:
                # split on underscores to capture the first element which is the library_batch number eg ONC100 or NGS100
                library_batch_numbers.append(fastq.split("_")[0])
        
        # There should always be  library batch numbers found - raise an error if not
        if len(library_batch_numbers) > 0:
            return "_".join(set(library_batch_numbers))
        else:
            # write to logger to prompt slack alert
            self.logger("unable to identify library batch numbers - are there underscores in the samplenames???" + self.runfolder_obj.runfolder_name, "UA_fail")
            if not self.debug_mode:
                # raise exception to stop script
                raise Exception, "Unable to identify library batch numbers"
            else:
                return False
                
    def build_nexus_project_name(self, wes_number, library_batch):
        """
        The DNA Nexus project name contains all the information required to quickly and easily identify the contents, which may help in the future.
        The project name starts with a code to denote the status of the project (eg live clinical, development or archived) and is followed by the name of the runfolder.
        The WES batches and library prep strings are suffixed onto the project name (received as inputs from other functions)
        A tuple is returned containing strings for self.dest, runfolder_obj.nexus_path and runfolder_obj.nexus_project_name
        Project names (and relevant file paths within the projext are saved to self.runfolderobject), the string for self.
        """
        nexus_path = ""
        nexus_project_name = ""
        # if wes batch numbers add this into the nexus path
        if wes_number:
            # self.nexus path
            nexus_path = self.runfolder_obj.runfolder_name + "_" + library_batch + "_" + wes_number + config.fastq_folder
            # build project name
            nexus_project_name = config.NexusProjectPrefix + self.runfolder_obj.runfolder_name + "_" + library_batch + "_" + wes_number
        else:
            # self.nexus path
            nexus_path = self.runfolder_obj.runfolder_name + "_" + library_batch + config.fastq_folder
            # build project name
            nexus_project_name = config.NexusProjectPrefix + self.runfolder_obj.runfolder_name + "_" + library_batch

        # write to log
        self.write_to_uascript_logfile("fastqs will be uploaded to " + self.runfolder_obj.nexus_path + "\n\n----------------------CREATE AND SHARED DNA NEXUS PROJECT----------------------\n")
        # return tuple of string for self.dest
        return (nexus_project_name + ":/", nexus_path, nexus_project_name)

    def write_create_project_script(self):
        """
        Once the project name has been defined the project can be created.
        This uses the DNANexus sdk, where commands are written to a bash script and executed using subprocess.
        The project is created and shared with users, with varying degrees of access as defined in the config file.
        Successful creation of the project is assertained by assessing the capture of a project id which fits the expected project name pattern (project-132456)
        Any issues identifying the project id will result in an alert being sent.
        The project id is returned as a string

        """
        project_bash_script_path = config.DNA_Nexus_project_creation_logfolder + self.runfolder_obj.runfolder_name + ".sh"

        # open bash script
        with open(project_bash_script_path, 'w') as create_nexus_project_script :
            create_nexus_project_script.write(self.source_command)
            create_nexus_project_script.write(self.createprojectcommand % (config.prod_organisation, self.runfolder_obj.nexus_project_name))

            # Share the project with the nexus usernames in the list in config file
            # first give view permissions
            for user in config.view_users:
                create_nexus_project_script.write("dx invite %s $project_id VIEW --no-email --auth-token %s\n" % (user, config.Nexus_API_Key))
            # then give admin permissions - ensure done in this order incase some users are in both lists.
            for user in config.admin_users:
                create_nexus_project_script.write("dx invite %s $project_id ADMINISTER --no-email --auth-token %s\n" % (user, config.Nexus_API_Key))

            # add a tag to denote live project (as opposed to archived)
            create_nexus_project_script.write(self.addprojecttag + config.live_tag + " --auth-token %s\n" % (config.Nexus_API_Key))

            # echo the project id so it can be captured below
            create_nexus_project_script.write("echo $project_id")
        return project_bash_script_path

    def run_project_creation_script(self,project_bash_script_path):
        """
        Recieves path to previously created script as input
        Calls subprocess command
        Will return projectid (if created) otherwise will return False (debug) or an exception (non-debug)

        For testing the subprocess command will return a debug string of no use to this function.
        Therefore the expected stdout can be passed as an input and used as the output of subprocess command


        """
        # run a command to execute the bash script made above
        cmd = "bash " + project_bash_script_path
        (out,err) = self.execute_subprocess_command(cmd)
        # if debug mode subprocess output is not useful to test this function
        # therefore the input to this function can be the expected subprocess stdout - assign this input to the out variable
        if self.debug_mode:
            out = project_bash_script_path
        
        # if start of project id is in out capture the id and write to logfiles and return
        if "project-" in out:
            # split std_out on "project" and get the last item to capture the project ID
            projectid = "project" + out.split("project")[-1].rstrip()

            # record in log file who project was shared with (VIEW)
            self.write_to_uascript_logfile("DNA Nexus project %s created and shared (VIEW) to " % (self.runfolder_obj.nexus_project_name) + ",".join(config.view_users) +
                "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (projectid))
            
            # record in log file who project was shared with (ADMIN)
            self.write_to_uascript_logfile("DNA Nexus project %s created and shared (ADMIN) to " % (self.runfolder_obj.nexus_project_name) + ",".join(config.admin_users) +
                "\nProjectid=%s \n\n----------------------TEST UPLOAD AGENT----------------------\n" % (projectid))
            # return projectid
            return projectid
        # return false if debug mode otherwise raise an exception.
        else:
            if self.debug_mode:
                return False
            else:
                self.logger("failed to create project in dna nexus " + self.runfolder_obj.nexus_project_name, "UA_fail")
                # raise exception to stop script
                raise Exception, "Unable to create DNA Nexus project"

    def upload_fastqs(self):
        """
        All samples to be processed were identified in find_fastqs(). 
        This function populates a string of local filepaths for all fastqs that is used by the upload agent.
        This command is passed to execute_subprocess_command() and all standard error/standard out written to a log file
        The upload command is written in a way where it is repeated until it exits with an exit status of 0.
        If debug mode the upload agent command is returned without calling execute_subprocess_command()
        """
        # build the nexus upload command
        nexus_upload_command = self.restart_ua_1 + config.upload_agent_path + " --auth-token " + config.Nexus_API_Key + " --project " \
                + self.runfolder_obj.nexus_project_name + "  --folder /" + self.runfolder_obj.nexus_path + " --do-not-compress --upload-threads 10" \
                + self.fastq_string + self.restart_ua_2 % ("fastq files")
        if self.debug_mode:
            return nexus_upload_command
        # open a file to hold all the upload agent commands
        with open(os.path.join(self.runfolder_obj.runfolderpath, config.runfolder_upload_cmds), 'w') as runfolder_upload_cmd_file:
            # write fastq upload commands and a way of distinguishing between upload of fastq and rest of runfolder
            runfolder_upload_cmd_file.write("----------------------Upload of fastqs----------------------\n" + nexus_upload_command \
                + "\n\n----------------------Upload rest of runfolder----------------------\n")

        # write to logfile
        self.write_to_uascript_logfile("Uploading Fastqs to Nexus. See commands at " + os.path.join(self.runfolder_obj.runfolderpath, \
                config.runfolder_upload_cmds) + "\n\n----------------------CHECKING SUCCESSFUL UPLOAD OF FASTQS----------------------\n")
        upload_agent_stdout_path = os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file)
        # open file to show upload has started and to hold upload agent standard out
        with open(upload_agent_stdout_path, 'a') as upload_agent_stdout_log:

            # capture stdout and stderr from execution of command
            (out,err) = self.execute_subprocess_command(nexus_upload_command)

            # write to uplaod agent std out logfile
            upload_agent_stdout_log.write("\n----------------------Uploading fastqs " + str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) \
                    + "-----------------\n" + out + err)
        return upload_agent_stdout_path
    
    def look_for_upload_errors_fastq(self, upload_agent_stdout_path):
        """
        Parse the file containing standard error/standard out from the upload agent.
        The upload agent command is reissued until it exists with a status of 0 which must be taken into account when identifying errors.
        If the expected error message (defined in config file) is present but the string "upload successfully" is still present it is assumed it uploaded successfully on the repeated attempt.
        If the success statement is absent raise an alert but do not stop script from running
        """
        # Open the log file and read to look for the string "ERROR"
        for upload in open(upload_agent_stdout_path).read().split("Uploading file"):
            # if there was an error during the upload...
            if config.ua_error in upload:
                # if it still completed successfully carry on
                if "uploaded successfully" in upload:
                    # debugmode
                    if self.debug_mode:
                        return "disrupted but complete"
                    else:
                        self.write_to_uascript_logfile("There was a disruption to the network when uploading the Fastq files but it completed successfully\n")
                        self.logger("upload of fastq was disrupted but completed for run " + self.runfolder_obj.runfolder_name, "UA_disrupted")
                # other wise write to log
                else:
                    if self.debug_mode:
                        return "fail"
                    else:
                        self.write_to_uascript_logfile("There was a disruption to the network which prevented the rest of the runfolder being uploaded\n")
                        self.logger("upload of fastqs failed for run " + self.runfolder_obj.runfolder_name, "UA_fail")
            # if error status is not present
            else:
                # return 
                if self.debug_mode:
                        return "no error"
                else:
                    # write to log file check was ok
                    self.logger("upload of fastq files complete for run " + self.runfolder_obj.runfolder_name, "UA_pass")

    def nexus_fastq_paths(self, read1):
        """
        Creates some variables used in the dx run commands
        Receive name of read 1 fastq file
        Creates a nexus filepath for read1 and read2
        Uses filename to create a sample name - this is supplied to senteion and BWA 
        Returns a tuple (r1_filepath,r2_filepath,samplename)
        """
        # build full file nexus path including project
        read1_nexus_path = self.runfolder_obj.nexus_project_name + ":" + os.path.join(self.runfolder_obj.nexus_path, read1)
        # create read2 by replacing R1 with R2
        read2_nexus_path = self.runfolder_obj.nexus_project_name + ":" + os.path.join(self.runfolder_obj.nexus_path, read1.replace("_R1_", "_R2_"))
        # samplename is used to assign read groups in BWA or as an input to senteion
        sample_name = read1.split("_R1_")[0]
        return ((read1_nexus_path,read2_nexus_path,sample_name))

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
            bed_dict["sambamba"] = config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["sambamba_bedfile"] + "dataSambamba.bed"
        else:
            bed_dict["sambamba"] = config.app_project + config.bedfile_folder + pannumber + "dataSambamba.bed"
            
        if self.panel_dictionary[pannumber]["hsmetrics_bedfile"]:
            bed_dict["hsmetrics"] = config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["hsmetrics_bedfile"] + "data.bed"
        else:
            bed_dict["hsmetrics"] = config.app_project + config.bedfile_folder + pannumber + "data.bed"
        
        bed_dict["mokaamp_bed_PE_input"] = config.app_project + config.bedfile_folder + pannumber + "_PE.bed"
        bed_dict["mokaamp_variant_calling_bed"] = config.app_project + config.bedfile_folder + pannumber + "_flat.bed"
        if self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]:
            bed_dict["rpkm_bedfile"] = config.app_project + config.bedfile_folder + self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"] + '_RPKM.bed'
        
        return bed_dict

    def start_building_dx_run_cmds(self, list_of_processed_samples):
        """
        loop through the list of fastqs to generate commands used to initiate the pipeline.
        For each sample use the panel dictionary to determine which functions are called.
        Each function builds a dx run command which is added to a list.
        The list of commands is returned
        """

        # Update script log file to say what is being done.
        self.write_to_uascript_logfile("\n\n----------------------RUN WORKFLOW----------------------\n")
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
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number and use this to determine which dx run commands are needed for the sample
                panel = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                print fastq, panel
                # The order in which the modules are called here is important to ensure the order of dx run commands is correct. This can affect which decision support tool data is sent to.
                if self.panel_dictionary[panel]["mokawes"]:
                    commands_list.append(self.create_mokawes_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command(panel))
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.run_sapientia_command(panel))
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["peddy"]:
                        peddy = True
                    if self.panel_dictionary[panel]["joint_variant_calling"]:
                        joint_variant_calling = True


                if self.panel_dictionary[panel]["mokapipe"]:
                    commands_list.append(self.create_mokapipe_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command(panel))
                        commands_list.append(self.add_to_depends_list())
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.run_sapientia_command(panel))
                        commands_list.append(self.add_to_depends_list())

                    if self.panel_dictionary[panel]["RPKM_bedfile_pan_number"]:
                        rpkm_list.append(panel)


                if self.panel_dictionary[panel]["mokaonc"]:
                    mokaonc_list.append(fastq)
                    
                if self.panel_dictionary[panel]["mokaamp"]:
                    commands_list.append(self.create_mokaamp_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list())
                    # if self.panel_dictionary[panel]["iva_upload"]:
                    #     commands_list.append(self.build_iva_mokaamp_input_command())
                    #     commands_list.append(self.add_to_depends_list())
                    # if self.panel_dictionary[panel]["sapientia_upload"]:
                    #     commands_list.append(self.build_sapientia_input_command())
                    #     commands_list.append(self.add_to_depends_list())

        
        # run wide jobs
        if len(mokaonc_list) != 0:
            commands_list.append(self.create_mokaonc_command(mokaonc_list))
        if joint_variant_calling:
            commands_list.append(self.create_joint_variant_calling_command())
            
        if len(rpkm_list) != 0:
            # Create a set of RPKM numbers for one command per panel
            for rpkm in set(rpkm_list):
                commands_list.append(self.create_rpkm_command(rpkm))
        if peddy:
            commands_list.append(self.run_peddy_command())        
        
            
        # multiqc 
        commands_list.append(self.create_multiqc_command())
        commands_list.append(self.create_upload_multiqc_command())
        # smartsheet 
        commands_list.append(self.create_smartsheet_command())


        return commands_list

    def create_mokawes_command(self, fastq, pannumber):
        """
        Takes fastq file and pan number for single sample and builds the mokawes dx run command
        Returns dx run command (string)
        """        
        # call function to build nexus fastq paths - returns tuple for read1 and read2 and samplename
        fastqs = self.nexus_fastq_paths(fastq)

        bedfiles = self.nexus_bedfiles(pannumber)

        # create the MokaWES dx command
        dx_command_list = [self.wes_command , fastqs[2] ,
            config.wes_fastqc1 , fastqs[0] ,
            config.wes_fastqc2 , fastqs[1] , 
            config.wes_sention_samplename , fastqs[2] , 
            config.wes_picard_bedfile , bedfiles["hsmetrics"] , 
            self.dest , self.dest_cmd , self.token]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_mokapipe_command(self, fastq, pannumber):
        """
        Receieves R1 fastq file name and pan number for a single sample

        Returns dx run command for mokapipe (string)
        Valid for workflow GATK v3.10
        """
        # build nexus fastq paths - returns tuple for read1 and read2 and samplename and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # create the dx command
        dx_command = self.mokapipe_command +fastqs[2]\
            + config.mokapipe_fastqc1 + fastqs[0] \
            + config.mokapipe_fastqc2 + fastqs[1] \
            + config.mokapipe_bwa_rg_sample + fastqs[2] \
            + config.mokapipe_sambamba_input + bedfiles["sambamba"] \
            + config.mokapipe_mokapicard_vendorbed_input + bedfiles["hsmetrics"] \
            + config.mokapipe_iva_email_input + self.panel_dictionary[pannumber]["ingenuity_email"] \
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
            dx_command += config.mokaonc_fq_input +  fastqs[0] + config.mokaonc_fq_input + fastqs[1]

        # create the dx command include email address for ingenuity - NB only one panel is supported by MokaONC hense hard coded pan number
        command_out = dx_command + config.mokaonc_ingenuity + self.panel_dictionary["Pan1190"]["ingenuity_email"] + self.dest + self.dest_cmd + "MokaONC_Output" + self.token
        
        return command_out


    # def build_iva_mokapipe_input_command(self):
    #     """
    #     Ingenuity import app is run once at the end of all workflows for all panels with iva_upload = True
    #     The ingenuity inputs are a list of jobid.output name. 
    #     Each workflow has a analysis-id so further steps are required to obtain the required job-id.
    #     A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
    #     This function returns the command for this python program
    #     """
    #     dx_command = "%s $jobid -t iva_mokapipe -p %s)" % (self.decision_support_preperation, self.runfolder_obj.nexus_project_name)
    #     return dx_command

    # def build_iva_mokaamp_input_command(self):
    #     """
    #     Ingenuity import app is run once at the end of all workflows for all panels with iva_upload = True
    #     The ingenuity inputs are a list of jobid.output name. 
    #     Each workflow has a analysis-id so further steps are required to obtain the required job-id.
    #     A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
    #     This function returns the command for this python program
    #     """
    #     dx_command = "%s $jobid -t iva_mokaamp -p %s)" % (self.decision_support_preperation, self.runfolder_obj.nexus_project_name)
    #     return dx_command
        
    def build_iva_input_command(self):
        """
        Ingenuity import app is run once at the end of all workflows for all panels with iva_upload = True
        The ingenuity inputs are a list of jobid.output name. 
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
        This function returns the command for this python program
        """
        dx_command = "%s $jobid -t iva -p %s)" % (self.decision_support_preperation, self.runfolder_obj.nexus_project_name)
        return dx_command

    def build_sapientia_input_command(self):
        """
        Sapientia import app is run once at the end of all workflows for all panels with sapientia_upload = True
        The sapientia inputs are a list of jobid.output name. 
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and decision support tool and prints the required input to command line
        This function returns the command for this python program
        """
        dx_command = "%s $jobid -t sapientia -p %s)" % (self.decision_support_preperation, self.runfolder_obj.nexus_project_name)
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
        dx_command_list = [self.mokaamp_command , fastqs[2], 
                    config.mokaamp_fastq_R1_stage , fastqs[0] , 
                    config.mokaamp_fastq_R2_stage , fastqs[1] , 
                    config.mokaamp_mokapicard_bed_stage , bedfiles["hsmetrics"] , 
                    config.mokaamp_mokapicard_capturetype_stage , self.panel_dictionary[pannumber]["capture_type"] , 
                    config.mokaamp_bamclipper_BEDPE_stage , bedfiles["mokaamp_bed_PE_input"] , 
                    config.mokaamp_chanjo_cov_level_stage , self.panel_dictionary[pannumber]["clinical_coverage_depth"] , 
                    config.mokaamp_sambamba_bed_stage , bedfiles["sambamba"] , 
                    config.mokaamp_vardict_bed_stage , bedfiles["mokaamp_variant_calling_bed"] , 
                    config.mokaamp_varscan_bed_stage , bedfiles["mokaamp_variant_calling_bed"] , 
                    config.mokaamp_lofreq_bed_stage , bedfiles["mokaamp_variant_calling_bed"] , 
                    config.mokaamp_varscan_strandfilter_stage , self.panel_dictionary[pannumber]["mokaamp_varscan_strandfilter"] , 
                    self.dest , self.dest_cmd , self.token
            ]

        # Variables from dx_command_list are read from config file as various atomic types. Convert to string and join to create dx_command.
        dx_command = "".join(map(str, dx_command_list))
        
        # remove the bit that adds the job to the depends on list for the negative control as varscan fails on nearempty/-empty BAM files and this will stop multiqc etc running
        if "NTCcon" in fastqs[0]:
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
        dx_command = self.RPKM_command + config.rpkm_bedfile_input + bedfiles["rpkm_bedfile"] + config.rpkm_project_input + self.runfolder_obj.nexus_project_name \
            + config.rpkm_bamfiles_to_download_input + string_of_pannumbers_to_analyse + self.project + self.projectid + self.depends + self.token.rstrip(")")
        return dx_command
    
    def create_joint_variant_calling_command(self):
        return dx_command

    def run_sapientia_command(self, pannumber):
        """
        The app which imports samples into ingenuity has been removed form the workflow. 
        It is now run as a seperate app, using the jobid.outputname as the input, which ensures the job doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job, and the output is captures into the variable $analysisid
        The dx run command is returned (string)
        """
        dx_command = self.sapientia_upload_command + " $analysisid -isapientia_project=" + self.panel_dictionary[pannumber]["sapientia_project"] + self.dest + self.dest_cmd + self.token
        return dx_command
    
    def run_iva_command(self, pannumber):
        """
        The app which imports samples into ingenuity has been removed form the workflow. 
        It is now run as a seperate app, using the jobid.outputname as the input, which ensures the job doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job, and the output is captures into the variable $analysisid
        The ingenuity email is taken from the panel dictionary using the pan number input to this function.
        The dx run command is returned (string)
        """
        dx_command = self.iva_upload_command + " $analysisid" + config.iva_email_input_name + self.panel_dictionary[pannumber]["ingenuity_email"] + self.project + self.projectid + config.iva_reference_inputname + config.iva_reference_default + self.token
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
        dx_command = self.multiqc_command + config.multiqc_project_input + self.runfolder_obj.nexus_project_name + config.multiqc_coverage_level_input \
            + str(lowest_coverage_level) + self.project + self.projectid + self.depends + self.token
        return dx_command
    
    def create_upload_multiqc_command(self):
        """
        """
        # dx run + config.app_project + config.upload_multiqc_path + -imultiqc_html= + input.html
        dx_command = "".join([
            self.upload_multiqc_command, " -imultiqc_html=$jobid:multiqc_report",
            self.project, self.projectid, self.token
        ])
        return dx_command
    
    def run_peddy_command(self):
        """
        Peddy is run once at the end of a WES run. It takes a project and downloads all the required files.
        This function builds that commands and the dx run command is returned (string)
        """
        # build peddy command - eg command = jobid=$(dx run peddy -iproject_for_peddy = 002_170222_ALEDTEST --project project-F2fpzp80P83xBBJy8F1GB2Zb -y --depends-on $jobid)
        dx_command = self.peddy_command + config.peddy_project_input + self.runfolder_obj.nexus_project_name + self.project + self.projectid.rstrip() + self.depends + self.token
        return dx_command

    def create_smartsheet_command(self):
        """
        Once all workflows have completed smartsheet can be updated to record OPMS.
        This function calls the app which updates smartsheet, returning the dx run command (string)
        """
        dx_command = self.smartsheet_update_command + config.smartsheet_mokapipe_complete + self.runfolder_obj.runfolder_name + self.project + self.projectid + self.depends + self.token.rstrip(")")
        return dx_command
    

    def write_dx_run_cmds(self, command_list):
        """
        Takes a list of commands and writes them to file.
        """
        with open(self.runfolder_obj.runfolder_dx_run_script, 'w') as dxrun_commands:
            dxrun_commands.writelines([ line + "\n" for line in command_list ])

    def run_dx_run_commands(self):
        """
        Executes the bash script
        Writes the job ids to log file
        Reports any standard error
        """
        # run a command to execute the bash script made above
        cmd = "bash " + self.runfolder_obj.runfolder_dx_run_script
        (out,err) = self.execute_subprocess_command(cmd)

        
        # capture standard out (the job ids) to the log file
        self.write_to_uascript_logfile(out)

        # if any standard error
        if err:
            self.logger("Error when starting pipeline for run " + self.runfolder_obj.runfolder_name + " stderror = " + err, "UA_fail")

            # write error message to log file# exact error message is written to log file by logger function
            self.write_to_uascript_logfile("\n\n!!!!!!!!!Uh Oh!!!!!!!!\nstandard error: " + err + "\n\n")
        else:
            # write error message to log file
            self.logger("dx run commands issued without error for run " + self.runfolder_obj.runfolder_name, "UA_pass")

    
    def smartsheet_workflows_commands_sent(self):
        """
        This function updates smartsheet to say that the runfolder has started to be processed
        A payload is created, including a count of samples, timestamp and runfolder
        This is posted using the requests module to a given url
        The response is parsed to check the status was "success" otherwise an error is raised.
        """
        self.write_to_uascript_logfile("\n----------------------UPDATE SMARTSHEET----------------------\n")
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
        payload = '{"cells": [{"columnId": ' + str(config.ss_title) + ', "value": "' + self.runfolder_obj.runfolder_name + '"}, {"columnId": ' + str(config.ss_description) + \
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
                    self.write_to_uascript_logfile("smartsheet updated to say in progress\n")
                    self.logger("run started added to smartsheet", "smartsheet_pass")
                else:
                    self.logger("run started NOT added to smartsheet for run " + self.runfolder_obj.runfolder_name, "smartsheet_fail")
                    self.write_to_uascript_logfile("smartsheet NOT updated at in progress step\n" + str(response))
                    
    def write_opms_queries_mokapipe(self,list_of_processed_samples):
        """
        Samples processed using Mokapipe are recorded in moka using an insert query.
        This function will create an insert query for each sample processed through mokapipe.
        If mokapipe samples are found this function will return a dictionary of sample counts, and a list of queries to be added to global dictionary. 
        If no mokapipe samples are found None object is returned
        """
        queries = []
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokapipe add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokapipe"]:
                    queries.append("insert into NGSCustomRuns(DNAnumber,PipelineVersion) values ('" + str(fastq.split("_")[2]) + "','" + config.mokapipe_pipeline_ID + "')")
        if len(queries)> 0:
            # add workflow to sql dictionary
            return {"count":len(queries),"query":queries}
        else:
            return None

    def write_opms_queries_mokawes(self,list_of_processed_samples):
        """
        Samples processed using MokaWES are recorded in moka using an update query.
        If wes samples found this function will return a dictionary of sample counts, and a query (str) to be added to global dictionary. 
        If no wes samples are found None object is returned
        """
        dnanumbers = []
        # add workflow to sql dictionary
        
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokawes add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokawes"]:
                    dnanumbers.append(str(fastq.split("_")[2]))
        if len(dnanumbers) > 0:
            return {"count":len(dnanumbers), "query":["update NGSTest set PipelineVersion = " + config.mokawes_pipeline_ID + " , StatusID = " \
            + config.mokastatus_dataproc_ID + " where dna in ('" + ("','").join(dnanumbers) + "') and StatusID = " + config.mokastat_nextsq_ID]}
        else:
            return None

    def write_opms_queries_oncology(self,list_of_processed_samples):
        """
        Samples tested using mokaamp or mokaonc are not booked into moka until the analysis stage so queries cannot be used to record pipeline version.
        This is recorded manually when creating the test in Moka
        Therefore an email informing the oncology team which version of the pipeline was applied is sent.
        If present a dictionary is returned with a list of workflows and a message (str). If not a None object is returned
        """
        # list of workflows used in this run
        workflows = []
        # loop through fastqs to see which workflows were used
        for fastq in list_of_processed_samples:
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
            return {"workflows": set(workflows), \
                    "query": self.runfolder_obj.runfolder_name + " being processed using workflow " + ",".join(set(workflows))+ "\n\n" \
                    + config.mokaamp_email_message}
        else:
            return None
        
    def send_opms_queries(self):
        """
        Queries to record the pipeline versions are emailed. 
        Custom panel and WES queries are sent to bioinformatics to action where as cancer workflows are sent to oncology team to action.
        This function sends the emails, using the queries built earlier.
        The oncology and rare disease emails are sent seperately and independantly of each other.
        """
        # send oncology email first
        if self.sql_queries["oncology"]:
            # email the workflow used to the oncology team 
            self.email_subject = "MOKAPIPE ALERT : Started pipeline for " + self.runfolder_obj.runfolder_name
            self.email_message = self.runfolder_obj.runfolder_name + " being processed using workflow " + ",".join(self.sql_queries["oncology"]["workflows"]) \
                                + "\n\n" + self.sql_queries["oncology"]["query"]
            # send email - pass multiple reciepients in a list
            self.send_an_email([config.oncology_you, config.you])

        # determine if need to send rare disease email too.
        workflows = []
        sql_statements = []
        count = 0
        # use the dnanexus workflow path, taking only the workflow name
        if self.sql_queries["mokapipe"]:
            workflows.append(config.mokapipe_path.split("/")[-1])
            sql_statements += self.sql_queries["mokapipe"]["query"]
            count += self.sql_queries["mokapipe"]["count"]
        if self.sql_queries["mokawes"]:
            workflows.append(config.mokawes_path.split("/")[-1])
            sql_statements += self.sql_queries["mokawes"]["query"]
            count += self.sql_queries["mokawes"]["count"]
        
        if len(workflows) > 0 and len(sql_statements) > 0:
            # email this query
            self.email_subject = "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for " + self.runfolder_obj.runfolder_name
            self.email_priority = 1  # high priority
            self.email_message = self.runfolder_obj.runfolder_name + " being processed using workflow " + ",".join(set(workflows)) + \
            "\n\nPlease update Moka using the below query and ensure that " + str(count) + " records are updated:\n\n" + "\n".join(sql_statements)
            # send email
            self.send_an_email(config.you)

    def upload_rest_of_runfolder(self):
        """
        The rest of the runfolder requires backing up, excluding bcl files.
        A python script which is a wrapper for the upload agent is used.
        """
        # write status update to log file
        self.write_to_uascript_logfile("\n----------------------UPLOAD REST OF RUNFOLDER----------------------\n")
        
        # create the samplesheet name to copy
        samplesheet_name = self.runfolder_obj.runfolder_name + "_SampleSheet.csv"

        # copy samplesheet into project
        copyfile(config.samplesheets + samplesheet_name, os.path.join(self.runfolder_obj.runfolderpath, samplesheet_name))

        cmd = "python3 " + config.backup_runfolder_script + " -i " + self.runfolder_obj.runfolderpath + " -p " + self.runfolder_obj.nexus_project_name + " --ignore /L00,DNANexus_upload_started,add_runfolder_to_nexus_cmds --logpath " + config.backup_runfolder_logfile + " -a " + config.Nexus_API_Key

        # write to the log file that samplesheet was copied and runfolder is being uploaded, linking to log files for cmds and stdout
        self.write_to_uascript_logfile("Copied samplesheet to runfolder\nUploading rest of run folder to Nexus using backup_runfolder.py:\n " + cmd \
                + "\nsee standard out from these commands in log file @ " + os.path.join(config.backup_runfolder_logfile, self.runfolder_obj.runfolder_name) + "\n\n----------------CHECKING SUCCESSFUL UPLOAD OF RUNFOLDER----------------\n")
        
        # run the command
        out, err = self.execute_subprocess_command(cmd)
        backup_logfile = config.backup_runfolder_logfile + '/' + self.runfolder_obj.runfolder_name + '.log'
        return backup_logfile

    def list_log_files(self):
        """
        log files include:
        1. the log file for this script containing all commands used (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_log)
        2. demultiplexing log file (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_log_files)
        3. nexus project creation logs (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Nexus_project_creation_logs)
        4. runfolder_upload_commands (in the run folder)
        5. runfolder_upload_stdout (in the run folder)
        6. logfile used to set off the workflow (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs)
        """
        ua_log = self.upload_agent_logfile_path # Script logfile containing all commands used
        nexus_create_log = config.DNA_Nexus_project_creation_logfolder + self.runfolder_obj.runfolder_name + '.sh' # Nexus project creation log
        runfolder_upload_log =   os.path.join(self.runfolder_obj.runfolderpath, config.runfolder_upload_cmds) # Runfolder upload commands
        runfolder_upload_start_log =  os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file) # Runfolder upload stdout
        workflow_command_log =  self.runfolder_obj.runfolder_dx_run_script # File used to set off dx run commands
        demultiplex_logfiles = [ os.path.join(config.demultiplex_logfiles, filename) for filename in os.listdir(config.demultiplex_logfiles) if self.runfolder_obj.runfolder_name in filename ]
        logfiles = [ua_log, nexus_create_log, runfolder_upload_log, runfolder_upload_start_log, workflow_command_log] + demultiplex_logfiles
        return logfiles

    def upload_log_files(self):
        nexus_upload_folder = "/" + self.runfolder_obj.nexus_project_name.replace(self.nexusproject, "") + "/Logfiles/"
        command_list = [
            config.upload_agent_path, "--auth-token", config.Nexus_API_Key, "--project",
            self.runfolder_obj.nexus_project_name, "--folder", nexus_upload_folder, "--do-not-compress", "--upload-threads", "10"
            ] + self.list_log_files()

        cmd = subprocess.list2cmdline(command_list)

        # write these commands to the runfolder_upload_cmds_logfile before upload.
        runfolder_upload_cmd_file = open(os.path.join(self.runfolder_obj.runfolderpath, config.runfolder_upload_cmds), 'a')
        runfolder_upload_cmd_file.write("\n----------------------Upload log files----------------------\n")
        runfolder_upload_cmd_file.write(cmd+ "\n")
        runfolder_upload_cmd_file.close()

        # Write to logfiles
        out, err = self.execute_subprocess_command(cmd)

        # capture stdout to log file containing stdour and stderr
        runfolder_upload_stdout_file = open(os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file), 'a')
        runfolder_upload_stdout_file.write("\n----------------------Uploading logfiles (this will not be included in the file within DNA Nexus) " +
            str('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())) + "-----------------\n")
        runfolder_upload_stdout_file.write(out)
        runfolder_upload_stdout_file.write(err)
        runfolder_upload_stdout_file.close()

        return os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file)


    def look_for_upload_errors(self, logfile, success=None):
        successful_upload = False
        upload_error = False

        for upload in open(logfile ,'r').read().split("Uploading file"):
            # if there was an error during the upload...
            if config.ua_error in upload:
                # if error seen set flag
                upload_error = True
                # if it still completed successfully carry on
                if "uploaded successfully" in upload:
                    self.write_to_uascript_logfile("There was a disruption to the network when uploading the rest of the runfolder but it completed successfully\n")
                    self.logger("upload of runfolder was disrupted but completed for run " + self.runfolder_obj.runfolder_name, "UA_disrupted")
                # other wise send an email and write to log
                else:
                    self.write_to_uascript_logfile("There was a disruption to the network which prevented the rest of the runfolder being uploaded\n")
                    self.logger("upload of runfolder failed for run " + self.runfolder_obj.runfolder_name, "UA_fail")
            # Check upload success if success string passed
            if success and (success in upload):
                successful_upload = True

        # Write an error if a success string was passed but not found
        if success and not successful_upload:
            self.write_to_uascript_logfile("Backup script did not complete successfully\n")
            self.logger("backup of runfolder incomplete for run " + self.runfolder, "UA_fail")
        # only state no errors seen if no errors were seen!
        elif not upload_error:
            # write to log file check was ok
            self.write_to_uascript_logfile("There were no issues when backing up the run folder\n")
            self.logger("backup of runfolder complete for run " + self.runfolder_obj.runfolder_name, "UA_pass")
    
    def execute_subprocess_command(self,command):
        """
        Takes a command, executes using subprocess and returns tuple of (stdout,stderr)
        """
        if not self.debug_mode:
            proc = subprocess.Popen([command], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, executable="/bin/bash")

            # capture the streams
            return proc.communicate()
        else:
            return (" ".join([config.upload_agent_expected_stdout,config.dx_sdk_test_expected_stdout, config.demultiplex_success_string]),"err")


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
        self.write_to_uascript_logfile("\nEmail sent to...... " + str(to) + "\nsubject:" + self.email_subject + "\nbody:" + self.email_message + "\n\n")
        self.logger("Upload Agent email sent" + str(to) + ". Subject:" + self.email_subject + ". Body:" + self.email_message, "UA_pass")
    
    def write_to_uascript_logfile(self,message):
        """
        Write message to logfile - open file in append mode each time
        """
        if not self.debug_mode:
            with open(self.upload_agent_logfile_path,'a+') as logfile:
                logfile.write(message)
    

    def logger(self, message, tool):
        """Write log messages to the system log.
        Arguments:
        message (str)
            Details about the logged event.
        tool (str)
            Tool name. Used to search within the insight ops website.
        """
        if not self.debug_mode:
            # Create subprocess command string, passing message and tool name to the command
            log = "/usr/bin/logger -t %s '%s'" % (tool, message)

            if subprocess.call([log], shell=True) == 0:
                # If the log command produced no errors, record the log command string to the script logfile.
                self.write_to_uascript_logfile("Log written to /usr/bin/logger\n" + log + "\n")
            # Else record failure to write to system log to the script log file
            else:
                self.write_to_uascript_logfile("Failed to write log to /usr/bin/logger\n" + log + "\n")


if __name__ == '__main__':
    # Create instance of get_list_of_runs
    runs = get_list_of_runs()
    # call function
    runs.loop_through_runs()
