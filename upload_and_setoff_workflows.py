#!/usr/bin/python2
"""upload_and_setoff_workflows.py

Upload NGS data to DNANexus and trigger analysis workflows.
"""
import datetime
import os
import re
import smtplib
import subprocess
from email.message import Message
from shutil import copyfile

import automate_demultiplex_config as config
import git_tag
import requests
import adlogger #import ADLoggers, get_runfolder_log_config


class SequencingRuns(list):
    """A container for NGS runfolders with methods to initiate runfolder processing.
    
    Args:
        None
    Methods:
        set_runfolders(): Update list to contain NGS runfolders on the system
        loop_through_runs(): Process all NGS runfolders in class instance list
    """

    def __init__(self):
        # Enable this class to hold sequencing runs by inheriting from python's List object.
        super(SequencingRuns, self).__init__()
        # Timestamp for each instance is used to name logfiles.
        self.now = str("{:%Y%m%d_%H%M%S}".format(datetime.datetime.now()))

    def set_runfolders(self):
        """
        Update internal list with NGS runfolders present on the system. The root directory to
        search for runfolders is specified in the config object.

        >>> runs = SequencingRuns()
        >>> # runs == []
        >>> runs.set_runfolders()
        >>> # runs == ['runfolder1', 'runfolder2', 'runfolder3']
        Returns = None
        """
        all_runfolders = os.listdir(config.runfolders)
        for folder in all_runfolders:
            folder_exists = os.path.isdir(os.path.join(config.runfolders, folder))
            if folder not in config.ignore_directories and folder_exists:
                self.append(folder)

    def loop_through_runs(self):
        """
        Input = None
        Process all NGS runfolders in class instance list.
        Returns = None
        """

        # Track processed runfolders to use later for naming logfiles.
        processed_runfolders = []

        # Process any runfolders added to class instance with self.set_runfolders()
        for folder in self:
            runfolder_instance = RunfolderProcessor(folder, self.now, debug_mode=config.debug)
            # Append processed runfolders to tracking list
            if runfolder_instance.quarterback():
                processed_runfolders.append(folder)
            # close down the run folder specific logger handles
            runfolder_instance.loggers.shutdown_logs()
            

        # Add names of any processed runfolders to logfile
        if processed_runfolders:
            original_logfile_path = config.upload_and_setoff_workflow_logfile + self.now + "_upload_and_setoff_workflow.log"
            new_logfile = original_logfile_path.replace(self.now, self.now + "_".join(processed_runfolders)) 
            os.rename(original_logfile_path, new_logfile)

#TODO: Comments and docstrings from Line 70 onwards
class RunfolderObject(object):
    """
    An object with runfolder specific properties.
    """

    def __init__(self, runfolder):
        # set empty variables to be defined based on the run
        self.runfolder_name = runfolder
        # create full path to runfolder
        self.runfolderpath = os.path.join(config.runfolders, runfolder)
        # folder containing the fastqs for this project
        self.fastq_folder_path = self.runfolderpath + config.fastq_folder
        # path to the run folder's dx run commands
        self.runfolder_dx_run_script = (
            config.DNA_Nexus_workflow_logfolder + self.runfolder_name + "_dx_run_commands.sh"
        )
        self.sapientia_upload_command_script = (
            config.DNA_Nexus_workflow_logfolder + self.runfolder_name + "_sapientia_upload_commands.sh"
        )
        self.nexus_project_name = ""
        self.nexus_path = ""
        self.nexus_project_id = ""


