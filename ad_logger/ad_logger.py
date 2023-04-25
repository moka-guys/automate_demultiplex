# coding=utf-8
"""
Automate demultiplex logging.

Currently only the 'script", 'upload_agent' and 'backup' logfiles are
configured to be writeable to by this script. These logfiles are written to by
the upload and setoff workflows script.

        self.script = self._get_ad_logger('automate_demultiplex", script)
        self.upload_agent = self._get_ad_logger('upload_agent", upload_agent)
        self.backup = self._get_ad_logger('backup_runfolder", backup)
"""
import sys
import os
import logging
import logging.handlers
import ad_config as config


class AdLoggers(object):
    """
    Access runfolder-associated logfiles, which are also uploaded to DNAnexus
    as part of the automate demultiplex scripts. (upload_agent file is not
    uploaded because it is being written to as the upload is taking place)

    Args:
        demultiplex(str):   Path to logfile of decisions made during
                            demultiplexing script
                            *projname*_demultiplex_script_log.txt
        upload_agent(str):  Upload agent logfile. Stores Logs relating to
                            runfolder upload.
                            *runfolderpath*/DNANexus_upload_started.txt
        backup(str):        Path to logfile for runfolder backup.
                            *projname*_backup_runfolder.log
        project(str):       Path to DNAnexus project creation bash script
                            create_nexus_project_*projname*.sh
        dx_run(str):        Path to dx run commands.
                            *projname*_dx_run_commands.sh
        upload_script(str): upload_and_setoff_workflows script logfile.
                            *projname*_upload_and_setoff_workflow.log
    """

    _formatter = logging.Formatter(
        config.LOGGING_FORMATTER
    )  # Log string format

    def __init__(self, timestamp, rf_obj=None):
        """
        Args:
            logger_name(str): Logger name
            logfile_path(str): Logfile path
        """
        self.timestamp = timestamp
        self.rf_obj = rf_obj
        self.log_config = self.get_log_config()
        self.loggers = self.get_loggers()  # Collect all loggers

    def get_loggers(self):
        """
        Assign loggers using log config
        """
        all_loggers = []

        for key in self.log_config:
            setattr(
                AdLoggers, key, self._get_logger(key, self.log_config[key])
            )
            all_loggers.append(getattr(AdLoggers, key))
        return all_loggers

    def get_log_config(self):
        """Return an ADLogger config for a runfolder.

        Returns:
            log_config(dict): A dictionary of arguments for ADLoggers
        """

        # Configuration for ADLoggers. Dictionary where keys are
        # ADLoggers.__init__ arguments and values are logfile paths.

        log_config = {
            # Upload and setoff workflows script logfile
            "upload_script": self.get_scriptlog(
                config.UPLOAD_SCRIPT_LOGDIR,
                config.UPLOAD_SCRIPT_LOGFILE % self.timestamp,
            ),
            "demultiplex": self.get_scriptlog(
                config.DEMULTIPLEX_LOGPATH,
                config.DEMULTIPLEX_SCRIPT_LOGFILE % self.timestamp,
            ),
        }

        if self.rf_obj:
            rf_log_config = {
                "upload_agent": self.rf_obj.upload_agent_logfile,
                "backup": self.rf_obj.backup_runfolder_logfile,
                "project": self.rf_obj.project_creation_logfile,
                "dx_run": self.rf_obj.runfolder_dx_run_script,
            }
            log_config |= rf_log_config
        return log_config

    def get_scriptlog(self, directory, logfile):
        """
        Find the demultiplex logfile for the runfolder. Logfile name contains
        demultiplex timestamp which is unknown at this point. Search for any
        demultiplex logfiles matching the runfodler name and return the first
        If none exist, get the logfile from before it is renamed with
        processed runfolders
        """

        any_logs = [
            os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if self.rf_obj.runfolder_name in filename
        ]
        logfile = any_logs.pop() if any_logs else logfile
        return logfile

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove
        all handlers for all log files that have a python logging object
        """
        for logger in self.loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

    def _get_file_handler(self, filepath):
        file_handler = logging.FileHandler(filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._formatter)
        return file_handler

    def _get_syslog_handler(self):
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self._formatter)
        return syslog_handler

    def _get_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self._formatter)
        return stream_handler

    def _get_logger(self, name, filepath):
        """
        Returns a Python logging object

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
