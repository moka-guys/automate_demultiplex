# coding=utf-8
""" rf_obj.py

This module creates an object with runfolder specific properties
"""
import os
import ad_config as config


class RunfolderObject(object):
    """
    An object with runfolder specific properties.
    """

    def __init__(self, runfolder_name, timestamp):
        self.timestamp = timestamp
        # Set empty variables to be defined based on the run
        self.runfolder_name = runfolder_name
        self.runfolderpath = os.path.join(
            config.RUNFOLDERS, self.runfolder_name
        )
        # Sequencing finished file
        self.rtacompletefile_path = os.path.join(
            self.runfolderpath, config.FILENAMES["rtacomplete"]
        )
        # Samplesheet
        self.samplesheet_name = config.SAMPLESHEET_NAME % self.runfolder_name
        self.samplesheet_path = config.SAMPLESHEET_PATH % self.runfolder_name
        self.runfolder_samplesheet_path = os.path.join(
            self.runfolderpath, self.samplesheet_name
        )

        # Integrity check file
        self.checksumfile_path = os.path.join(
            self.runfolderpath, config.FILENAMES["md5checksum"]
        )
        # Bcl2fastq log file
        self.bcl2fastqlog_path = os.path.join(
            self.runfolderpath, config.FILENAMES["bcl2fastqlog"]
        )
        # Project fastq folder
        self.fastq_dir_path = os.path.join(
            self.runfolderpath, config.DIRS["fastqs"]
        )
        # Runfolder dx run commands
        self.runfolder_dx_run_script = config.DXRUN_SCRIPT % runfolder_name
        self.congenica_upload_cmds_file = (
            config.PATHS["congenica_upload_script"] % self.runfolder_name
        )
        # Dnanexus project creation logfile
        self.project_creation_logfile = (
            config.PROJ_CREATION_SCRIPT % self.runfolder_name
        )
        # Backup runfolder logfile
        self.backup_runfolder_logfile = (
            config.BACKUP_RUNFOLDER_LOGFILE % self.runfolder_name
        )
        # Upload agent logfile
        self.upload_agent_logfile = os.path.join(
            self.runfolderpath, config.FILENAMES["upload_started"]
        )

        self.bcl2fastqstats_file = os.path.join(
            self.runfolderpath,
            config.DIRS["bcl2fastq_stats"],
            config.FILENAMES["bcl2fastq_stats"],
        )

        self.nexus_project_name = ""
        self.nexus_path = ""
        self.nexus_project_id = ""
        self.nexus_runfolder_subdir = ""
        self.nexus_proj_root = ""
