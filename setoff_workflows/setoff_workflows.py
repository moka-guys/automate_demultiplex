#!/usr/bin/python3
# coding=utf-8
"""setoff_workflows.py

Collect sequencing runs and initiate runfolder processing for those requiring
processing. See Readme and docstrings for further details. Contains the following classes:

- SequencingRuns
    Collects sequencing runs and initiates runfolder processing for those sequencing runs requiring processing
- ProcessRunfolder
    A new instance of this class is initiated for each runfolder being assessed. Calls methods to process and
    upload a runfolder including creation of DNAnexus project, upload of data using upload_runfolder,
    building and execution of dx run commands to set off sample workflows and apps, creation of decision
    support tool upload scripts, and sending of pipeline emails
- CollectRunfolderSamples
    Collect attributes for all samples within the runfolder
- SampleObject
    Collect sample-specific attributes for a sample
- BuildDxCommands
    Build run-wide commands for runfolder, and write sample-level commands from the
    samples_obj along with the run-wide commands to the dx run script
- PipelineEmails
    Class for sending the start of pipeline emails. Calls the AdEmail class for email
    sending. The following emails are sent:
    - Pipeline started email. Contains SQL queries used to update the Moka database
    - Samples being processed email
"""
import sys
import os
import re
import datetime
from itertools import *
from shutil import copyfile
from typing import Union, Tuple
from ad_logger.ad_logger import AdLogger, shutdown_logs
from config.ad_config import SWConfig
from ad_email.ad_email import AdEmail
from upload_runfolder.upload_runfolder import UploadRunfolder
from toolbox.toolbox import (
    return_scriptlog_config,
    test_upload_software,
    RunfolderObject,
    read_lines,
    get_num_processed_runfolders,
    get_credential,
    git_tag,
    write_lines,
    execute_subprocess_command,
)
from seglh_naming.sample import Sample as seglh_namingSample


