#!/usr/bin/python3
"""upload_and_setoff_workflows.py

Upload NGS data to DNANexus and trigger analysis workflows.
"""
import datetime
import os
import re
import subprocess
from shutil import copyfile
from git_tag.git_tag import git_tag  # Import function which reads the git tag
import ad_logger.ad_logger as ad_logger
import config.ad_config as ad_config
import config.panel_config as panel_config
from ad_email.ad_email import AdEmail
from runfolder_obj.runfolder_obj import RunfolderObject
from backup_runfolder.backup_runfolder import UAcaller


def execute_subprocess_command(command):
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
    out, err = proc.communicate()
    # capture the streams
    return (out.decode("utf-8"), err.decode("utf-8"))


# TODO incorporate traceback into logging
class SequencingRuns(list):
    """
    A container for NGS runfolders with methods to initiate
    runfolder processing.

    Methods:
        set_runfolders():       Update list to contain NGS runfolders on the
                                system
        loop_through_runs():    Process all NGS runfolders in class instance
                                list
    """

    def __init__(self):
        """
        Constructor for the SequencingRuns class
        """
        # Enable this class to hold sequencing runs by inheriting from
        # python's List object
        super(SequencingRuns, self).__init__()
        # Timestamp for each instance is used to name logfiles.
        self.timestamp = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
        self.runfolders = []
        # This is used as an object where various logs can be written
        self.loggers = ad_logger.AdLoggers(self.timestamp)
        self.loggers.usw_script.info(
            self.loggers.msgs["usw"]["script_start"],
            git_tag(),
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

    def set_runfolders(self):
        """
        Update internal list with NGS runfolders present on the system. The
        root directory to search for runfolders is specified in the ad_config
        object.

        >>> runs = SequencingRuns()
        >>> # runs == []
        >>> runs.set_runfolders()
        >>> # runs == ['runfolder1', 'runfolder2', 'runfolder3']
        Returns = None
        """
        for folder in os.listdir(ad_config.RUNFOLDERS):
            # If exists and is directory, shouldn't be ignored, and
            # matches runfolder pattern
            if os.path.isdir(os.path.join(ad_config.RUNFOLDERS, folder)) and re.compile(
                ad_config.RUNFOLDER_PATTERN
            ).match(folder):
                self.loggers.usw_script.info(
                    self.loggers.msgs["usw"]["runfolder_identified"],
                    folder,
                    extra={"flag": self.loggers.log_flags["usw"]["info"]},
                )
                self.runfolders.append(folder)

    def loop_through_runs(self):
        """
        Input = None
        Process all NGS runfolders in class instance list.
        Returns = None
        """
        # Track processed runfolders to use later for naming logfiles.
        processed_runfolders = []

        self.loggers.usw_script.info(
            self.loggers.msgs["usw"]["runfolder_looping"],
            self.runfolders,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Process any runfolders added to class instance with
        # self.set_runfolders()
        for runfolder in self.runfolders:
            if self.run_tests():
                runfolder_obj = RunfolderObject(runfolder, self.timestamp)
                runfolder_obj.get_samples()
                if self.runfolder_obj.fastqs_list:
                    runfolder_obj.get_nexus_paths()
                    runfolder_obj.get_upload_cmds()
                    runfolder_instance = ProcessRunfolder(runfolder_obj, self.timestamp)
                    # Append processed runfolders to tracking list
                    if runfolder_instance.process_runfolder():
                        processed_runfolders.append(runfolder)
                        # Close down the run folder specific logger handlers
                        runfolder_instance.loggers.shutdown_logs()

                        self.loggers.usw_script.info(
                            self.loggers.msgs["usw"]["runfolder_processed"],
                            runfolder_instance.runfolder_obj.runfolder_name,
                            extra={"flag": self.loggers.log_flags["usw"]["info"]},
                        )
                    else:
                        runfolder_instance.loggers.shutdown_logs()
                        self.loggers.usw_script.info(
                            self.loggers.msgs["usw"]["runfolder_not_processed"],
                            runfolder_instance.runfolder_obj.runfolder_name,
                            extra={"flag": self.loggers.log_flags["usw"]["info"]},
                        )
        # No. runfolders processed during this cycle
        num_processed_runfolders = len(processed_runfolders)

        # Comma delimited string of all runfolders processed in cycle
        processed_run_string = ", ".join(processed_runfolders)

        self.loggers.usw_script.info(
            self.loggers.msgs["usw"]["script_complete"],
            git_tag(),
            num_processed_runfolders,
            processed_run_string,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

    def run_tests(self):
        """
        Inputs = None
        Test the software is installed and performing, by calling the
        test_upload_agent and test_dx_toolkit functions
        Returns = None
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["testing_software"],
            git_tag(),
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        if self.upload_agent_pass() and self.dx_toolkit_pass():
            return True

    def upload_agent_pass(self):
        """
        Assess output of upload agent test command
        Raises exception if test does not pass
        """
        out, err = self.execute_subprocess_command(
            ad_config.EXECUTABLES["upload_agent"] + ad_config.UPLOAD_AGENT_TEST_CMD
        )
        if ad_config.UPLOAD_AGENT_EXPECTED_STDOUT in out:
            self.loggers.usw_script.info(
                self.loggers.msgs["usw"]["uatest_pass"],
                out,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return True
        else:
            self.loggers.usw_script.exception(
                self.loggers.msgs["usw"]["uatest_fail"],
                out,
                err,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
            raise Exception  # Stop script

    def dx_toolkit_pass(self):
        """
        Assess output of dx toolkit test command
        Raises exception if test does not pass
        """
        out, err = self.execute_subprocess_command(ad_config.DX_SDK_TEST)

        if ad_config.DX_SDK_TEST_EXPECTED_STDOUT in out:
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["dxtoolkittest_pass"],
                out,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            return True
        else:
            self.loggers.usw_rf.exception(
                self.loggers.msgs["usw"]["dxtoolkittest_fail"],
                out,
                err,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
            raise Exception  # Stop script


class ProcessRunfolder(object):
    """
    This class assesses a runfolder to check if it required processing. If the
    runfolder meets the
    criteria to be processed.
    Fastqs are uploaded to DNAnexus, dx run commands built and executed and
    then the rest of the
    runfolder is also uploaded.
    All actions are logged in the logfile created when the script is run.
    A new instance of this class is initiated for each runfolder being assessed

    Methods:
    """

    def __init__(self, runfolder_obj, timestamp):
        """
        Constructor for the RunfolderProcessor class
            :param runfolder (str):     Runfolder name string
            :param timestamp (str):     Timetamp in the format
                                        str(f"{datetime.datetime.now():
                                        %Y%m%d_%H%M%S}")
        """
        # Capture class inputs
        self.timestamp = timestamp
        self.runfolder_obj = runfolder_obj
        self.fastqs_str = " ".join(self.runfolder_obj.fastqs_list)

        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token

        # Input - WES number and library batch numbers
        # The DNAnexus project name contains all the information required to
        # quickly and easily identify the contents, which may help in the future.
        # The project name starts with a code to denote the status of the project
        # (eg live clinical, development or archived) and is followed by the name
        # of the runfolder.
        # The WES batches and library prep strings are suffixed onto the project
        # name (received as inputs from other functions).
        # Returns = tuple containing strings for self.dest_str,
        # runfolder_obj.nexus_fastqs_dir and runfolder_obj.nexus_project_name
        self.users_dict = self.get_users_dict()

        # This is used as an object where various logs can be written
        self.loggers = ad_logger.AdLoggers(self.timestamp, self.runfolder_obj)
        self.email = AdEmail(logger=self.loggers.usw_rf)
        self.write_project_creation_script()
        self.nexus_project_id = self.run_project_creation_script()
        # list to hold all dx run commands
        self.dx_run_cmds_list = [
            ad_config.CMDS["sdk_source"],
            ad_config.EMPTY_DEPENDS,
            ad_config.EMPTY_GATK_DEPENDS,
        ]

    def process_runfolder(self):
        """"""
        file_upload_dict = {
            "fastqs": {
                "cmd": self.runfolder_obj.fastq_upload_command,
                # List contains samplesheet for tso runs
                "files_list": self.runfolder_obj.fastqs_list,
            },
            "cluster density files": {
                "cmd": self.runfolder_obj.cd_upload_cmd,
                "files_list": self.runfolder_obj.runfolder_obj.cluster_density_files,
            },
            "bcl2fastq QC files": {
                "cmd": self.rufolder_obj.bcl2fastq_qc_upload_cmd,
                "files_list": self.runfolder_obj.bcl2fastqstats_file,
            },
        }
        if self.runfolder_obj.pipeline == "tso500":
            # Remove fastqs from upload dict as they don't exist for tso runfolders
            file_upload_dict.pop('fastqs')
            # Add samplesheet entry
            file_upload_dict['runfolder samplesheet'] = {
                "cmd": self.runfolder_obj.rf_samplesheet_upload_command,
                "files_list": [self.runfolder_samplesheet_path]
            }
            self.upload_tso_runfolder()
        # Upload files and write stdout to upload started txt file
        for key in file_upload_dict:
            self.upload_files(key["cmd"], key["files_list"], key)
            self.look_for_upload_errors(key["files_list"], key)

        # If there is a congenica upload create the congenica upload bash file, which
        # is run manually after QC has passed
        if self.pipeline in ("pipe", "wes"):
            self.create_congenica_command_file()

        dx_run_cmds = self.build_dx_run_cmds(self.nexus_project_id)

        self.write_dx_run_cmds(dx_run_cmds)
        self.run_dx_run_commands()

        pipeline_emails = PipelineEmails(self.runfolder_obj)
        queries = pipeline_emails.collect_queries()
        pipeline_emails.send_sql_email(queries)
        pipeline_emails.send_samples_email()
        # if not TSO500 will return None

        if not self.runtype == "tso":
            self.upload_rest_of_runfolder()
            self.check_backuprunfolder_errors()

        self.upload_files(self.logfiles_upload_cmd, self.logfiles_to_upload, "logfiles")
        self.look_for_upload_errors(self.logfiles_to_upload, "logfiles")

    def get_users_dict(self):
        """"""
        # Pull out drylab_dnanexus_ids for pan numbers where this is
        # not None (default = False)

        # Some samples are analysed at dry labs. Access to projects is
        # only given when there is a sample for that dry lab on the run

        dry_lab_list = set(
            [
                k
                for k, v in self.runfolder_obj.sample_dict.items()
                if v["panel_settings"]["drylab_dnanexus_id"]
            ]
        )
        return {
            "viewers": (ad_config.DNANEXUS_USERS["viewers"].append(dry_lab_list)),
            "admins": ad_config.DNANEXUS_USERS["admins"],
        }

    def write_project_creation_script(self):
        """
        Input = list of processed samples
        Once the project name has been defined the project can be created using
        the DNANexus sdk
        Commands are written to a bash script and executed using subprocess.
        The project is created
        and shared with users, with varying degrees of access as defined in the
        ad_config file.
        The list of processed samples is passed, extracting Pan numbers and
        assessing if the project
        should also be shared with any
        additional dry lab DNANexus accounts.
        This function writes a bash script containing the project creation
        command
        Return = two lists, one of users shared with view permissions, one
        with admin
        """
        # open bash script
        with open(
            self.runfolder_obj.project_creation_logfile, "w", encoding="utf-8"
        ) as project_script:
            project_script.write(f"{ad_config.CMDS['sdk_source']}\n")
            project_script.write(ad_config.EMPTY_DEPENDS)
            project_script.write(
                ad_config.DX_RUN_CMDS["create_proj"]
                % (
                    ad_config.PROD_ORGANISATION,
                    self.runfolder_obj.nexus_project_name,
                    self.dnanexus_apikey,
                )
            )
            # Give view and admin permissions for project
            for permissions in (("viewers", "VIEW"), ("admins", "ADMIN")):
                for user in self.users_dict[permissions[0]]:
                    project_script.write(
                        f"dx invite {user} $project_id {permissions[1]} "
                        f"--no-email --auth-token {self.dnanexus_apikey}\n"
                    )
            project_script.write("echo $project_id")  # Capture project id

    def run_project_creation_script(self):
        """
        Inputs = users dictionary containing viewers and admins key value pairs
        Calls subprocess command executing project creation bash script
        Output of this command is tested to see if it meets the expected
        pattern
        Records in log file who project has been shared with
        Returns - projectid (if created), False (if debug) or an exception
        (non-debug)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["creating_proj"],
            self.runfolder_obj.project_creation_logfile,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Execute script made above
        cmd = f"bash {self.runfolder_obj.project_creation_logfile}"
        (out, _) = self.execute_subprocess_command(cmd)

        # If start of project id is in out capture the id and write to logfiles
        # and return
        if "project-" in out:
            # Split std_out on "project" and get the last item to capture th
            # project ID
            projectid = "project" + out.rsplit("project", maxsplit=1)[-1].rstrip()
            for permissions_tuple in (
                ("VIEW", self.users_dict["viewers"]),
                ("ADMIN", self.users_dict["admins"]),
            ):
                self.loggers.usw_rf.info(
                    self.loggers.msgs["usw"]["proj_created"],
                    self.runfolder_obj.nexus_project_name,
                    projectid,
                    permissions_tuple[0],
                    ",".join(permissions_tuple[1]),
                    extra={"flag": self.loggers.log_flags["usw"]["info"]},
                )
            return projectid
        else:
            self.loggers.usw_rf.exception(
                self.loggers.msgs["usw"]["proj_creation_fail"],
                self.runfolder_obj.nexus_project_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
            raise Exception  # Stop script

    def upload_tso_runfolder(self):
        """"""
        backup_attempt_count = 1
        while backup_attempt_count < 5:
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["TSO_backup_attempt"],
                backup_attempt_count,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            self.upload_rest_of_runfolder()
            if self.check_backuprunfolder_errors():
                backup_attempt_count = 10
            else:
                # Increase backup count
                backup_attempt_count += 1

    def upload_rest_of_runfolder(self):
        """
        Input = None
        The rest of the runfolder requires backing up, excluding bcl files.
        BCL files are uploaded for TSO runs only.
        A python script which is a wrapper for the upload agent is used.
        This function copies the samplesheet from into the runfolder and then
        builds and executes the backup_runfolder.py command
        Returns = filepath to backup script.
        """
        # Try to copy samplesheet into project
        if os.path.exists(self.runfolder_obj.samplesheet_path):
            copyfile(
                self.runfolder_obj.samplesheet_path,
                self.runfolder_obj.runfolder_samplesheet_path,
            )
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["ss_copy_success"],
                self.runfolder_obj.runfolder_samplesheet_path,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
        else:
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["ss_copy_fail"],
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
        # build backup_runfolder.py commands, ignoring some files
        if self.runtype == "tso":
            ignore = "DNANexus_upload_started,add_runfolder_to_nexus_cmds"
        else:
            ignore = "/L00,DNANexus_upload_started,add_runfolder_to_nexus_cmds"

        UAcaller(
            self.runfolder_obj.runfolder_name,
            ignore,
            self.loggers,
            self.dnanexus_apikey,
            self.runfolder_obj.nexus_project_name,
        ).perform_backup()

        # Record runfolder upload in log file
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["uploading_rf"],
            ignore,
            self.runfolder_obj.backup_runfolder_logfile,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # TODO add some tests for stderr?

    def look_for_upload_errors(self, files_to_upload, stage):
        """
        Inputs :
        A tuple containing:
            path to log file
            file_list = string (space delimited list) or list of files to be
            uploaded at this stage
            stage = the stage to be included in error report.
        Parse the file containing standard error/standard out from the upload
        agent.
        For each expected file to be uploaded check the expected upload success
        statement is present
        If the success statement is absent raise an alert but do not stop
        script from running
        Returns:
            strings (debug mode only).
        """
        # Check not always required, e.g. when optional files (eg lane metrics)
        # are not created
        # so allow a new stage to be used to skip testing
        issue_list = []  # List to hold files with issues
        for file in files_to_upload:
            upload_ok = False  # Set flag to upload unsuccessful
            # Loop through log file - if line relates to this fastq check,
            # upload was successful
            for line in open(
                self.loggers.upload_agent.filepath, "r", encoding="utf-8"
            ).readlines():
                if file in line and "was uploaded successfully. Closing..." in line:
                    upload_ok = True
            if not upload_ok:  # If no success statement at end of file
                issue_list.append(file)
        if issue_list:  # Report back if ok
            self.loggers.usw_rf.error(
                self.loggers.msgs["usw"]["upload_fail"],
                stage,
                issue_list,
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
        # if no error
        else:
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["upload_success"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )

    def upload_files(self, upload_cmd, files_list, upload_type):
        """
        Details written to log files (upload agent logfile and runfolder
        logfile) and then command passed to execute_subprocess_command().
        All standard error/standard out written to a log file

        Inputs:
            upload_cmd (str):   Command to use to upload the files
            files_list (list):  List of all files requiring upload
            upload_type (str):  String describing the files being uploaded
        Returns:
            None
        """
        self.loggers.upload_agent.info(
            self.loggers.msgs["usw"]["upload_cmds"],
            upload_type,
            upload_cmd,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["uploading_files"],
            upload_type,
            files_list,
            self.loggers.upload_agent.filepath,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Check all files exist before trying to upload
        # If they don't the script will fail when trying to upload them
        if all([os.path.isfile(f) for f in files_list]):
            # Execute upload agent command
            out, err = self.execute_subprocess_command(upload_cmd)
            # Write stdout and stderr to upload agent logfile
            self.loggers.upload_agent.info(
                self.loggers.msgs["usw"]["upload_output"],
                upload_type,
                out,
                err,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )


class BuildDxCommands(object):
    """"""
    def __init__(self):
        """"""
        # Update script log file to say what is being done.
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmds"],
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Decidsion support tool python script is run after each dx run command,
        # taking analysis and project name as input, and printing the required inputs
        # to the command line which are required by the congenica upload script
        # $jobid is a bash variable which will be populated by when run on the
        # command line
        # The python script has three inputs - the analysisID ($jobid), -t is
        # the DSS and -p is the DNAnexus project the analysis is running in
        self.congenica_input_cmd = (
            f"{ad_config.DX_RUN_CMDS['decision_support_prep']} $jobid -t "
            f"congenica -p {self.runfolder_obj.nexus_project_name})"
        )

    def build_dx_run_cmds(self):
        """
        Input = list of fastqs to be processed
        Loop through the list of fastqs, determine the pan number and use this
        to determine which workflow/apps should be run. Each app/workflow
        command is built by calling the relevant function
        When looping through samples flags and lists are used to determine
        which run wide tasks are required
        These run wide commands eg multiqc are built after sample specific
        commands
        All commands are added to a list.
        Returns = list of commands
        """
        dx_cmd_list = []

        # Get sample workflow-level commands
        if self.pipeline != "tso500":
            dx_cmd_list.append(self.return_sample_workflow_cmds())
            # Get run-wide commands
            if self.pipeline == "wes":
                dx_cmd_list.append(self.return_wes_runwide_cmds())

            if self.pipeline == "pipe":
                dx_cmd_list.append(self.return_pipe_runwide_cmds())

            dx_cmd_list.append(self.return_multiqc_cmds())

        elif self.pipeline == "tso500":
            dx_cmd_list.append(self.return_tso_runwide_cmds())

        dx_cmd_list.append(self.create_duty_csv_command())

        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["cmds_built"],
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        return dx_cmd_list

    def return_tso_runwide_cmds(self):
        """
        Build command for the TSO500 app and set off fastqc commands, multiqc commands
        and sambamba commands.
        TSO commands are all generated within this function as the dependency order is
        different for this pipeline
        """
        cmd_list = []
        sambamba_cmds_list = []

        cmd_list.append(self.create_tso500_cmd())
        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])

        # For TSO samples, the fastqs are created within DNAnexus and the
        # commands are generated using sample names parsed from the
        # samplesheet. If for whatever reason those fastqs are not created
        # by the DNAnexus app, the downstream job will not set off and
        # therefore will produce no job ID to provide to the depends_list,
        # which will create an error/ slack alert. To solve this problem,
        # the job ID is only added to the depends list if it exits
        for sample_name in self.sample_dict.items():
            # Append all fastqc commands to cmd_list
            cmd_list.append(self.sample_dict[sample_name]["sample_pipeline_cmd"])
            # Only add to depends_list if job ID from previous command is not empty
            cmd_list.append(
                ad_config.UPLOAD_ARGS["if_jobid_exists_depends"]
                % ad_config.UPLOAD_ARGS["depends_list"]
            )
            if "HD200" in sample_name:
                cmd_list.append(
                    self.create_sompy_cmd(
                        sample_name,
                        self.sample_dict[sample_name]['panel_settings']['pannumber']
                        )
                    )
                # Only add to depends_list if job ID from previous command
                # is not empty
                cmd_list.append(
                    ad_config.UPLOAD_ARGS["if_jobid_exists_depends"]
                    % ad_config.UPLOAD_ARGS["depends_list"]
                )

            sambamba_cmds_list.append(
                self.create_sambamba_cmd(
                    sample_name,
                    self.sample_dict[sample_name]['panel_settings']['pannumber']
                    )
                )
            # Exclude negative controls from the depends list as the NTC
            # coverage calculation can often fail. We want the coverage
            # report for the NTC sample to help assess contamination.
            # Only add to depends_list if job ID from previous command
            # is not empty
            if "NTCcon" not in sample_name:
                sambamba_cmds_list.append(
                    ad_config.UPLOAD_ARGS["if_jobid_exists_depends"]
                    % ad_config.UPLOAD_ARGS["depends_list"]
                )

        cmd_list.append(self.return_multiqc_cmds())
        # Set off after as they are not depended upon by MultiQC but are required for
        # duty_csv
        cmd_list.append(sambamba_cmds_list)

    def return_multiqc_cmds(self):
        """
        """
        cmd_list = []
        cmd_list.append(self.create_multiqc_cmd())
        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
        cmd_list.append(self.create_upload_multiqc_cmd())
        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
        return cmd_list

    def return_sample_workflow_cmds(self):
        """"""
        cmd_list = []
        for sample in self.sample_dict.items():
            self.loggers.usw_rf.info(
                    self.loggers.msgs["usw"]["sample"],
                    self.pipeline,
                    extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
            cmd_list.append(self.sample_dict[sample]["sample_pipeline_cmd"])
            # If not a negative control, add string that adds the job to the depends
            # list for downstream jobs to depend upon
            if "NTCcon" not in self.sample_dict[sample]['sample_name']:
                cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
                if self.pipeline == "pipe":
                    # Add to gatk depends list because #TODO
                    cmd_list.append(ad_config.UPLOAD_ARGS["depends_list_gatk"])

            if self.sample_dict[sample]["congenica_upload_cmd"]:
                cmd_list.append(self.congenica_input_cmd)
                cmd_list.append(
                    self.sample_dict[sample]["congenica_upload_cmd"]
                )
        return cmd_list

    def return_pipe_runwide_cmds(self):
        """
        RPKM is required per core panel in the run
        """
        cmd_list = []
        for core_panel in ["vcp1", "vcp2", "vcp3"]:
            if core_panel in (
                [
                    k['panel_settings']['capture_panel']
                    for k, v in self.sample_dict.keys()
                    ]
            ):
                cmd_list.append(self.create_rpkm_cmd(core_panel))
                cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])

        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list_recombined"])
        return cmd_list

    def write_dx_run_cmds(self, command_list):
        """
        Input = list of commands
        Takes a list of commands generated by start_building_dx_run_cmds and
        writes them to file.
        Returns = None
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["writing_cmds"],
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        with open(
            self.runfolder_obj.runfolder_dx_run_script, "w", encoding="utf-8"
        ) as dxrun_commands:
            # remove any None values from the command_list
            dxrun_commands.writelines(
                [line + "\n" for line in filter(None, command_list)]
            )

    def add_to_depends_list(self, fastq, depends_type):
        """
        Input = fastq file
        As jobs are set off the jobid is captured
        The job ids are built into a string which can be passed to any apps to
        ensure these jobs don't start until all specified jobs have sucessfully
        completed.
        However, some jobs should be excluded from the depends list, eg
        negative controls
        Returns = command which adds jobid to the bash string (string)
        """
        if "NTCcon" in fastq:
            return None
        elif depends_type == "depends_list":
            return

    def create_congenica_command_file(self):
        """
        Inputs = None
        Create the file which will hold congenica commands.
        Write the source command, activating the environment (the sdk).
        Returns = None
        """
        with open(
            self.runfolder_obj.congenica_dx_run_script, "w", encoding="utf-8"
        ) as congenica_script:
            congenica_script.write(ad_config.CMDS["sdk_source"] + "\n")
            congenica_script.write(ad_config.EMPTY_DEPENDS)

    def build_peddy_cmd(self):
        """
        Input = None
        Peddy is run once at the end of a WES run. Downloads required files
        from project
        Returns = dx run command for the peddy app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "peddy",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        dx_command = (
            ad_config.DX_RUN_CMDS["peddy"]
            + "Peddy"
            + ad_config.APP_INPUTS["peddy"]["project_name"]
            + self.runfolder_obj.nexus_project_name
            + ad_config.UPLOAD_ARGS["proj"]
            + self.nexus_project_id
            + ad_config.UPLOAD_ARGS["depends"]
            + ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        )
        return dx_command

    def create_sompy_cmd(self, sample, pannumber):
        """
        Build dx run command, to run sompy on a single vcf file
        Inputs:
            sample name
            Pan number
        Returns:
            dx run command for sompy (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "sompy",
            sample,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Get inputs based on output location within project
        vcf = (
            f"{self.runfolder_obj.nexus_proj_root}analysis_folder/Results/"
            f"{sample}/{sample}_MergedSmallVariants.genome.vcf"
        )
        dx_command_list = [
            ad_config.DX_RUN_CMDS["sompy"],
            sample,
            ad_config.APP_INPUTS["sompy"]["truth_vcf"],
            ad_config.APP_INPUTS["sompy"]["query_vcf"],
            vcf,
            ad_config.APP_INPUTS["sompy"]["tso"],
            ad_config.APP_INPUTS["sompy"]["skip"],
            self.dest_str,
            f"{self.runfolder_obj.nexus_proj_root }coverage/{pannumber}",
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]
        return "".join(map(str, dx_command_list))

    def create_multiqc_cmd(self):
        """
        Input = None
        MultiQC is run at the very end of the run, after all QC tools have been
        run.
        MultiQC requires a project to download data from, and a coverage level.
        Coverage level differs between panels. Lowest value for the panels on
        this run is used.
        Returns = dx run command (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "multiqc",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # for each fastq to be processed
        for fastq in self.samples_to_process:  # take read one
            if re.search(r"_R1_", fastq) or fastq.startswith("TSO"):
                # extract_Pan number and use this to determine which coverage
                # level is required
                pannumber = re.search(r"Pan\d+", fastq).group()
                # If required coverage for panel is less than current value of
                # lowest_coverage_level
                # set lowest_coverage_level to this level
                lowest_coverage_level = int(
                    panel_config.PANEL_DICT[pannumber]["multiqc_coverage_level"]
                )

        # build multiqc command
        dx_command = (
            ad_config.DX_RUN_CMDS["multiqc"]
            + "MultiQC"
            + ad_config.APP_INPUTS["multiqc"]["project_name"]
            + self.runfolder_obj.nexus_project_name
            + ad_config.APP_INPUTS["multiqc"]["coverage_level"]
            + str(lowest_coverage_level)
            + ad_config.UPLOAD_ARGS["proj"]
            + self.nexus_project_id
            + ad_config.UPLOAD_ARGS["depends"]
            + ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        )
        return dx_command

    def create_upload_multiqc_cmd(self):
        """
        Input = None
        The input to the upload_multiqc app is the html_report output of the
        multiqc app,
        in the format jobid:output_name
        Returns = dx run command for the upload_multiqc app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "upload multiqc",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        if self.pipeline == "tso500":
            multiqc_data_input = (
                f"{self.runfolder_obj.nexus_project_name}:/"
                f"{self.runfolder_obj.nexus_runfolder_subdir}/*"
                f"{self.runfolder_obj.runfolder_name}"
                f"{ad_config.CLUSTER_DENSITY_FILE_SUFFIX}"
            )
        else:
            multiqc_data_input = (
                f"{self.runfolder_obj.nexus_project_name}:/QC/*"
                f"{self.runfolder_obj.runfolder_name}"
                f"{ad_config.CLUSTER_DENSITY_FILE_SUFFIX}"
            )
        dx_command = "".join(
            [
                ad_config.DX_RUN_CMDS["upload_multiqc"],
                "Upload_MultiQC",
                ad_config.APP_INPUTS["upload_multiqc"]["multiqc_html"],
                ad_config.APP_INPUTS["upload_multiqc"]["data_input"],
                "$jobid:multiqc",
                ad_config.APP_INPUTS["upload_multiqc"]["data_input"],
                multiqc_data_input,
                ad_config.UPLOAD_ARGS["proj"],
                self.nexus_project_id,
                ad_config.UPLOAD_ARGS["depends"],
                ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
            ]
        )
        print(dx_command)
        return dx_command

    def create_sambamba_cmd(self, sample, pannumber):
        """
        Build dx run command, to run sambamba on a single bam file
        Inputs:
            sample name
            Pan number
        Returns:
            dx run command for sambamba (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "sambamba",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        # Get inputs based on output location within project
        bam_index = (
            f"{self.runfolder_obj.nexus_proj_root}analysis_folder/"
            f"Logs_Intermediates/StitchedRealigned/{sample}/{sample}.bam.bai"
        )
        bam = (
            f"{self.runfolder_obj.nexus_proj_root}analysis_folder/"
            f"Logs_Intermediates/StitchedRealigned/{sample}/{sample}.bam"
        )

        dx_command_list = [
            ad_config.DX_RUN_CMDS["sambamba"],
            sample,
            ad_config.APP_INPUTS["sambamba"]["bam"],
            bam,
            ad_config.APP_INPUTS["sambamba"]["bai"],
            bam_index,
            ad_config.APP_INPUTS["sambamba"]["coverage_level"],
            str(panel_config.PANEL_DICT[pannumber]["clinical_coverage_depth"]),
            ad_config.APP_INPUTS["sambamba"]["sambamba_bed"],
            f"{panel_config.PANEL_DICT[pannumber]['sambamba_bedfile']}",
            ad_config.APP_INPUTS["sambamba"]["cov_cmds"]
            % (
                str(panel_config.PANEL_DICT[pannumber]["coverage_min_basecall_qual"]),
                str(panel_config.PANEL_DICT[pannumber]["coverage_min_mapping_qual"]),
            ),
            self.dest_str,
            f"{self.runfolder_obj.nexus_proj_root}coverage/{pannumber}",
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ]
        return "".join(map(str, dx_command_list))

    def create_rpkm_cmd(self, core_panel_name):
        """
        Input = Name of core panel (str)
        The RPKM app requires a project id, bedfile and a string containing the
        pannumber(s) of all files that should be included in this analysis.
        Multiple pannumbers can be included in a single analysis.
        Return = dx run command for RPKM app for this analysis (string)
        """
        # Samples with different pannumbers can be included in the same RPKM
        # analysis (defined in ad_config).
        # The app takes these pan numbers as a string, and will seperate on
        # commas to identify multiple pan numbers

        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "RPKM",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        string_of_pannumbers_to_analyse = ",".join(
            panel_config.VCP_PANELS[core_panel_name]
        )
        # build RPKM command
        dx_command = (
            ad_config.DX_RUN_CMDS["rpkm"]
            + "RPKM_using_conifer"
            + ad_config.APP_INPUTS["rpkm"]["bed"]
            + self.nexus_rpkm_bed(panel_config.VCP_PANELS[core_panel_name][0])
            + ad_config.APP_INPUTS["rpkm"]["proj"]
            + self.runfolder_obj.nexus_project_name
            + ad_config.APP_INPUTS["rpkm"]["pannos"]
            + string_of_pannumbers_to_analyse
            + ad_config.UPLOAD_ARGS["proj"]
            + self.nexus_project_id
            + ad_config.UPLOAD_ARGS["depends_gatk"]
            + ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        )
        return dx_command

    def nexus_rpkm_bed(self, pannumber):
        """
        Construct the rpkm bed file path using the panel dictionaries
        """
        rpkm_bedfile = (
            f"{ad_config.BEDFILE_FOLDER}"
            f"{panel_config.PANEL_DICT[pannumber]['capture_pan_num']}_RPKM.bed"
        )
        return rpkm_bedfile

    def create_duty_csv_command(self):
        """
        Input = None
        The input to the duty_csv app is the dnanexus project name, and the
        pan numbers for tso samples, stg samples, and the custom panel whole
        capture for each core panel
        Returns = dx run command for the upload_multiqc app (string)
        """
        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["building_cmd"],
            "create_duty_csv",
            self.runfolder_obj.runfolder_name,
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )
        dx_command = (
            " ".join(
                [
                    f"{ad_config.DX_RUN_CMDS['duty_csv']}duty_csv",
                    ad_config.APP_INPUTS["duty_csv"]["project_name"]
                    + self.runfolder_obj.nexus_project_name,
                    ad_config.APP_INPUTS["duty_csv"]["tso_pannumbers"]
                    + ",".join(panel_config.TSO_VIAPATH_PANNUMBERS),
                    ad_config.APP_INPUTS["duty_csv"]["stg_pannumbers"]
                    + ",".join(panel_config.STG_PANNUMBERS),
                    ad_config.APP_INPUTS["duty_csv"]["cp_capture_pannos"]
                    + ",".join(panel_config.CP_CAPTURE_PANNOS),
                ]
            )
            + ad_config.UPLOAD_ARGS["proj"]
            + self.nexus_project_id
            + ad_config.UPLOAD_ARGS["depends"]
            + ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        )
        return dx_command

    def run_dx_run_commands(self):
        """
        Input = None
        Executes the bash script written in write_dx_run_cmds()
        Cleans and reports any standard error via the logfile and sys.log
        Outpt = None
        """

        # run a command to execute the bash script made above
        cmd = f"bash {self.runfolder_obj.runfolder_dx_run_script}"

        self.loggers.usw_rf.info(
            self.loggers.msgs["usw"]["running_cmds"],
            extra={"flag": self.loggers.log_flags["usw"]["info"]},
        )

        (_, err) = self.execute_subprocess_command(cmd)

        # if any standard error
        if err:
            # currently have a conflict between packages from different python
            # instances. parse stdout to ignore these
            cleaned_error = self.clean_stderr(err)
            # if stderr after ignorning lines referring to the package conflict
            # write to logger
            if cleaned_error:
                error_str = "\n".join(cleaned_error)
                # send message to logger/log file
                self.loggers.usw_rf.error(
                    self.loggers.msgs["usw"]["dx_run_err"],
                    self.runfolder_obj.runfolder_name,
                    cmd,
                    error_str,
                    extra={"flag": self.loggers.log_flags["usw"]["fail"]},
                )
        else:
            # write error message to log file
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["dx_run_err"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )

    # TODO check if this can be removed
    def clean_stderr(self, err):
        """
        Input = stderror (string)
        Currently have a conflict between packages from different python
        instances.
        This function parses stderr to remove these so real error messages
        stand out
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

    def check_backuprunfolder_errors(self):
        """
        Input = path to logfile(backup_runfolder.py logfile)
        The presence of expected success/failure messages are checked and
        reported
        Returns = None
        """
        # parse the output of the backup runfolder script
        # if error statement seen report it regardless of presence of success
        # statement. if success statement seen report it too.
        # set flags to avoid multiple reports

        upload_ok = False
        error_seen = []
        with open(
            self.runfolder_obj.backup_runfolder_logfile, "r", encoding="utf-8"
        ) as backup_logfile:
            for line in backup_logfile.readlines():
                if ad_config.BACKUP_RUNFOLDER_SUCCESS in line:
                    upload_ok = True
                if ad_config.BACKUP_RUNFOLDER_ERROR in line:
                    error_seen.append(line)
        if error_seen:
            self.loggers.usw_rf.error(
                self.loggers.msgs["usw"]["upload_rf_fail"],
                ";".join(error_seen),
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["fail"]},
            )
        if upload_ok:
            self.loggers.usw_rf.info(
                self.loggers.msgs["usw"]["upload_rf_success"],
                self.runfolder_obj.runfolder_name,
                extra={"flag": self.loggers.log_flags["usw"]["info"]},
            )
        return upload_ok


# TODO check these are being sent to the right people
# TODO convert this to using html
class PipelineEmails():
    """
    SQL emails should be sent to binfx for all pipelines
    Samples processed using each workflow are recorded in Moka using an
    insert query per sample
    Samples being processed emails should be sent to binfx for all runs, plus to
    additional recipeints for:
        WES --> WES email list
        Cancer runs --> m.neat
    """
    def __init__(self, runfolder_obj):
        """"""
        self.pipeline = runfolder_obj.pipeline
        # TODO fix this as think this returns all sample names not fastqs
        self.samples_dict = self.runfolder_obj.samples_dict
        self.workflows = [
            self.samples_dict[k]['panel_settings']['pipeline']
            for k in self.samples_dict.keys()
        ]
        self.sample_count = len(self.samples_dict)
        self.pipeline_started_subj = (
                    ad_config.MAIL_SETTINGS["pipeline_started_subj"] %
                    self.runfolder_obj.runfolder_name
                )
        self.samples_recipients = [ad_config.MAIL_SETTINGS['binfx_recipient']]
        if self.pipeline == 'wes':
            self.samples_recipients.append(
                ad_config.MAIL_SETTINGS['wes_samplename_emaillist']
                )
        elif self.pipeline in ['amp', 'tso500', 'archerdx']:
            self.samples_recipients.append(
                ad_config.MAIL_SETTINGS['oncology_ops_email']
            )
        # Base email string included in all emails
        self.base_email_str = "%s %s being processed using workflow(s) %s\n\n%s\n"
        # Additional email string included only in SQL emails
        self.sql_email_str = (
            "Please update Moka using the below queries and ensure"
            " that %s records are updated:\n\n%s"
        )

    def collect_queries(self):
        """
        Collect queries from the sample_dict (for all runs with per-sample queries)
        For those with run-level queries (wes), generate query
        """
        if self.pipeline == "wes":
            queries = self.return_wes_query()
        else:
            queries = [
                self.samples_dict[k]['SQL_query'] for k in self.samples_dict.keys()
            ]
        return "\n".join(queries)

    def return_wes_query(self):
        """
        Input = list of dnanumbers
        All samples processed using WES are recorded in moka using a single
        update query.
        Returns = query (str), workflow_name (str)
        """
        wes_dnanumbers = [
            self.samples_dict[k]['identifiers'][0] for k in self.sample_dict.keys()
            ]
        query = [
            ad_config.QUERIES["wes"]
            % (
                str(ad_config.SQL_IDS["WORKFLOWS"]["wes"]),
                str(ad_config.SQL_IDS["WES_TEST_STATUS"]["data_processing"]),
                ("','").join(wes_dnanumbers),
                str(ad_config.SQL_IDS["WES_TEST_STATUS"]["nextseq_sequencing"]),
            )
        ]
        return query

        # TODO add logging
        def send_sql_email(self, queries):
            """
            Construct pipeline started email. This is sent to the binfx team.
            Contains queries to record the pipeline versions emailed
            Call email sending module
            """
            sql_str = self.sql_email_str % (str(self.sample_count), queries)

            email_msg = self.base_email_str % (
                ad_config.EMAIL_HEADER,
                self.runfolder_obj.runfolder_name,
                ",".join(self.workflows),
                sql_str,
            )

            # Send SQL queries email
            self.email.send_email(
                recipients=ad_config.MAIL_SETTINGS["binfx_recipient"],
                email_subject=self.pipeline_started_subj,
                email_message=email_msg,
                email_priority=1,
            )

        # TODO add logging
        def send_samples_email(self, queries):
            """
            Send the samples being processed email. This informs the relevant parties
            that the pipeline has been started
            """
            email_msg = self.base_email_str % (
                ad_config.EMAIL_HEADER,
                self.runfolder_obj.runfolder_name,
                ",".join(self.workflows),
                (
                    f"{str(self.sample_count)} "
                    "samples are being processed"
                ),
                "",
            )

            self.email.send_email(
                recipients=self.samples_recipients,
                email_subject=self.pipeline_started_subj,
                email_message=email_msg,
                email_priority=1,
            )


if __name__ == "__main__":
    # Create a custom list object to hold sequencing runs
    runs = SequencingRuns()
    # Set list with runfolder objects
    runs.set_runfolders()
    # Call upload and workflow logic on runfolders
    runs.loop_through_runs()
