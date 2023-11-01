#!/usr/bin/python3
# coding=utf-8
"""upload_and_setoff_workflows.py

Upload NGS data to DNAnexus and trigger analysis workflows.
"""
import os
import re
from shutil import copyfile
from toolbox import toolbox
from ad_logger import ad_logger
from config import ad_config, panel_config
from ad_email.ad_email import AdEmail
from backup_runfolder.UACaller import UACaller
from itertools import chain
from typing import Union, Tuple


class SequencingRuns(object):
    """
    Collects sequencing runs and initiates runfolder processing for those sequencing
    runs requiring processing.

    Attributes
        runs_to_process (dict):         Object containing runs that require processing
                                        as key,value pairs
        script_logger (object):         Script-level logger
        processed_runfolders (list):    List of runfolders processed by the script
        num_processed_runfolders (int): Number of runfolders processed during this cycle

    Methods:
        set_runfolders()
            Update self.runfolders list with NGS runfolders in the runfolders directory
        requires_processing()
            Calls other methods to determine whether the runfolder requires processing
            (demultiplexing has finished successfully and the runfolder has not already
            been uploaded)
        already_uploaded()
            Checks for presence of upload agent logfile (denotes that the runfolder has
            already been processed).
        has_demultiplexed()
            Check if demultiplexing has already been performed and completed sucessfully
    """

    def __init__(self):
        """
        Constructor for the SequencingRuns class
        """
        self.runs_to_process = {}
        self.processed_runfolders = []
        self.script_logger = ad_logger.AdLogger(
            'usw', 'usw', toolbox.return_scriptlogfile('usw')
        ).get_logger()

    def setoff_processing(self) -> None:
        """
        Call methods to collect runfolders for processing
            :return None:
        """
        self.set_runfolders()
        if toolbox.test_upload_software(self.script_logger):
            for runfolder, rf_obj in self.runs_to_process.items():
                self.process_runfolder(runfolder, rf_obj)
            self.return_num_processed_runfolders()

    def set_runfolders(self) -> None:
        """
        Update self.runs_to_process dict with NGS runfolders in the runfolders directory
        that match the runfolder pattern, and require processing by the script
            :return None:
        """
        for folder in os.listdir(ad_config.RUNFOLDERS):
            if os.path.isdir(os.path.join(ad_config.RUNFOLDERS, folder)) and re.compile(
                ad_config.RUNFOLDER_PATTERN
            ).match(folder):
                self.script_logger.info(
                    self.script_logger.log_msgs["runfolder_identified"], folder
                )
                rf_obj = toolbox.RunfolderObject(folder, ad_config.TIMESTAMP)
                if self.requires_processing(rf_obj):
                    self.runs_to_process[folder] = rf_obj

    def requires_processing(self, rf_obj) -> bool:
        """
        Calls other methods to determine whether the runfolder requires processing
        (demultiplexing has finished successfully and the runfolder has not already been
        uploaded)
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
            :return bool:           Returns true if runfolder requires processing, else
                                    False
        """
        if (self.has_demultiplexed(rf_obj) and not self.already_uploaded(rf_obj)):
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_requires_proc"],
                rf_obj.runfolder_name
            )
            return True
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_prev_proc"],
                rf_obj.runfolder_name
            )
            return False


    def already_uploaded(self, rf_obj) -> bool:
        """
        Checks for presence of upload agent logfile (denotes that the runfolder has
        already been processed).
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
            :return (bool):         Returns True if runfolder already uploaded, else
                                    False
        """
        if os.path.isfile(rf_obj.upload_agent_logfile):
            self.script_logger.info(self.script_logger.log_msgs["ua_file_present"])
            return True
        else:
            # If file doesn't exist return false to continue, write to log file
            self.script_logger.info(self.script_logger.log_msgs["ua_file_absent"])
            return False

    def has_demultiplexed(self, rf_obj) -> bool:
        """
        Check if demultiplexing has already been performed and completed sucessfully
        Checks the demultiplex log file exists, and if present checks the expected
        success string is in the last line of the log file.
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
            :return (bool):         Return True if runfolder already demultiplexed, else
                                    False
        """
        if os.path.isfile(rf_obj.bcl2fastqlog_path):
            with open(rf_obj.bcl2fastqlog_path, "r", encoding="utf-8") as logfile:
                logfile_list = logfile.readlines()
                completed_strs = [
                    ad_config.STRINGS['demultiplexlog_tso500_msg'],
                    ad_config.STRINGS['demultiplex_success']
                ]
                if logfile_list:
                    if any(
                        re.search(success_str, logfile_list[-1])
                        for success_str in completed_strs
                    ):
                        self.script_logger.info(
                            self.script_logger.log_msgs["demux_complete"]
                        )
                        return True
                    else:
                        self.script_logger.info(self.script_logger.log_msgs["demux_failed"])
                        return False
                else:
                    # Write to logfile that not yet demultiplexed
                    self.script_logger.info(
                        self.script_logger.log_msgs["bcl2fastqlog_empty"]
                    )
        else:
            # Write to logfile that not yet demultiplexed
            self.script_logger.info(
                self.script_logger.log_msgs["not_yet_demultiplexed"]
            )
            return False

    def process_runfolder(self, runfolder, rf_obj):
        """
        if software tests pass, set up logging and pass rf_obj to the ProcessRunfolder
        class for processing, shutting down logs upon completion. Append to
        self.processed_runfolders
        """
        rf_obj.add_runfolder_loggers()  # Add runfolder loggers attribute
        process_runfolder_obj = ProcessRunfolder(rf_obj)

        for logger in rf_obj.rf_loggers.loggers:
            ad_logger.shutdown_logs(logger)  # Shut down logging
        self.processed_runfolders.append(runfolder)
        self.script_logger.info(
            self.script_logger.log_msgs["runfolder_processed"],
            process_runfolder_obj.rf_obj.runfolder_name,
        )

    def return_num_processed_runfolders(self):
        """"""
        num_processed_runfolders = toolbox.get_num_processed_runfolders(
            self.script_logger, "usw", self.processed_runfolders
        )
        setattr(self, 'num_processed_runfolders', num_processed_runfolders)


