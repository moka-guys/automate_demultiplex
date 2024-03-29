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
import adlogger  # import ADLoggers, get_runfolder_log_config


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
        self.runfolders = []

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
            folder_exists = os.path.isdir(
                os.path.join(config.runfolders, folder)
            )
            if (
                folder not in config.ignore_directories
                and folder_exists
                and re.compile(config.runfolder_pattern).match(folder)
            ):
                self.runfolders.append(folder)

    def loop_through_runs(self):
        """
        Input = None
        Process all NGS runfolders in class instance list.
        Returns = None
        """

        # Track processed runfolders to use later for naming logfiles.
        processed_runfolders = []

        # Process any runfolders added to class instance with self.set_runfolders()
        for folder in self.runfolders:
            runfolder_instance = RunfolderProcessor(
                folder, self.now, debug_mode=config.testing
            )
            # Append processed runfolders to tracking list
            if runfolder_instance.quarterback():
                processed_runfolders.append(folder)
            # close down the run folder specific logger handles
            runfolder_instance.loggers.shutdown_logs()

        # Add names of any processed runfolders to logfile
        if processed_runfolders:
            original_logfile_path = (
                config.upload_and_setoff_workflow_logfile
                + self.now
                + "_upload_and_setoff_workflow.log"
            )
            new_logfile = original_logfile_path.replace(
                self.now, self.now + "_" + "_".join(processed_runfolders)
            )
            os.rename(original_logfile_path, new_logfile)


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
            config.DNA_Nexus_workflow_logfolder
            + self.runfolder_name
            + "_dx_run_commands.sh"
        )
        self.congenica_upload_command_script = (
            config.DNA_Nexus_workflow_logfolder
            + self.runfolder_name
            + "_congenica_upload_commands.sh"
        )
        self.TSO500_post_run_command_script = (
            config.DNA_Nexus_workflow_logfolder
            + self.runfolder_name
            + "_TSO_post_run_commands.sh"
        )
        
        self.nexus_project_name = ""
        self.nexus_path = ""
        self.nexus_project_id = ""
        self.runfolder_subdir = ""
        self.runfolder_samplesheet_path = os.path.join(
            config.samplesheets_dir, self.runfolder_name + "_SampleSheet.csv"
        )
        self.runfolder_samplesheet_name = (
            self.runfolder_name + "_SampleSheet.csv"
        )


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

        # string of fastqs for upload agent
        self.fastq_string = ""

        # list of fastqs to get ngs run number and WES batch
        self.list_of_processed_samples = []

        #list of TSO samplesheets
        self.TSO500_samplesheets_list = []

        # DNA Nexus commands to be built on later
        self.source_command = "#!/bin/bash\n. %s" % (
            config.sdk_source_cmd
        )
        self.empty_depends = "depends_list=''"
        self.empty_gatk_depends = "depends_list_gatk=''"
        self.createprojectcommand = 'project_id="$(dx new project --bill-to %s "%s" --brief --auth-token %s)"\n'
        self.mokapipe_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.mokapipe_path)
        )
        self.wes_command = "jobid=$(dx run %s%s --priority high -y --name " % (
            config.app_project,
            config.mokawes_path,
        )
        self.mokasnp_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.mokasnp_path)
        )
        self.fastqc_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.fastqc_app)
        )
        self.tso500_dx_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.tso500_app)
        )
        self.sompy_dx_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.sompy_app_id)
        )
        self.sambamba_dx_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.sambamba_app_id)
        )
        self.peddy_command = "jobid=$(dx run %s%s --priority high -y --instance-type mem1_ssd1_v2_x2" % (
            config.app_project,
            config.peddy_path,
        )
        self.multiqc_command = "jobid=$(dx run %s%s --priority high -y --instance-type mem1_ssd1_v2_x4" % (
            config.app_project,
            config.multiqc_path,
        )
        self.upload_multiqc_command = "jobid=$(dx run %s%s --priority high -y --instance-type mem1_ssd1_v2_x2" % (
            config.app_project,
            config.upload_multiqc_path,
        )
        self.duty_csv_command = "jobid=$(dx run %s -y" % config.duty_csv_id
        self.RPKM_command = (
            "jobid=$(dx run %s%s --priority high -y --instance-type mem1_ssd1_v2_x8"
            % (config.app_project, config.RPKM_path)
        )
        self.ED_readcount_command = (
            "EDjobid=$(dx run %s%s --priority high -y --instance-type %s"
            % (config.app_project, config.ED_readcount_path, config.ED_readcount_path_instance_type)
        )
        self.ED_cnvcalling_command = (
            "jobid=$(dx run %s%s --priority high -y --instance-type %s"
            % (config.app_project, config.ED_cnvcalling_path, config.ED_cnvcalling_instance_type)
        )
        self.mokaamp_command = (
            "jobid=$(dx run %s%s --priority high -y --name "
            % (config.app_project, config.mokaamp_path)
        )
        self.decision_support_preperation = "analysisid=$(python %s -a " % (
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                config.decision_support_tool_input_script,
            )
        )
        self.congenica_upload_command = "echo 'dx run %s%s -y --instance-type mem1_ssd1_v2_x2" % (
            config.app_project,
            config.congenica_app_path,
        )
        self.congenica_sftp_upload_command = "echo 'dx run %s%s -y" % (
            config.app_project,
            config.congenica_SFTP_upload_app,
        )
        # create filepath for file to hold congenica command(s)
        self.congenica_upload_command_script_path = "%s%s_congenica.sh" % (
            config.DNA_Nexus_workflow_logfolder,
            self.runfolder_obj.runfolder_name,
        )
        # string to redirect command (with variables) into file
        self.congenica_upload_command_redirect = "' >> %s" % (
            self.congenica_upload_command_script_path
        )
        # project to upload run folder into
        self.nexusproject = config.NexusProjectPrefix
        self.project_bash_script_path = (
            config.DNA_Nexus_project_creation_logfolder
            + self.runfolder_obj.runfolder_name
            + ".sh"
        )

        self.dest = " --dest="
        self.dest_cmd = ""
        self.project = " --project="
        self.token = " --brief --auth-token %s)" % (config.Nexus_API_Key)
        self.depends = " $depends_list"
        self.depends_gatk = " $depends_list_gatk"

        # arguments to capture jobids
        self.depends_list = 'depends_list="${depends_list} -d ${jobid} "'
        self.depends_list_ED_readcount = 'depends_list="${depends_list} -d ${EDjobid} "'
        self.depends_list_gatk = 'depends_list_gatk="${depends_list_gatk} -d ${jobid} "'
        self.depends_list_recombined = 'depends_list="${depends_list} ${depends_list_gatk} "'
        # Argument to define depends_list only if the job ID exists
        self.if_jobid_exists_depends = 'if ! [ -z "${jobid}" ]; then %s; fi'

        # command to restart upload agent part 1
        self.restart_ua_1 = "ua_status=1; while [ $ua_status -ne 0 ]; do "
        self.restart_ua_2 = (
            "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo "
            '"temporary issue when uploading file %s"; fi ; done'
        )

        self.panel_dictionary = self.set_panel_dictionary()
        self.sql_queries = {}

        # call the function which populates a dictionary of run specific logs and logfile paths.
        self.log_config = adlogger.get_runfolder_log_config(
            self.runfolder_obj, self.now
        )
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
        self.loggers.script.info(
            "automate_demultiplexing release:{}".format(git_tag.git_tag())
        )
        # Call upload agent,using perform test function. Pass output of this to self.test_upload_agent
        if not self.test_upload_agent(
            self.perform_test(
                self.execute_subprocess_command(
                    config.upload_agent_path + config.upload_agent_test_command
                )[0],
                "ua",
            )
        ):
            raise Exception("Upload agent not installed")

        # test dx toolkit installation
        if not self.test_dx_toolkit(
            self.perform_test(
                self.execute_subprocess_command(config.dx_sdk_test)[0],
                "dx_toolkit",
            )
        ):
            raise Exception("dx toolkit not installed")

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
            self.calculate_cluster_density(
                self.runfolder_obj.runfolderpath,
                self.runfolder_obj.runfolder_name,
            )
            # check for development pan number. If found self.list_of_processed_sampels will be empty and no further processing will occur
            if self.check_for_development_run():
                self.loggers.script.info("development pan number identified in samplesheet. Stopping any further processing")
            else:
                # check for TSO500 run - this is not demultiplexed locally but the entire runfolder is uploaded
                # read samplesheet to create a list of samples
                TSO500_sample_list = self.check_for_TSO500()
                # if not TSO500 will return None
                if TSO500_sample_list:
                    self.list_of_processed_samples, self.fastq_string = (
                        TSO500_sample_list,
                        self.runfolder_obj.runfolder_samplesheet_path, #this sets the fastq_string to be the samplesheet path
                    )

                else:
                    (
                        self.list_of_processed_samples,
                        self.fastq_string,
                    ) = self.find_fastqs(self.runfolder_obj.fastq_folder_path)

            if self.list_of_processed_samples:
                # build the project name using the WES batch and NGS run numbers
                (
                    self.dest_cmd,
                    self.runfolder_obj.nexus_path,
                    self.runfolder_obj.nexus_project_name,
                    self.runfolder_subdir
                ) = self.build_nexus_project_name(
                    self.capture_any_WES_batch_numbers(),
                    self.capture_library_batch_numbers(),
                )
                # create bash script to create and share nexus project -return filepath
                # pass filepath into module which runs project creation script - capturing projectid
                (
                    view_users_list,
                    admin_users_list,
                ) = self.write_create_project_script()
                self.runfolder_obj.nexus_project_id = (
                    self.run_project_creation_script(
                        view_users_list, admin_users_list
                    ).rstrip()
                )
                # split tso samplesheet and write split versions to the runfolder
                # build upload agent command for fastq upload and write stdout to ua_stdout_log
                # pass path to function which checks files were uploaded without error
                if TSO500_sample_list:
                    # split TSO samplesheet  to multiple sheets with <=16 samples/sheet
                    self.TSO500_samplesheets_list = self.split_TSO500_samplesheet()
                    backup_attempt_count = 1
                    while backup_attempt_count < 5:
                        self.loggers.script.info(
                            "Attempting to backup TSO runfolder. attempt {}".format(
                                backup_attempt_count
                            )
                        )
                        if self.look_for_upload_errors_backup_runfolder(
                            self.upload_rest_of_runfolder()
                        ):
                            backup_attempt_count = 10
                        else:
                            # increase backup count
                            backup_attempt_count += 1

                #upload fastqs. if TSO500 run, this uploads the samplesheet to the project root
                self.look_for_upload_errors(self.upload_fastqs())

                # upload cluster density files and check upload was successful.
                self.look_for_upload_errors(
                    self.upload_cluster_density_files_for_multiQC()
                )
                # upload bcl2fastq stats files and check upload was successful.
                self.look_for_upload_errors(
                    self.upload_bcl2fastq_QC_files_for_multiQC()
                )

                self.write_dx_run_cmds(
                    self.start_building_dx_run_cmds()
                )
                self.run_dx_run_commands()

                self.sql_queries["mokawes"] = self.write_opms_queries_mokawes()
                self.sql_queries[
                    "oncology"
                ] = self.write_opms_queries_oncology()
                self.sql_queries["TSO500"] = self.write_opms_queries_TSO500()
                self.sql_queries[
                    "custom_panel"
                ] = self.write_opms_queries_custom_panel()
                self.sql_queries["mokasnp"] = self.write_opms_queries_mokasnp()
                self.send_opms_queries()
                # if not TSO500 will return None
                if not TSO500_sample_list:
                    self.look_for_upload_errors_backup_runfolder(
                        self.upload_rest_of_runfolder()
                    )
                self.look_for_upload_errors(self.upload_log_files())
                # return true to denote that a runfolder was processed
                return True
        else:
            self.loggers.script.info(
                "Runfolder has already been processed: {}. Skipping.".format(
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
                dictionary_to_return[panel][
                    setting
                ] = config.default_panel_properties[setting]
            for setting in config.panel_settings[panel]:
                dictionary_to_return[panel][setting] = config.panel_settings[
                    panel
                ][setting]
        return dictionary_to_return

    def test_upload_agent(self, test_result):
        """
        Input = boolean value (True/False)
        This function receives the value from the function which assesses the output of calling the
        upload agent with --version.
        Returns = boolean value
        """
        if not test_result:
            self.loggers.script.error("UA_fail 'Upload Agent Test Failed'")
            return False
        else:
            self.loggers.script.info(
                "UA_pass 'Upload Agent function test passed'"
            )
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
        if test == "TSO500":
            if not re.search(
                config.demultiplexing_log_file_TSO500_message, test_input
            ):
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
            if (
                config.cluster_density_success_statement not in test_input
                or config.cluster_density_error_statement in test_input
            ):
                return False

        return True

    def test_dx_toolkit(self, test_result):
        """
        Input = Boolean
        This function receives a True/False value from the function which assesses the output of the
        dx toolkit test command
        Returns = boolean value
        """
        if not test_result:
            self.loggers.script.error(
                "UA_fail 'dx toolkit function test failed'"
            )
            return False

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
        self.loggers.script.info(
            "Working on {}".format(self.runfolder_obj.runfolderpath)
        )

        # use perform_test function to assert if the file exists - will return True if file exists
        if self.perform_test(
            os.path.join(
                self.runfolder_obj.runfolderpath, config.upload_started_file
            ),
            "already_uploaded",
        ):
            self.loggers.script.info(
                "Upload started file present. Terminating."
            )
            return True
        else:
            # if file doesn't exist return false to continue and write to log file
            self.loggers.script.info(
                "Upload started file not found. Continuing."
            )
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
            self.runfolder_obj.runfolderpath, config.file_demultiplexing
        )
        # check demultiplexing has been done using perform_test - returns true if file present
        if self.perform_test(demultiplex_file_path, "demultiplex_started"):
            with open(demultiplex_file_path, "r") as logfile:
                # capture logfile into list (not doing this caused an issue with the if loop below)
                logfile_list = logfile.readlines()
                # check if it's a TSO500 run
                if self.perform_test(logfile_list[-1], "TSO500"):
                    self.loggers.script.info("TSO500 run detected.")
                    return True
                # check if successful demuliplex statement in last line of log
                elif self.perform_test(
                    logfile_list[-1], "demultiplex_success"
                ):
                    self.loggers.script.info(
                        "Demultiplex completed succesfully."
                    )
                    return True
                else:
                    # write to logfile that demultplex was not successful
                    self.loggers.script.info("Demultiplex failed.")
                    return False
        else:
            # write to logfile that not yet demultiplexed
            self.loggers.script.info("Demultiplex has not been performed.")
            return False

    def check_for_TSO500(self):
        """
        Read samplesheet looking for TSO500 pan number.
        If TSO500 pannumber present add samplename to list
        return sample_list (will return False if empty)
        """
        sample_list = []
        with open(
            self.runfolder_obj.runfolder_samplesheet_path, "r"
        ) as samplesheet_stream:
            # read the file into a list and loop through the list in reverse (bottom to top).
            # this allows us to access the sample names, and stop when reach the column headers, skipping the header of the file.
            for line in reversed(samplesheet_stream.readlines()):
                if line.startswith("Sample_ID") or "[Data]" in line:
                    break
                # skip empty lines (check first element of the line, after splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                # if it's a line detailing a sample
                else:
                    for pannum in config.tso500_panel_list:
                        if pannum in line:
                            sample_list.append(line.split(",")[0])
        # as it takes a long time before the upload create the file to stop further processing
        if sample_list:
            open(self.loggers.upload_agent.filepath, "w").close()
        return sample_list

    def split_TSO500_samplesheet(self):
        """
        take TSO500 samplesheet and split in to parts with x samples per samplesheet (x defined in config.batch_size)
        write samplesheets to runfolder
        returns: list of samplesheet names
        """
        # samplesheet in the runfolder
        samplesheet_file = self.runfolder_obj.runfolder_samplesheet_path
        
        samplesheet_header = []
        samples = []
        no_sample_lines = 0
        expected_data_headers = ["Sample_ID", "Sample_Name", "index"]

        # Read all lines from the sample sheet
        with open(samplesheet_file) as samplesheet:
            for line in reversed(samplesheet.readlines()):
                # stop when get to data headers section
                if any(header in line for header in expected_data_headers):
                    break
                # skip empty lines (check first element of the line, after splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                        # If its a line containing a sample::
                elif line.startswith("TSO"):
                    samples.append(line)
                    no_sample_lines += 1
        # get header
        with open(samplesheet_file) as samplesheet:
            for line in samplesheet.readlines():
                # stop when get to data headers section- add header line to header then break
                if any(header in line for header in expected_data_headers):
                    samplesheet_header.append(line)
                    break
                else:
                    samplesheet_header.append(line)

        # reverse samples list to get back in correct order (starting at sample 1)
        samples.reverse()

        # Split samples into batches (size specified in config)
        # batches is a list of lists, where each list is a subset of the samples from the samplesheet
        # e.g. if batch_size=16, each list will contain up to 16 samples
        batches = [samples[i:i + config.batch_size] for i in range(0, len(samples), config.batch_size)]
        
        # Write batches to separate files named "PartXofY", and add samplesheet to list
        samplesheet_list = []
        number_of_batches = len(batches)
        #capture path for samplesheet in runfolder
        runfolder_samplesheet_file = os.path.join(self.runfolder_obj.runfolderpath, self.runfolder_obj.runfolder_samplesheet_name)
        samplesheet_base_name = runfolder_samplesheet_file.split(".csv")[0]
        for samplesheet_count, batch in enumerate(batches, start=1):
            #capture samplesheet file path to write samplesheet paths to the runfolder
            samplesheet_filepath = "%sPart%sof%s.csv" % (samplesheet_base_name,samplesheet_count,number_of_batches)
            # capture samplesheet name to write to list- use runfolder name
            samplesheet_name = "%s_SampleSheetPart%sof%s.csv" % (self.runfolder_obj.runfolder_name,samplesheet_count,number_of_batches)
            samplesheet_list.append(samplesheet_name)
            with open(samplesheet_filepath, "a") as new_samplesheet:
                new_samplesheet.writelines(samplesheet_header)
                new_samplesheet.writelines(batch)

        return(samplesheet_list)

    def check_for_development_run(self):
        """
        Read samplesheet looking for development pan number.
        If pannumber where development_run is True is present add samplename to list
        return sample_list (will return False if empty)
        """
        sample_list = []
        # build list of development pan numbers
        development_panel_list=[]
        for pan in self.panel_dictionary.keys():
            if self.panel_dictionary[pan]["development_run"]:
                development_panel_list.append(pan)

        with open(
            self.runfolder_obj.runfolder_samplesheet_path, "r"
        ) as samplesheet_stream:
            # read the file into a list and loop through the list in reverse (bottom to top).
            # this allows us to access the sample names, and stop when reach the column headers, skipping the header of the file.
            for line in reversed(samplesheet_stream.readlines()):
                if line.startswith("Sample_ID") or "[Data]" in line:
                    break
                # skip empty lines (check first element of the line, after splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                # if it's a line detailing a sample
                else:
                    for pannum in development_panel_list:
                        if pannum in line:
                            sample_list.append(line.split(",")[0])
        # as it takes a long time before the upload create the file to stop further processing
        if sample_list:
            open(self.loggers.upload_agent.filepath, "w").close()
        return sample_list
    
    def calculate_cluster_density(self, runfolder_path, runfolder_name):
        """
        Inputs = runfolder name and runfolder path
        Uses a dockerised version of GATK to run picard CollectIlluminaLaneMetrics
        This calculates cluster density and saves files (runfolder.illumina_phasing_metrics and runfolder.illumina_lane_metrics) to the runfolder
        If success statement seen in stderr record in log file else raise slack alert but do not stop run.
        Returns = None
        """
        # if novaseq need to give an extra flag to CollectIlluminaLaneMetrics
        if config.novaseq_id in runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        # docker command for tool
        cmd = "sudo docker run --rm -v {}:/input_run \
        broadinstitute/gatk:4.1.8.1 \
        ./gatk CollectIlluminaLaneMetrics \
        --RUN_DIRECTORY /input_run \
        --OUTPUT_DIRECTORY /input_run \
        --OUTPUT_PREFIX {} {}".format(
            runfolder_path, runfolder_name, novaseq_flag
        )

        # capture stdout and stderr
        # NB all output from picard tool is in stderr
        (out, err) = self.execute_subprocess_command(cmd)
        # assess stderr , looking for expected success statement
        if self.perform_test(err, "cluster_density"):
            self.loggers.script.info(
                "Cluster density calculation saved to {}".format(
                    runfolder_name + config.cluster_density_file_suffix
                )
            )
        # raise slack alert if success statement not present.
        else:
            self.loggers.script.error(
                "UA_fail 'Cluster density calculation failed for : {}'".format(
                    self.runfolder_obj.runfolder_name
                )
            )

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
                pan_match = re.search(r"Pan\d+", fastq)
                if pan_match and (pan_match.group()) in config.panel_list:
                    # we know what to do with it:
                    # append to string of paths for upload agent
                    fastq_string = (
                        fastq_string
                        + " "
                        + self.runfolder_obj.fastq_folder_path
                        + "/"
                        + fastq
                    )
                    # add the fastq name to a list to be used in create_nexus_file_path
                    list_of_processed_samples.append(fastq)
                else:
                    not_processed.append(fastq)
        if not_processed:
            self.loggers.script.error(
                "UA_fail '{} contained an unrecognised pan numbers: {}'".format(
                    self.runfolder_obj.runfolder_name, ",".join(not_processed)
                )
            )

        if not list_of_processed_samples:
            self.loggers.script.error(
                "UA_fail 'No known Pan numbers in fastq list'"
            )
            # if no fastqs to be processed return none object rather than empty list
            list_of_processed_samples = None
            fastq_string = None
        else:
            self.loggers.script.info(
                "{} fastqs found".format(str(len(list_of_processed_samples)))
            )

        return (list_of_processed_samples, fastq_string)

    def capture_any_WES_batch_numbers(self):
        """
        Input = list of samples to be processed
        DNANexus projects are named after the runfolder suffixed with identifiers.
        This function parses samplenames and identifies any WES batch numbers from the samplenames
        If WES batch number(s) are identified, Returns a string to be included in the project name
        If no batch numbers returns None
        Returns = string or None
        """
        # a list to hold all the wes numbers
        wes_numbers = []

        # for each fastq in the list of fastqs
        for fastq in self.list_of_processed_samples:
            # if the run has any WES samples
            if "WES" in fastq:
                # capture the WES batch (WES followed by digits)
                # optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", fastq).group()
                wes_numbers.append(wesbatch.replace("_", ""))
        # if no wes numbers are found return None rather than an empty string
        if wes_numbers:
            return "_".join(set(wes_numbers))
        else:
            return None

    def capture_library_batch_numbers(self):
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
        for fastq in self.list_of_processed_samples:
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
            # raise exception to stop script
            raise Exception("Unable to identify library batch numbers")

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
            runfolder_subdir = (
                self.runfolder_obj.runfolder_name
                + "_"
                + library_batch
                + "_"
                + wes_number
            )
            # build project name
            nexus_project_name = (
                config.NexusProjectPrefix
                + runfolder_subdir
            )

        else:
            # self.nexus path
            nexus_path = (
                self.runfolder_obj.runfolder_name
                + "_"
                + library_batch
                + config.fastq_folder
            )
            runfolder_subdir = (
                self.runfolder_obj.runfolder_name
                + "_"
                + library_batch
            )
            # build project name
            nexus_project_name = (
                config.NexusProjectPrefix
                + runfolder_subdir
            )


        # return tuple of string for self.dest
        return (nexus_project_name + ":/", nexus_path, nexus_project_name, runfolder_subdir)

    def write_create_project_script(self):
        """
        Input = list of processed samples
        Once the project name has been defined the project can be created using the DNANexus sdk
        Commands are written to a bash script and executed using subprocess. The project is created
        and shared with users, with varying degrees of access as defined in the config file.
        The list of processed samples is passed, extracting Pan numbers and assessing if the project should also be shared with any
        additional dry lab DNANexus accounts.
        This function writes a bash script containing the project creation command
        Return = two lists, one of users shared with view permissions, one with admin
        """
        view_users_list = []
        admin_users_list = []
        # open bash script
        with open(self.project_bash_script_path, "w") as project_script:
            project_script.write(self.source_command + "\n")
            project_script.write(self.empty_depends + "\n")
            project_script.write(
                self.createprojectcommand
                % (
                    config.prod_organisation,
                    self.runfolder_obj.nexus_project_name,
                    config.Nexus_API_Key,
                )
            )

            # Share the project with the nexus usernames in the list in config file
            # first give view permissions
            for user in config.view_users:
                project_script.write(
                    "dx invite %s $project_id VIEW --no-email --auth-token %s\n"
                    % (user, config.Nexus_API_Key)
                )
                view_users_list.append(user)
            # then give admin permissions - required incase some users are in both lists.
            for user in config.admin_users:
                project_script.write(
                    "dx invite %s $project_id ADMINISTER --no-email --auth-token %s\n"
                    % (user, config.Nexus_API_Key)
                )
                admin_users_list.append(user)
            # Some samples are analysed at dry labs. Access to projects should only be given when there is a sample for that dry lab on the run.
            # create a list of Pan numbers in the run
            pannumber_list = set(
                [
                    re.search(r"Pan\d+", sample).group()
                    for sample in self.list_of_processed_samples
                ]
            )
            # Pull out the drylab_dnanexus_ids for pan numbers where this is not None (default is None)
            dry_lab_list = [
                self.panel_dictionary[pannumber]["drylab_dnanexus_id"]
                for pannumber in pannumber_list
                if self.panel_dictionary[pannumber]["drylab_dnanexus_id"]
            ]
            # loop through dry_lab_list sharing project with user with readonly access
            for user in dry_lab_list:
                project_script.write(
                    "dx invite %s $project_id VIEW --no-email --auth-token %s\n"
                    % (user, config.Nexus_API_Key)
                )
                view_users_list.append(user)
            # echo the project id so it can be captured below
            project_script.write("echo $project_id")
            return view_users_list, admin_users_list

    def run_project_creation_script(self, view_users_list, admin_users_list):
        """
        Inputs = two lists, one with view permissions, one with admin permissions
        Calls subprocess command executing project creation bash script.
        Output of this command is tested to see if it meets the expected pattern.
        Returns - projectid (if created) , False (if debug) or an exception (non-debug)
        """
        # run a command to execute the bash script made above
        cmd = "bash " + self.project_bash_script_path
        (out, _) = self.execute_subprocess_command(cmd)

        # if start of project id is in out capture the id and write to logfiles and return
        if "project-" in out:
            # split std_out on "project" and get the last item to capture the project ID
            projectid = "project" + out.split("project")[-1].rstrip()

            # record in log file who project was shared with (VIEW)
            self.loggers.script.info(
                "DNA Nexus project {} created and shared (VIEW) to {}".format(
                    self.runfolder_obj.nexus_project_name,
                    ",".join(view_users_list),
                )
            )

            # record in log file who project was shared with (ADMIN)
            self.loggers.script.info(
                "DNA Nexus project {} created and shared (ADMIN) to {}".format(
                    self.runfolder_obj.nexus_project_name,
                    ",".join(admin_users_list),
                )
            )

            self.loggers.script.info("Projectid={}".format(projectid))
            # return projectid
            return projectid
        else:
            self.loggers.script.error(
                "UA_fail 'failed to create project in dna nexus'"
            )
            # raise exception to stop script
            raise Exception("Unable to create DNA Nexus project")

    def upload_fastqs(self):
        """
        Inputs:
            None
        All samples to be processed were identified in find_fastqs() which also created a string of
        filepaths for all fastqs that is required by the upload agent.
        This function can upload fastqs or a tar'd runfolder (previously used for TSO500)
        - If fastq's are being uploaded upload to subfolder, else upload to root of project
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        Returns:
            filepath to logfile
            file_list (space delimited string of files)
            stage name (string)
        """
        # test if fastqs are being uploaded - if so, set folder to the expected fastq location.
        upload_folder = ""
        if "fastq.gz" in self.fastq_string:
            upload_folder = self.runfolder_obj.nexus_path

        # build the nexus upload command
        nexus_upload_command = (
            self.restart_ua_1
            + config.upload_agent_path
            + " --auth-token "
            + config.Nexus_API_Key
            + " --project "
            + self.runfolder_obj.nexus_project_name
            + "  --folder /"
            + upload_folder
            + " --do-not-compress --upload-threads 10 "
            + self.fastq_string
            + self.restart_ua_2
        )

        # Log fastq upload command to the upload agent logfile
        self.loggers.upload_agent.info(
            "Fastq upload commands:\n{}".format(nexus_upload_command)
        )
        # write to automated script logfile
        self.loggers.script.info(
            "Uploading fastqs. See commands at {}".format(
                self.loggers.upload_agent.filepath
            )
        )

        # execute upload agent command and write stdout and stderr to the DNANexus_upload_started.txt file
        out, err = self.execute_subprocess_command(nexus_upload_command)
        self.loggers.upload_agent.info(
            "Uploading fastqs:\n{}\n{}".format(out, err)
        )
        return self.loggers.upload_agent.filepath, self.fastq_string, "fastq"

    def look_for_upload_errors(self, upload_module_output):
        """
        Inputs :
        A tuple containing:
            path to log file
            file_list = a string (space delimited list) or list of files to be uploaded at this stage
            stage = the stage to be included in error report.
        Parse the file containing standard error/standard out from the upload agent.
        For each expected file to be uploaded check the expected upload success statement is present.
        If the success statement is absent raise an alert but do not stop script from running
        Returns:
            strings (debug mode only).
        """
        upload_agent_stdout_path, file_list, stage = upload_module_output
        # This check is not always required, such as when optional files (eg the lane metrics) are not created so allow a new stage to be used to skip testing.
        if not stage == "skip_upload_error_check":
            # list to hold any files with issues
            issue_list = []
            # for each file in the list to upload
            for file in file_list:
                # set flag to say upload unsuccessful
                upload_ok = False
                # loop through log file - if it's a line relating to this fastq check it's uploaded successfully.
                for line in open(upload_agent_stdout_path).readlines():
                    if (
                        file in line
                        and "was uploaded successfully. Closing..." in line
                    ):
                        upload_ok = True
                # if at the end of the file there was no success statement found
                if not upload_ok:
                    issue_list.append(file)
            # Report back if ok
            if issue_list:
                self.loggers.script.error(
                    "UA_fail 'upload of {} files failed for run {}'".format(
                        stage, self.runfolder_obj.runfolder_name
                    )
                )
                self.loggers.script.error(
                    "UA_fail 'following files were not uploaded {}'".format(
                        issue_list
                    )
                )
            # if no error
            else:
                self.loggers.script.info(
                    "UA_pass 'upload of files complete for run {}'".format(
                        self.runfolder_obj.runfolder_name
                    )
                )

    def upload_cluster_density_files_for_multiQC(self):
        """
        Inputs = None
        Some QC metrics files that are used by multiqc may need to be uploaded before the rest of the runfolder to ensure they are included in the report
        This function build an upload agent command for the cluster density files.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        If debug mode the upload agent command is returned without calling execute_subprocess_command()
        Returns filepath to logfile (non-debug)
        """
        # build the nexus upload command
        file_list = [
            os.path.join(
                self.runfolder_obj.runfolderpath,
                str(self.runfolder_obj.runfolder_name)
                + str(config.cluster_density_file_suffix),
            ),
            os.path.join(
                self.runfolder_obj.runfolderpath,
                str(self.runfolder_obj.runfolder_name)
                + str(config.phasing_metrics_file_suffix),
            ),
        ]
        # check if the cluster density files exist before trying to upload- if they don't the script will fail when trying to upload them.
        if all([os.path.isfile(f) for f in file_list]):
            nexus_upload_command = (
                self.restart_ua_1
                + config.upload_agent_path
                + " --auth-token "
                + config.Nexus_API_Key
                + " --project "
                + self.runfolder_obj.nexus_project_name
                + "  --folder /QC"
                + " --do-not-compress --upload-threads 1 "
                + " ".join(file_list)
                + self.restart_ua_2
            )

            # Log fastq upload command to the upload agent logfile
            self.loggers.upload_agent.info(
                "Upload cluster density commands:\n{}".format(
                    nexus_upload_command
                )
            )
            # write to automated script logfile
            self.loggers.script.info(
                "Uploading cluster density files. See commands at {}".format(
                    self.loggers.upload_agent.filepath
                )
            )

            # execute upload agent command and write stdout and stderr to the DNANexus_upload_started.txt file
            out, err = self.execute_subprocess_command(nexus_upload_command)
            self.loggers.upload_agent.info(
                "Uploading cluster density files\n{}\n{}".format(out, err)
            )
            return (
                self.loggers.upload_agent.filepath,
                file_list,
                "cluster density",
            )
        # if the cluster density files do not exist skip the upload and return a string which skip the look_for_upload_errors checks.
        else:
            self.loggers.script.info(
                "UA_pass 'skipping upload of cluster density files - not all files present'"
            )
            return None, None, "skip_upload_error_check"

    def upload_bcl2fastq_QC_files_for_multiQC(self):
        """
        Inputs = None
        Some QC metrics files that are used by multiqc may need to be uploaded before the rest of the runfolder to ensure they are included in the report
        This function build an upload agent command for the bcl2fastq stats.json.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        Returns filepath to logfile (non-debug)
        """
        # build the nexus upload command
        file_list = [
            str(self.runfolder_obj.runfolderpath)
            + os.path.join(
                str(config.bcl2fastq_stats_path),
                str(config.bcl2fastq_stats_filename),
            )
        ]
        # check if the files exist before trying to upload- if they don't the script will fail when trying to upload them.
        if all([os.path.isfile(f) for f in file_list]):
            nexus_upload_command = (
                self.restart_ua_1
                + config.upload_agent_path
                + " --auth-token "
                + config.Nexus_API_Key
                + " --project "
                + self.runfolder_obj.nexus_project_name
                + "  --folder /"
                + self.runfolder_obj.nexus_path
                + "/Stats"
                + " --do-not-compress --upload-threads 1 "
                + " ".join(file_list)
                + self.restart_ua_2
            )

            # Log fastq upload command to the upload agent logfile
            self.loggers.upload_agent.info(
                "Upload bcl2fastq stats file commands:\n{}".format(
                    nexus_upload_command
                )
            )
            # write to automated script logfile
            self.loggers.script.info(
                "Uploading bcl2fastq stats files. See commands at {}".format(
                    self.loggers.upload_agent.filepath
                )
            )

            # execute upload agent command and write stdout and stderr to the DNANexus_upload_started.txt file
            out, err = self.execute_subprocess_command(nexus_upload_command)
            self.loggers.upload_agent.info(
                "Uploading bcl2fastq stats files\n{}\n{}".format(out, err)
            )
            return (
                self.loggers.upload_agent.filepath,
                file_list,
                "bcl2fastq_stats",
            )
        # if the cluster density files do not exist skip the upload and return a string which skip the look_for_upload_errors checks.
        else:
            self.loggers.script.info(
                "UA_pass 'skipping upload of bcl2fastq stats files - not all files present'"
            )
            return None, None, "skip_upload_error_check"

    def nexus_fastq_paths(self, read1):
        """
        Inputs = name of R1 fastq file (str)
        Creates some variables used in the dx run commands
        Creates a nexus filepath for read1 and read2
        Uses filename to create a sample name - this is supplied to sentieon and BWA
        Returns a tuple (r1_filepath,r2_filepath,samplename)
        """
        # build full file nexus path including project
        if "TSO" in read1:
            read1_nexus_path = (
                self.runfolder_obj.nexus_project_name
                + ":/analysis_folder/Logs_Intermediates/CollapsedReads/"
                + "%s/%s_R1.fastq.gz" % (read1, read1)
            )
            # create read2 by replacing R1 with R2
            read2_nexus_path = (
                self.runfolder_obj.nexus_project_name
                + ":/analysis_folder/Logs_Intermediates/CollapsedReads/"
                + "%s/%s_R2.fastq.gz" % (read1, read1)

            )
        else:
            read1_nexus_path = (
                self.runfolder_obj.nexus_project_name
                + ":"
                + os.path.join(self.runfolder_obj.nexus_path, read1)
            )
            # create read2 by replacing R1 with R2
            read2_nexus_path = (
                self.runfolder_obj.nexus_project_name
                + ":"
                + os.path.join(
                    self.runfolder_obj.nexus_path, read1.replace("_R1_", "_R2_")
                )
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
                config.app_project
                + config.bedfile_folder
                + pannumber
                + "dataSambamba.bed"
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
                config.app_project
                + config.bedfile_folder
                + pannumber
                + "data.bed"
            )
        # FH
        if self.panel_dictionary[pannumber]["FH_PRS_bedfile"]:
            bed_dict["fh_prs"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["FH_PRS_bedfile"]
            )
        else:
            bed_dict["fh_prs"] = (
                config.app_project
                + config.bedfile_folder
                + pannumber
                + "data.bed"
            )
        # BED file used for variant calling
        # Given bed file could have same pan number, different pan number, the name of a capture kit or None
        # BED file may not be provided for variant calling
        if self.panel_dictionary[pannumber]["variant_calling_bedfile"]:
            # if bedfile starts with Pan use the Pan123data.bed
            if (
                self.panel_dictionary[pannumber]["variant_calling_bedfile"][
                    0:3
                ]
                == "Pan"
            ):
                bed_dict["variant_calling_bedfile"] = (
                    config.app_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber][
                        "variant_calling_bedfile"
                    ]
                )
            # if bedfile stated is not named with "Pan" don't add "data.bed" - could be the capture design
            else:
                bed_dict["variant_calling_bedfile"] = (
                    config.app_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber][
                        "variant_calling_bedfile"
                    ]
                )
        # if mokawes command to be executed and the variant calling bedfile not in config
        else:
            bed_dict["variant_calling_bedfile"] = None

        # paired end BED file used by primer clipping tool
        if self.panel_dictionary[pannumber]["mokaamp_bed_PE_input"]:
            bed_dict["mokaamp_bed_PE_input"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["mokaamp_bed_PE_input"]
            )
        else:
            bed_dict["mokaamp_bed_PE_input"] = (
                config.app_project
                + config.bedfile_folder
                + pannumber
                + "_PE.bed"
            )

        #  oncology variant callers need the flat file
        if self.panel_dictionary[pannumber]["mokaamp_bed_PE_input"]:
            bed_dict["mokaamp_variant_calling_bed"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber][
                    "mokaamp_variant_calling_bed"
                ]
            )
        else:
            bed_dict["mokaamp_variant_calling_bed"] = (
                config.app_project
                + config.bedfile_folder
                + pannumber
                + "_flat.bed"
            )

        # RPKM bedfile has a different Pan number - defined in the config dictionary
        if self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]:
            bed_dict["rpkm_bedfile"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]
                + "_RPKM.bed"
            )
        
        if self.panel_dictionary[pannumber]["exome_depth_cnvcalling_BED"]:
            bed_dict["exome_depth_cnvcalling_BED"] = (
                config.app_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["exome_depth_cnvcalling_BED"]
                + "_CNV.bed"
            )

        return bed_dict

    def start_building_dx_run_cmds(self):
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
        commands_list.append(self.empty_depends)
        commands_list.append(self.empty_gatk_depends)

        # lists/flags for run wide commands
        peddy = False
        congenica_upload = False
        joint_variant_calling = False  # not currently in use
        rpkm_list = []  # list for panels needing RPKM analysis
        pannnumber_list= [] 
        exome_depth = False
        TSO500 = False

        # loop through samples
        for fastq in self.list_of_processed_samples:
            # Check if TSO sample using read 1 (TSO runs treated differently)
            if not re.search(r"_R1_", fastq) and fastq.startswith("TSO"):
                # extract Pan number and use this to determine which dx run commands are needed for the sample
                panel = re.search(r"Pan\d+", fastq).group()

                if self.panel_dictionary[panel]["TSO500"]:
                    TSO500 = True

            # If read 1 but not a not TSO500 sample
            elif re.search(r"_R1_", fastq):
                # extract Pan number and use this to determine which dx run commands are needed for the sample
                panel = re.search(r"Pan\d+", fastq).group()
                #create a list of all pan numbers in the run
                pannnumber_list.append(panel)
                # The order in which the modules are called here is important to ensure the order
                # of dx run commands is correct. This affects which decision support tool data is sent to.
                
                # determine if exome depth is needed - the exact commands will be determined in the function which handles exome_depth commands
                if self.panel_dictionary[panel]["exome_depth_cnvcalling_BED"]:
                    exome_depth = True
                
                # If panel is to be processed using MokaWES
                if self.panel_dictionary[panel]["mokawes"]:
                    # call function to build the MokaWES command and add to command list and depends list
                    commands_list.append(
                        self.create_mokawes_command(fastq, panel)
                    )
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list'))
                    # if sample to be uploaded to congenica there are 2 methods.
                    # if a project id is specified in the config it means it can eb uploaded as if it were a custom panel sample
                    # eg IR does not need patient specific info and can be uploaded using the upload agent
                    # otherwise if the congenica project is not set it should be uploaded via the SFTP
                    if self.panel_dictionary[panel]["congenica_upload"]:
                        congenica_upload = True
                        commands_list.append(
                            self.build_congenica_input_command()
                        )
                        # if project is specified then upload via upload agent
                        if self.panel_dictionary[panel]["congenica_project"]:
                            commands_list.append(
                                self.run_congenica_command(fastq, panel)
                            )
                        # if project is not specified upload via SFTP
                        else:
                            commands_list.append(
                                self.run_congenica_SFTP_upload_command(fastq)
                            )
                    # Set run-wide flags for Peddy and joint variant calling
                    if self.panel_dictionary[panel]["peddy"]:
                        peddy = True

                # If panel is to be processed using mokapipe
                if self.panel_dictionary[panel]["mokapipe"]:
                    # call function to build the Mokapipe command and add to command list and depends list
                    commands_list.append(
                        self.create_mokapipe_command(fastq, panel)
                    )
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list'))
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list_gatk'))
                    # # Add command for congenica
                    if self.panel_dictionary[panel]["congenica_upload"]:
                        congenica_upload = True
                        commands_list.append(
                            self.build_congenica_input_command()
                        )
                        commands_list.append(
                            self.run_congenica_command(fastq, panel)
                        )
                    # add panel to RPKM list
                    if self.panel_dictionary[panel]["RPKM_bedfile_pan_number"]:
                        rpkm_list.append(panel)

                # If panel is to be processed using MokaAMP
                if self.panel_dictionary[panel]["mokaamp"]:
                    commands_list.append(
                        self.create_mokaamp_command(fastq, panel)
                    )
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list'))

                # if panel is to be processed using mokasnp
                if self.panel_dictionary[panel]["mokasnp"]:
                    commands_list.append(
                        self.create_mokasnp_command(fastq, panel)
                    )
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list'))

                if self.panel_dictionary[panel]["archerdx"]:
                    commands_list.append(
                        self.create_fastqc_command(fastq)
                    )
                    commands_list.append(self.add_to_depends_list(fastq, 'depends_list'))

        # if there is a congenica upload create the file which will be run manually, once QC is passed.
        if congenica_upload:
            self.build_congenica_command_file()
            # write to logger to create slack alert that there are some congenica files to upload
            self.loggers.script.info(
                "Congenica samples to upload in project {}".format(
                    self.runfolder_obj.nexus_project_name
                )
            )

        # build run wide commands
        if joint_variant_calling:
            commands_list.append(self.create_joint_variant_calling_command())
        if peddy:
            # TODO if custom panels and WES done together currently no way
            # to stop custom panels being analysed by peddy - may cause problems
            commands_list.append(self.run_peddy_command())
            commands_list.append(self.add_to_depends_list("peddy", 'depends_list'))
        
        if exome_depth:
            commands_list.append("# Exome depth is run once per capture and then once per Pan number within that capture")
            # exome depth is run once per capture, and then for each capture, one per pannumber. This function returns a list of commands so need to add these to commands list
            for cmd in self.determine_exome_depth_requirements(pannnumber_list):
                commands_list.append(cmd)

        # write TSO commands if a TSO run.
        if TSO500:
            commands_list.append("#The TSOapp is set off once for each samplesheet made")
            commands_list.append("#Other jobs must be set off manually by running the file once the pipeline has finished")
            # build commands for the TSO500 app and set off fastqc commands (need a command per samplesheet)
            for samplesheet in self.TSO500_samplesheets_list:
                commands_list.append(self.create_tso500_command(samplesheet))
            
            self.build_TSO500_post_run_commands()
        
        # TSO500 multiqc commands are written to a separate file with a function called above
        if not TSO500:
            commands_list.append(self.create_multiqc_command())
            commands_list.append(self.add_to_depends_list("MultiQC", 'depends_list'))
            commands_list.append(self.create_upload_multiqc_command(TSO500))
            commands_list.append(self.add_to_depends_list("UploadMultiQC", 'depends_list'))
            
        # setoff the below commands later as they are not depended upon by 
        # MultiQC but are required for duty_csv
        if rpkm_list:
            # Create a set of RPKM numbers for one command per panel
            # pass this list into function which takes into account panels
            # which are to be analysed together and returns a "cleaned_list"
            for rpkm in self.prepare_rpkm_list(set(rpkm_list)):
                commands_list.append(self.create_rpkm_command(rpkm))
                commands_list.append(self.add_to_depends_list("rpkm", 'depends_list'))
            commands_list.append(self.add_to_depends_list("depends", 'depends_list_recombined'))

        if not TSO500:
            commands_list.append(self.create_duty_csv_command())

        return commands_list

    def build_TSO500_post_run_commands(self):
        """
        Function to build TSO500 commands to run after pipeline, i.e.
        Fastqc, sambamba, sompy, multiqc, upload multiqc and duty_csv
        Commands must be written to file _TSO_post_run_commands.sh 
        which can be run manually once pipeline done.
        For TSO samples, the fastqs are created within DNAnexus and the
        commands are generated using sample names parsed from the
        samplesheet. If for whatever reason those fastqs are not created
        by the DNAnexus app, the downstream job will not set off and
        therefore will produce no job ID to provide to the depends_list,
        which will create an error/ slack alert. To solve this problem,
        the job ID is only added to the depends list if it exits
        """
        # Update script log file to say what is being done.
        self.loggers.script.info("Building dx run commands for TSO500 post pipeline processing")

        # list to hold all commands.
        TSO500 = True
        TSOcommands_list = []
        TSOcommands_list.append(self.source_command)
        TSOcommands_list.append(self.empty_depends)
        TSOcommands_list.append(self.empty_gatk_depends)

        for sample in self.list_of_processed_samples:
            pannumber = re.search(r"Pan\d+", sample).group()
            TSOcommands_list.append(
                self.create_fastqc_command(sample)
            )
            # Only add to depends_list if job ID from previous command
            # is not empty
            TSOcommands_list.append(self.if_jobid_exists_depends % self.add_to_depends_list(sample, 'depends_list'))
            TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))

            TSOcommands_list.append(self.create_sambamba_cmd(sample, pannumber))
            # Exclude negative controls from the depends list as the NTC
            # coverage calculation can often fail. We want the coverage
            # report for the NTC sample to help assess contamination.
            # Only add to depends_list if job ID from previous command
            # is not empty
            TSOcommands_list.append(self.if_jobid_exists_depends % self.add_to_depends_list(sample, 'depends_list'))
            TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))

            if "HD200" in sample:
                TSOcommands_list.append(self.create_sompy_cmd(sample, pannumber))
                # Only add to depends_list if job ID from previous command
                # is not empty
                TSOcommands_list.append(self.if_jobid_exists_depends % self.add_to_depends_list("sompy", 'depends_list'))
                TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))
        
        TSOcommands_list.append(self.create_multiqc_command())
        TSOcommands_list.append(self.add_to_depends_list("MultiQC", 'depends_list'))
        TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))
        TSOcommands_list.append(self.create_upload_multiqc_command(TSO500))
        TSOcommands_list.append(self.add_to_depends_list("UploadMultiQC", 'depends_list'))
        TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))

        TSOcommands_list.append(self.create_duty_csv_command())
        TSOcommands_list.append(self.if_jobid_exists_depends % ('echo ${jobid}'))

        with open(
            self.runfolder_obj.TSO500_post_run_command_script, "w"
        ) as TSO500_commands:
            # remove any None values from the command_list
            TSO500_commands.writelines(
                [line + "\n" for line in filter(None, TSOcommands_list)]
            )

        return TSOcommands_list

    def determine_exome_depth_requirements(self,pannnumber_list):
        """
        This function takes a list of all pan numbers found on this run. 
        Exome depth is run in 2 stages, firstly readcounts are calculated for each capture panel (VCP1 or VCP2 etc).
        The jobid will be saved to $EDjobid which allows the output of this stage to be used to filter CNVs with a panel specific BEDfile.
        The CNV calling steps should be a dependancy of multiqc
        This function controls the order these commands are built and run so the output of the readcount step can be used as an input to the cnvcalling step
        Inputs:
            List of Pannumbers on the run
        Returns:
            List of dx run commands
        """
        
        # generate list of pan numbers in samplenames to process in ED
        VCP1=[]
        VCP2=[]
        VCP3=[]
        command_list=[]
        
        for pannumber in set(pannnumber_list):
            # not all VCP1/2/3 pan numbers need CNV calling
            if self.panel_dictionary[pannumber]["exome_depth_cnvcalling_BED"]:
                if pannumber in config.vcp1_panel_list:
                    VCP1.append(pannumber)
                if pannumber in config.vcp2_panel_list:
                    VCP2.append(pannumber)
                if pannumber in config.vcp3_panel_list:
                    VCP3.append(pannumber)
        
        # make sure there are enough samples for that capture
        if len(VCP1)>2:
            # first build readcount command.
            command_list.append(self.build_ED_readcount_cmd(set(VCP1), config.ED_readcount_normals_VCP1_file,config.ED_VCP1_readcount_BEDfile_pannum))
            # The output of readcount can be used in multiqc so add this to the multiqc depends list
            command_list.append(self.add_to_depends_list("exomedepth", 'depends_list_ED_readcount'))
            # the cnvcalling stage can use the jobid from the readcount stage as an input so run these before the next capture panel
            for panel in set(VCP1):# then build cnvcalling commands
                command_list.append(self.build_ED_cnv_calling_cmd(panel))
    
        if len(VCP2)>2:
            # first build readcount command
            command_list.append(self.build_ED_readcount_cmd(set(VCP2), config.ED_readcount_normals_VCP2_file,config.ED_VCP2_readcount_BEDfile_pannum))
            command_list.append(self.add_to_depends_list("exomedepth", 'depends_list_ED_readcount'))
            for panel in set(VCP2):# then build cnvcalling commands
                command_list.append(self.build_ED_cnv_calling_cmd(panel))

        if len(VCP3)>2:
            # first build readcount command
            command_list.append(self.build_ED_readcount_cmd(set(VCP3), config.ED_readcount_normals_VCP3_file,config.ED_VCP3_readcount_BEDfile_pannum))
            command_list.append(self.add_to_depends_list("exomedepth", 'depends_list_ED_readcount'))
            for panel in set(VCP3):# then build cnvcalling commands
                command_list.append(self.build_ED_cnv_calling_cmd(panel))

        return command_list
    
    def build_ED_readcount_cmd(self,pannumber_list, normals_file,readcount_bedfile_pannum):
        """
        This function builds the dx run command for the exome depth readcount app
        This is run once per capture panel
        Inputs:
            pannumber_list = list of Pan numbers for this capture panel on this run. used to determine which BAM files to download
            normals_file = predefined panel of normals data file (from config)
            readcount bedfile pannumber = predefined capture panel wide BEDfile (from config)
        Returns:
            dx run cmd (string)
        """
        #build bedfile address from the readcount_bedfile_pannum input 
        readcount_bedfile = "%s%s%s" % (config.app_project,config.bedfile_folder,readcount_bedfile_pannum)
    
        dx_command_list = [
            self.ED_readcount_command,
            config.exomedepth_readcount_reference_genome_input,
            config.exomedepth_readcount_bedfile_input,
            readcount_bedfile,
            config.exomedepth_readcount_normalsRdata_input,
            normals_file,
            config.exomedepth_readcount_projectname_input,
            self.runfolder_obj.nexus_project_name,
            config.exomedepth_readcount_pannumbers_input,
            ",".join(pannumber_list),
            self.depends_gatk, # use list of gatk related jobs to delay start
            self.dest,
            self.dest_cmd,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command
    
    def build_ED_cnv_calling_cmd(self,pannumber):
        """
        This function builds the dx run command to filter the CNV calls for a specific R number using a BEDfile
        Input:
            pannumber = pannumber to filter CNV calls
        Returns:
            dx run cmd (string)
        """
        # pull out the appropriate bedfile for ED cnvcalling app BEDfrom panel config dict (exome_depth_cnvcalling_BED)
        # note the Pan number for this BED will be different to that used to name the sample
        bedfiles = self.nexus_bedfiles(pannumber)
        ed_cnvcalling_bedfile = bedfiles["exome_depth_cnvcalling_BED"]

        dx_command_list = [
            self.ED_cnvcalling_command,
            config.exomedepth_cnvcalling_readcount_file_input,
            "$EDjobid:%s" % (config.exomedepth_readcount_rdata_output),
            config.exomedepth_cnvcalling_subpanel_bed_input,
            ed_cnvcalling_bedfile,
            config.exomedepth_cnvcalling_projectname_input,
            self.runfolder_obj.nexus_project_name,
            config.exomedepth_cnvcalling_pannumbers_input,
            pannumber,
            self.dest,
            self.dest_cmd,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command

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
                config.wes_sentieon_targets_bed
                + bedfiles["variant_calling_bedfile"]
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

    def create_fastqc_command(self, fastqs):
        """
        Build dx run command
        Inputs:
            fastqs
            Pan number
        Returns:
            dx run command for fastqc (string)
        """
        # call function to build nexus fastq paths - returns tuple for read1 and read2 and samplename
        fastqs = self.nexus_fastq_paths(fastqs)

        dx_command_list = [
            self.fastqc_command,
            fastqs[2],
            " -ireads=",
            fastqs[0],
            " -ireads=",
            fastqs[1],
            self.dest,
            self.dest_cmd,
        ]
        dx_command_list.append(self.token)

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_tso500_command(self,samplesheet):
        """
        Build dx run command for tso500 docker app.
        Will assess if it's a novaseq or not from the runfoldername and if it's
        a highthroughput TSO run (needing a larger instance type)
        Inputs:
            List of samplenames to be processed
        Returns:
            dx run command for tso500 app (string)
        """
        # Is it a novaseq run?
        if config.novaseq_id in self.runfolder_obj.runfolder_name:
            TSO500_analysis_options = "--isNovaSeq "
        else:
            TSO500_analysis_options = ""

        # get a list of unique pan numbers from samplenames
        pannumber_list = set(
            [
                re.search(r"Pan\d+", sample).group()
                for sample in self.list_of_processed_samples
            ]
        )
        # capture any pan numbers that are a highthroughput assay
        high_throughput_list = [
            pannumber
            for pannumber in pannumber_list
            if self.panel_dictionary[pannumber]["TSO500_high_throughput"]
        ]
        # if this list is not empty apply high throughput instance type,
        # otherwise use low throughput instance type
        if high_throughput_list:
            instance_type = (
                "--instance-type %s "
                % config.TSO500_analysis_instance_high_throughput
            )
        else:
            instance_type = (
                "--instance-type %s "
                % config.TSO500_analysis_instance_low_throughput
            )

        # build dx run command - inputs are:
        ## docker image (from config)
        ## runfolder_tar and samplesheet paths (from runfolder_obj class)
        ## analysis options eg --isNovaSeq flag
        dx_command_list = [
            self.tso500_dx_command,  # ends with --name so supply the runfolder name to name the job
            self.runfolder_obj.runfolder_name,
            config.TSO500_docker_image_stage,
            config.tso500_docker_image,
            config.TSO500_samplesheet_stage,
            self.runfolder_obj.nexus_project_id
            + ":"
            + self.runfolder_subdir 
            + "/"
            + samplesheet,
            config.TSO500_project_name_stage,
            self.runfolder_obj.nexus_project_name,
            config.TSO500_runfolder_name_stage, 
            self.runfolder_subdir,
            config.TSO500_analysis_options_stage,
            TSO500_analysis_options,
            instance_type,
            self.dest,
            self.dest_cmd,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command

    def create_sambamba_cmd(self, sample, pannumber):
        """"""
        # Get inputs based on output location within project
        bam_index = (
            "%sanalysis_folder/Logs_Intermediates/StitchedRealigned"
            "/%s/%s.bam.bai" % (self.dest_cmd, sample, sample)
            )
        bam = (
            "%sanalysis_folder/Logs_Intermediates/StitchedRealigned"
            "/%s/%s.bam" % (self.dest_cmd, sample, sample)
            )
        # Build dictionary of pan number specific/relevant bedfile to
        # be used in command
        bedfiles = self.nexus_bedfiles(pannumber)

        dx_command_list = [
            self.sambamba_dx_command,
            sample,
            " -ibam_index=%s" % bam_index,
            " -ibamfile=%s" % bam,
            (" -icoverage_level=%s"
            % self.panel_dictionary[pannumber]["clinical_coverage_depth"]),
            " -isambamba_bed=%s " % bedfiles["sambamba"],
            (config.TSO500_coverage_commands
                % (
                    self.panel_dictionary[pannumber][
                        "coverage_min_basecall_qual"
                    ],
                    self.panel_dictionary[pannumber][
                        "coverage_min_mapping_qual"
                    ],
                )),
            self.dest,
            "%scoverage/%s" % (self.dest_cmd, pannumber),
            self.token,
        ]
        return "".join(map(str, dx_command_list))

    def create_sompy_cmd(self, sample, pannumber):
        """"""
        dest_cmd = self.dest_cmd + "coverage/%s" % pannumber
        # Get inputs based on output location within project
        vcf = (
            "%sanalysis_folder/Results/%s/%s"
            "_MergedSmallVariants.genome.vcf" 
            % (self.dest_cmd, sample, sample)
            )
        dx_command_list = [
            self.sompy_dx_command,
            sample,
            " -itruthVCF=project-ByfFPz00jy1fk6PjpZ95F27J:file-G7g9Pfj0jy1f87k1J1qqX83X",
            " -iqueryVCF=%s" % vcf,
            " -iTSO=true",
            " -iskip=false",
            self.dest,
            self.dest_cmd,
            self.token,
        ]
        return "".join(map(str, dx_command_list))

    def create_mokasnp_command(self, fastq, pannumber):
        """
        Input = R1 fastq filename and Pan number for a single sample
        Returns = dx run command for MokaSNP workflow (string)
        """
        # call function to build nexus fastq paths - returns tuple for read1 and read2 and samplename
        fastqs = self.nexus_fastq_paths(fastq)
        # build dictionary of pan number specific/relevant bedfile to be used in command
        bedfiles = self.nexus_bedfiles(pannumber)

        # A bedfile to restrict variant calling should be defined in the config file, otherwise it's None
        # In the future we may not restrict variant calling using a bed file so support this possible use case.
        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.snp_sentieon_targets_bed
                + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # create the MokaSNP dx command
        dx_command_list = [
            self.mokasnp_command,
            fastqs[2],
            config.snp_fastqc1,
            fastqs[0],
            config.snp_fastqc2,
            fastqs[1],
            config.snp_sentieon_samplename,
            fastqs[2],
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

        # Congenica requires variant calling to be restricted in the pipeline, in some cases to prevent incidental findings
        # The variant caller pads bed files by 100bp by default so this may need to be overruled.
        # The panel dictionary default is to give a value of 0, which turns off this padding.
        # An example of the use of this is for STG BrCa who require padding of +/- 11bp (bed files are padded +/-10bp) so 1bp padding is applied.
        mokapipe_padding_cmd = config.mokapipe_haplotype_padding_input + str(
            self.panel_dictionary[pannumber][
                "mokapipe_haplotype_caller_padding"
            ]
        )

        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.mokapipe_filter_vcf_with_bedfile_bed_input
                + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # if sample is not NA12878 we want to skip the vcfeval stage (the app default is skip=false).
        # assume it's not a NA12878 sample, and set skip = true
        vcf_eval_skip_string = config.mokapipe_happy_skip % ("true")
        # set the prefix as the samplename
        vcf_eval_prefix_string = config.mokapipe_happy_prefix % (fastqs[2])

        # identify NA12878 samples by checking if any reference ids (flanked by underscores) are present in the fastq name
        # if so, set skip = false
        for id in config.reference_sample_ids:
            if "_%s_" % (id) in fastq:
                vcf_eval_skip_string = config.mokapipe_happy_skip % ("false")

        # Set parameters specific to FH_PRS app
        FH_prs_bedfile_cmd = (
            config.mokapipe_fhPRS_bedfile_input + bedfiles["fh_prs"]
        )
        FH_prs_cmd_string = ""

        if self.panel_dictionary[pannumber]["FH"]:
            # If sample is R134 we want app to run - set skip to false
            # Specify instance type for human exome app and specify output as both vcf and gvcf
            FH_prs_cmd_string += config.mokapipe_fhPRS_skip
            FH_prs_cmd_string += " --instance-type %s=%s" % (
                config.mokapipe_gatk_human_exome_stage,
                config.mokapipe_FH_humanexome_instance_type,
            )
            FH_prs_cmd_string += config.mokapipe_haplotype_vcf_output_format
            FH_prs_cmd_string += config.mokapipe_FH_GATK_timeout_args

        # Set parameters specific to polyedge app
        polyedge_cmd_string = ""

        if self.panel_dictionary[pannumber]["polyedge"]:
            gene = self.panel_dictionary[pannumber]["polyedge"]

            polyedge_cmd_string += config.polyedge_str.format(
                gene,
                config.polyedge_inputs[gene]["chrom"],
                config.polyedge_inputs[gene]["poly_start"],
                config.polyedge_inputs[gene]["poly_end"],
            )

        masked_reference_command = ""
        if self.panel_dictionary[pannumber]["masked_reference"]:
            masked_reference_command += config.mokapipe_bwa_ref_genome % (
                self.panel_dictionary[pannumber]["masked_reference"]
            )

        # Create the dx command
        dx_command = (
            self.mokapipe_command
            + fastqs[2]
            + config.mokapipe_fastqc
            + fastqs[0]
            + config.mokapipe_fastqc
            + fastqs[1]
            + config.mokapipe_bwa_reads
            + fastqs[0]
            + config.mokapipe_bwa_reads2
            + fastqs[1]
            + config.mokapipe_bwa_rg_sample
            + fastqs[2]
            + config.mokapipe_sambamba_bed_input
            + bedfiles["sambamba"]
            + config.mokapipe_sambamba_min_base_qual
            + config.mokapipe_sambamba_min_mapping_qual
            + config.mokapipe_sambamba_coverage_level
            + config.mokapipe_sambamba_filter_cmds
            + config.mokapipe_sambamba_exclude_duplicates
            + config.mokapipe_sambamba_exclude_failed_qual
            + config.mokapipe_sambamba_count_overlapping_mates
            + vcf_eval_skip_string
            + vcf_eval_prefix_string
            + FH_prs_cmd_string
            + FH_prs_bedfile_cmd
            + polyedge_cmd_string
            + masked_reference_command
            + config.mokapipe_mokapicard_vendorbed_input
            + bedfiles["hsmetrics"]
            + config.mokapipe_mokapicard_capturetype_stage
            % (self.panel_dictionary[pannumber]["capture_type"])
            + mokapipe_padding_cmd
            + bedfiles_string
            + self.dest
            + self.dest_cmd
            + self.token
        )

        return dx_command

    def build_congenica_command_file(self):
        """
        Inputs = None
        Create the file which will hold congenica commands.
        Write the source command, activating the environment (the sdk).
        Returns = None
        """
        with open(
            self.congenica_upload_command_script_path, "w"
        ) as congenica_script:
            congenica_script.write(self.source_command + "\n")
            congenica_script.write(self.empty_depends + "\n")

    def build_congenica_input_command(self):
        """
        Inputs = None
        congenica import app is outside out of the workflow.
        Inputs to the import can be provided in the format jobid.output name.
        Each workflow has a analysis-id so further steps are required to obtain the required job-id.
        A python script is run after each dx run command, taking the analysis id, project name and
        decision support tool and prints the required input to command line
        Returns = command for this python program (string)
        """
        # $jobid is a bash variable which will be populated by when run on the command line
        # The python script has three inputs - the analysisID ($jobid), -t is the DSS and -p is the
        # DNA Nexus project the analysis is running in
        dx_command = "%s $jobid -t congenica -p %s)" % (
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
            config.mokaamp_bwa_rg_sample,
            fastqs[2],
            config.mokaamp_mokapicard_bed_stage,
            bedfiles["hsmetrics"],
            config.mokaamp_mokapicard_capturetype_stage,
            self.panel_dictionary[pannumber]["capture_type"],
            config.mokaamp_ampliconfilter_BEDPE_stage,
            bedfiles["mokaamp_bed_PE_input"],
            config.mokaamp_chanjo_cov_level_stage,
            self.panel_dictionary[pannumber]["clinical_coverage_depth"],
            config.mokaamp_mpileup_cov_level_stage,
            self.panel_dictionary[pannumber]["clinical_coverage_depth"],
            config.mokaamp_sambamba_bed_stage,
            bedfiles["sambamba"],
            config.mokaamp_vardict_bed_stage,
            bedfiles["mokaamp_variant_calling_bed"],
            config.mokaamp_varscan_bed_stage,
            bedfiles["mokaamp_variant_calling_bed"],
            config.mokaamp_varscan_strandfilter_stage,
            self.panel_dictionary[pannumber]["mokaamp_varscan_strandfilter"],
            config.mokaamp_bwa_reference_stage,
            config.mokaamp_vardict_samplename_stage,
            fastqs[2],
            config.mokaamp_varscan_samplename_stage,
            fastqs[2],
            config.mokaamp_mokapicard_reference_stage,
            config.mokaamp_vardict_reference_stage,
            config.mokaamp_varscan_reference_stage,
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
        Pan numbers are used to distinguish between samples analysed in congenica or in ingenuity.
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
                rpkm_analysis_list += self.panel_dictionary[pannumber][
                    "RPKM_also_analyse"
                ]

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

        # Samples with different pannumbers can be included in the same RPKM analysis (defined in config).
        # The app takes these pan numbers as a string, and will seperate on commas to identify multiple pan numbers
        string_of_pannumbers_to_analyse = ",".join(
            set(self.panel_dictionary[pannumber]["RPKM_also_analyse"])
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
            + self.depends_gatk
            + self.token
        )
        return dx_command

    def run_congenica_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample
        The import congenica app takes inputs in the format jobid.outputname which ensures the job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        The panel dictionary in the config file is used to determine the congenica project, IR template and credentials file
        This command is appended to a file which will be run after the QC is passed.
        Returns = dx run command for congenica import app (string)
        """
        # check if any reference ids (flanked by underscores) are present in the fastq name and if so skip this step
        for id in config.reference_sample_ids:
            if "_%s_" % (id) in fastq:
                self.loggers.script.info(
                    "UA_pass 'NA12878 sample detected, not building congenica upload command for {}'".format(
                        fastq
                    )
                )
                return None

        # the nexus_fastq_paths function returns paths to the fastq files in Nexus and the sample name
        # The samplename (fastqs[2]) is used to name the job
        fastqs = self.nexus_fastq_paths(fastq)

        dx_command = (
            self.congenica_upload_command
            + "' $analysisid ' -icongenica_project="
            + self.panel_dictionary[pannumber]["congenica_project"]
            + " -icredentials="
            + self.panel_dictionary[pannumber]["congenica_credentials"]
            + " -iIR_template="
            + self.panel_dictionary[pannumber]["congenica_IR_template"]
            + " --name "
            + "congenica_"
            + fastqs[2]
            + config.congenica_samplename
            + fastqs[2]
            + self.dest
            + self.dest_cmd
            + self.token.replace(")", self.congenica_upload_command_redirect)
        )
        return dx_command

    def run_congenica_SFTP_upload_command(self, fastq):
        """
        Input = R1 fastq file name
        The import congenica SFTP app takes inputs in the format jobid.outputname which ensures the job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        Upload via SFTP only required the bam and vcf inputs, and does not need projectids, IR templates or names
        This command is appended to a file which will be run after the QC is passed.
        Returns = dx run command for congenica import app (string)
        """
        # check if any reference ids (flanked by underscores) are present in the fastq name and if so skip this step
        for id in config.reference_sample_ids:
            if "_%s_" % (id) in fastq:
                self.loggers.script.info(
                    "UA_pass 'NA12878 sample detected, not building congenica upload command for {}'".format(
                        fastq
                    )
                )
                return None

        # the nexus_fastq_paths function returns paths to the fastq files in Nexus and the sample name
        # The samplename (fastqs[2]) is used to name the job
        fastqs = self.nexus_fastq_paths(fastq)

        dx_command = (
            self.congenica_sftp_upload_command
            + "' $analysisid '"
            + " --name "
            + "congenica_SFTP_upload_"
            + fastqs[2]
            + self.dest
            + self.dest_cmd
            + self.token.replace(")", self.congenica_upload_command_redirect)
        )
        return dx_command

    def add_to_depends_list(self, fastq, depends_type):
        """
        Input = fastq file
        As jobs are set off the jobid is captured
        The job ids are built into a string which can be passed to any apps to ensure these jobs
        don't start until all specified jobs have sucessfully completed.
        However, some jobs should be excluded from the depends list, eg negative controls
        Returns = command which adds jobid to the bash string (string)
        """
        ntcon_strings = ["00000", "NTCcon", "NTC000", "NC000"]
        if any(identifier in fastq for identifier in ntcon_strings):
            return None
        elif depends_type=='depends_list':
            return self.depends_list
        elif depends_type=='depends_list_gatk':
            return self.depends_list_gatk
        elif depends_type=='depends_list_recombined':
            return self.depends_list_recombined
        elif depends_type=='depends_list_ED_readcount':
            return self.depends_list_ED_readcount

    def create_multiqc_command(self):
        """
        Input = None
        MultiQC is run at the very end of the run, after all QC tools have been run.
        MultiQC requires a project to download data from, and a coverage level.
        The coverage level differs between panels. The lowest value for the panels on this run is used.
        Returns = dx run command (string)
        """
        # set super high coverage level
        lowest_coverage_level = 100000
        # for each fastq to be processed
        for fastq in self.list_of_processed_samples:  # take read one
            if re.search(r"_R1_", fastq) or fastq.startswith("TSO"):
                # extract_Pan number and use this to determine which coverage level is required
                pannumber = re.search(r"Pan\d+", fastq).group()
            # if the required coverage for this panel is less than current value of lowest_coverage_level
            # set lowest_coverage_level to this level
                if (
                    int(
                        self.panel_dictionary[pannumber][
                            "multiqc_coverage_level"
                        ]
                    )
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

    def create_upload_multiqc_command(self, TSO500):
        """
        Input = None
        The input to the upload_multiqc app is the html_report output of the multiqc app, in the format jobid:output_name
        Returns = dx run command for the upload_multiqc app (string)
        """
        if TSO500:
            multiqc_data_input = (" -imultiqc_data_input=%s:/%s/*%s%s" %
                (self.runfolder_obj.nexus_project_name,
                self.runfolder_subdir,
                self.runfolder_obj.runfolder_name,
                config.cluster_density_file_suffix)
            )
        else:
            multiqc_data_input = (
                " -imultiqc_data_input=%s:/QC/*%s%s" %
                (self.runfolder_obj.nexus_project_name,
                self.runfolder_obj.runfolder_name,
                config.cluster_density_file_suffix)
            )

        dx_command = "".join(
            [
                self.upload_multiqc_command,
                " -imultiqc_html=$jobid:multiqc_report",
                " -imultiqc_data_input=$jobid:multiqc",
                multiqc_data_input,
                self.project,
                self.runfolder_obj.nexus_project_id,
                self.depends,
                self.token,
            ]
        )
        return dx_command

    def create_duty_csv_command(self):
        """
        Input = None
        The input to the duty_csv app is the pan numbers
         app is the html_report output of the multiqc app, in the format jobid:output_name
        Returns = dx run command for the upload_multiqc app (string)
        """
        dx_command = (
            " ".join(
                [
                    self.duty_csv_command,
                    "-iproject_name=%s"
                    % self.runfolder_obj.nexus_project_name,
                    config.duty_csv_inputs["tso_pannumbers"],
                    config.duty_csv_inputs["stg_pannumbers"],
                    config.duty_csv_inputs["cp_capture_pannos"],
                ]
            )
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token
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

    def write_dx_run_cmds(self, command_list):
        """
        Input = list of commands
        Takes a list of commands generated by start_building_dx_run_cmds and writes them to file.
        Returns = None
        """
        self.loggers.script.info("Writing dx run commands")

        with open(
            self.runfolder_obj.runfolder_dx_run_script, "w"
        ) as dxrun_commands:
            # remove any None values from the command_list
            dxrun_commands.writelines(
                [line + "\n" for line in filter(None, command_list)]
            )

    def clean_stderr(self, err):
        """
        Input = stderror (string)
        Currently have a conflict between packages from different python instances.
        This function parses stderr to remove these so real error messages stand out
        This function can be removed after the conflict is sorted
        Returns = lines of stderror not including expected messages (list)
        """
        std_err_ignore_match = (
            r"/usr/local/lib/python2.7/dist-packages/urllib3/util/ssl_.py:"
        )
        sni_warning_ignore_match = r"SNIMissingWarning"
        cleaned_error = []
        for line in err.split("\n"):
            clean_line = line.rstrip()
            # If the line doesn't contain a string that should be ignored
            if (
                not re.match(std_err_ignore_match, clean_line)
                and not re.search(sni_warning_ignore_match, clean_line)
                and len(clean_line) > 0
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
                        self.runfolder_obj.runfolder_name,
                        "\n".join(cleaned_error),
                    )
                )

        else:
            # write error message to log file
            self.loggers.script.info(
                "UA_pass 'dx run commands issued without error for run {}'".format(
                    self.runfolder_obj.runfolder_name
                )
            )

    def write_opms_queries_custom_panel(self):
        """
        Input = list of fastqs to be processed
        Samples processed using Mokapipe are recorded in Moka using an insert query.
        This function will create an insert query for each sample processed through mokapipe.
        If mokapipe samples are found this function will return a dictionary of sample counts, and a
        list of queries to be added to global dictionary.
        Returns = dictionary or None
        """
        queries = []
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                query = "insert into NGSCustomRuns(DNAnumber,PipelineVersion, RunID) values ('{}','{}','{}')"
                # if the pan number was processed using mokapipe and congenica, add the query to list of queries, capturing the DNA number from the fastq name
                if (
                    self.panel_dictionary[pannumber]["mokapipe"]
                    and self.panel_dictionary[pannumber]["congenica_upload"]
                ):
                    queries.append(
                        query.format(
                            str(fastq.split("_")[2]),
                            config.mokapipe_congenica_pipeline_ID,
                            self.runfolder_obj.runfolder_name,
                        )
                    )

        if queries:
            # add workflow to sql dictionary
            return {"count": len(queries), "query": queries}
        else:
            return None

    def write_opms_queries_mokawes(self):
        """
        Input = list of fastqs to be processed
        All samples processed using MokaWES are recorded in moka using a single update query.
        If MokaWES samples - Function populates a dictionary of sample counts, query (str) and list of samplenames to
        be added to global dictionary.
        Returns = dictionary or None
        """
        dnanumbers = []
        samplenames = []
        # add workflow to sql dictionary
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                # if the pan number was processed using mokawes add the query to list of queries,
                # capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokawes"]:
                    dnanumbers.append(str(fastq.split("_")[2]))
                    # call function to build nexus fastq paths - returns tuple for read1 and read2 and samplename
                    samplenames.append(self.nexus_fastq_paths(fastq)[2])
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
                "samplename_email": samplenames,
            }
        else:
            return None

    def write_opms_queries_mokasnp(self):
        """
        Input = list of fastqs to be processed
        Samples processed using MokaSNP are recorded in Moka using an insert query.
        This function will create an insert query for each sample processed through MokaSNP.
        If SNP genotyping samples are found this function will return a dictionary of sample counts, and a
        list of queries to be added to global dictionary.
        Returns = dictionary or None
        """
        queries = []
        for fastq in self.list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                query = "insert into NGSCustomRuns(DNAnumber,PipelineVersion, RunID) values ('{}','{}','{}')"
                # if the pan number was processed using mokapipe and congenica, add the query to list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["mokasnp"]:
                    queries.append(
                        query.format(
                            str(fastq.split("_")[2]),
                            config.mokasnp_pipeline_ID,
                            self.runfolder_obj.runfolder_name,
                        )
                    )

        if queries:
            # add workflow to sql dictionary
            return {"count": len(queries), "query": queries}
        else:
            return None

    def write_opms_queries_oncology(self):
        """
        Input = list of fastqs to be processed
        Samples tested using mokaamp or mokaonc are not booked into Moka until the analysis stage so
        create a query using IDs form the samplename
        An insert query is build for each sample, recording the IDs which are the 3rd and 4th elements in the samplename.
        These are recorded along with the pipeline version and the name of the run.
        If not a None object is returned
        Return = dictionary
        """
        queries = []
        workflows = []
        # loop through fastqs to see which workflows were used
        for fastq in self.list_of_processed_samples:
            # take read one
            # example fastq names: ONC20085_08_EK20826_2025029_SWIFT57_Pan2684_S8_R2_001.fastq.gz and ONC20085_06_NTCcon1_SWIFT57_Pan2684_S6_R1_001.fastq.gz
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                # record id1 and 2 by taking the second and third elements
                id1, id2 = fastq.split("_")[2:4]
                # negative controls only have one ID so set id2 to null
                if "NTCcon" in fastq:
                    id2 = "NULL"
                # define query with placeholders
                query = "insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid) values ('{}','{}','{}','{}','{}')"

                # for mokaamp and mokaonc if relevant build the query, populating the placeholders.
                # add the name of the workflow to the list of workflows
                if self.panel_dictionary[pannumber]["mokaamp"]:
                    queries.append(
                        query.format(
                            id1,
                            id2,
                            self.runfolder_obj.runfolder_name,
                            config.mokaamp_pipeline_ID,
                            pannumber.replace("Pan", ""),
                        )
                    )
                    workflows.append(config.mokaamp_path.split("/")[-1])
                if self.panel_dictionary[pannumber]["archerdx"]:
                    queries.append(
                        query.format(
                            id1,
                            id2,
                            self.runfolder_obj.runfolder_name,
                            config.archerDx_pipeline_ID,
                            pannumber.replace("Pan", ""),
                        )
                    )
                    workflows.append(config.fastqc_app.split("/")[-1])
        # if queries have been created return a dictionary
        if queries:
            # use queries list to create a count of samples, return list of queries and the set of the workflows (removing duplicates)
            return {
                "count": len(queries),
                "query": queries,
                "workflows": set(workflows),
            }
        else:
            return None

    def write_opms_queries_TSO500(self):
        """
        Input = list of samples to be processed
        Samples tested using TSO500
        An insert query is build for each sample, recording the IDs which are the 3rd and 4th elements in the samplename.
        These are recorded along with the pipeline version and the name of the run.
        If not a None object is returned
        Return = dictionary
        """
        queries = []
        workflows = []
        query = "insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid) values ('{}','{}','{}','{}','{}')"

        # loop through fastqs to see which workflows were used
        for sample in self.list_of_processed_samples:
            # extract_Pan number
            pannumber = re.search(r"Pan\d+", sample).group()
            if self.panel_dictionary[pannumber]["TSO500"]:
                # record id1 and 2 by taking the second and third elements
                id1, id2 = sample.split("_")[2:4]
                # define query with placeholders
                queries.append(
                    query.format(
                        id1,
                        id2,
                        self.runfolder_obj.runfolder_name,
                        config.TSO_pipeline_ID,
                        pannumber.replace("Pan", ""),
                    )
                )
                workflows.append(config.tso500_app_name)
        # if queries have been created return a dictionary
        if queries:
            # use queries list to create a count of samples, return list of queries and the set of the workflows (removing duplicates)
            return {
                "count": len(queries),
                "query": queries,
                "workflows": set(workflows),
            }
        else:
            return None

    def send_opms_queries(self):
        """
        Input = None
        Queries to record the pipeline versions are emailed.
        This function sends emails, using the queries written to self.sql_queries by the various test specific functions.
        Oncology and rare disease emails are sent seperately and independantly of each other.
        Returns = None
        """
        # email body template - has the following requires following format:
        # {config.test_email_header} {self.runfolder_obj.runfolder_name} being processed using workflow(s) {",".join(self.sql_queries["oncology"]["workflows"])}\n\n{sql_string}\n{"\n".join(self.sql_queries["oncology"]["query"])}\n
        #
        #  eg
        #   AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. PLEASE IGNORE THIS EMAIL (config.test_email_header - can be empty string)
        #   999999_M02353_0496_000000000-D8M36_SWIFT being processed using workflow(s) MokaAMP_v2.2 (self.runfolder_obj.runfolder_name ... ",".join(self.sql_queries["oncology"]["workflows"]) )
        #   Please update Moka using the below queries and ensure that 10 records are updated: (sql string - This can change - is different for the email to users who don't need the sql queries)
        #   insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid) values ('NTCcon','NULL','999999_M02353_0496_000000000-D8M36_SWIFT','4851','4081') (sql queries - can be empty string for users who don't need these)

        sql_email_message = (
            "{} {} being processed using workflow(s) {}\n\n{}\n{}\n"
        )

        # send oncology email first
        if self.sql_queries["oncology"]:
            email_subject = "MOKA ALERT: Started pipeline for {}".format(
                self.runfolder_obj.runfolder_name
            )
            email_priority = 1  # high priority
            # populate the sql_string needed to fill the email_message
            sql_string = "Please update Moka using the below queries and ensure that {} records are updated:\n\n".format(
                str(self.sql_queries["oncology"]["count"])
            )
            email_message = sql_email_message.format(
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["oncology"]["workflows"]),
                sql_string,
                "\n".join(self.sql_queries["oncology"]["query"]),
            )
            # send email - if needed, pass multiple recipients in a list (no longer needed)
            self.send_an_email(
                config.you, email_subject, email_message, email_priority
            )

            # email_for_cancer_ops leads to inform the pipeline has started
            # set sql_string for the email message
            sql_string = "{} samples are being processed".format(
                str(self.sql_queries["oncology"]["count"])
            )
            # fill template using empty string in place of sql queries
            email_message = sql_email_message.format(
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["oncology"]["workflows"]),
                sql_string,
                "",
            )
            self.send_an_email(
                config.oncology_you,
                email_subject,
                email_message,
                email_priority,
            )

        # Send TSO500 queries
        if self.sql_queries["TSO500"]:
            email_subject = "MOKA ALERT: Started pipeline for {}".format(
                self.runfolder_obj.runfolder_name
            )
            email_priority = 1  # high priority
            sql_string = "Please update Moka using the below queries and ensure that {} records are updated:\n\n".format(
                str(self.sql_queries["TSO500"]["count"])
            )
            email_message = sql_email_message.format(
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["TSO500"]["workflows"]),
                sql_string,
                "\n".join(self.sql_queries["TSO500"]["query"]),
            )
            # send email
            self.send_an_email(
                config.you, email_subject, email_message, email_priority
            )

        # build rare disease emails
        # Start counters and placeholders to for email data
        workflows = []
        sql_statements = []
        count = 0

        # for each pipeline take queries, sample count and workflow name
        if self.sql_queries["custom_panel"]:
            workflows.append(config.mokapipe_path.split("/")[-1])
            sql_statements += self.sql_queries["custom_panel"]["query"]
            count += self.sql_queries["custom_panel"]["count"]
        if self.sql_queries["mokawes"]:
            workflows.append(config.mokawes_path.split("/")[-1])
            sql_statements += self.sql_queries["mokawes"]["query"]
            count += self.sql_queries["mokawes"]["count"]
        if self.sql_queries["mokasnp"]:
            workflows.append(config.mokasnp_path.split("/")[-1])
            sql_statements += self.sql_queries["mokasnp"]["query"]
            count += self.sql_queries["mokasnp"]["count"]

        # send email
        if workflows and sql_statements:
            # email this query
            email_subject = "MOKA ALERT: Started pipeline for {}".format(
                self.runfolder_obj.runfolder_name
            )
            email_priority = 1  # high priority
            sql_string = "Please update Moka using the below queries and ensure that {} records are updated:\n\n".format(
                str(count)
            )
            email_message = sql_email_message.format(
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(set(workflows)),
                sql_string,
                "\n".join(sql_statements),
            )
            # send email
            self.send_an_email(
                config.you, email_subject, email_message, email_priority
            )

        if self.sql_queries["mokawes"]:
            # send email to WES team to help IR upload
            email_subject = "MOKA ALERT: Started pipeline for {}".format(
                self.runfolder_obj.runfolder_name
            )
            sql_string = "The following samples are being processed:\n"
            email_message = sql_email_message.format(
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                config.mokawes_path.split("/")[-1],
                sql_string,
                "\n".join(self.sql_queries["mokawes"]["samplename_email"]),
            )
            self.send_an_email(
                config.WES_sample_name_email_list,
                email_subject,
                email_message,
                email_priority,
            )

    def upload_rest_of_runfolder(self):
        """
        Input = None
        The rest of the runfolder requires backing up, excluding bcl files. BCL files are uploaded for TSO runs only.
        A python script which is a wrapper for the upload agent is used.
        This function copies the samplesheet from into the runfolder and then builds and executes
        the backup_runfolder.py command
        Returns = filepath to backup script.
        """
        # try to copy samplesheet into project
        if os.path.exists(self.runfolder_obj.runfolder_samplesheet_path):
            copyfile(
                self.runfolder_obj.runfolder_samplesheet_path,
                os.path.join(
                    self.runfolder_obj.runfolderpath,
                    self.runfolder_obj.runfolder_samplesheet_name,
                ),
            )
            self.loggers.script.info(
                "Samplesheet copied to runfolder: {}".format(
                    self.runfolder_obj.runfolder_samplesheet_name
                )
            )
        else:
            self.loggers.script.info("Samplesheet not copied to runfolder")

        # build backup_runfolder.py command for TSO run
        if self.check_for_TSO500():
            cmd = (
                "python3 "
                + config.backup_runfolder_script
                + " -i "
                + self.runfolder_obj.runfolderpath
                + " -p "
                + self.runfolder_obj.nexus_project_name
                + " --ignore DNANexus_upload_started,add_runfolder_to_nexus_cmds --logpath "
                + config.backup_runfolder_logfile
                + " -a "
                + config.Nexus_API_Key
            )
        else:
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
        self.loggers.script.info(
            "Uploading rest of run folder to Nexus using backup_runfolder.py"
        )
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
        Returns = filepath to the logfile containing output from the command, string of files to be uploaded and name of the stage to test
        """
        # define where files to be uploaded to
        nexus_upload_folder = ("/%s/Logfiles/" % ("_".join(self.runfolder_obj.nexus_project_name.split("_")[1:])))
        # create a list of files to be used to check outputs
        files_to_upload_list = []
        # create a space delimited string of files to be uploaded defined by the logger class
        files_to_upload_string = ""
        for logger in self.loggers.all:
            if logger.filepath:
                files_to_upload_string += "'"
                files_to_upload_string += logger.filepath
                files_to_upload_string += "' "
                # add to the list
                files_to_upload_list.append(logger.filepath)

        # add the demultiplexing log file
        files_to_upload_string += (
            " '"
            + os.path.join(
                self.runfolder_obj.runfolderpath, config.file_demultiplexing
            )
            + "'"
        )
        files_to_upload_list.append(
            os.path.join(
                self.runfolder_obj.runfolderpath, config.file_demultiplexing
            )
        )
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
            " --do-not-compress ",
            files_to_upload_string,
        ]
        # convert list to command line and append the logfile list
        cmd = " ".join(command_list)

        # write these commands to the upload agent logfile before upload.
        self.loggers.script.info("Uploading logfiles.")
        self.loggers.script.info(cmd)

        # execute ua command
        out, err = self.execute_subprocess_command(cmd)

        # capture stdout to upload agent log file AND the script logfile
        self.loggers.script.info(
            "Uploading logfiles (this will not be included in DNANexus)"
        )
        self.loggers.script.info(out)
        self.loggers.script.info(err)
        self.loggers.upload_agent.info(out)
        self.loggers.upload_agent.info(err)
        # TODO check correct logfile is being checked
        return (
            self.loggers.upload_agent.filepath,
            files_to_upload_list,
            "log files",
        )

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
        return upload_ok

    def execute_subprocess_command(self, command):
        """
        Input = command (string)
        Takes a command, executes using subprocess.Popen
        Returns =  (stdout,stderr) (tuple)
        """

        proc = subprocess.Popen(
            [command],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            shell=True,
            executable="/bin/bash",
        )

        # capture the streams
        return proc.communicate()

    def send_an_email(
        self, to, email_subject, email_message, email_priority=3
    ):
        """
        Input = email address, email_subject, email_message, email_priority (optional, default = standard priority)
        Uses smtplib to send an email.
        Returns = None
        """
        # write to logfile
        self.loggers.script.info(
            "UA_pass Email being composed: Recipient: {}. Subject: {}. Body:\n{}".format(
                str(to), email_subject, email_message
            )
        )

        # create message object
        m = Message()
        # set priority
        m["X-Priority"] = str(email_priority)
        # set subject
        m["Subject"] = email_subject
        # set body
        m.set_payload(email_message)

        try:
            # server details
            server = smtplib.SMTP(
                host=config.host, port=config.port, timeout=10
            )
            server.set_debuglevel(
                False
            )  # verbosity turned off - set to true to get debug messages
            server.starttls()
            server.ehlo()
            server.login(config.user, config.pw)
            server.sendmail(config.me, to, m.as_string())

            # write to logfile
            self.loggers.script.info("UA_pass Email sent without error")
        except:
            # write to logfile
            self.loggers.script.info(
                "UA_fail Error when attempting to send email"
            )


if __name__ == "__main__":
    # Create a custom list object to hold sequencing runs
    runs = SequencingRuns()
    # Set list with runfolder objects
    runs.set_runfolders()
    # Call upload and workflow logic on runfolders
    runs.loop_through_runs()
