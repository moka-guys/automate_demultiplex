# coding=utf-8
""" Automate demultiplex logging.

Currently only the 'script', 'upload_agent' and 'backup' logfiles are configured to be writeable to
by this script. These logfiles are written to by the upload and setoff workflows script.


        self.script = self._get_ad_logger('automate_demultiplex', script)
        self.upload_agent = self._get_ad_logger('upload_agent', upload_agent)
        self.backup = self._get_ad_logger('backup_runfolder', backup)
"""
import sys
import os
import logging
import logging.handlers
import ad_config as config


def get_demux_log_config(timestamp):
    """Get the demultiplex script logfile before it is renamed with processed runfolders"""
    log_config = {
        "demultiplex": os.path.join(config.demultiplex_logpath, f"{timestamp}.txt")
        }
    return log_config


# TODO finish filling in arguments
def get_runfolder_log_config(runfolder_obj, timestamp):
    """Return an ADLogger config for a runfolder.
    Args:
        runfolder_obj: A runfolder object with the following attributes:
                        runfolder_name runfolderpath
        runfolder_dx_run_script


        timestamp(str): Timestamp as str("{:%Y%m%d_%H%M%S}".format(datetime.datetime.now()))
    Returns:
        log_config(dict): A dictionary of arguments for ADLoggers
    """

    # Find the demultiplex logfile for the runfolder.
    # Logfile name contains demultiplex timestamp which is unknown at this point.
    # Search for any demultiplex logfiles matching the runfodler name and return the first.
    any_demultiplex_logs = [
        os.path.join(config.demultiplex_logpath, filename)
        for filename in os.listdir(config.demultiplex_logpath)
        if runfolder_obj.runfolder_name in filename
    ]
    demultiplex_log = any_demultiplex_logs.pop() if any_demultiplex_logs else None

    # Configuration for ADLoggers.
    # Dictionary where keys are ADLoggers.__init__ arguments and values are logfile paths.
    log_config = {
        "demultiplex": demultiplex_log,
        "upload_agent": os.path.join(
            runfolder_obj.runfolderpath, config.upload_started_filename
        ),
        "backup": os.path.join(
            config.backup_runfolder_logfile, f"{runfolder_obj.runfolder_name}_backup_runfolder.log",
        ),
        "project": os.path.join(config.dnanexus_projectcreation_logfolder,
                                "{runfolder.runfolder_name}.sh"),
        "dx_run": runfolder_obj.runfolder_dx_run_script,
        "upload_script": os.path.join(config.upload_script_logpath,
                                      f"{timestamp}_upload_and_setoff_workflow.log")
    }
    return log_config


class AdLoggers(object):
    """Access runfolder-associated logfiles, which are also uploaded to DNAnexus as part of the
    automate demultiplex scripts. (upload_agent file is not uploaded because it is being written
    to as the upload is taking place)

    Args:
        demultiplex(str): Path to logfile of decisions made during demultiplexing script
                          *projname*_demultiplex_script_log.txt
        upload_agent(str): Upload agent logfile. Stores Logs relating to runfolder upload.
                           *runfolderpath*/DNANexus_upload_started.txt
        backup(str): Path to logfile for runfolder backup. *projname*_backup_runfolder.log
        project(str): Path to DNAnexus project creation bash script
                      create_nexus_project_*projname*.sh
        dx_run(str): Path to dx run commands. *projname*_dx_run_commands.sh
        upload_script(str): upload_and_setoff_workflows script logfile.
                            *projname*_upload_and_setoff_workflow.log
    """

    formatter = logging.Formatter(config.logging_formatter)  # Log string format

    def __init__(self, log_config, runfolder=True):
        """
        Args:
            logger_name(str): Logger name
            logfile_path(str): Logfile path
        """
        # Logfile to be written to by demultiplex.py
        self.demultiplex = self._get_logger('demultiplex', log_config['demultiplex'])

        if not runfolder:
            self.upload_agent = False
            self.backup = False
            self.project = False
            self.dx_run = False
            self.upload_script = False
        else:
            # Logfiles to be written to by upload_and_setoff_workflows
            self.upload_agent = self._get_logger('upload_agent', log_config['upload_agent'])
            self.backup = self._get_logger('backup_runfolder', log_config['backup'])
            self.project = self._get_logger("create_project", log_config['project'])
            self.dx_run = self._get_logger("dx_run", log_config['dx_run'])
            self.upload_script = self._get_logger('upload_script', log_config['script'])

        # Container for all loggers
        self.all = [
            self.demultiplex,
            self.backup,
            self.project,
            self.dx_run,
            self.upload_script
        ]

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove all handlers
        for all log files taht have a python logging object
        """
        for ad_logger in self.all:
            if ad_logger:
                for handler in ad_logger.handlers[:]:
                    handler.close()
                    ad_logger.removeHandler(handler)
        logging.shutdown()

    def _get_file_handler(self, filepath):
        file_handler = logging.FileHandler(filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        return file_handler

    def _get_syslog_handler(self):
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self.formatter)
        return syslog_handler

    def _get_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self.formatter)
        return stream_handler

    def _get_logger(self, name, filepath):
        """ Returns a Python logging object

        Args:
            name(str): Logger name
            filepath(str): Logfile path
        """
        logger = logging.getLogger(name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(filepath))
        logger.addHandler(self._get_syslog_handler())
        logger.addHandler(self._get_stream_handler())
        return logger
