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
- DevPipeline
    Collate DNAnexus commands for development runs. This runtype has no decision
    support upload or postprocessing commands, or SQL queries
- ArcherDxPipeline
    Collate DNAnexus commands for ArcherDX runs. This runtype has no decision
    support upload or postprocessing commands
- SnpPipeline
    Collate DNAnexus commands for SNP runs. This run type has no decision
    support upload or post processing commands
- OncoDeepPipeline
    Collate DNAnexus commands for OncoDEEP runs. This runtype has no post processing commands
- TsoPipeline
    Collate commands for TSO workflow. This runtype has postprocessing commands, decision
    support upload commands, and SQL queries
- WesPipeline
    Collate commands for WES workflow. This runtype has no postprocesing commands
- CustomPanelsPipelines
    Collate commands for Custom Panels workflow. This runtype has no postprocesing commands
"""

import sys
import os
import re
import subprocess
from itertools import chain
from typing import Optional, Union
from ad_logger.ad_logger import AdLogger, shutdown_logs
from config.ad_config import SWConfig
import logging
from upload_runfolder.upload_runfolder import UploadRunfolder
from config.ad_config import DemultiplexConfig
from toolbox.toolbox import (
    return_scriptlog_config,
    test_upload_software,
    RunfolderObject,
    RunfolderSamples,
    read_lines,
    get_num_processed_runfolders,
    get_credential,
    git_tag,
    write_lines,
    execute_subprocess_command,
    get_samplename_dict,
)
from setoff_workflows.pipeline_emails import PipelineEmails
from setoff_workflows.build_dx_commands import (
    BuildRunfolderDxCommands,
    BuildSampleDxCommands,
)
from toolbox.toolbox import script_start_logmsg, script_end_logmsg

# Set up script logging
ad_logger_obj = AdLogger(__name__, "sw", return_scriptlog_config()["sw"])
script_logger = ad_logger_obj.get_logger()


class SequencingRuns(SWConfig):
    """
    Collects sequencing runs and initiates runfolder processing for those
    sequencing runs requiring processing

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
    """

    def __init__(self):
        """
        Constructor for the SequencingRuns class
        """

    def setoff_processing(self) -> None:
        """
        Call methods to collect runfolders for processing. Called by __main__.py
            :return None:
        """
        processed_runfolders = []
        script_start_logmsg(script_logger, __file__)
        runs_to_process = self.set_runfolders()
        if test_upload_software(script_logger):
            for rf_obj in runs_to_process:
                if not os.path.exists(rf_obj.upload_flagfile):
                    script_logger.info(
                        script_logger.log_msgs["start_runfolder_proc"],
                        rf_obj.runfolder_name,
                    )
                    if self.process_runfolder(rf_obj):
                        processed_runfolders.append(rf_obj.runfolder_name)
            get_num_processed_runfolders(script_logger, processed_runfolders)
            script_end_logmsg(script_logger, __file__)

    def set_runfolders(self) -> list:
        """
        Update self.runs_to_process list with NGS runfolders in Illumina and AVITI
        runfolders directory that match the runfolder pattern, and require processing 
        by the script
            :return (list):     List of runfolder objects that require processing
        """
        runs_to_process = []
        # Combine Illumina and AVITI runs in respecitve directories
        # into one list
        illumina_runfolders = os.listdir(SWConfig.RUNFOLDERS)
        aviti_runfolders = os.listdir(SWConfig.AVITI_RUNFOLDER)
        sequenced_folders = illumina_runfolders + aviti_runfolders
        # Iterate through list and check directory follows runfolder patter and also exists in 
        # either the Illumina or AVITI directory. Specific Runfolder path is confirmed when 
        # RunFolderObject is created in Toolbox.py
        for folder in sequenced_folders:
            if re.compile(SWConfig.RUNFOLDER_PATTERN).match(folder):
                if os.path.isdir(
                    os.path.join(SWConfig.RUNFOLDERS, folder)
                    ) or os.path.isdir(
                        os.path.join(SWConfig.AVITI_RUNFOLDER, folder)):
                    script_logger.info(
                        script_logger.log_msgs["runfolder_identified"], folder
                    )
                    rf_obj = RunfolderObject(folder, SWConfig.TIMESTAMP)
                    if self.requires_processing(rf_obj):
                        runs_to_process.append(rf_obj)
        return runs_to_process

    def requires_processing(self, rf_obj: object) -> Optional[bool]:
        """
        Calls other methods to determine whether the runfolder requires processing (demultiplexing
        has finished successfully and the runfolder has not already been uploaded)
            :param rf_obj (obj):        RunfolderObject object (contains runfolder-specific attributes)
            :return (Optional[bool]):   Returns true if runfolder requires processing, else None
        """
        if self.has_demultiplexed(rf_obj):
            if self.already_uploaded(rf_obj):
                script_logger.info(
                    script_logger.log_msgs["runfolder_prev_proc"],
                    rf_obj.runfolder_name,
                )
            else:
                script_logger.info(
                    script_logger.log_msgs["runfolder_requires_proc"],
                    rf_obj.runfolder_name,
                )
                return True

    def has_demultiplexed(self, rf_obj: object) -> Optional[bool]:
        """
        Check if demultiplexing has already been performed and completed sucessfully. Checks the
        demultiplex log file exists, and if present checks the expected success string is in the
        last line of the log file.
            :param rf_obj (obj):        RunfolderObject object (contains runfolder-specific attributes)
            :return (Optional[bool]):   Return True if runfolder already demultiplexed, else None
        """
        if os.path.isfile(rf_obj.demultiplexlog_file):
            logfile_list = read_lines(rf_obj.demultiplexlog_file)
            completed_strs = [
                SWConfig.STRINGS["demultiplex_not_required_msg"].partition(" ")[-1],
                SWConfig.STRINGS["illumina_demultiplex_success"],
                SWConfig.STRINGS["aviti_demultiplex_success"],
            ]
            if logfile_list:
                if any(
                    re.search(success_str, logfile_list[-1])
                    for success_str in completed_strs
                ):
                    script_logger.info(script_logger.log_msgs["demux_complete"])
                    return True
                else:
                    script_logger.info(script_logger.log_msgs["success_string_absent"])
            else:
                script_logger.info(script_logger.log_msgs["demultiplexlog_empty"])
        else:
            script_logger.info(script_logger.log_msgs["not_yet_demultiplexed"])

    def already_uploaded(self, rf_obj: object) -> Optional[bool]:
        """
        Checks for presence of DNAnexus upload flag file (denotes that the runfolder has already been processed)
            :param rf_obj (obj):        RunfolderObject object (contains runfolder-specific attributes)
            :return (Optional[bool]):   Returns True if runfolder already uploaded, else None
        """
        if os.path.isfile(rf_obj.upload_flagfile):
            script_logger.info(script_logger.log_msgs["ua_file_present"])
            return True
        else:
            script_logger.info(script_logger.log_msgs["ua_file_absent"])

    def process_runfolder(self, rf_obj: object) -> Optional[bool]:
        """
        If software tests pass, set up logging and pass rf_obj to the ProcessRunfolder class for processing,
        shutting down logs upon completion. Append to self.processed_runfolders
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific attributes)
            :return (str):          True name if runfolder has been processed
        """
        loggers = rf_obj.get_runfolder_loggers(__package__)  # Get dictionary of loggers

        loggers["sw"].info(
            loggers["sw"].log_msgs["ad_version"],
            git_tag(),
        )
        samplename_dict = get_samplename_dict(loggers["sw"], rf_obj.samplesheet_path)
        if samplename_dict:
            ProcessRunfolder(rf_obj, loggers)
            for logger_name in loggers.keys():
                shutdown_logs(loggers[logger_name])  # Shut down logging
            script_logger.info(
                script_logger.log_msgs["runfolder_processed"],
                rf_obj.runfolder_name,
            )
            return True


class ProcessRunfolder(SWConfig):
    """
    A new instance of this class is initiated for each runfolder being assessed. Calls methods to process and
    upload a runfolder including creation of DNAnexus project, upload of data using upload_runfolder,
    building and execution of dx run commands to set off sample workflows and apps, creation of decision
    support tool upload scripts, and sending of pipeline emails

    Attributes:
        rf_obj (obj):                       RunfolderObject() object (contains runfolder-specific attributes)
        loggers (dict):                     Dict of loggers
        dnanexus_auth (str):                DNAnexus auth token
        rf_samples_obj (object):            RunfolderSamples object
        users_dict (dict):                  Dictionary of users and admins requiring access to the DNAnexus project
        nexus_identifiers (dict):           Dictionary containing project name and ID
        upload_runfolder (obj):             UploadRunfolder() object with methods that can be called to upload
                                            files to the DNAnexus project
        upload_cmds (dict):                 Dictionary of commands for uploading files to the DNAnexus project
        pre_pipeline_upload_dict (dict):    Dict of files to upload prior to pipeline setoff, and commands
        pipeline_obj (object):              Object with the workflow_cmds, dx_postprocessing_cmds,
                                            decision_support_upload_cmds and sql_queries as attributes
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
        build_dx_commands()
            Calls other classes to generate the required commands for the runfolder
        write_dx_run_cmds(pipeline_obj)
            Write dx run commands to the dx run script, post dx run script, and decision
            support upload script for the runfolder
        pre_pipeline_upload()
            Uploads the files in the rf_obj.pre_pipeline_upload_dict for the
            runfolder. Calls the tso runfolder upload function if the runfolder is tso
        upload_to_dnanexus(filetype, file_upload_dict)
            Passes the command and file list in file_upload_dict to upload_runfolder.upload_files()
            which writes log messages to the upload agent log within the runfolder
        upload_rest_of_runfolder()
            Backs up the rest of the runfolder, ignoring files dependent upon the type of run
        run_dx_run_commands()
            Execute the dx run bash script
        post_pipeline_upload()
            Uploads the rest of the runfolder if not a tso run, and uploads the
            runfolder logfiles (upload_agent file is not uploaded because it is being
            written to as the upload is taking place)
    """

    def __init__(self, rf_obj: RunfolderObject, loggers: dict):
        """
        Constructor for the RunfolderProcessor class. Calls the class methods
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
            :param loggers (dict):  Dict of loggers
        """
        self.rf_obj = rf_obj
        self.loggers = loggers
        self.dnanexus_auth = get_credential(SWConfig.CREDENTIALS["dnanexus_authtoken"])
        open(
            self.rf_obj.upload_flagfile, "w"
        ).close()  # Create upload flag file (prevents processing by other script runs)
        self.rf_samples_obj = RunfolderSamples(self.rf_obj, self.loggers["sw"])
        self.users_dict = self.get_users_dict()
        self.write_project_creation_script()
        self.nexus_identifiers = {
            "proj_name": self.rf_samples_obj.nexus_paths["proj_name"],
            "proj_id": self.run_project_creation_script(),
        }
        self.upload_runfolder = UploadRunfolder(
            self.loggers["backup"],
            self.rf_obj.runfolder_name,
            self.rf_obj.runfolderpath,
            self.rf_obj.upload_flagfile,
            self.nexus_identifiers,
        )
        self.upload_cmds = self.get_upload_cmds()
        self.pre_pipeline_upload_dict = self.create_file_upload_dict()
        self.pipeline_obj = self.build_dx_commands()
        self.write_dx_run_cmds()
        self.pre_pipeline_upload()
        
        # Skip run_dx_run_commands for MSK pipeline
        if self.rf_samples_obj.pipeline != "msk":
            self.run_dx_run_commands()
        
        if self.rf_samples_obj.pipeline == "archerdx":
            self.run_decision_support_commands()
        elif self.rf_samples_obj.pipeline == "msk":
            self.run_msk_commands()
        self.pipeline_emails = PipelineEmails(
            self.rf_obj,
            self.rf_samples_obj,
            self.pipeline_obj.sql_queries,
            self.loggers["sw"],
        )
        if self.pipeline_obj.sql_queries:
            self.pipeline_emails.send_sql_email()
        self.pipeline_emails.send_samples_email()
        self.post_pipeline_upload()

    def get_users_dict(self) -> dict:
        """
        Create a dictionary of users and admins that require access to the DNAnexus project. This also
        includes dry lab DNAnexus IDs if applicable for the samples in the runfolder. These are taken
        from the per-sample panel_settings in the samples_dict. This is required because some samples
        are analysed at dry labs, with access to projects only given where there is a sample for that
        dry lab on the run
            :return (dict):     Dictionary of users and admins requiring access to the DNAnexus project
        """
        dry_lab_list = list(
            set(
                [
                    v["panel_settings"]["dry_lab"]
                    for k, v in self.rf_samples_obj.samples_dict.items()
                    if v["panel_settings"]["dry_lab"]
                ]
            )
        )
        if True in dry_lab_list:
            viewers = list(
                chain([SWConfig.BSPS_ID], SWConfig.DNANEXUS_USERS["viewers"])
            )
        else:
            viewers = SWConfig.DNANEXUS_USERS["viewers"]
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["view_users"],
            viewers,
        )
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["admin_users"],
            SWConfig.DNANEXUS_USERS["admins"],
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
            f"AUTH={self.dnanexus_auth}",
            SWConfig.DX_CMDS["create_proj"]
            % (
                SWConfig.PROD_ORGANISATION,
                self.rf_samples_obj.nexus_paths["proj_name"],
            ),
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
                        )
                    )
            else:
                self.loggers["sw"].info(
                    self.loggers["sw"].log_msgs["no_users"],
                    permissions_level,
                )
        lines_to_write.append("echo $PROJECT_ID")
        write_lines(self.rf_obj.proj_creation_script, "w", lines_to_write)

    def run_project_creation_script(self) -> str:
        """
        Set off the project creation script using subprocess. The output of this command is
        checked to ensure it meets the expected success pattern. If unsuccessful, exit script
            :return projectid (str):    Project ID of the created project
        """
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["creating_proj"],
            self.rf_obj.proj_creation_script,
        )
        project_creation_cmd = f"bash {self.rf_obj.proj_creation_script}"

        project_id, err, returncode = execute_subprocess_command(
            project_creation_cmd, self.loggers["sw"], "exit_on_fail"
        )
        if returncode == 0:
            return project_id
        else:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["proj_creation_fail"],
                self.rf_samples_obj["proj_name"],
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
                " ".join(
                    f"'{cd_file}'" for cd_file in self.rf_obj.cluster_density_files
                ),
            ),
            "bclconvert_qc": SWConfig.DX_CMDS["file_upload_cmd"]
            % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                 "/QC/bclconvert/",
                " ".join(
                    f"'{cd_file}'" for cd_file in self.rf_obj.bclconvertstats_file
                ),
            ),
            "logfiles": SWConfig.DX_CMDS["file_upload_cmd"]
            % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                self.rf_samples_obj.nexus_paths["logfiles_dir"],
                " ".join(f"'{logfile}'" for logfile in self.rf_obj.logfiles_to_upload),
            ),
        }
        if self.rf_samples_obj.pipeline == "tso500":
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
                f"/{self.rf_obj.runfolder_name}",
                " ".join(f"'{samplesheet}'" for samplesheet in samplesheet_paths),
            )
        if self.rf_samples_obj.pipeline == "oncodeep":
            upload_cmds["masterfile"] = SWConfig.DX_CMDS["file_upload_cmd"] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                f"/",
                self.rf_obj.runfolder_masterfile_path,
            )
        if self.rf_samples_obj.pipeline != "tso500":
            # tso500 run is not demultiplexed locally so there are no fastqs
            # All other runfolders have fastqs in the BaseCalls directory
            # This section covers uploading AVITI fastqs as this is only thing
            # Needed for DNANexus processing
            upload_cmds["fastqs"] = SWConfig.DX_CMDS["file_upload_cmd"] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                self.rf_samples_obj.nexus_paths["fastqs_dir"],
                " ".join(
                    [
                        self.rf_samples_obj.fastqs_str,
                        self.rf_samples_obj.undetermined_fastqs_str,
                    ]
                ),
            )
            upload_cmds["runfolder_samplesheet"] = SWConfig.DX_CMDS[
                "file_upload_cmd"
            ] % (
                self.rf_obj.dnanexus_auth,
                self.nexus_identifiers["proj_id"],
                "/",
                self.rf_obj.runfolder_samplesheet_path,
            )
        return upload_cmds

    def split_tso_samplesheet(self) -> list:
        """
        Split tso500 SampleSheet into parts with x samples per SampleSheet (no.
        defined in TSO_BATCH_SIZE), and write to runfolder
            :return (list):     SampleSheet names
        """
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["splitting_tso_samplesheet"],
            SWConfig.TSO_BATCH_SIZE,
            self.rf_obj.samplesheet_path,
        )
        samplesheet_list = []
        samples, samplesheet_header = self.read_tso_samplesheet()
        # Split samples into batches (size specified in config)
        batches = [
            samples[i : i + SWConfig.TSO_BATCH_SIZE]
            for i in range(0, len(samples), SWConfig.TSO_BATCH_SIZE)
        ]
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["tso_batches_count"],
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
        samplesheet = read_lines(self.rf_obj.runfolder_samplesheet_path)
        for line in samplesheet:
            line = line.strip("\n")
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
        pre_pipeline_upload_dict = {}

        if self.rf_samples_obj.pipeline == "tso500":  # Add SampleSheet entry
            pre_pipeline_upload_dict["runfolder_samplesheet"] = {
                "cmd": self.upload_cmds["runfolder_samplesheet"],
                "files_list": [
                    os.path.join(self.rf_obj.runfolderpath, ss)
                    for ss in self.rf_obj.tso_ss_list
                ],
            }
        else:
            pre_pipeline_upload_dict["runfolder_samplesheet"] = {
                "cmd": self.upload_cmds["runfolder_samplesheet"],
                "files_list": [self.rf_obj.runfolder_samplesheet_path],
            }
            pre_pipeline_upload_dict["fastqs"] = {
                "cmd": self.upload_cmds["fastqs"],
                "files_list": [
                    *self.rf_samples_obj.fastqs_list,
                    *self.rf_samples_obj.undetermined_fastqs_list,
                ],
            }
            if self.rf_obj.sequencer_type != SWConfig.AVITI_ID:
                pre_pipeline_upload_dict["bclconvert_qc"] = {
                "cmd": self.upload_cmds["bclconvert_qc"],
                "files_list": self.rf_obj.bclconvertstats_file,
            }
                pre_pipeline_upload_dict["cluster_density"] = {
                "cmd": self.upload_cmds["cd"],
                "files_list": self.rf_obj.cluster_density_files,
            }
            if self.rf_samples_obj.pipeline == "oncodeep":  # Add MasterFile entry
                pre_pipeline_upload_dict["masterfile"] = {
                    "cmd": self.upload_cmds["masterfile"],
                    "files_list": [self.rf_obj.runfolder_masterfile_path],
                }
        return pre_pipeline_upload_dict

    def build_dx_commands(self) -> object:
        """
        Build dx run commands (pipeline-dependent) by calling the relevant classes and
        appending to the cmd lists
            :return pipeline_obj (object):  Object with the workflow_cmds, dx_postprocessing_cmds,
                                            decision_support_upload_cmds and sql_queries as attributes
        """
        if self.rf_samples_obj.pipeline == "tso500":
            pipeline_obj = TsoPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "archerdx":
            pipeline_obj = ArcherDxPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "msk":
            pipeline_obj = MskPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "wes":
            pipeline_obj = WesPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "oncodeep":
            pipeline_obj = OncoDeepPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "snp":
            pipeline_obj = SnpPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "gatk_pipe":
            pipeline_obj = CustomPanelsPipelines(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )
        if self.rf_samples_obj.pipeline == "seglh_pipe":
            pipeline_obj = CustomPanelsPipelines(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )                       
        if self.rf_samples_obj.pipeline == "dev":
            pipeline_obj = DevPipeline(
                self.rf_obj, self.rf_samples_obj, self.loggers["sw"]
            )

        self.loggers["sw"].info(self.loggers["sw"].log_msgs["cmds_built"])
        return pipeline_obj

    def write_dx_run_cmds(self) -> None:
        """
        Write dx run commands to the dx run script, post dx run script, and decision support upload
        script for the runfolder. Remove any None values
        from the command list
            :param pipeline_obj (object):   Object with the workflow_cmds, dx_postprocessing_cmds,
                                            decision_support_upload_cmds and sql_queries as attributes
            :return None:
        """
        base_variables = [
            SWConfig.SDK_SOURCE,
            f"AUTH={get_credential(SWConfig.CREDENTIALS['dnanexus_authtoken'])}",
            f"PROJECT_ID={self.nexus_identifiers['proj_id']}",
            f"PROJECT_NAME={self.nexus_identifiers['proj_name']}",
            f"RUNFOLDER_NAME={self.rf_obj.runfolder_name}",
            SWConfig.EMPTY_DEPENDS,
        ]
        if self.pipeline_obj.workflow_cmds:  # Write dx run commands
            self.pipeline_obj.workflow_cmds[:0] = base_variables
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["writing_cmds"],
                self.rf_obj.runfolder_dx_run_script,
            )
            write_lines(  # Write commands to dx run script
                self.rf_obj.runfolder_dx_run_script,
                "w",
                list(filter(None, self.pipeline_obj.workflow_cmds)),
            )
        if self.pipeline_obj.dx_postprocessing_cmds:  # Write postprocessing commands
            self.pipeline_obj.dx_postprocessing_cmds[:0] = base_variables
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["writing_cmds"],
                self.rf_obj.runfolder_dx_run_script,
            )
            write_lines(
                self.rf_obj.post_run_dx_run_script,
                "w",
                list(filter(None, self.pipeline_obj.dx_postprocessing_cmds)),
            )
        if self.pipeline_obj.decision_support_upload_cmds:
            self.pipeline_obj.decision_support_upload_cmds[:0] = base_variables
            write_lines(
                self.rf_obj.decision_support_upload_script,
                "w",
                list(filter(None, self.pipeline_obj.decision_support_upload_cmds)),
            )

    def pre_pipeline_upload(self) -> None:
        """
        Uploads the files in the pre_pipeline_upload_dict for the runfolder.
        Calls the upload_rest_of_runfolder function if the runfolder is tso500
            :return None:
        """
        for filetype in self.pre_pipeline_upload_dict.keys():
            self.upload_to_dnanexus(filetype, self.pre_pipeline_upload_dict)
        if self.rf_samples_obj.pipeline == "tso500":
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["tso_backup"],
            )
            self.upload_rest_of_runfolder()

    def upload_to_dnanexus(self, filetype: str, file_upload_dict: dict) -> None:
        """
        Passes the command and file list in file_upload_dict to upload_runfolder.upload_files()
        which writes log messages to the backup runfolder log file
            :param filetype (str):          Name of the file upload type
            :param file_upload_dict (dict): Dictionary of files for upload
            :return None:
        """
        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["uploading_files"], filetype
        )
        result = self.upload_runfolder.upload_files(
            file_upload_dict[filetype]["cmd"],
            file_upload_dict[filetype]["files_list"],
        )
        if result == "success":
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["upload_success"], filetype
            )
        if result == "fail":
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["upload_fail"],
                filetype,
                self.rf_obj.upload_runfolder_logfile,
            )
        elif result is list:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["nonexistent_files"], result
            )

    def upload_rest_of_runfolder(self) -> None:
        """
        Backs up the rest of the runfolder. Specifies which files to ignore (excludes BCL files for all Illumina
        runs except tso500 runs for which they are needed for demultiplexing on DNAnexus & Bases zip files for AVITI Runs).
        Calls upload_runfolder.upload_rest_of_runfolder(ignore), passing a run-dependent ignore string, and
        then this handles the runfolder upload. upload_runfolder writes log messages to the upload
        runfolder log file. If unsuccessful, exit script
            :return None:
        """
        # Build upload_runfolder.py commands, ignoring BCL files for Illumina runs and Bases zip files, 
        # Alignement, Filter and Location files for AVITI runs 
        if self.rf_samples_obj.pipeline in ["tso500"]:
            ignore = ""  # Upload BCL files for tso500 and dev runs
        elif self.rf_samples_obj.sequencer_type == SWConfig.AVITI_ID:
            ignore = "/BaseCalls,/Alignment,/Filter,/Location"
        else:
            ignore = "/L00"
        try:
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["uploading_rf"],
                ignore,
                self.rf_obj.upload_runfolder_logfile,
            )
            self.upload_runfolder.upload_rest_of_runfolder(ignore)
        except Exception as exception:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["upload_rf_error"],
                exception,
                self.rf_obj.sw_runfolder_logfile,
                self.rf_obj.upload_runfolder_logfile,
            )
            sys.exit(1)

    def run_decision_support_commands(self) -> None:
        """
        Execute the decision_support bash script
            :return None:
        """
        decision_support_run_cmd = f"bash {self.rf_obj.decision_support_upload_script}"

        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["running_decision_cmds"],
        )
        out, err, returncode = execute_subprocess_command(
            decision_support_run_cmd, self.loggers["sw"], "exit_on_fail"
        )
        if returncode != 0:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["decision_run_err"],
                decision_support_run_cmd,
                out,
                err,
            )
        else:
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["decision_run_success"],
                self.rf_obj.runfolder_name,
            )    
    def run_dx_run_commands(self) -> None:
        """
        Execute the dx run bash script
            :return None:
        """
        dx_run_cmd = f"bash {self.rf_obj.runfolder_dx_run_script}"

        self.loggers["sw"].info(
            self.loggers["sw"].log_msgs["running_cmds"],
        )
        out, err, returncode = execute_subprocess_command(
            dx_run_cmd, self.loggers["sw"], "exit_on_fail"
        )
        if returncode != 0:
            self.loggers["sw"].error(
                self.loggers["sw"].log_msgs["dx_run_err"],
                dx_run_cmd,
                out,
                err,
            )
        else:
            self.loggers["sw"].info(
                self.loggers["sw"].log_msgs["dx_run_success"],
                self.rf_obj.runfolder_name,
            )

    def post_pipeline_upload(self) -> None:
        """
        Uploads the rest of the runfolder if not a tso run
            :return None:
        """
        if self.rf_samples_obj.pipeline != "tso500":
            self.upload_rest_of_runfolder()

        logfiles_upload_dict = {
            "logfiles": {
                "cmd": self.upload_cmds["logfiles"],
                "files_list": self.rf_obj.logfiles_to_upload,
            },
        }
        for filetype in logfiles_upload_dict.keys():  # Upload logfiles for all runtypes
            self.upload_to_dnanexus(filetype, logfiles_upload_dict)

    def run_msk_commands(self):
        """Execute MSK pipeline commands directly without any DNAnexus interaction"""
        self.loggers["sw"].info("Executing MSK pipeline commands")
        
        # Set environment variables
        env = os.environ.copy()
        env['run_folder_name'] = self.rf_obj.runfolder_name
        
        # Try to get job name from RunParameters.xml, but continue without it if not found
        xml_path = os.path.join(self.rf_obj.runfolderpath, "RunParameters.xml")
        if os.path.exists(xml_path):
            try:
                xml_cmd = f"cat {xml_path} | grep -oP '(?<=ExperimentName>).*?(?=</ExperimentName)'"
                job_name = subprocess.check_output(xml_cmd, shell=True, text=True).strip()
                env['job_name'] = job_name
                self.loggers["sw"].info(f"Found job name: {job_name}")
            except subprocess.CalledProcessError as e:
                self.loggers["sw"].warning("Could not extract job name from RunParameters.xml, continuing without it")
                env['job_name'] = self.rf_obj.runfolder_name
        else:
            self.loggers["sw"].warning(f"RunParameters.xml not found at {xml_path}, continuing without job name")
            env['job_name'] = self.rf_obj.runfolder_name
        
        try:
            # Format the command with the actual runfolder path instead of using env var
            base_cmd = DemultiplexConfig.MSK_CMD
            msk_cmd = base_cmd.replace("${run_folder_name}", self.rf_obj.runfolder_name)
            
            # Create nohup command and output file path using job_name
            nohup_out = os.path.join(self.rf_obj.runfolderpath, f"{env['job_name']}_CLI.nohup.out")
            nohup_cmd = f"cd {self.rf_obj.runfolderpath} && nohup {msk_cmd} > {nohup_out} 2>&1 &"
            
            # Execute the nohup command
            result = subprocess.run(
                nohup_cmd,
                shell=True,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            self.loggers["sw"].info(
                "MSK command started in background. Output will be written to: %s",
                nohup_out
            )
            
        except subprocess.CalledProcessError as e:
            self.loggers["sw"].error(
                "Failed to start MSK command: %s\nError: %s",
                nohup_cmd,
                e.stderr
            )
            raise RuntimeError(f"MSK pipeline failed to start: {e.stderr}") from e

class DevPipeline:
    """
    Collate DNAnexus commands for development runs. This runtype has no decision
    support upload or postprocessing commands, or SQL queries
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):
        """
        Constructor for the DevPipeline class
        """
        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.sql_queries = False
        self.decision_support_upload_cmds, self.dx_postprocessing_cmds = False, False
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.workflow_cmds.append(sample_cmds_obj.create_fastqc_cmd())
            self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

        # Return downstream app commands
        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())


