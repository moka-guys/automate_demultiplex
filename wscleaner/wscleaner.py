"""wscleaner.py

Workstation Cleaner (wscleaner) automates the deletion of local directories that have been uploaded
to the DNAnexus cloud storage service.

Contains the following classes:

- RunFolderManager
    Contains methods for finding, checking and deleting runfolders in a root directory
- DxProjectRunFolder
    A DNAnexus project
- CheckRunfolder
    Class for determining whether a runfolder should be deleted, and deleting it
"""

import re
import logging
import shutil
import datetime
from typing import Optional
import os
import dxpy
from typing import List
from config.ad_config import RunfolderCleanupConfig
from ad_logger.ad_logger import AdLogger
from toolbox.toolbox import (
    return_scriptlog_config,
    get_credential,
    get_runfolder_path,
    RunfolderObject,
    RunfolderSamples,
    script_start_logmsg,
    script_end_logmsg
)
from ad_logger.ad_logger import set_root_logger

# TODO this script can be further simplified in future as it shares functionality with other
# modules in this repo - functions can be reused

root_logger = set_root_logger()

# DEBUG message are ommitted from the console output by setting the stream handler level
# to INFO, making console outputs easier to read. DEBUG messages are still written to
# the application logfile and system log.
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO)

ad_logger_obj = AdLogger(
    __name__,
    "wscleaner",
    return_scriptlog_config()["wscleaner"],
)
script_logger = ad_logger_obj.get_logger()


# Set DNAnexus authentication token
dxpy.set_security_context(
    {
        "auth_token_type": "Bearer",
        "auth_token": get_credential(
            RunfolderCleanupConfig.CREDENTIALS["dnanexus_authtoken"]
        ),
    }
)


