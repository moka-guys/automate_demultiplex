#!/usr/bin/env python3
"""backup_runfolder

Uploads an Illumina runfolder to DNANexus.

Example:
    usage: backup_runfolder.py [-h] -i RUNFOLDER -a AUTH [--ignore IGNORE]
                                [-p PROJECT]

    Ignore is a comma seperated string of terms which prevents the upload of
    files if that term is present in the filename or filepath.
"""

import datetime
import argparse
import re
import os
import sys
import subprocess
from distutils.spawn import find_executable
import math
from ad_logger import ad_logger
from runfolder_obj.runfolder_obj import RunfolderObject
import config.ad_config as ad_config
from git_tag.git_tag import git_tag  # Import function which reads the git tag

# TODO improve log messages in this script
# TODO work out how to set up repo wide logging - check out graemes basher repo
# TODO write a test suite
# TODO incorporate traceback into logging


def cli_arguments(args):
    """Parses command line arguments.
    Args:
        args: A list containing the expected commandline arguments. Example:
            ['backup_runfolder.py', '-i',
            '180216_M02353_0185_000000000-D357Y', '-a',
            'AUTH_TOKEN', '-p', '003_180924_TrioPipelineGATK',
            '--ignore', '.txt']
    Returns:
        An argparse.parser object with methods named after long-option
        command-line arguments. Example:
            --runfolder "media/data1/share/runfolder" -->
            parser.parse_args(args).runfolder
    """
    parser = argparse.ArgumentParser()

    with open(
        ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
    ) as token_file:
        dnanexus_apikey = token_file.readline().rstrip()  # Auth token

    # Define arguments
    parser.add_argument(
        "-i",
        "--runfolder",
        required=True,
        help="An Illumina runfolder name",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--auth-token",
        help=(
            "A string or file containing a DNAnexus authorisation key used to "
            "access the DNANexus project."
        ),
        default=dnanexus_apikey,
        type=os.path.expanduser,
    )
    parser.add_argument(
        "--ignore",
        default=None,
        help=(
            "Comma-separated list of patterns which prevents the file "
            "from being uploaded if any pattern is present in filename "
            "or filepath."
        ),
    )
    parser.add_argument(
        "-p",
        "--project",
        default=None,
        help=("The name of an existing DNAnexus project for the given runfolder"),
    )
    return parser.parse_args(args)  # Collect arguments and return