class ArcherDxPipeline:
    """
    Collate DNAnexus commands for ArcherDX runs. This runtype has no decision
    support upload or postprocessing commands
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):

        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.sql_queries = []
        self.dx_postprocessing_cmds = False
        self.decision_support_upload_cmds = []
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.workflow_cmds.append(sample_cmds_obj.create_fastqc_cmd())
            self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

            self.sql_queries.append(
                sample_cmds_obj.return_oncology_query()
            )  # Get SQL queries
        # Return the decision support command 
        ADX_runfolder = f"run_folder_name={self.rf_obj.runfolder_name}"
        ADX_jobID = f"job_name=$(cat {self.rf_obj.runfolderpath}/RunParameters.xml | grep -oP '(?<=ExperimentName>).*?(?=</ExperimentName)')"
        docker = DemultiplexConfig.ADX_CMD
        docker_api_cmd = [ADX_runfolder, ADX_jobID, docker]
        for api_cmd in docker_api_cmd:
            self.decision_support_upload_cmds.append(api_cmd)

        # Return downstream app commands
        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())

class MskPipeline:
    """
    Collate DNAnexus commands for MSK runs. Minimal implementation that only runs
    the MSK command and generates SQL queries for sample tracking.
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):
        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.sql_queries = []
        self.dx_postprocessing_cmds = False
        self.decision_support_upload_cmds = []
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        # Generate SQL queries for each sample
        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.sql_queries.append(
                sample_cmds_obj.return_oncology_query()
            )  # Get SQL queries

        # MSK command setup
        MSK_runfolder = f"run_folder_name={self.rf_obj.runfolder_name}"
        MSK_jobID = f"job_name=$(cat {self.rf_obj.runfolderpath}/RunParameters.xml | grep -oP '(?<=ExperimentName>).*?(?=</ExperimentName)')"
        docker = DemultiplexConfig.MSK_CMD
        docker_api_cmd = [MSK_runfolder, MSK_jobID, docker]
        for api_cmd in docker_api_cmd:
            self.decision_support_upload_cmds.append(api_cmd)