class RunFolderManager:
    """
    Contains methods for finding, checking and deleting runfolders in a root directory

    Attributes
        root (pathlib.Path):    A path object to the root directory
        deleted (List):         A list of deleted runfolders populated by calls to self.delete()

    Methods
        cleanup_runfolders()
            Calls methods for cleaning up runfolders
        get_runfolders_to_process()
            Identify runfolders to consider for deletion
        get_dirs_created_after(path, date_str)
            Get directories created after a specified date.
        delete()
            Delete the local runfolder from the root directory and append name to self.deleted
    """

    def __init__(self, dry_run=False, min_age=10, logfile_count=6):
        """
        Constructor for the RunFolderManager class
            :param runfolders_dir (str):    Runfolders directory, with default defined in the config
            :param dry_run (bool):          True if script should not delete runfolders, False if it should
            :param min_age Optional[int]:   Minimum age in days of runfolders that should be assessed by
                                            the script
            :param logfile_count (int):     Expected number of logfiles uploaded to the DNAnexus project.
                                            Default is 6
        """
        self.runfolders_dir = RunfolderCleanupConfig.RUNFOLDERS
        self.dry_run = dry_run
        self.min_age = min_age
        self.logfile_count = logfile_count
        self.samplesheets_dir = os.path.join(self.runfolders_dir, "samplesheets")

    def cleanup_runfolders(self) -> None:
        """
        Calls methods for cleaning up runfolders
            :return None:
        """
        script_start_logmsg(script_logger, __file__)

        deleted_runfolders = []  # Deleted runfolders appended here by self.deleted

        runfolder_objects = self.get_runfolders_to_process()
        script_logger.info(
            f"Found local runfolders to consider deleting: {[rf_obj.runfolder_name for rf_obj, rf_samples_obj in runfolder_objects]}"
        )
        for rf_obj, rf_samples_obj in runfolder_objects:
            cr_obj = CheckRunfolder(
                rf_obj.runfolder_name,
                rf_obj.upload_runfolder_logfile,
                rf_samples_obj.fastqs_list,
                self.logfile_count,
            )
            if cr_obj.to_delete(rf_samples_obj.pipeline):
                self.delete(rf_obj.runfolder_name, rf_obj.runfolderpath)
                deleted_runfolders.append(rf_obj.runfolder_name)
        # Record runfolders removed by this iteration
        script_logger.info(f"Runfolders deleted in this instance: {deleted_runfolders}")
        script_end_logmsg(script_logger, __file__)
        
        return deleted_runfolders

    def get_runfolders_to_process(self) -> list:
        """
        Identify runfolders to consider for deletion
            :return runfolder_objects (list):   List of tuples (RunfolderObject,
                                                RunfolderSamples)
        """
        runfolder_objects = []
        folders = self.get_dirs_created_after(self.runfolders_dir, '2024-06-12')  # V45.0.0 of the automated scripts (logfile number changed to 6)
        for runfolder_path in folders:
            folder_name = runfolder_path.split("/")[-1]
            if get_runfolder_path(folder_name) and re.compile(
                RunfolderCleanupConfig.RUNFOLDER_PATTERN
            ).match(folder_name):
                script_logger.debug(
                    f"Initiating RunfolderObject instance for {folder_name}"
                )
                rf_obj = RunfolderObject(folder_name, RunfolderCleanupConfig.TIMESTAMP)
                rf_age = rf_obj.age()
                if os.path.exists(os.path.join(self.samplesheets_dir, f"{folder_name}_SampleSheet.csv")):
                    rf_samples_obj = RunfolderSamples(rf_obj, script_logger)
                    if rf_samples_obj:
                        if os.path.exists(rf_obj.rtacompletefile_path):
                            if (rf_age >= self.min_age):
                                # Catch TSO500 runfolders here (do not contain fastqs)
                                if rf_samples_obj.pipeline == "dev":
                                    script_logger.info(
                                        f"{rf_obj.runfolder_name} is a DEV runfolder therefore should not be deleted"
                                    )
                                else:
                                    if rf_samples_obj.pipeline == "tso500":
                                        script_logger.info(
                                            f"{rf_obj.runfolder_name} is a TSO500 runfolder and is >= {self.min_age} days old"
                                        )
                                        runfolder_objects.append(tuple([rf_obj, rf_samples_obj]))  # Append to list to process
                                    else:
                                        # Criteria for runfolder: Older than or equal to min_age and contains fastq.gz files
                                        if rf_samples_obj.fastqs_list:
                                            if len(
                                                rf_samples_obj.fastqs_list
                                            ) > 0:
                                                script_logger.info(
                                                    f"{rf_obj.runfolder_name} contains 1 or more fastq and is >= {self.min_age} days old"
                                                )
                                                runfolder_objects.append(tuple([rf_obj, rf_samples_obj]))  # Append to list to process
                                            else:
                                                script_logger.info(
                                                    f"{rf_obj.runfolder_name} has 0 fastqs and is not a TSO runfolder"
                                                )
                                        else:
                                            script_logger.info(
                                                f"{rf_obj.runfolder_name}: Expected fastqs could not be parsed from the SampleSheet for the run"
                                            )
                            else:
                                script_logger.info(
                                    f"{rf_obj.runfolder_name} is < {self.min_age} days old"
                                )
                        else:
                            script_logger.info(
                                f"{rf_obj.runfolder_name} is not a runfolder, or sequencing has not yet finished"
                            )
                else:
                    script_logger.info(
                        f"Corresponding SampleSheet for {rf_obj.runfolder_name} could not be located. This is required for analysing for deletion"
                    )
        to_assess = [rf_obj.runfolder_name for runfolder_object in runfolder_objects]
        all_folders = [folder.split("/")[-1].strip() for folder in folders]
        to_skip = [folder for folder in all_folders if folder not in to_assess]
        script_logger.info(
            "Skipping over folders: " + ", ".join(to_skip)
        )
        return runfolder_objects

    def get_dirs_created_after(self, path: str, date_str: str) -> List[str]:
        """
        Get directories created after a specified date.
            :param path (str):      The directory path to check.
            :param date_str (str):  The date string to compare against in 'YYYY-MM-DD' format
            :return List[str]:      List of directory paths that were created after the specified date
        """
        specified_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        dirs_created_after = []

        for dirname in os.listdir(path):
            dir_full_path = os.path.join(path, dirname)
            if os.path.isdir(dir_full_path):
                if os.name == 'nt':
                    creation_time = os.path.getctime(dir_full_path)
                else:
                    stat_info = os.stat(dir_full_path)
                    creation_time = getattr(stat_info, 'st_birthtime', stat_info.st_mtime)

                if datetime.datetime.fromtimestamp(creation_time) > specified_date:
                    dirs_created_after.append(dir_full_path)

        return dirs_created_after

    def delete(self, runfolder_name: str, runfolder_path: str) -> Optional[bool]:
        """
        Delete the local runfolder from the root directory
            :param runfolder_name (str):        Runfolder name
            :param runfolder_path (str):        Path of runfolder
            :return Optional[bool]:             Return True if runfolder deleted,
                                                else None
        """
        if self.dry_run:
            script_logger.info(f"DRY RUN DELETE {runfolder_name}")
        else:
            shutil.rmtree(runfolder_path)
            script_logger.info(f"{runfolder_name} DELETED.")
            return True