class ProcessRunfolder(object):
    """
    A new instance of this class is initiated for each runfolder being assessed. Calls
    methods to process a upload a runfolder including creation of DNAnexus project,
    upload of data, building and execution of dx run commands to set off sample
    workflows and apps, creation of congenica upload script, and sending of pipeline
    emails

    Attributes:
        rf_obj (obj):                       RunfolderObject object (contains
                                            runfolder-specific attributes)
        dnanexus_apikey (str):              DNAnexus auth token
        samples_obj (obj):                  CollectRunfolderSamples object (contains
                                            sample-specific attributes)
        users_dict (dict):                  Dictionary of users and admins requiring
                                            access to the DNAnexus project
        nexus_project_id (str):             Project ID, generated when the DNAnexus
                                            project is created
        nexus_identifiers (dict):           Dictionary containing project name and ID
        backup_runfolder (obj):             UACaller object with methods that can be
                                            called to upload files to the DNAnexus
                                            project
        upload_cmds (dict):                 Dictionary of commands for uploading files
                                            to the DNAnexus project
        pre_pipeline_upload_dict (dict):    Dict of files to upload prior to pipeline
                                            setoff, and commands

    Methods:
        get_users_dict()
            Create a dictionary of users and admins that require access to the DNAnexus
            project
        write_project_creation_script()
            Write the script that creates the DNAnexus project and shares it with the
            required users with the required access level
        run_project_creation_script()
            Set off the project creation script using subprocess, return project ID
        get_upload_cmds()
            Build file upload commands
        split_tso500_samplesheet()
            Split tso500 samplesheet into parts with x samples per samplesheet (no. 
            defined in ad_config.TSO_BATCH_SIZE) and write to runfolder
        create_file_upload_dict()
            Create dictionary of files to upload prior to setting off the pipeline, and
            the upload commands required
        pre_pipeline_upload()
            Uploads the files in the samples_obj.pre_pipeline_upload_dict for the
            runfolder. Calls the tso runfolder upload function if the runfolder is tso
        upload_to_dnanexus(filetype, file_upload_dict)
            Passes the command and file list in file_upload_dict to
            backup_runfolder.upload_files() which writes log messages to the upload
            agent log within the runfolder
        upload_tso_runfolder()
            Uploads the tso runfolder prior to setting off the run commands. Atempts the
            upload 5 times, and checks the output for errors. If errors exist, it will
            attempt to upload again
        upload_rest_of_runfolder()
            Backs up the rest of the runfolder, ignoring files dependent upon the type
            of run
        create_congenica_command_file()
            If there is a congenica upload required, create the congenica upload bash"
            script, which  is run manually after QC has passed
        run_dx_run_commands()
            Execute the dx run bash script
        post_pipeline_upload()
            Uploads the rest of the runfolder if not a tso run, and uploads the
            runfolder logfiles (upload_agent file is not uploaded because it is being
            written to as the upload is taking place)
    """

    def __init__(self, rf_obj):
        """
        Constructor for the RunfolderProcessor class
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
        """
        self.rf_obj = rf_obj
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["ad_version"],
            toolbox.git_tag(),
        )
        self.samples_obj = CollectRunfolderSamples(self.rf_obj)

        if self.samples_obj.samplename_list and self.samples_obj.samples_dict:  # If samples are present
            if not any(panno in panel_config.DEVELOPMENT_PANELS for panno in self.samples_obj.unique_pannos):
                self.rf_obj.rf_loggers.usw.info(
                    self.rf_obj.rf_loggers.usw.log_msgs["not_dev_run"],
                    self.rf_obj.samplesheet_path,
                )
                self.users_dict = self.get_users_dict()
                self.write_project_creation_script()
                self.nexus_identifiers = {
                    "proj_name": self.samples_obj.nexus_paths['proj_name'],
                    "proj_id": self.run_project_creation_script()
                    }
                self.backup_runfolder = UACaller(self.rf_obj, self.nexus_identifiers)
                self.upload_cmds = self.get_upload_cmds()
                self.pre_pipeline_upload_dict = self.create_file_upload_dict()
                self.pre_pipeline_upload()
                BuildDxCommands(
                    self.rf_obj, self.samples_obj, self.nexus_identifiers["proj_id"]
                    )
                self.create_congenica_command_file()
                self.run_dx_run_commands()
                PipelineEmails(self.rf_obj, self.samples_obj)
                self.post_pipeline_upload()
            else:
                self.rf_obj.rf_loggers.usw.info(
                    self.rf_obj.rf_loggers.usw.log_msgs["dev_run"],
                    self.rf_obj.samplesheet_path,
                )

    def get_users_dict(self) -> dict:
        """
        Create a dictionary of users and admins that require access to the DNAnexus
        project. This also includes dry lab dnanexus IDs if applicable for the samples
        in the runfolder. These are taken from the per-sample panel_stettings in the
        samples_dict. This is required because some samples are analysed at dry labs,
        with access to projects only given where there is a sample for that dry lab on
        the run
            :return (dict):     Dictionary of users and admins requiring access to the
                                DNAnexus project
        """
        dry_lab_list = set(
            [
                k
                for k, v in self.samples_obj.samples_dict.items()
                if v["panel_settings"]["drylab_dnanexus_id"]
            ]
        )
        return {
            "viewers": {
                "user_list": ad_config.DNANEXUS_USERS["viewers"].append(dry_lab_list),
                "permissions": "VIEW",
                },
            "admins": {
                "user_list": ad_config.DNANEXUS_USERS["admins"],
                "permissions": "ADMINISTER",
                },
            }

    def write_project_creation_script(self) -> None:
        """
        Write the script that creates the dnanexus project and shares it with the
        required users with the required access levels. The project is created using
        the project creation command which utilises the DNAnexus sdk. This command and
        the project sharing commands are written to a bash script
            :return None:
        """
        with open(
            self.rf_obj.proj_creation_script, "w", encoding="utf-8"
        ) as project_script:
            project_script.write(f"{ad_config.SDK_SOURCE}\n")
            project_script.write(
                ad_config.DX_CMDS["create_proj"]
                % (
                    ad_config.PROD_ORGANISATION,
                    self.samples_obj.nexus_paths['proj_name'],
                    self.dnanexus_apikey,
                )
            )
            # Give view and admin permissions for project
            for permissions_level in self.users_dict.keys():
                if self.users_dict[permissions_level]["user_list"]:
                    for user in self.users_dict[permissions_level]["user_list"]:
                        project_script.write(
                            ad_config.DX_CMDS["invite_user"] % (
                                user,
                                self.users_dict[permissions_level]['permissions'],
                                self.dnanexus_apikey,
                            )
                        )
                else:
                    self.rf_obj.rf_loggers.usw.info(
                        self.rf_obj.rf_loggers.usw.log_msgs["no_users"],
                        permissions_level,
                    )
            project_script.write("echo $project_id")  # Capture project id

    def run_project_creation_script(self) -> str:
        """
        Set off the project creation script using subprocess. The output of this command
        is checked to ensure it meets the expected success pattern
            :return projectid (str):    Project ID of the created project
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["creating_proj"],
            self.rf_obj.proj_creation_script,
        )
        project_creation_cmd = f"bash {self.rf_obj.proj_creation_script}"

        project_id, err, returncode = toolbox.execute_subprocess_command(
            project_creation_cmd, self.rf_obj.rf_loggers.usw
            )
        if returncode == 0:
            return project_id
        else:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["proj_creation_fail"],
                self.samples_obj.nexus_paths['proj_name'],
            )
            raise Exception  # Stop script

    def get_upload_cmds(self) -> dict:
        """
        Build file upload commands
            :return upload_cmds (dict): Dictionary of commands for uploading files to
                                        the DNAnexus project
        """
        upload_cmds = {
            "cd": ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                "/QC",
                ' '.join(self.rf_obj.cluster_density_files)
            ),
            "bcl2fastq_qc": ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                f"{self.samples_obj.nexus_paths['fastqs_dir']}/Stats",
                self.rf_obj.bcl2fastqstats_file
            ),
            "logfiles": ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths['logfiles_dir'],
                ' '.join(self.rf_obj.logfiles_to_upload)
            ),
        }
        if self.samples_obj.pipeline == "tso500":
            self.rf_obj.tso_ss_list = self.split_tso500_samplesheet()
            samplesheet_paths = [os.path.join(self.rf_obj.runfolderpath, ss) for ss in self.rf_obj.tso_ss_list]
            # TODO amend the upload directory for this cmd
            upload_cmds["runfolder_samplesheet"] = ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths['runfolder_name'],
                ' '.join(samplesheet_paths)
            )
        else:
            upload_cmds["fastqs"] = ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths['fastqs_dir'],
                self.samples_obj.fastqs_str
                )
            upload_cmds["runfolder_samplesheet"] = ad_config.DX_CMDS['file_upload_cmd'] % (
                self.rf_obj.dnanexus_apikey, self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths['fastqs_dir'],
                self.rf_obj.runfolder_samplesheet_path
            )
        return upload_cmds

    # TODO streamline this
    def split_tso500_samplesheet(self):
        """
        Split tso500 samplesheet into parts with x samples per samplesheet (no. 
        defined in ad_config.TSO_BATCH_SIZE) and write to runfolder
            :return (list):     Samplesheet names
        """    
        samplesheet_header = []
        samples = []
        no_sample_lines = 0
        expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        header_identified = False
        samplesheet_list = []

        # Read all lines from the sample sheet
        with open(self.rf_obj.runfolder_samplesheet_path) as samplesheet:
            for line in samplesheet.readlines():
                if any(header in line for header in expected_data_headers):
                    samplesheet_header.append(line)  # Extract header and add to list
                    header_identified = True
                elif not header_identified:  # Extract lines above the header and add to list
                    samplesheet_header.append(line)
                # skip empty lines (check first element of the line, after splitting on comma)
                elif header_identified and len(line.split(",")[0]) > 2:
                    samples.append(line)
                    no_sample_lines += 1
                # Skip empty lines
                elif len(line.split(",")[0]) < 2:
                    pass

        # Split samples into batches (size specified in config)
        batches = [
            samples[i:i + ad_config.TSO_BATCH_SIZE]
            for i in range(0, len(samples), ad_config.TSO_BATCH_SIZE)
        ]
        # Create new samplesheets named "PartXofY", add samplesheet to list
        # Capture path for samplesheet in runfolder
        for samplesheet_count, batch in enumerate(batches, start=1):
            #capture samplesheet file path to write samplesheet paths to the runfolder
            samplesheet_filepath = f'{self.rf_obj.runfolder_samplesheet_path.split(".csv")[0]}Part{samplesheet_count}of{len(batches)}.csv'
            # capture samplesheet name to write to list- use runfolder name
            samplesheet_name = f"{self.rf_obj.runfolder_name}_SampleSheetPart{samplesheet_count}of{len(batches)}.csv"
            samplesheet_list.append(samplesheet_name)
            with open(samplesheet_filepath, "w") as new_samplesheet:
                new_samplesheet.writelines(samplesheet_header)
                new_samplesheet.writelines(batch)
        samplesheet_list.append(self.rf_obj.samplesheet_name)
        return samplesheet_list

    def create_file_upload_dict(self) -> dict:
        """
        Create dictionary of files to upload prior to setting off the pipeline, and the
        upload commands required
            :return pre_pipeline_upload_dict (dict):    Dict of files to upload prior to
                                                        pipeline setoff, and commands
        """
        pre_pipeline_upload_dict = {
            "cluster density": {
                "cmd": self.upload_cmds["cd"],
                "files_list": self.rf_obj.cluster_density_files,
            },
        }
        if self.samples_obj.pipeline == "tso500":  # Add samplesheet entry       
            pre_pipeline_upload_dict['runfolder_samplesheet'] = {
                "cmd": self.upload_cmds["runfolder_samplesheet"],
                "files_list": [os.path.join(self.rf_obj.runfolderpath, ss) for ss in self.rf_obj.tso_ss_list],
            }
        else:
            pre_pipeline_upload_dict["fastqs"] = {
                "cmd": self.upload_cmds["fastqs"],
                "files_list": self.samples_obj.fastqs_list,
            }
            pre_pipeline_upload_dict["bcl2fastq_qc"] = {
                "cmd": self.upload_cmds["bcl2fastq_qc"],
                "files_list": [self.rf_obj.bcl2fastqstats_file],
            }
        return pre_pipeline_upload_dict

    def pre_pipeline_upload(self) -> None:
        """
        Uploads the files in the samples_obj.pre_pipeline_upload_dict for the runfolder.
        Calls the tso runfolder upload function if the runfolder is tso500
            :return None:
        """
        for filetype in self.pre_pipeline_upload_dict.keys():
            self.upload_to_dnanexus(filetype, self.pre_pipeline_upload_dict)
        if self.samples_obj.pipeline == "tso500":
            self.upload_tso_runfolder()

    def upload_to_dnanexus(self, filetype: str, file_upload_dict: dict) -> None:
        """
        Passes the command and file list in file_upload_dict to
        backup_runfolder.upload_files() which writes log messages to the upload agent
        log within the runfolder
            :param filetype (str):          Name of the file upload type
            :param file_upload_dict (dict): Dictionary of files for upload
            :return None:
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["uploading_files"], filetype
        )
        result = self.backup_runfolder.upload_files(
            file_upload_dict[filetype]["cmd"],
            file_upload_dict[filetype]["files_list"], filetype
        )
        if result == "success":
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["upload_success"], filetype
            )
        elif result == "fail":
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["upload_fail"],
                filetype, self.rf_obj.upload_agent_logfile
            )
        elif type(result) == list:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["nonexistent_files"], result
            )
            # TODO how should the above error be handled? (i.e. upload failures)

    def upload_tso_runfolder(self) -> None:
        """
        Uploads the tso runfolder prior to setting off the run commands. Atempts the
        upload 5 times, and checks the output for errors. If errors exist, it will
        attempt to upload again
            :return None:
        """
        backup_attempt_count = 0
        while backup_attempt_count < 5:  # Attempts to upload 5 times
            try:
                self.rf_obj.rf_loggers.usw.info(
                    self.rf_obj.rf_loggers.usw.log_msgs["TSO_backup_attempt"],
                    backup_attempt_count,
                )
                self.upload_rest_of_runfolder()
                backup_attempt_count += 1
            except Exception as exception:
                raise Exception(exception)

    def upload_rest_of_runfolder(self) -> None:
        """
        Backs up the rest of the runfolder. First copies the samplesheet intto the
        project, then specifies which files to ignore (excludes BCL files for all runs
        except tso500 runs for which they are needed for demultiplexing on DNAnexus).
        Calls backup_runfolder.upload_rest_of_runfolder(ignore), passing a run-dependent
        ignore string, and the this handles the runfolder upload. backup_runfolder
        writes log messages to the upload agent log within the runfolder
            :return None:
        """
        # Try to copy samplesheet into project
        if os.path.exists(self.rf_obj.samplesheet_path):
            copyfile(
                self.rf_obj.samplesheet_path,
                self.rf_obj.runfolder_samplesheet_path,
            )
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["ss_copy_success"],
                self.rf_obj.runfolder_samplesheet_path,
            )
        else:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["ss_copy_fail"],
            )
        # Build backup_runfolder.py commands, ignoring some files
        if self.samples_obj.pipeline == "tso500":
            ignore = "DNANexus_upload_started,add_runfolder_to_nexus_cmds"
        else:
            ignore = "/L00,DNANexus_upload_started,add_runfolder_to_nexus_cmds"

        try:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["uploading_rf"],
                ignore,
                self.rf_obj.backup_runfolder_logfile,
            )
            self.backup_runfolder.upload_rest_of_runfolder(ignore)
        except Exception as exception:
            self.rf_obj.rf_loggers.usw.exception(
                self.rf_obj.rf_loggers.usw.log_msgs["upload_rf_error"],
                exception,
                self.rf_obj.backup_runfolder_logfile,
                self.rf_obj.upload_agent_logfile,
            )
            raise Exception  # Stop script

    def create_congenica_command_file(self) -> None:
        """
        If there is a congenica upload required, create the congenica upload bash file,
        which is run manually after QC has passed. Writes the source command, activating
        the environment (the sdk). Specific upload commands are echoed into this file
        at a later point when the pipeline run script is executed
            :return None:
        """
        if self.samples_obj.pipeline in ("pipe", "wes"):
            with open(
                self.rf_obj.congenica_dx_run_script, "w", encoding="utf-8"
            ) as congenica_script:
                congenica_script.write(f"{ad_config.SDK_SOURCE}\n")
                congenica_script.write(ad_config.EMPTY_DEPENDS)

    def run_dx_run_commands(self) -> None:
        """
        Execute the dx run bash script
            :return None:
        """
        dx_run_cmd = f"bash {self.rf_obj.runfolder_dx_run_script}"

        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["running_cmds"],
        )
        out, err, returncode = toolbox.execute_subprocess_command(
            dx_run_cmd, self.rf_obj.rf_loggers.usw
            )
        if err:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["dx_run_err"],
                self.rf_obj.runfolder_name, dx_run_cmd, err
            )
        else:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["dx_run_success"],
                self.rf_obj.runfolder_name,
            )

    def post_pipeline_upload(self) -> None:
        """
        Uploads the rest of the runfolder if not a tso run, and uploads the runfolder
        logfiles (upload_agent file is not uploaded because it is being written to as
        the upload is taking place)
            :return None:
        """
        if self.samples_obj.pipeline != "tso500":
            self.upload_rest_of_runfolder()

        file_upload_dict = {
            "logfiles": {
                "cmd": self.upload_cmds['logfiles'],
                "files_list": self.rf_obj.logfiles_to_upload,
            }
        }
        for filetype in file_upload_dict.keys():
            self.upload_to_dnanexus(filetype, file_upload_dict)