class SnpPipeline:  # TODO eventually remove this and associated pipeline-specific functions
    """
    Collate DNAnexus commands for SNP runs. This run type has no decision
    support upload or post processing commands

    Attributes
        workflow_cmd (str): Dx run command for the sample workflow
        query (str):        Sample-level SQL query
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):

        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.sql_queries = []
        self.decision_support_upload_cmds, self.dx_postprocessing_cmds = False, False
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.workflow_cmds.append(sample_cmds_obj.create_snp_cmd())
            self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

            self.sql_queries.append(
                sample_cmds_obj.return_rd_query()
            )  # Get SQL queries
        # Return downstream app commands
        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())


class OncoDeepPipeline:
    """
    Collate DNAnexus commands for OncoDEEP runs. This runtype has no post processing commands
    or decision support upload script, as the decision support commands are run automatically
    therefore reside in the dx run script
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):
        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.sql_queries = []
        self.decision_support_upload_cmds, self.dx_postprocessing_cmds = False, False
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.workflow_cmds.append(sample_cmds_obj.create_fastqc_cmd())
            self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

            self.sql_queries.append(sample_cmds_obj.return_oncology_query())
            for read in ["R1", "R2"]:  # Generate sample oncodeep upload commands
                self.workflow_cmds.append(
                    sample_cmds_obj.build_oncodeep_upload_cmd(
                        f"{sample_name}-{read}",
                        self.rf_samples_obj.nexus_runfolder_suffix,
                        self.rf_samples_obj.samples_dict[sample_name]["fastqs"][read][
                            "nexus_path"
                        ],
                    )
                )
        # Generate command for MasterFile upload
        self.workflow_cmds.append(
            sample_cmds_obj.build_oncodeep_upload_cmd(
                self.rf_obj.masterfile_name,
                self.rf_samples_obj.nexus_runfolder_suffix,
                f"{self.rf_obj.DNANEXUS_PROJ_ID}:{self.rf_obj.masterfile_name}",
            )
        )
        # Return downstream app commands
        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())