class CheckRunfolder:
    """
    Class for determining whether a runfolder should be deleted, and deleting it

    Attributes
        runfolder_name (str):                Runfolder name
        upload_runfolder_logfile (str):      Path to upload runfolder logfile
        fastqs_list (list):                  List of fastq files in the local runfolder
        dx_project (DxProjectRunfolder):     Instance of DxProjectRunfolder

    Methods
        check_fastqs()
            Returns true if a runfolder's fastq.gz files match those in it's DNAnexus project
        check_logfiles()
            Returns true if a runfolder's DNAnexus project contains 6 logfiles in the
            expected location
        upload_log_exists()
            Returns true if a runfolder's upload log exists
        check_upload_log()
            Returns true if a runfolder's upload log contains no upload errors
        to_delete(pipeline)
            Determine whether a runfolder is safe for deletion
    """

    def __init__(
        self,
        runfolder_name: str,
        upload_runfolder_logfile: str,
        fastqs_list: list,
        logfile_count: int,
    ):
        """
        Constructor for the CheckRunfolder object
            :param runfolder_name (str):                Runfolder name
            :param upload_runfolder_logfile (str):      Path to upload runfolder logfile
            :param fastqs_list (list):                  List of fastq files in the local runfolder
            :param logfile_count (int):                 Number of logfiles expected in the DNAnexus project
        """
        self.runfolder_name = runfolder_name
        script_logger.info(f"Processing {self.runfolder_name}")
        self.upload_runfolder_logfile = upload_runfolder_logfile
        self.fastqs_list = fastqs_list
        self.logfile_count = logfile_count
        self.dx_project = DxProjectRunFolder(self.runfolder_name)

    def check_fastqs(self) -> bool:
        """
        Returns true if a runfolder's fastq.gz files match those in it's DNAnexus project.
        Ensures all fastqs were uploaded.
            :return fastq_bool (bool):                  True if all fastqs present in DNAnexus project,
                                                        False if any fastqs are missing
        """
        if self.dx_project:
            dx_fastqs = self.dx_project.find_fastqs()
            fastq_bool = True
            for fastq in self.fastqs_list:  # Local fastqs
                if fastq.split("/")[-1] not in dx_fastqs:
                    script_logger.debug(f"Fastq missing from DNAnexus project: {fastq}")
                    fastq_bool = False
            script_logger.debug(f"{self.runfolder_name} FASTQ BOOL: {fastq_bool}")

            if not fastq_bool:  # Fastqs not all present in DNAnexus
                script_logger.warning(f"{self.runfolder_name} - FASTQ MISMATCH")
            return fastq_bool

    def check_logfiles(self) -> bool:
        """
        Returns true if a runfolder's DNAnexus project contains logfile_count
        logfiles in the expected location
            :return
        """
        if self.dx_project:
            dx_logfiles = self.dx_project.count_logfiles()
            logfile_bool = dx_logfiles == self.logfile_count
            script_logger.debug(f"{self.runfolder_name} LOGFILE BOOL: {logfile_bool}")
            if not logfile_bool:
                script_logger.warning(f"{self.runfolder_name} - LOGFILE MISMATCH")
            return logfile_bool

    def upload_log_exists(self) -> Optional[bool]:
        """
        Returns true if a runfolder's upload log file exists
            :return Optional[bool]: Return True if runfolder upload log file
                                    exists, else None
        """
        if os.path.exists(self.upload_runfolder_logfile):
            return True
        else:
            script_logger.warning(f"{self.runfolder_name} - UPLOAD LOG MISSING")
            script_logger.debug(f"{self.runfolder_name} upload log file does not exist")

    def check_upload_log(self):
        """
        Returns true if a runfolder's upload log file contains no ERROR logs
            :return Optional[bool]: Return True if upload log file exists and contains
                                    no errors, else None
        """
        upload_log_bool = False
        if os.path.exists(self.upload_runfolder_logfile):
            with open(self.upload_runfolder_logfile, "r") as f:
                log_contents = f.readlines()
                print
            if any("- ERROR -" in string for string in log_contents):
                script_logger.debug(f"{self.runfolder_name} upload log contains errors")
                script_logger.warning(
                    f"{self.runfolder_name} - UPLOAD LOG CONTAINS ERRORS"
                )
                upload_log_bool = False
            else:
                upload_log_bool = True
        script_logger.debug(f"{self.runfolder_name} UPLOAD LOG BOOL: {upload_log_bool}")
        return upload_log_bool

    def to_delete(self, pipeline: str) -> Optional[bool]:
        """
        Determine whether a runfolder is safe for deletion
            :param pipeline (str):  Name of pipeline
            :return Optional[bool]: Return True if runfolder deleted / marked for deletion, else None
        """
        # Delete runfolder if it meets the backup criteria
        # dx_project is evaluated first as following criteria checks depend on it
        tso_run = False

        if pipeline == RunfolderCleanupConfig.CAPTURE_PANEL_DICT["tso500"]["pipeline"]:
            tso_run = True

        if self.dx_project:
            upload_log_exists = self.upload_log_exists()
            clean_upload_log = self.check_upload_log()
            logfiles_uploaded = self.check_logfiles()

            if tso_run:
                if all(
                    [
                        logfiles_uploaded,
                        upload_log_exists,
                        clean_upload_log,
                    ]
                ):
                    return True
            else:
                fastqs_uploaded = self.check_fastqs()
                if all(
                    [
                        fastqs_uploaded,
                        logfiles_uploaded,
                        upload_log_exists,
                        clean_upload_log,
                    ]
                ):
                    return True


