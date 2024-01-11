#!/usr/bin/python3
# coding=utf-8
"""
upload_runfolder.py Uploads an Illumina runfolder to DNAnexus. Contains the following classes:

- UploadRunfolder
    Uploads a runfolder to DNAnexus
"""
import sys
import os
import re
import math
from config.ad_config import URConfig
from toolbox.toolbox import execute_subprocess_command, git_tag, test_upload_software


class UploadRunfolder(URConfig):
    """
    Uploads a runfolder to DNAnexus.

    Attributes:
        rf_obj (obj):               RunfolderObject object (contains runfolder-specific attributes)
        logger (obj):               Logger object
        nexus_identifiers (dict):   Dictionary containing project name and ID

    Methods:
        find_nexus_project()
            Search DNAnexus for the project given as an input argument. If the input is
            'None', searches for a project matching self.rf_obj.runfolder_name
        upload_rest_of_runfolder(ignore)
            Call methods to upload the rest of the runfolder (the runfolder
            minus the fastqs and several QC files)
        check_runfolder_exists()
            Check runfolder exists
        get_file_dict(ignore)
            Get dictionary of all files and folders requiring upload, ignoring any
            files specified in the ignore string. Folders as key and files in the
            folder as the value in list format
        get_folderpaths()
            Walk through runfolder and create a list of all folder paths within the runfolder
        get_filepaths(folderpaths, ignore)
            Add the files contained within each folder to the file_dict, ignoring
            any files in the filepath_list that are specified in the ignore string
        ignore_file(filepath, ignore)
            Determine whether a file should be ignored by parsing the ignore string
            and comparing to the filepath
        build_upload_cmds()
            Build upload commands to upload the rest of the runfolder. The upload
            agent command can take multiple files separated by a space, with the
            full path required for each file, and it has a max number of uploads
            of 1000 per command. This function generates per-folder upload commands,
            with maximum 100 files being uploaded per command
        get_nexus_project_subdirectory(folderpath)
            Get the corresponding DNAnexus subdirectory name for the folderpath.
            This is used in the upload agent's '--folder' argument
        get_required_iterations(folderpath)
            Upload agent has a max number of uploads of 1000 per command. Uploading
            multiple files at a time is quicker, but uploading too many at a time
            has caused it to hang.
        upload_files(upload_cmd, files_list)
            Uploads files when provided with an upload command and files list
        count_uploaded_files(ignore)
            Count the number of files to be uploaded and check if any that should
            have been ignored are in DNAnexus
    """

    def __init__(self, rf_obj: object, nexus_identifiers=False):
        """
        Constructor for the UploadRunfolder class
            :param rf_obj (obj):        RunfolderObject object (contains runfolder-specific attributes)
            :param nexus_identifiers    Dictionary of proj_name and proj_id, or False
            (dict | False):
        """
        self.rf_obj = rf_obj
        self.logger = self.rf_obj.rf_loggers.backup
        if nexus_identifiers:
            self.nexus_identifiers = nexus_identifiers
        else:
            self.nexus_identifiers = self.find_nexus_project()

    def find_nexus_project(self) -> dict:
        """
        Search DNAnexus for the project given as an input argument. If the input is
        'None', searches for a project matching self.rf_obj.runfolder_name.
            :return (dict):     Dictionary containing proj_name and proj_id
        """
        self.logger.info(
            self.logger.log_msgs["finding_project"],
            self.rf_obj.runfolder_name,
        )
        project_name, _, _ = execute_subprocess_command(
            URConfig.DX_CMDS["find_proj_name"]
            % (self.rf_obj.runfolder_name, self.rf_obj.dnanexus_auth),
            self.logger,
            "exit_on_fail",
        )
        self.logger.info(
            self.logger.log_msgs["project_name"],
            project_name,
        )
        self.logger.info(
            self.logger.log_msgs["finding_project_id"],
            self.rf_obj.runfolder_name,
        )
        project_id, _, _ = execute_subprocess_command(
            URConfig.DX_CMDS["find_proj_id"]
            % (project_name, self.rf_obj.dnanexus_auth),
            self.logger,
            "exit_on_fail",
        )
        self.logger.info(
            self.logger.log_msgs["project_id"],
            project_id,
        )
        return {
            "proj_name": project_name,
            "proj_id": project_id,
        }

    def upload_rest_of_runfolder(self, ignore: str) -> None:
        """
        Call methods to upload the rest of the runfolder (the
        runfolder minus the fastqs and several QC files)
            :return None:
        """
        self.logger.info(
            self.logger.log_msgs["ad_version"],
            git_tag(),
        )
        test_upload_software(self.logger)
        self.check_runfolder_exists()
        self.file_dict = self.get_file_dict(ignore)
        self.build_upload_cmds()
        # It is quicker to upload files in parallel so files in each
        # folder are uploaded as separate commands
        for folderpath in self.file_dict:
            self.logger.info(self.logger.log_msgs["uploading_files"], folderpath)
            if "upload_cmds" in self.file_dict[folderpath].keys():
                for upload_cmd in self.file_dict[folderpath]["upload_cmds"]:
                    filepath_list = self.file_dict[folderpath]["upload_cmds"][
                        upload_cmd
                    ]
                    self.upload_files(upload_cmd, filepath_list)
        self.count_uploaded_files(ignore)  # Run tests to count files

    def check_runfolder_exists(self) -> None:
        """
        Check runfolder exists. If it does not, exit script
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
            sys.exit(1)

    def get_file_dict(self, ignore: str) -> dict:
        """
        Get dictionary of all files and folders requiring upload, ignoring any
        files specified in the ignore string. Folders as key and files in the
        folder as the value in list format
            :return file_dict (dict):   Dictionary of files for upload. Of
                                        structure {folderpath: filepath_list}
        """
        self.logger.info(self.logger.log_msgs["building_file_dict"])
        folderpaths = self.get_folderpaths()
        file_dict = self.get_filepaths(folderpaths, ignore)
        return file_dict

    def get_folderpaths(self) -> list:
        """
        Walk through runfolder and create a list of all folder paths within the runfolder
            :return folderpaths (list): Return a list of folder paths within the runfolder
        """
        self.logger.info(self.logger.log_msgs["getting_folder_paths"])
        folderpaths = [self.rf_obj.runfolderpath]  # Add root folder path
        for root, subfolders, _ in os.walk(self.rf_obj.runfolderpath):
            for folder in subfolders:  # Add subfolder paths
                folderpaths.append(os.path.join(root, folder))
        return folderpaths

    def get_filepaths(self, folderpaths: str, ignore: str) -> dict:
        """
        Add the files contained within each folder to the file_dict, ignoring any
        files in the filepath_list that are specified in the ignore string
            :param folderpaths (list):  List of folder paths within the runfolder
            :param ignore (str):        String for which files that match this
                                        string should be ignored
            :return file_dict (dict):   Dictionary containing runfolder folder paths
                                        and filepaths wtihin each folder
        """
        self.logger.info(self.logger.log_msgs["getting_file_paths"])
        file_dict = {}
        for folderpath in folderpaths:
            file_dict[folderpath] = {"filepaths": []}
            filepath_list = [
                os.path.join(folderpath, file)
                for file in os.listdir(folderpath)
                if os.path.isfile(os.path.join(folderpath, file))
            ]
            for filepath in filepath_list:
                if not self.ignore_file(filepath, ignore):
                    file_dict[folderpath]["filepaths"].append(filepath)
        self.logger.info(  # Report the folders and files to be uploaded
            self.logger.log_msgs["files_for_upload"], file_dict[folderpath]["filepaths"]
        )
        return file_dict

    def ignore_file(self, filepath: str, ignore: str) -> bool:
        """
        Determine whether a file should be ignored by parsing the ignore string and comparing
        to the filepath. If an ignore pattern was specified, split the string on the comma and
        loop through the list, searching for the pattern in the filepath with standardised case.
        If the pattern is present, return True (file should not be uploaded), else return False
        if no pattern was given or the pattern was not found in the filepath (file should be uploaded)
            :param filepath (str):  Path of file for comparison
            :param ignore (str):    String containing files to ignore
            :return bool:           True if file should be ignored, False if not
        """
        if ignore:
            for pattern in ignore.split(","):
                if pattern.upper() in filepath.upper():
                    self.logger.info(self.logger.log_msgs["ignoring_files"], filepath)
                    return True
        else:
            return False

    def build_upload_cmds(self) -> None:
        """
        Build upload commands to upload the rest of the runfolder. The upload agent command can take
        multiple files separated by a space, with the full path required for each file, and it has a
        max number of uploads of 1000 per command. This function generates per-folder upload
        commands, providing 100 files maximum per upload command
            :return None:
        """
        for folderpath in self.file_dict:
            if self.file_dict[folderpath]["filepaths"]:
                nexus_project_subdirectory = self.get_nexus_project_subdirectory(
                    folderpath
                )
                # Used as indices to pass a slice of the file list (0-100) to the upload agent
                start_index, stop_index = 0, 100
                iterations_needed = self.get_required_iterations(folderpath)
                iteration_count = 1
                while (
                    iteration_count <= iterations_needed
                ):  # While we haven't finished the iterations
                    self.logger.info(
                        self.logger.log_msgs["command_iteration"],
                        iteration_count,
                        iterations_needed,
                    )
                    files_string = ""
                    # If last iteration, set stop as list length (only includes indices of elements)
                    # that exist in the list (e.g. if 4 elements, slice is 0:4)
                    if iteration_count == iterations_needed:
                        stop_index = len(self.file_dict[folderpath]["filepaths"])

                    files_list = []
                    # Take a slice of list using from and to
                    for file in self.file_dict[folderpath]["filepaths"][
                        start_index:stop_index
                    ]:
                        # Upload agent command can take multiple space-separated files
                        # Full file path is required for each file
                        files_string = (
                            f"{files_string} '{os.path.join(folderpath, file)}'"
                        )
                        files_list.append(os.path.join(folderpath, file))

                    self.logger.info(self.logger.log_msgs["building_command"])
                    nexus_upload_cmd = URConfig.DX_CMDS["file_upload_cmd"] % (
                        self.rf_obj.dnanexus_auth,
                        self.nexus_identifiers["proj_name"],
                        nexus_project_subdirectory,
                        f"--tries 100 {files_string}",
                    )
                    self.file_dict[folderpath]["upload_cmds"] = {
                        nexus_upload_cmd: files_list
                    }
                    self.logger.info(self.logger.log_msgs["added_command"])
                    # Increase iteration_count and start and stop by 100 for the next iteration
                    # so second iteration will do next batch of up to 100 files
                    iteration_count += 1
                    start_index += 100
                    stop_index += 100

    def get_nexus_project_subdirectory(self, folderpath: str) -> str:
        """
        Get the corresponding DNAnexus subdirectory name for the folderpath.
        This is used in the upload agent's '--folder' argument
            :param folder_path (str):                   Path of a local folder containing
                                                        files to be uploaded to DNAnexus
            :returnnexus_project_subdirectory (str):    DNAnexus folder name e.g. runfolder/RTALogs
        """
        # Files in the root of a runfolder do not require cleaning, while files not in the root
        # require removal of the runfolder name and parent folders from the input filepath
        if folderpath == self.rf_obj.runfolderpath:
            clean_runfolder_path = ""
        else:
            clean_runfolder_path = re.search(
                rf"{self.rf_obj.runfolder_name}[\/](.*)$", folderpath
            ).group(1)
        # Prepend nexus folder path to cleaned path. the nexus folder path is
        # the project name without the first four characters (002_)
        nexus_project_subdirectory = os.path.join(
            "/", self.nexus_identifiers["proj_name"][4:], clean_runfolder_path
        )
        self.logger.info(
            self.logger.log_msgs["nexus_project_subdirectory"],
            nexus_project_subdirectory,
        )
        return nexus_project_subdirectory

    def get_required_iterations(self, folderpath: str) -> int:
        """
        Upload agent has a max number of uploads of 1000 per command. Uploading multiple
        files at a time is quicker, but uploading too many at a time has caused it to hang.
        Therefore the maximum number per upload command created by these sripts is set at
        100. Counts the number of files in list and divide by 100.0 eg 20/100.0 = 0.02.
        ceil rounds up to the nearest integer (0.02->1). If there are 100,
        ceil(100/100.0)=1.0 iteration if there are 750 ceil(750/100.0)=8.0 iterations
            :param folderpath (str):            Path of a local folder containing
                                                files to be uploaded to DNAnexus
            :return iterations_needed (int):    The required number of upload commands to
                                                upload all the files in the folder
        """
        iterations_needed = math.ceil(
            len(self.file_dict[folderpath]["filepaths"]) / 100.0
        )
        self.logger.info(
            self.logger.log_msgs["iterations_needed"], iterations_needed, folderpath
        )
        return iterations_needed

    def upload_files(self, upload_cmd: str, files_list: list) -> list:
        """
        Uploads files when provided with an upload command and files list. Details
        are written to log files (upload agent logfile and runfolder logfile) and
        then command passed to execute_subprocess_command(). All standard
        error/standard out is written to a log file
            :param upload_cmd (str):    Command to use to upload the files
            :param files_list (list):   List of all files requiring upload
            :return "fail" (str) |
            "success" (str) |
            nonexistent_files (list):   "success" if upload successful, "fail" if
                                        unsuccessful, nonexistent_files if not all
                                        files for upload are present on the machine
        """
        upload_attempts = 0
        # Check all files exist before trying to upload. If they don't, the script
        # will fail when trying to upload them
        if all([os.path.isfile(file) for file in files_list]):
            self.logger.info(self.logger.log_msgs["call_ua"], files_list)
            while upload_attempts < 5:  # Attempt the upload 5 times
                # Execute upload agent command, writing log to upload agent log file
                _, _, returncode = execute_subprocess_command(
                    upload_cmd, self.rf_obj.rf_loggers.backup, "exit_on_fail"
                )
                if returncode == 0:
                    return "success"
                else:
                    upload_attempts += 1
            else:
                return "fail"
        else:
            nonexistent_files = []
            for file in files_list:
                if not os.path.isfile(file):
                    nonexistent_files.append(file)
            if nonexistent_files:
                self.logger.error(
                    self.logger.log_msgs["nonexistent_files"], nonexistent_files
                )
            else:
                self.logger.error(
                    self.logger.log_msgs["files_exist"],
                )
            return nonexistent_files

    def count_uploaded_files(self, ignore: str) -> None:
        """
        Count the number of files to be uploaded and check if any that should have been
        ignored are in DNAnexus
            :param ignore (str): String containing files to ignore
            :return None:
        """
        self.logger.info(self.logger.log_msgs["counting_files"])
        if ignore:
            # Split ignore string on comma and loop through list
            for pattern in ignore.split(","):
                # -v excludes any files matching the given terms (stated with -e)
                # -i makes this search case insensitive
                grep_ignore = f'| grep -v -i  -e "{pattern}" '
        else:
            grep_ignore = ""

        local_file_count = (
            f"find {self.rf_obj.runfolderpath} -type f {grep_ignore} | wc -l"
        )
        files_expected, _, _ = execute_subprocess_command(
            local_file_count, self.rf_obj.rf_loggers.backup, "exit_on_fail"
        )
        uploaded_file_count = URConfig.DX_CMDS["find_data"] % (
            self.nexus_identifiers["proj_name"],
            self.rf_obj.dnanexus_auth,
        )
        files_present, _, _ = execute_subprocess_command(
            uploaded_file_count, self.rf_obj.rf_loggers.backup, "exit_on_fail"
        )
        self.logger.info(
            self.logger.log_msgs["files_uploaded"],
            files_expected,
            files_present,
        )
        if ignore:  # Test for presense of ignore strings in project
            uploaded_file_count_ignore = URConfig.DX_CMDS["find_data"] % (
                f"{self.nexus_identifiers['proj_name']} {grep_ignore.replace('-v','')}",
                self.rf_obj.dnanexus_auth,
            )
            out, _, _ = execute_subprocess_command(
                uploaded_file_count_ignore,
                self.rf_obj.rf_loggers.backup,
                "exit_on_fail",
            )
            self.logger.info(self.logger.log_msgs["check_ignore"], out)