class TsoPipeline:
    """
    Collate commands for TSO workflow. This runtype has postprocessing commands and
    decision support upload commands, and SQL queries
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):
        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.dx_postprocessing_cmds = []
        self.decision_support_upload_cmds = []
        self.sql_queries = []
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        # Create tso app commands
        for tso_ss in self.rf_obj.tso_ss_list:
            # Exclude base SampleSheet as we only want to use split SampleSheets
            if tso_ss != self.rf_obj.samplesheet_name:
                self.workflow_cmds.append(self.rf_cmds_obj.create_tso500_cmd(tso_ss))

        # Create per-sample commands
        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            # Create fastqc commands and dependency
            self.dx_postprocessing_cmds.append(sample_cmds_obj.create_fastqc_cmd())
            self.dx_postprocessing_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])
            # Create coverage commands and dependency
            self.dx_postprocessing_cmds.append(
                sample_cmds_obj.create_sambamba_cmd(
                    sample_name, self.rf_samples_obj.samples_dict[sample_name]["pannum"]
                )
            )
            # Coverage is in depends list because per-gene coverage is included in MultiQC report
            # Exclude coverage jobs for negative controls from the depends list as the NTC coverage
            # calculation can often fail. We want the coverage report for the NTC sample to help
            # assess contamination. Only add to depends_list if job ID from previous command is not empty.
            if not self.rf_samples_obj.samples_dict[sample_name]["neg_control"]:
                self.dx_postprocessing_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

            if self.rf_samples_obj.samples_dict[sample_name]["pos_control"]:
                self.dx_postprocessing_cmds.append(
                    sample_cmds_obj.create_sompy_cmd(sample_name)
                )
                # Only add to depends_list if job ID from previous command
                # is not empty
                self.dx_postprocessing_cmds.append(SWConfig.UPLOAD_ARGS["depends_list"])

            if (
                not self.rf_samples_obj.samples_dict[sample_name]["neg_control"]
                or self.rf_samples_obj.samples_dict[sample_name]["neg_control"]
            ):
                self.decision_support_upload_cmds.append(
                    sample_cmds_obj.build_qiagen_upload_cmd()
                )  # Build decision support upload commands

            self.sql_queries.append(
                sample_cmds_obj.return_oncology_query()
            )  # Build SQL query

        self.dx_postprocessing_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.dx_postprocessing_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())


class WesPipeline:  # TODO eventually remove this and associated pipeline-specific functions
    """
    Collate commands for WES workflow. This runtype has no postprocesing commands
    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):

        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.dx_postprocessing_cmds = False
        self.decision_support_upload_cmds = []
        self.sql_queries = []
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            self.workflow_cmds.extend(
                [sample_cmds_obj.create_wes_cmd(), SWConfig.UPLOAD_ARGS["depends_list"]]
            )

            self.decision_support_upload_cmds.append(
                sample_cmds_obj.return_congenica_cmd()
            )
            self.sql_queries.append(
                sample_cmds_obj.return_rd_query()
            )  # Get SQL queries

        self.workflow_cmds.extend(
            [self.rf_cmds_obj.create_peddy_cmd(), SWConfig.UPLOAD_ARGS["depends_list"]]
        )

        # Return downstream app commands
        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )
        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())

        wes_dnanumbers = [
            self.rf_samples_obj.samples_dict[k]["identifiers"]["primary"]
            for k in self.rf_samples_obj.samples_dict.keys()
        ]
        self.sql_queries = self.rf_cmds_obj.return_wes_query(wes_dnanumbers)