class DxProjectRunFolder:
    """
    A DNAnexus runfolder object

    Attributes
        runfolder (str):    Runfolder name
        id (str):           Project ID of the matching runfolder project in DNANexus
        logfile_dir (str):  Directory in DNAnexus containing the logfiles

    Methods
        dx_find_one_project()
            Find a single DNAnexus project from the input runfolder name
        find_fastqs()
            Returns a list of files in the identified DNAnexus project with the fastq.gz extension
        count_logfiles()
            Count logfiles in the DNAnexus project, in the /$RUNFOLDER_NAME/automated_scripts_logfiles
            subdirectory
    """

    def __init__(self, runfolder_name: str):
        """
        Constructor for the DxProjectRunFolder class
            :param runfolder_name (str):    Name of runfolder
        """
        self.runfolder_name = runfolder_name
        self.dnanexus_id = self.dx_find_one_project()
        self.logfile_dir = str(
            os.path.join("/", self.runfolder_name, "automated_scripts_logfiles")
        )

    def dx_find_one_project(self) -> Optional[str]:
        """
        Find a single DNAnexus project from the input runfolder name
            :return Optional[str]:  Return DNAnexus project ID string, if identfied, else return None
        """
        try:
            # Search for the project matching self.runfolder.
            # name_mode='regexp' - look for any occurence of the runfolder name in the project name.
            # Setting more_ok/zero_ok to False ensures only one project is succesfully returned.
            project = dxpy.find_one_project(
                name=self.runfolder_name,
                name_mode="regexp",
                more_ok=False,
                zero_ok=False,
            )
            script_logger.debug(
                f'{self.runfolder_name} DNAnexus project: {project["id"]}'
            )
            return project["id"]
        except dxpy.exceptions.DXSearchError as error:
            # Catch exception and raise none
            script_logger.warning(
                f"DX PROJECT MISMATCH - 0 or >1 DNAnexus projects found for {self.runfolder_name}: {error}"
            )
            return None

    def find_fastqs(self):
        """
        Return a list of files in the DNAnexus project with the fastq.gz extension
            :return fastq_filenames (list): List of files in the DNAnexus project
                                            with the fastq.gz extension
        """
        # Search dnanexus for files with the fastq.gz extension.
        # name_mode='regexp' tells dxpy to look for any occurence of 'fastq.gz' in the filename
        search_response = dxpy.find_data_objects(
            project=self.dnanexus_id,
            classname="file",
            name="fastq.gz",
            name_mode="regexp",
        )
        file_ids = [result["id"] for result in search_response]
        # Gather a list of uploaded fastq files with the state 'closed', indicating a completed upload.
        fastq_filenames_unsorted = []
        for dx_file in file_ids:
            file_description = dxpy.describe(dx_file)
            if file_description["state"] == "closed":
                fastq_filenames_unsorted.append(file_description["name"])
        # Sort fastq filenames for cleaner logfile output
        fastq_filenames = sorted(fastq_filenames_unsorted)
        script_logger.debug(
            f'{self.dnanexus_id} contains {len(fastq_filenames)} "closed" fastq files: {fastq_filenames}'
        )
        return fastq_filenames

    def count_logfiles(self) -> int:
        """
        Count logfiles in the DNAnexus project, in the /$RUNFOLDER_NAME/automated_scripts_logfiles
        subdirectory
            :return (int):  Count of automated scripts logfiles identified in the DNAnexus project
        """
        logfile_list = dxpy.find_data_objects(
            project=self.dnanexus_id, folder=self.logfile_dir, classname="file"
        )
        return len(list(logfile_list))

    def __bool__(self) -> bool:
        """
        Allows boolean expressions on class instances
            :return (bool): Return True if a single DNAnexus project was found
        """
        if self.dnanexus_id:
            return True
        else:
            return False