class SequencingRuns(SWConfig):
    """
    Collects sequencing runs and initiates runfolder processing for those sequencing runs requiring processing

    Attributes
        ad_logger_obj (object):         AdLogger object, used to create a python logging object with custom attributes
                                        and a file handler, syslog handler, and stream handler    
        script_logger (object):         Script-level logger, created by the ad_logger_obj
        runs_to_process (list):         List of runfolder objects for runs that require processing
        processed_runfolders (list):    List of runfolders processed by the script
        num_processed_runfolders (int): Number of runfolders processed during this cycle

    Methods:
        setoff_processing()
            Call methods to collect runfolders for processing
        set_runfolders()
            Update self.runfolders list with NGS runfolders in the runfolders directory
        requires_processing(rf_obj)
            Calls other methods to determine whether the runfolder requires processing (demultiplexing
            has finished successfully and the runfolder has not already been uploaded)
        has_demultiplexed(rf_obj)
            Check if demultiplexing has already been performed and completed sucessfully
        already_uploaded(rf_obj)
            Checks for presence of DNAnexus upload flag file(denotes that the runfolder has
            already been processed)
        process_runfolder(rf_obj)
            If software tests pass, set up logging and pass rf_obj to the ProcessRunfolder class for
            processing, shutting down logs upon completion
        return_num_processed_runfolders()
            Set the total number of processed runfolders as a class attribute
    """

    def __init__(self):
        """
        Constructor for the SequencingRuns class
        """
        self.ad_logger_obj = AdLogger("sw", "sw", return_scriptlog_config()["sw"])
        self.script_logger = self.ad_logger_obj.get_logger()
        self.runs_to_process = self.set_runfolders()
        self.processed_runfolders = []

    def setoff_processing(self) -> None:
        """
        Call methods to collect runfolders for processing
            :return None:
        """
        if test_upload_software(self.script_logger):
            for rf_obj in self.runs_to_process:
                self.script_logger.info(
                    self.script_logger.log_msgs["start_runfolder_proc"],
                    rf_obj.runfolder_name,
                )
                self.process_runfolder(rf_obj)
            self.num_processed_runfolders()

    def set_runfolders(self) -> None:
        """
        Update self.runs_to_process list with NGS runfolders in the runfolders directory
        that match the runfolder pattern, and require processing by the script
            :return runs_to_process (list): List of runfolder objects for runs to process
        """
        runs_to_process = []
        for folder in os.listdir(SWConfig.RUNFOLDERS):
            if os.path.isdir(os.path.join(SWConfig.RUNFOLDERS, folder)) and re.compile(
                SWConfig.RUNFOLDER_PATTERN
            ).match(folder):
                self.script_logger.info(
                    self.script_logger.log_msgs["runfolder_identified"], folder
                )
                rf_obj = RunfolderObject(folder, SWConfig.TIMESTAMP)
                if self.requires_processing(rf_obj):
                    runs_to_process.append(rf_obj)
        return runs_to_process

    def requires_processing(self, rf_obj: object) -> Union[bool, None]:
        """
        Calls other methods to determine whether the runfolder requires processing (demultiplexing
        has finished successfully and the runfolder has not already been uploaded)
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific attributes)
            :return True | None:    Returns true if runfolder requires processing, else None
        """
        if self.has_demultiplexed(rf_obj) and not self.already_uploaded(rf_obj):
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_requires_proc"],
                rf_obj.runfolder_name,
            )
            return True
        else:
            self.script_logger.info(
                self.script_logger.log_msgs["runfolder_prev_proc"],
                rf_obj.runfolder_name,
            )

    def has_demultiplexed(self, rf_obj: object) -> Union[bool, None]:
        """
        Check if demultiplexing has already been performed and completed sucessfully. Checks the
        demultiplex log file exists, and if present checks the expected success string is in the
        last line of the log file.
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific attributes)
            :return True | None:    Return True if runfolder already demultiplexed, else None
        """
        if os.path.isfile(rf_obj.bcl2fastqlog_file):
            logfile_list = read_lines(rf_obj.bcl2fastqlog_file)
            completed_strs = [
                SWConfig.STRINGS["demultiplexlog_tso500_msg"],
                SWConfig.STRINGS["demultiplex_success"],
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

    def already_uploaded(self, rf_obj: object) -> Union[bool, None]:
        """
        Checks for presence of DNAnexus upload flag file (denotes that the runfolder has already been processed)
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific attributes)
            :return True | None:    Returns True if runfolder already uploaded, else None
        """
        if os.path.isfile(rf_obj.upload_flagfile):
            self.script_logger.info(self.script_logger.log_msgs["ua_file_present"])
            return True
        else:
            # If file doesn't exist return false to continue, write to log file
            self.script_logger.info(self.script_logger.log_msgs["ua_file_absent"])

    def process_runfolder(self, rf_obj: object) -> None:
        """
        If software tests pass, set up logging and pass rf_obj to the ProcessRunfolder class for processing,
        shutting down logs upon completion. Append to self.processed_runfolders
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific attributes)
            :return None:
        """
        rf_obj.add_runfolder_loggers()  # Add runfolder loggers attribute
        self.process_runfolder_obj = ProcessRunfolder(rf_obj)

        for logger in rf_obj.rf_loggers.loggers:
            shutdown_logs(logger)  # Shut down logging
        self.processed_runfolders.append(rf_obj.runfolder_name)
        self.script_logger.info(
            self.script_logger.log_msgs["runfolder_processed"],
            self.process_runfolder_obj.rf_obj.runfolder_name,
        )

    def num_processed_runfolders(self) -> None:
        """
        Set the total number of processed runfolders as a class attribute
            :return None:
        """
        num_processed_runfolders = get_num_processed_runfolders(
            self.script_logger, self.processed_runfolders
        )
        setattr(self, "num_processed_runfolders", num_processed_runfolders)


class ProcessRunfolder(SWConfig):
    """
    A new instance of this class is initiated for each runfolder being assessed. Calls methods to process and
    upload a runfolder including creation of DNAnexus project, upload of data using upload_runfolder,
    building and execution of dx run commands to set off sample workflows and apps, creation of decision
    support tool upload scripts, and sending of pipeline emails

    Attributes:
        rf_obj (obj):                       RunfolderObject() object (contains runfolder-specific attributes)
        dnanexus_auth (str):                DNAnexus auth token
        samples_obj (obj):                  CollectRunfolderSamples() object (contains sample-specific attributes)
        users_dict (dict):                  Dictionary of users and admins requiring access to the DNAnexus project
        nexus_identifiers (dict):           Dictionary containing project name and ID
        upload_runfolder (obj):             UploadRunfolder() object with methods that can be called to upload
                                            files to the DNAnexus project
        upload_cmds (dict):                 Dictionary of commands for uploading files to the DNAnexus project
        pre_pipeline_upload_dict (dict):    Dict of files to upload prior to pipeline setoff, and commands
        build_dx_commands(obj):             BuildDxCommands object for building run-wide commands for runfolder,
                                            and writing sample-level commands from the samples_obj along with the
                                            run-wide commands to the dx run script
        pipeline_emails (obj):              PipelineEmails object for sending the start of pipeline emails

    Methods:
        get_users_dict()
            Create a dictionary of users and admins that require access to the DNAnexus project
        write_project_creation_script()
            Write the script that creates the DNAnexus project and shares it with the
            required users with the required access level
        run_project_creation_script()
            Set off the project creation script using subprocess, return project ID
        get_upload_cmds()
            Build file upload commands
        split_tso_samplesheet()
            Split tso500 SampleSheet into parts with x samples per SampleSheet (no.
            defined in TSO_BATCH_SIZE) and write to runfolder
        read_tso_samplesheet()
            Read required lines from the TSO SampleSheet
        create_file_upload_dict()
            Create dictionary of files to upload prior to setting off the pipeline, and
            the upload commands required
        pre_pipeline_upload()
            Uploads the files in the samples_obj.pre_pipeline_upload_dict for the
            runfolder. Calls the tso runfolder upload function if the runfolder is tso
        upload_to_dnanexus(filetype, file_upload_dict)
            Passes the command and file list in file_upload_dict to upload_runfolder.upload_files()
            which writes log messages to the upload agent log within the runfolder
        upload_rest_of_runfolder()
            Backs up the rest of the runfolder, ignoring files dependent upon the type of run
        create_decision_support_command_file()
            If there is a decision support tool upload required, create the upload bash
            script, which  is run manually after QC has passed
        run_dx_run_commands()
            Execute the dx run bash script
        post_pipeline_upload()
            Uploads the rest of the runfolder if not a tso run, and uploads the
            runfolder logfiles (upload_agent file is not uploaded because it is being
            written to as the upload is taking place)
    """

    def __init__(self, rf_obj: RunfolderObject):
        """
        Constructor for the RunfolderProcessor class
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
        """
        self.rf_obj = rf_obj
        self.dnanexus_auth = get_credential(SWConfig.CREDENTIALS["dnanexus_authtoken"])
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["ad_version"],
            git_tag(),
        )
        self.samples_obj = CollectRunfolderSamples(self.rf_obj)

        if self.samples_obj.samplename_dict:  # If samples are present
            if not any(
                panno in SWConfig.DEVELOPMENT_PANEL
                for panno in self.samples_obj.unique_pannos
            ):
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["not_dev_run"],
                    self.rf_obj.samplesheet_path,
                )
                self.users_dict = self.get_users_dict()
                self.write_project_creation_script()
                self.nexus_identifiers = {
                    "proj_name": self.samples_obj.nexus_paths["proj_name"],
                    "proj_id": self.run_project_creation_script(),
                }
                self.upload_runfolder = UploadRunfolder(
                    self.rf_obj, self.nexus_identifiers
                )
                self.upload_cmds = self.get_upload_cmds()
                self.pre_pipeline_upload_dict = self.create_file_upload_dict()
                self.build_dx_commands = BuildDxCommands(
                    self.rf_obj, self.samples_obj, self.nexus_identifiers["proj_id"]
                )
                self.create_decision_support_command_file()
                self.pre_pipeline_upload()
                self.run_dx_run_commands()
                self.pipeline_emails = PipelineEmails(self.rf_obj, self.samples_obj)
                self.pipeline_emails.send_sql_email()
                self.pipeline_emails.send_samples_email()
                self.post_pipeline_upload()
            else:
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["dev_run"],
                    self.rf_obj.samplesheet_path,
                )

    def get_users_dict(self) -> dict:
        """
        Create a dictionary of users and admins that require access to the DNAnexus project. This also
        includes dry lab DNAnexus IDs if applicable for the samples in the runfolder. These are taken
        from the per-sample panel_stettings in the samples_dict. This is required because some samples
        are analysed at dry labs, with access to projects only given where there is a sample for that
        dry lab on the run
            :return (dict):     Dictionary of users and admins requiring access to the DNAnexus project
        """
        dry_lab_list = list(set(
            [
                v["panel_settings"]["dry_lab"]
                for k, v in self.samples_obj.samples_dict.items()
                if v["panel_settings"]["dry_lab"]
            ]
        ))
        if True in dry_lab_list:
            viewers = list(chain([SWConfig.BSPS_ID], SWConfig.DNANEXUS_USERS["viewers"]))
        else:
            viewers = SWConfig.DNANEXUS_USERS["viewers"]
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["view_users"],
            viewers,
        )
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["admin_users"],
            SWConfig.DNANEXUS_USERS["admins"]
        )
        return {
            "viewers": {
                "user_list": viewers,
                "permissions": "VIEW",
            },
            "admins": {
                "user_list": SWConfig.DNANEXUS_USERS["admins"],
                "permissions": "ADMINISTER",
            },
        }

    def write_project_creation_script(self) -> None:
        """
        Write the script that creates the DNAnexus project and shares it with the
        required users with the required access levels. The project is created using
        the project creation command which utilises the DNAnexus sdk. This command and
        the project sharing commands are written to a bash script
            :return None:
        """
        lines_to_write = [
            SWConfig.SDK_SOURCE,
            SWConfig.DX_CMDS["create_proj"]
            % (
                SWConfig.PROD_ORGANISATION,
                self.samples_obj.nexus_paths["proj_name"],
                self.dnanexus_auth,
            ),
            f'{SWConfig.DX_CMDS["write_projid"]} {self.rf_obj.runfolder_dx_run_script}',
        ]
        # Give view and admin permissions for project
        for permissions_level in self.users_dict.keys():
            if self.users_dict[permissions_level]["user_list"]:
                for user in self.users_dict[permissions_level]["user_list"]:
                    lines_to_write.append(
                        SWConfig.DX_CMDS["invite_user"]
                        % (
                            user,
                            self.users_dict[permissions_level]["permissions"],
                            self.dnanexus_auth,
                        )
                    )
                    lines_to_write.append("echo $PROJECT_ID")
            else:
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["no_users"],
                    permissions_level,
                )
        write_lines(self.rf_obj.proj_creation_script, "w", lines_to_write)

    def run_project_creation_script(self) -> str:
        """
        Set off the project creation script using subprocess. The output of this command is checked to
        ensure it meets the expected success pattern. If unsuccessful, exit script
            :return projectid (str):    Project ID of the created project
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["creating_proj"],
            self.rf_obj.proj_creation_script,
        )
        project_creation_cmd = f"bash {self.rf_obj.proj_creation_script}"

        project_id, err, returncode = execute_subprocess_command(
            project_creation_cmd, self.rf_obj.rf_loggers.sw, "exit_on_fail"
        )
        if returncode == 0:
            return project_id
        else:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["proj_creation_fail"],
                self.samples_obj.nexus_paths["proj_name"],
                err,
            )
            sys.exit(1)

    def get_upload_cmds(self) -> dict:
        """
        Build file upload commands
            :return upload_cmds (dict): Dictionary of commands for uploading
                                        files to the DNAnexus project
        """
        upload_cmds = {
            "cd": SWConfig.DX_CMDS["file_upload_cmd"]
            % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                "/QC",
                " ".join(f"'{cd_file}'" for cd_file in self.rf_obj.cluster_density_files),                
            ),
            "bcl2fastq_qc": SWConfig.DX_CMDS["file_upload_cmd"]
            % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                f"{os.path.join(self.samples_obj.nexus_paths['fastqs_dir'], 'Stats')}",
                self.rf_obj.bcl2fastqstats_file,
            ),
            "logfiles": SWConfig.DX_CMDS["file_upload_cmd"]
            % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths["logfiles_dir"],
                " ".join(f"'{logfile}'" for logfile in self.rf_obj.logfiles_to_upload),
            ),
        }
        if self.samples_obj.pipeline == "tso500":
            self.rf_obj.tso_ss_list = self.split_tso_samplesheet()
            samplesheet_paths = [
                os.path.join(self.rf_obj.runfolderpath, ss)
                for ss in self.rf_obj.tso_ss_list
            ]
            upload_cmds["runfolder_samplesheet"] = SWConfig.DX_CMDS[
                "file_upload_cmd"
            ] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                f'/{self.samples_obj.nexus_paths["runfolder_name"]}',
                " ".join(f"'{samplesheet}'" for samplesheet in samplesheet_paths),

            )
        else:
            upload_cmds["fastqs"] = SWConfig.DX_CMDS["file_upload_cmd"] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths["fastqs_dir"],
                " ".join([self.samples_obj.fastqs_str, self.samples_obj.undetermined_fastqs_str]),
            )
            upload_cmds["runfolder_samplesheet"] = SWConfig.DX_CMDS[
                "file_upload_cmd"
            ] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                self.samples_obj.nexus_paths["fastqs_dir"],
                self.rf_obj.runfolder_samplesheet_path,
            )
        return upload_cmds

    def split_tso_samplesheet(self) -> list:
        """
        Split tso500 SampleSheet into parts with x samples per SampleSheet (no.
        defined in TSO_BATCH_SIZE), and write to runfolder
            :return (list):     SampleSheet names
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["splitting_tso_samplesheet"],
            SWConfig.TSO_BATCH_SIZE,
            self.rf_obj.samplesheet_path,
        )
        samplesheet_list = []
        samples, samplesheet_header = self.read_tso_samplesheet()
        # Split samples into batches (size specified in config)
        batches = [
            samples[i: i + SWConfig.TSO_BATCH_SIZE]
            for i in range(0, len(samples), SWConfig.TSO_BATCH_SIZE)
        ]
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["tso_batches_count"],
            len(batches),
        )
        # Create new SampleSheets named "PartXofY", add SampleSheet to list
        # Capture path for SampleSheet in runfolder
        for samplesheet_count, batch in enumerate(batches, start=1):
            # Capture SampleSheet file path to write SampleSheet paths to the runfolder
            samplesheet_filepath = (
                f'{self.rf_obj.runfolder_samplesheet_path.split(".csv")[0]}'
                f"Part{samplesheet_count}of{len(batches)}.csv"
            )
            # Capture SampleSheet name to write to list- use runfolder name
            samplesheet_name = (
                f"{self.rf_obj.runfolder_name}_SampleSheetPart"
                f"{samplesheet_count}of{len(batches)}.csv"
            )
            samplesheet_list.append(samplesheet_name)
            write_lines(samplesheet_filepath, "w", samplesheet_header)
            write_lines(samplesheet_filepath, "a", batch)
        samplesheet_list.append(self.rf_obj.samplesheet_name)
        return samplesheet_list

    def read_tso_samplesheet(self) -> Union[list, list]:
        """
        Read required lines from the TSO SampleSheet
            :return samples (list):             Samples read from SampleSheet
            :return samplesheet_header (list):  SampleSheet header lines
        """
        samples, samplesheet_header = [], []
        no_sample_lines = 0
        expected_data_headers = ["Sample_ID", "Sample_Name", "index"]
        header_identified = False
        # Read all lines from the sample sheet
        with open(self.rf_obj.runfolder_samplesheet_path, "r") as samplesheet:
            for line in samplesheet.readlines():
                line = line.strip('\n')
                if any(header in line for header in expected_data_headers):
                    samplesheet_header.append(line)  # Extract header and add to list
                    header_identified = True
                elif (
                    not header_identified
                ):  # Extract lines above the header and add to list
                    samplesheet_header.append(line)
                # Skip empty lines (check first element of the line, after splitting on comma)
                elif header_identified and len(line.split(",")[0]) > 2:
                    samples.append(line)
                    no_sample_lines += 1
                elif len(line.split(",")[0]) < 2:  # Skip empty lines
                    pass
        return samples, samplesheet_header

    def create_file_upload_dict(self) -> dict:
        """
        Create dictionary of files to upload prior to setting off the pipeline,
        and the upload commands required
            :return pre_pipeline_upload_dict (dict):    Dict of files to upload prior to
                                                        pipeline setoff, and commands
        """
        pre_pipeline_upload_dict = {
            "cluster density": {
                "cmd": self.upload_cmds["cd"],
                "files_list": self.rf_obj.cluster_density_files,
            },
        }
        if self.samples_obj.pipeline == "tso500":  # Add SampleSheet entry
            pre_pipeline_upload_dict["runfolder_samplesheet"] = {
                "cmd": self.upload_cmds["runfolder_samplesheet"],
                "files_list": [
                    os.path.join(self.rf_obj.runfolderpath, ss)
                    for ss in self.rf_obj.tso_ss_list
                ],
            }
        else:
            pre_pipeline_upload_dict["fastqs"] = {
                "cmd": self.upload_cmds["fastqs"],
                "files_list": [*self.samples_obj.fastqs_list, *self.samples_obj.undetermined_fastqs_list],
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
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["tso_backup"],
            )
            self.upload_rest_of_runfolder()

    def upload_to_dnanexus(self, filetype: str, file_upload_dict: dict) -> None:
        """
        Passes the command and file list in file_upload_dict to upload_runfolder.upload_files()
        which writes log messages to the upload agent log within the runfolder
            :param filetype (str):          Name of the file upload type
            :param file_upload_dict (dict): Dictionary of files for upload
            :return None:
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["uploading_files"], filetype
        )
        result = self.upload_runfolder.upload_files(
            file_upload_dict[filetype]["cmd"],
            file_upload_dict[filetype]["files_list"],
        )
        if result == "success":
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["upload_success"], filetype
            )
        if result == "fail":
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["upload_fail"],
                filetype,
                self.rf_obj.upload_runfolder_logfile,
            )
        elif result is list:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["nonexistent_files"], result
            )

    def upload_rest_of_runfolder(self) -> None:
        """
        Backs up the rest of the runfolder. First copies the SampleSheet into the
        project, then specifies which files to ignore (excludes BCL files for all runs
        except tso500 runs for which they are needed for demultiplexing on DNAnexus).
        Calls upload_runfolder.upload_rest_of_runfolder(ignore), passing a run-dependent
        ignore string, and the this handles the runfolder upload. upload_runfolder
        writes log messages to the upload agent log within the runfolder. If unsuccessful,
        exit script
            :return None:
        """
        if os.path.exists(
            self.rf_obj.samplesheet_path
        ):  # Try to copy SampleSheet into project
            copyfile(
                self.rf_obj.samplesheet_path,
                self.rf_obj.runfolder_samplesheet_path,
            )
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["ss_copy_success"],
                self.rf_obj.runfolder_samplesheet_path,
            )
        else:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["ss_copy_fail"],
            )
        # Build upload_runfolder.py commands, ignoring some files
        if self.samples_obj.pipeline == "tso500":
            ignore = ""
        else:
            ignore = "/L00"

        try:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["uploading_rf"],
                ignore,
                self.rf_obj.upload_runfolder_logfile,
            )
            self.upload_runfolder.upload_rest_of_runfolder(ignore)
        except Exception as exception:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["upload_rf_error"],
                exception,
                self.rf_obj.sw_runfolder_logfile,
                self.rf_obj.upload_runfolder_logfile,
            )
            sys.exit(1)

    def create_decision_support_command_file(self) -> None:
        """
        If there is a decision support tool upload required, create the upload bash file,
        which is run manually after QC has passed. Writes the source command, activating
        the environment (the sdk). Specific upload commands are echoed into this file
        at a later point when the pipeline run script is executed
            :return None:
        """
        if self.samples_obj.pipeline in ("pipe", "wes"):
            lines_to_write = [SWConfig.SDK_SOURCE]
            write_lines(self.rf_obj.decision_support_upload_cmds, "w", lines_to_write)

    def run_dx_run_commands(self) -> None:
        """
        Execute the dx run bash script
            :return None:
        """
        dx_run_cmd = f"bash {self.rf_obj.runfolder_dx_run_script}"

        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["running_cmds"],
        )
        out, err, returncode = execute_subprocess_command(
            dx_run_cmd, self.rf_obj.rf_loggers.sw, "exit_on_fail"
        )
        if returncode != 0:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["dx_run_err"],
                self.rf_obj.runfolder_name,
                dx_run_cmd,
                out,
                err,
            )
        else:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["dx_run_success"],
                self.rf_obj.runfolder_name,
            )

    def post_pipeline_upload(self) -> None:
        """
        Uploads the rest of the runfolder if not a tso run, and
        uploads the runfolder logfiles
            :return None:
        """
        if self.samples_obj.pipeline != "tso500":
            self.upload_rest_of_runfolder()

        file_upload_dict = {
            "logfiles": {
                "cmd": self.upload_cmds["logfiles"],
                "files_list": self.rf_obj.logfiles_to_upload,
            }
        }
        for filetype in file_upload_dict.keys():
            self.upload_to_dnanexus(filetype, file_upload_dict)


class CollectRunfolderSamples(SWConfig):
    """
    Collect attributes for all samples within the runfolder

    Attributes
        param rf_obj (obj):             RunfolderObject object (contains
                                        runfolder-specific attributes)
        samplename_dict (dict):         Dict of sample names identified from the
                                        SampleSheet, and their pan numbers
        pipeline (str):                 Pipeline name
        runtype_str (str):              Runtype name string
        nexus_runfolder_suffix (str):   String of '_' delimited unique library numbers,
                                        and WES batch numbers if run is a WES run
        nexus_paths (dict):             Dictionary of paths within the DNAnexus project
                                        that are required for building dx commands
        unique_pannos (set):            Set of unique panel numbers within the run
        samples_dict (dict):            Dictionary of SampleObject per sample,
                                        containing sample-specific attributes
        fasqs_list (list):              List of all sample fastqs in the run
        fastqs_str (str):               Space separated string of sample fastqs with
                                        each fastq encased in quotation marks
        sample_obj (object):            SampleObject containing sample-specific attributes

    Methods
        get_samplename_dict()
            Read SampleSheet to create a dict of samples and their pan numbers for the run
        get_pipeline()
            Use self.samplename_dict and the config.PANEL_DICT to get a list of pipeline
            names for samples in the run. Returns the most frequent pipeline name in the set
        get_runtype()
            Use self.samplename_dict and the config.PANEL_DICT to get a list of runtype
            names for samples in the run. Returns the most frequent runtype name in the set
        get_nexus_runfolder_suffix()
            Get runfolder suffix for the DNAnexus project name. This consists of the library
            number, followed by the WES batch if the run is a WES run, followed by the runtype
        capture_library_numbers()
            Parse the names in self.samplename_dict to identify the library prep numbers
        capture_wes_batch_numbers()
            Parse the names in self.samplename_dict to identify the WES batch numbers
        get_nexus_paths()
            Build nexus paths, using NGS run numbers (and batch numbers in the case of WES)
        get_samples_dict()
            Create a SampleObject per sample, containing sample-specific properties, and
            add each SampleObject to a larger samples_dict
        validate_fastqs()
            Validate the fastqs in the BaseCalls directory by checking that all sample fastqs
            match a sample name from the self.samplename_dict
        fastq_not_undetermined(fastq_dir_file)
            Determine whether the fastq is an undetermined fastq
        get_fastqs_list()
            Return a list of sample fastqs for the run
        get_fastqs_str(fastqs_list)
            Return a space separated string of fastqs with each fastq encased in quotation marks
        get_undetermined_fastqs_list()
            Return a list of undetermined fastqs for the run
    """

    def __init__(self, rf_obj: RunfolderObject):
        """
        Constructor for the CollectRunfolderSamples class
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
        """
        self.rf_obj = rf_obj
        self.samplename_dict = self.get_samplename_dict()
        if self.samplename_dict:
            self.pipeline = self.get_pipeline()
            self.runtype_str = self.get_runtype()
            self.nexus_runfolder_suffix = self.get_nexus_runfolder_suffix()
            self.nexus_paths = self.get_nexus_paths()
            self.unique_pannos = set(self.samplename_dict.values())
            self.samples_dict = self.get_samples_dict()
            if self.pipeline != "tso500":
                # tso500 run is not demultiplexed locally so there are no fastqs
                # All other runfolders have fastqs in the BaseCalls directory
                # Check fastqs in fastq dir were correctly identified from the
                # SampleSheet and add any missing samples to the samples dict
                self.validate_fastqs()
                self.fastqs_list = self.get_fastqs_list()
                self.fastqs_str = self.get_fastqs_str(self.fastqs_list)
                self.undetermined_fastqs_list = self.get_undetermined_fastqs_list()
                self.undetermined_fastqs_str = self.get_fastqs_str(self.undetermined_fastqs_list)

    def get_samplename_dict(self) -> list:
        """
        Read SampleSheet to create a dict of samples and their pan numbers for the
        run. Reads file into list and loops through in reverse allowing us to access
        sample names and stop at column headers, skipping the file header. Creates
        upload agent file if samples have been identified, to prevent processing by
        other script runs
            :return samplename_dict (dict): Dict of sample names identified from the
                                            SampleSheet, and their pan numbers
        """
        samplename_dict = {}
        if os.path.exists(self.rf_obj.samplesheet_path):
            with open(self.rf_obj.samplesheet_path, "r") as samplesheet_stream:
                for line in reversed(samplesheet_stream.readlines()):
                    if line.startswith("Sample_ID") or "[Data]" in line:
                        break
                    # Skip empty lines (check first element of the line, after splitting on comma)
                    elif len(line.split(",")[0]) < 2:
                        pass
                    else:  # If it's a line detailing a sample, get sample name and pan num
                        panel_number = ""
                        sample_name = line.split(",")[0]
                        for pannum in SWConfig.PANELS:
                            if pannum in line:
                                panel_number = pannum
                            samplename_dict[sample_name] = panel_number
            if samplename_dict:  # If samples identified
                # Create upload flag file (prevents processing by other script runs)
                write_lines(
                    self.rf_obj.upload_flagfile,
                    "w",
                    f"{SWConfig.UPLOAD_STARTED_MSG}: {datetime.datetime.now()}",
                )
                return samplename_dict
            else:
                return False
        else:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["ss_missing"],
            )
            return False

    def get_pipeline(self) -> Union[str, None]:
        """
        Use samplename_dict and the config.PANEL_DICT to get a list of pipeline
        names for samples in the run. Generates error mesage if there is more than one
        pipeline name in the list. Returns the most frequent pipeline name in the set
            :return pipeline_name (str):  Pipeline name
        """
        pipelines_list = []
        for sample, panno in self.samplename_dict.items():
            pipelines_list.append(SWConfig.PANEL_DICT[panno]["pipeline"])
        pipelines_list = list(set(pipelines_list))
        if len(pipelines_list) > 1:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["multiple_pipeline_names"],
                pipelines_list,
            )
        else:
            pipeline_name = max(list(set(pipelines_list)), key=pipelines_list.count)
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["pipeline_name"],
                pipeline_name,
            )
            return pipeline_name  # Get pipeline from pipelines_list

    def get_runtype(self) -> str:
        """
        Use samplename_dict and the config.PANEL_DICT to get the runtype for samples
        in the run
            :return runtype_str (str):  Runtype name string
        """
        runtype_list = []
        for sample, panno in self.samplename_dict.items():
            runtype_list.append(SWConfig.PANEL_DICT[panno]["runtype"])
        runtype_str = "_".join(list(set(runtype_list)))
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["runtype_str"],
            runtype_str,
        )
        return runtype_str  # Get runtype from pipelines_list

    def get_nexus_runfolder_suffix(self) -> str:
        """
        Get the runfolder suffix for the DNAnexus project name. This consists of the
        library number, followed by the WES batch if the run is a WES run, followed by the runtype
            :return suffix (str):   String of '_' delimited unique library numbers, and WES
                                    batch numbers if run is a WES run, followed by the runtype
        """
        library_numbers = self.capture_library_numbers()
        if self.pipeline == "wes":
            library_numbers.extend(self.capture_wes_batch_numbers())
        suffix = f"{'_'.join(library_numbers)}_{self.runtype_str}"
        return suffix

    def capture_library_numbers(self) -> list:
        """
        Parse the names in self.samplename_dict to identify the library prep numbers.
        These are the first elements in the sample names (before the first underscore).
        These numbers are used as the suffix for the DNAnexus project name (along with
        the WES batch number in the case of WES runs). If no library prep numbers are
        found, exit the script
            :return (list) | None:   List of unique library numbers
        """
        library_numbers = []
        for samplename in self.samplename_dict.keys():
            if "_" in str(samplename):  # Check there are underscores present
                # Split on underscores to capture library number e.g. ONC100 or NGS100
                library_numbers.append(samplename.split("_")[0])
        if library_numbers:  # Should always be library numbers found
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["library_nos_identified"],
                ", ".join(list(set(library_numbers))),
            )
            return list(set(library_numbers))
        else:  # Prompt a slack alert
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["library_no_err"],
                self.rf_obj.runfolder_name,
            )
            sys.exit(1)

    def capture_wes_batch_numbers(self) -> list:
        """
        Parse the names in self.samplename_dict to identify the WES batch numbers. This
        along with the library prep number is used as the DNAnexus project name suffix.
        If unsuccessful, exit the script
            :return wes_batch_numbers_list (list):  List of unique WES batch numbers
        """
        wes_batch_numbers_list = []
        for samplename in self.samplename_dict.keys():
            if "WES" in str(samplename):
                # Capture WES batch (WES followed by digits)
                # Optional underscore ensures this will capture WES5 or WES_5
                wesbatch = re.search(r"WES_?\d+", samplename).group()
                wes_batch_numbers_list.append(wesbatch.replace("_", ""))
        if wes_batch_numbers_list:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["wes_batch_nos_identified"],
                ", ".join(wes_batch_numbers_list),
            )
            return list(set(wes_batch_numbers_list))
        else:  # Prompt a slack alert
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["wes_batch_nos_missing"],
                self.rf_obj.runfolder_name,
            )
            sys.exit(1)

    def get_nexus_paths(self) -> dict:
        """
        Build nexus paths, using NGS run numbers (and batch numbers in the case of WES).
        Builds the DNAnexus project name using the config-defined project prefix (denoting
        status of the DNAnexus project), followed by the runfolder name and the and
        self.nexus_runfolder_suffix as the suffix (library prep / WES batch numbers). Uses
        the DNAnexus project name to build additional paths required for later dx run commands
            :return nexus_paths (dict): Dictionary of paths within the DNAnexus project
                                        that are required for building dx commands
        """
        nexus_paths = {}
        if self.pipeline == "tso500":
            fastq_type = "tso_fastqs"
        else:
            fastq_type = "fastqs"

        nexus_paths[
            "runfolder_name"
        ] = f"{self.rf_obj.runfolder_name}_{self.nexus_runfolder_suffix}"
        nexus_paths[
            "proj_name"
        ] = f"{SWConfig.DNANEXUS_PROJECT_PREFIX}{nexus_paths['runfolder_name']}"
        nexus_paths["proj_root"] = f"{nexus_paths['proj_name']}:/"
        nexus_paths[
            "runfolder_subdir"
        ] = f"{nexus_paths['proj_root']}{self.rf_obj.runfolder_name}"
        nexus_paths[
            "fastqs_dir"
        ] = os.path.join(f"/{self.rf_obj.runfolder_name}", SWConfig.FASTQ_DIRS[fastq_type])
        nexus_paths[
            "logfiles_dir"
        ] = os.path.join(f"/{nexus_paths['runfolder_name']}", "automated_scripts_logfiles")
        nexus_paths[
            "samplesheet"
        ] = os.path.join(nexus_paths['proj_root'], self.rf_obj.samplesheet_name)
        return nexus_paths

    def get_samples_dict(self) -> dict:
        """
        Create a SampleObject for each sample which returns a sample dictionary
        containing the sample_name, pannum, panel_settings and fastqs paths for that
        sample. Add each SampleObject to a larger samples_dict
            :return samples_dict (dict):    Dictionary of SampleObject per sample,
                                            containing sample-specific attributes
        """
        samples_dict = {}
        for sample_name in self.samplename_dict.keys():
            self.sample_obj = SampleObject(
                sample_name,
                self.pipeline,
                self.rf_obj,
                self.nexus_paths,
            )
            if self.sample_obj.fastqs_dict:
                samples_dict[sample_name] = self.sample_obj.return_sample_dict()
            else:
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["sample_excluded"],
                    sample_name,
                )
        return samples_dict

    def validate_fastqs(self) -> None:
        """
        Validate the fastqs in the BaseCalls directory by checking that all sample fastqs
        match a sample name from the self.samplename_dict. If they do not, log an error
        and add to a missing_samples list. Add all samples in the missing samples list to
        the samples_dict so that they are processed
            :return None:
        """
        missing_samples = []
        for fastq_dir_file in os.listdir(self.rf_obj.fastq_dir_path):
            if os.path.isfile(fastq_dir_file):
                if fastq_dir_file.endswith("fastq.gz"):
                    self.rf_obj.rf_loggers.sw.info(
                        self.rf_obj.rf_loggers.sw.log_msgs["checking_fastq"],
                        fastq_dir_file,
                    )
                    if self.fastq_not_undetermined(fastq_dir_file):  # Exclude undetermined
                        try:
                            seglh_namingSample.from_string(fastq_dir_file)
                            sample_name = [
                                sample_name
                                for sample_name in self.samplename_dict.keys()
                                if sample_name in fastq_dir_file
                            ]
                            if sample_name:
                                self.rf_obj.rf_loggers.sw.info(
                                    self.rf_obj.rf_loggers.sw.log_msgs["sample_match"],
                                    fastq_dir_file,
                                    sample_name,
                                )
                            else:
                                self.rf_obj.rf_loggers.sw.error(
                                    self.rf_obj.rf_loggers.sw.log_msgs["sample_mismatch"],
                                    fastq_dir_file,
                                )
                                sample_name = re.sub("R[0-9]_001.fastq.gz", "", fastq_dir_file)
                                missing_samples.append(fastq_dir_file)
                        except ValueError as exception:
                            self.rf_obj.rf_loggers.sw.error(
                                self.rf_obj.rf_loggers.sw.log_msgs["fastq_wrong_naming"],
                                fastq_dir_file,
                                exception,                            
                            )
                else:
                    self.rf_obj.rf_loggers.sw.info(
                        self.rf_obj.rf_loggers.sw.log_msgs["not_fastq"], fastq_dir_file
                    )
        for sample_name in missing_samples:  # Add the sample to the sample_obj
            # Strip end off sample name
            sample_name = re.sub(r"_S[0-9]+_R[1-2]{1}_001.fastq.gz", '', sample_name)
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["add_missing_sample"], sample_name
            )
            self.sample_obj = SampleObject(
                sample_name,
                self.pipeline,
                self.rf_obj,
                self.nexus_paths,
            )
            self.samples_dict[sample_name] = self.sample_obj.return_sample_dict()

    def fastq_not_undetermined(self, fastq_dir_file: str) -> Union[bool, None]:
        """
        Determine whether the fastq is an undetermined fastq
            :return True | None:    Return True if undetermined, else return None
        """
        if not fastq_dir_file.startswith("Undetermined"):
            return True
        else:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["undetermined_identified"],
                fastq_dir_file,
            )

    def get_fastqs_list(self) -> list:
        """
        Return a list of sample fastqs for the run
            :return fastqs_list (list): List of all sample fastqs in the run
        """
        fastqs_list = []
        for sample_name in self.samples_dict.keys():
            if self.samples_dict[sample_name]["fastqs"]:
                fastqs_list.extend(
                    [
                        self.samples_dict[sample_name]["fastqs"][read]["path"]
                        for read, path in self.samples_dict[sample_name]["fastqs"].items()
                    ]
                )
        return fastqs_list

    def get_fastqs_str(self, fastqs_list: list) -> str:
        """
        Return a space separated string of fastqs with each fastq encased in quotation marks
            :return fastqs_str (str):   Space separated string of fastqs with
                                        each fastq encased in quotation marks
        """
        quotation_marked_list = []
        for fastq in fastqs_list:
            quotation_marked = f"'{fastq}'"
            quotation_marked_list.append(quotation_marked)
        return " ".join(quotation_marked_list)

    def get_undetermined_fastqs_list(self) -> list:
        """
        Return a list and string of undetermined fastqs for the run
            :return undetermined_fastqs_list (list): List of all undetermined fastqs in the run
        """
        undetermined_fastqs_list = []
        r1 = os.path.join(self.rf_obj.fastq_dir_path, "Undetermined_S0_R1_001.fastq.gz")
        r2 = os.path.join(self.rf_obj.fastq_dir_path, "Undetermined_S0_R2_001.fastq.gz")
        for fastq in [r1, r2]:
            if os.path.exists(fastq):
                undetermined_fastqs_list.append(fastq)
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["undetermined_exists"],
                    fastq,
                )
            else:
                self.rf_obj.rf_loggers.sw.error(
                    self.rf_obj.rf_loggers.sw.log_msgs["undetermined_missing"],
                    fastq,
                )
        return undetermined_fastqs_list


# TODO eventually adapt this class to use the SamplesheetValidator package
class SampleObject(SWConfig):
    """
    Collect sample-specific attributes for a sample

    Attributes
        rf_obj (obj):                       RunfolderObject object (contains runfolder-specific attributes)
        sample_name (str):                  Sample name
        pipeline (str):                     Pipeline name
        nexus_paths (dict):                 Dictionary of paths within the DNAnexus project that
                                            are required for building dx commands
        neg_control (bool):                 True if sample is a negative control, else False
        pos_control (bool):                 True if sample is a reference sample, else False
        workflow_name (str):                Workflow name
        pannum (str):                       Panel number that matches a config-defined panel
                                            number, or None if pannum not valid
        panel_settings (dict):              Config defined panel settings specific to the sample panel number
        primary_identifier (str):           Primary sample identifier
        secondary_identifier (str):         Secondary sample identifier
        fastqs_dict (dict):                 Dictionary containing R1 and R2 fastqs and their local and cloud paths
        query (str):                        Return sample SQL query (sample-level query)
        sample_pipeline_cmd (str):          Dx run command for the sample workflow
        decision_support_upload_cmd (str):  Dx run command for the decision support tool upload

    Methods
        check_negative_control()
            Determine whether sample is a negative control
        check_pos_control()
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
            null if the sample is a negative or positive control (these only have one identifier)
        get_fastqs_dict()
            Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        get_fastq_paths()
            Get fastqs in fastq directory that correspond to each sample name in the
            sample dictionary. Build the fastq name, local path, and DNAnexus path
            for each fastq file
        get_sample_sql_query()
            Call functions to construct SQL query for the sample (sample-level query)
        return_rd_query()
            Create a query per sample using the DNA number
        return_oncology_query()
            Create a query per sample using IDs from the samplename (3rd and 4th) elements
        build_sample_dx_run_cmd()
            Build sample-level dx run commands for the workflow and Congenica upload
        create_wes_cmd()
            Construct dx run command for WES workflow
        return_decision_support_cmd()
            Construct decision support tool command for decision support tool upload where required by
            calling build_congenica_sftp_cmd, build_congenica_cmd or build_qiagen_upload_cmd
        build_congenica_sftp_cmd()
            Build the command to write the Congenica upload dx run command for the SFTP
            app to the decision support tool upload bash script
        build_congenica_cmd()
            Build the command to write the Congenica upload dx run command to the decision
            support tool upload bash script
        build_qiagen_upload_cmd()
            Build the command to write the qiagen upload command to the decisions support
            tool upload bash script
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

    def __init__(
        self,
        sample_name: str,
        pipeline: str,
        rf_obj: RunfolderObject,
        nexus_paths: dict,
    ):
        """
        Constructor for the SampleObject class
            :param sample_name (str):       Sample name
            :param pipeline (str):          Pipeline name
            :param rf_obj (obj):            RunfolderObject object (contains runfolder-specific attributes)
            :param nexus_paths (dict):      Dictionary of paths within the DNAnexus project that are
                                            required for building dx commands
        """
        self.rf_obj = rf_obj
        self.sample_name = sample_name
        self.pipeline = pipeline
        self.nexus_paths = nexus_paths
        self.neg_control = self.check_negative_control()
        self.pos_control = self.check_pos_control()
        self.workflow_name = self.get_workflow_name()
        self.pannum = self.find_pannum()
        self.panel_settings = SWConfig.PANEL_DICT[self.pannum]
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["sample_identified"],
            self.panel_settings["panel_name"],
            self.sample_name,
        )
        self.primary_identifier, self.secondary_identifier = self.get_identifiers()
        self.fastqs_dict = self.get_fastqs_dict()
        self.query = self.get_sample_sql_query()
        (
            self.sample_pipeline_cmd,
            self.decision_support_upload_cmd,
        ) = self.build_sample_dx_run_cmd()

    def check_negative_control(self) -> bool:
        """
        Determine whether sample is a negative control
            :return (bool): True if sample is a negative control, else False
        """
        if any(identifier in self.sample_name for identifier in SWConfig.NTCON_IDS):
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["neg_control"],
                self.sample_name,
            )
            return True
        else:
            return False

    def check_pos_control(self) -> bool:
        """
        Check if sample is a reference sample by checking if reference
        ids are present in fastq name
            :return (bool): True if reference sample, else False
        """
        if any(
            f"_{ref_sample_id}_" in self.sample_name
            for ref_sample_id in SWConfig.PSCON_IDS
        ):
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["pos_control"],
                self.sample_name,
            )
            return True
        else:
            return False

    def get_workflow_name(self) -> str:
        """
        Get workflow name from the app ID by parsing the workflow metadata
        using dx describe and jq
            :return workflow_name (str): Workflow name
        """
        if self.pipeline == "tso500":
            (workflow_name, _, _) = execute_subprocess_command(
                f"dx describe {SWConfig.NEXUS_IDS['APPS'][self.pipeline]} "
                "--json | jq -r '(.name)'",
                self.rf_obj.rf_loggers.sw,
                "exit_on_fail",
            )
        else:
            (workflow_name, _, _) = execute_subprocess_command(
                "dx describe "
                f"{SWConfig.NEXUS_IDS['WORKFLOWS'][self.pipeline]} "
                "--json | jq -r '\"\(.folder)/\(.name)\"'",
                self.rf_obj.rf_loggers.sw,
                "exit_on_fail",
            )
        return workflow_name

    def find_pannum(self) -> Union[str, None]:
        """
        Extract panel number from sample name using regular expression
            :return pannum (str | None):    Panel number that matches a config-defined
                                            panel number, or None if pannum not valid
        """
        pannum = str(re.search(r"Pan\d+", self.sample_name).group())
        if self.validate_pannum(pannum):
            return pannum

    def validate_pannum(self, pannum: int) -> Union[bool, None]:
        """
        Check whether pan number is valid
            :return (True | None):  True if pan number is valid, else None
        """
        if str(pannum) in SWConfig.PANELS:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["recognised_panno"],
                self.sample_name,
                pannum,
            )
            return True
        else:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["unrecognised_panno"],
                self.sample_name,
            )
            sys.exit(1)

    def get_identifiers(self) -> Tuple[str, str]:
        """
        For WES and PIPE samples, extract DNA number from sample name. For oncology
        samples, collect 3rd and 4th identifiers, setting secondary_identifier to null
        if the sample is a positive or negative control (these only have one identifier)
            :return primary_identifier (str):    Primary sample identifier
            :return secondary_identifier (str):  Secondary sample identifier
        """
        if self.pipeline in ("wes", "pipe", "snp"):
            # Extract the dna number from sample name
            primary_identifier = self.sample_name.split("_")[2]
            secondary_identifier = False  # Secondary identifiers are not input to Moka
        elif self.pipeline in ("tso500", "archerdx"):
            # Collect 3rd and 4th elements (identifiers)
            primary_identifier, secondary_identifier = self.sample_name.split("_")[2:4]
            # Negative and positive controls only have one ID so set id2 to null
            if any([self.neg_control, self.pos_control]):
                secondary_identifier = "NULL"
        return primary_identifier, secondary_identifier

    def get_fastqs_dict(self) -> dict:
        """
        Collate R1 and R2 fastqs and their local and cloud paths into a dictionary.
        tso500 runs are not demultiplexed locally so have no local fastq path. All other
        runfolders have fastqs in the BaseCalls directory
            :return fastqs_dict (dict | False):     Dictionary containing R1 and R2 fastqs and
                                                    their local and cloud paths. False if either
                                                    fastq doesn't exist
        """
        fastqs_dict = {"R1": {}, "R2": {}}
        for read in ["R1", "R2"]:
            if self.pipeline == "tso500":
                fastqs_dict[read] = {
                    "name": None,
                    "path": None,
                    "nexus_path":
                        os.path.join(
                            SWConfig.FASTQ_DIRS['tso_fastqs'], self.sample_name,
                            f"{self.sample_name}_{read}.fastq.gz",
                    ),
                }
            else:
                (fastq_name, fastq_path, nexus_fastq_path) = self.get_fastq_paths(read)
                if not fastq_path:
                    fastqs_dict = False
                    break
                else:
                    fastqs_dict[read] = {
                        "name": fastq_name,
                        "path": fastq_path,
                        "nexus_path": nexus_fastq_path,
                    }
        return fastqs_dict
    
    def get_fastq_paths(self, read) -> str:
        """
        Get fastqs in fastq directory that correspond to each sample name in the
        sample dictionary. Build the fastq name, local path, and DNAnexus path
        for each fastq file
            :param read (str):                  Either 'R1' or 'R2'
            :return fastq_name (str):           Fastq name
            :return fastq_path (str):           Local fastq path
            :return nexus_fastq_path (str):     DNAnexus fastq path
        """
        matches = [self.sample_name, f"_{read}_"]
        try:
            fastq_name = list(
                fastq_path
                for fastq_path in os.listdir(self.rf_obj.fastq_dir_path)
                if all([substring in fastq_path for substring in matches])
            )[0]
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["fastq_identified"],
                fastq_name,
                ", ".join(matches),
            )
            fastq_path = os.path.join(self.rf_obj.fastq_dir_path, fastq_name)
            nexus_fastq_path = os.path.join(
                    f"{SWConfig.DNANEXUS_PROJ_ID}:{self.nexus_paths['fastqs_dir']}",
                    fastq_name
                )
            return fastq_name, fastq_path, nexus_fastq_path
        except:
            self.rf_obj.rf_loggers.sw.error(
                self.rf_obj.rf_loggers.sw.log_msgs["fastq_nonexistent"],
                ", ".join(matches),
            )
            return False, False, False

    def get_sample_sql_query(self) -> str:
        """
        Call functions to construct SQL query for the sample (sample-level query)
            :return query (str):    Return sample SQL query (sample-level query)
        """
        if self.pipeline in ("pipe", "snp"):
            query = self.return_rd_query()
        elif self.pipeline in ("tso500", "archerdx"):
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
        pipeline_version = str(SWConfig.SQL_IDS["WORKFLOWS"][self.pipeline])
        rd_query = SWConfig.QUERIES["customrun"] % (
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
        pipeline_version = str(SWConfig.SQL_IDS["WORKFLOWS"][self.pipeline])
        panel_id = self.pannum.replace("Pan", "")

        onc_query = SWConfig.QUERIES["oncology"] % (
            f"'{self.primary_identifier}','{self.secondary_identifier}',"
            f"'{self.rf_obj.runfolder_name}','{pipeline_version}','{panel_id}'"
        )
        return onc_query

    def build_sample_dx_run_cmd(self) -> Union[str, str]:
        """
        Build sample-level dx run commands for the workflow and Congenica upload
            :return workflow_cmd (str):                 Dx run command for the sample workflow
            :return decision_support_upload_cmd (str):  Cmd for running the script to generate
                                                        inputs to the decision support tool upload app
        """
        workflow_cmd, decision_support_upload_cmd = [], []

        if self.fastqs_dict:
            if self.pipeline == "wes":
                workflow_cmd = self.create_wes_cmd()
                decision_support_upload_cmd = self.return_decision_support_cmd()
            elif self.pipeline == "pipe":
                workflow_cmd = self.create_pipe_cmd()
                decision_support_upload_cmd = self.return_decision_support_cmd()
            elif self.pipeline == "snp":  # TODO eventually remove this
                workflow_cmd = self.create_snp_cmd()
                decision_support_upload_cmd = False, False
            elif self.pipeline == "archerdx":
                workflow_cmd = self.create_fastqc_cmd()
                decision_support_upload_cmd = False, False
            elif self.pipeline == "tso500":
                workflow_cmd = (
                    self.create_fastqc_cmd()
                )  # Pipeline cmd is built at whole-run level
                decision_support_upload_cmd = self.return_decision_support_cmd()

        return workflow_cmd, decision_support_upload_cmd

    def create_wes_cmd(self) -> str:
        """
        Construct dx run command for WES workflow
            :return (str):  Dx run command string
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"], self.pipeline, self.sample_name
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["wes"]}{self.sample_name}',
                f'{SWConfig.STAGE_INPUTS["wes"]["fastqc1_reads"]}{self.fastqs_dict["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["fastqc2_reads"]}{self.fastqs_dict["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["sentieon_samplename"]}{self.sample_name}',
                f'{SWConfig.STAGE_INPUTS["wes"]["picard_bed"]}{self.panel_settings["hsmetrics_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["wes"]["sambamba_bed"]}{self.panel_settings["sambamba_bedfile"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth,
            ]
        )

    def return_decision_support_cmd(self) -> Union[str, None]:
        """
        Construct decision support tool command for non-reference samples by calling build_congenica_sftp_cmd
        or build_congenica_cmd. If a sample requires Congenica upload, there are 2 methods. If Congenica
        project ID is specified as 'SFTP' within the config it means the sample requires upload via SFTP,
        else if congenica_project ID is specified it means it can be uploaded using the upload agent. Both
        Congenica apps app take inputs in the format jobid.outputname which ensures the job doesn't run until
        the vcfs have been created. App inputs are created by a python script, which is called immediately
        before the app is set off, and the script output (app inputs) is captured by the variable $DSS_INPUTS
            :return (str | None):   Dx run commands (Congenica input command, Congenica upload command),
                                    or None if sample is a reference sample
        """
        if self.pos_control:
            decision_support_cmd = None
        else:
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["decision_support_upload_required"],
                self.nexus_paths["proj_name"],
            )
            # If project is specified then upload via upload agent
            if self.panel_settings["congenica_project"] == "SFTP":  # SFTP upload cmd
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["congenica_upload_required"],
                    self.nexus_paths["proj_name"],
                )
                decision_support_cmd = self.build_congenica_sftp_cmd()
            elif isinstance(self.panel_settings["congenica_project"], int):
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["congenica_upload_required"],
                    self.nexus_paths["proj_name"],
                )
                decision_support_cmd = self.build_congenica_cmd()
            elif self.panel_settings["panel_name"] == "tso500":
                self.rf_obj.rf_loggers.sw.info(
                    self.rf_obj.rf_loggers.sw.log_msgs["qiagen_upload_required"],
                    self.nexus_paths["proj_name"],
                )
                decision_support_cmd = self.build_qiagen_upload_cmd()
            return decision_support_cmd

    def build_congenica_sftp_cmd(self) -> str:
        """
        Build the command to write the Congenica upload dx run command for the SFTP app to the decision
        support tool upload bash script. This command is used to upload the sample to Congenica using
        the SFTP Congenica upload app. Samples requiring upload by SFTP require patient-specific info
        to be pre-added into Congenica by the scientists. Takes BAM and VCF inputs, and does not require
        project IDs, IR templates or name
            :return (str):  Dx run command for the Congenica upload (SFTP app)
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "congenica sftp",
            self.sample_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["congenica_sftp"]}Congenica_SFTP_Upload-{self.sample_name}',
                SWConfig.UPLOAD_ARGS["dest"],
                (SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth).replace(
                    ")", f"' >> {self.rf_obj.decision_support_upload_cmds}"
                ),
            ]
        )

    def build_congenica_cmd(self) -> str:
        """
        Build the command to write the Congenica upload dx run command to the decision support tool
        upload bash script. This command is used to upload the sample to Congenica using the standard
        Congenica upload app. Takes BAM and VCF inputs, along with config-specified inputs congenica
        project ID, credentials, IR template and sample name
            :return (str):  Dx run command for the Congenica upload (standard Congenica upload app)
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "congenica",
            self.sample_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["congenica_upload"]}Congenica_Upload-{self.sample_name}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["congenica_project"]}'
                f'{str(self.panel_settings["congenica_project"])}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["congenica_project"]}'
                f'{self.panel_settings["congenica_credentials"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["ir_template"]}'
                f'{self.panel_settings["congenica_IR_template"]}',
                f'{SWConfig.APP_INPUTS["congenica_upload"]["samplename"]}{self.sample_name}',
                SWConfig.UPLOAD_ARGS["dest"],
                (SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth).replace(
                    ")", f"' >> {self.rf_obj.decision_support_upload_cmds}"
                ),
            ]
        )

    def build_qiagen_upload_cmd(self) -> str:
        """
        Build the command to write the qiagen upload dx run command to the decision
        support tool upload bash script. This command is used to upload the sample
        to QCII. The command takes sample_name and sample_zip_folder as inputs
            :return (str):  Dx run command for the qiagen_upload app
        """
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["qiagen_upload"]}Qiagen_Upload-{self.sample_name}',
                f'{SWConfig.APP_INPUTS["qiagen_upload"]["sample_name"]}{self.sample_name}',
                f'{SWConfig.APP_INPUTS["qiagen_upload"]["sample_zip_folder"]}{self.pannum}{self.sample_name}.zip',
                SWConfig.UPLOAD_ARGS["dest"],
                (SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth).replace(
                    ")", f"' >> {self.rf_obj.decision_support_upload_cmds}"
                ),
            ]
        )

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
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            self.pipeline,
            self.sample_name,
        )
        # Specify instance type for human exome app
        if self.panel_settings["FH"]:  # Larger instance required for FH samples
            GATK_INSTANCE = "mem3_ssd1_v2_x16"
        else:
            GATK_INSTANCE = "mem1_ssd1_v2_x8"
        
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["pipe"]}{self.sample_name}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["fastqc_reads"]}{self.fastqs_dict["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["fastqc_reads"]}{self.fastqs_dict["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_reads1"]}{self.fastqs_dict["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_reads2"]}{self.fastqs_dict["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["bwa_rg_sample"]}{self.sample_name}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_bed"]}{self.panel_settings["sambamba_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_min_base_qual"]}'
                f'{str(self.panel_settings["coverage_min_basecall_qual"])}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_min_mapping_qual"]}'
                f'{str(self.panel_settings["coverage_min_mapping_qual"])}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["sambamba_cov_level"]}'
                f'{str(self.panel_settings["clinical_coverage_depth"])}',
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_filter_cmds"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_excl_dups"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_excl_failed_qual"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_count_overl_mates"],
                self.get_vcfeval_cmd_string(),
                self.get_fhprs_cmd_string(),
                f'{SWConfig.STAGE_INPUTS["pipe"]["fhprs_bed"]}{SWConfig.FH_PRS_BEDFILE}',
                self.get_polyedge_cmd_string(),
                self.get_masked_reference_cmd_string(),
                f'{SWConfig.STAGE_INPUTS["pipe"]["picard_bed"]}{self.panel_settings["hsmetrics_bedfile"]}',
                f'{SWConfig.STAGE_INPUTS["pipe"]["picard_capturetype"]}{self.panel_settings["capture_type"]}',
                SWConfig.STAGE_INPUTS["pipe"]["gatk_padding"],
                f'{SWConfig.STAGE_INPUTS["pipe"]["filter_vcf_bed"]}{self.panel_settings["variant_calling_bedfile"]}',
                SWConfig.STAGE_INPUTS["pipe"]["bwa_instance"],
                f'{SWConfig.STAGE_INPUTS["pipe"]["gatk_instance"]}={GATK_INSTANCE}',
                SWConfig.STAGE_INPUTS["pipe"]["filter_vcf_instance"],
                SWConfig.STAGE_INPUTS["pipe"]["picard_instance"],
                SWConfig.STAGE_INPUTS["pipe"]["sambamba_instance"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth
            ]
        )

    def get_vcfeval_cmd_string(self) -> str:
        """
        Get command string for input to vcfeval stage of PIPE workflow. If sample is not
        NA12878 we want to skip the vcfeval stage (the app default is skip=False)
            :return (str):  App input string
        """
        prefix_str = (  # Set prefix as samplename
            f'{SWConfig.STAGE_INPUTS["pipe"]["happy_prefix"]}{self.sample_name}'
        )
        if self.pos_control:
            skip_str = f'{SWConfig.STAGE_INPUTS["pipe"]["happy_skip"]}false'
        else:
            skip_str = f'{SWConfig.STAGE_INPUTS["pipe"]["happy_skip"]}true'

        return " ".join([prefix_str, skip_str])

    def get_fhprs_cmd_string(self) -> str:
        """
        Get command string for input FH_PRS stage of PIPE workflow. If sample is specified as
        requiring FH analysis in the config, set skip to False (the app default is skip=True),
        and specify outptut as both VCF and GVCF
            :return fh_prs_cmd_string: App input string
        """
        if self.panel_settings["FH"]:
            return " ".join(
                [
                    SWConfig.STAGE_INPUTS["pipe"]["fhprs_skip"],
                    SWConfig.STAGE_INPUTS["pipe"]["gatk_vcf_format"],
                    SWConfig.PIPE_FH_GATK_TIMEOUT_ARGS,
                ]
            )
        else:
            return ""

    def get_polyedge_cmd_string(self) -> str:
        """
        Get command string for polyedge stage of PIPE workflow. If sample is specified
        as requiring polyedge analysis in the config, set skip to False (the app default
        is skip=True) and specify gene chrom and start / end inputs
            :return polyedge_cmd_string (str):  App input string
        """
        if self.panel_settings["polyedge"]:
            return " ".join(
                [
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_gene"]}{self.panel_settings["polyedge"]["gene"]}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_chrom"]}{str(self.panel_settings["polyedge"]["chrom"])}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_poly_start"]}'
                    f'{str(self.panel_settings["polyedge"]["poly_start"])}',
                    f'{SWConfig.STAGE_INPUTS["pipe"]["polyedge_poly_end"]}'
                    f'{str(self.panel_settings["polyedge"]["poly_end"])}',
                    SWConfig.STAGE_INPUTS["pipe"]["polyedge_skip"],
                ]
            )
        else:
            return ""

    def get_masked_reference_cmd_string(self) -> str:
        """
        Get input string for masked reference input for BWA stage of PIPE workflow, if
        specified for the pan number in the config
            :return masked_reference_cmd_string (str):  Masked reference input string
        """
        if self.panel_settings["masked_reference"]:
            return f"{SWConfig.STAGE_INPUTS['pipe']['bwa_ref']}{self.panel_settings['masked_reference']}"
        else:
            return ""

    def create_snp_cmd(self) -> str:  # TODO eventually remove this
        """
        Construct dx run command for SNP workflow
            :return (str):  Dx run command string
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            self.pipeline,
            self.sample_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["snp"]}{self.sample_name}',
                f'{SWConfig.STAGE_INPUTS["snp"]["fastqc1_reads"]}{self.fastqs_dict["R1"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["snp"]["fastqc2_reads"]}{self.fastqs_dict["R2"]["nexus_path"]}',
                f'{SWConfig.STAGE_INPUTS["snp"]["sentieon_samplename"]}{self.sample_name}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth,
            ]
        )

    def create_fastqc_cmd(self) -> str:
        """
        Build dx run command to run fastqc
            :return (str): Dx run command for fastqc app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "fastqc",
            self.sample_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["fastqc"]}FastQC-{self.sample_name}',
                f'{SWConfig.APP_INPUTS["fastqc"]["reads"]}{self.fastqs_dict["R1"]["nexus_path"]}',
                f'{SWConfig.APP_INPUTS["fastqc"]["reads"]}{self.fastqs_dict["R2"]["nexus_path"]}',
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth,
            ]
        )

    def return_sample_dict(self) -> dict:
        """
        Return sample dictionary with all collected information about the sample
            :return (dict): Collected information about the sample
        """
        return {
            "sample_name": self.sample_name,
            "pos_control": self.pos_control,
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
            "decision_support_upload_cmd": self.decision_support_upload_cmd,
        }


class BuildDxCommands(SWConfig):
    """
    Build run-wide commands for runfolder, and write sample-level commands from the
    samples_obj along with the run-wide commands to the dx run script

    Attributes:
        rf_obj (obj):                   RunfolderObject object (contains runfolder-specific attributes)
        samples_obj (obj):              CollectRunfolderSamples object (contains sample-specific attributes
        nexus_project_id (str):         Project ID, generated when the DNAnexus project is created
        dnanexus_auth (str):            DNAnexus auth token
        dx_cmd_list (list):             List of dx run commands for the project
        dx_postprocessing_cmds (list):  List of dx run commands to run after the TSO app. TSO runs only

    Methods:
        build_dx_cmds()
            Build dx run commands (pipeline-dependent) by calling the relevant functions
            and appending to the dx_cmd_list. This includes both sample workflow-level
            commands (self.return_sample_workflow_cmds()), and runwide commands
        return_tso_runwide_cmds()
            Collect runwide commands for tso500 runs. Includes tso500 app, fastqc,
            sompy, sambamba, multiqc and duty_csv. TSO commands are all generated within
            this function as the dependency order is different for this pipeline
        create_tso500_cmd(tso_ss)
            Build dx run command for tso500 docker app
        get_tso_analysis_options()
            Determine whether its a novaseq run from the runfoldername, and return the
            relevant tso500 app input string
        get_tso_instance_type()
            If run contains high throughput tso pannumbers, return the high throughput
            instance type (larger instance), else return low throughput instance type
        create_sompy_cmd(sample)
            Build dx run command to run sompy on a single VCF file
        create_sambamba_cmd(sample, pannumber)
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
            and Congenica input and upload commands if required for the sample type
        return_analysis_id_cmd()
            Generates the command that runs the congenica_upload python script, and
            captures the script output (the Congenica upload app input string)
        return_wes_runwide_cmds()
            Collect runwide commands for WES runs as a list. This includes peddy
        create_peddy_cmd()
            Build dx run command to run peddy for the project. Run once at the end of a
            WES run and downloads required files from the project
        return_pipe_runwide_cmds()
            Collect runwide commands for PIPE runs as a list. This includes RPKM (single
            command per vcp panel)
        create_rpkm_cmd(core_panel_name)
            Build dx run command to run RPKM for a core panel
        create_ed_readcount_cmd(core_panel_name)
            Build dx run command for exomedepth readcount app
        create_ed_cnvcalling_cmd(panno)
            Build dx run command for exomedepth cnv calling app
        create_duty_csv_cmd()
            Build dx run command to run create_duty_csv app for the run
        write_dx_run_cmds(cmds, script, location)
            Write dx run commands to the dx run script for the runfolder
    """

    def __init__(
        self,
        rf_obj: RunfolderObject,
        samples_obj: CollectRunfolderSamples,
        nexus_project_id: str,
    ):
        """
        Constructor for the BuildDxCommands class
            :param rf_obj (obj):            RunfolderObject object (contains runfolder-specific attributes)
            :param samples_obj (obj):       CollectRunfolderSamples object (contains sample-specific attributes)
            :param nexus_project_id (str):  Project ID, generated when the DNAnexus project is created
        """
        self.rf_obj = rf_obj
        self.samples_obj = samples_obj
        self.nexus_project_id = nexus_project_id
        self.dnanexus_auth = get_credential(SWConfig.CREDENTIALS["dnanexus_authtoken"])
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmds"]
        )
        self.dx_cmd_list, self.dx_postprocessing_cmds = self.build_dx_cmds()
        self.write_dx_run_cmds(  # Write commands to file
            self.dx_cmd_list, self.rf_obj.runfolder_dx_run_script, "dx run bash script"
        )
        if (
            self.samples_obj.pipeline == "tso500"
        ):  # Write commands to TSO post-processing file
            self.write_dx_run_cmds(
                self.dx_postprocessing_cmds,
                self.rf_obj.post_run_dx_run_script,
                "tso500 postprocessing script",
            )

    def build_dx_cmds(self) -> Union[list, list]:
        """
        Build dx run commands (pipeline-dependent) by calling the relevant functions and
        appending to the dx_cmd_list. This includes both sample workflow-level commands
        (self.return_sample_workflow_cmds()), and runwide commands
            :return dx_cmd_list (list):             Dx run command list for the run
            :return dx_postprocessing_cmds (list):  Commands for postprocessing.
                                                    Currently only releveant to tso500
        """
        # Get sample workflow-level commands
        if self.samples_obj.pipeline == "tso500":
            dx_cmd_list, dx_postprocessing_cmds = self.return_tso_runwide_cmds()
        else:
            dx_postprocessing_cmds = []
            dx_cmd_list = self.return_sample_workflow_cmds()

            # Get pipeline-specific run-wide commands. SNP, ADX and ONC do not have
            # pipeline-specific run-wide commands
            if self.samples_obj.pipeline == "wes":
                dx_cmd_list.extend(self.return_wes_runwide_cmds())
            if self.samples_obj.pipeline == "pipe":
                dx_cmd_list.extend(self.return_pipe_runwide_cmds())

            # Get run-wide commands that apply to all sequencing runs
            dx_cmd_list.extend(self.return_multiqc_cmds())
            
            if self.samples_obj.pipeline == "pipe":
                # We want duty_csv to also depend on the cnv calling jobs for PIPE workflows
                dx_cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_cnv_recombined"])

            dx_cmd_list.append(self.create_duty_csv_cmd())

            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["cmds_built"]
            )
        return dx_cmd_list, dx_postprocessing_cmds

    def return_tso_runwide_cmds(self) -> Union[list, list]:
        """
        Collect runwide commands for tso500 runs as a list. This includes tso500 app,
        fastqc, sompy, sambamba, multiqc and duty_csv. TSO commands are all generated
        within this function as the dependency order is different for this pipeline
            :return dx_cmd_list (list):     List of runwide commands for tso runs
            :dx_postprocessing_cmds (list): Post-processing commands for tso runs
        """
        dx_cmd_list, dx_postprocessing_cmds = [
            f"PROJECT_NAME={self.samples_obj.nexus_paths['proj_name']}",
            f"RUNFOLDER_NAME={self.rf_obj.runfolder_name}",
            SWConfig.EMPTY_DEPENDS
        ]
        sambamba_cmds_list = []
        # Remove base SampleSheet as we only want to use split SampleSheets
        for tso_ss in self.rf_obj.tso_ss_list:
            if tso_ss != self.rf_obj.samplesheet_name:
                dx_cmd_list.append(self.create_tso500_cmd(tso_ss))

        dx_cmd_list.append(
            (
                f"echo 'PROJECT_ID={self.nexus_project_id}"
                f"' >> {self.rf_obj.decision_support_upload_cmds}"
            )
        )
        for sample_name in self.samples_obj.samples_dict.keys():
            dx_cmd_list.append(
                self.samples_obj.samples_dict[sample_name][
                    "decision_support_upload_cmd"
                ]
            )
            # Append all fastqc commands to cmd_list
            dx_postprocessing_cmds.append(
                self.samples_obj.samples_dict[sample_name]["sample_pipeline_cmd"]
            )
            dx_postprocessing_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])
            sambamba_cmds_list.append(
                self.create_sambamba_cmd(
                    sample_name, self.samples_obj.samples_dict[sample_name]["pannum"]
                )
            )
            # Exclude negative controls from the depends list as the NTC coverage
            # calculation can often fail. We want the coverage report for the NTC sample
            # to help assess contamination. Only add to depends_list if job ID from
            # previous command is not empty
            if not self.samples_obj.samples_dict[sample_name]["neg_control"]:
                sambamba_cmds_list.append(SWConfig.UPLOAD_ARGS["depends_list"])

            if self.samples_obj.samples_dict[sample_name]["pos_control"]:
                dx_postprocessing_cmds.append(
                    self.create_sompy_cmd(sample_name)
                )
                # Only add to depends_list if job ID from previous command
                # is not empty
                dx_postprocessing_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

        dx_postprocessing_cmds.extend(self.return_multiqc_cmds())
        # Set off after as they are not depended upon by MultiQC but are
        # required for duty_csv
        dx_postprocessing_cmds.extend(sambamba_cmds_list)
        dx_postprocessing_cmds.append(self.create_duty_csv_cmd())

        return dx_cmd_list, dx_postprocessing_cmds

    def create_tso500_cmd(self, tso_ss: str) -> str:
        """
        Build dx run command for tso500 docker app
            :param tso_ss (str):    TSO SampleSheet
            :return (str):          Dx run command for tso500 app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            self.samples_obj.pipeline,
            tso_ss,
        )
        return " ".join( 
            [
                f'{SWConfig.DX_CMDS["tso500"]}{SWConfig.RUNFOLDER_NAME}',
                SWConfig.APP_INPUTS["tso500"]["docker"],
                f'{SWConfig.APP_INPUTS["tso500"]["samplesheet"]}{tso_ss}',
                SWConfig.APP_INPUTS["tso500"]["project_name"],
                SWConfig.APP_INPUTS["tso500"]["runfolder_name"],
                self.get_tso_analysis_options(),
                self.get_tso_instance_type(),
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.rf_obj.dnanexus_auth,
            ]
        )

    def get_tso_analysis_options(self) -> str:
        """
        Determine whether its a novaseq run from the runfoldername, and return the
        relevant tso500 app input string
            :return (str):  Analysis options for the tso500 app
        """
        if SWConfig.NOVASEQ_ID in self.rf_obj.runfolder_name:
            tso500_analysis_options = "--isNovaSeq "
        else:
            tso500_analysis_options = ""
        return f'{SWConfig.APP_INPUTS["tso500"]["analysis_options"]}{tso500_analysis_options}'

    def get_tso_instance_type(self) -> str:
        """
        If run contains high throughput tso pannumbers, return the high throughput
        instance type (larger instance), else return the low throughput instance type
            :return (str):  Instance type command for tso500 app execution
        """
        if any(
            SWConfig.PANEL_DICT[pannumber]["throughput"] == "high"
            for pannumber in self.samples_obj.unique_pannos
        ):
            return f"--instance-type {SWConfig.APP_INPUTS['tso500']['ht_instance']}"
        else:
            return f"--instance-type {SWConfig.APP_INPUTS['tso500']['lt_instance']}"

    def create_sompy_cmd(self, sample: str) -> str:
        """
        Build dx run command to run sompy on a single VCF file
            :param sample (str):    Sample name
            :return (str):          Dx run command for sompy app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"], "sompy", sample
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["sompy"]}Sompy-{sample}',
                SWConfig.APP_INPUTS["sompy"]["truth_vcf"],
                f'{SWConfig.APP_INPUTS["sompy"]["query_vcf"]}{sample}/{sample}_MergedSmallVariants.genome.vcf',
                SWConfig.APP_INPUTS["sompy"]["tso"],
                SWConfig.APP_INPUTS["sompy"]["skip"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def create_sambamba_cmd(self, sample: str, pannumber: str) -> str:
        """
        Build dx run command to run sambamba on a single BAM file
            :param sample (str):    Sample name
            :param pannumber (str): Config-defined pan number for sample
            :return (str):          Dx run command for sambamba app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "sambamba",
            sample,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["sambamba"]}Sambamba_Chanjo-{sample}',
                f'{SWConfig.APP_INPUTS["sambamba"]["bam"]}{sample}/{sample}.bam',
                f'{SWConfig.APP_INPUTS["sambamba"]["bai"]}{sample}/{sample}.bam.bai',
                f'{SWConfig.APP_INPUTS["sambamba"]["coverage_level"]}'
                f'{str(SWConfig.PANEL_DICT[pannumber]["clinical_coverage_depth"])}',
                f'{SWConfig.APP_INPUTS["sambamba"]["sambamba_bed"]}'
                f'{SWConfig.PANEL_DICT[pannumber]["sambamba_bedfile"]}',
                SWConfig.APP_INPUTS["sambamba"]["cov_cmds"]
                % (
                    str(
                        SWConfig.PANEL_DICT[pannumber]["coverage_min_basecall_qual"]
                    ),
                    str(
                        SWConfig.PANEL_DICT[pannumber]["coverage_min_mapping_qual"]
                    ),
                ),
                f'{SWConfig.UPLOAD_ARGS["dest"]}:/coverage/{pannumber}',
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def return_multiqc_cmds(self) -> list:
        """
        Create list of multiqc commands (for running multiqc and upload multiqc apps) by
        calling the relevant methods
            :return cmd_list (str): List of multiqc commands
        """
        cmd_list = []
        cmd_list.append(self.create_multiqc_cmd())
        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list"])
        cmd_list.append(self.create_upload_multiqc_cmd())
        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list"])
        return cmd_list

    def create_multiqc_cmd(self) -> str:
        """
        Build dx run command to run MultiQC for the run. MultiQC is run after all QC tools have been
        run. Requires a project to download data from, and a coverage level. Coverage level differs
        between panels. The lowest value for the panels on the run is used
            :return (str): Dx run command for MultiQC app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "multiqc",
            self.rf_obj.runfolder_name,
        )
        coverage_level = list(
            set(
                [
                    v["multiqc_coverage_level"]
                    for k, v in SWConfig.CAPTURE_PANEL_DICT.items()
                    if v["pipeline"] == self.samples_obj.pipeline
                ]
            )
        )[0]
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["multiqc"]}MultiQC',
                SWConfig.APP_INPUTS["multiqc"]["project_name"],
                f'{SWConfig.APP_INPUTS["multiqc"]["coverage_level"]}{str(coverage_level)}',
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ],
        )

    def create_upload_multiqc_cmd(self) -> str:
        """
        Build dx run command to run upload_multiqc app for the run. This uploads the
        MultiQC data to the genomics server. The input to the upload_multiqc app is the
        html_report output of the multiqc app in the format jobid:output_name
            :return (str): Dx run command for upload_multiqc app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "upload multiqc",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["upload_multiqc"]}Upload_MultiQC',
                SWConfig.APP_INPUTS["upload_multiqc"]["multiqc_html"],
                SWConfig.APP_INPUTS["upload_multiqc"]["lane_metrics"],
                SWConfig.APP_INPUTS["upload_multiqc"]["multiqc_output"],
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def return_sample_workflow_cmds(self) -> list:
        """
        Return sample-level commands. This includes the sample workflow command,
        and Congenica input and upload commands if required for the sample type
            :return cmd_list (list):    List of per-sample commands
        """
        cmd_list = [
            f"PROJECT_NAME={self.samples_obj.nexus_paths['proj_name']}",
            f"RUNFOLDER_NAME={self.rf_obj.runfolder_name}",
            SWConfig.EMPTY_DEPENDS,
        ]
        
        if self.samples_obj.pipeline == "pipe":
            cmd_list.extend(SWConfig.EMPTY_CP_DEPENDS)
        for sample_name in self.samples_obj.samples_dict.keys():
            self.rf_obj.rf_loggers.sw.info(
                self.rf_obj.rf_loggers.sw.log_msgs["sample_identified"],
                self.samples_obj.pipeline,
                sample_name,
            )
            cmd_list.append(
                self.samples_obj.samples_dict[sample_name]["sample_pipeline_cmd"]
            )
            cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list"])

            if self.samples_obj.pipeline == "pipe":
                # Add to gatk depends list because RPKM must depend only upon the
                # sample workflows completing successfully, whilst other downstream
                # apps depend on all prior jobs completing succesfully
                cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_gatk"])

            if self.samples_obj.pipeline in ["wes", "pipe"]:
                cmd_list.append(self.return_analysis_id_cmd())
                cmd_list.append(
                    self.samples_obj.samples_dict[sample_name][
                        "decision_support_upload_cmd"
                    ]
                )
        return cmd_list

    def return_analysis_id_cmd(self) -> str:
        """
        Generates the command that runs the congenica_upload python script, and captures the script
        output (the Congenica upload app input string) congenica_upload support tool python script is run
        after each dx run command, taking analysis and project name as input, and printing the required
        inputs to the command line which are required by the Congenica upload script ${JOB_ID} is a bash
        variable which will be populated by when run on the command line. The python script has three
        inputs - the analysisID (${JOB_ID}), and -p is the DNAnexus project the analysis is running in
            :return (str):  Command that runs the congenica_upload python script and obtains
                            some of the inputs for the upload app dx run command
        """
        return (
            "DSS_INPUTS=$(source /usr/local/bin/miniconda3/etc/profile.d/conda.sh "
            f"&& cd {SWConfig.PROJECT_DIR} && conda activate python3.10.6 && "
            "python3 -m congenica_inputs -a ${JOB_ID} "
            f"-p {SWConfig.DNANEXUS_PROJ_ID} -r {SWConfig.RUNFOLDER_NAME})"
        )

    def return_wes_runwide_cmds(self) -> list:
        """
        Collect runwide commands for WES runs as a list. This includes peddy.
            :return cmd_list (list):    List of runwide commands for WES runs
        """
        return [self.create_peddy_cmd(), SWConfig.UPLOAD_ARGS["depends_list"]]

    def create_peddy_cmd(self) -> str:
        """
        Build dx run command to run peddy for the project. Run once at the
        end of a WES run and downloads required files from the project
            :return (str):  Dx run command for peddy app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "peddy",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["peddy"]}Peddy',
                SWConfig.APP_INPUTS["peddy"]["project_name"],
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def return_pipe_runwide_cmds(self) -> list:
        """
        Collect runwide commands for PIPE runs as a list. This includes RPKM
        (single command per vcp panel)
            :return cmd_list (list):    List of runwide commands for PIPE runs
        """
        cmd_list = []
        for core_panel in ["vcp1", "vcp2", "vcp3"]:
            if core_panel in (
                [
                    self.samples_obj.samples_dict[k]["panel_settings"]["panel_name"]
                    for k, v in self.samples_obj.samples_dict.items()
                ]
            ):
                core_panel_pannos = [
                    self.samples_obj.samples_dict[k]["pannum"]
                    for k, v in self.samples_obj.samples_dict.items()
                    if self.samples_obj.samples_dict[k]["panel_settings"]["panel_name"]
                    == core_panel
                ]
                # Make sure there are enough samples for exome depth and RPKM
                if len(core_panel_pannos) >= 3:
                    if SWConfig.CAPTURE_PANEL_DICT[core_panel][
                        "ed_readcount_bedfile"
                    ]:
                        # CNV calling steps are a dependency of MultiQC
                        cmd_list.append(self.create_ed_readcount_cmd(core_panel))
                        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_edreadcount"])
                        for panno in set(core_panel_pannos):
                            cmd_list.append(self.create_ed_cnvcalling_cmd(panno))
                            cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_cnvcalling"])

                    cmd_list.append(self.create_rpkm_cmd(core_panel))
                    cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_cnvcalling"])

        cmd_list.append(SWConfig.UPLOAD_ARGS["depends_list_gatk_recombined"])
        return cmd_list

    def create_rpkm_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command to run RPKM for a core panel. RPKM app requires project id,
        bedfile and string containing the pannumber(s) of all files that should be included
        in this analysis (input list is pulled from PanelConfig.VCP_PANELS using the core_panel_name).
        App takes pan numbers as string, and will separate on commas when passed multiple pan numbers
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for RPKM app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "RPKM",
            core_panel_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["rpkm"]}RPKM_using_conifer-{core_panel_name}',
                f'{SWConfig.APP_INPUTS["rpkm"]["bed"]}{SWConfig.CAPTURE_PANEL_DICT[core_panel_name]["rpkm_bedfile"]}',
                SWConfig.APP_INPUTS["rpkm"]["proj"],
                f'{SWConfig.APP_INPUTS["rpkm"]["pannos"]}{",".join(SWConfig.VCP_PANELS[core_panel_name])}',
                SWConfig.UPLOAD_ARGS["depends_gatk"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def create_ed_readcount_cmd(self, core_panel_name: str) -> str:
        """
        Build dx run command for exomedepth readcount app. Exome depth is run in 2 stages,
        firstly readcounts are calculated for each capture panel. Job ID is saved to $ED_READCOUNT_JOB_ID
        which allows the output of this stage to be used to filter CNVs with a panel-specific BEDfile
            :param core_panel_name (str):   Name of synnovis core panel
            :return (str):                  Dx run command for ED readcount app

        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "ED_readcount",
            core_panel_name,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["ed_readcount"]}ED_Readcount-{core_panel_name}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["ref_genome"]}'
                f'{SWConfig.NEXUS_IDS["FILES"]["hs37d5_ref_no_index"]}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["bed"]}'
                f'{SWConfig.CAPTURE_PANEL_DICT[core_panel_name]["ed_readcount_bedfile"]}',
                f'{SWConfig.APP_INPUTS["ed_readcount"]["normals_rdata"]}'
                f'{SWConfig.NEXUS_IDS["FILES"][f"ed_{core_panel_name}_readcount_normals"]}',
                SWConfig.APP_INPUTS["ed_readcount"]["proj"],
                f'{SWConfig.APP_INPUTS["ed_readcount"]["pannos"]}{",".join(SWConfig.ED_PANNOS[core_panel_name])}',
                SWConfig.UPLOAD_ARGS[
                    "depends_gatk"
                ],  # Use list of gatk related jobs to delay start
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def create_ed_cnvcalling_cmd(self, panno: str) -> str:
        """
        Build dx run command for exomedepth cnv calling app
            :param panno (str):     Pannumber to filter CNV calls
            :return (str):          Dx run command for ED cnv calling app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "ED_cnvcalling",
            panno,
        )
        return " ".join(
            [
                f'{SWConfig.DX_CMDS["ed_cnvcalling"]}ED_CNVcalling-{panno}',
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["readcount"]}'
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["readcount_rdata"]}',
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["bed"]}'
                f'{SWConfig.BEDFILE_FOLDER}{SWConfig.PANEL_DICT[panno]["ed_cnvcalling_bedfile"]}_CNV.bed',
                SWConfig.APP_INPUTS["ed_cnvcalling"]["proj"],
                f'{SWConfig.APP_INPUTS["ed_cnvcalling"]["pannos"]}{panno}',
                SWConfig.UPLOAD_ARGS[
                    "depends_gatk"
                ],  # Use list of gatk related jobs to delay start
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def create_duty_csv_cmd(self) -> str:
        """
        Build dx run command to run create_duty_csv app for the run. This creates a CSV
        file for use in downloading files to the trust network with the process_duty_csv
        script. It also sends an email denoting the run is ready for processing. The
        input to the duty_csv app is the DNAnexus project name, and the pan numbers for
        tso samples, stg samples, and the custom panel whole capture for each core panel
            :return (str):  Dx run command for duty_csv app
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["building_cmd"],
            "create_duty_csv",
            self.rf_obj.runfolder_name,
        )
        return " ".join(
            [
                f"{SWConfig.DX_CMDS['duty_csv']}Duty_CSV",
                SWConfig.APP_INPUTS["duty_csv"]["project_name"],
                f'{SWConfig.APP_INPUTS["duty_csv"]["tso_pannumbers"]}{",".join(SWConfig.TSO_SYNNOVIS_PANNUMBERS)}',
                f'{SWConfig.APP_INPUTS["duty_csv"]["stg_pannumbers"]}{",".join(SWConfig.STG_PANNUMBERS)}',
                f'{SWConfig.APP_INPUTS["duty_csv"]["cp_capture_pannos"]}{",".join(SWConfig.CP_CAPTURE_PANNOS)}',
                SWConfig.UPLOAD_ARGS["depends"],
                SWConfig.UPLOAD_ARGS["dest"],
                SWConfig.UPLOAD_ARGS["token"] % self.dnanexus_auth,
            ]
        )

    def write_dx_run_cmds(self, cmds: list, script: str, location: str) -> None:
        """
        Write dx run commands to the dx run script for the runfolder. Remove any None values
            :param cmds (list): List of commands to write
            :script (str):      Path of script to write commands to
            :location (str):    Name of script the commands are being written to
            :return None:
        """
        self.rf_obj.rf_loggers.sw.info(
            self.rf_obj.rf_loggers.sw.log_msgs["writing_cmds"], location
        )
        # Remove any None values from the command_list
        write_lines(script, "a", list(filter(None, cmds)))