class CustomPanelsPipelines:
    """
    Collate commands for Custom Panels workflow. This runtype has no postprocesing commands

    """

    def __init__(self, rf_obj: object, rf_samples: object, logger: logging.Logger):
        """ """
        self.rf_obj = rf_obj
        self.rf_samples_obj = rf_samples
        self.logger = logger
        self.workflow_cmds = []
        self.dx_postprocessing_cmds = False
        self.decision_support_upload_cmds = []
        self.sql_queries = []
        self.rf_cmds_obj = BuildRunfolderDxCommands(self.rf_obj, self.logger)

        for sample_name in self.rf_samples_obj.samples_dict.keys():
            sample_cmds_obj = BuildSampleDxCommands(
                self.rf_obj.runfolder_name,
                self.rf_samples_obj.samples_dict[sample_name],
                self.logger,
            )
            # Add to gatk and sentieon depends list because RPKM / ExomeDepth must depend only upon the
            # sample workflows completing successfully, whilst other downstream
            # apps depend on all prior jobs completing succesfully

            pipeline_type = sample_cmds_obj.sample_dict["panel_settings"]["pipeline"]
            if pipeline_type == "gatk_pipe":
                cmd = sample_cmds_obj.create_gatk_pipe_cmd()
            elif pipeline_type == "seglh_pipe":
                cmd = sample_cmds_obj.create_seglh_pipe_cmd()
            else:
                raise ValueError(f"Unsupported pipeline type: {pipeline_type}")
            
            self.workflow_cmds.extend(
                [
                    cmd,
                    SWConfig.UPLOAD_ARGS["depends_list"],
                    SWConfig.UPLOAD_ARGS["depends_list_pipeline"],
                ]
            )
            
            self.sql_queries.append(sample_cmds_obj.return_rd_query())
            self.decision_support_upload_cmds.append(
                sample_cmds_obj.return_congenica_cmd()
            )

        # CNV calling steps are a dependency of MultiQC
        cmd_list = []
        for core_panel in ["vcp1", "CP2"]:
            if core_panel in (
                [
                    self.rf_samples_obj.samples_dict[k]["panel_settings"]["panel_name"]
                    for k, v in self.rf_samples_obj.samples_dict.items()
                ]
            ):
                core_panel_pannos = [
                    self.rf_samples_obj.samples_dict[k]["pannum"]
                    for k, v in self.rf_samples_obj.samples_dict.items()
                    if self.rf_samples_obj.samples_dict[k]["panel_settings"][
                        "panel_name"
                    ]
                    == core_panel
                ]
                # Make sure there are enough samples for RPKM and ExomeDepth
                if len(core_panel_pannos) >= 3:
                    rpkm_cmd = self.rf_cmds_obj.create_rpkm_cmd(core_panel)
                    if rpkm_cmd:
                        self.workflow_cmds.extend(
                        [
                            rpkm_cmd,
                            SWConfig.UPLOAD_ARGS["depends_list_cnvcalling"],
                        ]
                    )
                    self.workflow_cmds.extend(
                        [
                            self.rf_cmds_obj.create_ed_readcount_cmd(core_panel),
                            SWConfig.UPLOAD_ARGS["depends_list_edreadcount"],
                        ]
                    )
                    for panno in set(core_panel_pannos):
                        if (
                            SWConfig.CAPTURE_PANEL_DICT[core_panel][
                                "ed_readcount_bedfile"
                            ]
                            and SWConfig.PANEL_DICT[panno]["ed_cnvcalling_bedfile"]
                        ):
                            self.workflow_cmds.extend(
                                [
                                    self.rf_cmds_obj.create_ed_cnvcalling_cmd(panno),
                                    SWConfig.UPLOAD_ARGS["depends_list_cnvcalling"],
                                ]
                            )
                else:
                    self.logger.info(
                        self.logger.log_msgs["insufficient_samples_for_cnv"],
                        core_panel,
                    )
        self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list_pipeline_recombined"])

        self.workflow_cmds.extend(
            self.rf_cmds_obj.return_multiqc_cmds(self.rf_samples_obj.pipeline)
        )

        # We want duty_csv to also depend on the cnv calling jobs for PIPE workflows
        self.workflow_cmds.append(SWConfig.UPLOAD_ARGS["depends_list_cnv_recombined"])

        self.workflow_cmds.append(self.rf_cmds_obj.create_duty_csv_cmd())
