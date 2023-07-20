#!/usr/bin/python3
# coding=utf-8
"""
UACaller.py Uploads an Illumina runfolder to DNAnexus.
"""
import os
import re
import math
from config import ad_config
from toolbox import toolbox
from typing import Union, Tuple
# TODO improve log messages in this script
# TODO properly test this both on command line and within script


class UACaller:
    """
    Uploads a runfolder to DNAnexus.

    Attributes:
        rf_obj:          Runfolder object
        nexus_identifiers:      Dictionary containing dnanexus project name and id

    Methods:
        find_nexus_project()
            Search DNAnexus for the project given as an input argument. If the input is
            'None', searches for a project matching self.rf_obj.runfolder_name.
        upload_rest_of_runfolder()
            Call methods to upload the rest of the runfolder (the runfolder minus the
            fastqs and several QC files)
        check_runfolder_exists()
            Check runfolder exists
        get_file_dict(ignore)
            Get dictionary of all files and folders requiring upload, ignoring any files
            specified in the ignore string
        ignore_file(filepath, ignore)
            Determine whether a file should be ignored by parsing the ignore string and
            comparing to the filepath
        call_upload_agent(file_dict)
            Build upload commands for project. It is quicker to upload files in parallel
            so all files in a folder are added to a list and a single command issued per
            folder
        get_nexus_filepath(file_dict)
            Get the DNAnexus subdirectory name, and full DNAnexus directory path for the
            input folder. DNAnexus upload folder path is used in the upload agent's
            '--folder' argument.
        count_uploaded_files(ignore)
            Count the number of files to be uploaded and check if any that should have
            been ignored are in DNAnexus
        upload_files(upload_cmd, files_list, upload_type)
            Uploads files when provided with an upload command, files list, and upload
            type
    """
    def __init__(self, rf_obj: object, nexus_identifiers=False):
        """
        Constructor for the UACaller class
            :param rf_obj (obj):    RunfolderObject object (contains runfolder-specific
                                    attributes)
        """
        self.rf_obj = rf_obj
        self.logger = self.rf_obj.rf_loggers.backup
        if nexus_identifiers:
            self.nexus_project_name = nexus_identifiers['proj_name']
            self.nexus_project_id = nexus_identifiers['proj_id']
        else:
            self.nexus_project_name, self.nexus_project_id = self.find_nexus_project()

    def find_nexus_project(self) -> Tuple[str, str]:
        """
        Search DNAnexus for the project given as an input argument. If the input is
        'None', searches for a project matching self.rf_obj.runfolder_name.
            :return project_name (str):     Name of DNAnexus project
            :return project_id (str):       Id of DNAnexus project
        """
        self.logger.info(
            self.logger.log_msgs["finding_project"],
            self.rf_obj.runfolder_name,
        )
        try:
            # Get DNAnexus project name using runfolder name
            project_name, err, returncode = toolbox.execute_subprocess_command(
                ad_config.DX_CMDS['find_proj_name'] % (
                    self.rf_obj.runfolder_name,
                    self.rf_obj.dnanexus_apikey
                    ), self.logger
                )
            # Get project ID
            project_id, err, returncode = toolbox.execute_subprocess_command(
                ad_config.DX_CMDS['find_proj_id'] % project_name, self.nexus_project_id,
                self.logger
                )
            return project_name, project_id
        except Exception as exception:
            raise Exception(exception)

    def upload_rest_of_runfolder(self, ignore: str) -> None:
        """
        Call methods to upload the rest of the runfolder (the runfolder minus the
        fastqs and several QC files)
            :return None:
        """
        self.logger.info(
            self.logger.log_msgs["ad_version"],
            toolbox.git_tag(),
        )
        toolbox.test_upload_software(self.logger)
        self.check_runfolder_exists()
        file_dict = self.get_file_dict(ignore)
        self.call_upload_agent(file_dict)  # Call the DNAnexus upload agent
        self.count_uploaded_files(ignore)  # Run tests to count files

    def check_runfolder_exists(self) -> None:
        """
        Check runfolder exists
            :return None:
        """
        self.logger.info(
            self.logger.log_msgs["checking_runfolder"],
            self.rf_obj.runfolderpath,
        )
        if not os.path.isdir(self.rf_obj.runfolderpath):
            self.logger.error(
                self.logger.log_msgs["nonexistent_runfolder"],
                self.rf_obj.runfolderpath,
            )
            raise IOError("Invalid runfolder given as input")

    def get_file_dict(self, ignore: str) -> dict:
        """
        Get dictionary of all files and folders requiring upload, ignoring any files
        specified in the ignore string
            :return file_dict (dict):   Dictionary of files for upload
        """
        self.logger.info(
            self.logger.log_msgs["building_file_dict"],
        )
        # Create a dictionary to hold the directories as a key, and the list of
        # files as the value
        file_dict = {}
        # walk through run folder
        for root, subfolders, files in os.walk(self.rf_obj.runfolderpath):
            # for any subfolders
            for folder in subfolders:
                # build path to the folder
                folderpath = os.path.join(root, folder)
                # create a dictionary entry for this folder
                file_dict[folderpath] = []
                # create a list of filepaths for all files in the folder
                filepath_list = [
                    os.path.join(folderpath, file)
                    for file in os.listdir(folderpath)
                    if os.path.isfile(os.path.join(folderpath, file))
                ]
                # loop through this list
                for filepath in filepath_list:
                    # test filepath for ignore patterns
                    if not self.ignore_file(filepath, ignore):
                        # if ignore pattern not found add filepath to list
                        file_dict[folderpath].append(filepath)
            # repeat for the root (not just subfolders)
            # build path to the folder
            folderpath = os.path.join(root)
            # create a dictionary entry for this folder
            file_dict[folderpath] = []
            # create a list of filepaths for all files in the folder
            filepath_list = [
                os.path.join(folderpath, file)
                for file in os.listdir(folderpath)
                if os.path.isfile(os.path.join(folderpath, file))
            ]
            # Loop through this list
            for filepath in filepath_list:
                # Test filepath for ignore patterns
                if not self.ignore_file(filepath, ignore):
                    # If ignore pattern not found add filepath to list
                    file_dict[folderpath].append(filepath)

        # Report the folders and files to be uploaded
        self.logger.info(
            self.logger.log_msgs["files_for_upload"], str(file_dict.keys())
        )
        return file_dict

    def ignore_file(self, filepath: str, ignore: str) -> bool:
        """
        Determine whether a file should be ignored by parsing the ignore string and
        comparing to the filepath
            :param filepath (str):  Path of file for comparison
            :param ignore (str):    String containing files to ignore
            :return bool:           True if file should be ignored, False if not
        """
        if ignore:  # if an ignore pattern was specified
            # split this string on comma and loop through list
            for pattern in ignore.split(","):
                # Make ignore pattern and filepath upper case and search
                # filepath for the pattern
                if pattern.upper() in filepath.upper():
                    # if present return True to indicate the file should not
                    # be uploaded
                    return True
        # if no search patterns given, or pattern not found in filepath return
        # False to say file can be uploaded
        return False

    def call_upload_agent(self, file_dict: dict) -> None:
        """
        Build upload commands for project. It is quicker to upload files in parallel
        so all files in a folder are added to a list and a single command issued per
        folder
            :param file_dict (dict):    Dictionary of files for upload
            :return None:
        """
        # Call upload agent on each folder
        for path in file_dict:
            if file_dict[path]:  # if there are any files to upload
                # create the nexus path for each dir
                nexus_path, project_filepath = self.get_nexus_filepath(path)
                self.logger.info(
                    self.logger.log_msgs["call_ua"],
                    path, project_filepath
                )
                # upload agent has a max number of uploads of 1000 per command.
                # uploading multiple files at a time is quicker, but uploading too many
                # at a time has caused it to hang. count number of files in list and
                # divide by 100.0 eg 20/100.0 = 0.02. ceil rounds up to the nearest
                # integer (0.02->1). If there are 100, ceil(100/100.0)=1.0 if there are
                # 750. ceil(750/100.0)=8.0
                iterations_needed = math.ceil(len(file_dict[path]) / 100.0)
                # set the iterations count to 1
                iteration_count = 1
                # will pass a slice of the file list to the upload agent so set
                # variables for start and stop so it uploads files 0-999
                start = 0
                stop = 100
                # while we haven't finished the iterations
                while iteration_count <= iterations_needed:
                    # if it's the last iteration, set stop == length of list so not to
                    # ask for elements that aren't in the list  (if 4 items in list
                    # len(list)=4 and slice of 0:4 won't miss the last element)
                    if iteration_count == iterations_needed:
                        stop = len(file_dict[path])
                    self.logger.info(
                        self.logger.log_msgs["uploading_file_range"], start, stop,
                    )
                    # the upload agent command can take multiple files separated by a
                    # space. the full file path is required for each file
                    files_string = ""
                    # take a slice of list using from and to
                    for file in file_dict[path][start:stop]:
                        files_string = f"{files_string} '{os.path.join(path, file)}'"

                    self.logger.info(self.logger.log_msgs["building_command"])
                    # Create DNAnexus upload command
                    nexus_upload_command = ad_config.DX_CMDS["file_upload_cmd"] % (
                        self.rf_obj.dnanexus_apikey,
                        self.nexus_project_name,
                        nexus_path,
                        f'--tries 100 {files_string}'
                    )
                    # Increase the iteration_count and start and stop by 1000 for the
                    # next iteration so second iteration will do files 1000-1999
                    iteration_count += 1
                    start += 100
                    stop += 100

                    out, err, returncode = toolbox.execute_subprocess_command(
                        nexus_upload_command, self.rf_obj.rf_loggers.upload_agent
                        )
                    # Write output stream to logfile and terminal
                    self.logger.info(self.logger.log_msgs["cmd_out"], out, err)

    def get_nexus_filepath(self, folder_path) -> Tuple[str, str]:
        """
        Get the DNAnexus subdirectory name, and full DNAnexus directory path for the
        input folder. DNAnexus upload folder path is used in the upload agent's
        '--folder' argument.
            :param folder_path (str):   Path of a local folder containing files to be
                                        uploaded to DNAnexus
            :return nexus_path (str):   DNAnexus folder name e.g. runfolder/RTALogs
            :return nexus_path (str):   DNAnexus full folder path
                                        e.g. PROJECT:/runfolder/RTALogs/
        """
        if folder_path == self.rf_obj.runfolderpath:
            # Files in the root of a runfolder do not require cleaning
            clean_runfolder_path = ""
        else:
            # Remove runfolder name and parent folders from the input file path
            clean_runfolder_path = re.search(
                rf"{self.rf_obj.runfolder_name}[\/](.*)$", folder_path
            ).group(1)
        # Prepend the nexus folder path to cleaned path. the nexus folder path is the
        # project name without the first four characters (002_)
        nexus_folder = os.path.join(
            "/", self.nexus_project_name[4:], clean_runfolder_path
        )
        nexus_path = f"{self.nexus_project_name}:{nexus_folder}"
        return nexus_folder, nexus_path  # Return nexus folder name and full folder path

    def count_uploaded_files(self, ignore) -> None:
        """
        Count the number of files to be uploaded and check if any that should have been
        ignored are in DNAnexus
            :param ignore (str): String containing files to ignore
        """
        self.logger.info(self.logger.log_msgs["counting_files"])
        # count number of files to be uploaded
        # if ignore terms given need to add a grep step
        if ignore:
            # -v excludes any files matching the given terms (stated with -e)
            # -i makes this search case insensitive
            # split ignore string on comma and loop through list
            for pattern in ignore.split(","):
                grep_ignore = f'| grep -v -i  -e "{pattern}" '
        else:
            grep_ignore = ""

        local_file_count = (
            f"find {self.rf_obj.runfolderpath} -type f {grep_ignore} | wc -l"
        )
        files_expected, err, returncode = toolbox.execute_subprocess_command(
            local_file_count, self.rf_obj.rf_loggers.upload_agent
            )
        uploaded_file_count = (
            ad_config.DX_CMDS['find_data'] % (
                self.nexus_project_name, self.rf_obj.dnanexus_apikey
                )
        )
        # Call upload command, writing to upload agent log
        files_present, err, returncode = toolbox.execute_subprocess_command(
            uploaded_file_count, self.rf_obj.rf_loggers.upload_agent
            )
        # Write output stream to logfile and terminal
        self.logger.info(
            self.logger.log_msgs["files_uploaded"], files_expected, files_present,
        )

        if ignore:
            # test for presense of any ignore strings in project
            uploaded_file_count_ignore = (
                ad_config.DX_CMDS['find_data'] % (
                    f"{self.nexus_project_name} {grep_ignore.replace('-v','')}",
                    self.rf_obj.dnanexus_apikey
                    )
                )
            out, err, returncode = toolbox.execute_subprocess_command(
                uploaded_file_count_ignore, self.rf_obj.rf_loggers.upload_agent
                )
            # Write output stream to logfile and terminal
            self.logger.info(self.logger.log_msgs["check_ignore"], out)

    def upload_files(
        self, upload_cmd: str, files_list: list, upload_type: str
    ) -> Union[str, list]:
        """
        Uploads files when provided with an upload command, files list, and upload type
        Details written to log files (upload agent logfile and runfolder logfile) and
        then command passed to execute_subprocess_command(). All standard error/standard
        out written to a log file
            :param upload_cmd (str):    Command to use to upload the files
            :param files_list (list):   List of all files requiring upload
            :param upload_type (str):   String describing the files being uploaded
            :return "fail" (str) |
            "success" (str) |
            nonexistent_files (list):   "success" if upload successful, "fail" if
                                        unsuccessful, nonexistent_files if not all
                                        files for upload are present on the machine
        """
        # Check all files exist before trying to upload. If they don't the script will
        # fail when trying to upload them
        upload_attempts = 0
        if all([os.path.isfile(f) for f in files_list]):
            while upload_attempts < 5:  # Attempt the upload 5 times
                # Execute upload agent command, writing log to upload agent log file
                out, err, returncode = toolbox.execute_subprocess_command(
                    upload_cmd, self.rf_obj.rf_loggers.upload_agent
                    )
                if returncode == 0:
                    return "success"
                    break
                else:
                    upload_attempts += 1
            else:
                return "fail"
        else:
            nonexistent_files = []
            for f in files_list:
                if not os.path.isfile(f):
                    nonexistent_files.append(f)
            return nonexistent_files
