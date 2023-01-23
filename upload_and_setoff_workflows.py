#!/usr/bin/python2
"""upload_and_setoff_workflows.py

Upload NGS data to DNANexus and trigger analysis workflows.
"""
import datetime
import os
import re
import subprocess
from shutil import copyfile
import ad_config as config
from git_tag.git_tag import git_tag  # Import function which reads the git tag
import ad_logger.ad_logger as ad_logger
import panel_config
from ad_email.ad_email import AdEmail


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
        self.now = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
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
            folder_exists = os.path.isdir(os.path.join(config.runfolders, folder))
            if (
                folder not in config.ignore_dirs
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
            # Close down the run folder specific logger handles
            runfolder_instance.loggers.shutdown_logs()

        # Add names of any processed runfolders to logfile
        if processed_runfolders:
            original_logfile_path = os.path.join(
                config.upload_script_logpath,
                f"{self.now}_upload_and_setoff_workflow.log",
            )
            processed_runfolders_str = "_".join(processed_runfolders)
            new_logfile = original_logfile_path.replace(
                self.now, f"{self.now}_{processed_runfolders_str}"
            )
            os.rename(original_logfile_path, new_logfile)


class RunfolderObject(object):
    """
    An object with runfolder specific properties.
    """

    def __init__(self, runfolder):
        # Set empty variables to be defined based on the run
        self.runfolder_name = runfolder
        self.runfolderpath = os.path.join(config.runfolders, runfolder)
        # Project fastq folder
        self.fastq_dir_path = os.path.join(self.runfolderpath, config.fastq_dir)
        # Runfolder dx run commands
        self.runfolder_dx_run_script = os.path.join(
            config.dnanexus_workflow_logfolder, "{runfolder_name}_dx_run_commands.sh"
        )

        self.congenica_upload_command_script = os.path.join(
            config.dnanexus_workflow_logfolder,
            f"{self.runfolder_name}_" f"congenica_upload_commands.sh",
        )
        self.nexus_project_name = ""
        self.nexus_path = ""
        self.nexus_project_id = ""
        self.runfolder_samplesheet_path = os.path.join(
            config.samplesheet_dir, f"{self.runfolder_name}_SampleSheet.csv"
        )
        self.runfolder_samplesheet_name = f"{self.runfolder_name}_SampleSheet.csv"


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
        # Capture class inputs
        self.debug_mode = debug_mode
        self.runfolder_obj = RunfolderObject(runfolder)
        self.bcl2fastq_logfile = os.path.join(
            self.runfolder_obj.runfolderpath, config.bcl2fastqlog_filename
        )
        self.now = now
        self.fastq_string = ""  # String of fastqs for upload agent
        self.list_of_processed_samples = (
            []
        )  # Fastq list to get NGS run number and WES batch

        # DNA Nexus commands to be built on later

        self.congenica_upload_command = (
            f"echo 'dx run {config.tools_project}{config.congenica_app_path} -y"
        )
        # Create filepath for file to hold congenica command(s)
        self.congenica_upload_command_script_path = os.path.join(
            config.dnanexus_workflow_logfolder,
            f"{self.runfolder_obj.runfolder_name}_congenica.sh",
        )
        # String to redirect command (with variables) into file
        self.congenica_upload_command_redirect = (
            f"' >> {self.congenica_upload_command_script_path}"
        )
        # Project to upload run folder into
        self.project_bash_script_path = os.path.join(
            config.dnanexus_projectcreation_logfolder,
            f"{self.runfolder_obj.runfolder_name}.sh",
        )

        self.dest_str = " --dest="
        self.project = " --project="
        self.token = f" --brief --auth-token {config.nexus_apikey})"
        self.depends = " -y $depends_list"

        # Argument to capture jobids
        self.depends_list = 'depends_list="${depends_list} -d ${jobid} "'

        # Command to restart upload agent part 1
        self.restart_ua_1 = "ua_status=1; while [ $ua_status -ne 0 ]; do "
        self.restart_ua_2 = (
            "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo "
            '"temporary issue when uploading file %s"; fi ; done'
        )

        self.panel_dictionary = {}  # self.set_panel_dictionary()
        self.sql_queries = {}

        # Call function which populates a dictionary of run specific logs and logfile paths.
        self.log_config = ad_logger.get_adlogger_config(
            self.runfolder_obj, self.now
        )
        # Pass the dictionary into ADloggers class - ** unpacks this dictionary to populate inputs.
        # This is used as an object where various logs can be written
        self.loggers = ad_logger.ADLoggers(**self.log_config)

        self.email = AdEmail(email_priority=1, logger=self.loggers.script)

    def run_tests(self):
        """
        Inputs = None
        Test the performance of the required software (upload agent and dx toolkit)
        Calls the perform_test function and passes the output of this to functions which assess the
        performance of the software
        Raises exception if any test does not pass
        Returns = None
        """
        self.loggers.script.info("automate_demultiplexing release:%s", git_tag())
        # Call upload agent using perform test function. Pass output to self.test_upload_agent
        if not self.test_upload_agent(
            self.perform_test(
                self.execute_subprocess_command(
                    config.upload_agent_path + config.upload_agent_test_cmd
                )[0],
                "ua",
            )
        ):
            raise Exception("Upload agent not installed")

        # Test dx toolkit installation
        if not self.test_dx_toolkit(
            self.perform_test(
                self.execute_subprocess_command(config.dx_sdk_test)[0], "dx_toolkit"
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
        # Build dictionary of panel settings
        self.panel_dictionary = {}  # self.set_panel_dictionary()

        # Check if already uploaded and demultiplexing finished sucessfully
        if not self.already_uploaded() and self.has_demultiplexed():
            self.calculate_cluster_density(
                self.runfolder_obj.runfolderpath, self.runfolder_obj.runfolder_name
            )
            # tso500 run is not demultiplexed locally - entire runfolder is uploaded
            # Read samplesheet to create a list of samples
            tso500_sample_list = (
                self.check_for_tso500()
            )  # If not tso500 will return None
            if tso500_sample_list:
                (self.list_of_processed_samples,
                 self.fastq_string) = (tso500_sample_list,
                                       self.runfolder_obj.runfolder_samplesheet_path)
            else:
                self.list_of_processed_samples, self.fastq_string = self.find_fastqs(
                    self.runfolder_obj.fastq_dir_path
                )

            if self.list_of_processed_samples:
                # Build project name using WES batch and NGS run numbers
                (
                    self.dest_str,
                    self.runfolder_obj.nexus_path,
                    self.runfolder_obj.nexus_project_name,
                ) = self.build_nexus_project_name(
                    self.capture_any_wes_batch_numbers(self.list_of_processed_samples),
                    self.capture_library_batch_numbers(self.list_of_processed_samples),
                )
                # Create bash script to create and share nexus project - return filepath
                # Pass filepath into module which runs project creation script - capturing projectid
                view_users_list, admin_users_list = self.write_create_project_script(
                    self.list_of_processed_samples
                )
                self.runfolder_obj.nexus_project_id = self.run_project_creation_script(
                    view_users_list, admin_users_list
                ).rstrip()
                # Build upload agent command for fastq upload and write stdout to ua_stdout_log
                # Pass path to function which checks files were uploaded without error
                if tso500_sample_list:
                    backup_attempt_count = 1
                    while backup_attempt_count < 5:
                        self.loggers.script.info("Attempting to backup TSO runfolder. "
                                                 f"attempt {backup_attempt_count}")
                        if self.check_backuprunfolder_errors(self.upload_rest_of_runfolder()):
                            backup_attempt_count = 10
                        else:
                            # increase backup count
                            backup_attempt_count += 1

                self.look_for_upload_errors(self.upload_fastqs())

                # Upload cluster density files and check upload was successful.
                self.look_for_upload_errors(
                    self.upload_cluster_density_files_for_multiqc()
                )
                # Upload bcl2fastq stats files and check upload was successful.
                self.look_for_upload_errors(
                    self.upload_bcl2fastq_qc_files_for_multiqc()
                )

                self.write_dx_run_cmds(
                    self.start_building_dx_run_cmds(self.list_of_processed_samples)
                )
                self.run_dx_run_commands()

                self.sql_queries["mokawes"] = self.write_opms_queries_mokawes(
                    self.list_of_processed_samples
                )
                self.sql_queries["mokaamp"] = self.write_opms_queries_mokaamp(
                    self.list_of_processed_samples
                )
                self.sql_queries["tso500"] = self.write_opms_queries_tso500(
                    self.list_of_processed_samples
                )
                self.sql_queries["custom_panel"] = self.write_opms_queries_custom_panel(
                    self.list_of_processed_samples
                )
                self.sql_queries["mokasnp"] = self.write_opms_queries_mokasnp(
                    self.list_of_processed_samples
                )
                self.send_opms_queries()
                # if not TSO500 will return None
                if not tso500_sample_list:
                    self.check_backuprunfolder_errors(self.upload_rest_of_runfolder())

                self.look_for_upload_errors(self.upload_log_files())
                if tso500_sample_list:
                    self.remove_tso500_tar()

                # return true to denote that a runfolder was processed
                return True
        else:
            self.loggers.script.info(
                "Runfolder has already been processed: %s. Skipping.",
                self.runfolder_obj.runfolder_name,
            )
            return False

    # @staticmethod
    # def set_panel_dictionary():
    #     """
    #     Input = None
    #     Populate the dictionary detailing panel specific settings.
    #     Default settings are set in the config file and then updated as and when required for each
    #     panel the defaults in config file.
    #     Loop through panel specific properties in config file and overwrite any default with panel
    #     specific settings
    #     Returns = dictionary of panel specific settings
    #     """
    #     dictionary_to_return = {}
    #     for panel in panel_config.panel_list:
    #         # Loop through default settings, adding to dictionary. Then loop through panel
    #         # settings from config, overwriting any defaults
    #         dictionary_to_return[panel] = {}
    #         for setting in panel_config.default_panel_properties:
    #             dictionary_to_return[panel][
    #                 setting
    #             ] = panel_config.default_panel_properties[setting]
    #         for setting in panel_config.panel_dict[panel]:
    #             dictionary_to_return[panel][setting] = panel_config.panel_dict[
    #                 panel
    #             ][setting]
    #     return dictionary_to_return

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
            self.loggers.script.info("UA_pass 'Upload Agent function test passed'")
            return True

    def perform_test(self, test_input, test):
        """
        Input = test_input (string) and test_name (str)
        Recieves test name and stdout from execution of command which is performing a test
        Assesses output of test against expected response (as per config)
        Returns =  Boolean (True/False)
        """
        if test == "ua":
            if config.upload_agent_expected_stdout not in test_input:
                return False
        if test == "dx_toolkit":
            if config.dx_sdk_test_expected_stdout not in test_input:
                return False
        if (
            test == "demultiplex_started"
        ):  # False if the demultiplex started file does not exist
            if not os.path.isfile(test_input):
                return False
        if test == "tso500":
            if not re.search(config.demultiplexing_logfile_tso500_msg, test_input):
                return False
        if test == "already_uploaded":
            if not os.path.isfile(
                test_input
            ):  # False if upload file does not exist or empty
                return False
        if (
            test == "demultiplex_success"
        ):  # False if expected string NOT in last line of log file
            if not re.search(config.demultiplex_success_regex, test_input):
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
            self.loggers.script.error("UA_fail 'dx toolkit function test failed'")
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
        # Write to log file including GitHub repo tag and time stamp
        self.loggers.script.info("Working on %s", self.runfolder_obj.runfolderpath)

        # Use perform_test function to assert if the file exists - will return True if file exists
        if self.perform_test(
            os.path.join(
                self.runfolder_obj.runfolderpath, config.upload_started_filename
            ),
            "already_uploaded",
        ):
            self.loggers.script.info("Upload started file present. Terminating.")
            return True
        else:
            # If file doesn't exist return false to continue and write to log file
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
            self.runfolder_obj.runfolderpath, config.bcl2fastqlog_filename
        )
        # Check demultiplexing has been done using perform_test - return true if file present
        if self.perform_test(demultiplex_file_path, "demultiplex_started"):
            with open(demultiplex_file_path, "r", encoding="utf-8") as logfile:
                # Capture logfile into list (not doing this caused an issue with the if loop below)
                logfile_list = logfile.readlines()
                if self.perform_test(logfile_list[-1], "tso500"):  # Check if tso500 run
                    self.loggers.script.info("tso500 run detected.")
                    return True
                # Check if successful demuliplex statement in last line of log
                elif self.perform_test(logfile_list[-1], "demultiplex_success"):
                    self.loggers.script.info("Demultiplex completed succesfully.")
                    return True
                else:
                    # Write to logfile that demultplex was not successful
                    self.loggers.script.info("Demultiplex failed.")
                    return False
        else:
            # Write to logfile that not yet demultiplexed
            self.loggers.script.info("Demultiplex has not been performed.")
            return False

    def check_for_tso500(self):
        """
        Read samplesheet looking for tso500 pan number.
        If tso500 pannumber present add samplename to list
        return sample_list (will return False if empty)
        """
        sample_list = []
        with open(
            self.runfolder_obj.runfolder_samplesheet_path, "r", encoding="utf-8"
        ) as samplesheet_stream:
            # Read file into list and loop through list in reverse
            # Allows us to access sample names and stop at column headers, skipping file header
            for line in reversed(samplesheet_stream.readlines()):
                if line.startswith("Sample_ID") or "[Data]" in line:
                    break
                # Skip empty lines (check first element of the line, after splitting on comma)
                elif len(line.split(",")[0]) < 2:
                    pass
                else:  # If it's a line detailing a sample
                    for pannum in panel_config.tso500_panel_list:
                        if pannum in line:
                            sample_list.append(line.split(",")[0])
        if sample_list:
            # Create file - takes long time before upload creates file to stop further processing
            open(self.loggers.upload_agent.filepath, "w", encoding="utf-8").close()
        return sample_list

    def calculate_cluster_density(self, runfolder_path, runfolder_name):
        """
        Inputs = runfolder name and runfolder path
        Uses a dockerised version of GATK to run picard CollectIlluminaLaneMetrics
        This calculates cluster density and saves files (runfolder.illumina_phasing_metrics and
        runfolder.illumina_lane_metrics) to the runfolder
        If success statement seen in stderr record in log file else raise slack alert but do not
        stop run.
        Returns = None
        """
        # if novaseq need to give an extra flag to CollectIlluminaLaneMetrics
        if config.novaseq_id in runfolder_name:
            novaseq_flag = " --IS_NOVASEQ"
        else:
            novaseq_flag = ""

        # docker command for tool
        cmd = (
            f"sudo docker run --rm -v {runfolder_path}:/input_run broadinstitute/gatk:4.1.8.1 "
            "./gatk CollectIlluminaLaneMetrics "
            "--RUN_DIRECTORY /input_run "
            "--OUTPUT_DIRECTORY /input_run"
            f"--OUTPUT_PREFIX {runfolder_name} {novaseq_flag}"
        )

        # capture stdout and stderr. NB all output from picard tool is in stderr
        (_, err) = self.execute_subprocess_command(cmd)
        # assess stderr , looking for expected success statement
        if self.perform_test(err, "cluster_density"):
            self.loggers.script.info(
                "Cluster density calculation saved to %s",
                runfolder_name + config.cluster_density_file_suffix,
            )
        # raise slack alert if success statement not present.
        else:
            self.loggers.script.error(
                "UA_fail 'Cluster density calculation failed for : %s'",
                self.runfolder_obj.runfolder_name,
            )

    def find_fastqs(self, runfolder_fastq_path):
        """
        Input = path to fastqs in runfolder
        Loops through all the fastq files in the given folder
        Identifies the pan number and checks for presense of this pan number in the dictionary of
        panel settings. If there are any files where the pan number was not found sent an alert.
        Returns = a tuple of list of processed samples and string of fastq filepaths.
        """
        not_processed = []  # Set up list of fastqs not to be processed
        list_of_processed_samples = []
        fastq_string = ""
        for fastq in os.listdir(runfolder_fastq_path):
            # Exclude undetermined and any fastqs created by miseq (seerated by "-" rather than "_")
            if (
                fastq.endswith("fastq.gz")
                and not fastq.startswith("Undetermined")
                and "-Pan" not in fastq
            ):
                pan_match = re.search(r"Pan\d+", fastq)
                if pan_match and (pan_match.group()) in panel_config.panel_list:
                    # Append to string of paths for upload agent
                    fastq_string = (
                        f"{fastq_string} {self.runfolder_obj.fastq_dir_path}/{fastq}"
                    )
                    # Add fastq name to list to be used in create_nexus_file_path
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
                "UA_fail '%s contained an unrecognised pan numbers: %s'",
                self.runfolder_obj.runfolder_name,
                ",".join(not_processed),
            )

        if not list_of_processed_samples:
            self.loggers.script.error("UA_fail 'No known Pan numbers in fastq list'")
            # If no fastqs to be processed return none object rather than empty list
            list_of_processed_samples = None
            fastq_string = None
        else:
            self.loggers.script.info(
                "%s fastqs found", str(len(list_of_processed_samples))
            )

        return (list_of_processed_samples, fastq_string)

    def capture_any_wes_batch_numbers(self, list_of_processed_samples):
        """
        Input = list of samples to be processed
        DNANexus projects are named after the runfolder suffixed with identifiers.
        This function parses samplenames and identifies any WES batch numbers from the samplenames
        If WES batch number(s) are identified, Returns a string to be included in the project name
        If no batch numbers returns None
        Returns = string or None
        """
        wes_numbers = []

        for fastq in list_of_processed_samples:
            if "WES" in fastq:
                # Capture WES batch (WES followed by digits)
                # Optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", fastq).group()
                wes_numbers.append(wesbatch.replace("_", ""))
        if wes_numbers:
            return "_".join(set(wes_numbers))
        else:  # If no wes numbers are found return None instead of empty string
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
        library_batch_numbers = []

        for fastq in list_of_processed_samples:
            if "_" in fastq:  # Check there are underscores present
                # Split on underscores to capture library_batch number. eg ONC100 or NGS100
                library_batch_numbers.append(fastq.split("_")[0])

        # There should always be library batch numbers found - raise error if not
        if library_batch_numbers:
            return "_".join(set(library_batch_numbers))
        else:  # Prompt a slack alert
            self.loggers.script.error(
                "UA_fail '%s - Unable to identify library batch numbers. "
                "Check for underscores in the samplenames.",
                self.runfolder_obj.runfolder_name,
            )
            # Raise exception to stop script
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
        Returns = tuple containing strings for self.dest_str, runfolder_obj.nexus_path and
            runfolder_obj.nexus_project_name
        """
        nexus_path = ""
        nexus_project_name = ""
        if wes_number:  # If WES batch numbers add this into the nexus path
            nexus_path = (
                f"{self.runfolder_obj.runfolder_name}_{library_batch}"
                f"_{wes_number}{config.fastq_dir}"
            )
            nexus_project_name = (
                f"{config.dnanexus_project_prefix}"
                f"{self.runfolder_obj.runfolder_name}_{library_batch}_{wes_number}"
            )
        else:
            nexus_path = (
                f"{self.runfolder_obj.runfolder_name}_{library_batch}{config.fastq_dir}"
            )
            nexus_project_name = (
                f"{config.dnanexus_project_prefix}"
                f"{self.runfolder_obj.runfolder_name}_{library_batch}"
            )

        # Return tuple of string for self.dest_str
        return (nexus_project_name + ":/", nexus_path, nexus_project_name)

    def write_create_project_script(self, list_of_processed_samples):
        """
        Input = list of processed samples
        Once the project name has been defined the project can be created using the DNANexus sdk
        Commands are written to a bash script and executed using subprocess. The project is created
        and shared with users, with varying degrees of access as defined in the config file.
        The list of processed samples is passed, extracting Pan numbers and assessing if the project
        should also be shared with any
        additional dry lab DNANexus accounts.
        This function writes a bash script containing the project creation command
        Return = two lists, one of users shared with view permissions, one with admin
        """
        view_users_list = []
        admin_users_list = []
        # open bash script
        with open(
            self.project_bash_script_path, "w", encoding="utf-8"
        ) as project_script:
            project_script.write(config.source_cmd + "\n")
            project_script.write(
                config.create_project_cmd
                % (
                    config.prod_organisation,
                    self.runfolder_obj.nexus_project_name,
                    config.nexus_apikey,
                )
            )
            # Share project with the nexus users
            for user in config.view_users:  # Give view permissions
                project_script.write(
                    f"dx invite {user} $project_id VIEW --no-email "
                    f"--auth-token {config.nexus_apikey}\n"
                )
                view_users_list.append(user)
            # Give admin permissions - required incase some users are in both lists.
            for user in config.admin_users:
                project_script.write(
                    "dx invite {user} $project_id ADMINISTER --no-email "
                    "--auth-token {config.nexus_apikey}\n"
                )
                admin_users_list.append(user)
            # Some samples are analysed at dry labs. Access to projects should only be given when
            # there is a sample for that dry lab on the run.
            # Create list of Pan numbers in the run
            pannumber_list = set(
                [
                    re.search(r"Pan\d+", sample).group()
                    for sample in list_of_processed_samples
                ]
            )
            # Pull out drylab_dnanexus_ids for pan numbers where this is not None (default = None)
            dry_lab_list = [
                self.panel_dictionary[pannumber]["drylab_dnanexus_id"]
                for pannumber in pannumber_list
                if self.panel_dictionary[pannumber]["drylab_dnanexus_id"]
            ]
            # loop through dry_lab_list sharing project with user with readonly access
            for user in dry_lab_list:
                project_script.write(
                    f"dx invite {user} $project_id VIEW --no-email "
                    f"--auth-token {config.nexus_apikey}\n"
                )
                view_users_list.append(user)
            project_script.write("echo $project_id")  # Capture project id
            return view_users_list, admin_users_list

    def run_project_creation_script(self, view_users_list, admin_users_list):
        """
        Inputs = two lists, one with view permissions, one with admin permissions
        Calls subprocess command executing project creation bash script
        Output of this command is tested to see if it meets the expected pattern
        Records in log file who project has been shared with
        Returns - projectid (if created), False (if debug) or an exception (non-debug)
        """
        cmd = "bash " + self.project_bash_script_path  # Execute script made above
        (out, _) = self.execute_subprocess_command(cmd)

        # If start of project id is in out capture the id and write to logfiles and return
        if "project-" in out:
            # Split std_out on "project" and get the last item to capture the project ID
            projectid = "project" + out.rsplit("project", maxsplit=1)[-1].rstrip()

            self.loggers.script.info(
                "DNA Nexus project %s created and shared (VIEW) to %s",
                self.runfolder_obj.nexus_project_name,
                ",".join(view_users_list),
            )
            self.loggers.script.info(
                "DNA Nexus project %s created and shared (ADMIN) to %s",
                self.runfolder_obj.nexus_project_name,
                ",".join(admin_users_list),
            )
            self.loggers.script.info("Projectid=%s", projectid)
            return projectid
        else:
            self.loggers.script.error("UA_fail 'failed to create project in dna nexus'")
            raise Exception(
                "Unable to create DNA Nexus project"
            )  # Raise exception to stop script

    def upload_fastqs(self):
        """
        Inputs:
            None
        All samples to be processed were identified in find_fastqs() which also created a string of
        filepaths for all fastqs that is required by the upload agent.
        This function can upload fastqs or a tar'd runfolder (tso500) - If fastq's are being
        uploaded upload to subfolder, else upload to root of project
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        Returns:
            filepath to logfile
            file_list (space delimited string of files)
            stage name (string)
        """
        # Test if fastqs are being uploaded - if so, set folder to the expected fastq location.
        upload_folder = ""
        if "fastq.gz" in self.fastq_string:
            upload_folder = self.runfolder_obj.nexus_path

        nexus_upload_command = (
            f"{self.restart_ua_1}{config.upload_agent_path} "
            f"--auth-token {config.nexus_apikey} "
            f"--project {self.runfolder_obj.nexus_project_name} "
            f"--folder /{upload_folder} "
            f"--do-not-compress --upload-threads 10 {self.fastq_string}{self.restart_ua_2}"
        )
        # Log fastq upload command to the upload agent logfile
        self.loggers.upload_agent.info(
            "Fastq upload commands:\n%s", nexus_upload_command
        )
        # write to automated script logfile
        self.loggers.script.info(
            "Uploading fastqs. See commands at %s", self.loggers.upload_agent.filepath
        )
        # Execute upload agent command, write stdout and stderr to DNANexus_upload_started.txt
        out, err = self.execute_subprocess_command(nexus_upload_command)
        self.loggers.upload_agent.info("Uploading fastqs:\n%s\n%s", out, err)
        return self.loggers.upload_agent.filepath, self.fastq_string, "fastq"

    def look_for_upload_errors(self, upload_module_output):
        """
        Inputs :
        A tuple containing:
            path to log file
            file_list = string (space delimited list) or list of files to be uploaded at this stage
            stage = the stage to be included in error report.
        Parse the file containing standard error/standard out from the upload agent.
        For each expected file to be uploaded check the expected upload success statement is present
        If the success statement is absent raise an alert but do not stop script from running
        Returns:
            strings (debug mode only).
        """
        upload_agent_stdout_path, files_to_upload, stage = upload_module_output
        # Check not always required, e.g. when optional files (eg lane metrics) are not created
        # so allow a new stage to be used to skip testing
        if not stage == "skip_upload_error_check":
            issue_list = []  # List to hold files with issues
            for file in files_to_upload:
                upload_ok = False  # Set flag to upload unsuccessful
                # Loop through log file - if line relates to this fastq check, upload was successful
                for line in open(
                    upload_agent_stdout_path, "r", encoding="utf-8"
                ).readlines():
                    if file in line and "was uploaded successfully. Closing..." in line:
                        upload_ok = True
                if not upload_ok:  # If no success statement at end of file
                    issue_list.append(file)
            if issue_list:  # Report back if ok
                self.loggers.script.error(
                    "UA_fail 'upload of %s files failed for run %s'",
                    stage,
                    self.runfolder_obj.runfolder_name,
                )
                self.loggers.script.error(
                    "UA_fail 'following files were not uploaded %s'", issue_list
                )
            # if no error
            else:
                self.loggers.script.info(
                    "UA_pass 'upload of files complete for run %s'",
                    self.runfolder_obj.runfolder_name,
                )

    def upload_cluster_density_files_for_multiqc(self):
        """
        Inputs = None
        Some QC metrics files that are used by multiqc may need to be uploaded before the rest of
        the runfolder to ensure they are included in the report
        This function build an upload agent command for the cluster density files.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        If debug mode the upload agent command is returned without calling
        execute_subprocess_command()
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
        # Check cluster density files exist before trying to upload
        # If they don't the script will fail when trying to upload them
        if all([os.path.isfile(f) for f in file_list]):
            nexus_upload_command = (
                f"{self.restart_ua_1}{config.upload_agent_path} "
                "--auth-token {config.nexus_apikey} "
                f"--project {self.runfolder_obj.nexus_project_name} "
                "--folder /QC--do-not-compress --upload-threads 1 "
                f"{' '.join(file_list)}{self.restart_ua_2}"
            )

            # Log fastq upload command to the upload agent logfile
            self.loggers.upload_agent.info(
                "Upload cluster density commands:\n%s", nexus_upload_command
            )
            # Write to automated script logfile
            self.loggers.script.info(
                "Uploading cluster density files. See commands at %s",
                self.loggers.upload_agent.filepath,
            )

            # Execute upload agent command, write stdout and stderr to DNANexus_upload_started.txt
            out, err = self.execute_subprocess_command(nexus_upload_command)
            self.loggers.upload_agent.info(
                "Uploading cluster density files\n%s\n%s", out, err
            )
            return self.loggers.upload_agent.filepath, file_list, "cluster density"
        # If cluster density files do not exist skip the upload and return a string which skips the
        # look_for_upload_errors checks
        else:
            self.loggers.script.info(
                "UA_pass 'skipping upload of cluster density files - not all files present'"
            )
            return None, None, "skip_upload_error_check"

    def upload_bcl2fastq_qc_files_for_multiqc(self):
        """
        Inputs = None
        Some QC metrics files that are used by multiqc may need to be uploaded before the rest of
        the runfolder to ensure they are included in the report
        This function build an upload agent command for the bcl2fastq stats.json.
        This command is passed to execute_subprocess_command() and all standard error/standard out
        written to a log file. The upload command is written in a way where it is repeated until it
        exits with an exit status of 0.
        Returns filepath to logfile (non-debug)
        """
        # Build nexus upload command
        file_list = [
            str(self.runfolder_obj.runfolderpath)
            + os.path.join(
                str(config.bcl2fastq_stats_path), str(config.bcl2fastq_stats_filename)
            )
        ]
        # Check if files exist before trying to upload
        # If they don't the script will fail when trying to upload them.
        if all([os.path.isfile(f) for f in file_list]):
            nexus_upload_command = (
                self.restart_ua_1
                + config.upload_agent_path
                + " --auth-token "
                + config.nexus_apikey
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
                "Upload bcl2fastq stats file commands:\n%s", nexus_upload_command
            )
            # write to automated script logfile
            self.loggers.script.info(
                "Uploading bcl2fastq stats files. See commands at %s",
                self.loggers.upload_agent.filepath,
            )

            # Execute upload agent command and write stdout + stderr to DNANexus_upload_started.txt
            out, err = self.execute_subprocess_command(nexus_upload_command)
            self.loggers.upload_agent.info(
                "Uploading bcl2fastq stats files\n%s\n%s", out, err
            )
            return self.loggers.upload_agent.filepath, file_list, "bcl2fastq_stats"
        # If cluster density files do not exist skip upload and return string which skips
        # look_for_upload_errors checks
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

        # for sambamba/hs metrics bed file if a different bed file is specified in config file use
        # that, otherwise use the pannumber
        # given bed file could be a pan number or the name of a capture kit
        if self.panel_dictionary[pannumber]["sambamba_bedfile"]:
            bed_dict["sambamba"] = (
                config.tools_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["sambamba_bedfile"]
            )
        else:
            bed_dict["sambamba"] = (
                config.tools_project
                + config.bedfile_folder
                + pannumber
                + "dataSambamba.bed"
            )

        # for sambamba/hs metrics bed file if a different bed file is specified in config file use
        # that, otherwise use the pannumber
        if self.panel_dictionary[pannumber]["hsmetrics_bedfile"]:
            bed_dict["hsmetrics"] = (
                config.tools_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["hsmetrics_bedfile"]
            )
        else:
            bed_dict["hsmetrics"] = (
                config.tools_project + config.bedfile_folder + pannumber + "data.bed"
            )
        # FH
        if self.panel_dictionary[pannumber]["FH"]:
            bed_dict["fh_prs"] = (
                config.tools_project
                + config.bedfile_folder
                + panel_config.FH_PRS_bedfile
            )
        else:
            bed_dict["fh_prs"] = (
                config.tools_project + config.bedfile_folder + pannumber + "data.bed"
            )
        # BED file used for variant calling
        # Given bed file could have same pan number, different pan number, the name of a capture
        # kit or None
        # BED file may not be provided for variant calling
        if self.panel_dictionary[pannumber]["variant_calling_bedfile"]:
            # if bedfile starts with Pan use the Pan123data.bed
            if (
                self.panel_dictionary[pannumber]["variant_calling_bedfile"][0:3]
                == "Pan"
            ):
                bed_dict["variant_calling_bedfile"] = (
                    config.tools_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber]["variant_calling_bedfile"]
                )
            # If bedfile stated is not named with "Pan" don't add "data.bed" - could be the capture
            # design
            else:
                bed_dict["variant_calling_bedfile"] = (
                    config.tools_project
                    + config.bedfile_folder
                    + self.panel_dictionary[pannumber]["variant_calling_bedfile"]
                )
        # if mokawes command to be executed and the variant calling bedfile not in config
        else:
            bed_dict["variant_calling_bedfile"] = None

        # paired end BED file used by primer clipping tool
        bed_dict["mokaamp_bed_PE_input"] = (
                config.tools_project + config.bedfile_folder + pannumber + "_PE.bed"
            )

        #  mokaamp variant callers need the flat file
        bed_dict["mokaamp_variant_calling_bed"] = (
                config.tools_project + config.bedfile_folder + pannumber + "_flat.bed"
            )

        # RPKM bedfile has a different Pan number - defined in the config dictionary
        if self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]:
            bed_dict["rpkm_bedfile"] = (
                config.tools_project
                + config.bedfile_folder
                + self.panel_dictionary[pannumber]["RPKM_bedfile_pan_number"]
                + "_RPKM.bed"
            )
        return bed_dict

    def start_building_dx_run_cmds(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Loop through the list of fastqs, determine the pan number and use this to determine
        which workflow/apps should be run. Each app/workflow command is built by calling the
        relevant function
        When looping through samples flags and lists are used to determine which run wide tasks
        are required
        These run wide commands eg multiqc are built after sample specific commands
        All commands are added to a list.
        Returns = list of commands
        """

        # Update script log file to say what is being done.
        self.loggers.script.info("Building dx run commands")

        # list to hold all commands.
        commands_list = []
        commands_list.append(config.source_cmd)

        # lists/flags for run wide commands
        peddy = False
        congenica_upload = False
        rpkm_list = []  # list for panels needing RPKM analysis
        tso500 = False

        # loop through samples
        for fastq in list_of_processed_samples:

            # take read one - note tso500 sample list are not fastqs so are treated differently
            # (elif below)
            if re.search(r"_R1_", fastq):
                # extract Pan number and use this to determine which dx run commands are needed for
                # the sample
                panel = re.search(r"Pan\d+", fastq).group()
                # The order in which the modules are called here is important to ensure the order
                # of dx run commands is correct. This affects which decision support tool data is
                # sent to.

                # If panel is to be processed using MokaWES
                if self.panel_dictionary[panel]["pipeline"] == "mokawes":
                    # call function to build the MokaWES command and add to command list and
                    # depends list
                    commands_list.append(self.create_mokamokawes_cmd(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))
                    # if sample to be uploaded to congenica there are 2 methods.
                    # if a project id is specified in the config it means it can be uploaded as if
                    # it were a custom panel sample
                    # eg IR does not need patient specific info and can be uploaded using the
                    # upload agent
                    # otherwise if the congenica project is not set it should be uploaded via the
                    # SFTP
                    congenica_upload = True
                    commands_list.append(self.build_congenica_input_command())
                    # if project is specified then upload via upload agent
                    if self.panel_dictionary[panel]["congenica_project"]:
                        commands_list.append(
                            self.run_congenica_command(fastq, panel)
                        )
                    # if project is not specified upload via SFTP
                    else:
                        commands_list.append(
                            self.run_congenica_sftp_upload_command(fastq)
                        )
                    # Set run-wide flags for Peddy and joint variant calling
                    if self.panel_dictionary[panel]["peddy"]:
                        peddy = True

                # If panel is to be processed using mokapipe
                if self.panel_dictionary[panel]["pipeline"] == "mokapipe":
                    # call function to build the Mokapipe command and add to command list and
                    # depends list
                    commands_list.append(self.create_mokapipe_cmd(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))
                    # # Add command for congenica
                    congenica_upload = True
                    commands_list.append(self.build_congenica_input_command())
                    commands_list.append(self.run_congenica_command(fastq, panel))
                    # add panel to RPKM list
                    if self.panel_dictionary[panel]["RPKM_bedfile_pan_number"]:
                        rpkm_list.append(panel)

                # If panel is to be processed using MokaAMP
                if self.panel_dictionary[panel]["pipeline"] == "mokaamp":
                    commands_list.append(self.create_mokaamp_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))

                if self.panel_dictionary[panel]["pipeline"] == "mokacan":
                    commands_list.append(self.create_mokacan_command(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))

                # if panel is to be processed using mokasnp
                if self.panel_dictionary[panel]["pipeline"] == "mokasnp":
                    commands_list.append(self.create_mokasnp_cmd(fastq, panel))
                    commands_list.append(self.add_to_depends_list(fastq))

                if self.panel_dictionary[panel]["pipeline"] == "archerdx":
                    commands_list.append(self.create_archerdx_cmd(fastq, panel, "R1"))
                    commands_list.append(self.add_to_depends_list(fastq))
                    commands_list.append(self.create_archerdx_cmd(fastq, panel, "R2"))
                    commands_list.append(self.add_to_depends_list(fastq))

            elif not re.search(r"_R1_", fastq) and fastq.startswith("TSO"):
                # extract Pan number and use this to determine which dx run commands are needed for
                # the sample
                panel = re.search(r"Pan\d+", fastq).group()

                if self.panel_dictionary[panel]["pipeline"] == "tso500":
                    tso500 = True

        # if there is a congenica upload create the file which will be run manually, once QC is
        # passed.
        if congenica_upload:
            self.build_congenica_command_file()
            # write to logger to create slack alert that there are some congenica files to upload
            self.loggers.script.info(
                "Congenica samples to upload in project %s",
                self.runfolder_obj.nexus_project_name,
            )

        # build run wide commands
        if rpkm_list:
            # Create a set of RPKM numbers for one command per panel
            # pass this list into function which takes into account panels which are to be analysed
            # together and returns a "cleaned_list"
            for rpkm in self.prepare_rpkm_list(set(rpkm_list)):
                commands_list.append(self.create_rpkm_cmd(rpkm))
        if peddy:
            # TODO if custom panels and WES done together currently no way
            # to stop custom panels being analysed by peddy - may cause problems
            commands_list.append(self.run_peddy_cmd())
            # add to depends list so multiqc doesn't start until peddy finishes
            # add_to_depends_list requires a string to determine if it's a negative control and
            # shouldn't be added to depends on string.
            # pass "peddy" to ensure it isn't skipped
            commands_list.append(self.add_to_depends_list("peddy"))

        if tso500:
            # build command for the tso500 app
            commands_list.append(self.create_tso500_cmd(list_of_processed_samples))
            # add_to_depends_list requires a string to determine if it's a negative control and
            # shouldn't be added to depends on string.
            # pass "TSO" to ensure it isn't skipped
            commands_list.append(self.add_to_depends_list("TSO"))
            # build command for the tso500 output parser
            commands_list.append(self.create_tso500_output_parser_cmd())
            # add_to_depends_list requires a string to determine if it's a negative control and
            # shouldn't be added to depends on string.
            # pass "TSO" to ensure it isn't skipped
            commands_list.append(self.add_to_depends_list("TSO"))
        else:
            # don't need to do multiqc commands for tso500
            commands_list.append(self.create_multiqc_cmd())
            commands_list.append(self.create_upload_multiqc_cmd())

        return commands_list

    def create_mokamokawes_cmd(self, fastq, pannumber):
        """
        Input = R1 fastq filename and Pan number for a single sample
        Returns = dx run command for MokaWES workflow (string)
        """
        # Call function to build nexus fastq paths - returns tuple for read1, read2 and samplename
        fastqs = self.nexus_fastq_paths(fastq)
        # build dictionary of pan number specific/relevant bedfile to be used in command
        bedfiles = self.nexus_bedfiles(pannumber)

        # Bedfile to restrict variant calling should be defined in config file, otherwise it's None
        # In the future we may not restrict variant calling using a bed file so support this
        # possible use case
        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.wes_sentieon_targets_bed + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # Create the MokaWES dx command
        dx_command_list = [
            config.mokawes_cmd,
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
            self.dest_str,
            self.token,
        ]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_archerdx_cmd(self, fastq, read):
        """
        Build dx run command, in this case to run fastqc on a single fastq file
        Inputs:
            R1 fastq filename
            Pan number
            read (R1 or R2)
        Returns:
            dx run command for fastqc (string)
        """
        # Call function to build nexus fastq paths - returns tuple for read1, read2 and samplename
        fastqs = self.nexus_fastq_paths(fastq)
        dx_command_list = [
            config.archerdx_cmd,
            fastqs[2],
            " -ireads=",
            fastqs[0].replace("_R1_", f"_{read}_"),
            self.dest_str,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_tso500_cmd(self, list_of_processed_samples):
        """
        Build dx run command for tso500 docker app.
        Will assess if it's a novaseq or not from the runfoldername and if it's a highthroughput
        TSO run (needing a larger instance type)
        Inputs:
            List of samplenames to be processed
        Returns:
            dx run command for tso500 app (string)
        """
        # Is it a novaseq run?
        if config.novaseq_id in self.runfolder_obj.runfolder_name:
            tso500_analysis_options = "--isNovaSeq "
        else:
            tso500_analysis_options = ""

        # get a list of unique pan numbers from samplenames
        pannumber_list = set(
            [
                re.search(r"Pan\d+", sample).group()
                for sample in list_of_processed_samples
            ]
        )
        # capture any pan numbers that are a highthroughput assay
        high_throughput_list = [
            pannumber
            for pannumber in pannumber_list
            if self.panel_dictionary[pannumber]["panel_name"] == "tso500_high_throughput"
        ]
        # if this list is not empty apply high throughput instance type, otherwise use low
        # throughput instance type
        if high_throughput_list:
            instance_type = f" --instance-type {config.tso500_analysis_instance_high_throughput} "
        else:
            instance_type = f" --instance-type {config.tso500_analysis_instance_low_throughput} "

        # build dx run command - inputs are:
        # docker image (from config)
        # runfolder_tar and samplesheet paths (from runfolder_obj class)
        # analysis options eg --isNovaSeq flag
        dx_command_list = [
            config.tso500_cmd,  # ends with --name so supply the runfolder name to name the job
            self.runfolder_obj.runfolder_name,
            config.tso500_docker_image_stage,
            config.tso500_docker_image,
            config.tso500_samplesheet_stage,
            self.runfolder_obj.nexus_project_id
            + ":"
            + self.runfolder_obj.runfolder_samplesheet_name,
            config.tso500_project_name_stage,
            self.runfolder_obj.nexus_project_name,
            config.tso500_analysis_options_stage,
            tso500_analysis_options,
            instance_type,
            self.dest_str,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command

    def create_tso500_output_parser_cmd(self):
        """
        Build dx run command for tso500_output_parser app
        Inputs:
            None
        Returns:
            dx run command for tso500_output_parser app (string)
        """
        # TODO LIMITATION = Pan numbers that require different settings to be applied in downstream
        # tasks will need to be set off in different jobs.
        # This function will need to adapt to this (currently takes settings from the first item in
        # the list of tso500 pan numbers in config.
        # This primarily affects coverage
        tso_pan_num = "Pan4969"
        # build dictionary of pan number specific/relevant bedfile to be used in command
        bedfiles = self.nexus_bedfiles(tso_pan_num)
        dx_command_list = [
            config.tso500_output_parser_cmd,
            self.runfolder_obj.runfolder_name,
            config.tso500_output_parser_project_name_stage,
            self.runfolder_obj.nexus_project_name,
            config.tso500_output_parser_project_id_stage,
            self.runfolder_obj.nexus_project_id,
            config.tso500_output_parser_job_id_stage,
            "$jobid",
            config.tso500_output_parser_coverage_bedfile_id_stage,
            bedfiles["sambamba"],
            config.tso500_output_parser_coverage_app_id_stage,
            config.coverage_app_id,
            config.tso500_output_parser_fastqc_app_id_stage,
            config.fastqc_app_id,
            config.tso500_output_parser_sompy_app_id_stage,
            config.sompy_app_id,
            config.tso500_output_parser_multiqc_app_id_stage,
            config.multiqc_app_id,
            config.tso500_output_parser_upload_multiqc_app_id_stage,
            config.upload_multiqc_app_id,
            config.tso500_output_parser_coverage_commands_stage,
            config.tso500_output_parser_coverage_commands
            % (
                self.panel_dictionary[tso_pan_num]["coverage_min_basecall_qual"],
                self.panel_dictionary[tso_pan_num]["coverage_min_mapping_qual"],
            ),
            config.tso500_output_parser_coverage_level_stage,
            self.panel_dictionary[tso_pan_num]["clinical_coverage_depth"],
            config.tso500_output_parser_multiqc_coverage_level_stage,
            self.panel_dictionary[tso_pan_num]["multiqc_coverage_level"],
            " -d $jobid ",
            self.dest_str,
            self.token,
        ]
        dx_command = "".join(map(str, dx_command_list))
        return dx_command

    def create_mokasnp_cmd(self, fastq):
        """
        Input = R1 fastq filename and Pan number for a single sample
        Returns = dx run command for MokaSNP workflow (string)
        """
        # Call function to build nexus fastq paths - returns tuple for read1 and read2 and
        # samplename
        fastqs = self.nexus_fastq_paths(fastq)

        # Create the MokaSNP dx command
        dx_command_list = [
            config.mokasnp_cmd,
            fastqs[2],
            config.snp_fastqc1,
            fastqs[0],
            config.snp_fastqc2,
            fastqs[1],
            config.snp_sentieon_samplename,
            fastqs[2],
            self.dest_str,
            self.token,
        ]

        dx_command = "".join(map(str, dx_command_list))

        return dx_command

    def create_mokapipe_cmd(self, fastq, pannumber):
        """
        Input = R1 fastq filename and Pan number for a single sample
        Returns =  dx run command for Mokapipe (string)
        """
        # build nexus fastq paths - returns tuple for read1 and read2 and samplename and dictionary
        # for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # Congenica requires variant calling to be restricted in the pipeline, in some cases to
        # prevent incidental findings
        # The variant caller pads bed files by 100bp by default so this may need to be overruled.
        # The panel dictionary default is to give a value of 0, which turns off this padding.
        # An example of the use of this is for STG BrCa who require padding of +/- 11bp (bed files
        # are padded +/-10bp) so 1bp padding is applied.
        mokapipe_padding_cmd = (config.mokapipe_haplotype_padding_input +
                                str(panel_config.mokapipe_haplotype_caller_padding))

        if bedfiles["variant_calling_bedfile"]:
            bedfiles_string = (
                config.mokapipe_filter_vcf_with_bedfile_bed_input
                + bedfiles["variant_calling_bedfile"]
            )
        else:
            bedfiles_string = ""

        # if sample is not NA12878 we want to skip the vcfeval stage (the app default is skip=false)
        # assume it's not a NA12878 sample, and set skip = true
        vcf_eval_skip_string = config.mokapipe_happy_skip % ("true")
        # set the prefix as the samplename
        vcf_eval_prefix_string = config.mokapipe_happy_prefix % (fastqs[2])

        # identify NA12878 samples by checking if any reference ids (flanked by underscores) are
        # present in the fastq name
        # if so, set skip = false
        for ref_sample_id in config.reference_sample_ids:
            if f"_{ref_sample_id}_" in fastq:
                vcf_eval_skip_string = config.mokapipe_happy_skip % ("false")

        # Set parameters specific to FH_PRS app.
        fh_prs_bedfile_cmd = config.mokapipe_fhprs_bedfile_input + bedfiles["fh_prs"]
        fh_prs_cmd_string = ""

        if self.panel_dictionary[pannumber]["FH"]:
            # If sample is R134 we want app to run - set skip to false
            # Specify instance type for human exome app and specify output as both vcf and gvcf
            fh_prs_cmd_string += (
                f"{config.mokapipe_fhprs_skip} "
                f"--instance-type {config.mokapipe_gatk_human_exome_stage}="
                f"{config.mokapipe_fh_humanexome_instance_type}"
                f"{config.mokapipe_haplotype_vcf_output_format}"
                f"{config.mokapipe_fh_gatk_timeout_args}"
            )

        # Set parameters specific to polyedge app
        polyedge_cmd_string = ""

        # If test contains MSH2, we want app to run - set skip to false
        if self.panel_dictionary[pannumber]["MSH2"]:
            polyedge_cmd_string += config.mokapipe_polyedge_skip

        masked_reference_command = ""
        if self.panel_dictionary[pannumber]["masked_reference"]:
            masked_reference_command += config.mokapipe_bwa_ref_genome % (
                self.panel_dictionary[pannumber]["masked_reference"]
            )
        # Create the dx command
        dx_command = (
            config.mokapipe_cmd
            + fastqs[2]
            + config.mokapipe_fastqc1
            + fastqs[0]
            + config.mokapipe_fastqc2
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
            + fh_prs_cmd_string
            + fh_prs_bedfile_cmd
            + polyedge_cmd_string
            + masked_reference_command
            + config.mokapipe_mokapicard_vendorbed_input
            + bedfiles["hsmetrics"]
            + config.mokapipe_mokapicard_capturetype_stage
            % (self.panel_dictionary[pannumber]["capture_type"])
            + mokapipe_padding_cmd
            + bedfiles_string
            + self.dest_str
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
            self.congenica_upload_command_script_path, "w", encoding="utf-8"
        ) as congenica_script:
            congenica_script.write(config.source_cmd + "\n")

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
        dx_command = f"{config.decision_support_preperation} $jobid -t congenica "\
                     "-p {self.runfolder_obj.nexus_project_name})"
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
            config.mokaamp_cmd,
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
            config.mokaamp_bwa_ref_stage,
            config.mokaamp_vardict_samplename_stage,
            fastqs[2],
            config.mokaamp_varscan_samplename_stage,
            fastqs[2],
            config.mokaamp_mokapicard_ref_stage,
            config.mokaamp_vardict_ref_stage,
            config.mokaamp_varscan_ref_stage,
            self.dest_str,
            self.token,
        ]

        # Variables from dx_command_list are read from config file as various atomic types. Convert
        # to string and join to create dx_command.
        dx_command = "".join(map(str, dx_command_list))

        # remove the bit that adds the job to the depends on list for the negative control as
        # varscan fails on nearempty/-empty BAM files
        # and this will stop multiqc etc running
        if "NTC" in fastqs[0]:
            dx_command = dx_command.replace("jobid=$(", "").replace(
                config.nexus_apikey + ")", config.nexus_apikey
            )
        return dx_command

    def create_mokacan_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample
        Returns = dx run command for MokaCAN (string)
        """
        # build nexus fastq paths - returns tuple for read1 and read2 and dictionary for bed files
        fastqs = self.nexus_fastq_paths(fastq)
        bedfiles = self.nexus_bedfiles(pannumber)

        # create the MokaCAN dx command
        dx_command_list = [
            config.mokacan_cmd,
            fastqs[2],
            config.mokacan_fastqc_r1_stage,
            fastqs[0],
            config.mokacan_fastqc_r2_stage,
            fastqs[1],
            config.mokacan_sentieon_sample_name_stage,
            fastqs[2],
            config.mokacan_picard_bedfile_stage,
            bedfiles["hsmetrics"],
            config.mokacan_picard_capturetype_stage,
            self.panel_dictionary[pannumber]["capture_type"],
            config.mokacan_sambamba_coverage_level_stage,
            self.panel_dictionary[pannumber]["clinical_coverage_depth"],
            config.mokacan_sambamba_bedfile_stage,
            bedfiles["sambamba"],
            config.mokacan_vardict_bedfile_stage,
            bedfiles["variant_calling_bedfile"],
            config.mokacan_varscan_bedfile_stage,
            bedfiles["variant_calling_bedfile"],
            config.mokacan_vardict_sample_name_stage,
            fastqs[2],
            config.mokacan_senteion_bwa_ref_stage,
            config.mokacan_senteion_ref_stage,
            config.mokacan_picard_ref_stage,
            config.mokacan_vardict_ref_stage,
            config.mokacan_varscan_ref_stage,
            self.dest_str,
            self.token,
        ]

        # Variables from dx_command_list are read from config file as various atomic types. Convert
        # to string and join to create dx_command.
        dx_command = "".join(map(str, dx_command_list))
        # remove the bit that adds the job to the depends on list for the negative control as
        # varscan fails on near empty/-empty BAM files and this will stop multiqc etc running
        if "NTCcon" in fastqs[0]:
            dx_command = dx_command.replace("jobid=$(", "").replace(
                config.nexus_apikey + ")", config.nexus_apikey
            )
        return dx_command

    def prepare_rpkm_list(self, rpkm_list):
        """
        Input = a list of panels which requires RPKM analysis
        Pan numbers are used to distinguish between samples analysed in congenica or in ingenuity.
        These samples have the same wetlab work so can be combined for RPKM analysis
        This function determines if it's a pan number that can be analysed alongside another
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
            if ((self.panel_dictionary[pannumber]["pipeline"] == "mokapipe") and
               (self.panel_dictionary[pannumber]["analyse_RPKM"])):
                if self.panel_dictionary[pannumber]["panel_name"] == "vcp1":
                    rpkm_analysis_list += panel_config.vcp1_panel_list
                elif self.panel_dictionary[pannumber]["panel_name"] == "vcp1":
                    rpkm_analysis_list += panel_config.vcp2_panel_list
                elif self.panel_dictionary[pannumber]["panel_name"] == "vcp3":
                    rpkm_analysis_list += panel_config.vcp3_panel_list

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
            "Combining panels for RPKM analysis.\nOriginal panels: %s\nPanels to analyse: %s",
            ",".join(rpkm_list),
            ",".join(cleaned_list),
        )

        # return list to be used to build rpkm command(s).
        return cleaned_list

    def create_rpkm_cmd(self, pannumber):
        """
        Input = Pannumber for a single RPKM analysis
        The RPKM app requires a project id, bedfile and a string containing the pannumber(s) of all
        files that should be included in this analysis.
        Multiple pannumbers can be included in a single analysis.
        Return = dx run command for RPKM app for this analysis (string)
        """
        # call function to return all the bedfile paths
        bedfiles = self.nexus_bedfiles(pannumber)

        # Samples with different pannumbers can be included in the same RPKM analysis
        # (defined in config).
        # The app takes these pan numbers as a string, and will seperate on commas to identify
        # multiple pan numbers

        if self.panel_dictionary[pannumber]["panel_name"] == "vcp1":
            rpkm_analysis_list = panel_config.vcp1_panel_list
        elif self.panel_dictionary[pannumber]["panel_name"] == "vcp1":
            rpkm_analysis_list = panel_config.vcp2_panel_list
        elif self.panel_dictionary[pannumber]["panel_name"] == "vcp3":
            rpkm_analysis_list = panel_config.vcp3_panel_list

        string_of_pannumbers_to_analyse = ",".join(set(rpkm_analysis_list))

        # build RPKM command
        dx_command = (
            config.RPKM_cmd
            + config.mokapipe_rpkm_bedfile_input
            + bedfiles["rpkm_bedfile"]
            + config.mokapipe_rpkm_project_input
            + self.runfolder_obj.nexus_project_name
            + config.mokapipe_rpkm_bamfiles_to_download_input
            + string_of_pannumbers_to_analyse
            + self.project
            + self.runfolder_obj.nexus_project_id
            + self.depends
            + self.token.rstrip(")")
        )
        return dx_command

    def run_congenica_command(self, fastq, pannumber):
        """
        Input = R1 fastq file name and pan number for a single sample
        The import congenica app takes inputs in the format jobid.outputname which ensures the job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        The panel dictionary in the config file is used to determine the congenica project, IR
        template and credentials file
        This command is appended to a file which will be run after the QC is passed.
        Returns = dx run command for congenica import app (string)
        """
        # Check if any reference ids (flanked by underscores) are present in fastq name
        # If so skip this step
        for ref_sample_id in config.reference_sample_ids:
            if f"_{ref_sample_id}_" in fastq:
                self.loggers.script.info(
                    "UA_pass 'NA12878 sample detected, "
                    "not building congenica upload command for %s'",
                    fastq,
                )
                return None

        # nexus_fastq_paths function returns paths to the fastq files in Nexus and the sample name
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
            + self.dest_str
            + self.token.replace(")", self.congenica_upload_command_redirect)
        )
        return dx_command

    def run_congenica_sftp_upload_command(self, fastq):
        """
        Input = R1 fastq file name
        The import congenica SFTP app takes inputs in the format jobid.outputname which ensures job
        doesn't run until the vcfs have been created.
        These inputs are created by a python script, which is called immediately before this job,
        and the output is captures into the variable $analysisid
        Upload via SFTP only required the bam and vcf inputs, and does not need projectids,
        IR templates or names
        This command is appended to a file which will be run after the QC is passed.
        Returns = dx run command for congenica import app (string)
        """
        # Check if reference ids (flanked by underscores) present in fastq name. If so, skip step
        for ref_sample_id in config.reference_sample_ids:
            if f"_{ref_sample_id}_" in fastq:
                self.loggers.script.info(
                    "UA_pass 'NA12878 sample detected, "
                    "not building congenica upload command for %s'",
                    fastq,
                )
                return None

        # nexus_fastq_paths function returns paths to the fastq files in Nexus and the sample name
        # The samplename (fastqs[2]) is used to name the job
        fastqs = self.nexus_fastq_paths(fastq)

        dx_command = (
            config.congenica_sftp_upload_cmd
            + "' $analysisid '"
            + " --name "
            + "congenica_SFTP_upload_"
            + fastqs[2]
            + self.dest_str
            + self.token.replace(")", self.congenica_upload_command_redirect)
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

    def create_multiqc_cmd(self):
        """
        Input = None
        MultiQC is run at the very end of the run, after all QC tools have been run.
        MultiQC requires a project to download data from, and a coverage level.
        Coverage level differs between panels. Lowest value for the panels on this run is used.
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
                # If required coverage for panel is less than current value of lowest_coverage_level
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
            config.multiqc_cmd
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

    def create_upload_multiqc_cmd(self):
        """
        Input = None
        The input to the upload_multiqc app is the html_report output of the multiqc app,
        in the format jobid:output_name
        Returns = dx run command for the upload_multiqc app (string)
        """
        # dx run + config.tools_project + config.upload_multiqc_path + -imultiqc_html= + input.html
        dx_command = "".join(
            [
                config.upload_multiqc_cmd,
                " -imultiqc_html=$jobid:multiqc_report",
                " -imultiqc_data_input=$jobid:multiqc",
                f" -imultiqc_data_input={(self.runfolder_obj.nexus_project_name)}:/QC/*"
                f"{self.runfolder_obj.runfolder_name}{config.cluster_density_file_suffix}",
                self.project,
                self.runfolder_obj.nexus_project_id,
                self.token,
            ]
        )
        return dx_command

    def run_peddy_cmd(self):
        """
        Input = None
        Peddy is run once at the end of a WES run. Downloads required files from project
        Returns = dx run command for the peddy app (string)
        """
        dx_command = (
            config.peddy_cmd
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
        with open(
            self.runfolder_obj.runfolder_dx_run_script, "w", encoding="utf-8"
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
                    "UA_fail 'Error when starting pipeline for run %s. Stderror = \n%s",
                    self.runfolder_obj.runfolder_name,
                    "\n".join(cleaned_error),
                )
        else:
            # write error message to log file
            self.loggers.script.info(
                "UA_pass 'dx run commands issued without error for run %s'",
                self.runfolder_obj.runfolder_name,
            )

    def write_opms_queries_custom_panel(self, list_of_processed_samples):
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
                pannumber = re.search(r"Pan\d+", fastq).group()
                query = (
                    "insert into NGSCustomRuns(DNAnumber,PipelineVersion, "
                    "RunID) values ('%s','%s','%s')"
                )
                # if the pan number was processed using mokapipe and congenica, add query to list
                # of queries, capturing the DNA number from the fastq name
                if (
                    self.panel_dictionary[pannumber]["pipeline"] == "mokapipe"
                    and self.panel_dictionary[pannumber]["congenica_upload"]
                ):
                    queries.append(
                        query,
                        str(fastq.split("_")[2]),
                        config.mokapipe_congenica_pipeline_id,
                        self.runfolder_obj.runfolder_name,
                    )
                elif self.panel_dictionary[pannumber]["pipeline"] == "mokacan":
                    queries.append(
                        query,
                        str(fastq.split("_")[2]),
                        config.mokacan_pipeline_id,
                        self.runfolder_obj.runfolder_name,
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
        If MokaWES samples - Function populates a dictionary of sample counts, query (str) and list
        of samplenames to be added to global dictionary.
        Returns = dictionary or None
        """
        dnanumbers = []
        samplenames = []
        # add workflow to sql dictionary
        for fastq in list_of_processed_samples:
            # take read one
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                # if the pan number was processed using mokawes add the query to list of queries,
                # capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["pipeline"] == "mokawes":
                    dnanumbers.append(str(fastq.split("_")[2]))
                    # Call function to build nexus fastq paths - returns tuple for read1, read2
                    # and samplename
                    samplenames.append(self.nexus_fastq_paths(fastq)[2])
        if dnanumbers:
            return {
                "count": len(dnanumbers),
                "query": [
                    "update NGSTest set PipelineVersion = "
                    + config.mokawes_pipeline_id
                    + " , StatusID = "
                    + config.mokastatus_dataproc_id
                    + " where dna in ('"
                    + ("','").join(dnanumbers)
                    + "') and StatusID = "
                    + config.mokastatus_nextsq_id
                ],
                "samplename_email": samplenames,
            }
        else:
            return None

    def write_opms_queries_mokasnp(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Samples processed using MokaSNP are recorded in Moka using an insert query.
        This function will create an insert query for each sample processed through MokaSNP.
        If SNP genotyping samples are found this function will return a dictionary of sample counts
        and a list of queries to be added to global dictionary.
        Returns = dictionary or None
        """
        queries = []
        for fastq in list_of_processed_samples:
            if "_R1_" in fastq:  # Take read one
                pannumber = re.search(r"Pan\d+", fastq).group()  # Extract Pan number
                query = (
                    "insert into NGSCustomRuns(DNAnumber,PipelineVersion, RunID) "
                    "values ('%s','%s','%s')"
                )
                # If the pan number was processed using mokapipe and congenica, add the query to
                # list of queries, capturing the DNA number from the fastq name
                if self.panel_dictionary[pannumber]["pipeline"] == "mokasnp":
                    queries.append(
                        query,
                        str(fastq.split("_")[2]),
                        config.mokasnp_pipeline_id,
                        self.runfolder_obj.runfolder_name,
                    )
        if queries:
            return {
                "count": len(queries),
                "query": queries,
            }  # Add workflow to sql dictionary
        else:
            return None

    def write_opms_queries_mokaamp(self, list_of_processed_samples):
        """
        Input = list of fastqs to be processed
        Samples tested using mokaamp are not booked into Moka until the analysis stage so
        create a query using IDs form the samplename
        An insert query is build for each sample, recording the IDs which are the 3rd and 4th
        elements in the samplename.
        These are recorded along with the pipeline version and the name of the run.
        If not a None object is returned
        Return = dictionary
        """
        queries = []
        workflows = []
        # loop through fastqs to see which workflows were used
        for fastq in list_of_processed_samples:
            # take read one
            # example fastq names: ONC20085_08_EK20826_2025029_SWIFT57_Pan2684_S8_R2_001.fastq.gz
            # and ONC20085_06_NTCcon1_SWIFT57_Pan2684_S6_R1_001.fastq.gz
            if "_R1_" in fastq:
                # extract_Pan number
                pannumber = re.search(r"Pan\d+", fastq).group()
                # record id1 and 2 by taking the second and third elements
                id1, id2 = fastq.split("_")[2:4]
                # negative controls only have one ID so set id2 to null
                if "NTCcon" in fastq:
                    id2 = "NULL"
                # define query with placeholders
                query = (
                    "insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,"
                    "ngspanelid) values ('%s','%s','%s','%s','%s')"
                )

                # for mokaamp and archerdx if relevant build the query, populating the placeholders.
                # add the name of the workflow to the list of workflows
                if self.panel_dictionary[pannumber]["pipeline"] == "mokaamp":
                    queries.append(
                        query,
                        id1,
                        id2,
                        self.runfolder_obj.runfolder_name,
                        config.mokaamp_pipeline_id,
                        pannumber.replace("Pan", ""),
                    )
                    workflows.append(config.mokaamp_path.rsplit("/", maxsplit=1)[-1])
                if self.panel_dictionary[pannumber]["pipeline"] == "archerdx":
                    queries.append(
                        query,
                        id1,
                        id2,
                        self.runfolder_obj.runfolder_name,
                        config.archerDx_pipeline_id,
                        pannumber.replace("Pan", ""),
                    )
                    workflows.append(config.fastqc_app.rsplit("/", maxsplit=1)[-1])
        if queries:  # If queries have been created return a dictionary
            # Use queries list to create a count of samples, return list of queries and the set of
            # the workflows (removing duplicates)
            return {
                "count": len(queries),
                "query": queries,
                "workflows": set(workflows),
            }
        else:
            return None

    def write_opms_queries_tso500(self, list_of_processed_samples):
        """
        Input = list of samples to be processed
        Samples tested using tso500
        An insert query is build for each sample, recording the IDs which are the 3rd and 4th
        elements in the samplename.
        These are recorded along with the pipeline version and the name of the run.
        If not a None object is returned
        Return = dictionary
        """
        queries = []
        workflows = []
        query = (
            "insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,"
            "ngspanelid) values ('%s','%s','%s','%s','%s')"
        )

        # loop through fastqs to see which workflows were used
        for sample in list_of_processed_samples:
            # extract_Pan number
            pannumber = re.search(r"Pan\d+", sample).group()
            if self.panel_dictionary[pannumber]["pipeline"] == "tso500":
                # record id1 and 2 by taking the second and third elements
                id1, id2 = sample.split("_")[2:4]
                # define query with placeholders
                queries.append(
                    query,
                    id1,
                    id2,
                    self.runfolder_obj.runfolder_name,
                    config.tso_pipeline_id,
                    pannumber.replace("Pan", ""),
                )
                workflows.append(config.tso500_app_name)
        if queries:  # If queries have been created return a dictionary
            # Use queries list to create a count of samples, return list of queries and the set of
            # the workflows (removing duplicates)
            return {
                "count": len(queries),
                "query": queries,
                "workflows": set(workflows),
            }
        else:
            return None

    def send_opms_queries(self):
        """
        Queries to record the pipeline versions are emailed.
        This function sends emails, using the queries written to self.sql_queries by the various
        test specific functions.
        Oncology and rare disease emails are sent seperately and independantly of each other.
        Returns = None
        """
        # email body template - has the following requires following format:
        # {config.test_email_header} {self.runfolder_obj.runfolder_name} being processed using
        # workflow(s) {",".join(self.sql_queries["mokaamp"]["workflows"])}\n\n{sql_str}\n{"\n".
        # join(self.sql_queries["mokaamp"]["query"])}\n
        #
        #  eg
        #   AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. PLEASE IGNORE THIS EMAIL
        # (config.test_email_header - can be empty string)
        #   999999_M02353_0496_000000000-D8M36_SWIFT being processed using workflow(s) MokaAMP_v2.2
        # (self.runfolder_obj.runfolder_name ...
        # ",".join(self.sql_queries["mokaamp"]["workflows"]))
        #   Please update Moka using the below queries and ensure that 10 records are updated:
        # (sql string - This can change - is different for the email to users who don't need the
        # sql queries)
        #   insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid)
        # values ('NTCcon','NULL','999999_M02353_0496_000000000-D8M36_SWIFT','4851','4081') (sql
        # queries - can be empty string for users who don't need these)

        sql_email_msg = "%s %s being processed using workflow(s) %s\n\n%s\n%s\n"

        if self.sql_queries["mokaamp"]:  # Send mokaamp email first
            email_subject = (
                f"MOKA ALERT: Started pipeline for {self.runfolder_obj.runfolder_name}"
            )
            # Populate sql_str needed to fill the email_msg
            sql_str = (
                "Please update Moka using the below queries and ensure that %s "
                "records are updated:\n\n",
                str(self.sql_queries["mokaamp"]["count"]),
            )
            email_msg = sql_email_msg, (
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["mokaamp"]["workflows"]),
                sql_str,
                "\n".join(self.sql_queries["mokaamp"]["query"]),
            )
            self.email.send_email(recipients=config.mokaguys_recipient,
                                  email_subject=email_subject, email_message=email_msg)

            # Email_for_cancer_ops leads to inform the pipeline has started
            # Set sql_str for the email message
            sql_str = "%s samples are being processed", str(
                self.sql_queries["mokaamp"]["count"]
            )

            # Fill template using empty string in place of sql queries
            email_msg = sql_email_msg, (
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["mokaamp"]["workflows"]),
                sql_str,
                "",
            )
            self.email.send_email(recipients=config.oncology_ops_email,
                                  email_subject=email_subject, email_message=email_msg)

        if self.sql_queries["tso500"]:  # Send tso500 queries
            email_subject = (
                f"MOKA ALERT: Started pipeline for {self.runfolder_obj.runfolder_name}"
            )
            sql_str = (
                "Please update Moka using the below queries and ensure that %s records "
                "are updated:\n\n",
                str(self.sql_queries["tso500"]["count"]),
            )
            email_msg = sql_email_msg, (
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(self.sql_queries["tso500"]["workflows"]),
                sql_str,
                "\n".join(self.sql_queries["tso500"]["query"]),
            )
            self.email.send_email(recipients=config.mokaguys_recipient,
                                  email_subject=email_subject, email_message=email_msg)

        # Build rare disease emails
        # Start counters and placeholders to for email data
        workflows = []
        sql_statements = []
        count = 0

        # for each pipeline take queries, sample count and workflow name
        if self.sql_queries["custom_panel"]:
            workflows.append(config.mokapipe_path.rsplit("/", maxsplit=1)[-1])
            sql_statements += self.sql_queries["custom_panel"]["query"]
            count += self.sql_queries["custom_panel"]["count"]
        if self.sql_queries["mokawes"]:
            workflows.append(config.mokawes_path.rsplit("/", maxsplit=1)[-1])
            sql_statements += self.sql_queries["mokawes"]["query"]
            count += self.sql_queries["mokawes"]["count"]
        if self.sql_queries["mokasnp"]:
            workflows.append(config.mokasnp_path.rsplit("/", maxsplit=1)[-1])
            sql_statements += self.sql_queries["mokasnp"]["query"]
            count += self.sql_queries["mokasnp"]["count"]

        # send email
        if workflows and sql_statements:
            # email this query
            email_subject = (
                f"MOKA ALERT: Started pipeline for {self.runfolder_obj.runfolder_name}"
            )
            sql_str = (
                "Please update Moka using the below queries and ensure that "
                f"{str(count)} records are updated:\n\n"
            )

            email_msg = sql_email_msg, (
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                ",".join(set(workflows)),
                sql_str,
                "\n".join(sql_statements),
            )
            self.email.send_email(recipients=config.mokaguys_recipient,
                                  email_subject=email_subject, email_message=email_msg)

        if self.sql_queries["mokawes"]:  # Send email to WES team to help IR upload
            email_subject = (
                f"MOKA ALERT: Started pipeline for {self.runfolder_obj.runfolder_name}"
            )
            sql_str = "The following samples are being processed:\n"
            email_msg = sql_email_msg, (
                config.test_email_header,
                self.runfolder_obj.runfolder_name,
                config.mokawes_path.rsplit("/", maxsplit=1)[-1],
                sql_str,
                "\n".join(self.sql_queries["mokawes"]["samplename_email"]),
            )
            self.email.send_email(recipients=config.wes_samplename_email_list,
                                  email_subject=email_subject, email_message=email_msg)

    def upload_rest_of_runfolder(self):
        """
        Input = None
        The rest of the runfolder requires backing up, excluding bcl files.
        BCL files are uploaded for TSO runs only.
        The rest of the runfolder requires backing up, excluding bcl files.
        A python script which is a wrapper for the upload agent is used.
        This function copies the samplesheet from into the runfolder and then builds and executes
        the backup_runfolder.py command
        Returns = filepath to backup script.
        """
        # Try to copy samplesheet into project
        if os.path.exists(self.runfolder_obj.runfolder_samplesheet_path):
            copyfile(
                self.runfolder_obj.runfolder_samplesheet_path,
                os.path.join(
                    self.runfolder_obj.runfolderpath,
                    self.runfolder_obj.runfolder_samplesheet_name,
                ),
            )
            self.loggers.script.info(
                "Samplesheet copied to runfolder: %s",
                self.runfolder_obj.runfolder_samplesheet_name,
            )
        else:
            self.loggers.script.info("Samplesheet not copied to runfolder")

        # build backup_runfolder.py command for TSO run
        tso500_backup = self.check_for_tso500()
        # if not TSO500 will return None
        if tso500_backup:
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
                + config.nexus_apikey
            )
        else:  # Build backup_runfolder.py command ignore some files
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
                + config.nexus_apikey
            )

        # Record runfolder upload in log file, linking to log files for cmds and stdout
        self.loggers.script.info(
            "Uploading rest of run folder to Nexus using backup_runfolder.py"
        )
        self.loggers.script.info(cmd)
        self.loggers.script.info(
            "See standard out from these commands in logfile at %s",
            self.loggers.backup.filepath,
        )

        _out, _err = self.execute_subprocess_command(cmd)
        # TODO add some tests for stderr?

        return self.loggers.backup.filepath

    def upload_log_files(self):
        """
        Input = None
        Upload the log files found in list_log_files.
        Returns = filepath to the logfile containing output from the command, string of files to be
        uploaded and name of the stage to test
        """
        # Define where files to be uploaded to
        nexus_upload_folder = (
            "/"
            + self.runfolder_obj.nexus_project_name.replace(
                config.dnanexus_project_prefix, ""
            )
            + "/Logfiles/"
        )
        # Create list of files to be used to check outputs
        files_to_upload_list = []
        # Create space delimited string of files to be uploaded defined by the logger class
        files_to_upload_string = ""
        for logger in self.loggers.all:
            if logger.filepath:
                files_to_upload_string += f"'{logger.filepath}"
                files_to_upload_list.append(logger.filepath)

        files_to_upload_string += f" '{self.bcl2fastq_logfile}'"
        files_to_upload_list.append(self.bcl2fastq_logfile)
        # Create a list which, when joined will form a single upload agent command, uploading each
        # file in logger.filepath
        cmd = (f"{config.upload_agent_path} "
               f"--auth-token {config.nexus_apikey} "
               f"--project {self.runfolder_obj.nexus_project_name} "
               f"--folder {nexus_upload_folder} "
               f"--do-not-compress {files_to_upload_string}")

        # Write commands to the upload agent logfile before upload
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
        return self.loggers.upload_agent.filepath, files_to_upload_list, "log files"

    def check_backuprunfolder_errors(self, logfile):
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
        with open(logfile, "r", encoding="utf-8") as backup_logfile:
            for line in backup_logfile.readlines():
                if config.backup_runfolder_success in line:
                    upload_ok = True
                if config.backup_runfolder_error in line:
                    error_seen.append(line)
        if error_seen:
            self.loggers.script.error(
                "UA_fail 'Error in upload of rest of runfolder: %s in runfolder %s'",
                ";".join(error_seen), self.runfolder_obj.runfolder_name
            )
        if upload_ok:
            self.loggers.script.info(
                "UA_pass 'Rest of runfolder %s uploaded ok'", self.runfolder_obj.runfolder_name
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


if __name__ == "__main__":
    # Create a custom list object to hold sequencing runs
    runs = SequencingRuns()
    # Set list with runfolder objects
    runs.set_runfolders()
    # Call upload and workflow logic on runfolders
    runs.loop_through_runs()