class UAcaller:
    """Uploads a runfolder to DNAnexus.

    Attributes:
        now:            Current datetime string
        runfolder_obj:  Runfolder object
        loggers:        Runfolder loggers
        ignore:         A comma-separated string of regular expressions.
                        Used to skip files for upload.
        auth_token:     DNAnexus api key. Passed as string or filename argument

    Methods:
        find_ua():
        find_nexus_project(project):   Searches DNAnexus for a project matching
                                       the input. If the input argument is
                                       'None', searches for the first project
                                       matching project input
        get_nexus_filepath():
        ignore_file():
        call_upload_agent():           Calls the DNAnexus upload agent using
                                       the class attributes
        count_uploaded_files():
    """

    def __init__(
        self,
        runfolder,
        ignore,
        loggers,
        auth_token=False,
        project=None,
    ):
        self.now = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
        self.runfolder_obj = RunfolderObject(runfolder, self.now)
        self.loggers = loggers
        self.ignore = ignore

        # Set DNAnexus authentication token
        if not auth_token:
            with open(
                ad_config.CREDENTIALS["dnanexus_authtoken"], "r", encoding="utf-8"
            ) as token_file:
                self.auth_token = token_file.readline().rstrip()  # Auth token
        else:
            self.auth_token = auth_token

        self.loggers.backup.info(
            f"automate_demultiplexing release: {git_tag()}",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # Set DNAnexus project
        self.runfolder_obj.nexus_project_name = self.find_nexus_project(project)

    def perform_backup(self):
        """ """
        self.check_for_programs()  # Check upload agent exists in system path
        self.check_runfolder_exists()
        self.call_upload_agent()  # Call the DNAnexus upload agent
        self.count_uploaded_files()  # run tests to count files

    def check_for_programs(self):
        """Check upload agent exists in system path
        Uses distutils.spawn.find_executable package to assert the programs
        are callable by parsing the directories in the system PATH
        variable (i.e. bash `which` command)
        """
        # Raise error if any calls to find_executable() fail
        for program in ["dx", ad_config.EXECUTABLES["upload_agent"]]:
            if find_executable(program):
                self.loggers.backup.info(
                    f"Found program: {program}",
                    extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
                )
            else:
                self.loggers.backup.exception(
                    f"Could not find program: {program}",
                    extra={"flag": self.loggers.log_flags["backup_runfolder"]["fail"]},
                )

    def check_runfolder_exists(self):
        """ """
        self.loggers.backup.info(
            f"Checking the runfolder {self.runfolder_obj.runfolderpath}",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        if not os.path.isdir(self.runfolder_obj.runfolderpath):
            self.loggers.backup.exception(
                "The runfolder does not exist: " f"{self.runfolder_obj.runfolderpath}",
                extra={"flag": self.loggers.log_flags["backup_runfolder"]["fail"]},
            )
            raise IOError("Invalid runfolder given as input")

    def find_nexus_project(self, project):
        """Search DNAnexus for the project given as an input argument.
        If the input is 'None', searches for a project matching
        self.runfolder_obj.runfolder_name.
        Args:
            project: The name of a project on DNAnexus.
            If None, searches using runfolder name.
        """
        self.loggers.backup.info(
            f"Searching for DNAnexus project: {project}",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # Get list of projects from DNAnexus as a string. Due to python3's
        # default use of bytestrings from various modules, bytes.decode() must
        # be called to return the output as a pyton str object.
        # This is required for pattern matching with the re module.
        projects = subprocess.check_output(
            ["dx", "find", "projects", "--auth", self.auth_token]
        ).decode()
        # Set the regular expression pattern for asserting that the project
        # exists in DNAnexus. The bytes() function is required to create
        # bytestrings
        if project is None:
            # If no project given, search for one or more word character, using
            # \w+ ([a-zA-Z0-9_]), either side of the runfolder name given to
            # the class
            pattern = rf"(\w*{self.runfolder_obj.runfolder_name}\w*)"
        else:
            # Else, search for the exact project name passed to the function
            pattern = rf"({project})"

        # List all strings captured by the regular expression pattern defined
        # to match the project
        project_matches = re.findall(pattern, projects)

        # If only one project is found, return this value
        if len(project_matches) == 1:
            return project_matches[0]
        # Else if any other number of matching projects is foud, log this event
        # and raise an Error
        else:
            self.loggers.backup.error(
                f"{len(project_matches)} DNAnexus projects found for pattern "
                f"{pattern}: {project_matches}. Repeat script by giving "
                "explicit project to -p/--project flag",
                extra={"flag": self.loggers.log_flags["backup_runfolder"]["fail"]},
            )
            raise ValueError(
                "Invalid DNAnexus project name. 0 or >1 " "matching projects found."
            )

    def get_nexus_filepath(self, folder_path):
        """
        To recreate the directory structure in DNA Nexus need to take relative
        path of each the subfolder.
        This subfolder path is prefixed with the top level folder in DNAnexus
        (the project name without the first four characters (002_)).
        Returns a tuple (DNAnexus upload folder path, full DNAnexus file path)
        DNAnexus upload folder path is used in the upload agent's '--folder'
        argument.
        Args:
            folder_path - The path of a local folder containing files to be
                          uploaded to DNAnexus
        Returns:
            A tuple: (DNAnexus upload folder path, full DNAneuxs file path)
        Example:
            self.get_nexus_filepath('/media/data1/share/runfolder/RTALogs/')
            >>> (runfolder/RTALogs, PROJECT:/runfolder/RTALogs/)
        """
        # Clean the runfolder name and parent folders from the input file path.
        # Features of the regular expression below:
        #    {} - Replaced with the runfolder name by call to
        #           str.format(self.runfolder_obj.runfolder_name)
        #    [\/] - Looks a forward or backward slash in this position,
        #           accounting for linux or windows filesystems
        #    (.*)$ - Capture all characters to the end of the line.
        #    Parentheses in regular expressions capture a group, the first of
        #    which can be returned from re.search().group(1)DNAnexus
        # if we are uploading files in the root of a runfolder,
        # need to skip this step
        if folder_path == self.runfolder_obj.runfolderpath:
            clean_runfolder_path = ""
        else:
            clean_runfolder_path = re.search(
                rf"{self.runfolder_obj.runfolder_name}[\/](.*)$", folder_path
            ).group(1)

        # Prepend the nexus folder path to cleaned path. the nexus folder path
        # is the project name without the first four characters (002_).
        nexus_path = os.path.join(
            "/", self.runfolder_obj.nexus_project_name[4:], clean_runfolder_path
        )

        # Return the nexus folder and full project filepath
        return (
            nexus_path,
            f"{self.runfolder_obj.nexus_project_name}:{nexus_path}",
        )

    def ignore_file(self, filepath):
        # if an ignore pattern was specified
        if self.ignore:
            # split this string on comma and loop through list
            for pattern in self.ignore.split(","):
                # Make ignore pattern and filepath upper case and search
                # filepath for the pattern
                if pattern.upper() in filepath.upper():
                    # if present return True to indicate the file should not
                    # be uploaded
                    return True
        # if no search patterns given, or pattern not found in filepath return
        # False to say file can be uploaded
        return False

    def call_upload_agent(self):
        """
        Loop through the runfolder and build the upload agent command.
        It is quicker to upload files in paralell so all files in a folder are
        added to a list and a single command issued per folder
        """
        self.loggers.backup.info(
            "Calling upload agent for input files",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # create a dictionary to hold the directories as a key, and the list of
        # files as the value
        file_dict = {}
        # walk through run folder
        for root, subfolders, files in os.walk(self.runfolder_obj.runfolderpath):
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
                    if not self.ignore_file(filepath):
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
            # loop through this list
            for filepath in filepath_list:
                # test filepath for ignore patterns
                if not self.ignore_file(filepath):
                    # if ignore pattern not found add filepath to list
                    file_dict[folderpath].append(filepath)

        # report the folders and files to be uploaded
        self.loggers.backup.info(
            f"Files for upload: {file_dict}",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # call upload agent on each folder
        for path in file_dict:
            # if there are any files to upload
            if file_dict[path]:
                # create the nexus path for each dir
                nexus_path, project_filepath = self.get_nexus_filepath(path)
                self.loggers.backup.info(
                    f"Calling upload agent on {path} to location "
                    f"{project_filepath}",
                    extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
                )
                # upload agent has a max number of uploads of 1000 per command.
                # uploadingmultiple files at a time is quicker, but uploading
                # too many at a time has caused it to hang.
                # count number of files in list and divide by 100.0 eg 20/100.0
                # = 0.02. ceil rounds up to the nearest integer (0.02->1). If
                # there are 100, ceil(100/100.0)=1.0 if there are 750
                # ceil(750/100.0)=8.0
                iterations_needed = math.ceil(len(file_dict[path]) / 100.0)
                # set the iterations count to 1
                iteration_count = 1
                # will pass a slice of the file list to the upload agent so set
                # variables for start and stop so it uploads files 0-999
                start = 0
                stop = 100
                # while we haven't finished the iterations
                while iteration_count <= iterations_needed:
                    # if it's the last iteration, set stop == length of list so
                    # not to ask for elements that aren't in the list  (if 4
                    # items in list len(list)=4 and slice of 0:4 won't miss
                    # the last element)
                    if iteration_count == iterations_needed:
                        stop = len(file_dict[path])
                    self.loggers.backup.info(
                        f"Uploading files {start} to {stop}",
                        extra={
                            "flag": self.loggers.log_flags["backup_runfolder"]["info"]
                        },
                    )
                    # the upload agent command can take multiple files
                    # separated by a space. the full file path is required for
                    # each file
                    files_string = ""
                    # take a slice of list using from and to
                    for file in file_dict[path][start:stop]:
                        files_string = f"{files_string} '{os.path.join(path, file)}'"

                    # increase the iteration_count and start and stop by 1000
                    # for the next iteration so second iteration will do files
                    # 1000-1999
                    iteration_count += 1
                    start += 100
                    stop += 100

                    # Create DNAnexus upload command
                    nexus_upload_command = (
                        f"{ad_config.EXECUTABLES['upload_agent']} "
                        f"--auth-token {self.auth_token} "
                        f"--project {self.runfolder_obj.nexus_project_name} "
                        f"--folder {nexus_path} --do-not-compress "
                        f"--upload-threads 10 --tries 100 {files_string}"
                    )

                    # Mask the autentication key in the upload command and log
                    masked_nexus_upload_command = nexus_upload_command.replace(
                        self.auth_token, ""
                    )
                    self.loggers.backup.info(
                        masked_nexus_upload_command,
                        extra={
                            "flag": self.loggers.log_flags["backup_runfolder"]["info"]
                        },
                    )
                    # Call upload command redirecting stderr to stdout
                    proc = subprocess.Popen(
                        [nexus_upload_command],
                        stderr=subprocess.STDOUT,
                        stdout=subprocess.PIPE,
                        shell=True,
                    )
                    # Capture output streams (err is redirected to out above)
                    (out, err) = proc.communicate()
                    # Write output stream to logfile and terminal
                    self.loggers.backup.info(
                        out.decode(),
                        extra={
                            "flag": self.loggers.log_flags["backup_runfolder"]["info"]
                        },
                    )

    def count_uploaded_files(self):
        """Count the number of files to be uploaded and check if any that
        should have been ignored are in DNAnexus
        """
        self.loggers.backup.info(
            "Counting the number of files that need to be uploaded, have been "
            "uploaded and check if any that should have been ignored are in "
            "DNAnexus",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # count number of files to be uploaded
        # if ignore terms given need to add a grep step
        if self.ignore:
            # -v excludes any files matching the given terms (stated with -e)
            # -i makes this search case insensitive
            grep_ignore = "| grep -v -i "
            # split ignore string on comma and loop through list
            for pattern in self.ignore.split(","):
                grep_ignore = f'{grep_ignore} -e "{pattern}" '
        else:
            grep_ignore = ""

        local_file_count = (
            f"find {self.runfolder_obj.runfolderpath} -type f " f"{grep_ignore} | wc -l"
        )

        # Call upload command redirecting stderr to stdout
        proc = subprocess.Popen(
            [local_file_count],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=True,
        )
        # Capture output streams (err is redirected to out above)
        (out, err) = proc.communicate()
        # Write output stream to logfile and terminal
        self.loggers.backup.info(
            f"{out.decode().rstrip()} files that should have been uploaded "
            "(excluding any with ignore terms in filename or path)",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )
        # count number of uploaded files
        uploaded_file_count = (
            f"dx find data --project {self.runfolder_obj.nexus_project_name} " "| wc -l"
        )

        # Call upload command redirecting stderr to stdout
        proc = subprocess.Popen(
            [uploaded_file_count],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=True,
        )
        # Capture output streams (err is redirected to out above)
        (out, err) = proc.communicate()
        # Write output stream to logfile and terminal
        self.loggers.backup.info(
            f"{out.decode().rstrip()} files present in DNANexus project",
            extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
        )

        if self.ignore:
            # test for presense of any ignore strings in project
            uploaded_file_count_ignore = (
                "dx find data --project "
                f"{self.runfolder_obj.nexus_project_name} "
                f"{grep_ignore.replace('-v','')} | wc -l"
            )

            # Call upload command redirecting stderr to stdout
            proc = subprocess.Popen(
                [uploaded_file_count_ignore],
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                shell=True,
            )
            # Capture output streams (err is redirected to out above)
            (out, err) = proc.communicate()
            # Write output stream to logfile and terminal
            self.loggers.backup.info(
                f"{out.decode().rstrip()} files present in DNANexus project "
                "containing one of the ignore terms. NB this may not be "
                "accurate if the ignore term is found in the result of dx "
                "find data (eg present in project name)",
                extra={"flag": self.loggers.log_flags["backup_runfolder"]["info"]},
            )


def main(args):
    """Uploads runfolder to DNAnexus by passing given arguments to the
    DNAnexus upload agent.
    """
    # Get command line arguments
    parsed_args = cli_arguments(args)

    timestamp = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")

    runfolder_obj = RunfolderObject(parsed_args.runfolder, timestamp)

    loggers = ad_logger.AdLoggers(timestamp, runfolder_obj)

    # Create an object to set up the upload agent command
    ua_object = UAcaller(
        runfolder=parsed_args.runfolder,
        project=parsed_args.project,
        loggers=loggers,
        auth_token=parsed_args.auth_token,
        ignore=parsed_args.ignore,
    )
    # Check upload agent exists in system path
    # Call the DNAnexus upload agent
    # Run tests to count files
    ua_object.perform_backup()


if __name__ == "__main__":
    main(sys.argv[1:])