class CollectRunfolderSamples(object):
    """
    Collect attributes for all samples within the runfolder

    Attributes
        param rf_obj (obj):             RunfolderObject object (contains
                                        runfolder-specific attributes)
        samplename_list (list):         List of sample names identified from the
                                        samplesheet
        pipeline (str):                 Pipeline name
        nexus_runfolder_suffix (str):   String of '_' delimited unique library numbers,
                                        and WES batch numbers if run is a WES run
        nexus_paths (dict):             Dictionary of paths within the DNAnexus project
                                        that are required for building dx commands
        samples_dict (dict):            Dictionary of SampleObject per sample,
                                        containing sample-specific attributes
        fasqs_list (list):              List of all sample fastqs in the run
        fastqs_str (str):               Space separated string of sample fastqs with
                                        each fastq encased in quotation marks
        unique_pannos (list):           List of unique panel numbers within the run

    Methods
        get_samplename_list()
            Read samplesheet to create a list of samples for the run
        get_pipeline()
            Use self.samplename_list and the config.PANEL_DICT to get a list of pipeline
            names for samples in the run. Returns the most frequent pipeline name in the
            set
        get_nexus_runfolder_suffix()
            Get runfolder suffix for the DNAnexus project name. This consists of the
            library number, followed by the WES batch if the run is a WES run
        capture_library_numbers()
            Parse the names in self.samplename_list to identify the library prep numbers
        capture_wes_batch_numbers()
            Parse the names in self.samplename_list to identify the WES batch numbers
        get_nexus_paths()
            Build nexus paths, using NGS run numbers (and batch numbers in the case of
            WES)
        get_samples_dict()
            Create a SampleObject per sample, containing sample-specific properties, and
            add each SampleObject to a larger samples_dict
        check_fastqs()
            Check all fastqs in fastq dir were correctly identified from the samplesheet
            and stored in the sample dict, and add any missing samples to the samples
            dict
        fastq_not_undetermined()
            Determine whether the fastq is an undetermined fastq
        fastq_not_miseq()
            Determine whether the fastq is a MiSeq-created fastq (contains "-Pan")
        get_fastqs_list()
            Return a list of sample fastqs for the run
        get_fastqs_str()
            Return a space separated string of sample fastqs with each fastq encased in
            quotation marks
    """
    def __init__(self, rf_obj):
        """
        Constructor for the CollectRunfolderSamples class
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
        """
        self.rf_obj = rf_obj
        self.samplename_list = self.get_samplename_list()
        if self.samplename_list:
            self.pipeline = self.get_pipeline()
            self.nexus_runfolder_suffix = self.get_nexus_runfolder_suffix()
            self.nexus_paths = self.get_nexus_paths()
            self.unique_pannos = set([sample[1] for sample in self.samplename_list])     
            self.samples_dict = self.get_samples_dict()
            if self.pipeline != "tso500":
                    # tso500 run is not demultiplexed locally so there are no fastqs
                    # All other runfolders have fastqs in the BaseCalls directory
                    # Check fastqs in fastq dir were correctly identified from the
                    # samplesheet and add any missing samples to the samples dict
                    self.check_fastqs()
                    self.fastqs_list = self.get_fastqs_list()
                    self.fastqs_str = self.get_fastqs_str()

    def get_samples_dict(self) -> dict:
        """
        Create a SampleObject for each sample which returns a sample dictionary
        containing the sample_name, pannum, panel_settings and fastqs paths for that
        sample. Add each SampleObject to a larger samples_dict
            :return samples_dict (dict):    Dictionary of SampleObject per sample,
                                            containing sample-specific attributes
        """
        samples_dict = {}
        for sample_name in self.samplename_list:
            sample_name = sample_name[0]
            sample_obj = SampleObject(
                sample_name, self.pipeline, self.rf_obj, self.nexus_paths,
            )
            samples_dict[sample_name] = sample_obj.return_sample_dict()
        return samples_dict

    def get_samplename_list(self) -> list:
        """
        Read samplesheet to create a list of samples for the run. Reads file into list
        and loops through in reverse allowing us to access sample names and stop at
        column headers, skipping the file header. Creates upload agent file if samples
        have been identified, to prevent processing by other script runs
            :return samplename_list (list(tuple)):  List of tuples containing sample
                                                    name and pan num for each sample
        """
        samplename_list = []
        if os.path.exists(self.rf_obj.samplesheet_path):
            with open(
                self.rf_obj.samplesheet_path, "r", encoding="utf-8"
            ) as samplesheet_stream:
                for line in reversed(samplesheet_stream.readlines()):
                    if line.startswith("Sample_ID") or "[Data]" in line:
                        break
                    # Skip empty lines (check first element of the line, after
                    # splitting on comma)
                    elif len(line.split(",")[0]) < 2:
                        pass
                    else:  # If it's a line detailing a sample, get sample name and pan num
                        panel_number = ""
                        sample_name = line.split(",")[0]
                        for pannum in panel_config.PANELS:
                            if pannum in line:
                                panel_number = pannum
                        samplename_list.append((sample_name, panel_number))
            if samplename_list:  # If samples identified
                # Create upload agent file (prevents processing by other script runs)
                open(
                    self.rf_obj.rf_loggers.upload_agent.filepath, "w", encoding="utf-8"
                    ).close()
            return samplename_list
        else:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["ss_missing"],
            )

    def get_pipeline(self) -> str:
        """
        Use samplename_list and the config.PANEL_DICT to get a list of pipeline
        names for samples in the run. Generates error mesage if there is more than one
        piepline name in the list. Returns the most frequent pipeline name in the set
            :return (str):  Pipeline name
        """
        pipelines_list = []
        for sample in self.samplename_list:
            pipelines_list.append(panel_config.PANEL_DICT[sample[1]]['pipeline'])
        if len(set(pipelines_list)) > 1:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["multiple_pipeline_names"],
                pipelines_list,
            )
        # Get pipeline from pipelines_list
        return max(set(pipelines_list), key=pipelines_list.count)

    def get_nexus_runfolder_suffix(self) -> str:
        """
        Get the runfolder suffix for the DNAnexus project name. This consists of the
        library number, followed by the WES batch if the run is a WES run
            :return (str):  String of '_' delimited unique library numbers, and WES
                            batch numbers if run is a WES run
        """
        library_numbers = self.capture_library_numbers()
        if self.pipeline == "wes":
            library_numbers.extend(self.capture_wes_batch_numbers())
        return "_".join(library_numbers)

    def capture_library_numbers(self) -> list:
        """
        Parse the names in self.samplename_list to identify the library prep numbers.
        These are the first elements in the sample names (before the first underscore).
        These numbers are used as the suffix for the DNAnexus project name (along with
        the WES batch number in the case of WES runs). If no library prep numbers are
        found, raise an error
            :return (list) | None:   List of unique library numbers
        """
        library_numbers = []
        for samplename in self.samplename_list[0]:
            if "_" in str(samplename):  # Check there are underscores present
                # Split on underscores to capture library number e.g. ONC100 or NGS100
                library_numbers.append(samplename.split("_")[0])
        if library_numbers:  # Should always be library numbers found
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["library_nos_identified"],
                ", ".join(library_numbers),
            )
            return list(set(library_numbers))
        else:  # Prompt a slack alert
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["library_no_err"],
                self.rf_obj.runfolder_name,
            )
            raise Exception  # Stop script

    def capture_wes_batch_numbers(self) -> list:
        """
        Parse the names in self.samplename_list to identify the WES batch numbers. This
        along with the library prep number is used as the DNAnexus project name suffix
            :return wes_batch_numbers_list (list):  List of unique WES batch numbers
        """
        wes_batch_numbers_list = []
        for samplename in self.samplename_list[0]:
            if "WES" in str(samplename):
                # Capture WES batch (WES followed by digits)
                # Optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", samplename).group()
                wes_batch_numbers_list.append(wesbatch.replace("_", ""))
        if wes_batch_numbers_list:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["wes_batch_nos_identified"],
                ", ".join(wes_batch_numbers_list),
            )
            return list(set(wes_batch_numbers_list))
        else:  # Prompt a slack alert
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["wes_batch_nos_missing"],
                self.rf_obj.runfolder_name,
            )
            raise Exception  # Stop script

    def get_nexus_paths(self) -> dict:
        """
        Build nexus paths, using NGS run numbers (and batch numbers in the case of WES).
        Builds the DNAnexus project name using the config-defined project prefix
        (denoting status of the DNAnexus project), followed by the runfolder name and
        the and self.nexus_runfolder_suffix as the suffix (library prep / WES batch
        numbers). Uses the DNAnexus project name to build additional paths required for
        later dx run commands
            :return nexus_paths (dict):     Dictionary of paths within the DNAnexus
                                            project that are required for building dx
                                            commands
        """
        nexus_paths = {}
        if self.pipeline == "tso500":
            fastq_type = "tso_fastqs"
        else:
            fastq_type = "fastqs"

        nexus_paths["runfolder_name"] = (
            f"{self.rf_obj.runfolder_name}_{self.nexus_runfolder_suffix}"
            )
        nexus_paths["fastqs_dir"] = (
            f"/{nexus_paths['runfolder_name']}/{ad_config.FASTQ_DIRS[fastq_type]}/"
            )
        nexus_paths["proj_name"] = (
                f"{ad_config.DNANEXUS_PROJECT_PREFIX}{nexus_paths['runfolder_name']}"
            )
        nexus_paths["proj_root"] = f"{nexus_paths['proj_name']}:/"
        nexus_paths["runfolder_subdir"] = (
            f"{nexus_paths['proj_root']}{nexus_paths['runfolder_name']}/"
            )
        nexus_paths["logfiles_dir"] = f"/{nexus_paths['runfolder_name']}/Logfiles/"
        nexus_paths["samplesheet"] = (
            f"/{nexus_paths['proj_root']}/{self.rf_obj.samplesheet_name}"
            )
        return nexus_paths

    def check_fastqs(self) -> None:
        """
        Check all fastqs in fastq dir were correctly identified from the samplesheet and
        stored in the sample dict, and add any missing samples to the samples dict.
        Loops through all the files in the given folder, identifies if each file is a
        fastq, and checks it is not an undetermined fastq and not a miseq-created fastq,
        and. Then checks whether the fastq matches a sample in the sample_dict and if
        not, adds it as a sample to self.samples_dict
            :return None:
        """
        missing_samples = []
        for fastq_dir_file in os.listdir(self.rf_obj.fastq_dir_path):
            if fastq_dir_file.endswith("fastq.gz"):
                self.rf_obj.rf_loggers.usw.info(
                    self.rf_obj.rf_loggers.usw.log_msgs["checking_fastq"],
                    fastq_dir_file
                )
                if self.fastq_not_undetermined(
                    fastq_dir_file
                ) and self.fastq_not_miseq(fastq_dir_file):
                    # Check if fastq matches a sample in the sample_dict, if not add it
                    sample_name = [
                        sample_name for sample_name in self.samples_dict.keys()
                        if sample_name in fastq_dir_file
                    ]
                    if sample_name:
                        self.rf_obj.rf_loggers.usw.info(
                            self.rf_obj.rf_loggers.usw.log_msgs["sample_match"],
                            fastq_dir_file,
                            sample_name,
                        )
                    else:
                        self.rf_obj.rf_loggers.usw.info(
                            self.rf_obj.rf_loggers.usw.log_msgs["sample_mismatch"],
                            fastq_dir_file,
                        )
                        sample_name = re.sub(
                            "R[0-9]_001.fastq.gz", "", fastq_dir_file
                        )
                        missing_samples.append(fastq_dir_file)
                        # Add the sample to the sample_obj
            else:
                self.rf_obj.rf_loggers.usw.info(
                    self.rf_obj.rf_loggers.usw.log_msgs["not_fastq"], fastq_dir_file
                )
        for sample_name in missing_samples:
            self.samples_dict[sample_name] = SampleObject(
                    sample_name, self.pipeline, self.rf_obj, self.nexus_paths,
                ).return_sample_dict()

    def fastq_not_undetermined(self, fastq_dir_file: str) -> Union[bool, None]:
        """
        Determine whether the fastq is an undetermined fastq
            :return True | None:    Return True if undetermined, else return None
        """
        # Exclude undetermined
        if not fastq_dir_file.startswith("Undetermined"):
            return True
        else:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["undetermined_identified"],
                fastq_dir_file,
            )

    def fastq_not_miseq(self, fastq_dir_file: str) -> Union[bool, None]:
        """
        Determine whether the fastq is a MiSeq-created fastq (contains "-Pan")
            :return True | None:    Return True if created by MiSeq, else return None
        """
        if "-Pan" not in fastq_dir_file:
            return True
        else:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["miseq_fastq_identified"],
                fastq_dir_file,
            )            

    def get_fastqs_list(self):
        """
        Return a list of sample fastqs for the run
            :return fastqs_list (list):     List of all sample fastqs in the run
        """
        fastqs_list = []
        for sample_name in self.samples_dict.keys():
            fastqs_list.extend(
                [
                    self.samples_dict[sample_name]['fastqs'][read]['path']
                    for read, path in self.samples_dict[sample_name]['fastqs'].items()
                ]
            )
        return fastqs_list

    def get_fastqs_str(self):
        """
        Return a space separated string of sample fastqs with each fastq encased in
        quotation marks
            :return fastqs_str (str):   Space separated string of sample fastqs with
                                        each fastq encased in quotation marks
        """
        quotation_marked_list = []
        for fastq in self.fastqs_list:
            quotation_marked = f"'{fastq}'"
            quotation_marked_list.append(quotation_marked)
        return " ".join(quotation_marked_list)


