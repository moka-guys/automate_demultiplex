# coding=utf-8
""" runfolder_obj.py

This module creates an object with runfolder specific properties
"""
import os
import config.ad_config as ad_config

# TODO make this runnable on the command line

class RunfolderObject(object):
    """
    An object with runfolder-specific properties.

    Args:
        runfolder_name (str):   Runfolder name string
        timestamp (str):        Timetamp in the format
                                str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
    """

    def __init__(self, runfolder_name, timestamp):
        self.timestamp = timestamp
        self.runfolder_name = runfolder_name
        self.runfolderpath = os.path.join(
            ad_config.RUNFOLDERS, self.runfolder_name
        )
        self.samplesheet_name = (
            ad_config.SAMPLESHEET_NAME % self.runfolder_name
            )
        # Stored within runfolder
        # Sequencing finished file (within runfolder)
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["rtacomplete"]
        )
        # Samplesheet (within runfolder)
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )
        # Integrity check file (within runfolder)
        self.checksumfile_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["md5checksum"]
        )
        # Bcl2fastq log file (within runfolder)
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["bcl2fastqlog"]
        )
        # Runfolder fastq folder (within runfolder)
        self.fastq_dir_path = os.path.join(
            self.runfolderpath, ad_config.DIRS["fastqs"]
        )
        # Upload agent logfile (within runfolder)
        self.upload_agent_logfile = os.path.join(
            self.runfolderpath, ad_config.FILENAMES["upload_started"]
        )
        # Bcl2fastq stats file (within runfolder)
        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            ad_config.DIRS["bcl2fastq_stats"],
            ad_config.FILENAMES["bcl2fastq_stats"],
        )

        # Stored within samplesheets dir
        # Samplesheet (samplesheets dir)
        self.samplesheet_path = (
            ad_config.SAMPLESHEET_PATH % self.runfolder_name
            )

        # Stored within logfiles dir
        # Workflow dx run commands for runfolder (within logfiles dir)
        self.runfolder_dx_run_script = (
            ad_config.LOGFILES['dx_run_script'] % self.runfolder_name
            )
        # Congenica upload commands for runfolder (within logfiles dir)
        self.congenica_dx_run_script = (
            ad_config.LOGFILES["congenica_upload_script"] % self.runfolder_name
        )
        # Dnanexus project creation bash script (within logfiles dir)
        self.project_creation_logfile = (
            ad_config.LOGFILES["proj_creation_script"] % self.runfolder_name
        )
        # Backup runfolder logfile (within logfiles dir)
        self.backup_runfolder_logfile = (
            ad_config.LOGFILES["backup_runfolder"] % self.runfolder_name
        )
        # Logfiles that contain timestamps - uses get_scriptlog() to search
        # for existing logfile containing runfolder name

        # Logfile to contain runfolder upload log
        self.upload_runfolder_logfile = self.get_runfolder_logs(
            ad_config.LOGDIRS["upload_script"],
            ad_config.LOGFILES["upload_script"] %
            f"{self.timestamp}_{self.runfolder_name}"
            )
        # Logfile to contain runfolder demultiplex log
        self.demultiplex_runfolder_logfile = self.get_runfolder_logs(
            ad_config.LOGDIRS["demultiplex"],
            ad_config.LOGFILES["demultiplex_script_logfile"] %
            f"{self.timestamp}_{self.runfolder_name}"
            )

    def get_runfolder_logs(self, directory, logfile):
        """
        Find the the logfile for the runfolder. Logfile contains an unknown
        timestamp. Search for any demultiplex logfiles matching the runfolder
        name and return the first
        If none exist, get the logfile from before it is renamed with
        processed runfolders
        """
        any_logs = [
            os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if self.runfolder_name in filename
        ]
        logfile = any_logs.pop() if any_logs else logfile
        return logfile

        # TODO take these out of this class
        self.nexus_project_name = ""
        self.nexus_path = ""
        self.nexus_project_id = ""
        self.nexus_runfolder_subdir = ""
        self.nexus_proj_root = ""