class PipelineEmails(SWConfig):
    """
    Class for sending the start of pipeline emails. Calls the AdEmail class for email
    sending. The following emails are sent:

        - SQL emails for all pipelines. These are sent to binfx. This is because
            samples processed using each workflow are recorded in Moka using an
            insert query per sample
        - Emails with details of the samples being processed. These are sent to binfx
            for all runs, plus to additional recipients as defined within the
            config.ad_config file

        Attributes
            rf_obj (obj):           RunfolderObject object (contains runfolder-specific attributes)
            samples_obj (obj):      CollectRunfolderSamples object (contains sample-specific attributes)
            workflows (list):       List of names of all workflows used to process samples within the run
            sample_count (int):     Number of samples in the run
            email_subj (str):       Email subject used by all emails sent within this class
            email (obj):            AdEmail object (contains methods for sending emails)
            queries (str):          Newline-separated string of SQL queries

        Methods
            collect_queries()
                Collect queries from the samples_dict (for all runs with per-sample
                queries). For those with run-level queries (wes), call return_wes_query()
            return_wes_query()
                Return WES SQL query. This is a single update query per-run
            send_sql_email()
                Construct and send pipeline started email using the AdEmail class
            send_samples_email()
                Construct and send the samples being processed email using AdEmail class
    """

    def __init__(self, rf_obj: RunfolderObject, samples_obj: SampleObject):
        """
        Constructor for the PipelineEmails class
        """
        self.rf_obj = rf_obj
        self.samples_obj = samples_obj
        self.workflows = [
            self.samples_obj.samples_dict[k]["panel_settings"]["pipeline"]
            for k in self.samples_obj.samples_dict.keys()
        ]
        self.sample_count = len(self.samples_obj.samples_dict)
        self.email_subj = (
            SWConfig.MAIL_SETTINGS["pipeline_started_subj"] % self.rf_obj.runfolder_name
        )
        self.email = AdEmail(self.rf_obj.rf_loggers.sw)
        self.queries = self.collect_queries()

    def collect_queries(self) -> str:
        """
        Collect queries from the samples_dict (for all runs with per-sample queries).
        For those with run-level queries (wes), call return_wes_query()
            :return (list):  List of SQL queries
        """
        if self.samples_obj.pipeline == "wes":
            queries = self.return_wes_query()
        else:
            queries = [
                self.samples_obj.samples_dict[k]["SQL_query"]
                for k in self.samples_obj.samples_dict.keys()
            ]
        return queries

    def return_wes_query(self) -> str:
        """
        Return WES SQL query. This is a single update query per-run
            :return query (str):    Single update query for the WES run
        """
        wes_dnanumbers = [
            self.samples_obj.samples_dict[k]["identifiers"]["primary"]
            for k in self.samples_obj.samples_dict.keys()
        ]
        return [
            SWConfig.QUERIES["wes"]
            % (
                str(SWConfig.SQL_IDS["WORKFLOWS"]["wes"]),
                str(SWConfig.SQL_IDS["WES_TEST_STATUS"]["data_processing"]),
                ("','").join(wes_dnanumbers),
                str(SWConfig.SQL_IDS["WES_TEST_STATUS"]["nextseq_sequencing"]),
            )
        ]

    def send_sql_email(self) -> None:
        """
        Construct and send pipeline started email using the AdEmail class. Email is sent
        to the binfx team. Contains SQL queries used to update the Moka database.
        Logging is carried out within the AdEmail class
            :return None:
        """
        email_html = self.email.generate_email_html(
            self.rf_obj.runfolder_name,
            ",".join(list(set(self.workflows))),
            " <br> ".join(self.queries),
            self.sample_count,
            False,
        )
        self.email.send_email(
            recipients=[SWConfig.MAIL_SETTINGS["binfx_recipient"]],
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
            self.rf_obj.runfolder_name,
            ",".join(list(set(self.workflows))),
            False,
            self.sample_count,
            " <br> ".join(self.samples_obj.samples_dict.keys()),
        )
        recipients = [SWConfig.MAIL_SETTINGS["binfx_recipient"]]
        if self.samples_obj.pipeline == "wes":
            recipients.extend(SWConfig.MAIL_SETTINGS["wes_samplename_emaillist"])
        elif self.samples_obj.pipeline in ["tso500", "archerdx"]:
            recipients.append(SWConfig.MAIL_SETTINGS["oncology_ops_email"])
        self.email.send_email(
            recipients=recipients,
            email_subject=self.email_subj,
            email_message=email_html,
            email_priority=1,
        )