# TODO eventually adapt this class to use the seglh-naming library
class SampleObject:
    """
    Collect sample-specific attributes for a sample

    Attributes
        rf_obj (obj):               RunfolderObject object (contains runfolder-specific
                                    attributes)
        sample_name (str):          Sample name
        pipeline (str):             Pipeline name
        nexus_paths (dict):         Dictionary of paths within the DNAnexus project that
                                    are required for building dx commands
        neg_control (bool):         True if sample is a negative control, else False
        workflow_name (str):        Workflow name
        pannum (str):               Panel number that matches a config-defined panel
                                    number, or None if pannum not valid
        panel_settings (dict):      Config defined panel settings specific to the sample
                                    panel number
        primary_identifier (str):   Primary sample identifier
        secondary_identifier (str): Secondary sample identifier
        fastqs_dict (dict):         Dictionary containing R1 and R2 fastqs and their
                                    local and cloud paths
        query (str):                Return sample SQL query (sample-level query)
        sample_pipeline_cmd (str):  Dx run command for the sample workflow
        congenica_upload_cmd (str): Dx run command for the congenica upload

    Methods
        check_negative_control()
            Determine whether sample is a negative control
        check_reference_sample()
            Check if sample is a reference sample by checking if reference ids are
            present in fastq name
        get_workflow_name()
            Get workflow name from the app ID by parsing the workflow metadata using dx
            describe and jq
        find_pannum()
            Extract panel number from sample name using regular expression
        validate_pannum(pannum)
            Check whether pan number is valid
        get_identifiers()
            For WES and PIPE samples, extract DNA number from sample name. For oncology
            samples, collect 3rd and 4th identifiers, setting secondary_identifier to
            null if the sample is a negative control (these only have one identifier)
        get_fastqs_dict()
            Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        get_sample_SQL_query()
            Call functions to construct SQL query for the sample (sample-level query)
        return_rd_query()
            Create a query per sample using the DNA number
        return_oncology_query()
            Create a query per sample using IDs from the samplename (3rd and 4th)
            elements
        build_sample_dx_run_cmd()
            Build sample-level dx run commands for the workflow and congenica upload
        create_wes_cmd()
            Construct dx run command for WES workflow
        return_congenica_cmd()
            Construct dx run command for congenica upload where required by calling
            build_congenica_sftp_cmd or build_congenica_cmd
        build_congenica_sftp_cmd()
            Construct dx run command for congenica upload for samples requiring upload
            using the SFTP app
        build_congenica_input_cmd()
            Build command to run decision_support_tool_inputs.py to generate the inputs
            for the upload cmd
        build_congenica_cmd()
            Construct dx run command for congenica upload for samples requiring upload
            using the standard congenica upload app
        create_pipe_cmd()
            Construct dx run command for PIPE workflow
        get_vcfeval_cmd_string()
            Get command string for input to vcfeval stage of PIPE workflow
        get_fhprs_cmd_string()
            Get command string for input FH_PRS stage of PIPE workflow
        get_polyedge_cmd_string()
            Get command string for polyedge stage of PIPE workflow
        get_masked_reference_cmd_string()
            Get input string for masked reference input for BWA stage of PIPE workflow,
            if specified for the pan number in the config
        create_snp_cmd()
            Construct dx run command for SNP workflow
        create_fastqc_cmd()
            Build dx run command to run fastqc
        return_sample_dict()
            Return sample dictionary with all collected information about the sample
    """
    def __init__(self, sample_name, pipeline, rf_obj, nexus_paths):
        """
        Constructor for the SampleObject class
            :param sample_name (str):       Sample name
            :param pipeline (str):          Pipeline name
            :param rf_obj (obj):            RunfolderObject object (contains
                                            runfolder-specific attributes)
            :param nexus_paths (dict):      Dictionary of paths within the DNAnexus
                                            project that are required for building dx
                                            commands
        """
        self.rf_obj = rf_obj
        self.sample_name = sample_name
        self.pipeline = pipeline
        self.nexus_paths = nexus_paths
        self.neg_control = self.check_negative_control()
        self.reference_sample = self.check_reference_sample()
        self.workflow_name = self.get_workflow_name()
        self.pannum = self.find_pannum()
        self.panel_settings = panel_config.PANEL_DICT[self.pannum]
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["sample"],
            self.panel_settings['panel_name'],
            self.sample_name,
        )
        self.primary_identifier, self.secondary_identifier = self.get_identifiers()
        self.fastqs_dict = self.get_fastqs_dict()
        self.query = self.get_sample_SQL_query()
        (
            self.sample_pipeline_cmd,
            self.congenica_upload_cmd
        ) = self.build_sample_dx_run_cmd()

    def check_negative_control(self) -> bool:
        """
        Determine whether sample is a negative control
            :return (bool): True if sample is a negative control, else False
        """
        ntcon_strings = ["00000", "NTCcon", "NTC000", "NC000"]
        if any(identifier in self.sample_name for identifier in ntcon_strings):
            return True
        else:
            return False

    def check_reference_sample(self) -> bool:
        """
        Check if sample is a reference sample by checking if reference ids are present
        in fastq name
            :return (bool):             True if reference sample, else None
        """
        if any(
            f"_{ref_sample_id}_" in self.sample_name
            for ref_sample_id in ad_config.REF_SAMPLE_IDS
        ):
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["reference_sample"],
                self.sample_name
            )
            return True

    def get_workflow_name(self) -> str:
        """
        Get workflow name from the app ID by parsing the workflow metadata using dx
        describe and jq
            :return workflow_name (str): Workflow name
        """
        if self.pipeline == "tso500":
            (
                workflow_name, err, returncode
            ) = toolbox.execute_subprocess_command(
                f"dx describe {ad_config.NEXUS_IDS['APPS'][self.pipeline]} "
                "--json | jq -r '(.name)'", self.rf_obj.rf_loggers.usw
            )
        else:
            (
                workflow_name, err, returncode
            ) = toolbox.execute_subprocess_command(
                "dx describe "
                f"{ad_config.NEXUS_IDS['WORKFLOWS'][self.pipeline]} "
                "--json | jq -r '\"\(.folder)/\(.name)\"'",
                self.rf_obj.rf_loggers.usw
            )
        return workflow_name

    def find_pannum(self) -> Union[str, None]:
        """
        Extract panel number from sample name using regular expression
            :return pannum (str) | None:    Panel number that matches a config-defined
                                            panel number, or None if pannum not valid
        """
        pannum = str(re.search(r"Pan\d+", self.sample_name).group())
        if self.validate_pannum(pannum):
            return pannum

    def validate_pannum(self, pannum) -> Union[bool, None]:
        """
        Check whether pan number is valid
            :return True | None:    True if pan number is valid, else None
        """
        if str(pannum) in panel_config.PANELS:
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["recognised_panno"],
                self.sample_name,
                pannum
            )
            return True
        else:
            self.rf_obj.rf_loggers.usw.error(
                self.rf_obj.rf_loggers.usw.log_msgs["unrecognised_panno"],
                self.sample_name
            )

    def get_identifiers(self) -> Tuple[str, str]:
        """
        For WES and PIPE samples, extract DNA number from sample name. For oncology
        samples, collect 3rd and 4th identifiers, setting secondary_identifier to null
        if the sample is a negative control (these only have one identifier)
            :return primary_identifier (str):    Primary sample identifier
            :return secondary_identifier (str):  Secondary sample identifier
        """
        if self.pipeline in ("wes", "pipe", "snp"):
            # Extract the dna number from sample name
            primary_identifier = self.sample_name.split("_")[2]
            secondary_identifier = False
        elif self.pipeline in ("tso500", "archerdx", "amp"):
            # Collect 3rd and 4th elements (identifiers)
            primary_identifier, secondary_identifier = self.sample_name.split("_")[2:4]
            # negative controls only have one ID so set id2 to null
            if self.neg_control:
                secondary_identifier = "NULL"
        return primary_identifier, secondary_identifier

    def get_fastqs_dict(self) -> dict:
        """
        Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        tso500 runs are not demultiplexed locally so have no local fastq path. All other
        runfolders have fastqs in the BaseCalls directory
            :return fastqs_dict (dict):     Dictionary containing R1 and R2 fastqs and
                                            their local and cloud paths
        """
        fastqs_dict = {"R1": {}, "R2": {}}
        for read in ["R1", "R2"]:
            if self.pipeline == "tso500":
                fastqs_dict[read] = {
                    "name": None,
                    "path": None,
                    "nexus_path": f"{self.nexus_paths['proj_root']}{ad_config.FASTQ_DIRS['tso_fastqs']}{self.sample_name}/{self.sample_name}_R1.fastq.gz",
                }
            else:
                # TODO add improved error logging here
                matches = [self.sample_name, f"_{read}_"]
                fastq_name = list(
                    fastq_path for fastq_path
                    in os.listdir(self.rf_obj.fastq_dir_path)
                    if all([substring in fastq_path for substring in matches])
                )
                fastq_name = fastq_name[0]
                nexus_path = f"{self.nexus_paths['proj_root']}{self.nexus_paths['fastqs_dir']}{fastq_name}"
                fastqs_dict[read] = {
                    "name": fastq_name,
                    "path": os.path.join(
                        self.rf_obj.fastq_dir_path, fastq_name
                        ),
                    "nexus_path": nexus_path,
                }
        return fastqs_dict

    def get_sample_SQL_query(self) -> str:
        """
        Call functions to construct SQL query for the sample (sample-level query)
            :return query (str):    Return sample SQL query (sample-level query)
        """
        if self.pipeline in ("pipe", "snp"):
            query = self.return_rd_query()
        elif self.pipeline in ("tso500", "archerdx", "amp"):
            query = self.return_oncology_query()
        elif self.pipeline in "wes":
            # This query is constructed at the runfolder level, not the sample level
            query = False
        return query

    def return_rd_query(self) -> str:
        """
        Create a query per sample using the DNA number
            :return query (str):    Sample SQL rare disease query
        """
        pipeline_version = str(ad_config.SQL_IDS["WORKFLOWS"][self.pipeline])
        rd_query = ad_config.QUERIES["customrun"] % (
            f"'{self.primary_identifier}','{pipeline_version}',"
            f"'{self.rf_obj.runfolder_name}'"
        )
        return rd_query

    def return_oncology_query(self) -> str:
        """
        Create a query per sample using IDs from the samplename (3rd and 4th) elements.
        These are recorded along with the pipeline version, run name, and panel ID.
            :return query (str):    Sample SQL oncology query
        """
        pipeline_version = str(ad_config.SQL_IDS["WORKFLOWS"][self.pipeline])
        panel_id = self.pannum.replace("Pan", "")

        onc_query = ad_config.QUERIES["oncology"] % (
            f"'{self.primary_identifier}','{self.secondary_identifier}',"
            f"'{self.rf_obj.runfolder_name}','{pipeline_version}','{panel_id}'"
        )
        return onc_query

    def build_sample_dx_run_cmd(self) -> Tuple[str, str]:
        """
        Build sample-level dx run commands for the workflow and congenica upload
            :return workflow_cmd (str):         Dx run command for the sample workflow
            :return congenica_upload_cmd (str): Cmd for running the script to generate
                                                inputs to the congenica upload commands
        """
        if self.pipeline == "wes":
            workflow_cmd = self.create_wes_cmd()
            congenica_upload_cmd = self.return_congenica_cmd()
        elif self.pipeline == "pipe":
            workflow_cmd = self.create_pipe_cmd()
            congenica_upload_cmd = self.return_congenica_cmd()
        elif self.pipeline == "snp":
            workflow_cmd = self.create_snp_cmd()
            congenica_upload_cmd = False, False
        elif self.pipeline == "archerdx":
            workflow_cmd = self.create_fastqc_cmd()
            congenica_upload_cmd = False, False
        elif self.pipeline == "tso500":
            workflow_cmd = self.create_fastqc_cmd()  # Pipeline cmd is built at whole-run level
            congenica_upload_cmd = False, False
        return workflow_cmd, congenica_upload_cmd

    def create_wes_cmd(self) -> str:
        """
        Construct dx run command for WES workflow
            :return (str):  Dx run command string
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"], "WES", self.sample_name
        )
        return " ".join([
            f'{ad_config.DX_CMDS["wes"]}{self.sample_name}',
            f'{ad_config.STAGE_INPUTS["wes"]["fastqc1_reads"]}'
            f'{self.fastqs_dict["R1"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["wes"]["fastqc2_reads"]}'
            f'{self.fastqs_dict["R2"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["wes"]["sentieon_samplename"]}'
            f'{self.sample_name}',
            f'{ad_config.STAGE_INPUTS["wes"]["picard_bed"]}'
            f'{self.panel_settings["hsmetrics_bedfile"]}',
            f'{ad_config.STAGE_INPUTS["wes"]["sambamba_bed"]}'
            f'{self.panel_settings["sambamba_bedfile"]}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey,
        ])

    def return_congenica_cmd(self) -> Union[str, None]:
        """
        Construct dx run command for congenica upload for non-reference samples by
        calling build_congenica_sftp_cmd or build_congenica_cmd. If a sample requires
        congenica upload, there are 2 methods. If congenica project ID is specified as
        'SFTP' within the config it means the sample requires upload via SFTP, else if
        congenica_project ID is specified it means it can be uploaded using the upload
        agent. Both congenica apps app take inputs in the format jobid.outputname which
        ensures the job doesn't run until the vcfs have been created. App inputs are
        created by a python script, which is called immediately before the app is set
        off, and the script output (app inputs) is captured by the variable $analysisid
            :return tuple(str, str) | None: Dx run commands (congenica input command,
                                            congenica upload command), or None if sample
                                            is a reference sample
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["congenica_upload_required"],
            self.nexus_paths['proj_name'],
        )
        if self.reference_sample:
            return None
        else:
            # If project is specified then upload via upload agent
            if self.panel_settings["congenica_project"] == "SFTP":  # SFTP upload cmd
                congenica_upload_cmd = self.build_congenica_sftp_cmd()
            else:  # Upload agent command
                congenica_upload_cmd = self.build_congenica_cmd()
            return congenica_upload_cmd

    def build_congenica_sftp_cmd(self) -> str:
        """
        Construct dx run command for congenica upload for samples requiring upload
        using the SFTP app. Samples requiring upload by SFTP require patient-specific
        info to be pre-added into Congenica by the scientists. Takes BAM and VCF inputs,
        and does not require project IDs, IR templates or name
            :return congenica_upload_cmd (str): Dx run command for the congenica upload
                                                (SFTP app)
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "congenica sftp",
            self.sample_name,
        )
        congenica_upload_cmd = (" ".join([
            f'{ad_config.DX_CMDS["congenica_sftp"]}'
            f'congenica_SFTP_upload_{self.sample_name}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            (
                ad_config.UPLOAD_ARGS["token"] %
                self.rf_obj.dnanexus_apikey).replace(
                    ")", f"' >> {self.rf_obj.congenica_dx_run_script}"
            ),
        ]))
        return congenica_upload_cmd

    def build_congenica_cmd(self) -> str:
        """
        Construct dx run command for congenica upload for samples requiring upload
        using the standard congenica upload app. Takes BAM and VCF inputs, along with
        config-specified inputs congenica project ID, credentials, IR template and
        sample name
            :return congenica_upload_cmd (str): Dx run command for the congenica upload
                                                (standard congenica upload app)
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "congenica",
            self.sample_name,
        )
        congenica_upload_cmd = (" ".join([
            f'{ad_config.DX_CMDS["congenica_app"]}congenica_{self.sample_name}',
            f'-icongenica_project={str(self.panel_settings["congenica_project"])}',
            f'-icredentials={self.panel_settings["congenica_credentials"]}',
            f'-iIR_template={self.panel_settings["congenica_IR_template"]}',
            f'{ad_config.APP_INPUTS["congenica_upload"]["samplename"]}'
            f'{self.sample_name}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            (
                ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey
                ).replace(")", f"' >> {self.rf_obj.congenica_dx_run_script}")
                ]))
        return congenica_upload_cmd

    def create_pipe_cmd(self) -> str:
        """
        Construct dx run command for PIPE workflow. Congenica requires variant calling
        to be restricted in the pipeline, in some cases to prevent incidental findings.
        The variant caller pads bed files by 100bp by default so this may need to be
        overruled. The panel dictionary default is to give a value of 0, which turns off
        this padding. An example of the use of this is for STG BrCa who require padding
        of +/- 11bp (bed files are padded +/-10bp) so 1bp padding is applied.
            :return (str):  Dx run command string
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "PIPE",
            self.sample_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["pipe"]}{self.sample_name}',
            f'{ad_config.STAGE_INPUTS["pipe"]["fastqc_reads"]}'
            f'{self.fastqs_dict["R1"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["fastqc_reads"]}'
            f'{self.fastqs_dict["R2"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["bwa_reads1"]}'
            f'{self.fastqs_dict["R1"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["bwa_reads2"]}'
            f'{self.fastqs_dict["R2"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["bwa_rg_sample"]}'
            f'{self.sample_name}',
            f'{ad_config.STAGE_INPUTS["pipe"]["sambamba_bed"]}'
            f'{self.panel_settings["sambamba_bedfile"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["sambamba_min_base_qual"]}'
            f'{str(self.panel_settings["coverage_min_basecall_qual"])}',
            f'{ad_config.STAGE_INPUTS["pipe"]["sambamba_min_mapping_qual"]}'
            f'{str(self.panel_settings["coverage_min_mapping_qual"])}',
            f'{ad_config.STAGE_INPUTS["pipe"]["sambamba_cov_level"]}'
            f'{str(self.panel_settings["clinical_coverage_depth"])}',
            ad_config.STAGE_INPUTS["pipe"]["sambamba_filter_cmds"],
            ad_config.STAGE_INPUTS["pipe"]["sambamba_excl_dups"],
            ad_config.STAGE_INPUTS["pipe"]["sambamba_excl_failed_qual"],
            ad_config.STAGE_INPUTS["pipe"]["sambamba_count_overl_mates"],
            self.get_vcfeval_cmd_string(),
            self.get_fhprs_cmd_string(),
            f'{ad_config.STAGE_INPUTS["pipe"]["fhprs_bed"]}'
            f'{panel_config.FH_PRS_BEDFILE}',
            self.get_polyedge_cmd_string(),
            self.get_masked_reference_cmd_string(),
            f'{ad_config.STAGE_INPUTS["pipe"]["picard_bed"]}'
            f'{self.panel_settings["hsmetrics_bedfile"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["picard_capturetype"]}'
            f'{self.panel_settings["capture_type"]}',
            f'{ad_config.STAGE_INPUTS["pipe"]["gatk_padding"]}'
            f'{str(panel_config.PIPE_HAPLOTYPE_CALLER_PADDING)}',
            f'{ad_config.STAGE_INPUTS["pipe"]["filter_vcf_bed"]}'
            f'{self.panel_settings["variant_calling_bedfile"]}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey,
        ])

    def get_vcfeval_cmd_string(self) -> str:
        """
        Get command string for input to vcfeval stage of PIPE workflow. If sample is not
        NA12878 we want to skip the vcfeval stage (the app default is skip=False)
            :return (str):  App input string
        """
        # Set prefix as samplename
        prefix_str = (
            f'{ad_config.STAGE_INPUTS["pipe"]["happy_prefix"]}{self.sample_name}'
        )
        if self.reference_sample:
            skip_str = f'{ad_config.STAGE_INPUTS["pipe"]["happy_skip"]}false'
        else:
            skip_str = f'{ad_config.STAGE_INPUTS["pipe"]["happy_skip"]}true'

        return " ".join([prefix_str, skip_str])

    def get_fhprs_cmd_string(self) -> str:
        """
        Get command string for input FH_PRS stage of PIPE workflow. If sample is
        specified as requiring FH analysis in the config, set skip to False (the app
        default is skip=True), and specify instance type for human exome app and specify
        outptut as both VCF and GVCF
            :return fh_prs_cmd_string: App input string
        """
        if self.panel_settings["FH"]:
            fh_prs_cmd_string = " ".join([
                ad_config.STAGE_INPUTS['pipe']['fhprs_skip'],
                "--instance-type",
                f"{ad_config.NEXUS_IDS['STAGES']['pipe']['gatk']}="
                f'{ad_config.STAGE_INPUTS["pipe"]["fhprs_instance"]}',
                ad_config.STAGE_INPUTS['pipe']['gatk_vcf_format'],
                ad_config.PIPE_FH_GATK_TIMEOUT_ARGS,
            ])
        else:
            fh_prs_cmd_string = ""
        return fh_prs_cmd_string

    def get_polyedge_cmd_string(self) -> str:
        """
        Get command string for polyedge stage of PIPE workflow. If sample is specified
        as requiring polyedge analysis in the config, set skip to False (the app default
        is skip=True) and specify gene chrom and start / end inputs
            :return polyedge_cmd_string (str):  App input string
        """
        if self.panel_settings["polyedge"]:
            polyedge_cmd_string = " ".join([
                f'{ad_config.STAGE_INPUTS["pipe"]["polyedge_gene"]}'
                f'{self.panel_settings["polyedge"]["gene"]}',
                f'{ad_config.STAGE_INPUTS["pipe"]["polyedge_chrom"]}'
                f'{str(self.panel_settings["polyedge"]["chrom"])}',
                f'{ad_config.STAGE_INPUTS["pipe"]["polyedge_poly_start"]}'
                f'{str(self.panel_settings["polyedge"]["poly_start"])}',
                f'{ad_config.STAGE_INPUTS["pipe"]["polyedge_poly_end"]}'
                f'{str(self.panel_settings["polyedge"]["poly_end"])}',
                ad_config.STAGE_INPUTS["pipe"]["polyedge_skip"],
            ])
        else:
            polyedge_cmd_string = ""
        return polyedge_cmd_string

    def get_masked_reference_cmd_string(self) -> str:
        """
        Get input string for masked reference input for BWA stage of PIPE workflow, if
        specified for the pan number in the config
            :return masked_reference_cmd_string (str):  Masked reference input string
        """
        if self.panel_settings["masked_reference"]:
            masked_reference_cmd_string = (
                f"{ad_config.STAGE_INPUTS['pipe']['bwa_ref']}"
                f"{self.panel_settings['masked_reference']}"
            )
        else:
            masked_reference_cmd_string = ""
        return masked_reference_cmd_string

    def create_snp_cmd(self) -> str:
        """
        Construct dx run command for SNP workflow
            :return (str):  Dx run command string
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "SNP",
            self.sample_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["snp"]}{self.sample_name}',
            f'{ad_config.STAGE_INPUTS["snp"]["fastqc1_reads"]}'
            f'{self.fastqs_dict["R1"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["snp"]["fastqc2_reads"]}'
            f'{self.fastqs_dict["R2"]["nexus_path"]}',
            f'{ad_config.STAGE_INPUTS["snp"]["sentieon_samplename"]}{self.sample_name}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey,
        ])

    def create_fastqc_cmd(self) -> str:
        """
        Build dx run command to run fastqc
            :return (str): Dx run command for fastqc app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "fastqc",
            self.sample_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["fastqc"]}FASTQC-{self.sample_name}',
            f'-ireads={self.fastqs_dict["R1"]["nexus_path"]}',
            f'-ireads={self.fastqs_dict["R2"]["nexus_path"]}',
            f'{ad_config.UPLOAD_ARGS["dest"]}{self.nexus_paths["proj_root"]}',
            ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey,
        ])

    def return_sample_dict(self) -> dict:
        """
        Return sample dictionary with all collected information about the sample
            :return (dict): Collected information about the sample
        """
        return {
            "sample_name": self.sample_name,
            "neg_control": self.neg_control,
            "identifiers": {
                "primary": self.primary_identifier,
                "secondary": self.secondary_identifier,
            },
            "pannum": self.pannum,
            "panel_settings": self.panel_settings,
            "fastqs": self.fastqs_dict,
            "SQL_query": self.query,
            "sample_pipeline_cmd": self.sample_pipeline_cmd,
            "congenica_upload_cmd": self.congenica_upload_cmd,
        }


class BuildDxCommands(object):
    """
    Build run-wide commands for runfolder, and write sample-level commands from the
    samples_obj along with the run-wide commands to the dx run script.

    Attributes:
        rf_obj (obj):                   RunfolderObject object (contains runfolder-specific
                                        attributes)
        samples_obj (obj):              CollectRunfolderSamples object (contains sample-specific
                                        attributes
        nexus_project_id (str):         Project ID, generated when the DNAnexus project is
                                        created
        dnanexus_apikey (str):          DNAnexus auth token
        dx_cmd_list (list):             List of dx run commands for the project
        dx_postprocessing_cmds (list):  List of dx run commands to run after the TSO app. TSO
                                        runs only

    Methods:
        build_dx_cmds()
            Build dx run commands (pipeline-dependent) by calling the relevant functions
            and appending to the dx_cmd_list. This includes both sample workflow-level
            commands (self.return_sample_workflow_cmds()), and runwide commands
        return_tso_runwide_cmds()
            Collect runwide commands for tso500 runs. Includes tso500 app, fastqc,
            sompy, sambamba, multiqc and duty_csv. TSO commands are all generated within
            this function as the dependency order is different for this pipeline
        create_tso500_cmd()
            Build dx run command for tso500 docker app
        get_tso_analysis_options()
            Determine whether its a novaseq run from the runfoldername, and return the
            relevant tso500 app input string
        get_tso_instance_type()
            If run contains high throughput tso pannumbers, return the high throughput
            instance type (larger instance), else return low throughput instance type
        create_sompy_cmd()
            Build dx run command to run sompy on a single VCF file
        create_sambamba_cmd()
            Build dx run command to run sambamba on a single BAM file
        return_multiqc_cmds()
            Create list of multiqc commands (for running multiqc and upload multiqc
            apps) by calling the relevant methods
        create_multiqc_cmd()
            Build dx run command to run MultiQC for the run. MultiQC is run after all
            QC tools have been run
        create_upload_multiqc_cmd()
            Build dx run command to run upload_multiqc app for the run. This uploads the
            MultiQC data to the genomics server. The input to the upload_multiqc app is
            the html_report output of the multiqc app in the format jobid:output_name
        return_sample_workflow_cmds()
            Return sample-level commands. This includes the sample workflow command,
            and congenica input and upload commands if required for the sample type
        return_wes_runwide_cmds()
            Collect runwide commands for WES runs as a list. This includes peddy
        create_peddy_cmd()
            Build dx run command to run peddy for the project. Run once at the end of a
            WES run and downloads required files from the project
        return_pipe_runwide_cmds()
            Collect runwide commands for PIPE runs as a list. This includes RPKM (single
            command per vcp panel)
        create_rpkm_cmd()
            Build dx run command to run RPKM for a core panel
        create_duty_csv_cmd()
            Build dx run command to run create_duty_csv app for the run
        write_dx_run_cmds()
            Write dx run commands to the dx run script for the runfolder
    """
    def __init__(
        self, rf_obj: object, samples_obj: object, nexus_project_id: str
            ):
        """
        Constructor for the BuildDxCommands class
            :param rf_obj (obj):            RunfolderObject object (contains
                                            runfolder-specific attributes)
            :param samples_obj (obj):       CollectRunfolderSamples object (contains
                                            sample-specific attributes)
            :param nexus_project_id (str):  Project ID, generated when the DNAnexus
                                            project is created
        """
        self.rf_obj = rf_obj
        self.samples_obj = samples_obj
        self.nexus_project_id = nexus_project_id
        with open(
            ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
        ) as token_file:
            self.dnanexus_apikey = token_file.readline().rstrip()  # Auth token
        # Update script log file to say what is being done.
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmds"]
        )
        self.dx_cmd_list, self.dx_postprocessing_cmds = self.build_dx_cmds()
        self.write_dx_run_cmds(  # Write commands to file
            self.dx_cmd_list, self.rf_obj.runfolder_dx_run_script
        )
        if self.samples_obj.pipeline == "tso500":
            self.write_dx_run_cmds(  # Write commands to TSO post-processing file
                self.dx_postprocessing_cmds, self.rf_obj.post_run_dx_run_script
            )

    def build_dx_cmds(self) -> list:
        """
        Build dx run commands (pipeline-dependent) by calling the relevant functions and
        appending to the dx_cmd_list. This includes both sample workflow-level commands
        (self.return_sample_workflow_cmds()), and runwide commands
            :return None:
        """
        dx_cmd_list = []
        dx_postprocessing_cmds = []
        # Get sample workflow-level commands
        if self.samples_obj.pipeline == "tso500":
            dx_cmd_list, dx_postprocessing_cmds = self.return_tso_runwide_cmds()
        else:
            dx_cmd_list.extend(self.return_sample_workflow_cmds())

            # Get pipeline-specific run-wide commands. SNP, ADX and ONC do not have
            # pipeline-specific run-wide commands
            if self.samples_obj.pipeline == "wes":
                dx_cmd_list.extend(self.return_wes_runwide_cmds())
            if self.samples_obj.pipeline == "pipe":
                dx_cmd_list.extend(self.return_pipe_runwide_cmds())

            # Get run-wide commands that apply to all sequencing runs
            dx_cmd_list.extend(self.return_multiqc_cmds())
            dx_cmd_list.append(self.create_duty_csv_cmd())

            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["cmds_built"]
            )
        return dx_cmd_list, dx_postprocessing_cmds

    def return_tso_runwide_cmds(self):
        """
        Collect runwide commands for tso500 runs as a list. This includes tso500 app,
        fastqc, sompy, sambamba, multiqc and duty_csv. TSO commands are all generated
        within this function as the dependency order is different for this pipeline
            :return dx_cmd_list (list):     List of runwide commands for tso runs
            :dx_postprocessing_cmds (list): Post-processing commands for tso runs
        """
        dx_cmd_list = []
        dx_postprocessing_cmds = []
        sambamba_cmds_list = []
        # Remove base samplesheet as we only want to use split samplesheets
        for tso_ss in self.rf_obj.tso_ss_list:
            if tso_ss != self.rf_obj.samplesheet_name:
                dx_cmd_list.append(self.create_tso500_cmd(tso_ss))
                        
        for sample_name in self.samples_obj.samples_dict.keys():
            # Append all fastqc commands to cmd_list
            dx_postprocessing_cmds.append(
                self.samples_obj.samples_dict[sample_name]["sample_pipeline_cmd"]
            )
            dx_postprocessing_cmds.append(ad_config.UPLOAD_ARGS["depends_list"])
            sambamba_cmds_list.append(
                self.create_sambamba_cmd(
                    sample_name,
                    self.samples_obj.samples_dict[sample_name]['pannum']
                    )
                )
            # Exclude negative controls from the depends list as the NTC coverage
            # calculation can often fail. We want the coverage report for the NTC sample
            # to help assess contamination. Only add to depends_list if job ID from
            # previous command is not empty
            if not self.samples_obj.samples_dict[sample_name]['neg_control']:
                sambamba_cmds_list.append(ad_config.UPLOAD_ARGS["depends_list"])

            if "HD200" in sample_name:
                dx_postprocessing_cmds.append(
                    self.create_sompy_cmd(
                        sample_name,
                        self.samples_obj.samples_dict[sample_name]['pannum']
                        )
                    )
                # Only add to depends_list if job ID from previous command
                # is not empty
                dx_postprocessing_cmds.append(ad_config.UPLOAD_ARGS["depends_list"])

        dx_postprocessing_cmds.extend(self.return_multiqc_cmds())
        # Set off after as they are not depended upon by MultiQC but are required for
        # duty_csv
        dx_postprocessing_cmds.extend(sambamba_cmds_list)
        dx_postprocessing_cmds.append(self.create_duty_csv_cmd())

        return dx_cmd_list, dx_postprocessing_cmds

    def create_tso500_cmd(self, tso_ss) -> str:
        """
        Build dx run command for tso500 docker app
            :param tso_ss (str):        TSO samplesheet
            :return dx_run_cmd (str):   Dx run command for tso500 app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "TSO500",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["tso500"]}{self.rf_obj.runfolder_name}',
            f'{ad_config.APP_INPUTS["tso500"]["docker"]}'
            f'{ad_config.NEXUS_IDS["FILES"]["tso500_docker"]}',
            f'{ad_config.APP_INPUTS["tso500"]["samplesheet"]}'
            f'{self.nexus_project_id}:{self.samples_obj.nexus_paths["runfolder_name"]}/{tso_ss}',
            f'{ad_config.APP_INPUTS["tso500"]["project_name"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["tso500"]["runfolder_name"]}'
            f'{self.samples_obj.nexus_paths["runfolder_name"]}',
            self.get_tso_analysis_options(),
            self.get_tso_instance_type(),
            f'{ad_config.UPLOAD_ARGS["dest"]}'
            f'{self.samples_obj.nexus_paths["proj_root"]}',
            ad_config.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_apikey,
        ])

    def get_tso_analysis_options(self) -> str:
        """
        Determine whether its a novaseq run from the runfoldername, and return the
        relevant tso500 app input string
            :return analysis_options (str): Analysis options for the tso500 app
        """
        if ad_config.NOVASEQ_ID in self.rf_obj.runfolder_name:
            tso500_analysis_options = "--isNovaSeq "
        else:
            tso500_analysis_options = ""
        return (
            f'{ad_config.APP_INPUTS["tso500"]["analysis_options"]}'
            f'{tso500_analysis_options}'
            )

    def get_tso_instance_type(self) -> str:
        """
        If run contains high throughput tso pannumbers, return the high throughput
        instance type (larger instance), else return the low throughput instance type
            :return instance_str (str): Instance type command for tso500 app execution
        """
        if any(
            panel_config.PANEL_DICT[pannumber]["throughput"] == "high"
            for pannumber in self.samples_obj.unique_pannos
        ):
            return f"--instance-type {ad_config.APP_INPUTS['tso500']['ht_instance']}"
        else:
            return f"--instance-type {ad_config.APP_INPUTS['tso500']['lt_instance']}"

    def create_sompy_cmd(self, sample: str, pannumber: str) -> str:
        """
        Build dx run command to run sompy on a single VCF file
            :param sample (str):    Sample name
            :param pannumber (str): Config-defined pan number for sample
            :return (str):          Dx run command for sompy app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"], "sompy", sample
        )
        return " ".join([
            f'{ad_config.DX_CMDS["sompy"]}{sample}',
            ad_config.APP_INPUTS["sompy"]["truth_vcf"],
            # Get inputs based on output location within project
            f'{ad_config.APP_INPUTS["sompy"]["query_vcf"]}'
            f"{self.nexus_project_id}:analysis_folder/Results/"
            f"{sample}/{sample}_MergedSmallVariants.genome.vcf",
            ad_config.APP_INPUTS["sompy"]["tso"],
            ad_config.APP_INPUTS["sompy"]["skip"],
            f'{ad_config.UPLOAD_ARGS["dest"]}'
            f'{self.samples_obj.nexus_paths["proj_root"]}coverage/{pannumber}',
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ])

    def create_sambamba_cmd(self, sample: str, pannumber: str) -> str:
        """
        Build dx run command to run sambamba on a single BAM file
            :param sample (str):    Sample name
            :param pannumber (str): Config-defined pan number for sample
            :return (str):          Dx run command for sambamba app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "sambamba",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["sambamba"]}{sample}',
            f'{ad_config.APP_INPUTS["sambamba"]["bam"]}'
            f"{self.samples_obj.nexus_paths['proj_root']}analysis_folder/"
            f"Logs_Intermediates/StitchedRealigned/{sample}/{sample}.bam",
            f'{ad_config.APP_INPUTS["sambamba"]["bai"]}'
            f"{self.samples_obj.nexus_paths['proj_root']}analysis_folder/"
            f"Logs_Intermediates/StitchedRealigned/{sample}/{sample}.bam.bai",
            f'{ad_config.APP_INPUTS["sambamba"]["coverage_level"]}'
            f'{str(panel_config.PANEL_DICT[pannumber]["clinical_coverage_depth"])}',
            f'{ad_config.APP_INPUTS["sambamba"]["sambamba_bed"]}'
            f'{panel_config.PANEL_DICT[pannumber]["sambamba_bedfile"]}',
            ad_config.APP_INPUTS["sambamba"]["cov_cmds"]
            % (
                str(panel_config.PANEL_DICT[pannumber]["coverage_min_basecall_qual"]),
                str(panel_config.PANEL_DICT[pannumber]["coverage_min_mapping_qual"]),
            ),
            f'{ad_config.UPLOAD_ARGS["dest"]}'
            f'{self.samples_obj.nexus_paths["proj_root"]}coverage/{pannumber}',
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
        ])

    def return_multiqc_cmds(self) -> list:
        """
        Create list of multiqc commands (for running multiqc and upload multiqc apps) by
        calling the relevant methods
            :return cmd_list (str): List of multiqc commands
        """
        cmd_list = []
        cmd_list.append(self.create_multiqc_cmd())
        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
        cmd_list.append(self.create_upload_multiqc_cmd())
        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
        return cmd_list

    def create_multiqc_cmd(self) -> str:
        """
        Build dx run command to run MultiQC for the run. MultiQC is run after all QC
        tools have been run. Requires a project to download data from, and a coverage
        level. Coverage level differs between panels. The lowest value for the panels on
        the run is used.
            :return (str): Dx run command for MultiQC app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "multiqc",
            self.rf_obj.runfolder_name,
        )
        coverage_level = list(
            set(
                [
                    v["multiqc_coverage_level"] for k, v
                    in panel_config.CAPTURE_PANEL_DICT.items()
                    if v["pipeline"] == self.samples_obj.pipeline
                ]
            )
        )[0]
        return " ".join([
            f'{ad_config.DX_CMDS["multiqc"]}MultiQC',
            f'{ad_config.APP_INPUTS["multiqc"]["project_name"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["multiqc"]["coverage_level"]}{str(coverage_level)}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends"],
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey],
        )

    def create_upload_multiqc_cmd(self) -> str:
        """
        Build dx run command to run upload_multiqc app for the run. This uploads the
        MultiQC data to the genomics server. The input to the upload_multiqc app is the
        html_report output of the multiqc app in the format jobid:output_name
            :return (str): Dx run command for upload_multiqc app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "upload multiqc",
            self.rf_obj.runfolder_name,
        )
        if self.samples_obj.pipeline == "tso500":
            multiqc_data_input = (
                f"{self.samples_obj.nexus_paths['runfolder_subdir']}/"
                f"{ad_config.STRINGS['lane_metrics_suffix']}"
            )
        else:
            multiqc_data_input = (
                f"{self.samples_obj.nexus_paths['proj_name']}:/QC/*"
                f"{self.rf_obj.runfolder_name}"
                f"{ad_config.STRINGS['lane_metrics_suffix']}"
            )
        return " ".join(
            [
                f'{ad_config.DX_CMDS["upload_multiqc"]}Upload_MultiQC',
                ad_config.APP_INPUTS["upload_multiqc"]["multiqc_html"],
                f'{ad_config.APP_INPUTS["upload_multiqc"]["data_input"]}$jobid:multiqc',
                f'{ad_config.APP_INPUTS["upload_multiqc"]["data_input"]}'
                f'{multiqc_data_input}',
                f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
                ad_config.UPLOAD_ARGS["depends"],
                ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey,
            ]
        )

    def return_sample_workflow_cmds(self) -> list:
        """
        Return sample-level commands. This includes the sample workflow command,
        and congenica input and upload commands if required for the sample type
            :return cmd_list (list):    List of per-sample commands
        """
        cmd_list = []
        for sample_name in self.samples_obj.samples_dict.keys():
            self.rf_obj.rf_loggers.usw.info(
                self.rf_obj.rf_loggers.usw.log_msgs["sample"],
                self.samples_obj.pipeline,
                sample_name
            )
            cmd_list.append(
                self.samples_obj.samples_dict[sample_name]["sample_pipeline_cmd"]
                )
            # If not a negative control, add string that adds the job to the depends
            # list for downstream jobs to depend upon
            if not self.samples_obj.samples_dict[sample_name]['neg_control']:
                cmd_list.append(ad_config.UPLOAD_ARGS["depends_list"])
                if self.samples_obj.pipeline == "pipe":
                    # Add to gatk depends list because RPKM must depend only upon the
                    # sample workflows completing successfully, whilst other downstream
                    # apps depend on all prior jobs completing succesfully
                    cmd_list.append(ad_config.UPLOAD_ARGS["depends_list_gatk"])

            if self.samples_obj.pipeline in ["wes", "pipe"]:
                cmd_list.append(self.build_congenica_input_cmd())
                cmd_list.append(
                    self.samples_obj.samples_dict[sample_name]["congenica_upload_cmd"]
                )
        return cmd_list

    def build_congenica_input_cmd(self) -> str:
        """"""
        # Decision support tool python script is run after each dx run command, taking
        # analysis and project name as input, and printing the required inputs to the
        # command line which are required by the congenica upload script $jobid is a
        # bash variable which will be populated by when run on the command line. The
        # python script has three inputs - the analysisID ($jobid), -t is the DSS and -p
        # is the DNAnexus project the analysis is running in
        cmd = (
            "analysisid=$(source /usr/local/bin/miniconda3/etc/profile.d/conda.sh; "
            f"&& cd {ad_config.PROJECT_DIR} && "
            "conda activate python3.10.6 && python3 -m decision_support_tool_inputs "
            f"-a $jobid -t congenica -p {self.nexus_project_id} "
            f"-r {self.rf_obj.runfolder_name})"
            )
        return cmd

    def return_wes_runwide_cmds(self) -> list:
        """
        Collect runwide commands for WES runs as a list. This includes peddy.
            :return cmd_list (list):    List of runwide commands for WES runs
        """
        return [self.create_peddy_cmd()]

    def create_peddy_cmd(self) -> str:
        """
        Build dx run command to run peddy for the project. Run once at the end of a WES
        run and downloads required files from the project
            :return (str):  Dx run command for peddy app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "peddy",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["peddy"]}Peddy',
            f'{ad_config.APP_INPUTS["peddy"]["project_name"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends"],
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey]
        )

    def return_pipe_runwide_cmds(self) -> list:
        """
        Collect runwide commands for PIPE runs as a list. This includes RPKM (single
        command per vcp panel)
            :return cmd_list (list):    List of runwide commands for PIPE runs
        """
        cmd_list = []
        for core_panel in ["vcp1", "vcp2", "vcp3"]:            
            if core_panel in (
                [
                    self.samples_obj.samples_dict[k]['panel_settings']['panel_name']
                    for k, v in self.samples_obj.samples_dict.items()
                    ]
            ):
                core_panel_pannos = [
                    self.samples_obj.samples_dict[k]['pannum']
                    for k, v in self.samples_obj.samples_dict.items()
                    if self.samples_obj.samples_dict[k]['panel_settings']['panel_name'] == core_panel
                ]

                # Make sure there are enough samples for exome depth and RPKM
                # TODO check this has the desired effect
                if len(self.samples_obj.samples_dict.items()) >= 3:
                    if panel_config.CAPTURE_PANEL_DICT[core_panel]["ed_readcount_bedfile"]:
                        cmd_list.append(self.create_ed_readcount_cmd(core_panel))

                        for panno in set(core_panel_pannos):
                            cmd_list.append(self.create_ed_cnvcalling_cmd(panno))

                    cmd_list.append(self.create_rpkm_cmd(core_panel))

        cmd_list.append(ad_config.UPLOAD_ARGS["depends_list_recombined"])
        return cmd_list

    def create_rpkm_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command to run RPKM for a core panel. RPKM app requires project id,
        bedfile and string containing the pannumber(s) of all files that should be
        included in this analysis (input list is pulled from ad_config.VCP_PANELS using
        the core_panel_name). App takes pan numbers as string, and will separate on
        commas when passed multiple pan numbers
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for RPKM app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "RPKM",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["rpkm"]}RPKM_using_conifer',
            f'{ad_config.APP_INPUTS["rpkm"]["bed"]}'
            f'{panel_config.CAPTURE_PANEL_DICT[core_panel_name]["rpkm_bedfile"]}',
            f'{ad_config.APP_INPUTS["rpkm"]["proj"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["rpkm"]["pannos"]}'
            f'{",".join(panel_config.VCP_PANELS[core_panel_name])}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends_gatk"],
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey]
        )


    def create_ed_readcount_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command for exomedepth readcount app
        Exome depth is run in 2 stages, firstly readcounts are caalculated for each capture panel.
        Job ID is saved to $ed_jobid which allows the output of this stage to be used to filter
        CNVs with a panel-specific BEDfile
        CNV calling steps are a dependency of MultiQC
        This function controls the order these commands are built and run so the output of the
        readcount step can be used as an input to the CNV calling step
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for ED readcount app

        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "ED_readcount",
            self.rf_obj.runfolder_name,
        )

        return " ".join([
            f'{ad_config.DX_CMDS["ed_readcount"]}ED_readcount',
            f'{ad_config.APP_INPUTS["ed_readcount"]["ref_genome"]}'
            f'{ad_config.NEXUS_IDS["FILES"]["hs37d5_ref_no_index"]}',
            f'{ad_config.APP_INPUTS["ed_readcount"]["bed"]}'
            f'{panel_config.CAPTURE_PANEL_DICT[core_panel_name]["ed_readcount_bedfile"]}',
            f'{ad_config.APP_INPUTS["ed_readcount"]["normals_rdata"]}'
            f'{ad_config.NEXUS_IDS["FILES"][f"ed_{core_panel_name}_readcount_normals"]}',
            f'{ad_config.APP_INPUTS["ed_readcount"]["proj"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["ed_readcount"]["pannos"]}'
            f'{",".join(panel_config.ED_PANNOS[core_panel_name])}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends_gatk"],  # Use list of gatk related jobs to delay start
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        ])


    def create_ed_cnvcalling_cmd(self, panno: str):
        """
        Build dx run command for exomedepth cnv calling app
            :param panno (str):     Pannumber to filter CNV calls
            :return (str):          Dx run command for ED cnv calling app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "ED_cnvcalling",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f'{ad_config.DX_CMDS["ed_cnvcalling"]}ED_cnvcalling',
            f'{ad_config.APP_INPUTS["ed_cnvcalling"]["readcount"]}'
            f'$ed_jobid:{ad_config.APP_INPUTS["ed_cnvcalling"]["readcount_rdata"]}',
            f'{ad_config.APP_INPUTS["ed_cnvcalling"]["bed"]}'
            f'{panel_config.BEDFILE_FOLDER}{panel_config.PANEL_DICT[panno]["ed_cnvcalling_bedfile"]}_CNV.bed',
            f'{ad_config.APP_INPUTS["ed_cnvcalling"]["proj"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["ed_cnvcalling"]["pannos"]}{panno}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends_gatk"],  # Use list of gatk related jobs to delay start
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        ])


    def create_duty_csv_cmd(self) -> str:
        """
        Build dx run command to run create_duty_csv app for the run. This creates a CSV
        file for use in downloading files to the trust network with the process_duty_csv
        script. It also sends an email denoting the run is ready for processing. The
        input to the duty_csv app is the dnanexus project name, and the pan numbers for
        tso samples, stg samples, and the custom panel whole capture for each core panel
            :return (str):  Dx run command for duty_csv app
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["building_cmd"],
            "create_duty_csv",
            self.rf_obj.runfolder_name,
        )
        return " ".join([
            f"{ad_config.DX_CMDS['duty_csv']}duty_csv",
            f'{ad_config.APP_INPUTS["duty_csv"]["project_name"]}'
            f'{self.samples_obj.nexus_paths["proj_name"]}',
            f'{ad_config.APP_INPUTS["duty_csv"]["tso_pannumbers"]}'
            f'{",".join(panel_config.TSO_VIAPATH_PANNUMBERS)}',
            f'{ad_config.APP_INPUTS["duty_csv"]["stg_pannumbers"]}'
            f'{",".join(panel_config.STG_PANNUMBERS)}',
            f'{ad_config.APP_INPUTS["duty_csv"]["cp_capture_pannos"]}'
            f'{",".join(panel_config.CP_CAPTURE_PANNOS)}',
            f'{ad_config.UPLOAD_ARGS["proj"]}{self.nexus_project_id}',
            ad_config.UPLOAD_ARGS["depends"],
            ad_config.UPLOAD_ARGS["token"] % self.dnanexus_apikey
        ])

    def write_dx_run_cmds(self, cmds, script) -> None:
        """
        Write dx run commands to the dx run script for the runfolder
            :param cmds (list): List of commands to write
            :script (str):      Path of script to write commands to
            :return None:
        """
        self.rf_obj.rf_loggers.usw.info(
            self.rf_obj.rf_loggers.usw.log_msgs["writing_cmds"],
        )
        with open(script, "w", encoding="utf-8") as cmds_script:
            # remove any None values from the command_list
            cmds_script.writelines(
                [f"{line}\n" for line in filter(None, cmds)]
            )


class PipelineEmails():
    """
    Class for sending the start of pipeline emails. Calls the AdEmail class for email
    sending. The following emails are sent:
        SQL emails for all pipelines
            These are sent to binfx. This is because samples processed using each
            workflow are recorded in Moka using an insert query per sample
        Emails with details of the samples being processed
            These are sent to binfx for all runs, plus to additional recijpients as
            defined within the config.ad_config file

        Attributes
            rf_obj (obj):           RunfolderObject object (contains runfolder-specific
                                    attributes)
            samples_obj (obj):      CollectRunfolderSamples object (contains
                                    sample-specific attributes)
            workflows (list):       List of names of all workflows used to process
                                    samples within the run
            sample_count (int):     Number of samples in the run
            email_subj (str):       Email subject used by all emails sent within this
                                    class
            email (obj):            AdEmail object (contains methods for sending emails)
            queries (str):          Newline-separated string of SQL queries

        Methods
            collect_queries()
                Collect queries from the samples_dict (for all runs with per-sample
                queries). For those with run-level queries (wes), call
                return_wes_query()
            return_wes_query()
                Return WES SQL query. This is a single update query per-run
            send_sql_email()
                Construct and send pipeline started email using the AdEmail class
            send_samples_email()
                Construct and send the samples being processed email using AdEmail class
    """
    def __init__(self, rf_obj, samples_obj):
        """
        Constructor for the PipelineEmails class
        """
        self.rf_obj = rf_obj
        self.samples_obj = samples_obj
        self.workflows = [
            self.samples_obj.samples_dict[k]['panel_settings']['pipeline']
            for k in self.samples_obj.samples_dict.keys()
        ]
        self.sample_count = len(self.samples_obj.samples_dict)
        self.email_subj = (
            ad_config.MAIL_SETTINGS["pipeline_started_subj"] %
            self.rf_obj.runfolder_name
        )
        self.email = AdEmail(self.rf_obj.rf_loggers.usw)
        self.queries = self.collect_queries()
        self.send_sql_email()
        self.send_samples_email()

    def collect_queries(self) -> str:
        """
        Collect queries from the samples_dict (for all runs with per-sample queries)
        For those with run-level queries (wes), call return_wes_query()
            :return (str):  Newline-separated string of SQL queries
        """
        if self.samples_obj.pipeline == "wes":
            queries = self.return_wes_query()
        else:
            queries = [
                self.samples_obj.samples_dict[k]['SQL_query']
                for k in self.samples_obj.samples_dict.keys()
            ]
        return "\n".join(queries)

    def return_wes_query(self):
        """
        Return WES SQL query. This is a single update query per-run.
            :return query (str):    Single update query for the WES run
        """
        wes_dnanumbers = [
            self.samples_obj.samples_dict[k]['identifiers']['primary']
            for k in self.samples_obj.samples_dict.keys()
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

    def send_sql_email(self) -> None:
        """
        Construct and send pipeline started email using the AdEmail class. Email is sent
        to the binfx team. Contains SQL queries used to update the Moka database.
        Logging is carried out within the AdEmail class
            :return None:
        """
        email_html = self.email.generate_email_html(
            self.rf_obj.runfolder_name, ",".join(set(self.workflows)),
            self.queries, self.sample_count
        )
        self.email.send_email(
            recipients=[ad_config.MAIL_SETTINGS["binfx_recipient"]],
            email_subject=self.email_subj,
            email_message=email_html,
            email_priority=1,
        )

    def send_samples_email(self) -> None:
        """
        Construct and send the samples being processed email using the AdEmail class.
        Email is sent to the binfx team and other relevant parties dependent upon the
        pipeline. Contains details to inform the relevant parties that the pipeline has
        been started. Logging is carried out within the AdEmail class
            :return None:
        """
        email_html = self.email.generate_email_html(
            self.rf_obj.runfolder_name, ",".join(set(self.workflows)),
            False, self.sample_count
        )
        recipients = [ad_config.MAIL_SETTINGS['binfx_recipient']]
        if self.samples_obj.pipeline == 'wes':
            recipients.extend(ad_config.MAIL_SETTINGS['wes_samplename_emaillist'])
        elif self.samples_obj.pipeline in ['amp', 'tso500', 'archerdx']:
            recipients.append(ad_config.MAIL_SETTINGS['oncology_ops_email'])
        self.email.send_email(
            recipients=recipients,
            email_subject=self.email_subj,
            email_message=email_html,
            email_priority=1,
        )