class RunfolderProcessor(object):
    """
    This class assesses a runfolder to check if it required processing. If the runfolder meets the
    criteria to be processed.
    Fastqs are uploaded to DNA Nexus, dx run commands built and executed and then the rest of the
    runfolder is also uploaded.
    All actions are logged in the logfile created when the script is run.
    A new instance of this class is initiated for each runfolder being assessed.
    """

    def __init__(self, runfolder, now, debug_mode=False):
        # capture class inputs
        self.debug_mode = debug_mode
        self.runfolder_obj = RunfolderObject(runfolder)
        self.now = now
        
        # define logfile path for this execution of this script.
        self.upload_agent_logfile_path = config.upload_and_setoff_workflow_logfile + self.now + "_.txt"

        # string of fastqs for upload agent
        self.fastq_string = ""

        # list of fastqs to get ngs run number and WES batch
        self.list_of_processed_samples = []

        # DNA Nexus commands to be built on later
        self.source_command = (
            "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\ndepends_list=''"
        )
        self.createprojectcommand = (
            'project_id="$(dx new project --bill-to %s "%s" --brief --auth-token '
            + config.Nexus_API_Key
            + ')"\n'
        )

        self.mokapipe_command = (
            "jobid=$(dx run " + config.app_project + config.mokapipe_path + " -y --name "
        )
        self.wes_command = (
            "jobid=$(dx run " + config.app_project + config.mokawes_path + " -y --name "
        )
        self.peddy_command = "jobid=$(dx run " + config.app_project + config.peddy_path
        self.multiqc_command = "jobid=$(dx run " + config.app_project + config.multiqc_path
        self.upload_multiqc_command = (
            "jobid=$(dx run " + config.app_project + config.upload_multiqc_path + " -y "
        )
        self.smartsheet_update_command = "dx run " + config.app_project + config.smartsheet_path
        self.RPKM_command = "dx run " + config.app_project + config.RPKM_path
        self.mokaonc_command = "jobid=$(dx run " + config.app_project + config.mokaonc_path + " -y "
        self.mokaamp_command = (
            "jobid=$(dx run " + config.app_project + config.mokaamp_path + " -y --name "
        )
        self.decision_support_preperation = "analysisid=$(python %s -a " % (
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                config.decision_support_tool_input_script,
            )
        )
        self.sapientia_upload_command = (
            "echo 'dx run " + config.app_project + config.sapientia_app_path + " -y "
        )
        # create filepath for file to hold sapientia command(s)
        self.sapientia_upload_command_script_path = (
            config.DNA_Nexus_workflow_logfolder + self.runfolder_obj.runfolder_name + "_sapientia.sh"
        )
        # string to redirect command (with variables) into file
        self.sapientia_upload_command_redirect = "' >> " + self.sapientia_upload_command_script_path

        self.iva_upload_command = "jobid=$(dx run " + config.iva_app_path + " -y "
        # project to upload run folder into
        self.nexusproject = config.NexusProjectPrefix
        self.project_bash_script_path = (
            config.DNA_Nexus_project_creation_logfolder + self.runfolder_obj.runfolder_name + ".sh"
        )

        self.dest = " --dest="
        self.dest_cmd = ""
        self.project = " --project="
        self.token = " --brief --auth-token " + config.Nexus_API_Key + ")"
        self.depends = " -y $depends_list"

        # argument to capture jobids
        self.depends_list = 'depends_list="${depends_list} -d ${jobid} "'

        # command to restart upload agent part 1
        self.restart_ua_1 = "ua_status=1; while [ $ua_status -ne 0 ]; do "
        self.restart_ua_2 = (
            "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo "
            '"temporary issue when uploading file %s"; fi ; done'
        )

        # smartsheet API
        # newly inserted row
        self.rowid = ""

        # time stamp
        self.smartsheet_now = str("{:%Y-%m-%d}".format(datetime.datetime.utcnow()))

        # requests info
        self.headers = {
            "Authorization": "Bearer " + config.smartsheet_api_key,
            "Content-Type": "application/json",
        }
        self.smartsheet_url = "https://api.smartsheet.com/2.0/sheets/" + str(
            config.smartsheet_sheetid
        )

        self.panel_dictionary = self.set_panel_dictionary()
        self.sql_queries = {}

        # call the function which populates a dictionary of run specific logs and logfile paths.
        self.log_config = adlogger.get_runfolder_log_config(self.runfolder_obj, self.now)
        # pass the dictionary created above into ADloggers class - ** unpacks this dictionary  
        # to populate inputs. This is used as an object where various logs can be written 
        self.loggers = adlogger.ADLoggers(**self.log_config)
        

    def run_tests(self):
        """
        Inputs = None
        Test the performance of the required software (upload agent and dx toolkit)
        Calls the perform_test function and passes the output of this to functions which assess the
        performance of the software
        Raises exception if any test does not pass
        Returns = None
        """
        self.loggers.script.info("automate_demultiplexing release:{}".format(git_tag.git_tag()))
        # Call upload agent,using perform test function. Pass output of this to self.test_upload_agent
        if not self.test_upload_agent( 
            self.perform_test(
                self.execute_subprocess_command(
                    config.upload_agent_path + config.upload_agent_test_command
                )[0],
                "ua",
            )
        ):
            raise Exception, "Upload agent not installed"

        # test dx toolkit installation
        if not self.test_dx_toolkit(
            self.perform_test(self.execute_subprocess_command(config.dx_sdk_test)[0], "dx_toolkit")
        ):
            raise Exception, "dx toolkit not installed"

    def quarterback(self):
        """
        Input = None
        This method calls other methods in order
        Returns = True if runfolder processed
        """
        self.run_tests()
        # build dictionary of panel settings
        self.panel_dictionary = self.set_panel_dictionary()

        # check if already uploaded and demultiplexing finished sucessfully
        if not self.already_uploaded() and self.has_demultiplexed():
            # calculate cluster density
            self.calculate_cluster_density()
            self.list_of_processed_samples, self.fastq_string = self.find_fastqs(
                self.runfolder_obj.fastq_folder_path
            )
            if self.list_of_processed_samples:
                # build the project name using the WES batch and NGS run numbers
                (
                    self.dest_cmd,
                    self.runfolder_obj.nexus_path,
                    self.runfolder_obj.nexus_project_name,
                ) = self.build_nexus_project_name(
                    self.capture_any_WES_batch_numbers(self.list_of_processed_samples),
                    self.capture_library_batch_numbers(self.list_of_processed_samples),
                )
                # create bash script to create and share nexus project -return filepath
                # pass filepath into module which runs project creation script - capturing projectid
                self.write_create_project_script()
                self.runfolder_obj.nexus_project_id = self.run_project_creation_script().rstrip()
                # build upload agent command for fastq upload and write stdout to ua_stdout_log
                # pass path to function which checks files were uploaded without error
                self.look_for_upload_errors(self.upload_fastqs())
                
                # upload cluster density files and check upload was successful.
                self.look_for_upload_errors(self.upload_cluster_density())

                self.write_dx_run_cmds(
                    self.start_building_dx_run_cmds(self.list_of_processed_samples)
                )
                self.run_dx_run_commands()
                self.smartsheet_workflows_commands_sent()
                self.sql_queries["mokawes"] = self.write_opms_queries_mokawes(
                    self.list_of_processed_samples
                )
                self.sql_queries["oncology"] = self.write_opms_queries_oncology(
                    self.list_of_processed_samples
                )
                self.sql_queries["mokapipe"] = self.write_opms_queries_mokapipe(
                    self.list_of_processed_samples
                )
                self.send_opms_queries()
                self.look_for_upload_errors_backup_runfolder(self.upload_rest_of_runfolder())
                self.look_for_upload_errors(self.upload_log_files())
                # return true to denote that a runfolder was processed
                return True
        else:
            self.loggers.script.info(
                'Runfolder has already been processed: {}. Skipping.'.format(
                    self.runfolder_obj.runfolder_name
                )
            )
            return False

    @staticmethod
    def set_panel_dictionary():
        """
        Input = None
        Populate the dictionary detailing panel specific settings.
        Default settings are set in the config file and then updated as and when required for each
        panel the defaults in config file.
        Loop through panel specific properties in config file and overwrite any default with panel
        specific settings
        Returns = dictionary of panel specific settings
        """
        dictionary_to_return = {}
        # for each panel
        for panel in config.panel_list:
            # loop through default settings, adding to dictionary and  then loop through panel
            # settings from config, overwriting any defaults
            dictionary_to_return[panel] = {}
            for setting in config.default_panel_properties:
                dictionary_to_return[panel][setting] = config.default_panel_properties[setting]
            for setting in config.panel_settings[panel]:
                dictionary_to_return[panel][setting] = config.panel_settings[panel][setting]
        return dictionary_to_return

    def test_upload_agent(self, test_result):
        """
        Input = boolean value (True/False)
        This function receives the value from the function which assesses the output of calling the 
        upload agent with --version. If not debug mode the result is logged.
        Returns = boolean value
        """
        if not test_result:
            if not self.debug_mode:
                self.loggers.script.error("UA_fail 'Upload Agent Test Failed'")
                return False
            else:
                return False
        else:
            if not self.debug_mode:
                self.loggers.script.info("UA_pass 'Upload Agent function test passed'")
                return True
            else:
                return True

    def perform_test(self, test_input, test):
        """
        Input = test_input (string) and test_name (str)
        Recieves test name and stdout from execution of command which is performing a test
        Assesses output of test against expected response (as per config)
        Returns =  Boolean (True/False)
        """
        # if expected string not in stdout return Falsetest_upload_agent
        if test == "ua":
            if config.upload_agent_expected_stdout not in test_input:
                return False
        # if expected string not in stdout return False
        if test == "dx_toolkit":
            if config.dx_sdk_test_expected_stdout not in test_input:
                return False
        # False if the demultiplex started file does not exist
        if test == "demultiplex_started":
            if not os.path.isfile(test_input):
                return False
        # False if the upload file does not exist or does not contain data
        if test == "already_uploaded":
            if not os.path.isfile(test_input):
                return False
        # demultiplex success -return False  if expected string NOT in last line of log file
        if test == "demultiplex_success":
            if not re.search(config.demultiplex_success_match, test_input):
                return False
        if test == "cluster_density":
            if config.cluster_density_success_statement not in test_input
                return False
        return True

    def test_dx_toolkit(self, test_result):
        """
        Input = Boolean
        This function receives a True/False value from the function which assesses the output of the
        dx toolkit test command
        If not debug mode the result is logged.
        Returns = boolean value
        """
        if not test_result:
            if not self.debug_mode:
                self.loggers.script.error("UA_fail 'dx toolkit function test failed'")
                return False
            else:
                return False
        else:
            if not self.debug_mode:
                self.loggers.script.info("UA_pass 'dx toolkit function test passed'")
                return True
            else:
                return True

    def already_uploaded(self):
        """
        Input = None
        Upload agent stdout is written to a file, indicating that the runfolder has been processed.
        This function checks for presense of this file (using perform_test function).
        Returns = Boolean (True/False)
        """
        # write to log file including the github repo tag and time stamp
        self.loggers.script.info("Working on {}".format(self.runfolder_obj.runfolderpath))

        # use perform_test function to assert if the file exists - will return True if file exists
        if self.perform_test(
            os.path.join(self.runfolder_obj.runfolderpath, config.upload_started_file),
            "already_uploaded",
        ):
            self.loggers.script.info("Upload started file present. Terminating.")
            return True
        else:
            # if file doesn't exist return false to continue and write to log file
            self.loggers.script.info("Upload started file not found. Continuing.")
            return False

    def has_demultiplexed(self):
        """
        Input = None
        Check if demultiplexing has been performed and completed sucessfully.
        The demultiplexing script will raise any alerts if issues are found with demultiplexing, but
         we also need to prevent further processing of the run.
        Passes the expected demultiplex log file path to perform_test function
        If present, passes the last line of the log file to perform_test for a success check. 
        Returns = Boolean (True/False)
        """
        demultiplex_file_path = os.path.join(
            self.runfolder_obj.runfolderpath,
            config.file_demultiplexing
        )
        # check demultiplexing has been done using perform_test - returns true if file present
        if self.perform_test(demultiplex_file_path, "demultiplex_started"):
            with open(demultiplex_file_path, "r") as logfile:
                # check if successful demuliplex statement in last line of log
                if self.perform_test(logfile.readlines()[-1], "demultiplex_success"):
                    self.loggers.script.info("Demultiplex completed succesfully.")
                    return True
                else:
                    # write to logfile that demultplex was not successful
                    self.loggers.script.info("Demultiplex failed.")
                    return False
        else:
            # write to logfile that not yet demultiplexed
            self.loggers.script.info("Demultiplex has not been performed.")
            return False

    def calculate_cluster_density(self,runfolder_path, runfolder_name):
        """
        Inputs = runfolder name and runfolder path
        Uses a dockerised version of GATK to run picard CollectIlluminaLaneMetrics
        This calculates cluster density and saves files (runfolder.illumina_phasing_metrics and runfolder.illumina_lane_metrics) to the runfolder
        If success statement seen in stderr record in log file else raise slack alert but do not stop run.
        Returns = None
        """
        # docker command for tool
        cmd = "sudo docker run -v {}:/input_run \
        broadinstitute/gatk:4.1.8.1 \
        ./gatk CollectIlluminaLaneMetrics \
        --RUN_DIRECTORY /input_run \
        --OUTPUT_DIRECTORY /input_run \
        --OUTPUT_PREFIX {}".format(runfolder_path,runfolder_name)
        # capture stdout and stderr
        # NB all output from picard tool is in stderr
        (out, err) = self.execute_subprocess_command(cmd)
        # assess stderr , looking for expected success statement
        if self.perform_test(err,"cluster_density")
            self.loggers.script.info("Cluster density calculation saved to {}".format(runfolder_name+config.cluster_density_file_suffix))
        # raise slack alert if success statement not present.
        else:
            self.loggers.script.error("UA_fail 'Cluster density calculation failed for : {}'".format(self.runfolder_obj.runfolder_name))
            


    def find_fastqs(self, runfolder_fastq_path):
        """
        Input = path to fastqs in runfolder
        Loops through all the fastq files in the given folder
        Identifies the pan number and checks for presense of this pan number in the dictionary of
        panel settings. If there are any files where the pan number was not found sent an alert.
        Returns = a tuple of list of processed samples and string of fastq filepaths.
        """
        # set up list of fastqs not to be processed
        not_processed = []
        list_of_processed_samples = []
        fastq_string = ""
        # find all fastqs
        for fastq in os.listdir(runfolder_fastq_path):
            # exclude undetermined and any fastqs created by miseq (seerated by "-" rather than "_")
            if (
                fastq.endswith("fastq.gz")
                and not fastq.startswith("Undetermined")
                and "-Pan" not in fastq
            ):
                pan_match = re.search(r'Pan\d+', fastq)
                if pan_match and (pan_match.group()) in config.panel_list:
                    # we know what to do with it:
                    # append to string of paths for upload agent
                    fastq_string = (
                        fastq_string + " " + self.runfolder_obj.fastq_folder_path + "/" + fastq
                    )
                    # add the fastq name to a list to be used in create_nexus_file_path
                    list_of_processed_samples.append(fastq)
                else:
                    # self.loggers.script.warning(
                    #     'UA_warning unable to find PanNumber in {}.'.format(fastq)
                    # )
                    not_processed.append(fastq)

        if not_processed:
            # self.loggers.script.error(
            #     "UA_fail 'Unrecognised panel number found in run {}.'".format(
            #         self.runfolder_obj.runfolder_name
            #     )
            # )
            self.loggers.script.error(
                "UA_fail '{} contained an unrecognised pan numbers: {}'".format(
                    self.runfolder_obj.runfolder_name, ",".join(not_processed)
                )
            )

        if not list_of_processed_samples:
            self.loggers.script.error("UA_fail 'No known Pan numbers in fastq list'")
            # if no fastqs to be processed return none object rather than empty list
            list_of_processed_samples = None
            fastq_string = None
        else:
            self.loggers.script.info("{} fastqs found".format(str(len(list_of_processed_samples))))

        return (list_of_processed_samples, fastq_string)

    def capture_any_WES_batch_numbers(self, list_of_processed_samples):
        """
        Input = list of samples to be processed
        DNANexus projects are named after the runfolder suffixed with identifiers.
        This function parses samplenames and identifies any WES batch numbers from the samplenames
        (identified as anything between "_WES" and "_Pan").
        If WES batch number(s) are identified, Returns a string to be included in the project name
        If no batch numbers returns None
        Returns = string or None
        """
        # a list to hold all the wes numbers
        wes_numbers = []

        # for each fastq in the list of fastqs
        for fastq in list_of_processed_samples:
            # if the run has any WES samples
            if "WES" in fastq:
                # split on _WES to split the fastq name into two,
                # take the second half of it and split on "_Pan"
                # this will capture 5 or _5 depending if was WES5 or WES_5
                # remove any underscores and suffix to WES to make WES5
                wesbatch = "WES" + fastq.split("_WES")[1].split("_Pan")[0].replace("_", "")
                wes_numbers.append(wesbatch)
        # if no wes numbers are found return None rather than an empty string
        if wes_numbers:
            return "_".join(set(wes_numbers))
        else:
            return None

    def capture_library_batch_numbers(self, list_of_processed_samples):
        """
        Input = list of samples to be processed
        DNANexus project names are the runfolder suffixed with identifiers to help future dearchival
        This function parses samplenames and identifies the library prep numbers, identified as the
        first element in the sample name (before the first underscore)
        If no library batch numbers found raise error.
        Returns = unique library batch numbers (str)
        """
        # a list to hold all the librray batch numbers
        library_batch_numbers = []

        # for each fastq in the list of fastqs
        for fastq in list_of_processed_samples:
            # check there are underscores present
            if "_" in fastq:
                # split on underscores to capture the the library_batch number
                # eg ONC100 or NGS100
                library_batch_numbers.append(fastq.split("_")[0])

        # There should always be  library batch numbers found - raise an error if not
        if library_batch_numbers:
            return "_".join(set(library_batch_numbers))
        else:
            # Prompt a slack alert
            self.loggers.script.error(
                (
                    "UA_fail '{} - Unable to identify library batch numbers. "
                    "Check for underscores in the samplenames."
                ).format(self.runfolder_obj.runfolder_name)
            )
            if not self.debug_mode:
                # raise exception to stop script
                raise Exception, "Unable to identify library batch numbers"
            else:
                return False

    def build_nexus_project_name(self, wes_number, library_batch):
        """
        Input - WES number and library batch numbers
        The DNA Nexus project name contains all the information required to quickly and easily
        identify the contents, which may help in the future.
        The project name starts with a code to denote the status of the project (eg live clinical,
        development or archived) and is followed by the name of the runfolder.
        The WES batches and library prep strings are suffixed onto the project name (received as
        inputs from other functions).
        Returns = tuple containing strings for self.dest, runfolder_obj.nexus_path and
            runfolder_obj.nexus_project_name
        """
        nexus_path = ""
        nexus_project_name = ""
        # if wes batch numbers add this into the nexus path
        if wes_number:
            # self.nexus path
            nexus_path = (
                self.runfolder_obj.runfolder_name
                + "_"
                + library_batch
                + "_"
                + wes_number
                + config.fastq_folder
            )
            # build project name
            nexus_project_name = (
                config.NexusProjectPrefix
                + self.runfolder_obj.runfolder_name
                + "_"
                + library_batch
                + "_"
                + wes_number
            )
        else:
            # self.nexus path
            nexus_path = (
                self.runfolder_obj.runfolder_name + "_" + library_batch + config.fastq_folder
            )
            # build project name
            nexus_project_name = (
                config.NexusProjectPrefix + self.runfolder_obj.runfolder_name + "_" + library_batch
            )

        # return tuple of string for self.dest
        return (nexus_project_name + ":/", nexus_path, nexus_project_name)

    def write_create_project_script(self):
        """
        Input = None
        Once the project name has been defined the project can be created using the DNANexus sdk
        Commands are written to a bash script and executed using subprocess. The project is created
        and shared with users, with varying degrees of access as defined in the config file.
        This function writes a bash script containing the project creation command
        Return = None
        """

        # open bash script
        with open(self.project_bash_script_path, "w") as project_script:
            project_script.write(self.source_command + "\n")
            project_script.write(
                self.createprojectcommand
                % (config.prod_organisation, self.runfolder_obj.nexus_project_name)
            )

            # Share the project with the nexus usernames in the list in config file
            # first give view permissions
            for user in config.view_users:
                project_script.write(
                    "dx invite %s $project_id VIEW --no-email --auth-token %s\n"
                    % (user, config.Nexus_API_Key)
                )
            # then give admin permissions - required incase some users are in both lists.
            for user in config.admin_users:
                project_script.write(
                    "dx invite %s $project_id ADMINISTER --no-email --auth-token %s\n"
                    % (user, config.Nexus_API_Key)
                )


            # echo the project id so it can be captured below
            project_script.write("echo $project_id")

    def run_project_creation_script(self):
        """
        Inputs = None
        Calls subprocess command executing project creation bash script.
        Output of this command is tested to see if it meets the expected pattern.
        Returns - projectid (if created) , False (if debug) or an exception (non-debug)
        """
        # run a command to execute the bash script made above
        cmd = "bash " + self.project_bash_script_path
        (out, _) = self.execute_subprocess_command(cmd)
        # if debug mode subprocess output is not useful to test this function
        # therefore the input to this function can be the expected subprocess stdout
        # assign this input to the out variable
        if self.debug_mode:
            out = self.project_bash_script_path

        # if start of project id is in out capture the id and write to logfiles and return
        if "project-" in out:
            # split std_out on "project" and get the last item to capture the project ID
            projectid = "project" + out.split("project")[-1].rstrip()

            string_viewuser_list = ",".join(config.view_users)
            # record in log file who project was shared with (VIEW)
            self.loggers.script.info(
                "DNA Nexus project {} created and shared (VIEW) to {}".format(
                    self.runfolder_obj.nexus_project_name, string_viewuser_list
                )
            )

            # record in log file who project was shared with (ADMIN)
            string_adminuser_list = ",".join(config.admin_users)
            self.loggers.script.info(
                "DNA Nexus project {} created and shared (ADMIN) to {}".format(
                    self.runfolder_obj.nexus_project_name, string_adminuser_list
                )
            )

            self.loggers.script.info("Projectid={}".format(projectid))
            # return projectid
            return projectid
        # return false if debug mode otherwise raise an exception.
        else:
            if self.debug_mode:
                return False
            else:
                self.loggers.script.error("UA_fail 'failed to create project in dna nexus'")
                # raise exception to stop script
                raise Exception, "Unable to create DNA Nexus project"

    def upload_fastqs(self):
        """
        Inputs = None
        All samples to be processed were identified in find_fastqs() which also created a string of 
        filepaths for all fastqs that is required by the upload agent.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        If debug mode the upload agent command is returned without calling execute_subprocess_command()
        Returns filepath to logfile (non-debug) 
        """
        # build the nexus upload command
        nexus_upload_command = (
            self.restart_ua_1
            + config.upload_agent_path
            + " --auth-token "
            + config.Nexus_API_Key
            + " --project "
            + self.runfolder_obj.nexus_project_name
            + "  --folder /"
            + self.runfolder_obj.nexus_path
            + " --do-not-compress --upload-threads 10"
            + self.fastq_string
            + self.restart_ua_2 
        )
        if self.debug_mode:
            return nexus_upload_command

        # Log fastq upload command to the uplaod agent logfile
        self.loggers.upload_agent.info("Fastq upload commands:\n{}".format(nexus_upload_command))
        # write to automated script logfile
        self.loggers.script.info(
            "Uploading fastqs. See commands at {}".format(self.loggers.upload_agent.filepath)
        )

        # execute upload agent command and write stdout and stderr to the DNANexus_upload_started.txt file
        out, err = self.execute_subprocess_command(nexus_upload_command)
        self.loggers.upload_agent.info("Uploading fastqs:\n{}\n{}".format(out, err))
        return self.loggers.upload_agent.filepath , self.fastq_string, "fastq"

    def look_for_upload_errors(self, upload_agent_stdout_path, file_list, stage):
        """
        Inputs :
            path to log file
            file_list = a string (space delimited list) or list of files to be uploaded at this stage
            stage = the stage to be included in error report.
        Parse the file containing standard error/standard out from the upload agent.
        For each expected file to be uploaded check the expected upload success statement is present.
        If the success statement is absent raise an alert but do not stop script from running
        Returns: 
            strings (debug mode only).
        """
        # list to hold any files with issues
        issue_list=[]
        # for each file in the list to upload
        for file in file_list:
            # set flag to say upload unsuccessful
            upload_ok=False
            # loop through log file - if it's a line relating to this fastq check it's uploaded successfully.
            for line in open(upload_agent_stdout_path).read():
                if file in line and "was uploaded successfully. Closing..." in line:
                    upload_ok = True
            # if at the end of the file there was no success statement found
            if not upload_ok:
                issue_list.append(file)
        
        # Report back if ok, not ok with/without debug mode
        if issue_list and self.debug_mode:
            return  "fail"
        elif issue_list:
            self.loggers.script.error(
                "UA_fail 'upload of {} files failed for run {}'".format(
                    stage, self.runfolder_obj.runfolder_name
                    )
                )
        # if no error but debug
        elif not issue_list and self.debug_mode:
            return "no error"
        # if no error and not debug write to log file check was ok
        else:
            self.loggers.script.info(
                "UA_pass 'upload of files complete for run {}'".format(
                    self.runfolder_obj.runfolder_name
                )
            )

    def upload_cluster_density(self):
        """
        Inputs = None
        All samples to be processed were identified in find_fastqs() which also created a string of 
        filepaths for all fastqs that is required by the upload agent.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        If debug mode the upload agent command is returned without calling execute_subprocess_command()
        Returns filepath to logfile (non-debug) 
        """
        # build the nexus upload command
        file_list = [os.path.join(self.runfolder_obj.runfolderpath, self.runfolder_obj.runfolder_name + config.cluster_density_file_suffix),
            + os.path.join(self.runfolder_obj.runfolderpath, self.runfolder_obj.runfolder_name + config.phasing_metrics_file_suffix)]

        nexus_upload_command = (
            self.restart_ua_1
            + config.upload_agent_path
            + " --auth-token "
            + config.Nexus_API_Key
            + " --project "
            + self.runfolder_obj.nexus_project_name
            + "  --folder /QC"
            + " --do-not-compress --upload-threads 10"
            + " ".join(file_list)
            + self.restart_ua_2  
        )
        if self.debug_mode:
            return nexus_upload_command

        # Log fastq upload command to the uplaod agent logfile
        self.loggers.upload_agent.info("Upload cluster density commands:\n{}".format(nexus_upload_command))
        # write to automated script logfile
        self.loggers.script.info(
            "Uploading cluster density files. See commands at {}".format(self.loggers.upload_agent.filepath)
        )

        # execute upload agent command and write stdout and stderr to the DNANexus_upload_started.txt file
        out, err = self.execute_subprocess_command(nexus_upload_command)
        self.loggers.upload_agent.info("Uploading cluster density files\n{}\n{}".format(out, err))
        return self.loggers.upload_agent.filepath, file_list, "cluster density"

    

    def nexus_fastq_paths(self, read1):
        """
        Inputs = name of R1 fastq file (str)
        Creates some variables used in the dx run commands
        Creates a nexus filepath for read1 and read2
        Uses filename to create a sample name - this is supplied to sentieon and BWA
        Returns a tuple (r1_filepath,r2_filepath,samplename)
        """
        # build full file nexus path including project
        read1_nexus_path = (
            self.runfolder_obj.nexus_project_name
            + ":"
            + os.path.join(self.runfolder_obj.nexus_path, read1)
        )
        # create read2 by replacing R1 with R2
        read2_nexus_path = (
            self.runfolder_obj.nexus_project_name
            + ":"
            + os.path.join(self.runfolder_obj.nexus_path, read1.replace("_R1_", "_R2_"))
        )
        # samplename is used to assign read groups in BWA or as an input to sentieon
        sample_name = read1.split("_R1_")[0]
        return (read1_nexus_path, read2_nexus_path, sample_name)

    def nexus_bedfiles(self, pannumber):
        """
        Input = pannumber
        Builds a dictionary of all bedfile inputs for given pan number.
        This will create a path to any BED file related input, even if this input is not relevant to
        the applied workflows or the BED file does not exist.
        3 scenarios for BED files:
            - Use a BED file with the same Pan number as the panel
            - Use a BED file with a different Pan number
            - Use a BED file that isn't named with a Pan number eg the name of the capture kit 

        Returns a dictionary
        """
        # create dict
        bed_dict = {}

        # for sambamba/hs metrics bed file if a different bed file is specified in config file use that, otherwise use the pannumber
        # given bed file could be a pan number or the name of a capture kit
        if self.panel_dictionary[pannumber]["sambamba_bedfile"]:
            bed_dict["sambamba"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["sambamba_bedfile"]
            )
        else:
            bed_dict["sambamba"] = (
                config.app_project + config.bedfile_folder + pannumber + "dataSambamba.bed"
            )

        # for sambamba/hs metrics bed file if a different bed file is specified in config file use
        # that, otherwise use the pannumber
        if self.panel_dictionary[pannumber]["hsmetrics_bedfile"]:
            bed_dict["hsmetrics"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["hsmetrics_bedfile"]
            )
        else:
            bed_dict["hsmetrics"] = (
                config.app_project + config.bedfile_folder + pannumber + "data.bed"
            )

        # BED file used for variant calling
        # Given bed file could have same pan number, different pan number, the name of a capture kit or None
        # BED file may not be provided for variant calling
        if self.panel_dictionary[pannumber]["variant_calling_bedfile"]:
            # if bedfile starts with Pan use the Pan123data.bed
            if self.panel_dictionary[pannumber]["variant_calling_bedfile"][0:3] == "Pan":
                bed_dict["variant_calling_bedfile"] = (
                    config.app_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber]["variant_calling_bedfile"]
                )
            # if bedfile stated is not named with "Pan" don't add "data.bed" - could be the capture design
            else:
                bed_dict["variant_calling_bedfile"] = (
                    config.app_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber]["variant_calling_bedfile"]
                )
        # if mokawes command to be executed and the variant calling bedfile not in config
        else:
            bed_dict["variant_calling_bedfile"] = None
        
        # paired end BED file used by BAMClipper
        bed_dict["mokaamp_bed_PE_input"] = (
            config.app_project + config.bedfile_folder + pannumber + "_PE.bed"
        )
        # oncologt variant callers need the flat file
        bed_dict["mokaamp_variant_calling_bed"] = (
            config.app_project + config.bedfile_folder + pannumber + "_flat.bed"
        )
        # RPKM bedfile has a different Pan number - defined in the config dictionary
        if self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]:
            bed_dict["rpkm_bedfile"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]
                + "_RPKM.bed"
            )
        return bed_dict

    def start_building_dx_run_cmds(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Loop through the list of fastqs, determine the pan number and use this to determine
        which workflow/apps should be run. Each app/workflow command is built by calling the relevant function
        When looping through samples flags and lists are used to determine which run wide tasks are required 
        These run wide commands eg multiqc are built after sample specific commands
        All commands are added to a list.
        Returns = list of commands
        """

        # Update script log file to say what is being done.
        self.loggers.script.info("Building dx run commands")
        
        # list to hold all commands.
        commands_list = []
        commands_list.append(self.source_command)
        
        # lists/flags for run wide commands
        mokaonc_list = [] 
        peddy = False
        sapientia_upload = False
        joint_variant_calling = False # not currently in use
        rpkm_list = [] # list for panels needing RPKM analysis

        # loop through samples
        for fastq in list_of_processed_samples:
            # take read one
            if re.search(r"_R1_", fastq):
                # extract Pan number and use this to determine which dx run commands are needed for the sample
                panel = re.search(r"Pan\d+", fastq).group()
                # The order in which the modules are called here is important to ensure the order 
                # of dx run commands is correct. This affects which decision support tool data is sent to.
                
                # If panel is to be processed using MokaWES
                if self.panel_dictionary[panel]["mokawes"]:
                    # call function to build the MokaWES command and add to command list and depends list
                    commands_list.append(self.create_mokawes_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))
                    # Set run-wide flags for Peddy and joint variant calling
                    if self.panel_dictionary[panel]["peddy"]:
                        peddy = True
                    if self.panel_dictionary[panel]["joint_variant_calling"]:
                        joint_variant_calling = True
                    # Add command for iva
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command(fastq, panel))
                    # TODO add sapientia command  for mokawes

                # If panel is to be processed using mokapipe
                if self.panel_dictionary[panel]["mokapipe"]:
                    # call function to build the Mokapipe command and add to command list and depends list
                    commands_list.append(self.create_mokapipe_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))
                    # Add command for iva or sapientia
                    if self.panel_dictionary[panel]["iva_upload"]:
                        commands_list.append(self.build_iva_input_command())
                        commands_list.append(self.run_iva_command(fastq, panel))
                        commands_list.append(self.add_to_depends_list(fastq))
                    if self.panel_dictionary[panel]["sapientia_upload"]:
                        sapientia_upload = True
                        commands_list.append(self.build_sapientia_input_command())
                        commands_list.append(self.run_sapientia_command(fastq, panel))
                        commands_list.append(self.add_to_depends_list(fastq))
                    # add panel to RPKM list 
                    if self.panel_dictionary[panel]["RPKM_bedfile_pan_number"]:
                        rpkm_list.append(panel)
                
                # If panel is to be processed using MokaONC
                if self.panel_dictionary[panel]["mokaonc"]:
                    mokaonc_list.append(fastq)

                # If panel is to be processed using MokaAMP
                if self.panel_dictionary[panel]["mokaamp"]:
                    commands_list.append(self.create_mokaamp_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))
        
        # if there is a sapientia uplaod create the file which will be run manually, once QC is passed.
        if sapientia_upload:
            self.build_sapientia_command_file()
            # write to logger to create slack alert that there are some sapientia files to upload
            self.loggers.script.info("Sapientia samples to upload in project {}".format(
                    self.runfolder_obj.nexus_project_name
                )
            )

        # build run wide commands 
        if mokaonc_list:
            commands_list.append(self.create_mokaonc_command(mokaonc_list))
        if joint_variant_calling:
            commands_list.append(self.create_joint_variant_calling_command())
        if rpkm_list:
            # Create a set of RPKM numbers for one command per panel
            # pass this list into function which takes into account panels which are to be analysed
            # together and returns a "cleaned_list"
            for rpkm in self.prepare_rpkm_list(set(rpkm_list)):
                commands_list.append(self.create_rpkm_command(rpkm))
        if peddy:
            # TODO if custom panels and WES done together currently no way
            # to stop custom panels being analysed by peddy - may cause problems
            commands_list.append(self.run_peddy_command())
        # multiqc commands
        commands_list.append(self.create_multiqc_command())
        commands_list.append(self.create_upload_multiqc_command())
        # smartsheet
        commands_list.append(self.create_smartsheet_command())
        return commands_list

    def create_mokawes_command(self, fastq, pannumber):
        """
        Input = R1 fastq filename and Pan number for a single sample 
        Returns = dx run command for MokaWES workflow (string)
        """
        # call function to build nexus fastq paths - returns tuple for read1 and read2 and samplename
        fastqs = self.nexus_fastq_paths(fastq)
        # build dictionary of pan number specific/relevant bedfile to be used in command
        bedfiles = self.nexus_bedfiles(pannumber)

        # A bedfile to restrict variant calling should be defined in the config file, otherwise it's None
        # In the future we may not restrict variant calling using a bed file so support this possible use case.
        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.wes_sentieon_targets_bed + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # create the MokaWES dx command
        dx_command_list = [
            self.wes_command,
            fastqs[2],
            config.wes_fastqc1,
            fastqs[0],
            config.wes_fastqc2,
            fastqs[1],
            config.wes_sentieon_samplename,
            fastqs[2],
            config.wes_picard_bedfile,
            bedfiles["hsmetrics"],
            config.wes_sambamba_bedfile,
            bedfiles["sambamba"],
            bedfiles_string,
            self.dest,
            self.dest_cmd,
            self.token,
        ]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_mokapipe_command(self, fastq, pannumber):
        """
        Input = R1 fastq filename and Pan number for a single sample 
        Returns =  dx run command for Mokapipe (string)
        """
        # build nexus fastq paths - returns tuple for read1 and read2 and samplename and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # bedfiles aren't usually provided to mokapipe variant calling but this is required for sapientia
        # STG require padding of +/- 11bp (bed files are padded +/-10bp) so may need to utilise the Haplotype caller padding argument.
        
        if self.panel_dictionary[pannumber]["mokapipe_haplotype_caller_padding"]:
            mokapipe_padding_cmd = config.mokapipe_haplotype_padding_input +\
                str(self.panel_dictionary[pannumber]["mokapipe_haplotype_caller_padding"])
        else:
            mokapipe_padding_cmd = ""
        
        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.mokapipe_haplotype_bedfile_input + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # create the dx command
        dx_command = (
            self.mokapipe_command
            + fastqs[2]
            + config.mokapipe_fastqc1
            + fastqs[0]
            + config.mokapipe_fastqc2
            + fastqs[1]
            + config.mokapipe_bwa_rg_sample
            + fastqs[2]
            + config.mokapipe_sambamba_input
            + bedfiles["sambamba"]
            + config.mokapipe_mokapicard_vendorbed_input
            + bedfiles["hsmetrics"]
            + mokapipe_padding_cmd
            + bedfiles_string
            + self.dest
            + self.dest_cmd
            + self.token
        )

        return dx_command

    def create_mokaonc_command(self, mokaonc_list):
        """
        Input = List of read1 fastqs.
        MokaONC only supports one panel (Pan1190) so some values are hard coded here
        This pipeline is soon to be discontinued
        Returns = one dx run command for all samples (string)
        """
        # start dx run command capturing job id etc
        dx_command = self.mokaonc_command
        # loop through the list of read 1 fastqs
        for sample_fq in mokaonc_list:
            # call function to build nexus fastq paths - returns tuple for read1 and read2
            fastqs = self.nexus_fastq_paths(sample_fq)
            # add each as an input
            dx_command += config.mokaonc_fq_input + fastqs[0] + config.mokaonc_fq_input + fastqs[1]

        # create the dx command include email address for ingenuity - NB only one panel is supported by MokaONC hense hard coded pan number
        command_out = (
            dx_command
            + config.mokaonc_ingenuity
            + self.panel_dictionary["Pan1190"]["ingenuity_email"]
            + self.dest
            + self.dest_cmd
            + "amplivar_output"
            + self.token
        )

        return command_out

    def build_iva_input_command(self):
        """
        Inputs = None
        Ingenuity import app has been moved out of the workflow.
        The input to the app are in the format jobid.output name.
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and
        decision support tool and prints the required input to command line
        Returns = command for this python program (string)
        """
        # $jobid is a bash variable which will be populated by when run on the command line
        # The python script has three inputs - the analysisID ($jobid), -t is the DSS and -p is the
        # DNA Nexus project the analysis is running in
        dx_command = "%s $jobid -t iva -p %s)" % (
            self.decision_support_preperation,
            self.runfolder_obj.nexus_project_name,
        )
        return dx_command
    
    def build_sapientia_command_file(self):
        """
        Inputs = None
        Create the file which will hold sapientia commands. 
        Write the source command, activating the environment (the sdk).
        Returns = None
        """
        with open(self.sapientia_upload_command_script_path, "w") as sapientia_script:
            sapientia_script.write(self.source_command + "\n")

    def build_sapientia_input_command(self):
        """
        Inputs = None
        Saptientia import app is outside out of the workflow.
        Inputs to the import can be provided in the format jobid.output name.
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and
        decision support tool and prints the required input to command line
        Returns = command for this python program (string)
        """
        # $jobid is a bash variable which will be populated by when run on the command line
        # The python script has three inputs - the analysisID ($jobid), -t is the DSS and -p is the
        # DNA Nexus project the analysis is running in
        dx_command = "%s $jobid -t sapientia -p %s)" % (
            self.decision_support_preperation,
            self.runfolder_obj.nexus_project_name,
        )
        return dx_command

    def create_mokaamp_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample        
        Returns = dx run command for MokaAMP (string)
        """

        # build nexus fastq paths - returns tuple for read1 and read2 and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # create the MokaAMP dx command
        dx_command_list = [
            self.mokaamp_command,
            fastqs[2],
            config.mokaamp_fastq_R1_stage,
            fastqs[0],
            config.mokaamp_fastq_R2_stage,
            fastqs[1],
            config.mokaamp_mokapicard_bed_stage,
            bedfiles["hsmetrics"],
            config.mokaamp_mokapicard_capturetype_stage,
            self.panel_dictionary[pannumber]["capture_type"],
            config.mokaamp_bamclipper_BEDPE_stage,
            bedfiles["mokaamp_bed_PE_input"],
            config.mokaamp_chanjo_cov_level_stage,
            self.panel_dictionary[pannumber]["clinical_coverage_depth"],
            config.mokaamp_sambamba_bed_stage,
            bedfiles["sambamba"],
            config.mokaamp_vardict_bed_stage,
            bedfiles["mokaamp_variant_calling_bed"],
            config.mokaamp_varscan_bed_stage,
            bedfiles["mokaamp_variant_calling_bed"],
            config.mokaamp_varscan_strandfilter_stage,
            self.panel_dictionary[pannumber]["mokaamp_varscan_strandfilter"],
            self.dest,
            self.dest_cmd,
            self.token,
        ]

        # Variables from dx_command_list are read from config file as various atomic types. Convert
        # to string and join to create dx_command.
        dx_command = "".join(map(str, dx_command_list))

        # remove the bit that adds the job to the depends on list for the negative control as varscan
        # fails on nearempty/-empty BAM files 
        # and this will stop multiqc etc running
        if "NTCcon" in fastqs[0]:
            dx_command = dx_command.replace("jobid=$(", "").replace(
                config.Nexus_API_Key + ")", config.Nexus_API_Key
            )
        return dx_command

    def prepare_rpkm_list(self, rpkm_list):
        """
        Input = a list of panels which requires RPKM analysis
        Pan numbers are used to distinguish between samples analysed in sapientia or in ingenuity.
        These samples have the same wetlab work so can be combined for RPKM analysis 
        This function determines if it's a pan number that can be analysed alongside another
        (using config bedfile property "RPKM_also_analyse")
        and makes sure only one job is set off       
        Returns = A list with one pan number per analysis.
        """
        # empty list to return
        cleaned_list = []
        # list of bedfiles which already have a rpkm command
        addressed_panels = []
        
        # for each panel which requires rpkm
        for pannumber in rpkm_list:
            # create a list for all pannumbers that should be included in this analysis
            rpkm_analysis_list = [pannumber]
            # if it is analysed with other panels append these other panels 
            if self.panel_dictionary[pannumber]["RPKM_also_analyse"]:
                rpkm_analysis_list += self.panel_dictionary[pannumber]["RPKM_also_analyse"]
            
            # Now we have all pan numbers to be included within this analysis
            for panel in rpkm_analysis_list:
                # if one of the panels involved in the analysis has already been parsed this panel
                # will be in the addressed_panels list
                if panel in addressed_panels:
                    pass
                # if it's not in the addressed_panels list it means none of the panels in this
                # analysis have been assessed
                # add all the panels in this analysis to addressed_panels list and just one panel
                # to the cleaned list to set off one RPKM job
                else:
                    addressed_panels += rpkm_analysis_list
                    cleaned_list.append(panel)

        # record output of logic in logfile
        self.loggers.script.info(
            "Combining panels for RPKM analysis.\nOriginal panels: {}\nPanels to analyse: {}".format(
                ",".join(rpkm_list), ",".join(cleaned_list)
            )
        )

        # return list to be used to build rpkm command(s).
        return cleaned_list

    def create_rpkm_command(self, pannumber):
        """
        Input = Pannumber for a single RPKM analysis
        The RPKM app requires a project id, bedfile and a string containing the pannumber(s) of all
        files that should be included in this analysis.
        Multiple pannumbers can be included in a single analysis.
        Return = dx run command for RPKM app for this analysis (string)
        """
        # call function to return all the bedfile paths
        bedfiles = self.nexus_bedfiles(pannumber)

        # Samples with different pannumbers can be included in the same RPKM analysis.
        # The app takes these pan numbers as a string, and will seperate on commas to identify multiple pan numbers
        # Multiple pannumbers are specified in the panel dictionary as a list under "RPKM_also_analyse"
        string_of_pannumbers_to_analyse = pannumber
        if self.panel_dictionary[pannumber]["RPKM_also_analyse"]:
            string_of_pannumbers_to_analyse = (
                string_of_pannumbers_to_analyse
                + ","
                + ",".join(self.panel_dictionary[pannumber]["RPKM_also_analyse"])
            )

        # build RPKM command
        dx_command = (
            self.RPKM_command
            + config.rpkm_bedfile_input
            + bedfiles["rpkm_bedfile"]
            + config.rpkm_project_input
            + self.runfolder_obj.nexus_project_name
            + config.rpkm_bamfiles_to_download_input
            + string_of_pannumbers_to_analyse
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token.rstrip(")")
        )
        return dx_command

    def create_joint_variant_calling_command(self):
        """-"""
        # TODO: Implement joint-variant calling command for peddy
        raise NotImplementedError

    def run_sapientia_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample
        The import saptientia app takes inputs in the format jobid.outputname which ensures the job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        The panel dictionary in the config file is used to determine the sapientia project
        This command is appended to a file which will be run after the QC is passed.
        Returns = dx run command for sapientia import app (string)
        """
        # the nexus_fastq_paths function returns paths to the fastq files in Nexus and the sample name 
        # The samplename (fastqs[2]) is used to name the job
        fastqs = self.nexus_fastq_paths(fastq)

        dx_command = (
            self.sapientia_upload_command
            + "' $analysisid ' -isapientia_project="
            + self.panel_dictionary[pannumber]["sapientia_project"]
            + " --name "
            + "SAPIENTIA_"
            + fastqs[2]
            + self.dest
            + self.dest_cmd
            + self.token.replace(")", self.sapientia_upload_command_redirect)
        )
        return dx_command

    def run_iva_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample
        The Ingenuity import app takes inputs in the format jobid.outputname which ensures the job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        The panel dictionary in the config file is used to determine the email account to upload samples into.
        Returns = dx run command for Ingenuity import app (string)
        """
        # the nexus_fastq_paths function returns paths to the fastq files in NExus and the sample name 
        # The samplename (fastqs[2]) is used to name the job
        fastqs = self.nexus_fastq_paths(fastq)

        dx_command = (
            self.iva_upload_command
            + " $analysisid"
            + " --name "
            + "QIAGEN_IVA_"
            + fastqs[2]
            + config.iva_email_input_name
            + self.panel_dictionary[pannumber]["ingenuity_email"]
            + self.project
            + self.runfolder_obj.nexus_project_id
            + config.iva_reference_inputname
            + config.iva_reference_default
            + self.token
        )
        return dx_command

    def add_to_depends_list(self, fastq):
        """
        Input = fastq file
        As jobs are set off the jobid is captured
        The job ids are built into a string which can be passed to any apps to ensure these jobs
        don't start until all specified jobs have sucessfully completed.
        However, some jobs should be excluded from the depends list, eg negative controls
        Returns = command which adds jobid to the bash string (string) 
        """
        if "NTCcon" in fastq:
            return None
        else:
            return self.depends_list

    def create_multiqc_command(self):
        """
        Input = None
        MultiQC is run at the very end of the run, after all QC tools have been run.
        MultiQC requires a project to download data from, and a coverage level.
        The coverage level differs between panels. The lowest value for the panels on this run is used.
        Returns = dx run command (string)
        """
        # set super high coverage level
        lowest_coverage_level = 1000000
        # for each fastq to be processed 
        for fastq in self.list_of_processed_samples:
            # take read one
            if re.search(r"_R1_", fastq):
                # extract_Pan number and use this to determine which coverage level is required
                pannumber = re.search(r"Pan\d+", fastq).group()
                # if the required coverage for this panel is less than current value of lowest_coverage_level
                # set lowest_coverage_level to this level
                if (
                    int(self.panel_dictionary[pannumber]["multiqc_coverage_level"])
                    < lowest_coverage_level
                ):
                    lowest_coverage_level = self.panel_dictionary[pannumber][
                        "multiqc_coverage_level"
                    ]
        
        # build multiqc command
        dx_command = (
            self.multiqc_command
            + config.multiqc_project_input
            + self.runfolder_obj.nexus_project_name
            + config.multiqc_coverage_level_input
            + str(lowest_coverage_level)
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token
        )
        return dx_command

    def create_upload_multiqc_command(self):
        """
        Input = None
        The input to the upload_multiqc app is the html_report output of the multiqc app, in the format jobid:output_name
        Returns = dx run command for the upload_multiqc app (string)
        """
        # dx run + config.app_project + config.upload_multiqc_path + -imultiqc_html= + input.html
        dx_command = "".join(
            [
                self.upload_multiqc_command,
                " -imultiqc_html=$jobid:multiqc_report",
                " -multiqc_data_input=$jobid:multiqc",
                " -multiqc_data_input=/QC/*" + self.runfolder_obj.runfolder_name + config.cluster_density_file_suffix,
                self.project,
                self.runfolder_obj.nexus_project_id,
                self.token,
            ]
        )
        return dx_command

    def run_peddy_command(self):
        """
        Input = None
        Peddy is run once at the end of a WES run. It takes a project and downloads all the required files.
        Returns = dx run command for the peddy app (string)
        """
        dx_command = (
            self.peddy_command
            + config.peddy_project_input
            + self.runfolder_obj.nexus_project_name
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token
        )
        return dx_command

    def create_smartsheet_command(self):
        """
        Input = None
        Once all workflows have completed smartsheet can be updated to record OPMS.
        Returns = dx run command (string)
        """
        dx_command = (
            self.smartsheet_update_command
            + config.smartsheet_mokapipe_complete
            + self.runfolder_obj.runfolder_name
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token.rstrip(")")
        )
        return dx_command

    def write_dx_run_cmds(self, command_list):
        """
        Input = list of commands
        Takes a list of commands generated by start_building_dx_run_cmds and writes them to file.
        Returns = None
        """
        with open(self.runfolder_obj.runfolder_dx_run_script, "w") as dxrun_commands:
            # remove any None values from the command_list
            dxrun_commands.writelines([line + "\n" for line in filter(None, command_list)])

    def clean_stderr(self, err):
        """
        Input = stderror (string)
        Currently have a conflict between packages from different python instances.
        This function parses stderr to remove these so real error messages stand out
        This function can be removed after the conflict is sorted
        Returns = lines of stderror not including expected messages (list)
        """
        std_err_ignore_match = r"/usr/local/lib/python2.7/dist-packages/urllib3/util/ssl_.py:"
        sni_warning_ignore_match = r"SNIMissingWarning"
        cleaned_error = []
        for line in err.split("\n"):
            clean_line = line.rstrip()
            # If the line doesn't contain a string that should be ignored
            if not re.match(std_err_ignore_match, clean_line) and not re.search(
                sni_warning_ignore_match, clean_line
            ):
                cleaned_error.append(line)
        return cleaned_error

    def run_dx_run_commands(self):
        """
        Input = None
        Executes the bash script written in write_dx_run_cmds()
        Cleans and reports any standard error via the logfile and sys.log
        Outpt = None 
        """

        # run a command to execute the bash script made above
        cmd = "bash " + self.runfolder_obj.runfolder_dx_run_script
        (_, err) = self.execute_subprocess_command(cmd)

        # if any standard error
        if err:
            # currently have a conflict between packages from different python instances.
            # parse stdout to ignore these
            cleaned_error = self.clean_stderr(err)
            # if stderr after ignorning lines referring to the package conflict write to logger
            if cleaned_error:
                # send message to logger/log file
                self.loggers.script.error(
                    "UA_fail 'Error when starting pipeline for run {}. Stderror = \n{}".format(
                        self.runfolder_obj.runfolder_name, "\n".join(cleaned_error)
                    )
                )

        else:
            # write error message to log file
            self.loggers.script.info(
                "UA_pass 'dx run commands issued without error for run {}'".format(
                    self.runfolder_obj.runfolder_name
                )
            )

    def smartsheet_workflows_commands_sent(self):
        """
        Input = None
        This function updates smartsheet to say that the runfolder has started to be processed
        A payload is created, including a count of samples, timestamp and runfolder
        This is posted using the requests module to a given url
        The response is parsed to check the status was "success" otherwise an error is raised via (sys.log).
        Returns = None
        """

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
        payload = (
            '{"cells": [{"columnId": '
            + str(config.ss_title)
            + ', "value": "'
            + self.runfolder_obj.runfolder_name
            + '"}, {"columnId": '
            + str(config.ss_description)
            + ', "value": "MokaPipe"},{"columnId": '
            + str(config.ss_samples)
            + ', "value": '
            + str(len(self.list_of_processed_samples) / 2)
            + '},{"columnId": '
            + str(config.ss_status)
            + ', "value": "In Progress"},{"columnId": '
            + str(config.ss_priority)
            + ', "value": "Medium"},{"columnId": '
            + str(config.ss_assigned)
            + ', "value": "aledjones@nhs.net"},{"columnId": '
            + str(config.ss_received)
            + ', "value": "'
            + str(self.smartsheet_now)
            + '"}], "toBottom":true}'
        )

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
                    self.loggers.script.info(
                        "smartsheet_pass 'smartsheet updated to say in progress'"
                    )
                else:
                    self.loggers.script.error(
                        "smartsheet_fail 'run started NOT added to smartsheet for run {}'".format(
                            self.runfolder_obj.runfolder_name
                        )
                    )

    def write_opms_queries_mokapipe(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Samples processed using Mokapipe are recorded in Moka using an insert query.
        This function will create an insert query for each sample processed through mokapipe.
        If mokapipe samples are found this function will return a dictionary of sample counts, and a
        list of queries to be added to global dictionary.
        Returns = dictionary or None 
        """
        queries = []
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokapipe add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokapipe"]:
                    queries.append(
                        "insert into NGSCustomRuns(DNAnumber,PipelineVersion) values ('"
                        + str(fastq.split("_")[2])
                        + "','"
                        + config.mokapipe_pipeline_ID
                        + "')"
                    )
        if queries:
            # add workflow to sql dictionary
            return {"count": len(queries), "query": queries}
        else:
            return None

    def write_opms_queries_mokawes(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        All samples processed using MokaWES are recorded in moka using a single update query.
        If MokaWES samples - Function populates a dictionary of sample counts, and a query (str) to
        be added to global dictionary.
        Returns = dictionary or None 
        """
        dnanumbers = []
        # add workflow to sql dictionary
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = "Pan" + str(fastq.split("_Pan")[1].split("_")[0])
                # if the pan number was processed using mokawes add the query to list of queries,
                # capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokawes"]:
                    dnanumbers.append(str(fastq.split("_")[2]))
        if dnanumbers:
            return {
                "count": len(dnanumbers),
                "query": [
                    "update NGSTest set PipelineVersion = "
                    + config.mokawes_pipeline_ID
                    + " , StatusID = "
                    + config.mokastatus_dataproc_ID
                    + " where dna in ('"
                    + ("','").join(dnanumbers)
                    + "') and StatusID = "
                    + config.mokastat_nextsq_ID
                ],
            }
        else:
            return None

    def write_opms_queries_oncology(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Samples tested using mokaamp or mokaonc are not booked into Moka until the analysis stage so
        queries cannot be used to record pipeline version.
        This is recorded manually when creating the test in Moka
        Therefore an email informing the oncology team which version of the pipeline was applied is sent.
        If oncology samples found a dictionary is populated with a list of workflows and a message (str).
        If not a None object is returned
        Return = dictionary
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
        if workflows:
            return {
                "workflows": set(workflows),
                "query": self.runfolder_obj.runfolder_name
                + " being processed using workflow "
                + ",".join(set(workflows))
                + "\n\n"
                + config.mokaamp_email_message,
            }
        else:
            return None

    def send_opms_queries(self):
        """
        Input = None
        Queries to record the pipeline versions are emailed.
        This function sends the emails, using the queries built by write_opms_queries_oncology(),
        write_opms_queries_mokawes() and write_opms_queries_mokapipe() stored in self.sql_queries.
        The oncology and rare disease emails are sent seperately and independantly of each other.
        Returns = None
        """
        # send oncology email first
        if self.sql_queries["oncology"]:
            # email the workflow used to the oncology team
            email_subject = (
                "MOKAPIPE ALERT : Started pipeline for " + self.runfolder_obj.runfolder_name
            )
            email_message = (
                self.runfolder_obj.runfolder_name
                + " being processed using workflow "
                + ",".join(self.sql_queries["oncology"]["workflows"])
                + "\n\n"
                + self.sql_queries["oncology"]["query"]
            )
            # send email - pass multiple recipients in a list
            self.send_an_email([config.oncology_you, config.you], email_subject, email_message)

        # Start counters and placeholders to for email data
        workflows = []
        sql_statements = []
        count = 0

        # for each pipeline take queries, sample count and workflow name
        if self.sql_queries["mokapipe"]:
            workflows.append(config.mokapipe_path.split("/")[-1])
            sql_statements += self.sql_queries["mokapipe"]["query"]
            count += self.sql_queries["mokapipe"]["count"]
        if self.sql_queries["mokawes"]:
            workflows.append(config.mokawes_path.split("/")[-1])
            sql_statements += self.sql_queries["mokawes"]["query"]
            count += self.sql_queries["mokawes"]["count"]
        
        # send email
        if workflows and sql_statements:
            # email this query
            email_subject = (
                "MOKAPIPE ALERT - ACTION NEEDED: Started pipeline for "
                + self.runfolder_obj.runfolder_name
            )
            email_priority = 1  # high priority
            email_message = (
                self.runfolder_obj.runfolder_name
                + " being processed using workflow "
                + ",".join(set(workflows))
                + "\n\nPlease update Moka using the below query and ensure that "
                + str(count)
                + " records are updated:\n\n"
                + "\n".join(sql_statements)
            )
            # send email
            self.send_an_email(config.you, email_subject, email_message, email_priority)

    def upload_rest_of_runfolder(self):
        """
        Input = None
        The rest of the runfolder requires backing up, excluding bcl files.
        A python script which is a wrapper for the upload agent is used.
        This function copies the samplesheet from into the runfolder and then builds and executes
        the backup_runfolder.py command
        Returns = filepath to backup script.
        """

        # create the samplesheet name to copy
        samplesheet_name = self.runfolder_obj.runfolder_name + "_SampleSheet.csv"

        # try to copy samplesheet into project
        if os.path.exists(config.samplesheets + samplesheet_name):
            copyfile(
                config.samplesheets + samplesheet_name,
                os.path.join(self.runfolder_obj.runfolderpath, samplesheet_name),
            )
            self.loggers.script.info("Samplesheet copied to runfolder: {}".format(samplesheet_name))
        else:
            self.loggers.script.info("Samplesheet not copied to runfolder - already existed in runfolder")
        # build backup_runfolder.py command ignore some files
        cmd = (
            "python3 "
            + config.backup_runfolder_script
            + " -i "
            + self.runfolder_obj.runfolderpath
            + " -p "
            + self.runfolder_obj.nexus_project_name
            + " --ignore /L00,DNANexus_upload_started,add_runfolder_to_nexus_cmds --logpath "
            + config.backup_runfolder_logfile
            + " -a "
            + config.Nexus_API_Key
        )

        # write to the log file that the runfolder is being uploaded, linking to log files for cmds and stdout
        self.loggers.script.info("Uploading rest of run folder to Nexus using backup_runfolder.py")
        self.loggers.script.info(cmd)
        self.loggers.script.info(
            "See standard out from these commands in logfile at {}".format(
                self.loggers.backup.filepath
            )
        )

        # run the command
        _out, _err = self.execute_subprocess_command(cmd)
        # TODO add some tests for stderr?

        return self.loggers.backup.filepath

    def upload_log_files(self):
        """
        Input = None
            Upload the log files found in list_log_files.
        Returns = filepath to the logfile containing output from the command, string of files to be uploaded and 
        """
        # define where files to be uploaded to
        nexus_upload_folder = (
            "/"
            + self.runfolder_obj.nexus_project_name.replace(self.nexusproject, "")
            + "/Logfiles/"
        )
        
        # create a space delimited string of files to be uploaded defined by the logger class
        files_to_upload_string = " ".join([logger.filepath for logger in self.loggers.all if logger.filepath])
        files_to_upload_string += " " + os.path.join(self.runfolder_obj.runfolderpath, config.file_demultiplexing)
        
        # create a list which, when joined will form a single upload agent command, uploading each
        # file in logger.filepath
        command_list = [
            config.upload_agent_path,
            "--auth-token",
            config.Nexus_API_Key,
            "--project",
            self.runfolder_obj.nexus_project_name,
            "--folder",
            nexus_upload_folder,
            "--do-not-compress",
            "--upload-threads",
            "10",
            files_to_upload_string]
        #execute the command list
        cmd = subprocess.list2cmdline(command_list)

        # write these commands to the upload agent logfile before upload.
        self.loggers.upload_agent.info("Uploading logfiles.")
        self.loggers.upload_agent.info(cmd)

        # execute ua command
        out, err = self.execute_subprocess_command(cmd)

        # capture stdout to upload agent log file
        self.loggers.upload_agent.info("Uploading logfiles (this will not be included in DNANexus)")
        self.loggers.upload_agent.info(out)
        self.loggers.upload_agent.info(err)

        return self.loggers.upload_agent.filepath, files_to_upload_string, "log files"

    def look_for_upload_errors_backup_runfolder(self, logfile):
        """
        Input = path to logfile(backup_runfolder.py logfile)
        The presence of expected success/failure messages are checked and reported
        Returns = None
        """
        # parse the output of the backup runfolder script
        # if error statement seen report it regardless of presence of success statement
        # if success statement seen report it too.
        # set flags to avoid multiple reports
        
        upload_ok = False
        error_seen = []
        with open(logfile, "r") as backup_logfile:
            for line in backup_logfile.readlines():
                if config.backup_runfolder_success in line:
                    upload_ok = True
                if config.backup_runfolder_error in line:
                    error_seen.append(line)
        if error_seen:
            self.loggers.script.error(
                "UA_fail 'Error in upload of rest of runfolder: {} in runfolder {}'".format(
                    ";".join(error_seen), self.runfolder_obj.runfolder_name
                )
            )
        if upload_ok:
            self.loggers.script.info(
                "UA_pass 'Rest of runfolder {} uploaded ok'".format(
                    self.runfolder_obj.runfolder_name
                    )
                )



    def execute_subprocess_command(self, command):
        """
        Input = command (string)
        Takes a command, executes using subprocess.Popen
        If debug will return some predefined statements
        Returns =  (stdout,stderr) (tuple)
        """
        if not self.debug_mode:
            proc = subprocess.Popen(
                [command],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True,
                executable="/bin/bash",
            )

            # capture the streams
            return proc.communicate()
        else:
            return (
                " ".join(
                    [
                        config.upload_agent_expected_stdout,
                        config.dx_sdk_test_expected_stdout,
                        config.demultiplex_success_match,
                    ]
                ),
                "err",
            )

    def send_an_email(self, to, email_subject, email_message, email_priority=3):
        """
        Input = email address, email_subject, email_message, email_priority (optional, default = standard priority)
        Uses smtplib to send an email. 
        Returns = None
        """
        # create message object
        m = Message()
        # set priority
        m["X-Priority"] = str(email_priority)
        # set subject
        m["Subject"] = email_subject
        # set body
        m.set_payload(email_message)

        # server details
        server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
        server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
        server.starttls()
        server.ehlo()
        server.login(config.user, config.pw)
        server.sendmail(config.me, to, m.as_string())

        # write to logfile
        self.loggers.script.info(
            "UA_pass Email sent to {}. Subject {}. Body:\n{}".format(
                str(to), email_subject, email_message
            )
        )


if __name__ == "__main__":
    # Create a custom list object to hold sequencing runs
    runs = SequencingRuns()
    # Set list with runfolder objects
    runs.set_runfolders()
    # Call upload and workflow logic on runfolders
    runs.loop_through_runs()
